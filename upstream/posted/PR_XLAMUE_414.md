## Description of Changes:
Floors SAMF deep's entrainment rate at `0.001·clamt` (= `xlamud`), so the sub-cloud mass flux no longer grows downward when TKE raises `clamt` (#401). One line; changes answers wherever `tkemean` > 0.35.

## Tests Conducted:
`hafs_global_1nest_atm`, 48 h, 10 runs: develop crashes 6, with the floor none (largest one-step heating 5.5–7.6 K, from 49–96 K). `hafs_global_multiple_4nests_atm`, 5 runs: develop crashes 1, with the floor none. Precipitation changes are in #401. Full RT on Hercules with #405 (ufs-community/ufs-weather-model#3408): 54 compiles pass; 122 tests identical, 95 change answers, none fail to run.

## Dependencies:
None. Pairs with #405 in the ufsatm and ufs-weather-model PRs.

## Documentation:
None needed.

## Issue (optional):
#401

## Contributors (optional):
AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

