#!/usr/bin/env python3
"""F3 gate from a run's stdout (TM/TP tracer meters + TX F3 meter).
usage: f3_gate.py <out> [n1name:col n2name:col]  (default pt_ghg:15 pt_udry:16)
Chemical tracers: n=1 pt_ghg (TM column 15), n=2 pt_udry (16); generic pt_cnv (12) shown as a fscav-free reference.
TX slots (per step, summed over ranks, kg): deep 1-8, shallow 11-18 (see meter_f3.py)."""
import sys
import re
from fractions import Fraction as F

out = sys.argv[1]
g = 9.80665
map_ = [a.split(':') for a in sys.argv[2:4]] or [['pt_ghg', '15'], ['pt_udry', '16']]
TM, TP, TX = {}, {}, {}
pat = re.compile(r'\b(TM|TP|TX) +(\d+ .*)$')
for line in open(out, errors='replace'):
    m = pat.search(line)
    if not m:
        continue
    tag, rest = m.groups()
    f = rest.split()
    if tag == 'TX':
        TX[int(f[0])] = [float(x) for x in f[1:]]
        continue
    step, ip = int(f[0]), int(f[1])
    r = f[2:]
    v = [F(r[2 * c]) + F(r[2 * c + 1]) for c in range(len(r) // 2)]
    (TM if tag == 'TM' else TP)[(step, ip)] = v
steps = sorted({s for s, _ in TM})
s0, s1 = steps[0], steps[-1]
cols = {m[0]: int(m[1]) for m in map_}
cols['pt_cnv'] = 12
nidx = {m[0]: i + 1 for i, m in enumerate(map_)}
xs = sorted(TX)
print(f"run {out}: TM steps {s0}..{s1} ({len(steps)}), TX steps {len(xs)}")


def txsum(i):
    return sum(TX[s][i - 1] for s in xs)


print("tracer   n  M0(kg)        dM_atm/M0      D_deep/M0     D_shal/M0     (dM+D)/M0     [SAMF: (dM+D)/D deep, shal]  sum|col res|/D deep, shal")
for name, c in cols.items():
    m0 = float(TM[(s0, 1)][c]) / g
    dm = float(TM[(s1, 18)][c] - TM[(s0, 1)][c]) / g
    if name == 'pt_cnv':
        print(f"{name:8s} -  {m0:.6e}  {dm / m0:+.6e}  (generic, no scavenging)")
        continue
    n = nidx[name]
    dd, ds = txsum(2 + n), txsum(12 + n)
    md, ms = txsum(n), txsum(10 + n)
    rd = (md + dd) / dd if dd else 0.0
    rs = (ms + ds) / ds if ds else 0.0
    print(f"{name:8s} {n}  {m0:.6e}  {dm / m0:+.6e}  {dd / m0:+.6e}  {ds / m0:+.6e}  {(dm + dd + ds) / m0:+.6e}"
          f"  [{rd:+.3e}, {rs:+.3e}]")
for b, nm in ((0, 'deep'), (10, 'shallow')):
    D = txsum(b + 3) + txsum(b + 4)
    print(f"{nm:8s}: sum|column residual|/D = {txsum(b + 5) / D if D else 0:.3e};  borrow events else/if = "
          f"{txsum(b + 6):.0f}/{txsum(b + 7):.0f};  wet_dep at stake in else-branch / D = {txsum(b + 8) / D if D else 0:.3e}")
for k, nm in ((1, 'DCNV'), (2, 'SCNV')):
    if (s1, k) in TP:
        for name, n in nidx.items():
            tp = float(TP[(s1, k)][cols[name]]) / g
            tx = txsum((k - 1) * 10 + n)
            print(f"{nm} post applied dM ({name}) {tp:+.6e} kg vs scheme dM {tx:+.6e} kg: rel diff {(tp - tx) / tx if tx else 0:+.2e}")
