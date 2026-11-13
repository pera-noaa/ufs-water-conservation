#!/usr/bin/env python3
"""Attribute tracer-mass changes from TM/TP lines in a run's stdout.
usage: analyze_tm.py <out file> [names comma list: index:name] ; prints relative (to initial mass) 24 h sums per term.
Columns: air(0), tracers 1..nq, dry(nq+1). Terms are differences between consecutive meter points."""
import sys, re, math
from fractions import Fraction as F

path = sys.argv[1]
TM, TP, TU = {}, {}, {}
pat = re.compile(r'\b(TM|TP|TU|TQ) +(\d+ .*)$')
HL = '--hl' in sys.argv
for line in open(path, errors='replace'):
    m = pat.search(line)
    if not m:
        continue
    tag, rest = m.groups()
    f = rest.split()
    if tag == 'TU':
        TU[int(f[0])] = [float(x) for x in f[1:]]
        continue
    if tag == 'TQ':
        continue
    step, ip = int(f[0]), int(f[1]); r = f[2:]
    if HL:   # (hi, lo) pairs -> exact Fractions
        v = [F(r[2 * c]) + F(r[2 * c + 1]) for c in range(len(r) // 2)]
    else:
        v = [F(x) for x in r]
    (TM if tag == 'TM' else TP)[(step, ip)] = v
steps = sorted({s for s, _ in TM})
nv = len(next(iter(TM.values())))
nq = nv - 2
names = {0: 'air', nq + 1: 'dry'}
default = ['sphum', 'liq_wat', 'ice_wat', 'rainwat', 'snowwat', 'graupel', 'ice_nc', 'rain_nc', 'o3mr', 'sgs_tke',
           'pt_dyn_nopbl', 'pt_cnv', 'pt_plume', 'pt_umoist', 'pt_ghg', 'pt_udry']
for i, n in enumerate(default[:nq], start=1):
    names[i] = n
cols = [0] + [i for i in range(1, nq + 1) if names[i].startswith('pt_')] + [nq + 1]
TERMS = [('A>B1 pre-dyn', 1, 2), ('B1>C1 dyn_core+tracer_2d', 2, 3), ('C1>D1 remap', 3, 4), ('D1>B2', 4, 5),
         ('B2>C2 dyn_core+tracer_2d', 5, 6), ('C2>D2 remap', 6, 7), ('D2>E', 7, 8), ('E>F neg_adj3', 8, 9),
         ('F>G end fv_dyn', 9, 10), ('G>H fv_subgrid_z', 10, 11), ('H>I gap', 11, 12), ('I>J statein conv', 12, 13),
         ('J>K physics', 13, 14), ('K>L fill_gfs', 14, 15), ('L>M nopbl', 15, 16), ('M>N write-back', 16, 17),
         ('N>O fv_update_phys', 17, 18)]
last = steps[-1]
acc = {t[0]: [F(0)] * nv for t in TERMS}
acc['O>A gap'] = [F(0)] * nv
rms = {k: [0.0] * nv for k in acc}
for s in steps:
    for name, a, b in TERMS:
        if (s, a) in TM and (s, b) in TM:
            for c in range(nv):
                d = F(TM[(s, b)][c]) - F(TM[(s, a)][c]); acc[name][c] += d; rms[name][c] += float(d) ** 2
    if s < last and (s + 1, 1) in TM:
        for c in range(nv):
            d = F(TM[(s + 1, 1)][c]) - F(TM[(s, 18)][c]); acc['O>A gap'][c] += d; rms['O>A gap'][c] += float(d) ** 2
# physics slots
slots = {1: 'phys: DCNV post', 2: 'phys: SCNV post', 3: 'phys: GWD post (sfc+PBL+GWD)'}
for k, nm in slots.items():
    if (last, k) in TP:
        acc[nm] = [F(x) for x in TP[(last, k)]]
        rms[nm] = [0.0] * nv
        prev = [0.0] * nv
        for s in steps:
            if (s, k) in TP:
                cur = TP[(s, k)]; rms[nm] = [r + (c - p) ** 2 for r, c, p in zip(rms[nm], cur, prev)]; prev = cur
m0 = [F(x) for x in TM[(steps[0], 1)]]
tot = [F(TM[(last, 18)][c]) - m0[c] for c in range(nv)]
w = 11
print(f"run {path}: steps {steps[0]}..{last}; values = 24 h sum / initial mass  [rms per-step / initial mass]")
print('term'.ljust(32) + ''.join(names[c][:w].rjust(w + 1) for c in cols))
for k in list(acc):
    row = acc[k]
    if all(row[c] == 0 for c in cols):
        print(k.ljust(32) + ''.join('0'.rjust(w + 1) for c in cols)); continue
    print(k.ljust(32) + ''.join(f"{float(row[c] / m0[c]) if m0[c] else 0.:{w+1}.2e}" for c in cols))
    print(''.ljust(32) + ''.join(f"[{math.sqrt(rms[k][c]) / float(m0[c]) if m0[c] else 0.:.1e}]".rjust(w + 1) for c in cols))
print('TOTAL O(last)-A(1)'.ljust(32) + ''.join(f"{float(tot[c] / m0[c]) if m0[c] else 0.:{w+1}.2e}" for c in cols))
print('initial mass (Pa m2)'.ljust(32) + ''.join(f"{float(m0[c]):{w+1}.4e}" for c in cols))
if TU:
    s0, s1 = min(TU), max(TU)
    print('TU udry_min udry_max umoist_min umoist_max  first:', ' '.join(f'{x:.10e}' for x in TU[s0]))
    print('TU                                           last :', ' '.join(f'{x:.10e}' for x in TU[s1]))
TQ = {}
for line in open(path, errors='replace'):
    m = re.search(r'\bTQ +(\d+ .*)$', line)
    if m:
        f = m.group(1).split(); TQ[int(f[0])] = [float(x) for x in f[1:]]
if TQ:
    print('uniform-moist tracer, relative change per scheme call (max over steps; cells>1% summed over steps):')
    for k, nm in slots.items():
        mx = max(TQ.values(), key=lambda r: r[4 * (k - 1)])
        print(f'  {nm:32s} max {mx[4*(k-1)]:.3e} at level {int(mx[4*(k-1)+1])}  '
              f'cells>1%: {sum(r[4*(k-1)+2] for r in TQ.values()):.0f} of {sum(r[4*(k-1)+3] for r in TQ.values()):.0f}')
