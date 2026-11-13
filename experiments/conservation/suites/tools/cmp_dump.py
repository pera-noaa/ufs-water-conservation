"""Compare per-column dumps (sm_dump_*.txt) of two runs by (probe, lon, lat). usage: cmp_dump.py <runA> <runB>"""
import sys, glob
def load(r):
    d = {}
    for f in glob.glob(f"{r}/sm_dump_*.txt"):
        for l in open(f):
            p = l.split()
            d[(int(p[1]), p[2], p[3])] = p[4:]
    return d
a, b = load(sys.argv[1]), load(sys.argv[2])
print(len(a), len(b), "columns x probes")
NAMES = ["W", "cpT", "Lqv", "-Lfqi", "KE", "EF", "Tu", "Ts", "devU", "T1", "Wv", "Wi", "gt0(1)"]
diff = {}
for k in sorted(a):
    if k in b and a[k] != b[k]:
        diff.setdefault(k[0], []).append((k[1], k[2], [NAMES[i] for i in range(len(a[k])) if a[k][i] != b[k][i]]))
for p in sorted(diff):
    print(f"probe {p}: {len(diff[p])} columns differ; first: {diff[p][:5]}")
