"""Link the differing column (probe dumps, lon/lat) to its SAMF checkpoints (keyed by psp, garea).
usage: find_target.py <runA> <runB>"""
import sys, glob
def dump(r):
    d = {}
    for f in glob.glob(f"{r}/sm_dump_*.txt"):
        for l in open(f):
            p = l.split(); d[(int(p[1]), p[2], p[3])] = p[4:]
    return d
def cps(r):
    d = {}
    for f in glob.glob(f"{r}/samf_cp_*.txt"):
        for l in open(f):
            h = l.split(); d.setdefault(h[0], {})[int(h[2], 16)] = h[3:]
    return d
a, b = dump(sys.argv[1]), dump(sys.argv[2])
tg = sorted({(k[1], k[2]) for k in a if k in b and a[k] != b[k]})
print("differing columns:", tg)
ca, cb = cps(sys.argv[1]), cps(sys.argv[2])
for lon, lat in tg[:3]:
    psp = a[(4, lon, lat)][-1].lower()
    psp16 = psp.rjust(16, '0')
    keys = [k for k in ca if k.lower().rjust(16, '0') == psp16] + [k for k in cb if k.lower().rjust(16, '0') == psp16]
    print(lon, lat, "psp", psp, "keys", set(keys))
    for k in set(keys):
        print("  A checkpoints:", {c: v for c, v in sorted(ca.get(k, {}).items())})
        print("  B checkpoints:", {c: v for c, v in sorted(cb.get(k, {}).items())})
    for p in range(1, 9):
        if (p, lon, lat) in a:
            print("  probe", p, "same" if a[(p, lon, lat)] == b.get((p, lon, lat)) else "DIFF")
