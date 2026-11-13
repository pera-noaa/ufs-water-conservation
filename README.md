# Water, energy and tracer conservation in UFS physics

Measured defects in the UFS physics (ccpp-physics, FV3 and its coupling, Noah-MP), the fixes we propose, and the
evidence behind each one. Written for the developers who own the code. Ash Pera (NOAA GML / CIRES).

**Start here:** find your scheme below. Each scheme page lists every defect in that code, its measured size, the fix,
where it stands upstream, and links to the evidence.

## Status (13 November 2026)

- **Water.** In `FV3_GFS_v17_p8_ugwpv1` the physics creates water: +0.25 % of precipitation on the first day at C96,
  +0.45 % at C384. The dynamical core conserves water; the physics and its coupling to the land model do not
  ([proposal](proposals/water_closure_proposal.md)).
- **Energy and tracers.** With every fix on (C96, 24 h), total energy closes to 1.6 × 10⁻¹² W/m² (from +2.08) and
  passive-tracer mass to ~3 × 10⁻¹⁵ per day ([proposal](proposals/conservation_proposal.md)).
- **Upstream.** 8 ccpp-physics PRs posted; 5 approved (#405, #406, #407, #408, #414); none merged. The fixes go in as
  three packages (SAMF/PBL, microphysics, Noah-MP), so regression baselines change three times, not eight
  ([roadmap](upstream/ROADMAP.md)). The plan is filed as
  [ufs-weather-model#3404](https://github.com/ufs-community/ufs-weather-model/issues/3404).

## By scheme

| Scheme | Page | Upstream items |
|---|---|---|
| SAMF convection | [samf](components/samf.md) | #401, #405, #408, #414; #403 (not ours) |
| PBL (satmedmfvdifq, MLM, shinhongvdif) | [pbl](components/pbl.md) | #404, NCAR/ccpp-physics#1251 |
| MYNN-EDMF | [mynn](components/mynn.md) | drafted |
| Grell–Freitas | [grell_freitas](components/grell_freitas.md) | drafted |
| Gravity-wave drag and tendency application (TOPT) | [gwd](components/gwd.md) | not posted |
| Thompson microphysics | [thompson](components/thompson.md) | #406 |
| TEMPO microphysics | [tempo](components/tempo.md) | #407; NCAR/TEMPO PR and issue drafted |
| GFDL MP v3 | [gfdl_mp](components/gfdl_mp.md) | #413; NOAA-GFDL/GFDL_atmos_cubed_sphere#430, #431 |
| Noah-MP | [noahmp](components/noahmp.md) | #409, #410; NCAR/noahmp#274 |
| NSST and sea ice | [surface](components/surface.md) | not posted |
| FV3 dycore, its coupling to the physics, tracer transport | [fv3](components/fv3.md) | not posted |

Issue and PR numbers without a repository are ufs-community/ccpp-physics. Per-item state, with links:
[`upstream/POSTING.md`](upstream/POSTING.md).

## Reproduce

- **Patches:** [`patches/README.md`](patches/README.md): one diff per fix against ccpp-physics `ufs/dev`, `git
  format-patch` series, and ports to other copies of the code (NCAR, WRF, MPAS, NOAA-EMC/noahmp) in
  [`patches/ports/`](patches/ports/README.md).
- **Meters:** [`methods/METERS.md`](methods/METERS.md): the in-model budget meters behind every number, which one to
  use for which question, and how to read them. A design for maintained upstream meters:
  [`methods/meter_design.md`](methods/meter_design.md).
- **How we measured, and pitfalls:** water proposal §5 and §8; energy proposal *Method*.
- **Test plan per package** (regression tests, HAFS checks): [`upstream/ROADMAP.md`](upstream/ROADMAP.md).

## Layout

| Directory | What is in it |
|---|---|
| [`components/`](components/) | one page per scheme (start here) |
| [`proposals/`](proposals/) | the full write-ups: water, energy and tracers, round-1 PR set, round-2 issues, triage of what is not yet posted, code audit, literature |
| [`methods/`](methods/) | meters, meter design and prototypes, analysis scripts |
| [`experiments/`](experiments/) | run reports: `conservation/<topic>/report.md` (energy, tracer, surface, suites, red teams), `runs_29oct/` (re-measurements), `hafs_samf/` |
| [`patches/`](patches/) | diffs and patch series, ports to other copies |
| [`upstream/`](upstream/) | posting state, roadmap, PR and issue bodies as posted, replies, per-item test harnesses |

Long documents are split into a short head (`<name>.md`) and a dated archive (`<name>.history.md`); read the head.
Section numbers (`§N`) are stable.
