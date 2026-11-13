# =========================================================
# SONNA AI - Web server
# Run:  python main.py      then open  http://127.0.0.1:8000
# Needs: pip install fastapi uvicorn python-multipart
# =========================================================
import json
import os
import sys
from pathlib import Path
import threading
import time
import uuid
from typing import List, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse, JSONResponse
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.append(parent_dir)
from google_drive import (
    get_authorization_url,
    complete_oauth,
    is_google_drive_connected,
)

# --- ضبط المسارات بشكل صحيح ---
# مجلد sonna-ai (المجلد الحالي)
current_dir = os.path.dirname(os.path.abspath(__file__))
# مجلد ASK_SONA (المجلد الرئيسي)
parent_dir = os.path.dirname(current_dir)

# إضافة المجلد الرئيسي ومجلد tools إلى مسارات بايثون
# insert(0) = ASK_SONA يتقدم على مجلد sonna-ai، فنسخة tracing.py اللي في ASK_SONA هي اللي تتحمل
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

tools_dir = os.path.join(parent_dir, "tools")
if tools_dir not in sys.path:
    sys.path.append(tools_dir)

# --- استيراد الملفات من المجلد الرئيسي ASK_SONA ---
try:
  import permissions
  from orchestrator import orchestrator, router
  from PC_agent import run_pc_agent
  from Rag import MAX_FILE_MB, add_uploaded_file, answer_from_files, list_files, remove_file
  from Search_agent import run_search_agent
  from chat_voice import transcribe_audio
  from tracing import TRACE_FILE
  from history import (
    load_chat_history,
    save_chat_message,
    clear_chat_history,
)
except ImportError as e:
  print(f"خطأ في الاستيراد: {e}")

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

MAX_MESSAGE_CHARS = 4000
MAX_AUDIO_MB = 25
CONFIRM_TIMEOUT_SECONDS = 60

# app واحد فقط. (كان فيه app = FastAPI() مرتين، والتاني كان بيمسح الأول
# ومعاه endpoint الـ monitoring، وده سبب Not Found)
app = FastAPI(title="SONNA AI")


@app.get("/api/google-drive/connect")
async def google_drive_connect():
    try:
        authorization_url = get_authorization_url()

        return RedirectResponse(
            url=authorization_url,
            status_code=302,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth error: {str(e)}",
        )


@app.get("/api/google-drive/callback")
async def google_drive_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "Google authorization was denied.",
            },
        )

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth code or state.",
        )

    try:
        complete_oauth(code, state)

        return {
            "ok": True,
            "message": "Google Drive connected successfully!",
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth callback failed: {str(e)}",
        )


@app.get("/api/google-drive/status")
async def google_drive_status():
    return {
        "ok": True,
        "connected": is_google_drive_connected(),
    }


_pending = {}
_pending_lock = threading.Lock()


def to_json_safe(value):
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def web_ask_user(tool_name, arguments):
    confirm_id = uuid.uuid4().hex
    item = {
        "id": confirm_id,
        "tool": tool_name,
        "level": permissions.get_level(tool_name).value,
        "arguments": to_json_safe(permissions.shorten(arguments)),
        "created": time.time(),
        "event": threading.Event(),
        "approved": False,
    }
    with _pending_lock:
        _pending[confirm_id] = item
    try:
        item["event"].wait(CONFIRM_TIMEOUT_SECONDS)
        return item["approved"]
    finally:
        with _pending_lock:
            _pending.pop(confirm_id, None)


permissions.ask_user = web_ask_user


# =========================================================
# Helpers
# =========================================================

def summarize_steps(history, agent_name=None):
    """Send only a small summary of each tool call to the browser (no huge page texts)."""
    steps = []
    for item in history or []:
        result = item.get("result") or {}
        steps.append({
            "agent": item.get("agent", agent_name),
            "tool": item.get("tool"),
            "ok": bool(result.get("ok")) if isinstance(result, dict) else False,
            "error": result.get("error") if isinstance(result, dict) else None,
        })
    return steps


def run_mode(message, mode, history=None):

    # Auto: orchestrator handles routing itself
    if mode == "auto":
        r = orchestrator(message, history=history)
        return {
            "ok": r["ok"],
            "route": r["route"],
            "answer": r["answer"],
            "error": r["error"],
            "steps": summarize_steps(r.get("steps", [])),
            "sources": r.get("sources", []),
        }

    # Documents / RAG
    if mode == "rag":
        r = answer_from_files(message)
        return {
            "ok": r["ok"],
            "route": "rag",
            "answer": r["answer"],
            "error": r["error"],
            "steps": [],
            "sources": r.get("sources", []),
        }

    # PC / Search
    _, selected_model = router(message, history=history)

    if mode == "pc":
        r = run_pc_agent(message, selected_model, history=history)
        return {
            "ok": r["ok"],
            "route": "pc",
            "answer": r["answer"],
            "error": r["error"],
            "steps": summarize_steps(r.get("tool_history", []), "pc"),
            "sources": [],
        }

    if mode == "search":
        r = run_search_agent(message, selected_model, history=history)
        return {
            "ok": r["ok"],
            "route": "search",
            "answer": r["answer"],
            "error": r["error"],
            "steps": summarize_steps(r.get("tool_history", []), "search"),
            "sources": [],
        }

    return {
        "ok": False,
        "route": mode,
        "answer": None,
        "error": f"Unsupported mode: {mode}",
        "steps": [],
        "sources": [],
    }

