"""Edge cases of the v3 kit, offline: a brand with many live ads (page 1 draws a bar, not 62 marks), no launch in the 90
days, a quiet competitor, ended ads, a line-up past 700 ads, a count in words ("1 in 5", "almost all"), a long
competitor name on the speed chart, a brand with no logo. Run: python3 tests/v3edge.py"""
import copy
import datetime as dt
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


def built(edit):
    s = F.spec()
    edit(s)
    return K.build(s)


# in_n: a share in the words a marketer says
check("in_n", [K.in_n(k, n) for k, n in ((0, 5), (12, 62), (151, 209), (62, 62), (5, 10), (1, 50))]
      == ["none", "1 in 5", "7 in 10", "almost all", "5 in 10", "1 in 50"], [K.in_n(12, 62), K.in_n(151, 209)])


# a brand with 120 live ads: page 1 shows a bar, every count still comes from the rows
def big(s):
    b = s["brands"][0]
    b["ads"] = b["ads"] + copy.deepcopy(b["ads"])
    for i, a in enumerate(b["ads"]):
        a["ad_id"] = f"{a['ad_id']}-{i // 62}"
    s["p1_ad"] = "4213052325638037-0"
    s["p3_ads"][0]["ad_id"] += "-0"
doc, r = built(big)
check("120 live ads: a bar, not 120 marks", 'class="fbar"' in doc and 'class="strip"' not in doc)
check("120 live ads: the finding counts every ad", "<em>104 of your 124</em>" in doc and r.M[0].live == 124, r.M[0].live)

# no launch in the window
def quiet(s):
    for a in s["brands"][0]["ads"]:
        a["start_date"] = "2026-03-01T07:00:00+00:00"
try:
    built(quiet)
    check("no launch in 90 days is refused", False, "built")
except ValueError as e:
    check("no launch in 90 days is refused", "launched no ads since July 24" in str(e), str(e)[:200])

