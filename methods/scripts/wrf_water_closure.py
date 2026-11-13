#!/usr/bin/env python3
"""Domain water closure of a doubly periodic WRF ideal run with no surface fluxes: total water (vapour and all
hydrometeors, weighted by each layer's dry-air mass from the hybrid coordinate) plus accumulated grid-scale
precipitation must stay constant. Usage: python3 wrf_water_closure.py <wrfout file> [<wrfout file> ...]
RAINNC is all grid-scale precipitation (liquid equivalent). Prints, per output time, the change in W + RAINNC since
the first time, in kg/m2 and as a fraction of the precipitation since then."""
import sys
import numpy as np
from netCDF4 import Dataset

G = 9.81
SPECIES = ["QVAPOR", "QCLOUD", "QRAIN", "QICE", "QSNOW", "QGRAUP", "QHAIL"]
for path in sys.argv[1:]:
    nc = Dataset(path)
    nt = len(nc.dimensions["Time"])
    dnw = np.asarray(nc["DNW"][0], float)                    # negative
    c1h, c2h = np.asarray(nc["C1H"][0], float), np.asarray(nc["C2H"][0], float)
    rows = []
    for t in range(nt):
        mut = np.asarray(nc["MU"][t] + nc["MUB"][t], float)  # dry column mass (Pa) below p_top
        dm = (c1h[:, None, None]*mut[None] + c2h[:, None, None])*(-dnw[:, None, None])/G   # kg/m2 per layer
        q = sum(np.asarray(nc[s][t], float) for s in SPECIES if s in nc.variables)
        w = (q*dm).sum(axis=0).mean()
        p = np.asarray(nc["RAINNC"][t], float).mean()
        rows.append((float(nc["XTIME"][t]), w, p))
    w0, p0 = rows[0][1], rows[0][2]
    print(f"### {path}  species: {[s for s in SPECIES if s in nc.variables]}")
    print("  minutes      W (kg/m2)    P (kg/m2)   W+P-(W0+P0)   residual/P")
    for m, w, p in rows:
        r = (w + p) - (w0 + p0)
        print(f"  {m:7.1f}  {w:12.6f}  {p:10.6f}  {r:+.4e}  {r/(p-p0) if p > p0 else float('nan'):+.3e}")
