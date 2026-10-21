@JongilHan66 @lisa-bengtsson, cc @BinLiu-NOAA

# Description

In `samfdeepcnv.f`, `xmbmax` (Han and Pan 2011, eq. 7) keeps the layer CFL ≤ 1 only at `kbcon`, where `eta` = 1. Below cloud base `eta` can exceed 1 (101 at `kb` for elevated convection), so layers from `kb` to `kbcon` reach CFL 24 and heat by tens of kelvin in one step: on develop (f1d68949), `hafs_global_1nest_atm` has 257–351 layer-steps above 4 K per 6 h, up to 52 K (20 perturbed members).

Develop survives, but only just: small, unrelated answer changes push the tail past the limit, and the test stops with `compute_qs: saturation vapor pressure table overflow` after one cell gains about 70 K in a step. 24 of our water/energy bug fixes, none in this code, crashed it in 3 of 20 members, the unperturbed RT member included; develop crashed in none.

Expected: CFL ≤ 1 in every layer, as at `kbcon`. `samfshalcnv.f` has the same code but no event above 4 K here.

### Possible fixes (we can test any)
- **A. Bound `xmb` by the CFL limit in every updraft layer** (tested, works): eq. 7 with the local `eta`, from `kb` to `ktcon`, not only at `kbcon`:
  ```fortran
  !  keep CFL <= 1 in every updraft layer, kb to ktcon, not only at kbcon (eta can exceed 1 there)
        do k = 1, km
          do i = 1, im
            if(cnvflg(i) .and. k >= kb(i) .and. k < ktcon(i)) then
              dp = 1000.0_conv_wp * del(i,k)
              xmbmax(i) = min(xmbmax(i), dp /
       &        (real(grav, kind=conv_wp) * dt2 * eta(i,k)))
            endif
          enddo
        enddo
  ```
  No crash in 40 members (develop and the 24 fixes), at most one layer-step above 4 K per member (≤ 4.8 K, CFL ≤ 0.9), precipitation −0.18 % (*Output*). Bounding only `kb ≤ k < kbcon` gives the same statistics in all 40 members: every binding layer is below cloud base.
- **B. Keep the vapour positive** (tested, does not help): cap `xmb` so that no layer loses more vapour in one step than it holds. Event counts stay at develop's, and the 24 fixes still crash 1 of 20 members.
- **C. Keep `eta` ≤ 1 below cloud base**: no organized detrainment below `kbcon`, or a cap.
- **D. Apply the convective tendencies implicitly, or sub-step them**, so they stay stable at CFL > 1. Sub-stepping only the tracer transport does not change the counts; heat and moisture would have to be included.
- **E. Bound the convective TKE source** (with any of the above). "include TKE contribution from deep convection" (and its shallow twin) adds `0.5·σ·w_u²`, `w_u = η·xmb/(σρ)`, once per call, not as a rate. With a CFL bound it still adds +383 m²/s² per 90 s step at 3.5 km in these cells, about what the PBL removes: `w_u` ≈ 160 m/s at σ's 0.03 floor. Alternatively, take `clamt`'s TKE scaling from the TKE before convection, so the overshoot cannot hold its own entrainment at the cap.

### Questions
1. Which option, and for `samfshalcnv` too?
2. Is the convective TKE source meant to be added once per call (no `dt`), and should `w_u` be bounded?
3. Would you take the bound as its own PR, ahead of other SAMF changes? We can open it.

## Steps to Reproduce

