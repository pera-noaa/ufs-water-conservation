#!/usr/bin/env python3
"""Latent check: the bug's extra ground ice (orig - fix) vs the meter's sneqv_entry - I (ice the bug creates
without heat). Usage: echeck.py <dir> [...]"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import load
for d in sys.argv[1:]:
    ca, sa, _ = load(os.path.join(d, 'orig'))
    cb, sb, _ = load(os.path.join(d, 'fix'))
    f = (ca[:, 5] + ca[:, 6]) > 0
    dice = sa['ice'][f, 0] - sb['ice'][f, 0]
    pred = ca[f, 19] - ca[f, 18]
    r = dice - pred
    print(f'{d}: n {f.sum()}  dice mean {dice.mean():.4f}  |dice - (sneqv_entry - I)| max {np.abs(r).max():.2e}'
          f'  (n > 1e-5: {(np.abs(r) > 1e-5).sum()})')
