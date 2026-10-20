*History of `report.md` (nm12), moved verbatim on 18 October 2026. The head is `report.md`.*

# NM12 — Noah-MP `combine` melt-out (agent nm12)

**Status (17 Oct, DONE):**
- CONFIRMED in the real code (harness drives the final tree's `noahmpdrv_run`). Fires only when a ≥2-layer pack melts to
  ≤0.1 mm ice in one step. Per firing: water error −S (step's ground snowfall lost) or +sublimation (when it fires at the
  `snowh2o` call site), |errw| ≤ 0.16 mm, mean ~1e-3 mm; **energy error −1.1 to −8.5 MJ/m² (mean −2.9 MJ/m² at dt 3600 s)**
  — L−S of meltwater turned back into snow without releasing the melt heat; the pre-step pack (SWE, depth) is restored.
- Rare at UFS time steps: 0 / 1e6 random calls and 1 / 2e5 melt-out-prone calls at dt = 720 s; 0 firings in 8,000
  column melt-seasons at dt ≤ 1800 s, 1 in 4,000 at 3600 s. 7e-4 of random calls at 3600 s.
- Fix `isnow < -1` (ccpp `combine` and `combine_glacier`): water closes to ≤ 2.2e-12 mm in every firing column; non-firing
  columns bitwise identical (every run); meter-instrumented build bitwise identical to pristine. `isnow < 0` does not fix it
  and breaks single-layer packs (water error up to 0.18 mm per call in non-firing columns).
- Glacier: the ccpp glacier resets the pack to 600 mm every call, so it cannot fire there in practice; fix included for
  consistency and for NOAA-EMC/noahmp (no reset).
- Diffs: `patches/20_NM12_noahmp_combine_melt_out.diff` (ccpp-physics) and `patches/20b_NM12-EMC_noahmp-emc_combine_melt_out.diff`.

Harness (survives): `$U/cons/nm12` — `src/` (final-tree copies), `harness/` (gen_call.py, nm12_main.F90, mkvariants.py,
build.sh, run.sh, compare.py, cats.py, echeck.py), `variants/{pristine,orig,fix,neg}`, `build/<v>/nm12_<v>.x`, `runs/`.
Local copy of the harness sources: `nm12/harness/`.

Disk: `$U/cons/nm12` is 14 GB (end states of the 1e6-column runs); `runs/rand*` can be deleted once reviewed.

## 2. Harness

Fresh, from the final tree's real sources (`p20rt_final`): `gen_call.py` turns every non-optional `noahmpdrv_run` dummy
into an allocatable array and writes a keyword call, so the harness runs the real driver (`noahmpdrv_init`, tables from
`noahmptable.tbl`, `iter=1`) on `ncol` independent columns with the UFS RT options (default_vars.sh: dveg 4, crs 2, btr 1,
run 1, sfc 3, frz 1, inf 1, rad 3, alb 1, snf 4, tbot 2, stc 3, trs 2, diag 2). Intel, `-real-size 64 -O2 -fp-model precise`.

- Water meter per column per call: `errw = Δ(weasd + canice + canliq + Σsmc·dz·1000 + waxy) − (P − ecan − etran − edir − runoff − drain)·dt`.
  Closes to ≤ 2.3e-12 mm in every non-firing column of every run (~4e6 column-calls + 8,000 seasons).
- Firing meter (variants `orig/fix/neg` only): in `combine`/`combine_glacier` at j = 0, counts `isnow_old < -1 .and. isnow == -1`
  (exactly where old and new conditions differ) and records the bottom layer's liquid L, ice I and `sneqv` at that point.
  `orig` is bitwise identical to `pristine` (no meter) in every run.
- Energy: differential. The step's energy solve and phase change run before `water`, so `orig` and `fix` share every flux
  of the firing step; the end-state difference is the defect's own term. Latent part `−hfus·Δ(ground ice)`
  (snow layers or bulk snow + soil ice); `Δice` = `sneqv_entry − I` to within the step's sublimation/frost and the
  thin-snow truncation (≤ 0.18 mm).
- Column kinds: `built` (2–3-layer ripe packs, 2.6–6 cm layers, 60–250 kg/m³, warm sun/rain forcing — melt-out-prone),
  `random` (NM11-like: bare to 1.5 m packs, 255–273 K, any forcing), `wet` (red team: ≤0.5 mm ice per layer, mostly
  liquid — forces firing at any dt), `built1` (single layer), `season` (120-day melt season: diurnal sun, +12–25 K
  warming, random storms; rain/snow by T).

## 7. Diffs (`nm12/patches/`)

- `20_NM12_noahmp_combine_melt_out.diff` — ccpp-physics, `module_sf_noahmplsm.F90` and `module_sf_noahmp_glacier.F90`,
  `isnow_old < -1` → `isnow < -1` (stale "change to isnow" comment dropped). Applies cleanly on the final tree, and on
  `develop` @242a2fc with offsets (−40, −15).
- `20b_NM12-EMC_noahmp-emc_combine_melt_out.diff` — NOAA-EMC/noahmp (2c7b3bc) `src/` lsm + glacier, same change;
  applies cleanly on both trees. The draft (13_NM12.md) should also name the glacier copies.
