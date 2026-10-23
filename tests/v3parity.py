"""The v3 kit renders the five-page Natural Retreats report Kevin signed off on 10/22 (.scratch/report-mocks-2026-10-21/
mock.html): every page's text, every chart label and every number equal the mock's (tests/fixtures/mock-pages.json), from
the 10/21 ad rows and the benchmark alone. Offline. Run: python3 tests/v3parity.py"""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import v3fixture as F

fails = 0


def check(label, ok, detail=""):
    global fails
    fails += not ok
    print(("OK   " if ok else "FAIL ") + label, detail if not ok else "")


doc, r = F.build()
mock = json.loads((F.FIX / "mock-pages.json").read_text())
got = F.page_text(doc)
check("five pages", len(got) == 5, len(got))
for i, (a, b) in enumerate(zip(mock, got), 1):
    check(f"page {i} text equals the mock", a == b, f"\n  mock: {a[:200]}\n  kit:  {b[:200]}")
M = {m.name: m for m in r.M}
nr, vr, ins, air = (M[n] for n in ("Natural Retreats", "Vrbo", "Inspirato", "Airbnb"))
want = [("live ads", (nr.live, vr.live, ins.live, air.live), (62, 209, 31, 43)),
        ("focus ads", nr.focus_n, 52), ("reasons", (nr.reasons, vr.reasons), (3, 5)),
        ("launched since July 24", (nr.n_new, vr.n_new), (32, 163)), ("busiest week", vr.peak, 103),
        ("last 30 days", (nr.last30, vr.last30), (12, 151)), ("one-home ads", nr.one_n, 45),
        ("named audience", (nr.named, vr.named, air.named, ins.named), (0, 65, 2, 0)),
        ("new ads", r.ctx["new_ads"], 135), ("total", r.ctx["total_ads"], 197),
        ("typical at $100K+", r.ctx["t100"].median, 101), ("pace", (nr.pace, vr.pace), (2.5, 12.6))]
for label, g, w in want:
    check(label, g == w, f"{g} != {w}")
check("weeks to launch 135 (you, Vrbo)", (round(135 / nr.pace), round(135 / vr.pace)) == (54, 11))
check("every page ends / 5", all(re.search(r"Prepared by Crux · %d / 5$" % n, t) for n, t in enumerate(got, 1)))
check("no em or en dash anywhere", not re.search("[—–]", re.sub(r'src="data:[^"]*"', "", doc)))
check("the booking button links to the spec's calendly", 'href="https://calendly.com/atharva-getcrux/30min"' in doc)
check("page 1 strip has 62 marks, 52 filled", doc.count('<i class="on"></i>') == 52 and doc.count("<i></i>") == 10)
sys.exit(1 if fails else 0)
