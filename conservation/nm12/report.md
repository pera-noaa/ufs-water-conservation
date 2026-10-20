# NM12 — Noah-MP `combine` melt-out (agent nm12)

## Status

- NM12 is in the final series as row 12 (`12_NM12.diff`, byte-identical to `patches/20_NM12_noahmp_combine_melt_out.diff`). Class BF, unconditional (no switch). SL2 (row 38) needs it for context.
- The fix is `isnow_old < -1` → `isnow < -1` in ccpp-physics `combine` and `combine_glacier` (§1).
- The NOAA-EMC/noahmp companion `patches/20b_NM12-EMC_noahmp-emc_combine_melt_out.diff` is not in the series.
- Red team (§6): BUG FIX. It changes answers only in firing columns; forecast impact is nil at UFS time steps.

| Per firing | `orig` | `fix` |
|---|---|---|
| water error | \|errw\| ≤ 0.16 mm, mean ~1e-3 mm | ≤ 2.2e-12 mm |
| energy error | −1.1 to −8.5 MJ/m² (mean −2.9 MJ/m² at dt 3600 s) | — |

| dt (s) | random calls | melt-out-prone calls | melt seasons (2 × 2,000 columns) |
|---|---|---|---|
| 720 | 0 / 1e6 | 1 / 2e5 | 0 |
| 3600 | 7.3e-4 per call | 1.7e-2 per call | 1 |


## Current answers

## 1. Code path (final tree = develop @242a2fc for these lines)

| copy | line |
|---|---|
| ccpp-physics `module_sf_noahmplsm.F90` `combine` (final tree) | L7701 (develop L7661) |
| ccpp-physics `module_sf_noahmp_glacier.F90` `combine_glacier` (final) | L2954 (develop L2939) — **same line; the draft misses it** |
| NOAA-EMC/noahmp `src/module_sf_noahmplsm.F90` (2c7b3bc, final = develop) | L7643 |
| NOAA-EMC/noahmp `src/module_sf_noahmp_glacier.F90` | L2911 — same line |

