## Description of Changes:
Seven bug fixes in Noah-MP and the code that couples it to the atmosphere, one commit each. Each commit message gives the defect, the fix and the measured effect. All change answers in suites that use Noah-MP.

| Fix | What goes wrong | Effect |
|---|---|---|
| Evaporation hand-off (`noahmpdrv`) | The atmosphere receives Noah-MP's latent heat divided by the host's `con_hvap`, not the water Noah-MP removed. The two use different latent heats. | The atmosphere gains 0.07–0.10 % of global precipitation more water than the land loses |
| Coastal snow (`GFS_surface_composites_pre`) | With `frac_grid`, the land's snow is overwritten with the cell mean every step | Thin coastal snow is lost |
| Snow initialisation (`GFS_phys_time_vary`) | With `frac_grid`, cold-start snow layers are built from the cell-mean snow | 0.29 kg/m² of land snow lost at the first step |
| Snow layer count (`combine`) | Tests `isnow_old` instead of `isnow` (NCAR/noahmp#47) | Up to 0.16 mm of water and 8.5 MJ/m² per occurrence |
| Snow layer heat (3 commits: `combine`, `csnow`, `combo`) | Merged layers keep the receiver's temperature; layers that vanish drop their heat; heat capacities are computed per volume from capped volume fractions but used per kg | Noah-MP's soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m², measured together with a thin-snow fix that is held for later |

Related fixes come later, separately:
- With `frac_grid`, coastal land is stepped twice per time step. Sea ice has the same cause, and both have two tested forms.
- Fixes where the destination of the water or heat is a judgement: truncated thin snow, truncated canopy water, the heat of a melted-out snow layer, and Noah-MP's own latent heats.

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the SAMF/PBL fixes and the GFDL MP v3 fixes, 23 October 2026 (develop 5651397d, baselines 20261016). [RT 0b] The log will be in the ufs-weather-model PR that follows review. Effects in the table are from budget meters added to the model (C96 `control_p8_ugwpv1`, 24 h).

## Dependencies:
None. The ufs-weather-model PR, with the RT log, follows review.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
