import os
import time
from collections import Counter
from pathlib import Path

import psutil
from docx import Document
from openpyxl import Workbook

# =========================
# Default folder and path helper
# =========================

default_DIR = Path(r"C:\Users\ELZAHBIA\Vs_code\personal_AI_Assistant\auto_files")


def resolve_path(path=None):
    """Return a full Path. Empty -> default folder. Relative -> inside default folder."""
    if not path or not str(path).strip():
        return default_DIR.resolve()
    return (default_DIR / str(path).strip()).resolve()


# =========================
# File tools
# =========================

def create_files(path, content):
    try:
        target = resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "x", encoding="utf-8") as f:
            f.write(content)
        return {"ok": True, "path": str(target)}
    except FileExistsError:
        return {"ok": False, "error": "file already exists"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_docx(path, title, content):
    try:
        target = resolve_path(path)
        if target.suffix.lower() != ".docx":
            target = target.with_suffix(".docx")
        if target.exists():
            return {"ok": False, "error": "file already exists"}
        target.parent.mkdir(parents=True, exist_ok=True)
        doc = Document()
        doc.add_heading(title, level=0)
        for line in content.split("\n"):
            doc.add_paragraph(line)
        doc.save(target)
        return {"ok": True, "path": str(target)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_folder(path):
    try:
        target = resolve_path(path)
        target.mkdir(parents=True, exist_ok=True)
        return {"ok": True, "path": str(target)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_xlsx(path, rows):
    if not isinstance(rows, list) or not rows:
        return {"ok": False, "error": "rows must be a non-empty list"}
    try:
        target = resolve_path(path)
        if target.suffix.lower() != ".xlsx":
            target = target.with_suffix(".xlsx")
        if target.exists():
            return {"ok": False, "error": "file already exists"}
        target.parent.mkdir(parents=True, exist_ok=True)
        wb = Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        wb.save(target)
        return {"ok": True, "path": str(target)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================
# PC search
# =========================

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", "AppData",
    "Windows", "Program Files", "Program Files (x86)", "$Recycle.Bin",
}


def pc_search(query, start_dir=None, max_results=30):
    if not query or not str(query).strip():
        return {"ok": False, "error": "query is empty"}
    try:
        root = Path(start_dir) if start_dir else Path.home()
        if not root.exists():
            return {"ok": False, "error": "start_dir does not exist"}

        q = query.strip().lower()
        results = []
        truncated = False

        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for name in dirs + files:
                if q in name.lower():
                    results.append(str(Path(current) / name))
                    if len(results) >= max_results:
                        truncated = True
                        break
            if truncated:
                break

        return {
            "ok": True,
            "count": len(results),
            "results": results,
            "truncated": truncated,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================
# System status
# =========================

def to_gb(value):
    return round(value / 1024**3, 2)


def get_system_status():
    try:
        cpu = {
            "percentage": psutil.cpu_percent(interval=1),
            "cores": psutil.cpu_count(),
        }

        mem = psutil.virtual_memory()
        ram = {
            "total_gb": to_gb(mem.total),
            "used_gb": to_gb(mem.used),
            "percent": mem.percent,
        }

        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "drive": part.mountpoint,
                    "total_gb": to_gb(usage.total),
                    "used_gb": to_gb(usage.used),
                    "percent": usage.percent,
                })
            except Exception:
                continue

        procs = []
        for p in psutil.process_iter(["name", "memory_percent"]):
            info = p.info
            if info.get("memory_percent") is not None:
                procs.append(info)
        procs.sort(key=lambda x: x["memory_percent"], reverse=True)
        top_processes = [
            {"name": p["name"], "memory_percent": round(p["memory_percent"], 2)}
            for p in procs[:5]
        ]

        return {
            "ok": True,
            "cpu": cpu,
            "ram": ram,
            "disks": disks,
            "top_processes": top_processes,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================
# Count images
# =========================

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".heic"}


def count_images(start_dir=None):
    try:
        root = Path(start_dir) if start_dir else Path.home()
        if not root.exists():
            return {"ok": False, "error": "start_dir does not exist"}

        counts = Counter()
        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for name in files:
                ext = Path(name).suffix.lower()
                if ext in IMAGE_EXTS:
                    counts[ext] += 1

        return {
            "ok": True,
            "scanned": str(root),
            "total": sum(counts.values()),
            "by_extension": dict(counts),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================
# Tests (run: python -m tools.tools)
# Delete the test files from auto_files before each run.
# =========================

if __name__ == "__main__":
    print(resolve_path(None))
    print(resolve_path("notes.txt"))
    print(resolve_path("D:/work/a.txt"))

    print(create_files("hello.txt", "hi"))
    print(create_files("hello.txt", "hi"))
    print(create_files("sub/folder/a.md", "# title"))

    print(create_docx("report", "My Report", "line one\nline two"))
    print(create_docx("report", "My Report", "line one\nline two"))

    print(create_folder("projects/ai"))
    print(create_folder("projects/ai"))

    data = [["name", "age"], ["Ahmed", 25], ["Sara", 30]]
    print(create_xlsx("people", data))
    print(create_xlsx("people", data))
    print(create_xlsx("bad", []))

    t = time.time()
    print(pc_search("personal_AI_Assistant"))
    print("seconds:", round(time.time() - t, 2))
    print(pc_search("zzz_not_exist_zzz"))
    print(pc_search(""))
    print(pc_search("a", max_results=5))

    print(get_system_status())

    print(count_images("C:/Users/ELZAHBIA/Pictures"))
    print(count_images("D:/not_a_folder"))