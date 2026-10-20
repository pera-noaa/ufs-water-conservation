#!/usr/bin/env python3
"""print reference full-level pressure (hPa) for dyn levels (top=1) and physics levels (surface=1). usage: pfull.py <atmf file> k..."""
import sys, netCDF4 as nc
p = nc.Dataset(sys.argv[1])['pfull'][:]
n = len(p)
for k in map(int, sys.argv[2:]):
    print(f'dyn k={k:3d}: {p[k-1]:7.1f} hPa   | phys k={k:3d} (dyn {n+1-k}): {p[n-k]:7.1f} hPa')
