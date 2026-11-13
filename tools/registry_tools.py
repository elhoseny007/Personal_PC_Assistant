import os
import subprocess
from pathlib import Path

from permissions import privacy
from tools.tools import (
    count_images, create_docx, create_files, create_folder, create_xlsx,
    get_system_status, pc_search, resolve_path,
)
from tools.web_tools import download_files, google_search, scrape_page
from tools.google_drive_tools import upload_to_google_drive

# =========================
# Open apps
# =========================

APP_WHITELIST = {
    "vs_code": Path(r"C:\Users\ELZAHBIA\AppData\Local\Programs\Microsoft VS Code\Code.exe"),
    "sql_server": Path(r"C:\Program Files\Microsoft SQL Server Management Studio 22\Release\Common7\IDE\SSMS.exe"),
    "microsoft_edge": Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    "desktop": Path(r"C:\Users\ELZAHBIA\Desktop"),
    "obs_studio": Path(r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"),
    "excel": Path(r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"),
    "word_office": Path(r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"),
    "anaconda_prompt": [
        r"C:\Windows\System32\cmd.exe",
        "/K",
        r"C:\Users\ELZAHBIA\anaconda3\Scripts\activate.bat",
        r"C:\Users\ELZAHBIA\anaconda3",
    ],
    "cmd": Path(r"C:\Windows\System32\cmd.exe"),
}

CONSOLE_APPS = {"cmd", "anaconda_prompt"}
def list_indexed_files():
    """
    Return files stored in the local RAG knowledge base.
    """

    try:
        from Rag import list_files

        files = list_files()

        return {
            "ok": True,
            "files": files
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

def open_apps(name):
    if not name or not str(name).strip():
        return {"ok": False, "error": "name is empty"}

    clean_name = str(name).strip().lower()
    app = APP_WHITELIST.get(clean_name)
    if app is None:
        return {
            "ok": False,
            "error": "app not allowed",
            "allowed": list(APP_WHITELIST.keys()),
        }
    try:
        if isinstance(app, list):
            command = app
            program = Path(app[0])
        else:
            command = [str(app)]
            program = app
        if not program.exists():
            return {"ok": False, "error": f"path not found: {program}"}
        if isinstance(app, Path) and app.is_dir():
            os.startfile(str(app))
        else:
            flags = subprocess.CREATE_NEW_CONSOLE if clean_name in CONSOLE_APPS else 0
            subprocess.Popen(command, creationflags=flags)
        return {"ok": True, "app": clean_name, "message": "launched"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def open_folder(path):
    if not path or not str(path).strip():
        return {"ok": False, "error": "path is empty"}
    raw = str(path).strip()
    if raw.startswith("\\\\"):
        return {"ok": False, "error": "network paths are not allowed"}
    try:
        folder = Path(raw).expanduser().resolve()
        if not folder.is_dir():
            return {"ok": False, "error": "folder not found (only folders can be opened)"}
        os.startfile(str(folder))
        return {"ok": True, "message": "opened", "path": str(folder)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# =========================
# Registry
# =========================

registry = {
    "create_files": create_files,
    "create_docx": create_docx,
    "create_folder": create_folder,
    "create_xlsx": create_xlsx,
    "pc_search": pc_search,
    "get_system_status": get_system_status,
    "count_images": count_images,
    "google_search": google_search,
    "scrape_page": scrape_page,
    "download_files": download_files,
    "open_apps": open_apps,
    "open_folder": open_folder,
    "upload_to_google_drive": upload_to_google_drive,
    "list_indexed_files": list_indexed_files
}

PATH_TOOLS = {"create_files", "create_docx", "create_folder", "create_xlsx"}


def execute_tool(tool_name, arguments):
    
    if tool_name not in registry:
        return {"ok": False, "error": "unknown tool"}
    if not isinstance(arguments, dict):
        return {"ok": False, "error": "arguments must be a dict"}

    args = dict(arguments)

    if tool_name in PATH_TOOLS:
        try:
            args["path"] = str(resolve_path(args.get("path")))
        except Exception as e:
            return {"ok": False, "error": f"invalid path: {e}"}
    if tool_name == "upload_to_google_drive":
        try:
            file_path = Path(args.get("file_path", "")).expanduser().resolve()

            if not file_path.is_file():
                return {"ok": False, "error": "File not found."}

            args["file_path"] = str(file_path)

        except Exception as e:
            return {"ok": False, "error": f"Invalid file path: {e}"}

    if not privacy(tool_name, args):
        return {"ok": False, "error": "denied"}

    try:
        return registry[tool_name](**args)
    except TypeError as e:
        return {"ok": False, "error": f"bad arguments: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================
# Tests (run: python -m tools.registry_tools)
# =========================

if __name__ == "__main__":
    print(execute_tool("get_system_status", {}))
    print(execute_tool("create_files", {"path": "reg_test.txt", "content": "hi"}))
    print(execute_tool("create_files", {"path": "reg_test.txt", "content": "hi"}))
    print(execute_tool("create_files", {"path": "C:/Windows/x.txt", "content": "hi"}))
    print(execute_tool(
        "pc_search",
        {"query": "reg_test", "start_dir": r"C:\Users\ELZAHBIA\Vs_code\personal_AI_Assistant\auto_files"},
    ))
    print(execute_tool("open_apps", {"name": "cmd"}))
    print(execute_tool("delete_everything", {}))
    print(execute_tool("create_files", {"wrong_name": "x"}))