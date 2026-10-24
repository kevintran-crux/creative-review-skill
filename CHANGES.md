# Changes: directional report for competitors with fewer than 20 live ads

Second round (10/23 copilot test of `creative-report-v3-directional-check`, 5.11 Tactical pants): the kit built the report with the
footer on pages 1, 3 and 4 and the page 4 "too few to compare" line, and the test showed two defects, both fixed below: only the
compare competitor was labelled small, and the brand name was respelled to dodge the digit check.

## Files

- `build_kit_v3.py`
  - New constants beside `MIN_RIVAL_ADS = 20`: `SMALL_SAMPLE_MIN = 5`, `SAMPLES = ("standard", "directional")`, `MIN_LAUNCHES = 5`.
  - Spec field `sample` (optional). Absent, `None` or `"standard"`: unchanged. `"directional"`: a competitor needs 5 live ads
    after set-asides; the brand's own minimum is unchanged.
  - `problems()`: refuses a `sample` that is not one of the two values; the competitor minimum is 5 when directional, and the
    message names the floor ("needs at least 5 even in a directional report"). The standard message is unchanged.
  - `small_note()`: "Small sample: {competitor} has {n} live ads in this line, so read this as a direction." Added to the
    footers of pages 1, 3 and 4 (the pages that set the compare competitor beside the brand). It names every competitor under
    20 with its own count, the compare competitor first ("Small sample: Propper has 15, LA Police Gear has 7 and First Tactical
    has 6 live ads in this line, so read this as a direction."). A competitor of 20 or more is not named; with none under 20 there
    is no line. (First version named only the compare competitor; the 10/23 copilot test showed the 7 and 6 left unlabelled.)
  - `lint()`: digits inside a brand's `name` or `short` no longer count as "digits typed by hand" (alt text such as "Your 5.11
    Tactical ad ..." was refused, and the copilot respelled the brand "Five Eleven Tactical" on the 10/23 test). Other digits are
    still refused. Output for a spec whose names carry no digits is unchanged.
  - Page 4: in a directional report, a competitor with fewer than `MIN_LAUNCHES` launches in the window gets one line ("{name}
    launched {n} ads since {date}, too few to compare.") in place of its weeks bar; the brand's bar stays, scaled to itself, and the
    chart's aria label says so. No weeks figure is computed for it on the page.
- `SKILL_v3.src.md`
  - New hard rule in "Rules for every word": only the kit builds the report; never write the HTML or build a file `save_check`
    did not save; if the kit refuses, say what it refused and stop.
  - Stage 1 step 4: when no line-up reaches 20, show the counts and offer the directional report ("build with at least 5 live ads
    each, labelled as a small sample"); the rep's "build it anyway" means this choice and nothing else.
  - Stage 1: new stop-list item for that choice; the proposal row, the "after the rep's yes" recount and the Stage 2 set-aside
    rule name 5 for a directional report; "A report is never impossible" line mentions the choice.
  - Stage 1 zero-ad imports: a competitor that imports with 0 live ads is checked against the Meta Ad Library page before it is
    replaced, and the flags say what was found. Text only.
  - Stage 4 setup list: `sample`. Stage 6 refusal list: the 5 floor and the `sample` values.
  - Stage 6 and the Stage 7 checklist: names are written exactly as the brand writes them ("5.11 Tactical", never "Five Eleven
    Tactical"); never respell a name to get past a check.
- `tests/v3sample.py` (new): the tests below.
- `tests/fixtures/base-kit-current.py` (new): copy of the unmodified `build_kit_v3.py`, saved before editing.
- `CHANGES.md` (this file).

Not changed: page 2 and page 3's charts (see "Checked"), `make_skill_v3.py`, `v3_static.py`, other tests.

## Checked for breakage with 5 to 12 ads

- Page 2 bars: widths are a share of the largest of the brand, the benchmark, the new total and the competitor, so a 5-ad
  competitor draws a short bar and nothing divides by it. No change.
- Page 3 named-guest chart: the share is named / live, which is safe for any live >= 1; rows sort by share. The existing refusal
  (compare has no named-audience ad) still applies. No change.
- Page 4 rings and the "1 in N" wording: fine at 5 to 12 ads. The line chart and its axis step are fine.
- Page 4 weeks to launch: this is what broke (2 launches in 90 days is hundreds of weeks). Guarded as above.
- The guard runs only in a directional report, so a standard report prints exactly what it did. A standard report whose compare
  competitor launched under 5 ads in the window still shows a large weeks figure, as before; not changed because the spec says
  standard output stays byte for byte.

## Tests (offline)

`for t in v3parity v3refuse v3edge v3checkcap v3platform v3sample; do python3 tests/$t.py; done`

- Without Chromium (as the repo's tests assume): all six pass.
- `v3sample.py` (34 checks): default and `"standard"` specs equal the baseline kit's output byte for byte on the Natural Retreats fixture;
  directional with competitors of 5, 6 and 12 ads builds, prints the real counts and the footer line on pages 1, 3 and 4 (and not
  on 2 or 5); 4 ads in a directional spec is refused naming the floor of 5; 12 ads in a standard spec (and with no `sample`) is
  refused for the 20 minimum; an unknown or wrongly cased `sample` is refused; a brand with no live ads is still refused; 3
  launches in the window gives the "too few to compare" line and no weeks bar for the competitor, 5 launches keeps the bar, and a
  standard spec with 3 launches is unchanged.

## Page fit and browser

Chromium ran here (installed Chromium 1243 pointed at Playwright 1.57 through symlinks in the session's scratchpad, nothing in the
repo). With it:

- `tests/v3browser.py`: passes (24 checks: Meta, TikTok, Google, LinkedIn fixtures). It does not build a directional spec.
- `v3sample.py` also runs the kit's own `measure()` on two directional builds (5, 6, 12 ads; and 12, 12, 12 ads with 3 launches):
  five pages, none past A4 height, no broken image, no sideways scroll at 375 px. I looked at page 4 of the 3-launch build; the
  footer line wraps to a second line and fits.
- `tests/v3edge.py` fails with Chromium present, with or without my change ("the page scrolls sideways by 240 px on a 375 px
  phone", in the long-name test, line 97). I checked by running it on the unmodified kit. It passes without a browser. Not fixed.

## Not measured

- `tests/v3loader.py` (needs a local port and an installed skill file); the installable skill (`make_skill_v3.py` writes a draft
  only: `python3 make_skill_v3.py --draft` runs).
- No copilot run against the new skill text: the Stage 1 wording is untested with a rep.
- The cause of the two zero-ad imports (First Tactical, VIKTOS) is not looked at; the skill change is text only.
- Competitor names with 18 characters were measured only at 5, 6 and 12 ads (with and without 3 launches), not with every ad
  count; the page 3 bar-row overflow below was measured only for the Natural Retreats fixture.

## Second round: results

- Offline: all six tests pass (v3parity 23, v3refuse 28, v3checkcap 13, v3platform 35, v3sample 34 checks; v3edge as above).
- New checks: the footer names all of 5, 6 and 12 with their counts; one small competitor keeps the one-name wording; a competitor of
  25 is not named; a brand named "5.11 Tactical" builds, prints as written in the header and title, and other typed digits are still
  refused.
- Chromium: v3browser passes (24); the three-name directional build measures within A4 (kit `measure()` returns no problem).
- Not changed: the deployed test skill in the GetCrux workspace still carries the first-round kit. It needs the new kit hosted and the
  skill text updated before the fixes can be tried in the copilot.

## Third round: browser measures and notes

Setup: `pip install playwright` gave 1.64.1, which wants Chromium revision 1248; the container has 1243. Nothing installed: a scratch
directory with symlinks `chromium-1248` and `chromium_headless_shell-1248` to the installed 1243 builds, and
`PLAYWRIGHT_BROWSERS_PATH` pointed at it (outside the repo).

Results with Chromium (`for t in v3parity v3refuse v3edge v3checkcap v3platform v3sample v3browser`): v3parity 23, v3refuse 28,
v3checkcap 13, v3platform 35, v3browser 24 checks pass; v3edge fails (below); v3sample 58 checks pass (34 before this round, 24 new, 22 of them in Chromium); v3edge passes 9 checks and then stops on the
exception from the long-name build (exit 1). The default spec is still byte-identical to `tests/fixtures/base-kit-current.py`.

**Why `v3edge.py` fails with Chromium (not fixed).** The long-name test sets the competitor's name to "Southern New Hampshire
University" and leaves `short` unset, so `short` is 34 characters. The skill caps `short` at 18 characters for this reason (line 163
of `SKILL_v3.src.md`: "a long name wraps and can push a page sideways"). The element that scrolls is page 3's bar rows: `.bars` is a
grid of `max-content 1fr max-content` columns (build_kit_v3.py line 667), so the value label "65 of Southern New Hampshire University's 209"
cannot wrap and the row is wider than a 375 px phone (240 px over). Without a browser `measure()` returns None and the test passes,
which is why the offline run never showed it. The cause is the same on the unmodified kit. A fix is a CSS rule for the 640 px
breakpoint (let `.bars` wrap or stack at phone width); that changes the CSS every report carries, so the default output would no longer
match `tests/fixtures/base-kit-current.py` byte for byte. Left alone. The test could use a short of 18 or fewer, but then it would
stop testing a long label on the speed chart, which is its point.

**The same cause with names at the 18-character limit.** Three competitors with 18-character shorts ("Alpine Stays Group", "Summit Lodge
Rents", "Valley Home Rental") push page 3's bar rows past a 375 px phone by 21 px in the standard report and by 4 px in the directional
report with 5, 6 and 12 ads. So the 18-character limit does not by itself keep page 3 inside a phone. The small-sample footer is not
the cause: footers fit at 375 px, the three names are all in the page 4 footer, and the only element past the phone is in `.bars`.
Because the kit refuses any build whose `measure()` finds a sideways scroll, a directional build with three 18-character names is
refused in a browser today ("the page scrolls sideways by 4 px"); it is the same refusal a standard build gets. Fix when someone
accepts a one-time change to the standard output: in the `max-width: 640px` block, `.bars { grid-template-columns: max-content 1fr; }`
with `.bars .val { grid-column: 1 / -1; }` would put each value under its bar.

**Measured (all in Chromium, `tests/v3sample.py`):**

| Build | Result |
|---|---|
| Directional on TIKTOK, GOOGLE, LINKEDIN, 5, 6 and 12 ads (`F.on`, `F.benchmarks()`) | builds; footer on pages 1, 3, 4 only; five pages, none past 1123 px, no sideways scroll at 375 px |
| Three 18-character names, 5, 6 and 12 ads, and again with 3 launches | footer on pages 1, 3, 4 only; all three names in page 4's footer; five pages within A4; no footer wider than 375 px; the 4 px sideways scroll is page 3's bar rows (see above) |
| Three competitors of exactly 5 ads | builds; footer names Vrbo, Airbnb, Inspirato; five pages within A4; no sideways scroll at 375 px |

No footer wrapped badly, so no CSS or footer text was changed in this round.

## Decision note: the launch guard in standard reports

In a standard report a compare competitor that launched fewer than 5 ads in the window still prints a weeks figure from the same
division: with 3 launches in 90 days the fixture's page 4 prints "Vrbo, 0.2 a week 675 weeks". The guard is not extended to standard
reports in this branch, because it would change standard output and the spec says that must stay byte for byte today. A standard
report needs 20 live ads from a competitor, so a competitor with 20 or more ads and under 5 launches is possible (a mature, quiet
library) and does print a figure that large. Recommendation: extend the guard to standard reports, as its own change, with its own
approval and a new baseline file (a quiet competitor is a real case, and "675 weeks" tells a rep nothing). Until then, nothing here
changes it.

## Fourth round: page 3 and page 4 bars on a phone

Change (`build_kit_v3.py`, inside the `max-width: 640px` block, four lines): `.bars` and `.hbars` (page 3's named-guest bars and
page 4's weeks bars) drop to two columns (`minmax(0, max-content) 1fr`: the name can wrap, the bar takes the rest) and the value
(`.val`, `.hv`) goes on its own row under its bar. Wider than 640 px, and in print, nothing changes. This replaces the "not fixed" cause
above: the 34-character name also pushed page 4's weeks bars (113 px) once page 3's were fixed, so both charts needed the rule.

Effect on standard output: every report now carries these four CSS lines, so output is no longer byte-identical to
`tests/fixtures/base-kit-current.py` or to `base-kit-a04b115ebc4a.py`. Both tests (v3sample, v3platform) now compare against the
baseline kit's output with those four lines added (`F.with_phone_css` in `tests/v3fixture.py`), and v3sample checks that this is the only
difference. A phone-width screenshot of both charts with the three 18-character names looks right (name above its bar, value under it).

Results with Chromium: v3parity 23, v3refuse 28, v3edge 20 (was failing), v3checkcap 13, v3platform 35, v3sample 59, v3browser 24;
no failure. The three 18-character names now have no sideways scroll at 375 px (the 4 px overflow is gone).

Added `RELEASE_STEPS.md`: the steps from this branch to the live skill (copy, build, host, test copy, check chat, live), with the
files to copy and what to look for. Not done here: none of those steps can be run from this session.

Still open and decided by Kevin: extending the "too few to compare" guard to standard reports; a kit-side refusal of a `short` over 18
characters; opening the pull request.
