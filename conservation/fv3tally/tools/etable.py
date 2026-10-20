#!/usr/bin/env python3
"""etable.py <run out file> [<run2 out> ...] : 24 h per-term tally of FV3's TE from the ETL lines of fv_etally.
Prints W m-2 (sum of per-step J m-2 / 86400). Positive = energy gained by the atmosphere."""
import sys
B = ['RAY', 'CONV', 'DYN', 'DCON', 'DYN2', 'TRC', 'REMAP', 'FIX', 'L2EX', 'POST']
C = ['IE', 'PE', 'KH', 'KW']
D = ['Ldiv', 'Lvort', 'Lw', 'Hw', 'Huv']
H = ['raw', 'smo', 'app', 'cap', 'ncap']
G = ['k1', 'k2', 'k3+']


NT = 70


def load(fn):
    """ETL records. The root PE's long write wraps at a fixed width, mid-number, onto continuation lines
    (srun --label prefix 'N: '): strip the label and concatenate the raw text before splitting."""
    import re
    lab = re.compile(r'^\s*\d+: ')
    rows, cur = [], None
    for ln in open(fn):
        body = lab.sub('', ln.rstrip('\n'), count=1)
        if body.lstrip().startswith('ETL'):
            cur = body.split('ETL', 1)[1]
        elif cur is not None:
            cur += body
        else:
            continue
        t = cur.split()
        if len(t) >= NT + 1 and not cur.endswith(t[-1]) or len(t) == NT + 1 and re.search(r'E[+-]\d\d$', t[-1]):
            rows.append([float(x) for x in t[1:NT+1]])
            cur = None
    return rows


def table(fn):
    rows = load(fn)
    n = len(rows)
    tot = [sum(r[i] for r in rows) for i in range(len(rows[0]))]
    w = [x / 86400. for x in tot]
    print(f'== {fn}: {n} steps (W m-2, 24 h; +gain)')
    bt = {}
    for b in range(10):
        v = w[b*4:b*4+4]
        bt[B[b]] = sum(v)
        print(f'{B[b]:6s} TE {sum(v):+.6e}  ' + '  '.join(f'{C[c]} {v[c]:+.4e}' for c in range(4)))
    o = 40
    for d in range(5):
        print(f'dsw {D[d]:6s} ' + '  '.join(f'{G[g]} {w[o+d*3+g]:+.5e}' for g in range(3)) + f'  sum {sum(w[o+d*3:o+d*3+3]):+.5e}')
    o = 55
    for h in range(5):
        vals = tot[o+h*3:o+h*3+3] if h == 4 else w[o+h*3:o+h*3+3]
        print(f'heat {H[h]:5s} ' + '  '.join(f'{G[g]} {vals[g]:+.5e}' for g in range(3)) + f'  sum {sum(vals):+.5e}')
    inwin = sum(bt[k] for k in ['RAY', 'CONV', 'DYN', 'DCON', 'DYN2', 'TRC', 'REMAP', 'L2EX'])
    print(f'fixer window terms (te0 -> before fix) {inwin:+.6e}; fixer {bt["FIX"]:+.6e}; window net {inwin+bt["FIX"]:+.3e}')
    return w


if __name__ == '__main__':
    for f in sys.argv[1:]:
        table(f)
