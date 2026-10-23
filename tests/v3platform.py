"""v3 on TikTok, Google and LinkedIn, offline. Meta without a platform key renders byte for byte as the a04b115ebc4a kit
did (tests/fixtures/base-kit-a04b115ebc4a.py, a copy of the hosted kit: make_skill_v3.py deletes older dist kits); a TikTok, Google or LinkedIn spec prints its own platform's name, footers,
benchmark count and caveat; one platform per report; a missing start date, copy or landing page is not a refusal.
Run: python3 tests/v3platform.py"""
import copy
import hashlib
import json
import re
import sys
import types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import v3fixture as F

K = F.kit
fails = 0


def check(label, ok, detail=""):
    global fails
    fails += not ok
    print(("OK   " if ok else "FAIL ") + label, "" if ok else detail)


B = F.benchmarks()
check("benchmark accounts: Meta 85, TikTok 19, Google 13, LinkedIn 1",
      [B[p]["accounts"] for p in B] == [85, 19, 13, 1], [B[p]["accounts"] for p in B])
check("caveat under 85, none under 10", [(B[p]["caveat"], B[p]["none"]) for p in B]
      == [(False, False), (True, False), (True, False), (True, True)], [(B[p]["caveat"], B[p]["none"]) for p in B])
check("window kept", B["TIKTOK"]["window"] == "9 Aug 2026 to 7 Sep 2026", B["TIKTOK"]["window"])
check("one account has no slope to fit", B["LINKEDIN"]["fit"]["slope"] == 0.0, B["LINKEDIN"]["fit"])


# ---- Meta is unchanged: the a04b115ebc4a kit and this one print the same bytes for the fixture
base_src = (Path(__file__).resolve().parent / "fixtures" / "base-kit-a04b115ebc4a.py").read_bytes()
check("base kit is a04b115ebc4a", hashlib.sha256(base_src).hexdigest().startswith("a04b115ebc4a"))
base = types.ModuleType("base_kit")
exec(base_src.decode(), base.__dict__)
base._fonts = K._fonts
want, _ = base.build(F.spec())
got, _ = K.build(F.spec())
check("Meta output is byte-identical to a04b115ebc4a", got == want, f"{len(got)} vs {len(want)} bytes")


on = F.on
RULES = F.RULES
for plat in ("TIKTOK", "GOOGLE", "LINKEDIN"):
    nm = K.PLATFORMS[plat]["name"]
    doc, r = K.build(on(plat, B[plat], RULES[plat]))
    text = " ".join(F.page_text(doc))
    check(f"{nm}: h1, lede, title", f"What do your {nm} ads sell?" in text and f"Your 62 live {nm} ads, next to" in text
          and f"<title>Natural Retreats {nm} ads report</title>" in doc)
    check(f"{nm}: footer names the library and the rule", f"{K.PLATFORMS[plat]['library']}, live = {RULES[plat]}, October 21, 2026." in text)
    first4 = " ".join(F.page_text(doc)[:4])  # page 5 keeps Crux's fixed Cloaked case study, which says Meta
    check(f"{nm}: no Meta on pages 1 to 4", "Meta" not in first4, re.findall(r".{30}Meta.{20}", first4)[:2])
    check(f"{nm}: summary names the platform", r.summary().startswith(f"platform: {nm};"), r.summary()[:60])

doc, _ = K.build(on("TIKTOK", B["TIKTOK"], RULES["TIKTOK"]))
t = " ".join(F.page_text(doc))
check("TikTok: caveat shows the real count and window",
      "Based on 19 TikTok accounts on Crux that pay in US dollars, 9 Aug 2026 to 7 Sep 2026. A small sample, a guide only." in t)
check("TikTok: the $100K+ bar says how many accounts", "the middle of 7 TikTok accounts at $100K+ a month" in t and "Typical at $100K+" in t)
check("TikTok: footer counts TikTok accounts", "19 TikTok ad accounts on Crux that pay in US dollars" in t)
doc, _ = K.build(on("GOOGLE", B["GOOGLE"], RULES["GOOGLE"]))
t = " ".join(F.page_text(doc))
check("Google: caveat 13, bar 4, image and video only",
      "Based on 13 Google accounts" in t and "the middle of 4 Google accounts" in t and "Image and video ads only." in t)
