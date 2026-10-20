#!/usr/bin/env python3
"""Per-firing diagnostics: S_meter = I + L - sneqv_entry vs ground snowfall qsnowxy*dt; canopy ice; errw.
Usage: sdiag.py <prefix> <dt>"""
import sys
import numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import load
p, dt = sys.argv[1], float(sys.argv[2])
c, s, _ = load(p)
f = (c[:, 5] + c[:, 6]) > 0
S = c[f, 17] + c[f, 18] - c[f, 19]
q = s['qsnowxy'][f, 0] * dt
e = c[f, 7]
print('firing cols', f.sum())
print('corr(errw, -S_meter) max abs diff', np.abs(e + S).max())
print('S_meter vs qsnow*dt: max abs diff', np.abs(S - q).max(), ' n(S<0)', (S < -1e-9).sum(), ' n(q>0)', (q > 1e-12).sum())
neg = S < -1e-9
if neg.any():
    print('S<0 cases: veg', np.unique(c[f, 1][neg].astype(int)), ' qsnow*dt', q[neg][:5], ' S', S[neg][:5])
    print('  canice end', s['canicexy'][f, 0][neg][:5], ' canliq end', s['canliqxy'][f, 0][neg][:5])
    print('  edir*dt', (s['edir'][f, 0] * dt)[neg][:5])
pos = S > 1e-9
print('S>0 cases', pos.sum(), ' S mean', S[pos].mean() if pos.any() else 0, ' max', S.max())
print('errw per firing: mean', e.mean(), ' min', e.min(), ' max', e.max(), ' mean|errw|', np.abs(e).mean())
