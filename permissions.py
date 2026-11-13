import json
from datetime import datetime
from enum import Enum
from pathlib import Path

LOG_FILE = Path(__file__).parent / "audit.jsonl"


class lvl(Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class decision_result(Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


TOOL_LEVELS = {
    "google_search": lvl.green,
    "pc_search": lvl.green,
    "get_system_status": lvl.green,
    "count_images": lvl.green,
    "scrape_page": lvl.green,
    "create_files": lvl.yellow,
    "create_docx": lvl.yellow,
    "create_folder": lvl.yellow,
    "open_folder": lvl.yellow,
    "create_xlsx": lvl.yellow,
    "download_files": lvl.yellow,
    "open_apps": lvl.red,
    "upload_to_google_drive": lvl.red,
}

protected = [
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
]


def get_level(tool_name):
    return TOOL_LEVELS.get(tool_name, lvl.red)


def is_protected(user_path):
    try:
        target = Path(user_path).resolve()
    except Exception:
        return True
    for folder in protected:
        if target.is_relative_to(folder.resolve()):
            return True
    return False


def check_permission(tool_name, arguments):
    arguments = arguments if isinstance(arguments, dict) else {}
    level = get_level(tool_name)
    path = arguments.get("path")

    if level == lvl.green:
        return decision_result.ALLOW

    if path is not None and is_protected(path):
        return decision_result.DENY

    if level == lvl.yellow:
        if path is not None and Path(path).exists():
            return decision_result.CONFIRM
        return decision_result.ALLOW

    return decision_result.CONFIRM


def ask_user(tool_name, arguments):
    answer = input(f"Allow {tool_name} with {shorten(arguments)}? (y/n): ")
    return answer.strip().lower() == "y"


def shorten(value, limit=200):
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"... [{len(value)} chars]"
    if isinstance(value, dict):
        return {k: shorten(v, limit) for k, v in value.items()}
    if isinstance(value, list):
        return f"[list of {len(value)} items]"
    return value


def write_log(tool_name, arguments, decision, result):
    entry = {
        "time": datetime.now().isoformat(),
        "tool": tool_name,
        "arguments": shorten(arguments),
        "decision": decision.value,
        "result": result,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


def privacy(tool_name, arguments):
    decision = check_permission(tool_name, arguments)

    if decision == decision_result.DENY:
        write_log(tool_name, arguments, decision, "denied")
        return False

    if decision == decision_result.CONFIRM:
        if not ask_user(tool_name, arguments):
            write_log(tool_name, arguments, decision, "user_rejected")
            return False
        write_log(tool_name, arguments, decision, "approved_by_user")
        return True

    write_log(tool_name, arguments, decision, "allowed")
    return True


if __name__ == "__main__":
    print(get_level("open_apps"))
    print(privacy("google_search", {}))
    print(privacy("create_files", {"path": "C:/Windows/x.txt"}))
    print(privacy("create_files", {"path": "C:/Users/../Windows/x.txt"}))
    print(privacy("create_files", {"path": "D:/new_file.txt"}))
    print(privacy("open_apps", {"name": "vs_code"}))
    print(privacy("delete_everything", {}))