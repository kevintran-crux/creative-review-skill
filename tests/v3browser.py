"""The v3 report in Chromium (the Claude sandbox blocks Chromium; run this in a normal terminal): five A4 pages, none
taller than 1123 px, no image that fails to load, nothing wider than a 390 px phone, no text past a page's right
margin; saves a screenshot of each page in tests/out/v3-page-N.png. Run: python3 tests/v3browser.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import v3fixture as F
from playwright.sync_api import sync_playwright

# the real font, so the page fit is what a reader sees
kit = F.kit
kit._fonts = lambda *a, **k: (F.FIX / "fonts.css").read_text()
doc, r = F.build()
out = F.HERE / "out"
out.mkdir(exist_ok=True)
(out / "v3-nr.html").write_text(doc)
fails = 0
# the same fixture on TikTok, Google and LinkedIn: page 2 carries a caveat line (or no chart at all) and must still fit
BENCH = F.benchmarks()
DOCS = [("", doc)] + [(f"-{p.lower()}", kit.build(F.on(p, BENCH[p], F.RULES[p]))[0]) for p in ("TIKTOK", "GOOGLE", "LINKEDIN")]
for tag, d in DOCS[1:]:
    (out / f"v3-nr{tag}.html").write_text(d)


def one(b, tag, doc):
    global fails
    pg = b.new_page(viewport={"width": 900, "height": 1200})
    pg.set_content(doc, wait_until="networkidle")
    pg.wait_for_timeout(400)
    heights = pg.evaluate("[...document.querySelectorAll('section.page')].map(p => Math.round(p.getBoundingClientRect().height))")
    broken = pg.evaluate("[...document.images].filter(i => !i.naturalWidth).length")
    over = pg.evaluate("""[...document.querySelectorAll('section.page')].map(p => { const R = p.getBoundingClientRect();
        return [...p.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > R.right - 40 && e.getBoundingClientRect().width > 0
          && !e.closest('.bench-wrap, .lwrap')).length })""")
    for i, el in enumerate(pg.query_selector_all("section.page"), 1):
        el.screenshot(path=str(out / f"v3-page-{i}{tag}.png"))
    pg.set_viewport_size({"width": 390, "height": 800})
    pg.wait_for_timeout(300)
    wide = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    pg.set_viewport_size({"width": 375, "height": 800})
    pg.wait_for_timeout(300)
    wide375 = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    pg.close()
    for label, ok, detail in (("five pages", len(heights) == 5, heights), ("each page 1123 px or less", max(heights) <= 1123, heights),
                              ("no broken image", broken == 0, broken), ("nothing past the right margin", sum(over) == 0, over),
                              ("no sideways scroll at 390 px", wide <= 1, wide), ("no sideways scroll at 375 px", wide375 <= 1, wide375)):
        print(("OK   " if ok else "FAIL ") + (tag.strip("-").upper() or "META") + ": " + label, "" if ok else detail)
        fails += not ok


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for tag, d in DOCS:
        one(b, tag, d)
    b.close()
sys.exit(1 if fails else 0)
