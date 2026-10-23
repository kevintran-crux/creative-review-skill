"""What the v3 kit refuses, and that it lists every problem at once. Offline. Run: python3 tests/v3refuse.py"""
import copy
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


def problems(edit):
    s = F.spec()
    edit(s)
    return K.precheck(s)


def has(label, edit, *needles):
    out = "\n".join(problems(edit))
    check(label, all(n in out for n in needles), out[:600])


check("the signed-off spec builds with no problem", problems(lambda s: None) == [])
has("a competitor under 20 live ads", lambda s: s["brands"][2].update(ads=s["brands"][2]["ads"][:10]), "Inspirato has 10 live guest ads")
has("compare must be a competitor", lambda s: s.update(compare="Nobody"), "compare 'Nobody'")
has("a digit typed by hand", lambda s: s["text"]["p1"].update(works="You run 62 ads."), "digits typed by hand in text.p1.works")
has("the brand's own name", lambda s: s["text"]["p3"].update(answer="Natural Retreats sells homes."), "names the brand")
has("rivals", lambda s: s["text"]["p3"].update(answer="Your rivals say who it is for."), "'rivals'")
has("spend words", lambda s: s["text"]["p1"].update(works="Your budget is well spent."), "'budget'", "'spent'")
has("performance words", lambda s: s["text"]["p1"].update(works="Your ads work and win."), "perform")
has("an em dash", lambda s: s["text"]["p1"].update(works="Homes — and trips."), "a dash")
has("a period with no dates", lambda s: s["text"]["p1"].update(works="You launched recently."), "'recently'")
has("a sentence past 20 words", lambda s: s["text"]["p3"].update(
    answer="They say who the trip is for and where the trip goes and when the trip starts and why the guest should go and how long."),
    "a sentence of")
has("focus audience on no ad", lambda s: s["focus"].update(audience="skiers"), "focus.audience 'skiers' is on none of your live ads")
has("one_home tag on no ad", lambda s: s["one_home"].update(tag="nothing"), "one_home.tag 'nothing'")
has("named tags on no ad", lambda s: s.update(named=["pirates"]), "named tags on no live ad")
has("two guests", lambda s: s.update(guests=s["guests"][:2]), "guests needs exactly 3")
has("a hook with a digit", lambda s: s["guests"][0].update(hook="Ski 5 days."), "digits typed by hand in guests[0].hook")
has("a hook with a performance word", lambda s: s["guests"][0].update(hook="The best ski week."), "'best'")
has("p3 ad of the wrong brand", lambda s: s["p3_ads"][1].update(brand="Airbnb"), "p3_ads[1]")
has("p3 ads count", lambda s: s.update(p3_ads=s["p3_ads"][:3]), "p3_ads needs exactly 4")
has("p3's first ad is the brand's", lambda s: s["p3_ads"].reverse(), "p3_ads[0] must be one of your own")
has("p1_ad not the brand's", lambda s: s.update(p1_ad="2388818754857340"), "p1_ad 2388818754857340 is not one of your live ads")
has("no market", lambda s: s["brands"][1].pop("market"), "Vrbo needs a market")
has("an untagged ad", lambda s: s["brands"][0]["ads"][0].pop("audience"), "have no reason_to_buy or audience")
has("an empty text field", lambda s: s["text"]["p3"].update(opportunity=""), "text.p3.opportunity is empty")
has("compare with no named-audience ad", lambda s: s.update(compare="Inspirato"), "Inspirato has no live ad tagged with a named audience")
has("no booking link", lambda s: s.pop("calendly"), "spec needs calendly")


def many(s):
    s["text"]["p1"]["works"] = "You run 62 ads."
    s["text"]["p3"]["answer"] = "Your rivals win."
    s["guests"] = s["guests"][:1]
    s["compare"] = "Nobody"
out = problems(many)
check("every problem at once", len(out) >= 4 and sum("\n" in x or True for x in out) >= 4, out)
try:
    s = F.spec()
    many(s)
    K.build(s)
    check("build raises", False, "built")
except ValueError as e:
    check("build raises one ValueError with all of them", "problems; fix them all" in str(e) or str(e).count("\n") > 3, str(e)[:300])
sys.exit(1 if fails else 0)
