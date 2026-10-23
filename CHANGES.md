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

- Other directional shapes in a browser: other platforms (TikTok, Google, LinkedIn) with `sample` directional; a competitor name
  near the 18-character limit with the footer line; competitors with 5 ads in all three slots.
- `tests/v3loader.py` (needs a local port and an installed skill file); the installable skill (`make_skill_v3.py` writes a draft
  only: `python3 make_skill_v3.py --draft` runs).
- No copilot run against the new skill text: the Stage 1 wording is untested with a rep.
- The cause of the two zero-ad imports (First Tactical, VIKTOS) is not looked at; the skill change is text only.

## Second round: results

- Offline: all six tests pass (v3parity 23, v3refuse 28, v3checkcap 13, v3platform 35, v3sample 34 checks; v3edge as above).
- New checks: the footer names all of 5, 6 and 12 with their counts; one small competitor keeps the one-name wording; a competitor of
  25 is not named; a brand named "5.11 Tactical" builds, prints as written in the header and title, and other typed digits are still
  refused.
- Chromium: v3browser passes (24); the three-name directional build measures within A4 (kit `measure()` returns no problem).
- Not changed: the deployed test skill in the GetCrux workspace still carries the first-round kit. It needs the new kit hosted and the
  skill text updated before the fixes can be tried in the copilot.
