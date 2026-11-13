#!/usr/bin/env python3
"""Firing events by class. Usage: cats.py <dir> <dt> [<dir> <dt> ...]  (each dir holds orig and fix runs)
Classes: snowfall (S = I + L - sneqv_entry > 0), none (|S| <= 1e-9), sublimation (S < 0: the snowh2o call site)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import load
H = 3.3358e5
args = sys.argv[1:]
print(f'{"run":12s} {"class":11s} {"n":>7s} {"errw_orig mean":>15s} {"min":>10s} {"max":>10s} {"max|errw_fix|":>13s}'
      f' {"dE_lat mean MJ":>14s} {"min":>8s} {"max":>8s} {"W/m2 mean":>9s} {"L mean":>7s} {"dSWE":>6s} {"dDepth mm":>9s}')
for k in range(0, len(args), 2):
    d, dt = args[k], float(args[k + 1])
    ca, sa, _ = load(os.path.join(d, 'orig'))
    cb, sb, _ = load(os.path.join(d, 'fix'))
    f = (ca[:, 5] + ca[:, 6]) > 0
    S = ca[:, 17] + ca[:, 18] - ca[:, 19]
    for name, m in (('snowfall', f & (S > 1e-9)), ('none', f & (np.abs(S) <= 1e-9)), ('sublimation', f & (S < -1e-9)),
                    ('all', f)):
        if not m.any():
            print(f'{d:12s} {name:11s} {0:7d}')
            continue
        ew, ef = ca[m, 7], cb[m, 7]
        de = -H * (sa['ice'][m, 0] - sb['ice'][m, 0]) / 1e6
        print(f'{d:12s} {name:11s} {m.sum():7d} {ew.mean():+15.3e} {ew.min():+10.3e} {ew.max():+10.3e} {np.abs(ef).max():13.2e}'
              f' {de.mean():+14.3f} {de.min():+8.2f} {de.max():+8.2f} {de.mean()*1e6/dt:+9.0f} {ca[m,17].mean():7.2f}'
              f' {(sa["weasd"][m,0]-sb["weasd"][m,0]).mean():+6.2f} {(sa["snwdph"][m,0]-sb["snwdph"][m,0]).mean():+9.1f}')
