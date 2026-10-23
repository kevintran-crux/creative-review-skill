"""Write SKILL_v3.md from SKILL_v3.src.md, and the kit file the v3 skill loads, from build_kit_v3.py and v3_static.py.

The v3 skill is the five-page report (Kevin's 10/22 sign-off). It is built beside v2 and touches none of v2's files:
the dist file is build_kit_v3-<sha12>.py, which make_skill.py never deletes, and the skill file is SKILL_v3.md.
Edit build_kit_v3.py and SKILL_v3.src.md, never SKILL_v3.md, then run: python3 make_skill_v3.py
The kit (v3_static.py first, then build_kit_v3.py) is stripped of comments and inner docstrings and written to
kit_embedded_v3.py (the tests' copy) and to dist/build_kit_v3-<sha12>.py, the exact bytes to host. SKILL_v3.md carries a short loader with the kit's URL and
SHA-256 instead of the kit; the copilot refuses to run a kit whose hash differs. kit_host.txt holds the URL
folder the dist file is served from. SKILL_v3.md is written only once that URL serves the kit with the right
SHA-256 (host dist/build_kit_v3-<sha12>.py first, README "v3 skill"); then the paste body's SHA-256 is printed, to compare
with the saved text after the paste.
`python3 make_skill_v3.py --draft` writes SKILL_v3.md without the URL check, for the local tests; its URL reads NOT-HOSTED
and it is not ready to paste.
"""
import ast
import hashlib
import json
import io
import sys
import tokenize
import urllib.request
from pathlib import Path

# arguments first, before anything is written: until 10/14 "--help" rebuilt everything (change 33)
FLAGS = {"--draft"}
USAGE = "usage: python3 make_skill_v3.py [--draft]\n\n" + __doc__.strip()
if set(sys.argv[1:]) & {"-h", "--help"}:
    print(USAGE)
    sys.exit(0)
if set(sys.argv[1:]) - FLAGS or len(sys.argv[1:]) > 1:
    bad = " ".join(a for a in sys.argv[1:] if a not in FLAGS)
    print((f"unknown argument(s): {bad}" if bad else "one flag at most") + f"\n\n{USAGE}", file=sys.stderr)
    sys.exit(2)
embed = False
draft = "--draft" in sys.argv

HERE = Path(__file__).parent
src = (HERE / "build_kit_v3.py").read_text()
STATIC_IMPORT = """try:
    STATIC
except NameError:
    from v3_static import STATIC  # noqa: F401 (make_skill_v3.py puts v3_static.py above the kit instead)
"""
assert STATIC_IMPORT in src, "the STATIC import block moved: update make_skill_v3.py"
src = (HERE / "v3_static.py").read_text() + "\n" + src.replace(STATIC_IMPORT, "")
drop = set()
for node in ast.walk(ast.parse(src)):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.body and isinstance(node.body[0], ast.Expr) \
            and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
        drop.update(range(node.body[0].lineno, node.body[0].end_lineno + 1))
lines = src.splitlines()
for tok in tokenize.generate_tokens(io.StringIO(src).readline):
    if tok.type == tokenize.COMMENT:
        r, c = tok.start
        lines[r - 1] = lines[r - 1][:c].rstrip()
kit = "\n".join(l for i, l in enumerate(lines, 1) if i not in drop).replace("\n\n\n\n", "\n\n\n")
ast.parse(kit)
data = (kit + "\n").encode("utf-8")
sha = hashlib.sha256(data).hexdigest()
name = f"build_kit_v3-{sha[:12]}.py"
(HERE / "kit_embedded_v3.py").write_bytes(data)
dist = HERE / "dist"
dist.mkdir(exist_ok=True)
for old in dist.glob("build_kit_v3-*.py"):
    if old.name != name:
        old.unlink()
(dist / name).write_bytes(data)
(dist / "kit_v3.sha256").write_text(f"{sha}  {name}\n")
host = HERE / "kit_host.txt"
url = host.read_text().strip().rstrip("/") + "/" + name if host.exists() and not draft else "NOT-HOSTED/" + name
if not (embed or draft):
    for _try in range(3):  # a read cut short is retried: the Claude sandbox cut this download short on 2026-10-23
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            served = hashlib.sha256(urllib.request.urlopen(req, timeout=60).read()).hexdigest()
            why = None if served == sha else f"it serves a file with SHA-256 {served[:12]}…, not {sha[:12]}…"
            break
        except Exception as e:  # noqa: BLE001
            why = f"it does not serve the kit ({e})"
    if why:
        print(f"kit {sha[:12]}…, dist/{name}, kit_embedded_v3.py written. SKILL_v3.md NOT written: {url} — {why}.\n"
              "Host dist/" + name + " in the Build Kit Host chat first (README Install), then run this again; "
              "for the local tests only, run with --draft.", file=sys.stderr)
        sys.exit(1)

