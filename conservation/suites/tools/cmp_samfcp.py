"""Compare samf_cp_*.txt checkpoint hashes of two runs by (psp, garea, cp). usage: cmp_samfcp.py <runA> <runB>"""
import sys, glob
N = ["psp", "garea", "cp", "cnvflg", "kb|kbcon|ktcon", "jmin", "aa1", "edto", "xmb", "sum(t1+q1 new)"]
def load(r):
    d = {}
    for f in glob.glob(f"{r}/samf_cp_*.txt"):
        for l in open(f):
            h = l.split(); d[(h[0], h[1], int(h[2], 16))] = h
    return d
a, b = load(sys.argv[1]), load(sys.argv[2])
print(len(a), len(b), "entries")
cols = {}
for k in a:
    if k in b and a[k] != b[k]:
        cols.setdefault((k[0], k[1]), []).append((k[2], [N[i] for i in range(3, 10) if a[k][i] != b[k][i]]))
for c, v in cols.items():
    v.sort()
    print("column", c, "first differing checkpoint:", v[0], "all:", [x[0] for x in v])
onlya = [k for k in a if k not in b]; onlyb = [k for k in b if k not in a]
print("checkpoints present in one run only:", len(onlya), len(onlyb), sorted(set(k[2] for k in onlya)), sorted(set(k[2] for k in onlyb)))
