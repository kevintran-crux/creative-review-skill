# Plan: v3 report when a competitor has fewer than 20 live ads

For a cloud session working only in this folder. Written 2026-10-23. Everything here is safe for the whole Crux team to read.

## Goal

The v3 report (five A4 pages, built by the GetCrux copilot from a kit) refuses to build when a competitor has fewer than 20 live ads in the product line reviewed. Reps hit this on niche lines and ask the copilot to "build it anyway". Give the skill a supported way to build a smaller, clearly labelled report through the kit, so the copilot never has to improvise.

## What happened (5.11 Tactical, pants line, 2026-10-23)

- The brand has 490 live ads, 168 of them pants ads. The first competitors, First Tactical and VIKTOS, imported with 0 tracked live ads (Meta pages FirstTacticalUS and VIKTOSBRAND). Why they imported empty is not known.
- Replacement competitors had too few pants ads: TRU-SPEC 2, LA Police Gear 6, VERTX 4. The skill stopped, as written ("a competitor under 20 ads is replaced; if no line-up works, stop and tell the rep").
- The rep wrote "build it out anyways its ok". The copilot did not use the kit. It wrote its own HTML (three files, one named `...-checked.html`), with its own wording and no kit checks. The kit's page fit, word rules and number checks never ran.
- Two failures, then: (1) the threshold has no supported lower setting, (2) "build it anyway" has no supported path, so the copilot left the kit.

## Decision for Kevin (one choice; the default below is what to build)

Recommended: keep 20 as the standard bar, and add a **directional report** that the kit builds when the rep asks for it. Alternatives, not to build unless Kevin says so:

- Lower the bar for everyone (for example to 10). Simplest, but every report then shows thin comparisons with no label.
- Count a competitor's whole library when its line is thin. Rejected: the page counts would mix product lines.
- Pool several small competitors into one comparator. Optional later: 2 + 6 + 4 = 12 here, still thin.

## What to build (default: the directional report)

1. **Spec field `sample`.** Optional. Absent or `"standard"`: today's behaviour, byte for byte. `"directional"`: competitors need `SMALL_SAMPLE_MIN = 5` live ads after set-asides (one constant beside `MIN_RIVAL_ADS = 20`). The brand's own minimum is unchanged.
2. **Label the small sample on the page.** When `sample` is directional, any page that sets the compare competitor beside the brand (pages 1, 3, 4) gets one line in its footer: "Small sample: {name} has {n} live ads in this line, so read this as a direction." Use the competitor's real count from the rows, as every other count.
3. **Guard the arithmetic that breaks on tiny samples.** Page 4's "weeks to launch" for a competitor divides by its weekly pace: 2 ads in 90 days gives hundreds of weeks. When the competitor launched fewer than 5 ads in the window, replace its bar with one line saying it launched too few to compare, and keep the brand's bar. Check page 2's bars and page 3's named-guest chart for the same kind of breakage with 5 to 10 ads.
4. **Skill text** (`SKILL_v3.src.md`, Stage 1 and the stop list): when no line-up reaches 20, show the rep the counts and offer the directional report as the choice ("build with at least 5 live ads each, labelled as a small sample"). A rep's "build it anyway" means this choice and nothing else. Add a hard rule: never write the report HTML yourself, never build a file the kit did not save; if the kit refuses, say what it refused and stop. Put `sample` in the setup list.
5. **Refusals.** `sample` must be one of the two values. A directional spec with a competitor under 5 still refuses, naming the floor.
6. **Zero-ad imports.** Add a short Stage 1 note: a competitor that imports with 0 live ads is checked against the Meta Ad Library page itself before it is replaced, and the flags say what was found. (This is text only; the cause of the two empty imports is for the GetCrux team to look into.)

## Tests (offline, add to `tests/v3platform.py` or a new `tests/v3sample.py`)

- Default spec output is unchanged: build the Natural Retreats fixture with the current kit and with the new one, compare bytes. `tests/fixtures/base-kit-a04b115ebc4a.py` is an older kit; build a fresh baseline from the unmodified `build_kit_v3.py` before editing it and keep it as a second base file.
- Directional spec with competitors of 5, 6 and 12 ads builds, prints the real counts and the footer line on pages 1, 3 and 4.
- Competitor with 4 ads in a directional spec is refused with the floor named. The same competitor with 12 ads in a standard spec is refused for the 20 minimum, as today.
- Competitor with 3 launches in the window: page 4 shows the "too few to compare" line and no weeks bar for it, and does not print a division result.
- Unknown `sample` value is refused.
- All existing tests pass: `v3parity`, `v3refuse`, `v3edge`, `v3checkcap`, `v3platform`.
- Page fit on A4 for the directional build: run `tests/v3browser.py` where Chromium works. If the cloud session has none, say so and list what was not measured.

## Rules for the cloud session

- Work only in this folder. It holds the v3 kit, skill source, tests and fixtures, and nothing else. Do not add files from outside it.
- No network calls to GetCrux or any Crux system. Everything runs offline against the fixtures.
- `make_skill_v3.py` here writes a draft only: it has no customer list, so its output says "do not install" in place of the list. Do not try to build an installable skill.
- Do not edit `build_kit_v3.py` comments or structure beyond what the plan needs. Keep each change small and match the surrounding code.
- Do not commit credentials or personal data. The fixtures hold public ad data and one team email.

## Done when

- The offline tests above pass, and the default output is byte-identical to the baseline.
- A short `CHANGES.md` lists each changed file, what changed, the test results, and anything not measured.
- Nothing outside this folder was touched.

## After the cloud session (Kevin, on the local checkout)

Copy the changed `build_kit_v3.py`, `SKILL_v3.src.md` and new tests back into the main v3 folder, run `make_skill_v3.py` with the real customer list, host the new kit, update the test copy `creative-report-v3-check`, run one check chat on a thin-line brand, and only then update the live skill. Hosting, the test copy and the live skill are separate yeses.