# =========================================================
# API
# =========================================================

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    chat_id: str = Field(min_length=1, max_length=128)
    mode: Literal["auto", "pc", "search", "rag"] = "auto"

class ConfirmAnswer(BaseModel):
    approved: bool


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    message = body.message.strip()

    if not message:
        raise HTTPException(400, "message is empty")

    chat_id = body.chat_id.strip()

    if not chat_id:
        raise HTTPException(400, "chat_id is empty")

    try:
        # 1. Load previous messages BEFORE saving current message
        history = await run_in_threadpool(
            load_chat_history,
            chat_id
        )

        # 2. Save current user message
        await run_in_threadpool(
            save_chat_message,
            chat_id,
            "user",
            message
        )

        # 3. Run the selected mode with previous history
        result = await run_in_threadpool(
            run_mode,
            message,
            body.mode,
            history
        )

        # 4. Save assistant response if available
        answer = result.get("answer")

        if answer:
            await run_in_threadpool(
                save_chat_message,
                chat_id,
                "assistant",
                answer,
                agent=result.get("route", body.mode)
            )

        # 5. Return response
        return result

    except Exception as e:
        return {
            "ok": False,
            "route": body.mode,
            "answer": None,
            "error": str(e),
            "steps": [],
            "sources": [],
        }
@app.delete("/api/chat/{chat_id}")
async def clear_chat(chat_id: str):
    try:
        await run_in_threadpool(clear_chat_history, chat_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))  
@app.get("/api/confirm/pending")
async def pending_confirmations():
    with _pending_lock:
        items = [
            {k: v for k, v in item.items() if k not in ("event", "approved")}
            for item in _pending.values()
        ]
    return {"items": items, "timeout": CONFIRM_TIMEOUT_SECONDS}


@app.post("/api/confirm/{confirm_id}")
async def answer_confirmation(confirm_id: str, body: ConfirmAnswer):
    with _pending_lock:
        item = _pending.get(confirm_id)
    if item is None:
        raise HTTPException(404, "confirmation not found or expired")
    item["approved"] = body.approved
    item["event"].set()
    return {"ok": True}


@app.get("/api/rag/files")
async def rag_files():
    return {"ok": True, "files": await run_in_threadpool(list_files)}


@app.post("/api/rag/upload")
async def rag_upload(files: List[UploadFile] = File(...)):
    results = []
    for f in files:
        data = await f.read(MAX_FILE_MB * 1024 * 1024 + 1)
        result = await run_in_threadpool(
            add_uploaded_file, f.filename, data
        )
        results.append({"name": f.filename, **result})
    return {"ok": all(r["ok"] for r in results), "results": results}


@app.delete("/api/rag/files/{name}")
async def rag_remove(name: str):
    return await run_in_threadpool(remove_file, name)


@app.post("/api/voice")
async def voice(audio: UploadFile = File(...), language: str = Form("ar")):
    data = await audio.read(MAX_AUDIO_MB * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(400, "audio is empty")
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(413, f"audio is larger than {MAX_AUDIO_MB} MB")
    try:
        text = await run_in_threadpool(
            transcribe_audio, data, audio.filename or "audio.webm", language
        )
        return {"ok": True, "text": text}
    except Exception as e:
        return {"ok": False, "text": None, "error": str(e)}


# =========================================================
# MONITORING - reads the traces.jsonl written by ASK_SONA\tracing.py
# =========================================================

def read_traces():
    rows = []
    path = Path(TRACE_FILE)
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip a half-written line
    return rows


def build_monitoring(rows, limit=50):
    limit = max(1, min(int(limit), 200))
    total = len(rows)
    ok_count = sum(1 for r in rows if r.get("ok"))
    latencies = sorted(
        r["latency_ms"] for r in rows if isinstance(r.get("latency_ms"), (int, float))
    )
    avg = round(sum(latencies) / len(latencies), 1) if latencies else None
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else None

    recent = []
    for r in rows[-limit:][::-1]:
        models = sorted({g.get("model") for g in r.get("generations", []) if g.get("model")})
        recent.append({
            "timestamp": r.get("timestamp"),
            "agent": r.get("agent"),
            "query": (r.get("query") or "")[:160],
            "ok": bool(r.get("ok")),
            "error": r.get("error"),
            "latency_ms": r.get("latency_ms"),
            "total_tokens": r.get("total_tokens", 0),
            "iterations": r.get("iterations", 0),
            "models": models,
        })

    return {
        "ok": True,
        "trace_file": str(TRACE_FILE),
        "summary": {
            "requests": total,
            "success_rate": round(ok_count * 100 / total, 1) if total else None,
            "errors": total - ok_count,
            "avg_latency_ms": avg,
            "p95_latency_ms": p95,
            "total_tokens": sum(r.get("total_tokens", 0) or 0 for r in rows),
        },
        "recent": recent,
    }


@app.get("/api/monitoring")
async def monitoring(limit: int = 50):
    rows = await run_in_threadpool(read_traces)
    return build_monitoring(rows, limit)

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)