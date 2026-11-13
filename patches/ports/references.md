# References for the water-conservation fixes

**Status (2026-10-14).**
- **Records:** all 42 records below were verified, 37 DOIs against Crossref and 4 against DataCite. BibTeX is in [`references.bib`](references.bib).
- **Content reads:** five sources were read for their content, so that the claims citing them rest on the text and not just the title. They are marked **content** in the table.
- **AMS full text:** AMS blocks automated access. Juang & Hong (2010), Thompson et al. (2008) and Thompson & Eidhammer (2014) were read from Wayback Machine snapshots of the AMS full-text pages (2017-06-27 and 2026-10-12).
- **Not in the bib:** a "Bernardet et al." CCPP paper and a journal article on the SAMF TVD change could not be found. NCEP Office Note 506 is the TVD source; Heinzeller et al. (2023) is the CCPP paper.
- **Do not cite yet:** Thuburn (2008). Its record is verified, but its abstract was not reachable.

## What the sources say about the claims

| Claim | Source | Finding |
|---|---|---|
| **T1:** TEMPO's semi-Lagrangian edge test is inverted | Juang & Hong 2010, appendix eq. (A4) | The published piecewise-linear (PLM) safeguard is "Q⁺ = Q⁻ = Q̄ if Q⁺ < 0 or Q⁻ < 0" (Q = ρq).<br>CCPP Thompson `semi_lagrange_sedim` (f601ce98, line 6351, `qpi<0 .or. qmi<0`) is exactly this PLM, steps (A1)–(A5). Its header comment calls it "piecewise parabolic", which is wrong.<br>TEMPO's `qpi > 0 .or. qmi < 0` (c62699fb, line 1911) contradicts (A4): it keeps exactly the profile with a negative upper edge.<br>The PPM variant (A6)–(A10) has a limiter instead and no revert-to-constant test.<br>**Cite T1 as the PLM safeguard, eq. (A4).** |
| No floor in the published scheme | Juang & Hong 2010, eqs. (5), (9), (12), (14), (15) | Mass conservation is local and total, and surface precipitation is the mass that arrives below ground (14b).<br>The paper has no threshold. The code floors (`max(qn,R1)` in CCPP, `max(xr,limit)` in TEMPO) are additions that do not conserve mass. This supports TH7. |
| R1 = 1e-12 | Thompson et al. 2008 | The only 10⁻¹² in the paper is the initial mass (kg) of a nucleated ice crystal (CCPP `xm0i = R1`).<br>The paper does not document R1 as a mixing-ratio threshold. |
| Which density sedimentation uses (TH4, TH5) | Thompson et al. 2008; Thompson & Eidhammer 2014 eq. (1) | Sedimentation is described only as "forward-in-time, backward-in-space".<br>Eq. (1) is flux form with ρ "the air density", moist or dry not stated.<br>Neither paper fixes the density, so the host's dry mass is a coupling choice the papers leave open. |
| TEMPO's documentation | TEMPO README; Jensen 2024 workshop abstract | There is no journal article for TEMPO.<br>The README names the papers to cite (Thompson 2004, 2008, 2013; Thompson & Eidhammer 2014; Jensen et al. 2023) and warns that the code may differ from them. |
| **SA1:** the SAMF TVD rewrite | NCEP Office Note 506 (Han et al. 2022) | TVD (Thuburn 1993) replaced central differencing in the mass-flux transport.<br>A column-conserving borrowing fixes the remaining negatives (eqs. 10–11).<br>The note warns that zeroing negatives "increas[es] the total tracer amount with time". |
| MPAS 0012: falling water's frictional heating is a real, missing heat source of a few % of latent heating | Pauluis, Balaji & Held 2000; Makarieva et al. 2013 | Read at abstract level. PBH estimate the dissipation in the shear zones around falling hydrometeors at 2–4 W/m² in the tropics; Makarieva et al. revise it to 1–2 W/m², mainly through a shorter mean precipitation path. The supercell's layer-coupling term is 2.75 % of gross condensation heating. |
| Physics-dynamics coupling is a known source of spurious sources and sinks | Lauritzen et al. 2018; Lauritzen & Williamson 2019; Lauritzen et al. 2022 | Each was read at abstract level. They support the general framing: a dry-mass coordinate, condensate loading, and inconsistent thermodynamics between the parameterizations and the host. |

## Reference table

