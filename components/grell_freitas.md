# Grell–Freitas convection (`cu_gf_driver.F90`, `cu_gf_deep.F90`, `cu_gf_sh.F90` in ccpp-physics)

**Status (13 November 2026).** GF loses 30 % of its own precipitation: shallow-only columns dry the air but report no
precipitation, and the driver mixes mass bases. A tested fix closes GF's water to round-off but raises global
precipitation 8.9 %, so it sits behind `gf_closure` (default off). Nothing is posted: round-2 issue 4 is drafted and asks
the owner whether the fix should be unconditional or switched. Open: GF's −0.26 W/m² energy gap (two ice partitions),
a restructuring left to the owners, and the untested GF paths (`rrfs_sd` chemistry, `FV3_HRRR_gf`, OpenACC).

## Defects and fixes

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| GF 03 (a) | `raincv` includes the shallow precipitation only when deep convection is active, so shallow-only columns dry the air but report no precipitation. | shallow-only columns: tendencies remove 0.281 kg/m²/day, 0.126 reported (C96 `rap_control`, 24 h) | Report the water the applied tendencies remove, in host layer mass, in every GF column. GF 03 as a whole: −1.37 × 10⁻¹ kg/m²/day (−30 % of GF precipitation) → +2.5 × 10⁻¹⁶. | round-2 issue 4 drafted, not posted | [issue draft](../proposals/round2_issues.md#4-grellfreitas-loses-30--of-its-own-precipitation), [conservation §10](../proposals/conservation_proposal.md#10-other-suites-mynn-edmf-gfdl-mp-v3-grellfreitas), [suites §5](../experiments/conservation/suites/report.md#5-e5-grellfreitas-fv3_rap-rap_control) |
| GF 03 (b) | GF converts q → r = q/(1 − q) and back with r/(1 + r), so the host's vapour change differs from the Δr that GF's heating and condensate use. | water and frame-P energy inconsistent at ~2r | Apply GF's vapour increment on its own basis (`new_q = q + (r_new − r_in)`); untouched columns stay bitwise. | as (a) | [suites §5](../experiments/conservation/suites/report.md#5-e5-grellfreitas-fv3_rap-rap_control) |
| GF 03 (c) | GF shallow is not consistent with itself: precipitation is Σ `pwo`, while the vapour tendency removes it on interpolated interfaces. | −2.5 % (removed 0.321 vs `pre·dt` 0.329, GF's own frame) | Precipitation taken from the applied tendencies (as (a)). | as (a) | [suites §5](../experiments/conservation/suites/report.md#5-e5-grellfreitas-fv3_rap-rap_control) |
| GF 03 (d) | The floors (qv ≥ 1e-16, `cliw`/`clcw` ≥ 0) create a little water; some columns are net moistening. | small (not separated) | Where the tendencies would add water, scale the positive increments to zero net (0.5 % of column-steps; the water cut is 1.7 % of GF's precipitation). | as (a) | [suites §5](../experiments/conservation/suites/report.md#5-e5-grellfreitas-fv3_rap-rap_control), [row 50](../experiments/conservation/replay/patches/50_GF03.diff) |
| GF energy | The deep updraft freezes condensate with its own partition and heat; the driver re-partitions detrained and transported condensate into ice by temperature with no heat; shallow and mid have no ice phase. | −0.26 W/m² (frame P, with `gf_closure`) | None: one ice partition with its heat across `cu_gf_deep`, `cu_gf_sh` and the driver would close it. | asked in round-2 issue 4 | [conservation §13](../proposals/conservation_proposal.md#13-what-remains), [suites §10.2](../experiments/conservation/suites/report.md#102-design-energy-gaps) |

## Not proposed, or a judgement call

- **Unconditional or switched.** (a) is a plain bug, but fixing it raises global precipitation 8.9 % (convective bucket
  +2.9 × 10⁻⁶ kg/m²/s), SH −0.10 W/m², T −0.011 K, rms 1.0–1.4× noise. The patch defaults to off; the owner decides
  ([conservation §15](../proposals/conservation_proposal.md#15-decisions)).
- **Older figure superseded:** the water proposal's candidate gave +8.6 % ([Appendix E](../proposals/water_closure_proposal.md#appendix-e--separate-issues-found-along-the-way));
  the final `gf_closure` gives +8.9 % ([conservation §14](../proposals/conservation_proposal.md#14-corrections)). The
  earlier candidate ([`issue7_gf_shallow_precip_from_tendencies.diff`](../patches/candidates/issue7_gf_shallow_precip_from_tendencies.diff)) is replaced by row 50.
- **Adding GF's own shallow precipitation instead overshoots** (0.126 + 0.237 = 0.363 vs 0.281 removed), because of (c).
- **`rap_control`'s whole-model loss** (−6.0 / −5.8 / −4.8 % of precipitation per 6 h) was placed outside the metered
  physics by the older survey ([ports](../patches/ports/README.md)), while the suites meter places GF's own −30 % inside
  GF. The notes do not reconcile the two.
- **Untested:** GF chemistry transport and wet scavenging (`rrfs_sd`), `FV3_HRRR_gf`, the OpenACC build. GF does not
  transport the generic passive tracers.

## Reproduce

- Patch: [row 50](../experiments/conservation/replay/patches/50_GF03.diff) of the
  [series](../experiments/conservation/replay/SERIES.md) (= `suites/patches/03_E5_gf_water_closure.diff`), switch
  `gf_closure`.
- Meter: the suites meter, `experiments/conservation/suites/meters/01_suites_meter.diff` ([`../methods/METERS.md`](../methods/METERS.md)).
- Runs to compare: the GF table in [suites §5](../experiments/conservation/suites/report.md#5-e5-grellfreitas-fv3_rap-rap_control)
  (`rap_control`, C96, 24 h, `-no-fma`; unfixed, closure off, closure on).
- RT: none for row 50. The earlier candidate ran all 44 GF regression tests with reproducibility intact
  ([Appendix E](../proposals/water_closure_proposal.md#appendix-e--separate-issues-found-along-the-way)). Row 50's gates:
  switch off inert, 3×8 = 4×6 and restart 12 + 12 h bitwise on RAP all-on
  ([suites §10.5](../experiments/conservation/suites/report.md#105-final-gates-x10m10--no-fma)).
