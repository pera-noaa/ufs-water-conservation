# R2-8 (triage row #29): MYNN 01 + 01b against NCAR `main` and ccpp-physics `ufs/dev`

## Status (29 October 2026, read-only check; nothing posted, pushed or committed)

- **01b is fixed in NCAR `main`**: e447691 (2026-10-07) closed NCAR/MYNN-EDMF#84 (`mirfjc`). `Dth` now comes from the
  updated condensate, then `moisture_check` adds its fill heat to `dth` once, which is our 01b v2 ordering. The draft's
  "since ebd5d2d" premise is stale.
- **01 (a) surface-flux density and (b) dew limiter are still in `main` @11f6bc1**, verbatim apart from `0.0` → `zero`.
- **01 (c) filler mass is still mismatched in `main`, changed**: it weights by the host δp `pint(k)−pint(k+1)`, not the
  interpolated δp, while the solver conserves ρ·dz. The size of the residual is *inferred* small, not measured.
- **ccpp-physics `ufs/dev` @b7cb19b**: MYNN-EDMF is a vendored copy, not a submodule (only MYNN-SFC is a submodule).
  All four defects are present at the original lines +3. 01 applies cleanly, and 01b applies on top of 01.
- **#392 is OPEN** and updated today. It replaces the vendored copy with submodule `MYNN-EDMF` @**11f6bc1**
  (`release-v6.1` = `main` HEAD). Once it merges, UFS gets 01b fixed and (a), (b) and (c) still present.
- **Our patches do not apply to `main`**: 1 of 3 module hunks applies, (c). (a) and (b) fail on text, and 01b is moot.
  A verified 3-line port is below. The wrapper half needs a re-cut against #392's wrapper.
- **The draft needs re-targeting** to NCAR `main`: drop the 01b ask and the "still present?" question, and ask NCAR to
  take (a), (b) and (c) so that #392 carries them. The numbers were measured on the CCPP copy. (a)+(b) are identical
  code, so they should carry over (*inferred*). +8.0 W/m² does not apply to `main`.

