#!/usr/bin/env python3
"""Per-process attribution of the dry-mole-fraction spread of pt_udry (TD/TS lines), plus TO/TH/TC summaries.
usage: analyze_dry.py <out>. dev = c_dry/c0 - 1, c0 = 1e-6; MS = dry-mass-weighted mean of dev^2.
Physics points J..M and slots use the dry mass the write-back keeps, D = dp*(1 - qv_in)."""
import sys, re, math
TD, TS, TO, TH, TC = {}, {}, {}, {}, {}
for line in open(sys.argv[1], errors='replace'):
    m = re.search(r'\b(TD|TS|TO|TH|TC) +(\d+ .*)$', line)
    if not m:
        continue
    tag, f = m.group(1), m.group(2).split()
    if tag == 'TD':
        TD[(int(f[0]), int(f[1]))] = [float(x) for x in f[2:]]
    else:
        {'TS': TS, 'TO': TO, 'TH': TH, 'TC': TC}[tag][int(f[0])] = [float(x) for x in f[1:]]
steps = sorted({s for s, _ in TD})
ms = lambda s, p: TD[(s, p)][0] / TD[(s, p)][1]
TERMS = [('dyn_core+tracer_2d', [(2, 3), (5, 6)]), ('remap', [(3, 4), (6, 7)]), ('other fv_dynamics', [(1, 2), (4, 5), (7, 8), (8, 9), (9, 10)]),
         ('fv_subgrid_z', [(10, 11)]), ('gap H>I', [(11, 12)]), ('statein conv', [(12, 13)]), ('physics total', [(13, 14)]),
         ('fill_gfs + nopbl', [(14, 15), (15, 16)]), ('write-back', [(16, 17)]), ('fv_update_phys', [(17, 18)])]
print(f"pt_udry: rms dev at step {steps[0]} point A: {math.sqrt(ms(steps[0],1)):.4e}, max {TD[(steps[0],1)][2]:.4e};"
      f" at step {steps[-1]} point O: {math.sqrt(ms(steps[-1],18)):.4e}, max {TD[(steps[-1],18)][2]:.4e}")
print('process'.ljust(26) + 'sum dMS (24h)'.rjust(14) + '   largest 1-step increase of max|dev|')
tot = 0.
for name, pairs in TERMS:
    d = 0.; mx = 0.
    for s in steps:
        for a, b in pairs:
            if (s, a) in TD and (s, b) in TD:
                d += ms(s, b) - ms(s, a); mx = max(mx, TD[(s, b)][2] - TD[(s, a)][2])
    tot += d
    print(name.ljust(26) + f'{d:14.4e}   {mx:.3e}')
d = sum(ms(s + 1, 1) - ms(s, 18) for s in steps[:-1] if (s + 1, 1) in TD)
print('gap O>A'.ljust(26) + f'{d:14.4e}'); tot += d
print('TOTAL'.ljust(26) + f'{tot:14.4e}   check: {ms(steps[-1],18)-ms(steps[0],1):.4e}')
if TS:
    Dm = TD[(steps[0], 13)][1]
    for k, nm in enumerate(['  phys: SAMF deep (DCNV post)', '  phys: SAMF shallow (SCNV post)', '  phys: PBL etc (GWD post)']):
        print(nm.ljust(26) + f'{sum(v[2*k] for v in TS.values())/Dm:14.4e}   max|dev| after: {max(v[2*k+1] for v in TS.values()):.3e}')
if TO:
    names = ['qv', 'T', 'pt_umoist', 'pt_cnv']
    print('SAMF deep increments, levels 1-6: columns with >=4 sign alternations / columns changed; max rel. increment k<=5')
    for i, n in enumerate(names):
        a = sum(v[3*i] for v in TO.values()); c = sum(v[3*i+1] for v in TO.values()); mx = max(v[3*i+2] for v in TO.values())
        print(f'  {n:10s} {a:10.0f} / {c:10.0f} = {a/max(c,1):.4f}   max {mx:.3e}')
if TH:
    h = [sum(v[i] for v in TH.values()) for i in range(7)]; n = sum(h)
    print('SAMF deep column-steps by max donor Courant  <.5 <1 1-2 2-3 3-4 4-5 >=5:', ' '.join(f'{x:.0f}' for x in h),
          f' (>1: {sum(h[2:])/n:.3f})')
if TC:
    print('max Courant over run', max(v[0] for v in TC.values()))