1. Insert the print-only block [`dbg4_deep.f`](https://github.com/pera-noaa/ufs-water-conservation/blob/main/proposal/hafs_samf/dbg4_deep.f) in `samfdeepcnv.f` before "Negative moisture is set to zero after borrowing" (one `DBGSAMF` line per layer heated > 4 K; bitwise the official baseline) and build develop (f1d68949) with the `hafsw` compile in `rt.conf`.
2. Run `hafs_global_1nest_atm` as `rt.sh` sets it up (6 h, about 2.5 min on 6 nodes); more members: `consv_te` = 0.999, 0.998, … in `input.nml`.
3. Count the `DBGSAMF` lines ([`q_stats.py`](https://github.com/pera-noaa/ufs-water-conservation/blob/main/proposal/hafs_samf/q_stats.py)): 257–351 per member on develop, up to 52 K, almost all at `kb ≤ k < kbcon` with CFL > 1.
4. For the crash, add a small answer change, e.g. our SAMF + PBL, Noah-MP, sea-ice/NSST and GFDL MP v3 patches ([`pr_round1_patches/`](https://github.com/pera-noaa/ufs-water-conservation/tree/main/proposal/pr_round1_patches)): 3 of 20 members stop with the overflow, `consv_te` = 1 included.

## Additional Context

* Machine: Hercules (MSU)
* Compiler: Intel Fortran Classic 2021.13.1 (`rt.sh`)
* Suite Definition File or Scheme: `FV3_HAFS_v1_gfdlmp_tedmf` (`hafs_global_1nest_atm`; `dt_atmos` 90 s, `progsigma` false); `samfdeepcnv`, and `samfshalcnv` (same code)
* Related: #82 (2023), the same `compute_qs` overflow in a 25 km RRFS run with GFS v17 P8 physics, cured by a shorter `DT_ATMOS` or `samfdeepcnv.f`'s `cq` back at 1.3; both shrink what one SAMF step can move. #390 edits `samfdeepcnv.f`.

**Why `eta` grows and stays large.** Below cloud base `eta(k) = eta(k+1)/(1 + (xlamue − xlamud) dz)`, with `xlamue = clamt/z` and `xlamud = 0.001 clamt`. Above about 1 km detrainment exceeds entrainment, so for elevated convection (`kb` near 3 km) `eta` grows downward: 1 at `kbcon`, 101 at `kb`. The TKE scaling holds `clamt` at its cap (15 × `clam`) in about 3000 columns per 6 h, and the overshoot feeds TKE (column means up to 2.4 × 10⁶ m²/s² in 20 members), which keeps it capped. Sub-stepping SAMF's tracer transport does not change the counts.

**Fixes we are holding.** SAMF's cloud-base double-counting correction subtracts the TVD-limited value at `kb` and `jmin` instead of what the updraft took (`qo`): SAMF creates 0.8 % of convective rain and a convected tracer loses 2 %/day (C96 `control_p8_ugwpv1`, 24 h). Our fix changes the moisture flux at `kb`, where the overshoots are, and here raises the event count 1.7×; it will follow the option you choose. Our sea-ice/NSST and FV3 fixes also wait for the bound.

Data, scripts and instrumentation: https://github.com/pera-noaa/ufs-water-conservation/tree/main/proposal/hafs_samf

## Output

The crash (the 24 fixes, `consv_te` = 1):
```
FATAL from PE 0: compute_qs: saturation vapor pressure table overflow, nbad= 1
```
Its largest event: layer 18 (`kb` 17, `kbcon` 22) heats 72.8 K and loses 30.2 g/kg of vapour in one step, at CFL 14.3, `eta` 12.2, `xmb` = `xmbmax` (re-spaced):
```
DBGSAMF  i k kb kbcon jmin ktcon  dT(K)      dq(g/kg)   xmb        xmbmax     CFL        eta        del        TKE        clamt
DBGSAMF 16 18 17 22 27 28  7.283E+01 -3.020E+01  3.962E+00  3.962E+00  1.430E+01  1.217E+01  2.976E+00  5.961E+02  1.500E+00
```

Crash rate (6 h; members `consv_te` = 1, 0.999, …):

| Run | Members | Crashed | With a step > 60 K | Largest step per member: median, max |
|---|---|---|---|---|
| develop | 20 | 0 | 0 | 31 K, 52 K |
| + 24 fixes (SAMF, PBL, Noah-MP, sea ice/NSST, GFDL MP, SAMF build) | 20 | **3**, the RT member included | 4 | 40 K, 73 K |
| the 24 minus sea ice/NSST (4) | 20 | 0 | 0 | 32 K, 48 K |
| + all 37 fixes | 10 | 1 | 1 | 33 K, 74 K |

Event counts and precipitation overlap develop's throughout. No single fix stands out: without PBL05, the NSST rain fix or the three sea-ice fixes, the 24 each crash 0 of 10.

The options (6 h, 20 members each; event counts and largest step over the finished members):

| | develop | + A | + B | the 24 fixes | + A | + B |
|---|---|---|---|---|---|---|
| crashed | 0 | 0 | 0 | 3 | 0 | 1 |
| layer-steps heated > 4 K, per member | 257–351 | 0–1 | 246–384 | 241–369 | 0–1 | 252–344 |
| of which layer CFL > 1, all members | 5769 | 0 | 5839 | 5009 | 0 | 5541 |
| largest step | 52.0 K | 4.8 K | 42.2 K | 64.2 K | 4.5 K | 44.0 K |
| largest column-mean TKE where `clamt` is capped, m²/s² | 2.4 × 10⁶ | 434 | 2.3 × 10⁶ | 1.2 × 10⁶ | 417 | 2.3 × 10⁶ |
| mean precipitation, mm/day | 2.4370 | 2.4327 (−0.18 %) | 2.4372 | 2.4365 | 2.4324 (−0.17 %) | 2.4364 |

*Contributors: Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author.*
