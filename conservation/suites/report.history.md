*History of `report.md` (suites), moved verbatim on 18 October 2026. The head is `report.md`.*

# Suites: E.3 MYNN-EDMF, E.4 GFDL MP v3, E.5 Grell–Freitas — water, passive tracer and energy in their own suites

## Status (18 Oct 2026, round 2 done)

- **Water closes to round-off in every scheme metered** (24 h C96, 64-bit dycore, -no-fma, deterministic meter), final
  tree (`x10`/`m10` = series 01–08): MYNN −5.5e-15 kg m-2/day, GF +2.5e-16 (`gf_closure`), GFDL MP v3 −9.3e-16,
  satmedmfvdifq −3.6e-16 (was +2.6e-8, fix 05), Thompson ≤3e-15, dycore+coupling ≤1.1e-15.
- **Decomposition (round-2 item 1) fixed:** p8_mynn 3×8 ≠ 4×6 was SAMF deep returning early from a block where no
  column is convective *before* the cellular-automaton trigger (`do_ca`/`ca_trigger`, on in every p8 suite) can turn
  a column back on; first seen at step 46, one column (127.77E 13.44N). Fix 08 (BUG FIX): no early return while a
  later CA re-enable is possible. 3×8 = 4×6 bitwise in p8_mynn (default and all-on), RAP all-on, gfdlmpv3; impact
  below noise (rms 0.3–0.7×).
- **Energy (round-2 item 2):** MYNN θl-mixing gap closed exactly by opt-in 06 `mynn_mix_sl` (static-energy mixing):
  0.47 → 2e-9 W m-2; GFDL MP v3: the 0.12 W m-2 is falling-precipitation potential energy turned into heat (+0.61, a
  frame term: closes once water PE is counted) plus a real bug, rain sedimentation exchanging heat with the ICE heat
  capacity (fix 07, BUG FIX, 0.21 W m-2); remaining in GFDL's own frame with PE −0.007 W m-2 (w-sedimentation KE not
  metered). GF −0.26 W m-2: inherent (two incompatible ice partitions), not fixable without restructuring.
- **satmedmfvdifq (item 3):** surface fluxes applied with ρ_a·(zi2−zi1) instead of the host layer mass del/g
  (nonhydrostatic dz): fix 05, 2.6e-8 → 3.6e-16; impact at noise. Also in control_p8 (GFS v17).
- **mynnred corrections folded in:** 01b v2 (moisture_check after Dth with a scratch θ: snow fill now counted; forced
  snow-fill gate: v1 loses L_s·fill = 3.59e15 J in step 1, v2 6.6e5 J = 2e-10 of it); 01(d) hflx/qflx converted with
  the surface schemes' ideal-gas density (SMX 46 = reported E = applied E exactly); SMX 40 is zero by construction
  after 01b (not a gate), SMX 41 includes snow; impacts now area/mass weighted; 02 wording fixed.
- **Ash decides:** 03 `gf_closure` (+8.6 % precipitation); 06 `mynn_mix_sl` (PHYSICS CHANGE, impact beyond noise);
  01b unconditional with the largest impact (T −0.063 K).

| # | diff (`patches/`) | scheme | class | switch | closes | 24 h impact, area/mass-weighted (noise = consv_te 0.999) |
|---|---|---|---|---|---|---|
| 01 | `01_E3_mynn_surface_flux_density_dew_and_filler_mass.diff` | MYNN | BUG FIX (a,b,c) + NUMERICAL CONSISTENCY (d) | — | water +4.53e-2 → −5.5e-15 kg m-2/day | p8: LH +0.56, T2m −0.021 K, ps rms 1.19×; rap: LH +0.45, T2m −0.021 |
| 01b | `01b_E3_mynn_moisture_check_latent_heat_double_count.diff` | MYNN | BUG FIX (energy) | — | +8.0 W m-2 spurious heat → 0 | p8: T −0.063 K, LH +3.12, SH +0.42, ps rms 2.37×; rap: T −0.049, LH +3.82 |
| 02 | `02_E4_gfdlmp_v3_mass_basis.diff` | GFDL MP v3 | BUG FIX | — | water −8.39e-3 → −9.3e-16 | T +0.001 K, precip +0.16 %, rms 1.1–1.3× |
| 03 | `03_E5_gf_water_closure.diff` | GF | BUG FIX + NUMERICAL CONSISTENCY | `gf_closure` | water −1.37e-1 → +2.5e-16 | precip +8.9 % (+1.9e-6 kg m-2 s-1), SH −0.10, T −0.011 K |
| 04 | `04_E3c_mynn_surface_heat_flux_theta.diff` | MYNN | NUMERICAL CONSISTENCY | `mynn_sfc_heat` | SH applied = reported | at noise (0.9–1.2×) |
| 05 | `05_PBL_satmedmfvdifq_surface_flux_layer_mass.diff` | satmedmfvdifq | NUMERICAL CONSISTENCY | — | water +2.6e-8 → −3.6e-16 | at noise (1.0×) |
| 06 | `06_E3d_mynn_static_energy_mixing.diff` | MYNN | PHYSICS CHANGE | `mynn_mix_sl` | θl-energy 0.47 → 2e-9 W m-2 | p8: SH −0.68, LH +1.75, T2m +0.068 K, rms 1.3–1.5× |
| 07 | `07_E4c_gfdlmp_v3_rain_sedimentation_heat_capacity.diff` | GFDL MP v3 | BUG FIX (energy) | — | own-frame+PE gap +0.20 → −0.007 W m-2 | T −0.003 K, rms 1.1–1.3× |
| 08 | `08_SAMF_deep_ca_trigger_early_return_decomposition.diff` | SAMF deep | BUG FIX (reproducibility) | — | 3×8 = 4×6 bitwise | below noise (0.3–0.7×) |
| — | `not_proposed/E4b_gfdlmp_v3_host_constant_pressure.diff` | GFDL MP v3 | tested, not proposed | `gfdl_mp_host_cp` | — | sedimentation heat stays cv-based; worse in its own frame |

