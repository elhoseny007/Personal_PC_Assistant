import ipaddress
import os
import re
import socket
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()
MAX_SEARCH_RESULTS = 10
TAVILY_API_KEY=os.getenv('TAVILY_API_KEY')
Tavily_Client=TavilyClient(api_key=TAVILY_API_KEY)
if not Tavily_Client:
    raise ValueError("TAVILY_API_KEY is missing from .env")

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

loaded = load_dotenv(dotenv_path=ENV_PATH, override=True)

print("[ENV DEBUG]")
print("Env path:", ENV_PATH)
print("Env file exists:", ENV_PATH.is_file())
print("Dotenv loaded:", loaded)
print("API key exists:", bool(os.getenv("TAVILY_API_KEY")))
print("API key length:", len(os.getenv("TAVILY_API_KEY", "")))
#google_search
def google_search(query,max_results=5):
    try:
        load_dotenv()
        key=os.getenv("TAVILY_API_KEY") 
        if not key:
            return {"ok": False, "error":'TAVILY_API_KEY not exist'}
        if not query or not str(query).strip():
            return {"ok": False, "error":'the question is empty'}
        max_results = max(1, min(int(max_results), MAX_SEARCH_RESULTS))
        client = TavilyClient(api_key=key)
        response = client.search(query.strip(), max_results=max_results,search_depth="advanced")
        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
            for item in response.get("results", [])
        ]

        return {
            "ok": True,
            "query": query.strip(),
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    print(google_search("python asyncio tutorial"))
    print(google_search(""))
    print(google_search("python", max_results=100))
#---------------------------
#page

NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript"]

def is_safe_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        for info in socket.getaddrinfo(parsed.hostname, None):
            ip = ipaddress.ip_address(info[4][0].split("%")[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError):
        return False
    return True


def scrape_page(url, max_chars=20000):
    if not url or not str(url).strip():
        return {"ok": False, "error": "url is empty"}
    url = str(url).strip()

    if not is_safe_url(url):
        return {"ok": False, "error": "url not allowed: only public http/https links"}

    try:
        max_chars = max(1000, int(max_chars))

        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            return {"ok": False, "error": f"not an HTML page ({content_type})"}

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.get_text(strip=True) if soup.title else ""

        for tag in soup(NOISE_TAGS):
            tag.decompose()

        main = soup.find("article") or soup.find("main") or soup.body or soup
        text = main.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)

        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars]

        return {
            "ok": True,
            "url": url,
            "title": title,
            "text": text,
            "length": len(text),
            "truncated": truncated,
        }
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "request timed out"}
    except requests.exceptions.HTTPError as e:
        return {"ok": False, "error": f"site returned an error: {e}"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "connection failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    print(scrape_page("https://example.com"))
    print(scrape_page("not a url"))
    print(scrape_page("file:///C:/Windows/win.ini"))
    print(scrape_page("http://localhost:8000"))
    print(scrape_page("https://httpbin.org/status/404"))
    #---------------------------------
#download files
DOWNLOAD_DIR = Path(r"C:\Users\ELZAHBIA\Downloads")
BLOCKED_EXTS = {".exe", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".scr", ".js", ".jar", ".lnk"}
RESERVED_NAMES = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)
MAX_REDIRECTS = 5
CHUNK_SIZE = 1024 * 1024


def clean_filename(name):
    name = Path(str(name)).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if not name:
        name = "download"
    if Path(name).stem.upper() in RESERVED_NAMES:
        name = "_" + name
    return name


def unique_path(folder, name):
    candidate = folder / name
    stem, suffix = candidate.stem, candidate.suffix
    i = 1
    while candidate.exists():
        candidate = folder / f"{stem} ({i}){suffix}"
        i += 1
    return candidate


def download_files(url, filename=None, max_mb=100):
    if not url or not str(url).strip():
        return {"ok": False, "error": "url is empty"}
    url = str(url).strip()

    part = None
    response = None
    try:
        max_bytes = max(1, min(int(max_mb), 500)) * 1024 * 1024

        name = filename or Path(unquote(urlparse(url).path)).name
        name = clean_filename(name)
        if Path(name).suffix.lower() in BLOCKED_EXTS:
            return {"ok": False, "error": f"file type not allowed: {Path(name).suffix}"}

        current = url
        for _ in range(MAX_REDIRECTS + 1):
            if not is_safe_url(current):
                return {"ok": False, "error": "url not allowed: only public http/https links"}
            response = requests.get(
                current,
                stream=True,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
                allow_redirects=False,
            )
            if response.is_redirect:
                current = urljoin(current, response.headers["Location"])
                response.close()
                continue
            break
        else:
            return {"ok": False, "error": "too many redirects"}

        response.raise_for_status()

        final_ext = Path(unquote(urlparse(current).path)).suffix.lower()
        if final_ext in BLOCKED_EXTS:
            return {"ok": False, "error": f"file type not allowed: {final_ext}"}

        length = response.headers.get("Content-Length")
        if length and length.isdigit() and int(length) > max_bytes:
            return {"ok": False, "error": f"file is larger than {max_mb} MB"}

        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        target = unique_path(DOWNLOAD_DIR, name).resolve()
        if not target.is_relative_to(DOWNLOAD_DIR.resolve()):
            return {"ok": False, "error": "invalid file name"}

        part = target.with_name(target.name + ".part")
        size = 0
        with open(part, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError(f"file is larger than {max_mb} MB")
                f.write(chunk)
        part.replace(target)

        return {
            "ok": True,
            "path": str(target),
            "filename": target.name,
            "size_bytes": size,
            "content_type": response.headers.get("Content-Type", ""),
        }
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "request timed out"}
    except requests.exceptions.HTTPError as e:
        return {"ok": False, "error": f"site returned an error: {e}"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "connection failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if response is not None:
            response.close()
        if part is not None and part.exists():
            part.unlink()


if __name__ == "__main__":

    test_urls = [
        "https://example.com",
        "not a url",
        "file:///C:/Windows/win.ini",
        "http://localhost:8000",
        "https://httpbin.org/status/404",
    ]

    for url in test_urls:
        print("\n" + "=" * 60)
        print(f"Testing URL: {url}")

        result = scrape_page(url)

        print("Result:", result)
        print("Status:", "PASS" if isinstance(result, dict) and "ok" in result else "FAIL")
#---------------------------------
