*History of `report.md` (encpl): its original Status block, moved verbatim on 18 October 2026. The rest of the report is unchanged in `report.md`.*

## Status (17 Oct 2026, round 2)

- **Frame F** = FV3's own TE (MOIST_CAPPA: cvm·T + φ + K) + Σm(Lv00·qv − Li00·qice), Lv00 = hvap − (cp_v − c_l)T0,
  Li00 = hfus − (c_l − c_i)T0, T0 = 273.15 (hvap, hfus are the enthalpy latent heats at T0, consistent with FV3's heat
  capacities). Water crosses the surface at T1 and φ_s: evaporation brings h_v + φ_s, precipitation takes h_w + φ_s.
- With switch `cpl_water_energy` = 7 (fv_core_nml; bits 1 = PE, 2 = flow work, 4 = sensible exchange) the coupling's
  thermodynamic term closes to −1.4e-12 W m⁻². Off: bitwise identical to fx1. 3×8 vs 4×6 bitwise identical.
- **Flow work (derived, `tools/column_fw.py`).** FV3's path (physics cp·dT at fixed p → con_cp/cvm at fixed volume →
  vapour removed at fixed volume → column relaxes) delivers hvap + R_v·T per kg condensed: +1.2606e5 J/kg into E_F at
  the write, realised as +R_v·T of heating after relaxation (2.593 K vs the isobaric 2.468 K, to 0.4 %). With rain
  removed: +2.10e5 J/kg excess with no bits, +1.26e5 with PE + sensible, 2e-6 with the flow-work bit as well. MPAS's
  stock coupling (internal-energy latent heat at fixed volume) also gives 2e-6. The consv_te fixer moves only
  0.006 W m⁻² between bits 0 and 7. **FV3 is the model that is inconsistent with its own frame.** This holds if
  2.5e6 is the enthalpy of vaporisation (it physically is); GFDL MP reads it as internal energy and gets the same +5 %.
  Impact of fixing: LH −2.0 W m⁻², precipitation −3.4 % (all bits). **Red team: holds with qualifications (below); net sign is a sink. Ash decides.**
- **Gross Pauluis heating** (Thompson sedimentation + SAMF rain profiles exported): +1.47 W m⁻² (deep +0.74, shallow
  +0.05, Thompson liquid +0.21, ice +0.47); lifted vapour −0.99; net +0.48. The PE correction field is linear in the
  flux, so net = gross for the field.
- **Kirchhoff remainder** is −0.013 W m⁻² (round 1's +0.65 was a heat-capacity heuristic). Measured: SAMF deep −0.245,
  shallow +0.128, Thompson +0.028 (K1 → 0). SAMF constant hvap at `samfdeepcnv.f` 349–350, 705, 3354, 3646.
  Option S1 `samf_kirchhoff`. PBL has no phase change; its constant-hvap surface flux is `satmedmfvdifq.F` 2878.
- **Evaporation Kirchhoff is surface-side: −1.90 W m⁻²** (E-weighted skin − lowest-layer T = 2.07 K). The surface
  component must supply per column: E, skin T, latent heat removed per kg, and the temperature at which precipitation lands.