The diffs are a series: apply 01, 01b, 02, 03, 04, 05, 06, 07, 08 in order with `patch -p1` at the root of
`$U/cons/energy/full10/ufs-weather-model` (03, 04 and 06 add switches to `GFS_typedefs`). Checked: the series applied
to the pristine sources reproduces the tested sources (`work/`) exactly. The final trees `x10` (no meter) and `m10` (meter) were built from exactly these files.
Meters (instrumentation, separate): `meters/01_suites_meter.diff` (on full10), `meters/02_suites_meter_on_fixes.diff`
(on the series; adds the GF-closure fixer counters), generator `meters/instrument_sm.py`.

## 1. Setup
- Hercules `$S = $U/cons/suites`; local `conservation/suites/`. `base/` = rsync of `$U/cons/energy/full10` (all_full:
  develop @112b1d46 + water series + conservation fixes). Every tree = base + `tools/nofma.py` (all arms) + optional
  meter + fixes (`tools/mk_tree.sh`); `tools/build.sbatch`: APP=ATM, 64-bit dycore, CCPP_SUITES=FV3_GFS_v17_p8_mynn,
  FV3_GFS_v16_gfdlmpv3, FV3_RAP.
- Cases: copies of the develop RT dirs `$U/suites/wb/orig_{control_p8_mynn, control_iovr4_gfdlmpv3, rap_control}` →
  `$S/tmpl/<test>` (real files), 24 h, C96L127, 2021-03-22 06Z, dt 720/720/300 s, layout 3×8. Two passive tracers
  (`tools/make_ic2.py`): `pt_u` uniform 1e-6, `pt_s` structured (S of tracer/scripts/make_ic.py); before `cld_amt` in
  the GFDL suite (dnats = 1). Noise control per suite: ctl exe with `consv_te = 0.999` (`c999_*`).
- Tools: `analyze_sm.py` (tables), `cmp_bit.py` (bitwise, all variables), `impact.py` (rms/mean vs the noise pair),
  `mkrun.sh`, `runs.sbatch` (several 2-node runs per job), `mkrs.sh` + `rs.sbatch` (restart 12+12, layout 4×6).

## 2. The meter (`meters/`)
Probe schemes after named schemes in each suite (segments = rows of the tables below; p8_mynn: interstitial_1 |
surface_generic_post | mynnedmf_wrapper_post | GWD_post | DCNV_post | cnvc90 | MP_post | physics_post; gfdl: … PBL_post
| GWD_post | DCNV_post | SCNV_post | cnvc90 | MP_post …; rap: … mynnedmf_wrapper_post | GWD_post | interstitial_3 |
DCNV_post | interstitial_4 | cnvc90 | MP_post …). Each probe stores per column the effective state gq0 + dtp·dqdt with
host mass Δp/g: W (six species), frame-P energy cp·T + hvap·qv − hfus·(qi+qs+qg), KE, frame-F enthalpy (informative),
tracer masses, Σ m·|q_u − 1e-6|, vapour and ice. Water residual r = ΔW − (E − P), E = dqsfc1/hvap (as the PBL reports),
P = the scheme's own precipitation output; energy r_E = ΔE_P − F, F = SH + hvap·E (PBL), hfus·frozen MP precip (MP).
Rows "PHYSICS" (probe 1 → last) and "DYN+coupling" (last of step n → first of n+1) close the step. Per-rank double
sums → MPI_Gather → summed on root in rank order (deterministic). Scheme-internal terms (SMX): MYNN (E reported /
pre-clip, surface source as solved, ρdz-frame ΔW before/after `moisture_check`, host-frame ΔW of its tendencies, dew cut,
SH reported/solved, θl-equation energy split, filler heat/amount), GF (raincv, prets/pret/pretm and host ΔW for
shallow-only/deep/other columns, GF-shallow own-frame budget, floors, closure-fixer counts), GFDL (scheme-frame and
host-frame ΔW, P before/after rainmin zeroing, settled cloud water).
Validity: ctl vs m0, all 3 suites: 0 differing variables (atmf024, sfcf024, RESTART); fxa6 vs mf6 and fx6(s/cs) vs
mf6(s/cs): bitwise. Thompson closes to 1e-15 in its own segment; DYN+coupling water ≤ 5e-15 kg m-2/day.

