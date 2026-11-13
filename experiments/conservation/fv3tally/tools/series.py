#!/usr/bin/env python3
"""series.py <run out> : 3-hourly means (W m-2) of fixer, adiabatic remainder (DYN+TRC+damping KE), d_con, remap."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from etable import load
rows = load(sys.argv[1])
dt = 86400. / len(rows)
def g(r, b): return sum(r[(b-1)*4:(b-1)*4+4])
print(' hours   fixer    adiab    d_con    damp     remap')
for h0 in range(0, len(rows), len(rows)//8):
    blk = rows[h0:h0+len(rows)//8]
    f = sum(g(r, 8) for r in blk)/len(blk)/dt
    dmp = sum(sum(r[40:49]) for r in blk)/len(blk)/dt
    ad = sum(g(r, 3)+g(r, 6) for r in blk)/len(blk)/dt + dmp
    dc = sum(g(r, 4) for r in blk)/len(blk)/dt
    rm = sum(g(r, 7) for r in blk)/len(blk)/dt
    print(f'{h0*dt/3600:4.0f}-{(h0+len(blk))*dt/3600:<3.0f} {f:+.4f} {ad:+.4f} {dc:+.4f} {-dmp:+.4f} {rm:+.4f}')
