#!/usr/bin/env python3
"""r15 trace: per-window and 24-h sums of the PBL family residual and the satmedmfvdifq probes from <rundir>/out.
Usage: trace_table.py RUNDIR [...]"""
import re
import sys

NAMES = {1: 'MLM dW', 2: 'solver dW', 3: 'solver sfc src', 4: 'fixers dW', 5: 'scheme dW', 6: 'E (dt rho evap)',
         7: 'neg end', 8: 'neg entry', 9: 'neg after MLM', 10: 'MLM active frac*steps', 11: 'MLM gross',
         12: 'scheme res 5-6', 13: 'split chk 5-(1+2+4)', 14: 'solver res 2-3',
         15: 'q1(1)<qmin frac*steps', 16: 'sfc src - E (3-6)',
         17: 'qc neg k=mlmb-1 (bottom blk)', 18: 'qc neg k=mlmt+1 (top blk)', 19: 'qc neg k=cldbase-1 (smooth)',
         20: 'qc neg interior', 21: 'qc neg other'}
MP = ['qv', 'qc', 'qr', 'qi', 'qs', 'qg']


def lines(rd):
    b = {}
    for ln in open(f"{rd}/out", errors="replace"):
        ln = re.sub(r"^\s*\d+:\s*", "", ln)
        if ln.startswith("BUDGET water"):
            p = ln.split()
            b.setdefault(round(float(p[2])), {})[p[3]] = [float(x) for x in p[4:9]]
    return b


for rd in sys.argv[1:]:
    b = lines(rd)
    fhs = sorted(b)
    print(f"== {rd}  windows {fhs}")
    rows = [('C:fam_pbl', 'chg', 0), ('C:fam_pbl', 'decl', 1), ('C:fam_pbl', 'res', 2),
            ('C:satmedmfvdifq', 'chg', 0), ('C:GFS_PBL_generic_post', 'chg', 0)]
    for key, lab, j in rows:
        k = [s for s in b[fhs[0]] if s.endswith(key.split(':')[-1]) and (key.startswith('C:fam') == s.startswith('C:fam'))]
        if not k:
            continue
        vals = [b[f][k[0]][j] for f in fhs]
        print(f"{k[0]+' '+lab:44s}" + ''.join(f"{v:+.6e} " for v in vals) + f"| 24h {sum(vals):+.6e}")
    for s in range(1, 22):
        k = f"P:satmedmfvdifq:{s:02d}"
        if k not in b[fhs[0]]:
            continue
        vals = [b[f][k][0] for f in fhs]
        mabs = max(b[f][k][4] for f in fhs)
        print(f"P{s:02d} {NAMES[s]:39s}" + ''.join(f"{v:+.6e} " for v in vals) + f"| 24h {sum(vals):+.6e} max|col| {mabs:.3e}")
    tin = [0.0] * len(fhs)
    for s in range(1, 13):
        k = f"P:mp_thompson:{s:02d}"
        if k not in b[fhs[0]]:
            continue
        vals = [b[f][k][0] for f in fhs]
        if 2 <= s <= 6:
            tin = [a + v for a, v in zip(tin, vals)]
        lab = ('MP in neg ' if s <= 6 else 'MP out neg ') + MP[(s - 1) % 6]
        print(f"M{s:02d} {lab:39s}" + ''.join(f"{v:+.6e} " for v in vals) + f"| 24h {sum(vals):+.6e}")
    if any(tin):
        fam = [b[f]['C:fam_mp'][2] for f in fhs]
        print(f"{'MP in neg, condensate (2-6)':43s}" + ''.join(f"{v:+.6e} " for v in tin) + f"| 24h {sum(tin):+.6e}")
        print(f"{'fam_mp res + (2-6) [= res w/o clip]':43s}" + ''.join(f"{a+v:+.6e} " for a, v in zip(fam, tin)) + f"| 24h {sum(fam)+sum(tin):+.6e}")
