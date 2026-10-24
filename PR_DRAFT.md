<!-- Draft only. No pull request template exists in this repo (checked .github/, root, docs/ on main and on this branch), so these headings are the usual ones. Delete this file before merging. The pull request has not been opened. -->

# Directional report: build with 5 to 19 live ads per competitor, labelled as a small sample

## Summary

The v3 report refuses to build when a competitor has fewer than 20 live ads in the product line. Reps on niche lines ask the copilot to "build it anyway", and on 2026-10-23 (5.11 Tactical, pants line) the copilot wrote its own HTML and skipped the kit's checks. This branch adds a supported path: spec field `sample: "directional"` lets competitors with 5 to 19 live ads in, labels the pages, and guards the one number that breaks on tiny samples. Absent or `"standard"`, the report is what the kit built before, except for four phone-width CSS lines (below).

## What changed

- `build_kit_v3.py`
  - Spec field `sample` (`"standard"` or `"directional"`); an unknown value is refused. A directional competitor needs 5 live ads (`SMALL_SAMPLE_MIN`); a competitor with 4 is refused and the message names the floor. The brand's own minimum is unchanged.
  - Footer line on pages 1, 3 and 4: "Small sample: ... has N live ads in this line, so read this as a direction." It names every competitor under 20 with its own count.
  - Page 4: in a directional report, a competitor that launched fewer than 5 ads in the window gets "launched N ads since {date}, too few to compare" instead of a weeks bar (2 launches in 90 days would otherwise print hundreds of weeks).
  - The digit check ignores digits inside a brand's own `name` or `short` ("5.11 Tactical" builds as written).
- `SKILL_v3.src.md`
  - Hard rule: only the kit builds the report; if it refuses, say what it refused and stop.
  - Stage 1 offers the directional report when no line-up reaches 20; "build it anyway" means that choice only.
  - Setup list and refusal list name `sample` and the floor of 5.
  - Zero-ad imports are checked against the Meta Ad Library page before a competitor is replaced (text only).
  - Names are written exactly as the brand writes them.
- Four CSS lines at phone width for the page 3 and page 4 bars (see below).
- `tests/v3sample.py` (new), `tests/fixtures/base-kit-current.py` (new baseline: the kit before this change), `CHANGES.md`.

## Test results

Run with Chromium 1243 (symlinked for Playwright 1.64.1, nothing installed in the repo):

| Test | Result |
|---|---|
| v3parity | 23 pass |
| v3refuse | 28 pass |
| v3checkcap | 13 pass |
| v3platform | 35 pass |
| v3sample | 59 pass (default and `"standard"` specs equal the baseline kit's output plus the phone CSS, byte for byte) |
| v3browser | 24 pass (Meta, TikTok, Google, LinkedIn) |
| v3edge | 20 pass |

Measured in Chromium for directional builds: TikTok, Google and LinkedIn (5, 6 and 12 ads); three 18-character competitor names with the three-name footer; three competitors of exactly 5 ads. Each is five pages within 1123 px; footers fit at 375 px.

Phone-width fix: page 3's and page 4's bar rows were wider than a 375 px phone with long competitor names (v3edge failed with Chromium on the unmodified kit; three names at the 18-character limit overflowed by 21 px in a standard report). Four CSS lines in the 640 px block put each value under its bar. This changes the CSS every report carries, so standard output is no longer byte-identical to the old baselines; `v3sample` and `v3platform` now compare against the old kit's output plus exactly those four lines. v3edge now passes (20).

## Not measured

- `tests/v3loader.py`, and the installable skill (`make_skill_v3.py` writes a draft only).
- No copilot run against the new skill text; the Stage 1 wording is untested with a rep.
- The cause of the two empty imports (First Tactical, VIKTOS).
- Names at the 18-character limit were measured at 5, 6 and 12 ads only, on the Natural Retreats fixture.
- Hosting the kit and updating the test or live skill are separate steps and have not been done.

## Notes for the reviewer

- In a standard report, a competitor with 20 or more ads that launched under 5 in the window still prints a very large weeks figure on page 4 (the fixture with 3 launches prints "675 weeks"). The guard is not extended to standard reports because that would change standard output. `CHANGES.md` recommends doing it as its own change.
- Scope: against `main`, this diff is the directional report only. `main` already carries the TikTok, Google and LinkedIn code in the kit. The live skill does not have that platform support yet, so shipping this kit also ships it; the platform tests (`v3platform`, `v3browser`) cover it.
- `RELEASE_STEPS.md` lists the steps from here to the live skill.
- `PLAN.md` and `CHANGES.md` are working notes; remove or keep as the owner prefers.
