# preclag: precipitation hand-off lag (EML) and ensfc2 16 meta fix

## Status

preclag delivered two diffs, both in the final series (`replay/SERIES.md`).

| Row | Diff | Class | Switch: default / all-on | Before → after (24 h, frame F, W m-2) |
|---|---|---|---|---|
| 41 | `41_sfc_options_r4_16b.diff` = `patches/16b_sfc_options_r4_meta_fixed.diff` (ensfc2 16 with the `[tgrs]` standard name fixed) | PC | `sfc_precip_enthalpy`, `lw_sfc_return`, `noahmp_pore_air` F / T | 16 as delivered fails capgen; 16b builds |
| 46 | `46_PL1.diff` = `patches/01_PL1_sfc_precip_t1_carry.diff` | BUG FIX of the EP1 option | `sfc_precip_t1_carry` F / T (acts only with `sfc_precip_enthalpy`) | hand-off lag −1.2106e-2 → 0 (exact) |

- **Decided and built:** PL1 is folded into `sfc_precip_enthalpy` (proposal §15) in `full14`
  (`energy/patches/full14/delta_PL1_folded_into_EP1.diff`): lag 0 with EP1; with EP1 off, bitwise to a tree with no
  PL1 code; the restart field is written only with EP1 (energy §9.9).
- Gates (`-no-fma`): carry off vs full12 all-on, all switches default, restart, 3×8 vs 4×6, meters passive: all 0
  differing. Impact is at noise: T rms 0.139 K (noise 0.149), land LH +0.06 % (full list in the original Status).
- No red team. History: [`report.history.md`](report.history.md) holds the original Status block, verbatim.

## Log

### Task 1: ensfc2 16 meta defect (done)
- `patches/16b_sfc_options_r4_meta_fixed.diff` = ensfc2 `16_sfc_options_r4.diff` with one `+` line changed (meta `[tgrs]`
  standard_name `air_temperature` -> `physics_timestep_initial_air_temperature`). No context line changes, so 16b applies
  -F0 wherever 16 applies.
- Existing variable: `physics_timestep_initial_air_temperature` is Statein%tgrs in GFS_typedefs.meta (line 199), so no new
  metadata is needed; `air_temperature` is gt0 in both GFS_typedefs.meta and GFS_MP_generic_post.meta (duplicate -> capgen abort).
- Matches energy: `$E/accepted/27` (= 16 verbatim) vs 16b differ in exactly that line; energy's mk11b.sh applied the same
  one-line sed; full12's GFS_MP_generic_post.meta tail equals 16b's 25 added lines byte for byte.
- Note: ensfc2's report describes PH1's T1 as save_t (before MP tendencies); the built name is the step-start T1, which is
  what the frame-F meter (emf(13) = tgrs(:,1) at probe 1) books precipitation at. The step-start T1 is the consistent one.

### Task 2: PL1 design (`patches/01_PL1_sfc_precip_t1_carry.diff`, `tools/apply_pl1.py`)
- **Cause (code):** GFS_MP_generic_post sets tprcp/srflag in step N; the atmosphere's frame-F budget exports that water at
  T1(N) = Statein%tgrs(:,1) of step N (meter emf(13); PH1 L_f(T1) uses the same). The surfaces consume tprcp/srflag in
  step N+1, and EP1 books its enthalpy with that step's lowest-layer T: Noah-MP soil and glacier `sfctmp`, sfc_sice `t1`.
  Mismatch per step = c P(N) (T1(N+1) - T1(N)).
- **Fix:** new gfs_physics_nml switch `sfc_precip_t1_carry` (default .false.). When on:
  - GFS_MP_generic_post stores `Sfcprop%tprcp_t1 = tgrs(:,1)` next to tprcp (new arguments; tgrs already passed by 16b);
  - noahmpdrv passes `tprec` (carried T, else that step's T1) to noahmp_sflx and noahmp_glacier, which use it in place of
    sfctmp only in the EP1 target enthalpy; PAH and stored-water bookkeeping unchanged (EP1 puts the remainder in the top layer);
  - sfc_sice uses it in place of t1 in the EP1 snowfall content;
  - phy_data restart field `sfc_precip_t1` (registered only when on). A restart without it reads 0, and 0 means "use this
    step's T1" (stock behaviour for one step); same fallback at a cold start (kdt = 1).
- Off: the surfaces get tprec = their own T1, the same value as before; nothing new in the restart.
- Same mass: tprcp and srflag are written only in GFS_MP_generic_post (and GFS_stochastics under do_sppt, off here);
  between MP_generic_post(N) and the surfaces of N+1 nothing writes tprcp, srflag or tprcp_t1. The meter checks it (below).
- **Not changed, by decision:** NSST. Its qrain is Gosnell's wet-bulb skin flux on the current state (alfac, wetc, dwat,
  dtmp, q all from step N+1's T1, q1); it is not a frame-F booking, never reaches the atmosphere or a closed budget (prescribed
  tref), and swapping only the dry-bulb T would make the formula less self-consistent. The open ocean takes precipitation
  as an open boundary whose enthalpy is by definition the atmosphere's export. RUC/Noah are not in this suite and have no EP1.
- **Meter v2** (`patches/meter_PL1_lag_v2.diff`, `tools/apply_meter_pl1.py`, on mq12 + PL1): the lag of P(N) is taken at
  probe 1 of step N+1 (before the surfaces) against the T the surfaces will use (tprcp_t1 if on, else T1(N+1)); EML has 8
  columns: lag, land, unmatched, PH1 swap, sea ice, stock lag (= old EML), sum|c P_sfc - c P_atm|, sum c P_atm.
  `tools/frameF_table_pl.py` = energy's frameF_table + those columns.
- Trees built: pl1 (job 10156464), mpl1 (10156465); orchestrator `final_pl1.sh` -> `logs/final_pl1.txt`.

### First results (18 Oct)
- g_off (pl1, final12 switches, carry off, job 10156492) vs energy rs12_S (full12 all-on): atmf024 0/18, sfcf024 0/194,
  sfc_data 0/105, phy_data 0/24 differ. Switch off is bitwise (-no-fma).
- m_on (mpl1, final12 switches + carry, job 10156493), frame F, 24 h, W m-2:
  RESIDUAL net of declared -1.12e-11; EML lag at the booked T **0 exactly** (land 0, sea ice 0); stock lag on the same
  trajectory -1.210e-2; surface-side vs atmosphere capacity sum|d|/sum 7.2e-12; unmatched columns only at step 1.

### Final gates and impact (orchestrator `final_pl1.sh`, `logs/final_pl1.txt`)
- Jobs: g_off 10156492, m_on 10156493, rs 10156543/10156544, rsL (4,6) 10156576/10156577, m_off 10156592, gA_off 10156598.
- Old vs new lag meter (`tools/eml_steps.py`, m12 vs m_off): 118 paired steps, max |diff| 0; new-only last step
  -3.99e15 J = -9.1e-5 W m-2, which is the m_off - m12 EML difference.
- Red team: other MPs pass through the same MP_generic_post code (store only); RUC/Noah have no EP1; GFS_stochastics with
  do_sppt rescales tprcp after MP_generic_post (mass, not T; off here); threads: per-column locals only; a missing
  restart field reads 0 (phy%var2 = zero) = fallback to the step's T1.
