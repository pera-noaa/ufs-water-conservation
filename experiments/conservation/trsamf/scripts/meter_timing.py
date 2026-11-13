#!/usr/bin/env python3
"""METER (apply after fix_trsamf.py exp + meters): wall-clock of SAMF deep/shallow (normal exits) and of the
inserted tracer block, summed over calls and ranks, into tm_x: 51 deep routine, 52 deep tracer block, 53 shallow
routine, 54 shallow tracer block (seconds); 55/56 deep/shallow column-steps with the helper called, 57/58 sum of nsub.
Usage: meter_timing.py <tree>"""
import sys
from pathlib import Path
d = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF"
for name, hw, slot in (("samfdeepcnv.f", "hwrf_samfdeep", 0), ("samfshalcnv.f", "hwrf_samfshal", 2)):
    f = d / name
    s = f.read_text()
    use = "      use tm_meter, only : tm_x\n" if name == "samfshalcnv.f" else "      use tm_meter, only : tm_cfl_deep\n"
    reps = [
        ("      integer nsub\n", "      integer nsub\n      integer(8) tmc0, tmc1, tmc2, tmcr\n"),
        ("! tracers: transport in nsub sub-steps so that the donor-cell Courant\n",
         "      call system_clock(tmc1, tmcr)\n! tracers: transport in nsub sub-steps so that the donor-cell Courant\n"),
        (f"      if (.not.{hw}) then\n" + ("       indx = ntk - 2\n       do n = 1, ntr\n" if slot == 0 else "!\n      indx = ntk - 2\n      do n = 1, ntr\n"),
         "      call system_clock(tmc2)\n"
         f"      tm_x({52+slot}) = tm_x({52+slot}) + real(tmc2-tmc1,8)/real(tmcr,8)\n"
         + f"      if (.not.{hw}) then\n" + ("       indx = ntk - 2\n       do n = 1, ntr\n" if slot == 0 else "!\n      indx = ntk - 2\n      do n = 1, ntr\n")),
        ("            if (tranyd) then\n",
         f"            if (tranyd) tm_x({55+slot//2}) = tm_x({55+slot//2}) + 1.d0\n"
         f"            if (tranyd) tm_x({57+slot//2}) = tm_x({57+slot//2}) + nsub\n"
         "            if (tranyd) then\n"),
        ("      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n",
         "      call system_clock(tmc2)\n"
         f"      tm_x({51+slot}) = tm_x({51+slot}) + real(tmc2-tmc0,8)/real(tmcr,8)\n"
         "      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n"),
    ]
    if name == "samfshalcnv.f" and "use tm_meter, only : tm_x" not in s:
        reps.insert(0, ("      use funcphys , only : fpvs\n\n      implicit none\n",
                        "      use funcphys , only : fpvs\n      use tm_meter, only : tm_x\n\n      implicit none\n"))
    elif name == "samfdeepcnv.f":
        reps.insert(0, (use, use + "      use tm_meter, only : tm_x\n"))
    for a, b in reps:
        if s.count(a) != 1:
            sys.exit(f"ABORT {name} {s.count(a)} {a[:70]!r}")
        s = s.replace(a, b)
    # start clock at the first executable statement: right after 'dqtr  = 0._kind_phys'
    a = "      dqtr  = 0._kind_phys\n"
    if s.count(a) != 1:
        sys.exit(f"ABORT {name} start anchor {s.count(a)}")
    s = s.replace(a, a + "      call system_clock(tmc0, tmcr)\n")
    f.write_text(s)
    print("timing meter", f)
