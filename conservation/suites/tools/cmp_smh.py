"""First (kdt, probe) where SMH hashes of two runs differ. usage: cmp_smh.py <runA> <runB>"""
import sys
def load(r):
    return {int(l.split()[1]): l.split()[2:] for l in open(f"{r}/out") if l.startswith("SMH ")}
a, b = load(sys.argv[1]), load(sys.argv[2])
for k in sorted(set(a) & set(b)):
    for p, (x, y) in enumerate(zip(a[k], b[k]), start=1):
        if x != y:
            print(f"first diff kdt {k} probe {p}"); sys.exit()
print(f"identical over {len(set(a) & set(b))} steps")
