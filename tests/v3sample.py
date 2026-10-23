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
    line = f"Small sample: {c.short} has {c.live} live ads in this line, so read this as a direction."
    for n in (1, 3, 4):
        check(f"page {n} carries the footer line with the real count ({c.live})", line in pages[n - 1], pages[n - 1][-250:])
    for n in (2, 5):
        check(f"page {n} has no small-sample line", "Small sample" not in pages[n - 1])
    check("five pages", len(pages) == 5)
    # page 3 shows every competitor's real count in the chart
    for m in r.M[1:]:
        check(f"page 3 chart prints {m.short}'s {m.live} live ads", f"of {m.short}'s {m.live}" in pages[2] or f"of {F.kit.poss(m.short)} {m.live}" in pages[2], pages[2][:300])

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

sys.exit(1 if fails else 0)
