*History of `report.md` (canopy), moved verbatim on 18 October 2026. The head is `report.md`.*

# canopy: E.2 (Noah-MP canopy wetted fraction), TH8/TH9, E.1 (NSST sea spray) as switch-guarded fixes

## Status (18 Oct 2026, done)

- **E.2 `noahmp_fwet_opt` (0 stock | 1 mass-weighted | 2 larger fraction | 3 dominant phase, Noah-MP v5).** BUG FIX of an
  inconsistency: fwet picks the phase by "any ice", every consumer by tv. Off = bitwise. Closure: canopy R_S 3e-17 (CH1),
  storage-frame 6e-16 (CH2), atmosphere water 2e-20 and energy residual 1.6e-11 W m-2. Impact beyond noise over land
  (canopy evaporation +17 to +22 % at f24, +43 to +52 % at f06; sublimation -21 to -24 % at f06; land LH +0.6 to +1.0 %
  at f24); global T rms 0.153-0.159 vs noise 0.139. Recommend opt 2 (monotone: adding water never lowers fwet).
- **The proposal's E.2 candidate diff has a defect:** its new local `cwat` shadows the module's specific heat of water
  (4.188e6), so precip_heat's PAH terms read an uninitialised local and canwater's refreezing uses mm of water. 01 avoids it.
- **TH8 (energy 06, in full10) alone is far beyond noise over land:** canopy evaporation -68 % at f06, -47 % at f24
  (trace placeholder snow -> trace canopy ice -> E.2). TH8+TH9 reproduces the proposal (evcw -2.9 %, sbsno +1.3 % at f06).
  With E2 on, TH8+TH9 is at noise from f06 (rms 0.5-1.1x), TH8 alone is not quite (sublimation rms 1.7-2.5x at f06).
  **TH9 is still needed**; 03 puts it behind `thompson_sed_actual`; TH8 must ship with it.
- **E.1 `nst_spray_opt` (0 explicit | 1 backward Euler with the lowest layer).** Reproduced on develop without a TC:
  explicit spray is unstable (lam > 2) in 12k cell-steps per day; 2 oscillating cells in 24 h, 271 in 10 days
  (21 flips in a row at 240E 56S), 177 at dt 1440 (17.7 K/step). Implicit: 0, 2, and 10 (the 10 = spray-off background, 7).
  Conserves by construction (one flux pair); closure residual unchanged. Impact: global LH -0.21 to -0.27 W m-2
  (ocean -0.3 %), beyond noise in the mean: NUMERICAL STABILITY, PHYSICS CHANGE by the bar.
- Gates (all on): restart, 4x6, restart+4x6 BITWISE; all off = full10 BITWISE (-no-fma both); meters passive BITWISE.
- Not exact / not done: no TC on develop, so the v1 day-6.4 runaway is not reproduced (v1 step-700 restart deleted);
  sfc_ocean.F and the NOAA-EMC copy are compile-checked only (no suite here uses them); the EMC copy gets the setter but
  no land-component namelist plumbing.
- Hercules `$C = $U/cons/canopy`; local `conservation/canopy/`. Base = `$E/full10`. Patches in `patches/` (see Files).

### Land impact, mean difference in % of the control mean (f06 | f24); noise in the first row

