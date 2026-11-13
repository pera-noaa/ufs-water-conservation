#!/usr/bin/env python3
"""Print a few firing columns' end state in two runs. Usage: gdiag.py <A> <B> [n]"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import load
a, b = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
ca, sa, _ = load(a)
cb, sb, _ = load(b)
f = np.where((ca[:, 5] + ca[:, 6]) > 0)[0][:n]
np.set_printoptions(precision=5, suppress=True, linewidth=160)
for i in f:
    print(f'col {i+1}: meter liq {ca[i,17]:.4f} ice {ca[i,18]:.5f} sneqv_entry {ca[i,19]:.4f} weasd_init {ca[i,4]:.4f}')
    for lab, c, s in ((a, ca, sa), (b, cb, sb)):
        print(f'  {lab:5s} errw {c[i,7]:+.3e} weasd {s["weasd"][i,0]:.5f} snwdph {s["snwdph"][i,0]:.2f} snowxy {s["snowxy"][i,0]:.0f}'
              f' snice {s["snicexy"][i]} snliq {s["snliqxy"][i]} runoff*1 {s["runoff"][i,0]:.3e} drain {s["drain"][i,0]:.3e}'
              f' smc1 {s["smc"][i,0]:.5f} slc1 {s["slc"][i,0]:.5f} tsno {s["tsnoxy"][i]} stc1 {s["stc"][i,0]:.3f}')
