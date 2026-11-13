#!/usr/bin/env python3
"""Per-step residuals (W m-2 global): soil land R and parts, glacier R, ice3lay R. Usage: es_resid_ts.py <out> [k0 k1]"""
import sys
from collections import defaultdict
HF = 3.3358e5
fn = sys.argv[1]
k0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
k1 = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
st = defaultdict(lambda: [0.0] * 261)
for line in open(fn, errors="replace"):
    if "ESG " not in line:
        continue
    p = line[line.index("ESG "):].split()
    k, s = int(p[1]), int(p[2])
    for j, v in enumerate(p[3:13]):
        st[k][10 * (s - 1) + j + 1] = float(v)
print("kdt   soil:R        R_E        R_W        R_S   glacier:R  ice3lay:R  between(soil,gla,ice)")
for k in sorted(st):
    if not k0 <= k <= k1:
        continue
    G = st[k]
    w = 1.0 / (G[170] * 720.0)
    L = lambda f, o=0: G[o + f - 4] * w
    E = lambda kk: L(22 + kk)
    B = L(8) - L(9) - L(10) - L(11) + L(12) + E(14) + E(24) - HF * L(17) + HF * (E(22) + E(23))
    RE = E(5) + E(6) - E(29) - E(14)
    RW = E(7) + E(8) + E(9) + E(10) - (E(24) - HF * (L(17) - E(28)) + HF * (E(22) + E(23)))
    RS = -E(11) - E(13)
    Bg = L(8, 55) - L(9, 55) - L(10, 55) - L(23, 55) + L(25, 55) - HF * L(17, 55) + HF * (L(14, 55) + L(16, 55))
    I = lambda f: G[110 + f - 59] * w
    ri = I(65) - I(67) - I(68)
    print(f"{k:4d} {L(6) - B:+.3e} {RE:+.3e} {RW:+.3e} {RS:+.3e} {L(6, 55) - Bg:+.3e} {ri:+.3e}  "
          f"{G[191]*w:+.2e} {G[180]*w:+.2e} {G[193]*w:+.2e}")
