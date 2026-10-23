"""The Natural Retreats report as the v3 kit's regression fixture: the 10/21 GetCrux ads (62, Vrbo 209, Inspirato 31,
Airbnb 43, tagged by the copilot) and the text Kevin signed off on 10/22. Offline: the benchmark, the logo and the five
ad pictures are saved in tests/fixtures. KIT=kit_embedded_v3 runs a test against the embedded copy."""
import copy
import importlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
kit = importlib.import_module(os.environ.get("KIT", "build_kit_v3"))
kit._fonts = lambda *a, **k: (Path(__file__).resolve().parent / "fixtures" / "fonts.css").read_text()  # no download in tests
FIX = HERE / "fixtures"
PICS = ("4213052325638037", "1999058320801488", "2388818754857340", "1419605176367025", "1450952986900283")


def spec():
    brands = json.loads((FIX / "nr-ads.json").read_text())
    for b in brands:
        b["market"] = "US"
    brands[0]["dropped"], brands[0]["dropped_why"] = 14, "owners and realtors"
    for b in brands:
        for a in b["ads"]:
            if a["ad_id"] in PICS:
                a["image"] = str(FIX / f"{a['ad_id']}.jpg")
    return {
        "as_of": "2026-10-21", "rep": "Kevin Tran", "rep_email": "kevin.tran@getcrux.ai",
        "calendly": "https://calendly.com/atharva-getcrux/30min",
        "brand": {"name": "Natural Retreats", "accent": "#56755E", "logo": str(FIX / "nr-logo.png")},
        "brands": brands, "compare": "Vrbo", "merge": {},
        "benchmark": json.loads((FIX / "bench.json").read_text()),
        "focus": {"audience": "mountain vacation guests", "phrase": "a mountain getaway", "short": "A mountain trip",
                  "other": "Another trip"},
        "named": ["families and groups", "long stay travelers", "family vacation guests"],
        "named_phrase": "families, groups or longer stays", "named_one": "a family, a group or a longer stay",
        "one_home": {"tag": "explore a named vacation home", "unit": "home"},
        "guests": [
            {"who": "families", "one": "a family", "title": "For a family ski week",
             "hook": "Ski all day. Then the whole family by the fire."},
            {"who": "groups", "one": "a group", "title": "For a group of friends", "hook": "One home for the whole crew."},
            {"who": "longer stays", "one": "a longer-stay", "title": "For a longer stay",
             "hook": "Stay the month, not the weekend."}],
        "p1_ad": "4213052325638037",
        "p3_ads": [
            {"ad_id": "1999058320801488", "brand": "Natural Retreats", "for": "Built for a mountain trip",
             "alt": "Natural Retreats ad: a living room with a stone fireplace and mountain view, Spanish Peaks, Big Sky."},
            {"ad_id": "2388818754857340", "brand": "Vrbo", "for": "Built for families and groups",
             "alt": "Vrbo ad: a wood cabin among ferns, lit up at dusk."},
            {"ad_id": "1419605176367025", "brand": "Vrbo", "for": "Built for a longer stay",
             "alt": "Vrbo ad: a yellow A-frame house with a deck."},
            {"ad_id": "1450952986900283", "brand": "Airbnb", "for": "Built for a family vacation",
             "alt": "Airbnb ad: a parent lifts a child in a pool beside a thatched house."}],
        "text": {
            "p1": {"answer": "Beautiful homes, for one kind of trip: a mountain getaway.",
                   "alt": "Your Crail Creek ad in Big Sky: a great room with a long dining table under wood beams.",
                   "caption": "Crail Creek: one home, like most of your ads.",
                   "works": "The mountains are what you sell.",
                   "pitfall": "No ad names a family or group, so Meta can't find them.",
                   "try": "One ad for a family ski week, made from a home ad you already run.",
                   "reasons_note": "A specific home, a mountain escape, a destination."},
            "p3": {"answer": "They say who the trip is for, not just where.",
                   "opportunity": "Keep the home in each ad, and add who the trip is for."},
            "p5": {"answer": "Make your home ads into ads for new guests, in your own style."}},
    }


def build(**edit):
    """(html, report) for the fixture, after `edit(spec)` when given."""
    sp = spec()
    if edit.get("edit"):
        edit["edit"](sp)
    return kit.build(sp)


def page_text(doc):
    """Visible text of each page, pictures and charts by their alt and aria labels, as the parity test compares them."""
    import html as H
    import re
    doc = re.sub(r"<style.*?</style>", "", doc, flags=re.S)
    out = []
    for p in re.findall(r'<section class="page.*?</section>', doc, flags=re.S):
        p = re.sub(r'(?:alt|aria-label)="([^"]*)"', r" ALT[\1] ", p)
        p = re.sub(r"<svg.*?</svg>", lambda m: " SVG[" + " ".join(re.findall(r"ALT\[([^\]]*)\]", m.group(0))[:1]) + "] ", p, flags=re.S)
        out.append(re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", p))).strip())
    return out


# ---- the benchmark file, as the real one is shaped: 85 / 19 / 13 / 1 USD accounts, 34 / 7 / 4 / 1 at $100K+
def rows():
    out = []
    for plat, n, big in (("FACEBOOK", 85, 34), ("TIKTOK", 19, 7), ("GOOGLE", 13, 4), ("LINKEDIN", 1, 1)):
        for i in range(n):
            out.append({"platform": plat, "currency": "USD", "spend_30d": (150000 + 1000 * i) if i < big else (2000 + 700 * i),
                        "active_ads": 20 + 9 * i})
    out.append({"platform": "TIKTOK", "currency": "EUR", "spend_30d": 5000, "active_ads": 4})
    out.append({"platform": "GOOGLE", "currency": "USD", "spend_30d": 0, "active_ads": 4})
    return out


def _bench_page():
    return "window: 9 Aug 2026 to 7 Sep 2026\nvar ROWS = " + json.dumps(rows()) + ";"
def benchmarks():
    """load_benchmark for each platform from the synthetic file above (85 / 19 / 13 / 1 accounts)."""
    orig = kit._get
    kit._get = lambda url, timeout=30: _bench_page().encode()
    try:
        return {p: kit.load_benchmark(platform=p) for p in ("META", "TIKTOK", "GOOGLE", "LINKEDIN")}
    finally:
        kit._get = orig


# ---- a spec on another platform: rows shaped like the TikTok and Google ads seen 10/23 (no bodies, no landing page)
def on(plat, bench, rule, edit=None):
    s = spec()
    s["platform"], s["live_rule"], s["benchmark"] = plat, rule, bench
    s["text"]["p1"]["pitfall"] = "No ad names a family or group, so no family can tell a trip is for them."
    for b in s["brands"]:
        for a in b["ads"]:
            a["platform"] = plat
            a["start_date"] = a["start_date"][:10] + "T00:00:00+00:00"
            a.pop("landing_page_url", None)
            a.pop("bodies", None)
    if edit:
        edit(s)
    return s


RULES = {"TIKTOK": "seen in the last 7 days", "GOOGLE": "shown in the last 3 days", "LINKEDIN": "in LinkedIn's ad library on the day it was pulled"}