| comparison | evcw (canopy evap) | trans | sbsno | land LH | t2m (K) | cnwat |
|---|---|---|---|---|---|---|
| noise p0c-p0 | -0.01 / -0.30 | +0.00 / -0.18 | -0.00 / -0.05 | -0.00 / -0.11 | +0.000 / -0.001 | +0.01 / -0.07 |
| TH8 alone (full10 as is) q0-qT8 | **-68.3 / -47.1** | +17.0 / +8.6 | +6.5 / -2.3 | -4.8 / -1.8 | +0.080 / +0.049 | +34 / +48 |
| TH8+TH9, E2 off qT9-qT8 | **-2.9** / +0.2 | +0.3 / -0.7 | **+1.3** / -0.2 | -0.2 / -0.3 | +0.001 / -0.002 | +1.5 / +1.0 |
| TH8 alone, E2 opt1 qF1-qT8F1 | +0.02 / +0.34 | -0.00 / -0.50 | -0.04 / -0.68 | -0.01 / -0.13 | +0.000 / -0.000 | -0.01 / +0.07 |
| TH8+TH9, E2 opt1 qT9F1-qT8F1 | +0.01 / -0.02 | +0.00 / -0.23 | +0.00 / +0.02 | +0.00 / -0.01 | +0.000 / +0.000 | -0.01 / +0.19 |
| E2 opt1 on full10 (TH8 on) qF1-q0 | +352 / +122 | -17.2 / -8.8 | -25.7 / +0.9 | +7.9 / +2.4 | -0.113 / -0.065 | -38 / -45 |
| E2 opt2 qF2-q0 | +366 / +130 | -17.3 / -8.6 | -27.5 / -0.6 | +7.2 / +2.7 | -0.124 / -0.072 | -36 / -43 |
| E2 opt3 qF3-q0 | +364 / +125 | -17.3 / -8.8 | -26.9 / +0.7 | +7.2 / +2.4 | -0.121 / -0.073 | -36 / -43 |

- **full10 ships TH8 without TH9 or E2, and that is far beyond noise over land** (energy's "TH8 about noise" was the global
  T rms only). TH8 + TH9 reproduces the proposal's held numbers (evcw -2.9 % vs -2.4 %, sbsno +1.3 % vs +1.1 % in the
  first 6 h; noise -0.01 % / -0.00 %). With E2 on, TH8 alone and TH8 + TH9 are both within noise in the means.

## TH8 / TH9 diffs on full10

- `02_TH8_...` is energy's `06` verbatim (`if (.true.)` in the four surface-precipitation tests). It is the held TH8
  (proposal `patches/held/TH8_*`) in effect: identical arithmetic, comment differs. It applies on all_full and is already
  in full10; nothing replaces it.
- `03_TH9_thompson_sed_actual.diff` = held TH9 behind `thompson_sed_actual` (default .false., bitwise off): the four
  pre-loops and the eight `max(R1, ...)` -> `max(sfloor, ...)` with `sfloor = R1` unless the switch is on. With P8's
  `sedi_semi = .true.` only the ice and snow parts act. On mq10 (metered) `patch -F0` rejects 2 hunks (meter context in
  Thompson); `tools/apply_th9.py` applies it there by anchors.
- **Recommendation:** TH8 ships only with `thompson_sed_actual = .true.` (or with E2 on); better, make TH9 unconditional
  with TH8. The switch exists so the off state is provably bitwise.

## Files

- `patches/01_E2_noahmp_fwet_opt.diff`, `02_TH8_...`, `03_TH9_thompson_sed_actual.diff`, `04_E1_nst_spray_implicit.diff`
  (apply in order, `patch -p1 -F0` on `$E/full10/ufs-weather-model`; checked on a fresh copy).
- `patches/instrumentation/meter_spray_gain.diff` (print-only SPR meter, both spray on and off),
  `patches/instrumentation/test_only_th8_env_switch.diff` (env CANOPY_TH8_OFF, for the TH8 tests only; not a proposal).
- Tools: `tools/apply_{e2,th9,e1,spraymeter,spraymeter2,th8test}.py` (anchor-based, also apply to other trees),
  `impact.py`, `spr.py`, `tcfind.py`, `bitcmp.py` (ensfc2's), `mkrun.sh`, `runq.sh`, `mkrestart.sh`, `gates.sh`,
  `analyze1.sh`, `analyze2.sh`, `chk.sbatch`; logs in `logs/` (analysis1/2, eb_/fs_/ft_ meter tables, es2c_/es2t_).
- Hercules `$C`: trees n0 b1 b2 m1 s1, exes `exe/fv3_c_{n0,b1,b2,m1,s1}.exe`, runs in `runs/`.
- Disk: `$C` holds 278 GB (5 build dirs + runs, incl. two 10-day runs); build dirs `<tree>/ufs-weather-model/tests/build_fv3_c_*` can go once the exes in `exe/` are no longer needed.
