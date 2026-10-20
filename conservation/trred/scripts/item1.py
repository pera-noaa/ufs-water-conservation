#!/usr/bin/env python3
"""Item 1/2: tracer-moisture consistency and the dipole mechanism, on dumped real columns.
(a) one-step operators applied to qv: A base tracer op (mean start), B tracer op with qv's own interface values qo,
    C donor start nsub=1, D patch 02 (donor, sub-stepped); Q = model qv transport (dellaq*xmb*dt2).
(b) frozen-column iteration (N steps) of operators on uniform / pt_umoist-shaped / qv-shaped fields.
usage: item1.py <dumpdir> [maxcols] [nsteps]"""
import sys, numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import samfrep as S
d = sys.argv[1]; maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 300; N = int(sys.argv[3]) if len(sys.argv) > 3 else 60
cols = [c for c in S.read_all(d, maxn * 3) if c['rnpos']][:maxn]
print('columns', len(cols))
# (a)
R = {k: [] for k in ('int_vs_mean', 'donor_vs_mean', 'p02_vs_mean', 'mean_vs_int', 'donor_vs_int', 'p02_vs_int', 'sub_Bq', 'sub_Aq', 'sub_Dq', 'qstart')}
L = {k: [] for k in ('A', 'B', 'C', 'D')}
nsubs = []
for c in cols:
    kb, kt = c['kb'], c['ktcon']
    qv = c['q1'].copy()
    nsub, _ = S.nsub_of(c, True); nsubs.append(nsub)
    A = S.trsub(c, qv, 1, 'mean')[0] - qv
    B = S.trsub(c, qv, 1, 'mean', cto_in=c['qoi'])[0] - qv
    C = S.trsub(c, qv, 1, 'donor')[0] - qv
    D = S.trsub(c, qv, nsub, 'donor')[0] - qv
    Q = c['dellaq'] * c['xmb'] * c['dt2']
    sl = slice(1, kt + 1)
    na = np.sqrt(np.mean(A[sl] ** 2)) + 1e-300
    R['int_vs_mean'].append(np.sqrt(np.mean((B - A)[sl] ** 2)) / na)
    R['donor_vs_mean'].append(np.sqrt(np.mean((C - A)[sl] ** 2)) / na)
    R['p02_vs_mean'].append(np.sqrt(np.mean((D - A)[sl] ** 2)) / na)
    for k, X in (('mean_vs_int', A), ('donor_vs_int', C), ('p02_vs_int', D)):
        R[k].append(np.sqrt(np.mean((X - B)[sl] ** 2)) / na)
    ss = slice(1, max(2, c['kbcon']))   # sub-cloud layers (updraft unsaturated)
    nq = np.sqrt(np.mean(Q[ss] ** 2)) + 1e-300
    for k, X in (('sub_Bq', B), ('sub_Aq', A), ('sub_Dq', D)):
        R[k].append(np.sqrt(np.mean((X - Q)[ss] ** 2)) / nq)
    dm = 0.5 * (qv[kb] + qv[kb + 1])
    R['qstart'].append(((c['qoi'][kb] - dm), (qv[kb] - dm), qv[kb]))
    for k, X in (('A', A), ('B', B), ('C', C), ('D', D)):
        L[k].append((X[kb], X[kb + 1], Q[kb], Q[kb + 1], np.sqrt(np.mean((X - Q)[sl] ** 2)) / (np.sqrt(np.mean(Q[sl] ** 2)) + 1e-300)))
P = lambda a: f'median {np.median(a):.3g} p90 {np.percentile(a, 90):.3g}'
print('nsub', P(nsubs), 'frac nsub=1', np.mean(np.array(nsubs) == 1).round(3))
for k in ('int_vs_mean', 'donor_vs_mean', 'p02_vs_mean', 'mean_vs_int', 'donor_vs_int', 'p02_vs_int'):
    print(f'(a) rms|op(qv) - base op(qv)| / rms|base op(qv) incr| over 1..ktcon, {k}: {P(R[k])}')
qs = np.array(R['qstart'])
print(f'(a) start value - interface mean, relative to q(kb): qv rule qo(kb) {P(np.abs(qs[:,0])/qs[:,2])} ; donor q(kb) {P(np.abs(qs[:,1])/qs[:,2])}')
print(f'    sign agreement qo-mean vs donor-mean: {np.mean(np.sign(qs[:,0]) == np.sign(qs[:,1])):.2f}; ratio (qo-mean)/(donor-mean) {P(qs[:,0]/np.where(qs[:,1]==0,np.nan,qs[:,1]))}')
for k in ('sub_Bq', 'sub_Aq', 'sub_Dq'):
    print(f'(a) sub-cloud layers 1..kbcon-1: rms|op(qv) - model qv incr|/rms|model qv incr|, {k}: {P(R[k])}')
# (b) frozen-column iteration
ops = {'M1 mean nsub1': (1, 'mean'), 'M2 mean substep': (None, 'mean'), 'D1 donor nsub1': (1, 'donor'),
       'D2 donor substep (p02)': (None, 'donor'), 'U2 upper(qv-rule) substep': (None, 'upper')}
res = {}
for c in cols[:min(len(cols), 80)]:
    kb, kt, km = c['kb'], c['ktcon'], c['km']
    nsub, _ = S.nsub_of(c, True)
    ntr, itc = c['ntr'], c['itc']
    fields = {'uniform': np.ones(km + 1), 'pt_umoist': c['qtr'][5] / 1e-6, 'qv': c['q1'] / c['q1'][kb]}
    for fn, x0 in fields.items():
        for on, (ns, st) in ops.items():
            x = x0.copy()
            for it in range(N):
                x = S.trsub(c, x, ns or nsub, st)[0]
            d0 = x0[kb] - x0[kb + 1]; dN = x[kb] - x[kb + 1]
            # dipole: curvature across kb,kb+1 relative to neighbours, before and after
            def dip(y): return abs((y[kb] - y[kb + 1]) - 0.5 * ((y[kb - 1] - y[kb]) + (y[kb + 1] - y[kb + 2]))) if kb > 1 else abs(y[kb] - y[kb + 1] - (y[kb + 1] - y[kb + 2]))
            res.setdefault((fn, on), []).append((dip(x0), dip(x), np.max(np.abs(x[1:kt + 1] - 1.0)) if fn == 'uniform' else 0))
print(f'(b) frozen-column iteration, {N} steps, {min(len(cols),80)} columns; dipole = |2nd difference across kb/kb+1|')
for (fn, on), v in res.items():
    v = np.array(v)
    extra = f' max|c-1| {v[:,2].max():.2e}' if fn == 'uniform' else ''
    print(f'  {fn:9s} {on:28s} dipole initial median {np.median(v[:,0]):.3e} final median {np.median(v[:,1]):.3e} p90 {np.percentile(v[:,1],90):.3e}{extra}')
