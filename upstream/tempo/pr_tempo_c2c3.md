<!-- DRAFT 13 Nov 2026, not posted. NCAR/TEMPO PR, base main c62699fb, head pera-noaa:water-graupel-density db01901d
     (ca8252d5 graupel, db01901d density). CI on the fork: run 43497234719 pass. The c62699f rows wait for the
     Hercules runs in PREREG_tempo_port.md; fill them before posting, or post with the 2856696 rows only.
     Title: "Re-close graupel gains after the limiters; sedimentation with the entry density" -->

@AndersJensen-NOAA These are the two scheme fixes that ufs-community/ccpp-physics#406 makes in Thompson, ported to
`tempo_main`. Each closes a water leak and has one answer. The fallback sign in `semilagrangian_sedimentation` is
reported separately (#NN), since it changes forecasts.

**Graupel re-close** (ca8252d). As computed, rain–ice and rain–snow collection conserve: `prg_rci = pri_rci + prr_rci`
([L3339](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L3339))
and `prg_rcs = −(prr_rcs + prs_rcs)`. The per-term clamps
([L2995–2998](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L2995-L2998))
and `check_over_depletion`
(ice, rain and snow, [L1580–1625](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1580-L1625))
then limit the losses and leave the graupel gains alone, which creates graupel. The fix recomputes both gains after
the limiters, beside the existing rain–graupel and rain–hail resets
([L1657–1673](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1657-L1673)).
Below freezing the rain limit can leave snow gaining more than the rain it takes, so it caps that gain first. The
hail terms already close: rain–hail is reset there, and riming, deposition and melting use one variable on both sides.

**Entry density** (db01901). After the tendencies, `rho` is recomputed from the heated temperature
([L512](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L512),
[L605](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L605),
[L633](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L633)),
and sedimentation converts between mixing ratio and mass with it. `dz1d` doesn't change, so the new `rho` implies a
different layer mass. The fix keeps `rho` at the entry density and passes the updated one (`rhon`) only to
`thermo_vars`, for fall speeds and ventilation. Updating `dz1d` with `rho` instead would also close; in Thompson the
two differ in precipitation by up to 0.3 % globally.

Measured in UFS (C96 `control_p8_ugwpv1_tempo`, 24 h, with ufs-community/ccpp-physics#407) by an in-model water
meter, in % of TEMPO's grid-scale precipitation. On 2856696 (UFS's pin in October), each leak with every
other fix in, a build that otherwise closes to 2e-7:

| Leak | 0–6 h | 6–24 h |
|---|---|---|
| graupel gains not re-closed | creates 0.86 % | creates 0.004 % |
| sedimentation with the heated density | removes 0.12 % | removes 0.12 % |

On `main`, the residual R/P without and with this PR:

| c62699f | 0–6 h | 6–24 h | P 6–24 h |
|---|---|---|---|
| `main` | | | |
| + graupel | | | |
| + density | | | |
| + both (this PR) | | | |

Graupel leaks mostly during spin-up, as in Thompson. One case, so sizes vary. CI passes on the branch; `test/tests.F90`
has no stored answers, so it checks that the scheme builds and runs.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
