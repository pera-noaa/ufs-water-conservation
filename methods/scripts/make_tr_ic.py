#!/usr/bin/env python3
"""Copy the cold-start gfs_data.tile[1-6].nc into a run's own INPUT directory and add a structured passive tracer trpb.
Usage: python3 make_tr_ic.py <SRC_INPUT_DIR> <DST_INPUT_DIR>      (DST files must not exist; SRC is only read)
trpb (kg/kg, on the IC's 128 input levels, k = 0 at the top) = 4e-4 * [1 + 0.25 tanh(lat/15) + 0.15 cos(lat) sin(2 lon)]
  * (1 - 0.3 exp(-k/20))  +  4e-4 * [plume 35N 115E + 0.8 plume 5S 60W, 8-degree Gaussians] * exp(-(127-k)/8):
an interhemispheric gradient, a wave-2, a stratospheric deficit and two boundary-layer plumes. external_ic remaps it
to the model levels like any tracer it finds in the file."""
import os
import shutil
import sys

import numpy as np
from netCDF4 import Dataset

src, dst = sys.argv[1], sys.argv[2]
for t in range(1, 7):
    s, d = os.path.realpath(f"{src}/gfs_data.tile{t}.nc"), f"{dst}/gfs_data.tile{t}.nc"
    if os.path.lexists(d):
        sys.exit(f"ABORT: {d} exists")
    shutil.copyfile(s, d)
    with Dataset(d, "a") as nc:
        if "trpb" in nc.variables:
            sys.exit(f"ABORT: {d} already has trpb")
        lat = np.radians(np.asarray(nc["geolat"][:], float))
        lon = np.radians(np.asarray(nc["geolon"][:], float))
        nk = nc.dimensions["lev"].size
        k = np.arange(nk, dtype=float)[:, None, None]
        h = 1.0 + 0.25 * np.tanh(np.degrees(lat) / 15.0) + 0.15 * np.cos(lat) * np.sin(2.0 * lon)

        def plume(la, lo, w=8.0):
            dlon = (np.degrees(lon) - lo + 180.0) % 360.0 - 180.0
            return np.exp(-((np.degrees(lat) - la) ** 2 + (dlon * np.cos(lat)) ** 2) / (2.0 * w * w))

        p = plume(35.0, 115.0) + 0.8 * plume(-5.0, 300.0)
        q = 4e-4 * h[None] * (1.0 - 0.3 * np.exp(-k / 20.0)) + 4e-4 * p[None] * np.exp(-((nk - 1) - k) / 8.0)
        v = nc.createVariable("trpb", "f4", ("lev", "lat", "lon"))
        v.long_name = "passive tracer b (synthetic)"
        v.units = "kg/kg"
        v[:] = q.astype(np.float32)
    print(f"{d}: trpb {q.min():.3e} .. {q.max():.3e}")
