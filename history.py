
import json
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock

HISTORY_FILE = Path(__file__).parent / "chat_history.jsonl"

HISTORY_LOCK = Lock()


def save_chat_message(
    chat_id: str,
    role: str,
    content: str,
    user_id: str = "default_user",
    agent: str = "chat",
):
    """Save one message for a specific conversation."""

    if role not in ("user", "assistant"):
        return {"ok": False, "error": "invalid role"}

    if not chat_id or not str(chat_id).strip():
        return {"ok": False, "error": "chat_id is required"}

    if content is None or not str(content).strip():
        return {"ok": False, "error": "content is empty"}

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "chat_id": str(chat_id),
        "role": role,
        "content": str(content),
        "agent": agent,
    }

    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        with HISTORY_LOCK:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return {"ok": True}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def load_chat_history(
    chat_id: str,
    user_id: str = "default_user",
    limit: int = 50,
):
    """Load messages belonging to one conversation."""

    if not chat_id:
        return []

    messages = []

    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_LOCK:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Ignore old records without chat_id.
                    if (
                        data.get("user_id") == user_id
                        and data.get("chat_id") == str(chat_id)
                    ):
                        messages.append(data)

        return messages[-max(0, limit):] if limit > 0 else messages

    except Exception as e:
        print(f"Error loading chat history: {e}")
        return []


def clear_chat_history(
    chat_id: str,
    user_id: str = "default_user",
):
    """Delete one conversation without affecting other chats."""

    if not HISTORY_FILE.exists():
        return {"ok": True, "deleted": 0}

    try:
        kept_lines = []
        deleted = 0

        with HISTORY_LOCK:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        # Preserve malformed lines rather than deleting unknown data.
                        kept_lines.append(line)
                        continue

                    if (
                        data.get("user_id") == user_id
                        and data.get("chat_id") == str(chat_id)
                    ):
                        deleted += 1
                    else:
                        kept_lines.append(line)

            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.writelines(kept_lines)

        return {"ok": True, "deleted": deleted}

    except Exception as e:
        return {"ok": False, "error": str(e)}
