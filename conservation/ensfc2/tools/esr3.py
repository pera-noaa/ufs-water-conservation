import sys
import numpy as np
names = "r dH B b1 b2 b3 b4 e1 e2 p1 p2 E25 E19 d65 d66 EP LW2 AIR s31 s32 s33 s34 s35 s36 s37 s38 s39 s40".split()
rows = []
for line in open(sys.argv[1], errors="replace"):
    if "ESR " not in line: continue
    p = line[line.index("ESR "):].split()
    v = dict(zip(names, map(float, p[3:]))); v["kdt"] = int(p[1]); rows.append(v)
y = np.array([v["r"] for v in rows])
print("n", len(rows), "sum r", y.sum(), "rms", np.sqrt((y*y).mean()))
for c in ["s33", "s34", "s35", "s36", "p1", "p2", "e1", "E19", "EP", "b4", "b1"]:
    x = np.array([v[c] for v in rows]); 
    if np.all(x == 0): print(c, "all zero"); continue
    cc = np.corrcoef(x, y)[0, 1]; k = (x @ y)/(x @ x)
    print(f"{c:4s} corr {cc:+.3f} slope {k:+.4e} rms after {np.sqrt(((y-k*x)**2).mean()):.3e}")
# columns with no snow activity
q = [v for v in rows if v["p1"] == 0 and v["p2"] == 0 and abs(v["s33"]) < 1e-6 and abs(v["s34"]) < 1e-6]
print("rows with no snowwater change:", len(q), "their r rms", np.sqrt(np.mean([v["r"]**2 for v in q])) if q else 0)
for v in rows[:5]:
    print({k: round(v[k], 4) for k in ["r", "s33", "s34", "s35", "p1", "p2", "e1", "E19", "EP", "b4", "kdt"]})