`combine` is called from `snowwater` (after `snowfall`, `compact`) and from `snowh2o` (top layer sublimated below 1e-6 mm).
Loop `j = isnow_old+1, 0`: a layer with `snice <= 0.1` is merged into the layer below (j+1) and `isnow` is incremented.
At the bottom layer (j = 0) the merge goes UP into j-1 when `isnow_old < -1`. If every layer above was removed earlier in
this loop, `isnow` is already -1, so j-1 is an inactive slot: the bottom layer's ice+liquid is added into the stale
slot (which also still holds the old copy of what was merged down from it), `isnow` becomes 0, and the `else` branch
that sets `ponding1 = snliq`, `sneqv = snice`, `snowh = dzsnso` never runs. `combine` returns at `if (isnow == 0)`
without setting `sneqv`/`snowh`; `sneqv` is still the value at entry to `snowwater` (layered packs: `snowfall`,
`phasechange` do not update `sneqv`, so it is the previous step's layer sum). `snowh2o` then treats it as a bulk
(unlayered) pack of that size; `snowwater` zeroes all layer slots (`do iz = -nsnow+1, isnow`).

Net effect per firing (S = the step's ground snowfall incl. canopy unloading, all in the top layer; I = remaining pack ice
≤ 0.1 mm; L = pack liquid):
- end state: bulk snow `sneqv_pre` (all ice), `snowh_pre`; correct: snow I, ponding L to the soil surface.
- water: `sneqv_pre = I + L - S`, so the column loses S (≤ ~0.1 mm per firing, since S sits in the ≤0.1-mm bottom ice).
- energy: L - S of liquid becomes ice without releasing hfus — the melt heat already paid is destroyed; the pack
  has to be melted (paid) again next step(s). Runoff of L is delayed; depth and cover revert to the pre-step pack.
- rain: unaffected (with `isnow = 0` the caller routes `qrain` straight into `qinsur`).

`isnow < -1` (upstream fix): differs from `isnow_old < -1` only when `isnow_old < -1` and `isnow == -1` at j = 0, i.e.
exactly the firing case, so non-firing calls are unchanged by construction. `isnow < 0` is always true at j = 0
(`isnow <= -1` there), so it would merge single-layer packs into an inactive slot too: worse, not a fix.

Upstream NCAR/noahmp v5 (as vendored in our MPAS tree, `SnowLayerCombineMod.F90` L64) already tests the current count
(`NumSnowLayerNeg < -1`), i.e. the fix; it serves land and glacier alike.

## 3. Results — single calls (200,000 columns each unless noted)

Firing frequency (per call) and effect, `orig`:

| run | dt (s) | firings | per call | water err per firing (mm) mean / range | latent energy per firing (MJ/m²) mean / range | ΔSWE / Δdepth kept (orig−fix) |
|---|---|---|---|---|---|---|
| built | 150, 300, 450 | 0 | 0 | — | — | — |
| built | 720 | 1 | 5e-6 | 0 | −1.40 | +4.2 mm / +60 mm |
| built | 900 | 5 | 2.5e-5 | −3.6e-3 / [−0.018, 0] | −1.47 / [−1.91, −1.15] | +4.4 / +67 |
| built | 1200 | 31 | 1.6e-4 | −3.2e-3 / [−0.052, 0] | −1.78 / [−2.51, −1.21] | +5.3 / +76 |
| built | 1800 | 306 | 1.5e-3 | −1.2e-3 / [−0.100, 0] | −2.16 / [−4.31, −1.15] | +6.5 / +85 |
| built | 3600 | 3,477 | 1.7e-2 | −1.2e-4 / [−0.099, +0.161] | −2.89 / [−8.45, −1.12] | +8.7 / +96 |
| random (1e6) | 720 | 0 | 0 | — | — | — |
| random (1e6) | 3600 | 726 | 7.3e-4 | −5.4e-4 / [−0.079, +0.127] | −2.37 / [−6.71, −1.02] | +7.2 / +77 |
| wet (red team) | 150 / 720 / 3600 | 68,388 / 128,658 / 157,203 | — | −2.6e-3 / −2.0e-3 / −9.3e-4, all within [−0.100, +0.163] | −0.45 / −0.55 / −0.60 | +1.3–1.8 / +27–33 |

By class (built 3600; same pattern in every run): snowfall in the step (225 events): water −S, mean −0.017 mm, ≤ 0.1 mm
(S sits in the ≤ 0.1-mm bottom ice); no snowfall (3,142): water exact, energy error only; fired at the `snowh2o` call site
after sublimation emptied the top layer (110): the sublimation is undone, water +0.031 mm mean, up to +0.16 mm. Rain is never
lost (with `isnow = 0` the caller routes it to `qinsur`). The energy error is −800 W/m² averaged over a 3600-s step,
−1950 W/m² over 720 s: the melt the step paid for is undone, so the pack must be melted again and its runoff is delayed.

## 4. Fix verification

| check | result |
|---|---|
| water, firing columns, `fix` | max |errw| ≤ 2.2e-12 mm in every firing column of every run (≈ 500,000 firings: built, random, wet, glacier) |
| non-firing columns, `orig` vs `fix` | bitwise identical end state (all 59 fields) in every run, incl. 1e6 random columns |
| columns that differ `orig` vs `fix` | exactly the firing columns, in every run (none fired-but-identical, none differ-but-not-fired) |
| `neg` (`isnow < 0`) | identical to `orig` in every firing column (no fix); in single-layer packs it fires the same loss: changes 2,346 (3600 s) / 4 (720 s) non-firing single-layer columns; `built1` 3600 s −2.9 mm over 200,000 calls (max 0.18 mm per call), 720 s −3.5e-3 mm; `orig`/`fix` identical to each other there and close except the one side-finding column below |
| meter-instrumented `orig` vs `pristine` | bitwise identical in every run |

Side finding (not NM12, unchanged by the fix): `noahmp_sflx` L947 (NM5's end-of-call truncation) zeroes `sneqv` when
`sneqv <= 1e-3` but books it to soil only if `isnow == 0`; with `isnow = -1` the layer keeps its ≤ 1e-3 mm while `weasd`
reads 0, so the meter shows −1e-3 mm that reappears next call when `snowwater` re-sums the layers (1 column in 200,000
single-layer calls at 3600 s; `built1` 3600 `orig`/`fix` col 197075: −9.6e-4 mm).

## 5. Melt seasons (2 × 2,000 columns × 120 days per dt; `orig` and `fix`)

| dt (s) | columns with a spring pack that melted out (seed 1 of 2) | firings (both seeds) | fix water |
|---|---|---|---|
| 450 | 1,451 / 2,000 | 0 | ≤ 2.5e-12 mm per call |
| 720 | 1,404 / 2,000 | 0 | ≤ 2.4e-12 |
| 1800 | 1,189 / 2,000 | 0 | ≤ 2.5e-12 |
| 3600 | 953 / 2,000 | 1 (col 694, day 141: L 5.87 mm, water −0.016 mm) | ≤ 4.1e-12 |

Seasonal packs thin progressively and `combine` merges sub-2.5-cm layers as they go, so a pack is down to one layer (or
below 2.5 cm, the `ponding2` path) before it melts out; NM12 needs a ≥ 2-layer pack (≳ 5 cm, ≥ ~3–15 mm SWE) to vanish in
one step — thin fresh snow hit by strong melt or warm rain, with a long step. Seasonal total: nil at UFS steps; one
event per ~2,000 melt-outs at 3600 s (water −0.016 mm, energy ≈ −1.9 MJ/m² once).

## 6. Red team

- Single-layer packs (`isnow_old = -1`): both conditions false at j = 0, so the `else` branch runs as before; `fix` ≡ `orig`
  bitwise in all `built1` runs. `isnow < 0` breaks exactly these (section 4).
- Second call site (`snowh2o` → `combine` after sublimation empties the top layer): covered by the same line; it fires
  there too (the "sublimation" class) and the fix closes it.
- Glacier (`combine_glacier`, same line): UFS's ccpp glacier resets the pack to 600 mm in 3 layers every call, so a call
  can start thin only from an external initial state; forced with thin wet packs (`glawet`, 52,695 and 92,280 firings
  at 720 / 3600 s) `orig` errs −0.085 to +0.18 mm per firing and `fix` closes to ≤ 3.4e-13 mm; non-firing columns
  bitwise identical; the realistic glacier run (`gla`, built packs on ice) never fires. In `orig` the stranded liquid is
  absorbed into the reset's ice booking (`snoflow` → `drain`) instead of leaving as surface runoff. NOAA-EMC/noahmp's
  glacier has no reset (older `combine_glacier` without `dzsnso` merging) — the companion diff fixes the same line there.
- Ponding: the fix's `ponding1` enters `qinsur` like every other melt-out path; water closes, so no double count with the
  stale slot (all slots ≤ `isnow` are zeroed by `snowwater`).
- Over-sublimated bottom layer (`snice < 0`) in the newly reachable branch: pre-existing single-layer code; its
  `max(0, sice(1) + ponding1/…)` clip could create water if soil ice runs out, but no firing in any run hit a residual.
- Restart / decomposition: column-local, inside one call, no new state — unaffected.
- Other copies: the line appears in exactly 4 files of the final tree (ccpp lsm + glacier, NOAA-EMC lsm + glacier).
  NCAR/noahmp v5 (MPAS, WRF ≥ 4.5 via v5) already has the fix.

Classification: **BUG FIX** (restores the intended branch; upstream's own comment says "change to isnow"). Changes
answers only in firing columns; at UFS RT time steps (720 s, C768 150 s) it essentially never fires, so forecast impact is
nil there; it matters for long-step uses (dt ≥ 1800 s, e.g. C48 tests, offline land at 3600 s).

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| NM12 — Noah-MP `combine` melt-out (agent nm12) | title | current | `report.md` and `report.history.md` |
| (not a heading) the bold `Status (17 Oct, DONE)` block, with the harness and disk notes | status, harness location, disk use | superseded by `## Status` above | `report.history.md` |
| 1. Code path (final tree = develop @242a2fc for these lines) | the four copies, the defect, the fix | current | `report.md` |
| 2. Harness | harness design, meters, column kinds | archival | `report.history.md` |
| 3. Results — single calls (200,000 columns each unless noted) | firing frequency and error per firing | current | `report.md` |
| 4. Fix verification | water closure, bitwise checks, `isnow < 0` rejected | current | `report.md` |
| 5. Melt seasons (2 × 2,000 columns × 120 days per dt; `orig` and `fix`) | seasonal firing frequency | current | `report.md` |
| 6. Red team | edge cases, glacier, classification | current | `report.md` |
| 7. Diffs (`nm12/patches/`) | the two diffs and where they apply | archival | `report.history.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
