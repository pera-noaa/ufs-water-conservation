# samfinit: is the meter-induced round-off divergence an uninitialised/OOB read in samfdeepcnv?

## Status (17 Oct, DONE): No. It is FMA contraction in the edited surface routines. No SAMF bug, no fix needed.

| test | result |
|---|---|
| DEBUG base (p20rt_final), ifort `-O0 -check all -init=snan,arrays -ftrapuv -fpe0`, control_p8 C96 6 h (`runs/dbase`) | clean, no trap; 10793/55296 columns deep-convective in 6 h |
| DEBUG develop @112b1d46 (`runs/ddev`) | clean, no trap; 10802 deep columns |
| does ifort `-init=snan,arrays` cover automatic arrays? (`tools/inittest.sh`) | yes: 1-D and 2-D automatic arrays and scalars = 7FF7BADDADBADDAD (SNaN); integers not covered |
| bitwise state hash (T, u, v, all tracers, all tendencies) at all 12 energy probes, `tools/apply_hash.py` | production mfx (`hm`) vs ensfc msfc3 (`hs`): probes 1-4 equal at kdt 1; probe **5** (after satmedmfvdifq) first differs |
| same two trees, DEBUG (`hmd`, `hsd`) | **bitwise identical**: all probes, 5 steps; atmf/sfcf f001 0 vars differ |
| same two trees, production + `-no-fma` (`hmf`, `hsf`) | **bitwise identical**: all probes, 4 steps; f001 0/194 sfcf, 0/18 atmf vars differ |

- SAMF deep is not the origin. The state is already bitwise different after the PBL at kdt 1. The PBL is the first scheme to read the surface fluxes. The ensfc meters add statements inside noahmplsm, glacier, noahmpdrv, sfc_sice, sfc_nst and surface_composites_post. Release flags are `-O3 -fp-model precise -march=core-avx2` (IntelMixed.cmake), so FMA contraction is allowed. Added statements change which multiply-adds the compiler fuses, so the fluxes move by about 1 ulp.
- The EMS meter lines are 16-digit global sums. They cannot see a 1-ulp difference in one column. SAMF trigger thresholds amplify it into the first visible difference, which is where "diverges in SAMF deep" came from.
- encnv mallz: its meter edits samfdeepcnv.f itself, same mechanism. ensfc r0 vs sf1 (inert switches added to surface files): same mechanism.
- Uninitialised reads are ruled out two ways. (1) Debug traps cover real locals and automatic arrays, and bounds checks cover integer indices. (2) A layout-dependent read would still differ between metered and unmetered debug builds; they are bitwise equal.
- SA1: not implicated. The SA1 lines run inside both trees and show no trap or layout dependence.
- Consequence for the programme: a "bitwise inert" or "passive meter" gate is only meaningful with `-no-fma` (append to the `AVX2` branch of `cmake/IntelMixed.cmake`; `tools/nofma.py`). Otherwise any edit to a physics file shifts round-off. Fix-vs-unfixed comparisons of physics-file edits carry this FMA noise and should use the ctlc999 threshold-noise control.

Hercules: `$U/cons/samfinit` (trees/, runs/, logs/, tools/). Local tools: `tools/`.
