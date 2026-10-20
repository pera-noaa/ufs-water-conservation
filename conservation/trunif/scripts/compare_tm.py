#!/usr/bin/env python3
"""Bit-identity of the model state through the tracer agent's TM/TP meter lines ('TM step ip (hi lo) x (air, tracers.., dry)').
srun --label prefixes and runtime record wrapping (which can split a number) are undone by joining rank-0 continuation
lines. Compares, for every line present in both runs, the first n (hi, lo) pairs (air + the first n-1 tracers) as strings.
usage: compare_tm.py <out A> <out B> <n pairs>"""
import sys, re
LAB = re.compile(r'^\s*0: ?')
TAG = re.compile(r'^\s*(TM|TP|TU|TQ|TC|TH|TD|TS|TO|SH|SI|TG) ')
def load(f, n):
    recs, cur = [], None
    for ln in open(f, errors='replace'):
        m = LAB.match(ln)
        if not m:
            cur = None; continue
        body = ln[m.end():].rstrip('\n')
        if TAG.match(body):
            cur = [body]; recs.append(cur)
        elif cur is not None and re.match(r'^[0-9 .E+\-]+$', body):
            cur.append(body)
        else:
            cur = None
    d = {}
    for r in recs:
        p = ''.join(r).split()
        if p[0] in ('TM', 'TP'):
            d[(p[0], p[1], p[2])] = p[3:3 + 2 * n]
    return d
n = int(sys.argv[3])
a, b = load(sys.argv[1], n), load(sys.argv[2], n)
common = sorted(set(a) & set(b), key=lambda k: (k[0], int(k[1]), int(k[2])))
bad = [k for k in common if a[k] != b[k]]
print(f'lines A {len(a)} B {len(b)} common {len(common)} differing {len(bad)}; compared {n} pairs each')
for k in bad[:5]:
    print(k, [(i, x, y) for i, (x, y) in enumerate(zip(a[k], b[k])) if x != y][:3])
