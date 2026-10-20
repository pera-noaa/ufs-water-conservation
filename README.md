# UFS water and energy conservation: working notes

Working notes, patches and measurements behind a set of conservation bug fixes proposed to the UFS weather model
(ccpp-physics, GFDL_atmos_cubed_sphere, NOAA-EMC/noahmp, NOAA-EMC/ufsatm, ufs-weather-model). Linked from those
issues and pull requests so reviewers can check any number quoted there.

Ash Pera, NOAA GML / CIRES. Work in progress; the notes are a lab notebook, not documentation.

## Where to start

| File | What |
|---|---|
| `proposal/pr_round1.md` | round-1 plan: the 37 fixes, the tracks they post in, every check and its result |
| `proposal/pr_round1_descriptions.md` | drafts of the issue and PR texts |
| `proposal/round2_issues.md` | bugs whose fix needs an owner's decision |
| `proposal/water_closure_proposal.md`, `proposal/conservation_proposal.md` | the water and conservation proposals |
| `conservation/TRACKER.md` | status of each conservation study |
| `water_conservation_audit.md` | the original water-budget audit |

`*.history.md` files are archives behind the shorter head files of the same name.

## Layout

- `proposal/`: proposals, round-1 and round-2 drafts, `patches/` (one diff per water fix) and `pr_round1_patches/`
  (`git format-patch` per branch).
- `conservation/<study>/`: one directory per budget study (energy, tracer mass, PBL, convection, surface, …) with its
  report, meters, patches, scripts and logs. `conservation/replay/` holds the patch series.

Copies of patched upstream source trees are not included; the patches reproduce them on the stated upstream commits.
Measurements are from runs on NOAA RDHPCS Hercules and Orion; paths in the notes refer to those systems.

AI-assisted: written with Claude Opus 5.5; reviewed by author.