# a competitor with no big week: page 4 names its weekly pace, not a one-week jump
def steady(s):
    v = s["brands"][1]["ads"]
    for i, a in enumerate(v):
        a["start_date"] = (dt.date(2026, 7, 24) + dt.timedelta(days=(i * 89) // len(v))).isoformat() + "T07:00:00+00:00"
doc, r = built(steady)
check("a steady competitor: answer names its weekly pace", re.search(r"Vrbo launched about \d+\.\d a week", doc) is not None
      and "in one week" not in re.search(r'<h1>How often.*?</p>', doc, re.S).group(0))
check("a steady competitor: the chart has no one-week note", "in one week</text>" not in doc)

# ended ads are not live ads
def ended(s):
    for a in s["brands"][1]["ads"][:9]:
        a["end_date"] = "2026-10-01"
doc, r = built(ended)
check("ended ads leave the count", r.M[1].live == 200 and "209" not in re.search(r'How many you run.*?Live ads', doc, re.S).group(0), r.M[1].live)

# a line-up past 700 live ads
def huge(s):
    s["brands"][1]["ads"] = [copy.deepcopy(a) for _ in range(4) for a in s["brands"][1]["ads"]]
    for i, a in enumerate(s["brands"][1]["ads"]):
        a["ad_id"] = f"{a['ad_id']}-{i}"
s = F.spec()
huge(s)
out = K.precheck(s)
check("a line-up past 700 live ads is refused", any("past the 700 one run can tag" in x for x in out), out)

# a brand with no ads under 30 days: the ring sentence
def old(s):
    for a in s["brands"][0]["ads"]:
        if (dt.date(2026, 10, 21) - dt.date.fromisoformat(a["start_date"][:10])).days <= 30:
            a["start_date"] = "2026-09-01T07:00:00+00:00"
doc, r = built(old)
check("no ad under a month old: 'None of your live ads'", "None of your live ads is under a month old." in doc, r.M[0].last30)

# a long competitor name does not run off the speed chart
def longname(s):
    s["brands"][1]["name"] = "Southern New Hampshire University"
    s["compare"] = "Southern New Hampshire University"
    for x in s["p3_ads"]:
        if x["brand"] == "Vrbo":
            x["brand"] = "Southern New Hampshire University"
doc, r = built(longname)
check("a long competitor name widens the label room", 'viewBox="0 0 666 200"' in doc and "Southern New Hampshire University 163" in doc)

# no logo: the header prints the name
def nologo(s):
    s["brand"].pop("logo")
    s["brand"]["logo_missing"] = "header, schema, og:image: none loaded"
doc, r = built(nologo)
check("no logo: the name stands alone", '<div class="brand">Natural Retreats</div>' in doc and any("no logo" in f for f in r.brand["flags"]))

# a wide wordmark logo is drawn as a wordmark, with the name only in alt
def wide(s):
    from PIL import Image
    p = F.HERE / "out" / "wide-logo.png"
    p.parent.mkdir(exist_ok=True)
    im = Image.new("RGB", (400, 80), "white")
    for x in range(40, 360):
        for y in range(20, 60):
            im.putpixel((x, y), (20, 20, 20))
    im.save(p)
    s["brand"]["logo"] = str(p)
doc, r = built(wide)
check("a wide logo: wordmark, no name beside it", 'class="brand-logo"' in doc and 'class="brand-mark"' not in doc)

# a white wordmark with a dark gradient mark (TalkRemit, v3 check 2026-10-22) is a light logo: it gets a tile, not a bare
# white print on a light page
def whitelogo(s):
    s["brand"]["logo"] = str(F.FIX / "talkremit-logo.svg")
doc, r = built(whitelogo)
check("a white logo with a dark gradient is set on a tile", 'class="brand-logo" style="background:' in doc
      and any("light logo set on a" in f for f in r.brand["flags"]), r.brand["flags"])
check("a dark logo gets no tile", K._svg_lum('<svg viewBox="0 0 10 10"><path d="M0 0h10v10z" fill="#111"/></svg>') < .1)

# the buyer word: "sender" for a remittance brand, "guest" when none is given
def sender(s):
    s["buyer"] = "sender"
doc, r = built(sender)
check("buyer 'sender': new-sender ads, one per sender", "You with new-sender ads" in doc and "Ads for new senders would take you" in doc
      and "one per sender" in doc and "new-guest" not in doc)
check("no buyer: guests, as the mock", "You with new-guest ads" in built(lambda s: None)[0])

# a short display name: the pages print it, not the long legal name (UMass Global's check build, 2026-10-22: Western Governors
# University and Southern New Hampshire University wrapped and pushed pages past A4)
def shortnames(s):
    s["brands"][1]["short"] = "VRBO"
doc, r = built(shortnames)
check("a short name is printed for the competitor", "VRBO, of 209" in doc and ">VRBO<" in doc and "next to VRBO&#x27;s" in doc
      and "Vrbo, of" not in doc)
check("the page tightens itself when it runs past A4", "classList.add('tight')" in doc and ".page.tight" in doc and ".page.tighter" in doc)
check("a tall ad is capped, not shown at full height", ".ads .ad img { width: auto; max-width: 100%; max-height: 240px; }" in doc)

# no Natural Retreats text in a different brand's report: the kit holds no brand copy of its own
def other(s):
    s["brand"]["name"] = "Acme Stays"
    s["brands"][0]["name"] = "Acme Stays"
    for x in s["p3_ads"]:
        if x["brand"] == "Natural Retreats":
            x["brand"] = "Acme Stays"
            x["alt"] = x["alt"].replace("Natural Retreats", "Acme Stays")
doc, r = built(other)
check("the kit holds no Natural Retreats copy", doc.count("Natural Retreats") == 0, doc.count("Natural Retreats"))
sys.exit(1 if fails else 0)
