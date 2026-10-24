"""The directional report: spec "sample": "directional" lets a competitor with 5 or more live ads in. Offline.
Run: python3 tests/v3sample.py"""
import importlib.util
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import v3fixture as F

K = F.kit
fails = 0


def check(label, ok, detail=""):
    global fails
    fails += not ok
    print(("OK   " if ok else "FAIL ") + label, "" if ok else detail)


def trim(s, counts):
    """Cut each competitor to `counts` live ads, keeping the ads the pages show (p3_ads) and keeping launches in the window."""
    keep = {a["ad_id"] for a in s["p3_ads"]} | {s["p1_ad"]}
    for b, n in zip(s["brands"][1:], counts):
        shown = [a for a in b["ads"] if a["ad_id"] in keep]
        rest = [a for a in b["ads"] if a["ad_id"] not in keep]
        b["ads"] = (shown + rest)[:n]
        b["dropped"] = 0


def sp(counts, sample="directional", edit=None):
    s = F.spec()
    s["sample"] = sample
    trim(s, counts)
    if edit:
        edit(s)
    return s


def problems(s):
    return "\n".join(K.precheck(s))


# ---- the default spec is byte for byte what the kit built before the change
base = importlib.util.spec_from_file_location("base_kit", F.FIX / "base-kit-current.py")
old = importlib.util.module_from_spec(base)
base.loader.exec_module(old)
old._fonts = K._fonts
want, _ = old.build(F.spec())
got, _ = K.build(F.spec())
check("default spec: output equals the baseline kit's, byte for byte", got == want)
s = F.spec()
s["sample"] = "standard"
check("sample standard: output equals the baseline kit's, byte for byte", K.build(s)[0] == want)

# ---- a directional build with competitors of 5, 6 and 12 ads
s = sp([5, 6, 12])
check("the line-up has 5, 6 and 12 ads", [len(b["ads"]) for b in s["brands"][1:]] == [5, 6, 12])
out = problems(s)
check("a directional spec with competitors of 5, 6 and 12 ads has no problem", not out, out[:800])
if not out:
    doc, r = K.build(s)
    pages = F.page_text(doc)
    check("the report counts are the real ones", [m.live for m in r.M[1:]] == [5, 6, 12], [m.live for m in r.M])
    c = r.c
    line = "Small sample: Vrbo has 5, Inspirato has 6 and Airbnb has 12 live ads in this line, so read this as a direction."
    for n in (1, 3, 4):
        check(f"page {n} carries one footer line naming every small competitor with its real count", line in pages[n - 1], pages[n - 1][-250:])
    for n in (2, 5):
        check(f"page {n} has no small-sample line", "Small sample" not in pages[n - 1])
    check("five pages", len(pages) == 5)
    # page 3 shows every competitor's real count in the chart
    for m in r.M[1:]:
        check(f"page 3 chart prints {m.short}'s {m.live} live ads", f"of {m.short}'s {m.live}" in pages[2] or f"of {F.kit.poss(m.short)} {m.live}" in pages[2], pages[2][:300])

# ---- one small competitor keeps the one-name wording; a competitor of 20 or more is not called small
def one_small(s):
    pass
doc, r = K.build(sp([5, 25, 30]))
t = F.page_text(doc)
check("one small competitor: the one-name line, not naming the large ones",
      all("Small sample: Vrbo has 5 live ads in this line, so read this as a direction." in t[n - 1] for n in (1, 3, 4))
      and "Inspirato has 25" not in " ".join(t), t[0][-200:])
doc, r = K.build(sp([25, 5, 30], edit=lambda s: s.update(compare="Vrbo")))
t = F.page_text(doc)
check("a large compare with a small competitor beside it: the line names only the small one",
      "Small sample: Inspirato has 5 live ads in this line, so read this as a direction." in t[0], t[0][-200:])

# ---- refusals
out = problems(sp([4, 6, 12]))
check("a directional competitor with 4 ads is refused, naming the floor of 5",
      "has 4 live guest ads" in out and "needs at least 5" in out, out[:400])