## 7. Gates (all -no-fma, 24 h, atmf024 + sfcf024 + RESTART, every numeric variable)

| gate | runs | result |
|---|---|---|
| meters passive, unfixed | ctl vs m0, 3 suites | 0 differ |
| meters passive, fixed | fxa6 vs mf6 (3 suites); fx6s vs mf6s; fx6cs vs mf6cs (and mf7cs) | 0 differ |
| switches off inert | fx6 (03, 04 built, off) vs fxa6, 3 suites | 0 differ |
| restart 12+12 | rs5 rap (03+04 on); rs6p p8_mynn (04 on) | 0 differ |
| decomposition 3×8 vs 4×6 | rap all-on (v5 and v6) | 0 differ |
| decomposition, p8_mynn | ctl (unfixed) and fxa6 | differ in both: pre-existing in this suite, not from these diffs |
| other suites | control_p8 contains none of these schemes; MYNN shared by HRRR/RRFS, GF by HRRR_gf, GFDL v3 by HAFS | not run |

## 8. Out-of-scope observations
- `satmedmfvdifq` in FV3_GFS_v16_gfdlmpv3: water residual +2.6e-8 kg m-2/day (8e-9 of E), not round-off. For the PBL
  owner.
- The h2ophys photochemistry segment produces +5e-7 kg m-2/day of vapour in every suite: the declared S_chem.
- p8_mynn is not decomposition-reproducible (above).

## 9. Jobs
Builds 10155212, 10155399, 10155534, 10155599, 10155690, 10155804, 10155960, 10156142, 10156267. Runs 10155364,
10155389, 10155457, 10155458, 10155580, 10155686, 10155734, 10155857, 10155858, 10156021, 10156022, 10156108, 10156175,
10156176, 10156209, 10156261, 10156361. Red team 10156107 (rs5), 10156210 (rs6p).
Run dirs `$S/runs/<name>`: `ctl`/`c999` (full10), `m0…m3` (meter only), `fxw6` (01+02), `fxa6` (01+01b+02),
`fx6` (01–04), `mf6` (01–04 + meter); suffix `s` = `mynn_sfc_heat`, `c` = `gf_closure`, `cs` = both. All -no-fma.
## Log (as it happens)
- 18 Oct: builds ctl/m0 (10155212), runs 10155364/10155389 (m0, ctl). Meters passive: ctl vs m0 bitwise in all three
  suites (atmf024, sfcf024, RESTART: 0 differing variables), -no-fma.
- Unfixed 24 h, per-process water residual rW = ΔW − (E − P), kg m-2 per day (global mean):
  - p8_mynn: MYNN +4.53e-2 (1.52 % of E); Thompson −9e-16; dyn+coupling ~1e-15 (after the per-column flag fix in m1).
  - rap: MYNN +4.70e-2; GF −1.37e-1 (30 % of its reported precipitation); Thompson −3e-15.
  - gfdlmpv3: GFDL MP v3 −8.39e-3 (1.03 % of P_MP); satmedmfvdifq +3.0e-8 (not ours; noted); photochem segment +5e-7
    in all suites = h2ophys water production (declared source S_chem, not a defect).
- MYNN internals: own rho*dz frame closes (dW − surface source solved = −5e-15); surface source as solved exceeds
  the reported E by rhosfc/rho1 (+0.85 %) and the dew cut (+0.55–0.7 %). After rhosfc = rho(kts) and the limiter:
  p8_mynn +3.9e-7, rap −1.3e-10 — entirely moisture_check (column filler weighted by MYNN's interpolated delp, not by
  the rho*dz the solver conserves). Fix: pass rho*dz.
- GFDL MP v3 (mf1): basis fix closes MP to −1.0e-15 kg m-2/day (7.7e-17 per step max). rainmin zeroing and water0
  are zero in this case (P raw = P booked exactly).
- GF internals (unfixed): shallow-only columns lose 0.281 kg m-2/day, report 0.125 (mid part only); GF's own shallow
  precipitation is 0.237; GF shallow in its own frame removes 0.321 vs pre 0.329 (2.5 % inconsistent); deep columns
  gain +0.0096, other +0.0084.
- Energy, frame P (cp·T + hvap·qv − hfus·ice, W m-2), unfixed: MYNN +11.5 (KE −2.2); GF +1.17 (KE −0.11);
  GFDL MP −0.13; Thompson −0.004/−0.06. MYNN decomposition (p8_mynn, fixed water): SH solved 16.6 vs reported 16.9,
  dissipative heating 1.9, cp·Π·Δθl 26.9 → ~8.4 W m-2 unexplained in the θl equation (m2 splits it by term).
