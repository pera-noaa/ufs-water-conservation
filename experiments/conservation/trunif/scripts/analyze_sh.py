#!/usr/bin/env python3
"""Shadow-meter table from a run's stdout ('SH step ip iq ms max k lat lon', 'SI label ...').
usage: analyze_sh.py <out file> [first_step=1] [last_step=inf]"""
import sys, re, collections
f = sys.argv[1]; s0 = int(sys.argv[2]) if len(sys.argv) > 2 else 1; s1 = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
NAME = {1: 'O->A between steps', 2: 'A->B fv_dyn start', 3: 'dyn_core+tracer_2d', 4: 'remap (L2E+fillz)', 5: 'D->B gap',
        6: 'D2->E gap', 7: 'neg_adj3', 8: 'F->G rest fv_dyn', 9: 'fv_subgrid_z', 10: 'statein dyn->phys', 11: 'J->GWDpost (no apply)',
        12: 'PBL apply (satmedmfvdifq)', 14: 'SAMF deep (+photochem)', 15: 'SAMF shallow', 16: 'SCNV->M (mp,fill,nopbl)',
        17: 'write-back phys->dyn', 18: 'fv_update_phys'}
Q = ['dry', 'moist', 'physb', 'term', 'resid']
acc = collections.defaultdict(lambda: [0.0, 0.0, -1.0, None, 0, 0.0])  # sumMS, n, max, loc, step_of_max, step1 ms
nst = 0
for ln in open(f, errors='replace'):
    m = re.search(r'\b(SH|SI) +-?\d', ln)
    if not m:
        continue
    ln = ln[m.start():]
    if ln.startswith('SI '):
        print(ln.rstrip())
        continue
    p = ln.split()
    st, ip, iq = int(p[1]), int(p[2]), int(p[3])
    if st < s0 or st > s1:
        continue
    ms, mx, k, la, lo = float(p[4]), float(p[5]), p[6], p[7], p[8]
    a = acc[(ip, iq)]
    a[0] += ms; a[1] += 1
    if mx > a[2]:
        a[2] = mx; a[3] = (k, la, lo); a[4] = st
    if st == s0:
        a[5] = ms
    nst = max(nst, st)
print(f'steps {s0}..{min(s1, nst)}; per process: sum over steps of dry-mass-weighted MS (generated variance), max|dev| (k lat lon step)')
print(f"{'ip':>3} {'process':26s} " + ' '.join(f'{q:>22s}' for q in Q))
for ip in sorted({k[0] for k in acc}):
    row = [f'{ip:3d} {NAME.get(ip, "?"):26s}']
    for iq in range(1, 6):
        a = acc.get((ip, iq))
        row.append(f'{a[0]:10.3e}/{a[2]:10.3e}' if a else ' ' * 22)
    print(' '.join(row))
print('locations of max (k lat lon step) for dry/moist/physb:')
for ip in sorted({k[0] for k in acc}):
    print(f'{ip:3d} {NAME.get(ip, "?"):26s} ' + ' | '.join(f'{acc[(ip, iq)][3]} s{acc[(ip, iq)][4]}' for iq in (1, 2, 3)))