| Key | Citation | DOI | Used for | Verified |
|---|---|---|---|---|
| JuangHong2010 | Juang & Hong, *MWR* 138(5), 1778–1791 | 10.1175/2009MWR3109.1 | T1, TH7 | **content** (eqs. A1–A10) |
| Thompson2004 | Thompson, Rasmussen, Manning, *MWR* 132(2), 519–542 | 10.1175/1520-0493(2004)132<0519:EFOWPU>2.0.CO;2 | Thompson scheme | record |
| Thompson2008 | Thompson, Field, Rasmussen, Hall, *MWR* 136(12), 5095–5115 | 10.1175/2008MWR2387.1 | scheme; sedimentation; R1 origin | **content** |
| ThompsonEidhammer2014 | *JAS* 71(10), 3636–3658 | 10.1175/JAS-D-13-0305.1 | eq. (1), ρ unspecified | **content** |
| Jensen2023 | Jensen, Thompson, Ikeda, Tessendorf, *MWR* 151(9), 2307–2332 | 10.1175/MWR-D-21-0319.1 | TEMPO lineage (hail) | record |
| Thompson2013 | ECMWF Workshop on Parametrization of Clouds and Precipitation (2012), ecmwf.int/node/12672 | — | TEMPO lineage | record (pages not confirmed) |
| Jensen2024TEMPO | Joint WRF/MPAS Users Workshop abstract, 2024 | — | TEMPO description | **content** (abstract) |
| TEMPOcode | NCAR/TEMPO c62699fb, `src/module_mp_tempo_main.F90` L1911 | — | T1 | **content** |
| CCPPphysicscode | NCAR/ccpp-physics f601ce98, `physics/MP/Thompson/module_mp_thompson.F90` L6351, L180 | — | T1, R1 | **content** |
| HanPan2011 | *WAF* 26(4), 520–533 | 10.1175/WAF-D-10-05038.1 | SAMF predecessor | record |
| Han2017 | *WAF* 32(5), 2005–2017 | 10.1175/WAF-D-17-0046.1 | SAMF | record |
| HanON506 | NCEP Office Note 506 (2022) | 10.25923/5051-3r70 | SA1 | **content** |
| Thuburn1993 | *QJRMS* 119(511), 469–487 | 10.1002/qj.49711951107 | TVD scheme | record |
| HanBretherton2019 | *WAF* 34(4), 869–886 | 10.1175/WAF-D-18-0146.1 | PBL (ON506 scope) | record |
| Niu2011 | *JGR* 116, D12109 | 10.1029/2010JD015139 | Noah-MP | record |
| Yang2011 | *JGR* 116, D12110 | 10.1029/2010JD015140 | Noah-MP | record |
| He2023 | *GMD* 16(17), 5131–5151 | 10.5194/gmd-16-5131-2023 | Noah-MP v5 | record |
| Ek2003 | *JGR* 108(D22) | 10.1029/2002JD003296 | Noah (classic) | record |
| ChenDudhia2001 | *MWR* 129(4), 569–585 | 10.1175/1520-0493(2001)129<0569:CAALSH>2.0.CO;2 | Noah (classic) | record |
| Lin2004 | *MWR* 132(10), 2293–2307 | 10.1175/1520-0493(2004)132<2293:AVLFDC>2.0.CO;2 | FV3 vertical remap; the PPM limiter J&H adapt | record |
| PutmanLin2007 | *J. Comput. Phys.* 227(1), 55–78 | 10.1016/j.jcp.2007.07.022 | FV3 | record |
| Harris2020 | *JAMES* 12(10), e2020MS002223 (**2020**, not 2021) | 10.1029/2020MS002223 | SHiELD (FV1) | record |
| SkamarockWRF4 | NCAR/TN-556+STR (2019; the v4.3 revision of 2021 keeps the same TN number and DOI) | 10.5065/1dfh-6p97 | WRF | record |
| Skamarock2006 | Skamarock, *MWR* 134(8), 2241–2250 | 10.1175/MWR3170.1 | MPAS MP1/MP2 redesign: positive-definite flux renormalization for unrestricted time steps (WRF `moist_adv_opt=1`) | record (Crossref, 2026-10-14) |
| Skamarock2012 | *MWR* 140(9), 3090–3105 | 10.1175/MWR-D-11-00215.1 | MPAS | record |
| Pauluis2000 | Pauluis, Balaji, Held, *JAS* 57(7), 989–994 | 10.1175/1520-0469(2000)057<0989:FDIAPA>2.0.CO;2 | MPAS 0012 frictional heating of falling water | abstract (Crossref, 2026-10-17) |
| Makarieva2013 | Makarieva, Gorshkov, Nefiodov, Sheil, Nobre, Bunyard, Li, *JAS* 70(9), 2916–2929 | 10.1175/JAS-D-12-0231.1 | the same, revised estimate | abstract (Crossref, 2026-10-17) |
| Hong2004 | *MWR* 132(1), 103–120 | 10.1175/1520-0493(2004)132<0103:ARATIM>2.0.CO;2 | WSM3 (CT-L met) | record |
| BrethertonPark2009 | *J. Climate* 22(12), 3422–3448 | 10.1175/2008JCLI2556.1 | UW PBL (CT-L met) | record |
| GrellFreitas2014 | *ACP* 14(10), 5233–5250 | 10.5194/acp-14-5233-2014 | GF (CT-L met) | record |
| Iacono2008 | *JGR* 113(D13) | 10.1029/2008JD009944 | RRTMG (CT-L met) | record |
| Heinzeller2023 | *GMD* 16(8), 2235–2259 | 10.5194/gmd-16-2235-2023 | CCPP | record |
| Stein2015 | *BAMS* 96(12), 2059–2077 | 10.1175/BAMS-D-14-00110.1 | HYSPLIT | record |
| Nehrkorn2010 | *Meteorol. Atmos. Phys.* 107, 51–64 | 10.1007/s00703-010-0068-x | WRF-STILT | record |
| Hu2019 | *Sci. Adv.* 5(6), eaaw0076 | 10.1126/sciadv.aaw0076 | CT-Lagrange | record |
| Rastogi2021 | *ACP* 21(18), 14385–14401 | 10.5194/acp-21-14385-2021 | CT-Lagrange | record |
| Lauritzen2018 | *JAMES* 10(7), 1537–1570 | 10.1029/2017MS001257 | coupling framing | abstract |
| LauritzenWilliamson2019 | *JAMES* 11(5), 1309–1328 | 10.1029/2018MS001549 | coupling framing | abstract |
| Lauritzen2022 | *JAMES* 14(9), e2022MS003117 | 10.1029/2022MS003117 | coupling framing | abstract |
| Thuburn2008 | *J. Comput. Phys.* 227(7), 3715–3730 | 10.1016/j.jcp.2006.08.016 | — | record; **do not cite yet** |

Checked against: Crossref API, DataCite API, NOAA IR (Office Note 506, repository.library.noaa.gov/view/noaa/36734), GitHub NCAR/TEMPO and NCAR/ccpp-physics. Scratch copies of the archived pages and equation images are in the session scratchpad (`jh/`, `th/`, `on506/`, `code/`).
