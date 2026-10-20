#!/usr/bin/env python3
"""Gates for the offline replay: G1 qv della replay == model dellaq; G2 tracer replay == model new_qtr (columns with
rain and no positivity/borrowing action), with the configuration of the dump run; G2x = same with the parcel start
flipped (must FAIL, proves G2 can fail). usage: gate.py <dumpdir> <cfg: patched|base> [maxcols]"""
import sys, numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import samfrep as S
d, cfg = sys.argv[1], sys.argv[2]
maxn = int(sys.argv[3]) if len(sys.argv) > 3 else 400
cols = S.read_all(d, maxn)
print('columns', len(cols), 'rnpos', sum(c['rnpos'] for c in cols))
g1 = []; g2 = {}; g2x = {}
for c in cols:
    if not c['rnpos']:
        continue
    kt = c['ktcon']
    dq = S.dellaq_replay(c)
    sc = np.max(np.abs(c['dellaq'][1:kt + 1])) + 1e-300
    g1.append(np.max(np.abs(dq[1:kt + 1] - c['dellaq'][1:kt + 1])) / sc)
    ntr, itc, ntc, ntk = c['ntr'], c['itc'], c['ntc'], c['ntk']
    chem = set(range(itc - 2, itc - 2 + ntc))
    wl = 1.0 - c['q']
    for n in range(1, ntr + 1):
        if n == ntk - 2:
            continue                      # TKE gets a convective source after transport
        dry = (n in chem) and cfg == 'patched'
        if cfg == 'patched':
            nsub, _ = S.nsub_of(c, True)
            sub = dry or nsub > 1
        else:
            nsub, sub = 1, False
        start = 'donor' if sub else 'mean'
        fsc = c['fscav'][n - (itc - 2)] if n in chem else 0.0
        x = c['qtr'][n - 1]
        y, _ = S.trsub(c, x, nsub if sub else 1, start=start, wl=wl if dry else None, fsc=fsc)
        if np.any(y[1:kt + 1] < 0):
            continue
        ref = c['new_qtr'][n - 1]
        s = max(np.max(np.abs(ref[1:kt + 1] - x[1:kt + 1])), 1e-12 * np.max(np.abs(x[1:kt + 1]))) + 1e-300
        g2.setdefault(n, []).append(np.max(np.abs(y[1:kt + 1] - ref[1:kt + 1])) / s)
        yx, _ = S.trsub(c, x, nsub if sub else 1, start='mean' if start == 'donor' else 'donor',
                        wl=wl if dry else None, fsc=fsc)
        g2x.setdefault(n, []).append(np.max(np.abs(yx[1:kt + 1] - ref[1:kt + 1])) / s)
g1 = np.array(g1)
print(f'G1 dellaq replay: cols {len(g1)} max rel err {g1.max():.2e} median {np.median(g1):.2e}  ->',
      'PASS' if g1.max() < 1e-10 else 'FAIL')
for n in sorted(g2):
    a, b = np.array(g2[n]), np.array(g2x[n])
    print(f'G2 tracer {n}: cols {len(a)} max rel err {a.max():.2e} ->', 'PASS' if a.max() < 1e-10 else 'FAIL',
          f'| G2x flipped start: median {np.median(b):.2e} max {b.max():.2e} ->',
          'FAILS as it must' if np.median(b) > 1e-6 else 'DOES NOT FAIL')