out = problems(sp([12, 12, 12], sample="standard"))
check("a standard competitor with 12 ads is refused for the 20 minimum", "needs at least 20" in out and "has 12 live guest ads" in out, out[:400])
out = problems(sp([12, 12, 12], sample=None, edit=lambda s: s.pop("sample")))
check("no sample field: 12 ads is refused for the 20 minimum, as before", "needs at least 20" in out, out[:400])
out = problems(sp([5, 6, 12], sample="small"))
check("an unknown sample value is refused", "sample 'small' must be one of 'standard', 'directional'" in out, out[:400])
out = problems(sp([5, 6, 12], sample="Directional"))
check("sample is case sensitive: 'Directional' is refused", "must be one of" in out, out[:400])
out = problems(sp([5, 6, 12], edit=lambda s: s["brands"][0].update(ads=[])))
check("the brand's own minimum is unchanged: a brand with no live ads is still refused", "no live guest ads" in out, out[:300])


# ---- page 4 on tiny samples: launches in the window
def launches(k):
    """Make the compare competitor launch exactly k ads in the window; the rest started before it."""
    def edit(s):
        old_day = "2026-01-05T00:00:00+00:00"
        ads = s["brands"][1]["ads"]
        for i, a in enumerate(ads):
            a["start_date"] = ("2026-10-01T00:00:00+00:00" if i < k else old_day)
    return edit


for k in (3, 5):
    s = sp([12, 12, 12], edit=launches(k))
    doc, r = K.build(s)
    p4 = F.page_text(doc)[3]
    rival = r.c
    if k == 3:
        check("3 launches: page 4 says they launched too few to compare", "launched 3 ads since" in p4 and "too few to compare" in p4, p4[:700])
        check("3 launches: no weeks bar for the competitor", f"{rival.short}, " not in re.sub(r"\s+", " ", re.findall(r"Weeks to launch.*?(?:How many live ads)", p4)[0]), p4)
        check("3 launches: no division result is printed (no weeks figure for them)",
              not re.search(rf"{re.escape(rival.short)}, \d+(?:\.\d)? a week \d+ weeks", p4), p4)
        check("3 launches: the brand's bar stays", "You, " in p4 and re.search(r"You, [\d.]+ a week \d+ weeks", p4) is not None, p4)
        check("3 launches: the chart label says too few", "launched too few ads to compare" in doc)
    else:
        check("5 launches: page 4 keeps the weeks bar", "too few to compare" not in p4 and f"{rival.short}, " in p4, p4[:700])

# the same 3 launches in a standard report: today's page, unchanged by this change
s = F.spec()
launches(3)(s)
doc, _ = K.build(s)
check("standard spec: page 4 is not changed by the launch guard", "too few to compare" not in doc)

# ---- A4 fit of the directional builds, when Chromium runs here (the kit's own measure(); None means no browser)
for label, spec_ in (("5, 6 and 12 ads", sp([5, 6, 12])), ("12, 12 and 12 ads, 3 launches", sp([12, 12, 12], edit=launches(3)))):
    doc, _ = K.build(spec_)
    fit = K.measure(doc)
    if fit is None:
        print(f"SKIP page fit, {label}: no browser here")
    else:
        check(f"directional {label}: five pages, each within A4, no broken image, no sideways scroll", fit == [], fit)

# ---- a brand name that carries digits ("5.11 Tactical") is not "digits typed by hand" in alt text or lines
def rename(s):
    new = "5.11 Tactical"
    old = s["brand"]["name"]
    s["brand"]["name"] = new
    s["brands"][0]["name"] = new
    for x in s["p3_ads"]:
        if x["brand"] == old:
            x["brand"] = new
        x["alt"] = x["alt"].replace(old, new)
    s["text"]["p1"]["alt"] = "Your 5.11 Tactical ad in Big Sky: a great room with a long dining table under wood beams."
out = problems(sp([5, 6, 12], edit=rename))
check("brand name with digits: no digits-typed-by-hand problem", "digits typed by hand" not in out, out[:400])
doc, _ = K.build(sp([5, 6, 12], edit=rename))
check("brand name with digits prints as written in the header and title", '>5.11 Tactical</div>' in doc and "<title>5.11 Tactical Meta ads report</title>" in doc)
out = problems(sp([5, 6, 12], edit=lambda s: s["text"]["p1"].update(works="You run 62 ads.")))
check("other digits typed by hand are still refused", "digits typed by hand in text.p1.works" in out, out[:300])

