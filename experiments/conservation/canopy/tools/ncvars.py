#!/usr/bin/env python3
"""ncvars.py <file> : variable names."""
import sys
from netCDF4 import Dataset
print(" ".join(Dataset(sys.argv[1]).variables))
