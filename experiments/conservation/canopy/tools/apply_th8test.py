#!/usr/bin/env python3
"""apply_th8test.py <ufs-weather-model> : TEST ONLY (not a deliverable). Environment CANOPY_TH8_OFF=1 restores the
pre-TH8 surface-precipitation threshold (energy 06 reverted) at run time, so TH8 on/off share one executable."""
import sys
from pathlib import Path

mod = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90"
s = mod.read_text()


def sub(old, new, count=1):
    global s
    if s.count(old) != count:
        sys.exit(f"ABORT anchor {s.count(old)}x: {old[:120]}")
    s = s.replace(old, new)


sub("   logical                      :: thompson_kirchhoff = .false.\n",
    "   logical                      :: thompson_kirchhoff = .false.\n"
    "   logical                      :: th8_test_off = .false.  ! TEST ONLY: env CANOPY_TH8_OFF=1\n")
for sp in "risg":
    sub(f"if (.true.) then  ! all mass leaving the lowest layer is precipitation (was r{sp}(kts) > R1*rr_min)",
        f"if (.not. th8_test_off .or. r{sp}(kts).gt.R1*rr_min) then  ! TEST hook on TH8")
mod.write_text(s)
if "--module-only" in sys.argv:
    sys.exit(print("TH8 test hook, module only"))
drv = mod.parent / "mp_thompson.F90"
d = drv.read_text()
a = "         thompson_kirchhoff = kirchhoff\n"
assert d.count(a) == 1
d = d.replace(a, a + "         block\n           character(len=8) :: ev\n           integer :: ln, st\n"
              "           call get_environment_variable('CANOPY_TH8_OFF', ev, ln, st)\n"
              "           th8_test_off = (st == 0 .and. ev(1:1) == '1')\n"
              "           if (th8_test_off .and. mpirank == mpiroot) print *, 'CANOPY TEST: TH8 OFF'\n"
              "         end block\n")
a = "lvap0, lfus, thompson_kirchhoff"
assert d.count(a) == 1
d = d.replace(a, a + ", th8_test_off")
drv.write_text(d)
print("TH8 test hook applied")
