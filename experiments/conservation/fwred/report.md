# fwred: red team of encpl's "flow work" claim (bit 2)

## Status (17 Oct 2026): HOLDS WITH QUALIFICATIONS

**Mechanism confirmed.** The derivation, the code path and an independent dynamic test all agree.
Applying the physics' isobaric enthalpy latent heat (hvap) to U at fixed delz, then letting the column relax,
delivers hvap + Rv*T per kg condensed. The correct fixed-volume value is L_e = L_h - Rv*T.

## 1. Derivation (single layer, no E_F shortcut)
- Isobaric: H = sum m h is conserved, with h_v = cpv T + Lv00 and h_l = cl T. Relaxation from a fixed-volume
  write conserves U_layer + p*V (the overlying column's PE). V0 is the hydrostatic volume of the ORIGINAL gas,
  so H_final = U_write + n R T0.
- FV3 write: U_write = U0 + (u_l - u_v)dm + hvap dm, so H_final - H0 = [hvap - (L_h(T) - Rv T)] dm.
  At T0 this is Rv*T0*dm = 1.2606e5 J/kg.
- What hvap contains: L_h = L_e + p*dv_v. The Rv*T part is work done ON the layer by the overlying column as the
  gas volume shrinks. FV3 never shrinks delz at the write, so the dynamics releases that work again.
  The excess is that release counted twice.
- Pure sensible heating with cp/cv is correct (no change in gas content). The defect needs a change in the vapour
  mass at fixed delz.

## 2. Code (encpl/src copy of UFSATM)
- `atmosphere_state_update`: delp is rebuilt from the physics water. delz is untouched.
- `fv_update_phys`, nonhydrostatic, `phys_hydrostatic=.false.` (the value set in every encpl run):
  moist_cv, then `pt += t_dt*dt*cp_air/cvm`, with delz fixed. U gets cp_air*dT_phys*m = hvap*dm.
- `phys_hydrostatic=.true.` branch: moist_cp, and delz *= T_new/T_old. The rescale ignores the change in gas
  content, so the same Rv*T excess appears.
- Hydrostatic dycore: delz is diagnostic, so the excess is zero there.

## 3. GFDL MP (fv_sat_adj, v1_2019, v3_2022)
- Nonhydrostatic: c_vap = cv_vap and lv00 = hlv - (cv_vap - c_liq)*tice.
- So L(T) = L_e,true(T) + Rv*tice. The slope is correct; the offset is a constant 1.26e5 J/kg (+5 %), not Rv*T.
- The scheme is energy-conserving in its own frame, but that frame's latent heat is about 5 % high.
- With hydrostatic or phys_hydrostatic, it uses cp (enthalpy), which is consistent.

## 4. Test (tools/relax_column.py)
1-D compressible Lagrangian column: explicit acoustic integration, exact adiabat, damping heat returned to the
column, energy drift 0.6 J/m2. Case: 1 g/kg condensed at 747 hPa and T0.

| case | dT (K) | excess vs fixed-volume L_e (J/kg) |
|---|---|---|
| isobaric truth | 2.4742 | |
| fixed volume, L_e, relaxed | 2.4714 | ref (-2.8e3 vs isobaric) |
| FV3 path, relaxed | 2.5958 | +1.2570e5 (Rv T0 = 1.2606e5) |
| FV3, vapour precipitated out | 2.6051 | +1.2570e5 |

## 5. MPAS
Check: isobaric dtheta, then theta_m rebuilt at fixed rho_d. This gives cv dT = (L_h - Rv T)|dq|, which matches
encpl's statement.

## Qualifications
- **Global sign.** The global net is a SINK of 0.62 W/m2, not a creation: FW = -Rv sum dmv T = -0.620.
  - Vapour entering the PBL at warm T misses +Rv T.
  - Condensation aloft gains Rv T.
  - The gross terms are about 4 W/m2 each (estimate, Rv*T*P). Bit 2 therefore ADDS 0.62 W/m2 net: it cools the
    condensing levels and warms the PBL.
- **Scope of bit 2.** It acts on every vapour mass change (surface entry, PBL and convective transport), not only on
  condensation. That is correct (open-system enthalpy flux), but describe it that way.
- **Attribution.** -3.4 % precipitation is the all-bits result. Bit 2 alone gives LH -1.97 W/m2.
- **Classification.** PHYSICS CORRECTION of the coupling convention, consistent with FV3's own frame. Forecast
  improvement is not shown.
- **Literature.** Lauritzen et al. 2022, §4.5.2 gives the cp/cv rescaling (which FV3 follows) and leaves "other
  inconsistencies" out of scope. It does not treat Rv*T, so it neither supports nor contradicts the claim.
- **Not done.** No real-model column test. The remaining assumption is that FV3's acoustic solver and remap
  conserve E_F through the relaxation; encpl's fixer delta of 0.006 W/m2 supports this.
