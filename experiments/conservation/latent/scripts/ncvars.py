#!/usr/bin/env python3
"""ncvars.py <file> [substr]: list variables (name dtype shape) matching substr."""
import sys
from netCDF4 import Dataset
d = Dataset(sys.argv[1]); s = sys.argv[2] if len(sys.argv) > 2 else ''
for k, v in d.variables.items():
    if s in k:
        print(k, v.dtype, v.shape, getattr(v, 'units', ''))
