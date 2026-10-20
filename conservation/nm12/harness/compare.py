#!/usr/bin/env python3
"""Compare two NM12 harness runs column by column.

Usage: compare.py <runA> <runB> [hfus]
runX = output prefix (reads <runX>.state, <runX>.cols). A is normally orig, B fix (or pristine/neg).
Prints: columns whose end state differs bitwise; whether they are exactly the firing columns (in A's or B's
.cols); water error |sum errw| per firing column in A and B; latent-energy difference -hfus*(ice_A - ice_B).
"""
import sys
import numpy as np

WIDTHS = [('weasd', 1), ('snwdph', 1), ('tskin', 1), ('smc', 4), ('stc', 4), ('slc', 4), ('canopy', 1),
          ('snowxy', 1), ('tvxy', 1), ('tgxy', 1), ('canicexy', 1), ('canliqxy', 1), ('eahxy', 1), ('tahxy', 1),
          ('tsnoxy', 3), ('zsnsoxy', 7), ('snicexy', 3), ('snliqxy', 3)] + \
         [(n, 1) for n in 'waxy wtxy zwtxy taussxy alboldxy sneqvoxy qsnowxy gflux hflx evap runoff drain ecan '
          'etran edir sncovr1 qsurf sum_errw ice'.split()]


def load(prefix):
    cols = np.loadtxt(prefix + '.cols', comments='#')
    im = cols.shape[0]
    raw = np.fromfile(prefix + '.state', dtype='>f8')
    if raw.size != im * sum(w for _, w in WIDTHS):
        raw = np.fromfile(prefix + '.state', dtype='<f8')
    assert raw.size == im * sum(w for _, w in WIDTHS), raw.size
    out, k = {}, 0
    for n, w in WIDTHS:
        out[n] = raw[k:k + im * w].reshape(w, im).T  # Fortran (im, w)
        k += im * w
    mat = np.concatenate([out[n] for n, _ in WIDTHS], axis=1)
    return cols, out, mat


def main():
    a, b = sys.argv[1], sys.argv[2]
    hfus = float(sys.argv[3]) if len(sys.argv) > 3 else 3.3358e5
    ca, sa, ma = load(a)
    cb, sb, mb = load(b)
    im = ca.shape[0]
    diff = np.any(ma.view(np.uint64) != mb.view(np.uint64), axis=1)
    fa = (ca[:, 5] + ca[:, 6]) > 0
    fb = (cb[:, 5] + cb[:, 6]) > 0
    print(f'{a} vs {b}: columns {im}, differ bitwise {diff.sum()}, fired in A {fa.sum()} (events {int(ca[:,5].sum()+ca[:,6].sum())}), fired in B {fb.sum()}')
    print(f'  differ but not fired in A: {(diff & ~fa).sum()}   fired in A but identical: {(fa & ~diff).sum()}')
    for lab, c, m in (('A', ca, fa), ('B', cb, fa)):
        e = c[:, 7]
        if m.any():
            print(f'  {lab} firing cols: sum errw [mm] mean {e[m].mean():+.4e} min {e[m].min():+.4e} max {e[m].max():+.4e}'
                  f'  max|step errw| {c[m, 8].max():.3e}')
        if (~m).any():
            print(f'  {lab} other cols: max|step errw| {c[~m, 8].max():.3e}  sum errw {e[~m].sum():+.3e}')
    if fa.any():
        dice = sa['ice'][fa, 0] - sb['ice'][fa, 0]
        dw = (ca[fa, 7] - cb[fa, 7])
        print(f'  A-B water error per firing col [mm]: mean {dw.mean():+.4e} min {dw.min():+.4e} max {dw.max():+.4e}')
        print(f'  A-B ground ice per firing col [mm]: mean {dice.mean():+.4e} min {dice.min():+.4e} max {dice.max():+.4e}')
        de = -hfus * dice
        print(f'  latent energy -hfus*dice [J/m2]: mean {de.mean():+.4e} min {de.min():+.4e} max {de.max():+.4e}')
        print(f'  fire liq (A meter) [mm]: mean {ca[fa,17].mean():.3f} max {ca[fa,17].max():.3f};'
              f' fire ice mean {ca[fa,18].mean():.4f}; weasd_pre(sneqv at entry) mean {ca[fa,19].mean():.3f}')
        print(f'  weasd end A-B [mm]: mean {(sa["weasd"][fa,0]-sb["weasd"][fa,0]).mean():+.3f}'
              f'  snwdph end A-B [mm]: mean {(sa["snwdph"][fa,0]-sb["snwdph"][fa,0]).mean():+.2f}')


if __name__ == '__main__':
    main()