# ---- other directional shapes in the browser: other platforms, 18-character names, three competitors of exactly 5 ads
def small_pages(doc):
    """Which pages (1 to 5) carry the small-sample line."""
    return [i for i, t in enumerate(F.page_text(doc), 1) if "Small sample:" in t]


def fits(label, s, who=None):
    out = problems(s)
    check(f"{label}: no problem", not out, out[:600])
    if out:
        return
    doc, r = K.build(s)
    check(f"{label}: footer on pages 1, 3 and 4 only", small_pages(doc) == [1, 3, 4], small_pages(doc))
    if who:
        foot = re.sub(r"\s+", " ", re.findall(r"Small sample:.*?direction\.", F.page_text(doc)[3])[0])
        check(f"{label}: page 4 footer names {', '.join(who)}", all(w in foot for w in who), foot)
    fit = K.measure(doc)
    if fit is None:
        print(f"SKIP page fit, {label}: no browser here")
    else:
        check(f"{label}: five pages, each within A4, no broken image, no sideways scroll at 375 px", fit == [], fit)


BENCH = F.benchmarks()
for plat in ("TIKTOK", "GOOGLE", "LINKEDIN"):
    fits(f"directional on {plat}, 5, 6 and 12 ads",
         F.on(plat, BENCH[plat], F.RULES[plat], lambda s: (s.update(sample="directional"), trim(s, [5, 6, 12]))))

LONG = ("Alpine Stays Group", "Summit Lodge Rents", "Valley Home Rental")


def long_shorts(s):
    for b, short in zip(s["brands"][1:], LONG):
        b["short"] = short


def reach(doc):
    """At 375 px: (A4 problems from measure(), footers wider than the phone, elements past the phone that no overflow box clips,
    as 'ancestor class' strings). None when no browser runs here."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            try:
                pg = b.new_page(viewport={"width": 375, "height": 800})
                pg.set_content(doc, wait_until="networkidle")
                feet = pg.evaluate("[...document.querySelectorAll('footer')].filter(f => f.scrollWidth > f.clientWidth + 1 || f.getBoundingClientRect().right > 376).length")
                past = pg.evaluate("""() => [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > 376
                    && ![...Array(9)].reduce((a, _, i) => a.el && a.el.parentElement ? {el: a.el.parentElement, c: a.c || (a.el.parentElement !== document.documentElement && getComputedStyle(a.el.parentElement).overflowX !== 'visible')} : a, {el: e, c: false}).c)
                    .map(e => e.closest('.bars') ? 'bars' : e.closest('footer') ? 'footer' : e.tagName)""")
            finally:
                b.close()
    except Exception:
        return None
    return feet, sorted(set(past))


# 18-character names: the footer wraps inside the phone and the A4 pages. The page 3 bar rows (grid of max-content columns) are
# wider than a 375 px phone with names this long in a standard report too (21 px there, 4 px here); that is not the footer's.
check("the three test names are 18 characters", [len(x) for x in LONG] == [18, 18, 18])
for label, edit in (("", long_shorts), (", 3 launches", lambda s: (long_shorts(s), launches(3)(s)))):
    s = sp([5, 6, 12], edit=edit)
    real, K.measure = K.measure, lambda doc, notes=None: []
    try:
        doc, _ = K.build(s)
    finally:
        K.measure = real
    check(f"directional, three 18-character names{label}: footer on pages 1, 3 and 4 only", small_pages(doc) == [1, 3, 4], small_pages(doc))
    foot = re.sub(r"\s+", " ", re.findall(r"Small sample:.*?direction\.", F.page_text(doc)[3])[0])
    check(f"directional, three 18-character names{label}: page 4 footer names all three", all(w in foot for w in LONG), foot)
    fit, seen = real(doc), reach(doc)
    if fit is None or seen is None:
        print("SKIP page fit, 18-character names: no browser here")
        continue
    check(f"directional, three 18-character names{label}: five pages, none past A4", not [x for x in fit if "px tall" in x or "pages" in x or "load" in x], fit)
    check(f"directional, three 18-character names{label}: no footer wider than a 375 px phone", seen[0] == 0, seen)
    check(f"directional, three 18-character names{label}: the only thing past the phone is the page 3 bar rows", seen[1] == ["bars"], seen)
fits("directional, three competitors of exactly 5 ads", sp([5, 5, 5]), ("Vrbo", "Airbnb", "Inspirato"))

sys.exit(1 if fails else 0)
