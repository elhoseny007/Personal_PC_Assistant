
import json
import logging
import time
import uuid

from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar

logger = logging.getLogger(__name__)

TRACE_FILE = Path(__file__).parent / "traces.jsonl"


class TracingService:

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.langfuse = None

        self._active_record = ContextVar(
            "sonna_trace_record",
            default=None
        )

        self._initialize_langfuse()

    def _initialize_langfuse(self):
        """Initialize Langfuse once."""

        try:
            from config import (
                LANGFUSE_PUBLIC_KEY,
                LANGFUSE_SECRET_KEY,
                LANGFUSE_BASE_URL,
            )

            public_key = LANGFUSE_PUBLIC_KEY
            secret_key = LANGFUSE_SECRET_KEY

            if not public_key or not secret_key:
                logger.info("Langfuse is not configured.")
                return

            from langfuse import Langfuse

            client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=LANGFUSE_BASE_URL or "https://cloud.langfuse.com",
            )

            if not hasattr(client, "start_as_current_observation"):
                logger.warning(
                    "Langfuse SDK version does not support the required API."
                )
                return

            self.langfuse = client
            logger.info("Langfuse initialized.")

        except Exception:
            logger.exception("Langfuse initialization failed.")

    @contextmanager
    def trace_request(self, query, agent="main_agent"):

        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        record = {
            "request_id": request_id,
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "agent": agent,
            "generations": [],
        }

        token = self._active_record.set(record)

        try:
            # Avoid sending private prompts to cloud by default.
            try:
                from config import settings

                capture_content = getattr(
                    settings,
                    "LANGFUSE_CAPTURE_CONTENT",
                    False
                )

            except Exception:
                capture_content = False

            trace_input = (
                {"query": query}
                if capture_content
                else {"query_length": len(query)}
            )

            observation = (
                self.langfuse.start_as_current_observation(
                    as_type="span",
                    name="sonna_ai_request",
                    input=trace_input,
                    metadata={
                        "request_id": request_id,
                        "session_id": self.session_id,
                        "agent": agent,
                    },
                )
                if self.langfuse
                else nullcontext(None)
            )

            with observation as span:

                try:
                    yield record

                except Exception as e:
                    record["error"] = str(e)

                    if span:
                        span.update(
                            level="ERROR",
                            status_message=str(e),
                        )

                    raise

                finally:
                    record["latency_ms"] = round(
                        (time.perf_counter() - start) * 1000,
                        2
                    )

                    generations = record["generations"]

                    record["prompt_tokens"] = sum(
                        g["prompt_tokens"] for g in generations
                    )

                    record["completion_tokens"] = sum(
                        g["completion_tokens"] for g in generations
                    )

                    record["total_tokens"] = (
                        record["prompt_tokens"]
                        + record["completion_tokens"]
                    )

                    if span:
                        output = (
                            {
                                "answer": record.get("response", ""),
                                "ok": record.get("ok", False),
                            }
                            if capture_content
                            else {
                                "ok": record.get("ok", False),
                                "generations": len(generations),
                            }
                        )

                        span.update(
                            output=output,
                            metadata={
                                "request_id": request_id,
                                "iterations": record.get("iterations", 0),
                                "total_tokens": record["total_tokens"],
                                "latency_ms": record["latency_ms"],
                                "error": record.get("error"),
                            },
                        )

        finally:
            try:
                self._save_local(record)

            finally:
                self._active_record.reset(token)

    @contextmanager
    def generation(self, model, input_data=None):

        start = time.perf_counter()

        generation_data = {
            "model": model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": 0,
            "error": None,
        }

        try:
            from config import settings

            capture_content = getattr(
                settings,
                "LANGFUSE_CAPTURE_CONTENT",
                False
            )

        except Exception:
            capture_content = False

        observation_input = (
            input_data
            if capture_content
            else {
                "message_count": len(input_data or [])
            }
        )

        observation = (
            self.langfuse.start_as_current_observation(
                as_type="generation",
                name="groq_chat_completion",
                model=model,
                input=observation_input,
            )
            if self.langfuse
            else nullcontext(None)
        )

        try:
            with observation as generation:

                try:
                    yield generation_data

                except Exception as e:
                    generation_data["error"] = str(e)

                    if generation:
                        generation.update(
                            level="ERROR",
                            status_message=str(e),
                        )

                    raise

                finally:
                    generation_data["latency_ms"] = round(
                        (time.perf_counter() - start) * 1000,
                        2
                    )

                    if generation:
                        generation.update(
                            output=generation_data.get("output"),
                            usage_details={
                                "input": generation_data["prompt_tokens"],
                                "output": generation_data["completion_tokens"],
                            },
                            metadata={
                                "latency_ms": generation_data["latency_ms"],
                            },
                        )

        finally:
            # Attach this generation to the active request.
            record = self._active_record.get()

            if record is not None:
                record["generations"].append(generation_data)

    def _save_local(self, record):

        try:
            with open(TRACE_FILE, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        default=str
                    ) + "\n"
                )

        except Exception:
            logger.exception("Failed to save local trace.")

    def flush(self):

        if self.langfuse:
            try:
                self.langfuse.flush()

            except Exception:
                logger.exception("Langfuse flush failed.")


tracing = TracingService()