Sources: NCAR/MYNN-EDMF cloned at 11f6bc1 (2026-10-26, PR #87). ccpp-physics `ufs/dev` sparse clone at b7cb19b. #392
head 3120f71, wrapper fetched with `gh api`. Our patches: `conservation/suites/patches/01_E3_*.diff`, `01b_E3_*.diff`
(byte-identical to `conservation/replay/patches/47_MYNN01.diff`, `48_MYNN01b.diff`). Nothing was built or run.

## Per-defect table

`main` = NCAR/MYNN-EDMF @11f6bc1. `src/module_bl_mynnedmf.F90` is abbreviated `M`, `src/module_bl_mynnedmf_driver.F90`
is `Mdrv`. `dev` = ccpp-physics `ufs/dev` @b7cb19b, `physics/PBL/MYNN_EDMF/`: `module_bl_mynn.F90` is `C`,
`mynnedmf_wrapper.F90` is `W`. `#392 W` = the wrapper at #392 head 3120f71.

| Defect | In `main`? | `main` file:line | In `ufs/dev`? | `ufs/dev` file:line | Our patch applies? | Edit the draft needs |
|---|---|---|---|---|---|---|
| (a) fluxes made kinematic with ρ(k=1), applied with `rhosfc` (psfc with T, q of layer 1) | **yes** | defined `M:4051`; kinematic `M:698` `flqv = qfx/rho1(kts)`; applied `M:4376,4399` (sqw), `M:4561,4584` (sqv), 4279/4302 (θl). #392 W: ρ `W:613`, `hfx/qfx` `W:644-645`, unchanged from dev | **yes** | defined `C:4137`; kinematic `C:1069`; applied `C:4391` (sqw), `C:4521` (sqv); W: ρ `W:610`, `W:626-627` | dev: **yes** (offset +3). `main`: **no** (hunk 1 fails on whitespace; port below). #392 W: hunks 2–3 yes at fuzz 3, declaration hunk no | Keep it. Cite `main` lines, not "the CCPP copy" |
| (b) dew limiter `max(qvflux, min(0.9*sqv-1e-8, 0)/dtz)` is 0, so every negative flux is removed | **yes** | `M:4543` (`zero` in place of `0.0`) | **yes** | `C:4514` | dev: **yes**. `main`: **no** (text differs; port below) | Keep it. Cite `M:4543` |
| (c) `moisture_check` weights by δp, the solver conserves ρ·dz | **yes, changed form** | call `M:5397` with `delp`. `delp1 = max(0.01, pint(k)-pint(k+1))` `Mdrv:511`. #392 passes `pint = prsi` (`W:629`, `W:785`); ρ is ideal-gas `W:613` | **yes, original form** | call `C:5016`. Interpolated δp `C:4143`, `C:4154-4155` | dev: **yes**. `main`: **yes** (hunk 3 applies as is) | Reword: "weights by the host δp (prsi) while the solver conserves ρ·dz; ρ is ideal-gas, dz nonhydrostatic". Size in `main` *inferred* small, not measured |
| (d) ρ = Δp/(g·dz) in the solver (01, wrapper part) | n/a (host-side) | #392 `W:613` still ideal-gas ρ | **yes** | `W:610` | dev: **yes**. #392 W: hunk 2 yes at fuzz 3 | Goes to the CCPP wrapper (#392's), not to NCAR |
| 01b: `moisture_check` adds the fill heat to θl, then `Dth` (from post-fill `sqc2`/`sqi2`) counts it again | **no, fixed** (e447691, 2026-10-07, MYNN-EDMF#84) | `Dth` `M:5374`/`M:5388` from pre-fill `sqc2`/`sqi2`, then `moisture_check` `M:5397` adds its own fill heat to `dth` once (`M:5523`) | **yes** | call `C:5016`, before `Dth` `C:5034`, `C:5045`; fill heat to `th`(=thl) `C:5179` and to `dth` `C:5172` | dev: **yes, after 01** (fails alone: its context includes 01's call line). `main`: n/a (same change already there) | **Delete the ask.** Replace "since ebd5d2d … gone there" with "fixed in `main` by e447691 (#84); the vendored copy in `ufs/dev` still double counts until #392 merges" |

### Exact lines (verbatim)

`main` `M:4051` / `M:698` / `M:4543` / `M:5397`:
```fortran
    rhosfc     = psfc/(R_d*(tk(kts)+p608*qv(kts)))
    flqv = qfx/rho1(kts)
      qvflux = max(qvflux, (min(0.9*sqv(kts) - 1e-8, zero)/dtz(kts)))
    CALL moisture_check(kte, delt, delp, exner,        &
```
`ufs/dev` `C:4137` / `C:1069` / `C:4514` / `C:5016`:
```fortran
    rhosfc     = psfc/(R_d*(tk(kts)+p608*qv(kts)))
       flqv = qfx(i)/rho1(kts)
       qvflux = max(qvflux, (min(0.9*sqv(kts) - 1e-8, 0.0)/dtz(kts)))
    CALL moisture_check(kte, delt, delp, exner,        &
```
`main` `M:5370-5374`, the 01b fix as merged:
```fortran
    ! From the updated thl and the UPDATED condensate, before moisture_check:
    ! moisture_check adds the latent heat of its own fill to dth.
    IF (FLAG_QI) THEN
      DO k=kts,kte
         Dth(k)=(thl(k) + xlvcp/exner(k)*sqc2(k)          &
```

### Port of 01 (module part) to `main` @11f6bc1. `git apply --check` passes; not compiled or run

```diff
@@ -4048,7 +4048,7 @@
-    rhosfc     = psfc/(R_d*(tk(kts)+p608*qv(kts)))
+    rhosfc     = rho(kts) ! flqv = qfx/rho1(kts): apply with the same density
@@ -4540,7 +4540,7 @@
-      qvflux = max(qvflux, (min(0.9*sqv(kts) - 1e-8, zero)/dtz(kts)))
+      qvflux = max(qvflux, -max(0.9*sqv(kts) - 1e-8, zero)/dtz(kts))
@@ -5394,7 +5394,7 @@
-    CALL moisture_check(kte, delt, delp, exner,        &
+    CALL moisture_check(kte, delt, rho(kts:kte)*dz(kts:kte), exner, & ! layer mass the solver conserves
```
Full unified diff (with context): `/private/tmp/claude-33310/-Users-pera-Documents-ash-code-tm5-zoom/ee96825e-0c8b-4a26-8edc-7fcc1383da1f/scratchpad/r2_8_mynn01_port_main.diff`.
The wrapper half of 01 (`rho = delp/(grav*dz)`, `qfx`/`hfx` with the surface scheme's density) has to be re-cut against
#392's wrapper (`W:613`, `W:644-645`, plus a `rho_sfc` declaration).

### Other changes in `main` noticed in passing (*not measured*)

- 68d1af7 (2026-10-19) deleted the driver's `moisture_check2`. It now clips the input condensate to ≥ 0
  (`Mdrv:555`ff, `sqc1 = max(zero, sqc)`) and floors `sqv1` at 1e-10 (`Mdrv:547`). Tendencies are taken against the
  clipped input, so this should not create column water. A host negative persists instead (*inferred*).
- `mirfjc` also filed MYNN-EDMF#85 (DMP_mf cloud ice booked as a vapour flux; OPEN, Olson points to PR #86).
  Upstream is taking conservation reports of this kind quickly. No proposal or conservation document here mentions
  #84, #85 or e447691.
- `conservation_proposal.md:420-421` carries the same stale ebd5d2d sentence ("the CCPP copy and the MMM/MPAS copy
  still double count"). It needs the same correction (not edited; read-only task).

## Edit the draft issue needs (`round2_issues.md` §8)

1. **To:** NCAR/MYNN-EDMF (main). Cc #392. Drop "(after ufs-community/ccpp-physics#392)". #392 pins `main` HEAD, so a
   fix merged in `main` reaches UFS by a pointer bump before #392 merges.
2. Bullets: cite `main` lines (`module_bl_mynnedmf.F90:4051`/698, 4543, 5397 + driver 511). Reword (c) as the host
   δp vs ρ·dz. Delete the 01b bullet, or keep it as one line of context: "already fixed in `main` by e447691 (#84)".
3. Numbers: say they were measured on the CCPP copy (ufs/dev-era vendored `module_bl_mynn.F90`). Water +4.5×10⁻² →
   5×10⁻¹⁵ comes from 01 in full (a–d). Do not quote the +8.0 W/m² fill heat or the "fill-heat fix alone" impacts as a
   defect in `main`.
4. **Question**, replacing the current one: "(a) and (b) are unchanged in `main` @11f6bc1, and (c) remains with the
   host δp. Would you take the three-line fix in `main` (diff attached), so that #392's submodule pointer carries it?
   The wrapper half (ρ = δp/(g·dz), flux back-conversion) we would propose on #392."
5. Separate note for ccpp-physics (#392 thread or the triage): until #392 merges, `ufs/dev`'s vendored copy has all
   four defects, including 01b, and our 01+01b apply cleanly there.
