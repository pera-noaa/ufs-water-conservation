# SAMF TKE coupling: provenance, users, upstream reports (for ccpp-physics#401)

Researched 2026-10-21 from git history (ufs-community/ccpp-physics `ufs/dev` d9b70feb, NOAA-EMC/fv3atm,
hafs-community/HAFS tags), GitHub issues/PRs, and the two Han papers. "Unverified" means I did not confirm it.

## a. Where each piece came from

| Piece | Introduced | By | Stated rationale |
|---|---|---|---|
| (1a) `clamd=0.03, tkemx=0.65, tkemn=0.05` (±30 % entrainment with sub-cloud TKE) and (3) the convective TKE source `0.5*sigma*w_u**2`, deep and shallow | fv3atm [867dc10](https://github.com/NOAA-EMC/fv3atm/commit/867dc105197efe592cf9da086c4f9a8ed7929285), 2018-06-01, VLab ticket #48136. Same commit adds `satmedmfvdif.f` (TKE-EDMF) | committed by Jun Wang for J. Han (EMC) | CCPP docstring: added "for FY19 GFS implementation". Entrainment "proportional to sub-cloud mean TKE"; TKE from convection "deduced from cumulus mass flux". Published as Han & Bretherton (2019) Eq. 39 |
| (2) `xlamud = 0.001*clamt` and active floor `crtlame = 1.0e-4` (renamed from the commented-out `crtlamu`) | fv3atm [06b956a](https://github.com/NOAA-EMC/fv3atm/commit/06b956a1062ff267e0fe779d8fd44be0986e10c1), 2018-06-05, ticket #51114 | Jun Wang / J. Han | Commit title: "reduce too much cooling at the cloud top". The docstring says occasional crashes with stochastic physics came from cooling and heating near cloud top |
| CCPP port of the 2018 code | [46319db6](https://github.com/ufs-community/ccpp-physics/commit/46319db6), 2018-06-22 (NCAR/ccpp-physics history, same commits) | Grant Firl | Port only, code unchanged |
| (1b) `tkcrt=2, cmxfac=15`, scaling `clamt, xlamdet, xlamddt, cxlamet, cxlamdt` (deep); `cmxfac=15` (shallow) | [109d7f36](https://github.com/ufs-community/ccpp-physics/commit/109d7f36) 2023-04-21 + [c9757285](https://github.com/ufs-community/ccpp-physics/commit/c9757285), in [PR #65](https://github.com/ufs-community/ccpp-physics/pull/65) "PBL and Convection and Microphysics update for HR2", merged 2023-05-09; UFS-WM [#1731](https://github.com/ufs-community/ufs-weather-model/pull/1731) | Qingfu Liu, code from J. Han and R. Sun | PR text: the goal is "to reduce the negative hurricane intensity biases" in **GFS**. Entrainment is enhanced in proportion to TKE above a threshold, alongside the wind-shear term `wush`. Same PR: `cq` 1.3→1.0, CIN trigger tied to `hpbl` |
| Shallow `cmxfac` 15→10 (deep left at 15) | [PR #119](https://github.com/ufs-community/ccpp-physics/pull/119) (HR4), opened 2023-10-16, merged 2024-01-29 | Qingfu Liu / J. Han | PR item 4: the reduction is to avoid "a potential numerical instability due to too much entrainment increase"; also says it improves HAFS |

Note: `xlamud=0.001*clamt` already scaled the sub-cloud detrainment with `clamt` in 2018. That was harmless while `clamt` moved only ±0.03. PR #65 lets `clamt` grow ×15 but leaves `crtlame` unscaled. Neither the 2024 paper nor PR #65 mentions that the sub-cloud `xlamud` is scaled too.

## b. Target system and who runs it

- **The TKE scaling was built for GFS v17** ("HR2" is a GFSv17 prototype tag: [GFSv17.HR1](https://github.com/ufs-community/ccpp-physics/tree/GFSv17.HR1) has no `cmxfac`; HR2/HR3/HR4 do). It was tested in GFS at ~13 km, 2020 season (Han et al. 2024). HAFS adopted it afterwards.
- The TKE parts run only when `ntk > 0` (TKE tracer from `satmedmf`/`isatmedmf=1`) and `.not. hwrf_samfdeep`. `hwrf_samfdeep` (HWRF SAS branch) was added by Man Zhang ([5ca808ea](https://github.com/ufs-community/ccpp-physics/commit/5ca808ea), 2019-12-13). I found no UFS-WM regression test or HAFS config that sets it true. Since `cmxfac` there is no switch for the scaling alone; `clam_deep` changes only the base value.
- `progsigma=.true.` keeps the scaling. It does change the TKE source: `sigma = sigmab` (floor `sigmind=0.01` without `progomega`) replaces `max(sigmagfm, betaw=0.03)`. A floor up to 3× lower means up to 3× more TKE for the same mass flux (code reading, not run).

| System | Suite / PBL | 1a, 2, 3 | 1b (`cmxfac`) | progsigma / dt |
|---|---|---|---|---|
| GFS v15 / GEFS v12 (IPD) | not checked | code present | no | PBL believed K-EDMF (`ntk=0`), so TKE parts inert: unverified |
| GFS v16 (fv3atm production/GFS.v16 → NCAR/ccpp-physics@01ed01fb) | GFS_v16, satmedmfvdifq | yes | no | - |
| HAFS v1 (hafs.v1.0.5 2023-09-15 and fv3atm production/hafs.v1 → hafs-community/ccpp-physics@a501737d) | HAFS_v1_*_tedmf | yes | **no** | dt 90 s |
| HAFS v2.0 (hafs.v2.0.1 2024-05-21 → @a4a2b9bc) | HAFS_v1_thompson_nonsst (HFSA) | yes | deep 15, shallow 10 | progsigma F (HFSA AL), T (EP/CP, HFSB); dt 90 / 72 s |
| HAFS v2.1 (hafs.v2.1.2 2025-04-19 → @fbee8277) | same | yes | deep 15, shallow 10 | progsigma T everywhere (`hafs.conf`), dt 90 s |
| HAFS develop | HAFS_v2_coupled, `clam_deep=0.15` | yes | yes | progsigma T, dt 90 s |
| GFS v17 / P8 (production/GFS.v17 → @8007f2c3) | GFS_v17_p8, satmedmfvdifq | yes | yes (GFSv17.p8 2022 tag: no) | progsigma T in UFS-WM gfsv17 tests |
| GEFS v13 | UFS-WM `cpld_control_gefs` uses GFSv17 physics and progsigma T | yes (code) | yes (code) | operational config unverified |
| RRFS v1 (production/RRFS.v1 → @edd85a55) | v1beta: MYNN, **no SAMF**; `RRFS_sas` pairs MYNN + samfdeepcnv | code present | code present | whether `ntk>0` under MYNN: unverified |

HAFS v2 operational dates: PNS [24-05](https://www.weather.gov/media/notification/pdf_2023_24/pns24-05_hafsv2_comments.pdf) proposes "early Summer of 2024", with prognostic sigma "HFSB only". HAFS v2.1 is about 2025-07-29 per [SCN 25-48](https://www.weather.gov/media/notification/pdf_2025/scn25-48_HAFSv2.1.pdf) (date unverified).

## c. Upstream reports

- [ccpp-physics#82](https://github.com/ufs-community/ccpp-physics/issues/82) (2023-06-14, open): `compute_qs` overflow and CFL failures right after PR #65, at 25 km/dt 180 s. Reverting `cq` fixed it; Han replied he did not think `cq` could cause an instability. `cmxfac` was never tested.
- [ufs-weather-model#1742](https://github.com/ufs-community/ufs-weather-model/issues/1742) (2023-05-08, closed 2023-10-27, cause not recorded): `regional_atmaq_faster` died with `compute_qs: saturation vapor pressure table overflow` on WCOSS2/Acorn, starting with #1731 (the HR2 merge). Jun Wang called it "a stability issue".
- SRW App [#827](https://github.com/ufs-community/ufs-srweather-app/issues/827), #874, #923, #693: CFL failures after the same hash bump, worked around by lowering `DT_ATMOS`.
- ccpp-physics PR #119: the authors concede the instability risk for shallow convection only, and reduced `cmxfac` there to 10.
- I found nothing upstream on: eta > 1 below cloud base, the TKE source being applied per call rather than as a rate, TKE blow-up, `tkcrt`, or HAFS crashes tied to SAMF. That covers ccpp-physics, NCAR/ccpp-physics, ufs-weather-model, fv3atm, hafs-community/HAFS and NOAA-EMC/HAFS. HAFS GitHub issues are sparse, so EMC-internal reports may exist: unverified.

## d. Literature

- **Han & Bretherton 2019**, *Wea. Forecasting* 34, 869-886, [doi:10.1175/WAF-D-18-0146.1](https://doi.org/10.1175/WAF-D-18-0146.1) ([NOAA PDF](https://repository.library.noaa.gov/view/noaa/37598)):
  - §2: entrainment rises or falls 30 % across TKE 0.05-0.65 m² s⁻².
  - Eq. 39 is written as a step increment, `TKE = TKE + e_c`, with `e_c = 0.5 σ_c w_c²` and `w_c = M_c/(ρ σ_c)`. It is not a rate, and has no Δt or cap.
  - The paper says it time-splits the TKE equation "to avoid a numerical instability" at large Δt. It gives no such guard for e_c.
  - The motivation is tropical upper-troposphere mixing (their Fig. 1).
- **Han et al. 2024**, "Updates in the NCEP GFS PBL and Convection Models with Environmental Wind Shear Effect…", *Wea. Forecasting* 39(4), 679-, [doi:10.1175/WAF-D-23-0134.1](https://doi.org/10.1175/WAF-D-23-0134.1) ([NOAA PDF](https://repository.library.noaa.gov/view/noaa/63668)):
  - §2b: the ±30 % rule was meant for typical PBL TKE. In hurricanes TKE is much larger.
  - Eq. 5 above `e_th = 2 m² s⁻²`: `(ε, δ) = (1 + ē/ē_th)(ε, δ)`.
  - The ×15 cap (`cmxfac`) appears in neither the paper nor the PR text. It is code-only.
  - The paper does not mention stability or the sub-cloud layer.
  - Tested in GFS at ~13 km. It was "being tested" in HAFS at the time of writing.
- **Han et al. 2017**, *Wea. Forecasting* 32, 2005-2017 (scale/aerosol-aware SAS, `betaw`, σ): predates the TKE coupling and does not discuss it.
- I found no HAFS physics paper (2022-2025) that documents `cmxfac`/`tkcrt` or the convective TKE source. The HAFS [physics docs](https://hafs.readthedocs.io/en/latest/CustomizingTheWorkflow/PhysicsSchemes.html) list only "sa-SAS +shear", `clam_deep` and `progsigma`. EMC Office Notes: not found, unverified.
