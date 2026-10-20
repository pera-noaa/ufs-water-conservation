*History of `report.md` (preclag): its original Status block, moved verbatim on 18 October 2026. The rest of the report is unchanged in `report.md`.*

## Status (18 Oct 2026, done)

- **16b** `patches/16b_sfc_options_r4_meta_fixed.diff`: ensfc2 16 with the GFS_MP_generic_post.meta `[tgrs]` standard name
  `air_temperature` (gt0's, capgen duplicate) -> `physics_timestep_initial_air_temperature`, the existing Statein%tgrs name.
  One `+` line; identical to what energy built (mk11b.sh sed; full12 meta tail == 16b block).
- **PL1** `patches/01_PL1_sfc_precip_t1_carry.diff` (-p1 in ufs-weather-model; -F0 clean on full12 and mq12), switch
  `sfc_precip_t1_carry` (gfs_physics_nml, default .false.). Cause: tprcp/srflag of step N are booked by the surfaces in
  step N+1 with N+1's T1, the atmosphere exported them at T1(N). Fix: MP_generic_post stores T1(N) (tgrs(:,1)) with tprcp;
  Noah-MP soil + glacier and sfc_sice use it in EP1's precipitation enthalpy; phy_data restart field `sfc_precip_t1`.
- **Class:** BUG FIX of the EP1 option (EP1 means precipitation lands with the enthalpy the atmosphere exported); only acts
  with sfc_precip_enthalpy on. Could be folded into EP1 (Ash's call).
- **Meter** `patches/meter_PL1_lag_v2.diff` (on mq12 + PL1): lag measured at probe 1 of N+1 against the T the surfaces use.

| 24 h, frame F, W m-2 | full12 / carry off (m_off) | **carry on (m_on)** |
|---|---|---|
| EML hand-off lag, all surfaces | -1.2106e-2 | **0 (exact)** |
| of which land / sea ice | -2.410e-3 / +2.27e-5 | 0 / 0 |
| stock lag on the same trajectory (diagnostic) | -1.2106e-2 | -1.2104e-2 |
| RESIDUAL net of declared | +4.05e-11 | -1.12e-11 |
| fixer window | -2.5e-11 | +1.2e-10 |

- m_off reproduces energy's m12 bitwise (same residual); its per-step lag equals m12's EML at all 118 paired steps
  (max diff 0); the -1.2106e-2 vs m12's -1.2015e-2 is the one extra step (P(119)) the v2 meter counts.
- **Gates (-no-fma), all 0 differing:** carry off vs full12 all-on (rs12_S), 7 files; all switches default vs gA12_off,
  7 files; restart 24 vs 12+12, 3x8 vs 4x6, 4x6 restarted (6 files each; phy_data 25 vars); meters passive on and off.
- **Impact (carry on vs off, 24 h) is noise:** T rms 0.139 K (noise 0.149), ps 7.5 Pa (8.4), LH 2.92 (3.24) W m-2; land LH
  +0.06 % (noise -0.04 %), land t2m -0.001 K (-0.001), soilt1 +0.0006 K / rms 0.17 (noise 0.18), sea-ice tisfc -4e-4 K /
  rms 0.16 (noise 0.24), weasd and icetk at noise.
- **Not exact / not covered:** open ocean is an open boundary closed by definition (NSST qrain deliberately unchanged, see
  design); first step after a cold start, or after a restart file without `sfc_precip_t1`, books at that step's T1 (meter:
  unmatched); surface vs atmosphere precipitation capacity differs by 7.2e-12 relative (pre-existing water hand-off,
  same with carry off); PAH keeps T1(N+1) internally (EP1 tops it up to the target).
- Logs: `logs/final_pl1.txt` (Hercules `$U/cons/preclag/logs/`). Runs in `$U/cons/preclag/runs`.