LOAD = '''Every run that needs the kit (tagging, the summary, each build) starts with this block.
The kit is not in this skill: the block downloads it once per chat, checks it against the hash written here,
keeps the checked copy in the chat's files and refuses a kit that does not match. Copy the block exactly. Never
retype, rebuild or edit the kit, and never write your own HTML instead. When it raises, stop and tell the rep
the build kit failed its check.

```python
import hashlib, types, urllib.request
KIT_SHA256 = "{sha}"
KIT_URL = "{url}"
KIT_FILE = "{name}"
if globals().get("KIT_LOADED") != KIT_SHA256:
    try:
        src = open_artifact(KIT_FILE, "rb").read()
    except Exception:
        src = b""
    if hashlib.sha256(src).hexdigest() != KIT_SHA256:
        req = urllib.request.Request(KIT_URL, headers={{"User-Agent": "Mozilla/5.0"}})
        src = urllib.request.urlopen(req, timeout=60).read()
        if hashlib.sha256(src).hexdigest() != KIT_SHA256:
            raise RuntimeError("Build kit hash mismatch: stop and tell the rep. Do not build.")
        try:
            with open_artifact(KIT_FILE, "xb") as f:
                f.write(src)
        except Exception:
            pass
    kit = types.ModuleType("build_kit_v3")
    exec(src.decode("utf-8"), kit.__dict__)
    globals().update({{k: v for k, v in vars(kit).items() if not k.startswith("__")}})
    KIT_DOC, KIT_LOADED = kit.__doc__, KIT_SHA256
```

The first time in a chat, `print(KIT_DOC)`: it describes the `spec`. A later run that tags ads or builds pages
runs the same block and reads `ads.json` back with `open_artifact("ads.json")`.'''.format(sha=sha, url=url, name=name)

EMBED = '''Paste the kit once per chat. Python state usually carries over between runs in one chat, but a
sub-task or a new chat starts empty, so save the kit as a file the first time. The first run that
needs the kit wraps it, verbatim, in a raw string (it contains no three single quotes), runs it and
saves it:

```python
KIT = r\'\'\'<paste the build kit below here>\'\'\'
exec(KIT)
with open_artifact("build_kit.py", "x") as f:
    f.write(KIT)
```

Every later run starts with
`if "build" not in globals(): exec(open_artifact("build_kit.py").read())` instead of pasting it
again. A sub-task that tags ads or builds pages loads the kit and `ads.json` from those files.
The `spec` is described in the kit's header.'''

skill = (HERE / "SKILL_v3.src.md").read_text()
for mark in ("{{LOAD}}", "{{KIT_SECTION}}", "{{CUSTOMERS}}"):
    assert skill.count(mark) == 1, mark
# the customer list comes from Apollo through scripts/crux_customers.py; refresh that file first
# the isolated bundle holds no customer list: the owner fills it in locally before any install
CUSTOMERS_FILE = HERE / "customers.json"
if CUSTOMERS_FILE.exists():
    cust = json.loads(CUSTOMERS_FILE.read_text())
    skill = skill.replace("{{CUSTOMERS}}", ", ".join(c["name"] for c in cust["customers"] + cust["kept_by_hand"])
                          + f" (from Apollo won deals, {cust['pulled']})")
else:
    skill = skill.replace("{{CUSTOMERS}}", "<<CUSTOMER LIST NOT FILLED IN: do not install this body>>")
section = "## Build kit\n\nPaste this verbatim at the top of the build run.\n\n```python\n" + kit + "\n```\n" if embed else ""
out = skill.replace("{{LOAD}}", EMBED if embed else LOAD).replace("{{KIT_SECTION}}", section).rstrip() + "\n"
(HERE / "SKILL_v3.md").write_text(out)
print(f"SKILL_v3.md {len(out):,} chars ({'kit embedded' if embed else 'loader'}); kit {len(data):,} bytes, "
      f"sha256 {sha[:12]}…, dist/{name}")
# what gets pasted is the body below the frontmatter; GetCrux saves it without the blank line after the frontmatter
body = out.split("\n---\n", 1)[1].lstrip("\n")
if draft:
    print("DRAFT: the kit URL reads NOT-HOSTED; not ready to paste")
else:
    print(f"paste body: {len(body):,} chars, sha256 {hashlib.sha256(body.encode('utf-8')).hexdigest()}"
          + ("" if embed else f" (kit checked at {url})"))
