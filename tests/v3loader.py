"""Run the loader block from SKILL_v3.md against a local server: first load, cached reload, tampered kit refused, then a build from
the loaded kit with the Natural Retreats fixture. Needs a local port (the Claude sandbox blocks it): run in a normal terminal.
Run: python3 tests/v3loader.py   (after python3 make_skill_v3.py --draft)"""
import functools
import http.server
import re
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
block = re.search(r"```python\n(import hashlib, (?:types, )?urllib.request\n.*?)```", (ROOT / "SKILL_v3.md").read_text(), re.S).group(1)
store, serve = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())


def open_artifact(name, mode="r"):
    return open(store / name, mode)


def run(url):
    g = {"open_artifact": open_artifact}
    exec(re.sub(r'KIT_URL = ".*?"', f'KIT_URL = "{url}"', block), g)
    return g


def server():
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(serve)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


name = re.search(r'KIT_FILE = "(.*?)"', block).group(1)
(serve / name).write_bytes((ROOT / "dist" / name).read_bytes())
srv = server()
url = f"http://127.0.0.1:{srv.server_address[1]}/{name}"
g = run(url)
assert callable(g["build"]) and "Spec (dict)" in g["KIT_DOC"] and (store / name).exists()
print("OK   first load: fetched, checked, cached")
srv.shutdown()
g = run(url)
assert callable(g["build"])
print("OK   second load: from the cached copy, no network")
import v3fixture as F
g["_fonts"] = lambda *a, **k: ""
html, report = g["build"](F.spec())
assert html.count("<section") == 5 and "Prepared by Crux · 5 / 5" in html
print("OK   a build from the loaded kit: five pages")
(store / name).write_bytes((store / name).read_bytes() + b"\n# edited\n")
srv = server()
(serve / name).write_bytes((serve / name).read_bytes().replace(b"def build(", b"def build_(", 1))
try:
    run(f"http://127.0.0.1:{srv.server_address[1]}/{name}")
    print("FAIL tampered kit ran")
    sys.exit(1)
except RuntimeError as e:
    print("OK   tampered kit refused:", e)
srv.shutdown()
