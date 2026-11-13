#!/usr/bin/env python3
"""Meter add-on (apply after instrument_tm.py): print tm_meter's tm_x(100) each step as 'TX step v(1:100)' (summed over ranks).
Usage: post_tx.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90"
s = f.read_text()
reps = [("tm_iud, tm_icnv, tm_dr, tm_drs, tm_dry_phys, tm_osc, tm_cflh\n",
         "tm_iud, tm_icnv, tm_dr, tm_drs, tm_dry_phys, tm_osc, tm_cflh, tm_x\n"),
        ("   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,7f10.0)') 'TH ', tm_step, tm_cflh\n   tm_cflh = 0.d0\n",
         "   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,7f10.0)') 'TH ', tm_step, tm_cflh\n   tm_cflh = 0.d0\n"
         "   call mpp_sum(tm_x, 100)\n"
         "   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,100es24.15e3)') 'TX ', tm_step, tm_x\n"
         "   tm_x = 0.d0\n")]
for a, b in reps:
    if s.count(a) != 1:
        sys.exit(f"ABORT {s.count(a)} {a[:60]!r}")
    s = s.replace(a, b)
f.write_text(s)
print("TX print", f)
