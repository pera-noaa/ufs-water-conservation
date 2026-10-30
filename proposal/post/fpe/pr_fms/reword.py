# rebuild each PR branch with new messages on the same trees, author and dates kept; prints old -> new heads
import subprocess as sp, os
T = "\n\nPart of a water-conservation project for UFS physics (NOAA GML / CIRES).\n\nAI-assisted: written with Claude Opus 5.5; reviewed by author\n"
M = {
 'bd82d044': ("mp_tempo: don't create water in the q/r round trip", "Convert back with the input humidity, as on entry."),
 'f94cdbe5': ("SAMF: release fusion heat of frozen detrainment", "Heat the layer by hfus/cp times the frozen part (new argument hfus)."),
 '33edd661': ("SAMF: count all convective wet deposition", "Use eta(k), as the tracer loss does; keep wet_dep when borrowing."),
 '5fe87089': ("satmedmfvdifq: surface fluxes per layer mass", "Use dt*rho_a*g/del, not dt/(zi(2)-zi(1))."),
 'f5a9fc81': ("samfdeepcnv: no early return before the CA trigger", "Answers depended on the blocking; skip the returns while a column can turn on."),
 'eff197ff': ("GFS_surface_composites_pre: keep land snow", "With frac_grid, don't overwrite weasd_lnd with the cell mean (as for RUC)."),
 '31d017fb': ("GFS_phys_time_vary: Noah-MP snow from land snow", "With frac_grid, use weasdl and snodl, not the cell means."),
 'b0999980': ("Noah-MP combine: use the current layer count", "Test isnow, not isnow_old (NCAR/noahmp#47)."),
 'a10df6f2': ("noahmpdrv: pass Noah-MP's own water flux", "evap = (ecan+etran+edir)/density, not latent heat over con_hvap."),
 '67e8c229': ("Noah-MP combine: keep the snow heat", "When layers merge or vanish, and when sublimation takes soil ice."),
 'b6edd7ff': ("Noah-MP csnow: heat capacity from layer mass", "Use the ice and liquid mass, not the capped volume fractions."),
 '5e5770b2': ("Noah-MP combo: conserve heat when layers merge", "Per-kg heat capacities; phase changes left to phasechange."),
 '2ad4aa4b': ("GFDL MP v3: don't create water in the wrapper", "Rescale the returned species by delp_out/delp_in."),
 '552b1d54': ("GFDL MP v3: rain falls with c_liq", "terminal_fall passed c_ice for every species."),
}
g = lambda *a, env=None, inp=None: sp.run(['git', *a], capture_output=True, text=True, check=True, env=env, input=inp).stdout.strip()
BASE = g('rev-parse', '9b65688c')
new = {}
for b in ['pr1-tempo', 'pr1-samf', 'pr1-noahmp-1', 'pr1-noahmp-2', 'pr1-gfdlmp']:
    parent = BASE
    for c in g('rev-list', '--reverse', f'{BASE}..f/{b}').split():
        s = c[:8]
        assert s in M, s
        assert len(M[s][0]) <= 52, (s, len(M[s][0]))
        if s not in new:
            assert g('rev-parse', f'{c}^') == (BASE if parent == BASE else [k for k, v in new.items() if v == parent and True][0] and g('rev-parse', f'{c}^')), s
            env = dict(os.environ)
            for k, f in (('GIT_AUTHOR_NAME', '%an'), ('GIT_AUTHOR_EMAIL', '%ae'), ('GIT_AUTHOR_DATE', '%aI')):
                env[k] = g('log', '-1', f'--format={f}', c)
            env.update(GIT_COMMITTER_NAME='Ash Pera', GIT_COMMITTER_EMAIL='ashley.pera@noaa.gov')
            msg = M[s][0] + '\n\n' + M[s][1] + T
            new[s] = g('commit-tree', g('rev-parse', f'{c}^{{tree}}'), '-p', parent, '-F', '-', env=env, inp=msg)
        parent = new[s]
    assert g('rev-parse', f'{parent}^{{tree}}') == g('rev-parse', f'f/{b}^{{tree}}'), b
    g('branch', '-f', f'{b}-reworded', parent)
    print(b, g('rev-parse', '--short=8', f'f/{b}'), '->', parent[:8], 'trees equal')
