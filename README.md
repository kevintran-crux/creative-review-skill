# v3 skill bundle (isolated)

Everything a separate session needs to improve the v3 competitive creative report skill, and nothing else.
Start with `PLAN.md`.

- `build_kit_v3.py`: the report kit (`python3 build_kit_v3.py` is a library; tests import it)
- `SKILL_v3.src.md`: the copilot instructions source
- `make_skill_v3.py`, `v3_static.py`: build the draft skill and the kit file (no customer list here)
- `tests/`: offline tests (`v3parity`, `v3refuse`, `v3edge`, `v3checkcap`, `v3platform`) and fixtures; `v3browser.py` and
  `v3loader.py` need Chromium / a local port
- Run: `for t in v3parity v3refuse v3edge v3checkcap v3platform; do python3 tests/$t.py; done`

Left out on purpose: the main repo, the customer list the skill builder reads, other skills, notes and call material.
