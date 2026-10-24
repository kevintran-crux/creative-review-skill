# Release steps: the directional report, from this branch to the live skill

For whoever has the main v3 folder, the real customer list and GetCrux workspace access (this cloud session has none of those).
Each step needs its own yes from Kevin before the next one. Stop at any failed check and fix it on this branch first.

Kit file to host: `build_kit_v3.py` as it stands on `directional-report`. Do not edit it in the main folder; edit here, re-run the tests, and copy again.

## 0. Before copying: the tests pass on this branch

`for t in v3parity v3refuse v3edge v3checkcap v3platform v3sample v3browser; do python3 tests/$t.py; done` with Chromium available.
Expected (head of the branch): v3parity 23, v3refuse 28, v3edge 20, v3checkcap 13, v3platform 35, v3sample 59, v3browser 24, no FAIL.
`v3loader.py` needs a local port and an installed skill file; run it in step 2.

## 1. Copy the files into the main v3 folder

Copy these over the main folder's copies (look at `git diff` of each against the main folder first; anything the main folder changed since `main` here needs merging, not overwriting):

- `build_kit_v3.py`
- `SKILL_v3.src.md`
- `tests/v3sample.py` (new), `tests/v3fixture.py`, `tests/v3platform.py` (the baseline checks now allow for the phone CSS)
- `tests/fixtures/base-kit-current.py` (new baseline: the kit before the directional change)

Not changed: `make_skill_v3.py`, `v3_static.py`, `PLAN.md`. `CHANGES.md` and `PR_DRAFT.md` are notes; keep or drop.
Then run the test line from step 0 in the main folder.

## 2. Build the skill with the real customer list

`python3 make_skill_v3.py` (no `--draft`). It writes `dist/build_kit_v3-<sha12>.py` and refuses to write `SKILL_v3.md` until the kit URL serves a file with that SHA-256, so step 3 comes first in practice: build, host the dist file, build again. Then `python3 tests/v3loader.py`.

## 3. Host the kit

Upload `dist/build_kit_v3-<sha12>.py` to the folder named in `kit_host.txt`. Check the URL serves exactly those bytes (SHA-256 equal to the one `make_skill_v3.py` prints). Hosting is its own yes.

## 4. Update the test copy

Update `creative-report-v3-check` (the test skill) with the new `SKILL_v3.md`. Leave the live skill alone. Its own yes.

## 5. One check chat on a thin-line brand

Use a brand whose line has competitors under 20 live ads (5.11 Tactical, pants line, as on 10/23). Look for:

- The copilot shows the counts and offers the directional report; "build it anyway" is read as that choice and nothing else.
- It builds only through the kit; if the kit refuses, it says what it refused and stops. It never writes HTML itself.
- The report has five pages, the "Small sample: ... read this as a direction." line on pages 1, 3 and 4 naming every competitor under 20, and "too few to compare" on page 4 for a competitor with under 5 launches.
- "5.11 Tactical" is written as the brand writes it, not "Five Eleven Tactical".
- A normal brand (competitors of 20 or more) still gets a normal report with no small-sample line.
- Open the report on a phone: no sideways scroll.

## 6. Update the live skill

Only after step 5 is clean, with Kevin's yes. Paste `SKILL_v3.md`, then compare the SHA-256 that `make_skill_v3.py` prints with the saved text. This also brings TikTok, Google and LinkedIn support to the live skill, which it does not have yet.

## Open decisions (not needed for the steps above)

- Extend the "too few to compare" guard to standard reports (changes standard output; see `CHANGES.md`).
- Make the kit refuse a competitor `short` over 18 characters (the skill text already says 18).
- Open the pull request (`PR_DRAFT.md`); it has not been opened.
