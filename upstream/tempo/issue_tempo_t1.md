<!-- SUPERSEDED 13 Nov 2026: NCAR fixed T1 in NCAR/TEMPO#61 (tempo_v3.3.0); do not post. -->
<!-- DRAFT 13 Nov 2026, not posted. NCAR/TEMPO issue, cut from ncar_tempo_issue.md to T1; rows 2-4 as context.
     One-line fix ready: pera-noaa/TEMPO fallback-sign 10dc4577 (CI run 43497239698 pass). Open the PR only if asked.
     The c62699f row is from PREREG_tempo_port.md (Hercules runs 10468158).
     Title: "semilagrangian_sedimentation: the piecewise-constant fallback test is inverted (creates water)" -->

**Describe the bug**
In `semilagrangian_sedimentation`, the test that falls back to piecewise constant has the wrong sign
([L1911](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1911)):
```fortran
        if(qpi(k) > 0._wp .or. qmi(k) < 0._wp) then
```
The safeguard of Juang and Hong (2010, eq. A4) falls back where either edge value is negative. Up to v2 TEMPO tested
`qpi(k).lt.0.0` ([v2, L3313](https://github.com/NCAR/TEMPO/blob/19eaf25f9cb672846778aa23a6fb453067a03a5d/module_mp_tempo_main.F90#L3313)),
as Thompson still does; v3.0.0 (#24) changed it to `> 0`. Now it falls back in almost every cell and keeps the linear
profile only where the upper edge is negative. Those negatives are raised to the floor at
[L1984](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1984),
which creates water.

This changes forecasts, not only the budget. UFS runs `sedi_semi = .true.`, so rain and graupel use this path. With
the test corrected they fall as they did in v2, and grid-scale precipitation is 4–5 % lower in the runs below. Always
falling back (`qpi = qmi = qa`) also closes the budget, with precipitation within 0.6 % of the corrected test's, so
the 5 % comes from the cells where v3 keeps a linear profile with a negative upper edge.

Measured in UFS (C96 `control_p8_ugwpv1_tempo`, 24 h, with ufs-community/ccpp-physics#407) by an in-model water meter,
in % of TEMPO's grid-scale precipitation:

| TEMPO | Residual 6–24 h, as is | with the test corrected | Precipitation 6–24 h |
|---|---|---|---|
| 2856696 (UFS's pin in October) | creates 0.38 % | removes 0.26 % | −5 % |
| c62699f | creates 0.43 % | removes 0.33 % | −4.3 % |

The fallback alone accounts for 0.58 % (6–24 h) and 0.65 % (0–6 h), measured by leaving it out of a build with every
other fix in. Three smaller leaks make up the rest, for context; the first two are in a separate PR (#NN):

| Leak | 0–6 h | 6–24 h |
|---|---|---|
| graupel gains not recomputed after the rain and snow limits | creates 0.86 % | creates 0.004 % |
| sedimentation with the density after latent heating | removes 0.12 % | removes 0.12 % |
| cloud water settling out of the column not counted | removes 0.20 % | removes 0.14 % |

The fix is the one-line sign change. #57 (draft GPU port) carries the same line. v3.2.x hail tuning (#49, #53) was done
with the inverted test, so whether and when to change it is your call; I can open the PR.

**To Reproduce**
UFS `control_p8_ugwpv1_tempo`, C96, 24 h. A meter in `mp_tempo_run` adds each column's water change, in the host's
layer mass, to the precipitation the call produced, and sums them area-weighted. One case, so sizes will vary.

**System Environment**
- OS: Rocky Linux 9 (NOAA Hercules)
- Compiler: Intel Fortran Classic, oneAPI 2024.2.1 (spack-stack 1.9.2)
- MPI: Intel MPI 2021.13
- Configure options: UFS `compile.sh`, `-DAPP=ATM -D32BIT=ON`
