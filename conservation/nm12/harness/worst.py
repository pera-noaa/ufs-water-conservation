#!/usr/bin/env python3
"""Show the columns with the largest |errw| in a run. Usage: worst.py <prefix> [n]"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import load
c, s, _ = load(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
np.set_printoptions(precision=5, suppress=True, linewidth=170)
for i in np.argsort(-c[:, 8])[:n]:
    print(f'col {i+1} veg {c[i,1]:.0f} soil {c[i,2]:.0f} errw {c[i,7]:+.4e} weasd0 {c[i,4]:.4f} weasd {s["weasd"][i,0]:.6f} '
          f'snowxy {s["snowxy"][i,0]:.0f} snwdph {s["snwdph"][i,0]:.4f} snice {s["snicexy"][i]} snliq {s["snliqxy"][i]} '
          f'smc1 {s["smc"][i,0]:.5f} slc1 {s["slc"][i,0]:.5f} qsnow {s["qsnowxy"][i,0]:.3e} edir {s["edir"][i,0]:.3e} '
          f'runoff {s["runoff"][i,0]:.3e} stc1 {s["stc"][i,0]:.2f}')