doc, r = K.build(on("LINKEDIN", B["LINKEDIN"], RULES["LINKEDIN"]))
t = " ".join(F.page_text(doc))
check("LinkedIn: no benchmark, no typical bar, the too-few line",
      "No spend benchmark: Crux has 1 LinkedIn account that pay in US dollars, too few to show." in t.replace("pay", "pay")
      and "Typical at $100K+" not in t and 'class="bench"' not in doc, t[t.find("How many ads"):][:500])
check("LinkedIn: three bars, dated pull", "Pulled from LinkedIn's ad library on October 21, 2026." in t
      and doc.count('class="ht"') >= 0 and r.ctx["t100"].n == 0)
check("LinkedIn: page 2 answer carries no benchmark claim", "typically run" not in t.split("What do competitors")[0].split("How many ads")[1])

# a platform with no accounts at $100K+ drops the bar, not the chart
b0 = copy.deepcopy(B["GOOGLE"])
b0["points"] = [p for p in b0["points"] if p[0] < 1e5]
doc, r = K.build(on("GOOGLE", b0, RULES["GOOGLE"]))
check("no account at $100K+: no typical bar, chart stays", "Typical at $100K+" not in doc and 'class="bench"' in doc and r.ctx["t100"].n == 0)


# ---- refusals
def refused(label, s, needle):
    try:
        K.build(s)
        check(label, False, "built")
    except ValueError as e:
        check(label, needle in str(e), str(e)[:300])


def mixed(s):
    for a in s["brands"][1]["ads"][:3]:
        a["platform"] = "META"
refused("a Meta ad in a TikTok report is refused", on("TIKTOK", B["TIKTOK"], RULES["TIKTOK"], mixed),
        "Vrbo: 3 ads are from Meta, not TikTok: count one platform per report")
refused("an unknown platform is refused", on("TIKTOK", B["TIKTOK"], RULES["TIKTOK"], lambda s: s.update(platform="SNAP")),
        "platform 'SNAP' must be one of")
refused("a non-Meta platform needs live_rule", on("TIKTOK", B["TIKTOK"], "", None), "spec needs live_rule on TikTok")


def thin(s):
    s["brands"][2]["ads"] = s["brands"][2]["ads"][:10]
refused("a rival under 20 ads names the platform", on("GOOGLE", B["GOOGLE"], RULES["GOOGLE"], thin),
        "a competitor on Google needs at least 20")
refused("no live ads names the platform", on("TIKTOK", B["TIKTOK"], RULES["TIKTOK"], lambda s: s["brands"][0].update(ads=[])),
        "no live guest ads on TikTok: take the brand's next platform")


# ---- missing fields are normal off Meta
def nostart(s):
    for a in s["brands"][0]["ads"][:6]:
        a.pop("start_date")
doc, r = K.build(on("TIKTOK", B["TIKTOK"], RULES["TIKTOK"], nostart))
t = " ".join(F.page_text(doc))
check("ads with no start date build and the page-4 footer counts them",
      r.M[0].no_start == 6 and "6 live ads show no start date and are not in the pace." in t, t[-300:])
check("no start date: the ads still count as live", r.M[0].live == 62)
check("Meta page-4 footer has no start-date line", "no start date" not in " ".join(F.page_text(K.build(F.spec())[0])))


def nocopy(s):
    for b in s["brands"]:
        for a in b["ads"]:
            for k in ("landing_page_url", "tracking_url", "end_date", "bodies", "titles"):
                a.pop(k, None)
K.build(on("GOOGLE", B["GOOGLE"], RULES["GOOGLE"], nocopy))
check("ads with no copy, landing page, tracking url or end date build", True)

sys.exit(1 if fails else 0)
