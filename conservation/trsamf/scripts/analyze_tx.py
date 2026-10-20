#!/usr/bin/env python3
"""Cloud-base defect meter (TX, develop SAMF) against the SAMF slot changes (TP), per tracer, 24 h sums / initial mass.
usage: analyze_tx.py <out>"""
import sys, re
from fractions import Fraction as F
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from txparse import read_tx
TX, TP, TM = read_tx(sys.argv[1]), {}, {}
for line in open(sys.argv[1], errors='replace'):
    m = re.search(r'\b(TP|TM) +(\d+ .*)$', line)
    if not m:
        continue
    tag, f = m.group(1), m.group(2).split()
    r = f[2:]
    v = [F(r[2*c]) + F(r[2*c+1]) for c in range(len(r)//2)]
    (TP if tag == 'TP' else TM)[(int(f[0]), int(f[1]))] = v
steps = sorted(TX)
names = ['sphum','liq_wat','ice_wat','rainwat','snowwat','graupel','ice_nc','rain_nc','o3mr',
         'sgs_tke','pt_dyn_nopbl','pt_cnv','pt_plume','pt_umoist','pt_ghg','pt_udry']
m0 = TM[(min(s for s, _ in TM), 1)]
last = max(s for s, _ in TP)
dc = TP[(last, 1)]; sc = TP[(last, 2)]
tot = [sum(TX[s][i] for s in steps) for i in range(100)]
print('slot changes / initial mass (DCNV, SCNV):')
for j, nm in enumerate(names, start=1):
    if nm.startswith('pt_') or nm in ('o3mr', 'sgs_tke'):
        if m0[j] == 0:
            print(f'  {nm:13s} DCNV {float(dc[j]):11.3e}  SCNV {float(sc[j]):11.3e}  (absolute, m0 = 0)'); continue
        print(f'  {nm:13s} DCNV {float(dc[j]/m0[j]):11.3e}  SCNV {float(sc[j]/m0[j]):11.3e}  m0 {float(m0[j]):.4e}')
print('defect meter per ctr index n: deep kb(phi=0, phi>0) jmin(phi=0, phi>0) total | gross | shallow kb(phi=0, phi>0) total  [Pa m2, 24 h]')
for n in range(1, 11):
    d = tot[4*(n-1):4*n]; g = tot[40+n-1]; s = tot[60+2*(n-1):60+2*n]
    if not any(d) and not any(s):
        continue
    print(f'  n={n:2d} ' + ' '.join(f'{x:10.3e}' for x in d) + f' | {sum(d):10.3e} | {g:10.3e} | ' + ' '.join(f'{x:10.3e}' for x in s) + f' | {sum(s):10.3e}')
print('shallow diag (if present): n, pre-rescale update sum tm_x(80+n), end change tm_x(90+n)')
for n in range(1, 11):
    if tot[79+n] or tot[89+n]:
        print(f'  n={n:2d} {tot[79+n]:12.5e} {tot[89+n]:12.5e}')
print('timing (if present): deep routine/block, shallow routine/block [s, sum over ranks]:', ' '.join(f'{x:.2f}' for x in tot[50:54]),
      '| helper column-steps deep/shallow', f'{tot[54]:.0f} {tot[55]:.0f}', '| mean nsub', f'{tot[56]/max(tot[54],1):.2f} {tot[57]/max(tot[55],1):.2f}')
print('match: for each pt tracer, defect total / slot change (deep, shallow) using the n with the closest deep value')
for j, nm in enumerate(names, start=1):
    if not nm.startswith('pt_') and nm not in ('o3mr', 'sgs_tke'):
        continue
    best = min(range(1, 11), key=lambda n: abs(sum(tot[4*(n-1):4*n]) - float(dc[j])))
    dd = sum(tot[4*(best-1):4*best]); ss = sum(tot[60+2*(best-1):60+2*best])
    print(f'  {nm:13s} n={best:2d} deep defect {dd:12.5e} slot {float(dc[j]):12.5e} ratio {dd/float(dc[j]) if dc[j] else float("nan"):.6f}'
          f' | shallow defect {ss:12.5e} slot {float(sc[j]):12.5e} ratio {ss/float(sc[j]) if sc[j] else float("nan"):.6f}')
