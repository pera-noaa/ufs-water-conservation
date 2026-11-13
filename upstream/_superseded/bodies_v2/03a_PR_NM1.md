## Description of Changes:
Three bug fixes in Noah-MP's snow bookkeeping, one commit each. The two `frac_grid` fixes change answers in Noah-MP runs with `frac_grid`; the layer-count fix is rare at short time steps. Fixes to the evaporation hand-off and snow layer heat follow in #410, which builds on this PR.

@barlage @cenlinhe, the layer-count fix is the change NCAR made in NCAR/noahmp@218eb5a; the UFS copy never picked it up.

| Fix | What goes wrong | Effect |
|---|---|---|
| Coastal snow (`GFS_surface_composites_pre`) | With `frac_grid`, the land's snow is overwritten with the cell mean every step | Thin coastal snow is lost; Noah-MP's water check goes from +5 kg/m² per 6 h to −6 × 10⁻⁵, measured with the time-step fix below |
| Snow initialisation (`GFS_phys_time_vary`) | With `frac_grid`, cold-start snow layers are built from the cell-mean snow | 0.29 kg/m² of land snow lost at the first step |
| Snow layer count (`combine`, land and glacier) | Tests `isnow_old` instead of `isnow` (NCAR/noahmp#47) | Up to 0.16 mm of water and 8.5 MJ/m² per occurrence |

Notes:
- Snow initialisation: snow depth without snow water still builds no layers, as on develop. Otherwise dividing by a small land fraction can build layers with no ice, whose zero heat capacity divides by zero in Noah-MP's energy routine.
- Snow layer count: rare at short time steps (5 × 10⁻⁶ of calls on melt-out-prone packs at 720 s, 1.7 × 10⁻² at 3600 s); C96 24 h is bitwise unchanged by this fix alone.

Related fixes come later, separately: with `frac_grid`, coastal land is stepped twice per time step (the time-step fix). Sea ice has the same cause, and both have two tested forms.

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, #410, the SAMF/PBL fixes (#408) and the GFDL MP v3 fixes, 27 October 2026 (develop 3e48f4cc, baselines 20261022): all 54 builds compile; 116 tests are identical, 101 change answers, and 15 restart/IAU tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review. Effects in the table are from budget meters added to the model (C96 `control_p8_ugwpv1`, 24 h).

## Dependencies:
None. The ufs-weather-model PR, with the RT log, follows review.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
