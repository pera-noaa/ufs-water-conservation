# Cleaned phase-0 bodies (24 Oct)

These supersede `../bodies/` for items 02–10; `post_bundle.py` still renders the old ones. Placeholders to fill before posting:
- `#TBD-<KEY>`: the number from `numbers.json` once that item is posted.
- `[RT 0b]`: the result line of the 0b rerun (`rt_v0b`, with the 7-commit Noah-MP).
- `[0b global effect …]`, `[0b hafs …]` (WM 0b only): refresh from the rerun.

Posting check: `grep -n 'TBD\|\[RT\|\[0b' bodies_v2/<file>` must print nothing.
