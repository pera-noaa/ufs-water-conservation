"""cmp_bits.py A B fh : per-variable bitwise compare of atmf/sfcf<fh>.tile1-6 between run dirs A and B."""
import sys, numpy as np, netCDF4 as nc
A, B, fh = sys.argv[1], sys.argv[2], sys.argv[3]
for kind in ("sfcf", "atmf"):
    tot = {}
    for t in range(1, 7):
        fa = nc.Dataset(f"{A}/{kind}{fh}.tile{t}.nc"); fb = nc.Dataset(f"{B}/{kind}{fh}.tile{t}.nc")
        for v in fa.variables:
            a = fa[v][:]; b = fb[v][:]
            if a.ndim < 2: continue
            a = np.ma.filled(a, np.nan).astype("f8"); b = np.ma.filled(b, np.nan).astype("f8")
            d = (a != b) & ~(np.isnan(a) & np.isnan(b))
            n, m = tot.get(v, (0, 0.0))
            mx = np.nanmax(np.abs(a - b)[d]) if d.any() else 0.0
            # count differing horizontal columns
            col = d.reshape(-1, d.shape[-2], d.shape[-1]).any(axis=0)
            tot[v] = (n + int(col.sum()), max(m, mx))
        fa.close(); fb.close()
    nd = {v: x for v, x in tot.items() if x[0] > 0}
    print(f"{kind}{fh}: {len(nd)}/{len(tot)} vars differ")
    for v, (n, m) in sorted(nd.items(), key=lambda z: -z[1][0])[:25]:
        print(f"  {v:14s} cols={n:7d} max|d|={m:.3e}")
