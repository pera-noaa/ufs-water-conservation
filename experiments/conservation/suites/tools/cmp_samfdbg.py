"""Compare samf_dbg_*.txt of two runs, keyed by (psp, garea) hashes. usage: cmp_samfdbg.py <runA> <runB>"""
import sys, glob
N = "psp garea hpbl delp prslp phil tkeh q q1 t1 u1 v1 dot cnvw cnvc tgrs pflx tmf qtr maxMF ca_deep islimsk*1000+kcnv".split()
def load(r):
    d = {}
    for f in glob.glob(f"{r}/samf_dbg_*.txt"):
        for l in open(f):
            h = l.split()
            d[(h[0], h[1])] = h
    return d
a, b = load(sys.argv[1]), load(sys.argv[2])
print(len(a), len(b), "columns;", len(set(a) & set(b)), "matched")
cnt = {}
for k in a:
    if k in b and a[k] != b[k]:
        bad = [N[i] for i in range(len(N)) if a[k][i] != b[k][i]]
        for x in bad:
            cnt[x] = cnt.get(x, 0) + 1
print("columns with differing inputs, by input:", cnt)
