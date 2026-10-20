#!/usr/bin/env python3
"""tcfind.py <run> <fhr...> : per output time, the strongest 10-m winds over open water (land==0): max and its
lon/lat, and the count of cells with ws10 >= 20, 25, 28 m/s (spray gain ~ (ws10/30)**5.4 * 14 at dt 720 s)."""
import sys
import numpy as np
from netCDF4 import Dataset
run = sys.argv[1]
for fh in sys.argv[2:]:
    best = (0.0, 0.0, 0.0); cnt = [0, 0, 0]
    for t in range(1, 7):
        d = Dataset(f"{run}/sfcf{int(fh):03d}.tile{t}.nc")
        u = d.variables["ugrd10m"][0].astype(float); v = d.variables["vgrd10m"][0].astype(float)
        lm = d.variables["land"][0]; ice = d.variables["icec"][0] if "icec" in d.variables else 0 * lm
        lon = d.variables["grid_xt"][:]; lat = d.variables["grid_yt"][:]
        ws = np.sqrt(u * u + v * v); ws = np.where((lm == 0) & (ice <= 0), ws, 0.0)
        for k, c in enumerate((20, 25, 28)):
            cnt[k] += int((ws >= c).sum())
        j = np.unravel_index(np.argmax(ws), ws.shape)
        if ws[j] > best[0]:
            best = (float(ws[j]), float(lon[j]), float(lat[j]))
    print(f"f{int(fh):03d} max ws10 {best[0]:.1f} at {best[1]:.1f}E {best[2]:.1f}N  n>=20/25/28: {cnt}")
