#!/usr/bin/env python3
"""Host-frame water meter in the Thompson CCPP driver (diagnostic builds only; needs M4 applied, which passes prsi).
Usage: python3 instrument_wb_driver.py <ufs_model.fd>     (apply after apply_thompson_m_patches.py z and instrument_wb.py)
Per call and column, in the HOST's mass frame (layer mass = (prsi(k)-prsi(k+1))/g, species mass = q * layer mass):
  WBH  1 water out - water in + precipitation (kg/m2, summed over columns) | 2 precipitation | 3 columns
Printed by mp_thompson_finalize next to WBT. Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/MP/Thompson/mp_thompson.F90"
s = f.read_text()
Q = ("(spechum(ii,kk)+qc(ii,kk)+qr(ii,kk)+qi(ii,kk)+qs(ii,kk)+qg(ii,kk))"
     "*(prsi(ii,kk)-prsi(ii,kk+1))/con_g")
plan = [
    ("\nmodule mp_thompson\n", "\nmodule mp_thompson\n"),
    ("      implicit none\n\n      public :: mp_thompson_init", None),  # probed below, not required
    ("         real(kind_phys),           intent(in   ) :: prsi(:,:)\n",
     "         real(kind_phys),           intent(in   ) :: prsi(:,:)\n"
     "         real(kind=8) :: wbh_in(size(prsi,1)), wbh_out\n"
     "         integer :: ii, kk\n"),
    ("         ! DH* - do this only if istep == 1? Would be ok if it was\n",
     "         wbh_in = 0.0d0\n"
     "         do kk = 1, nlev\n"
     "            do ii = 1, ncol\n"
     f"               wbh_in(ii) = wbh_in(ii) + {Q}\n"
     "            enddo\n"
     "         enddo\n"
     "         ! DH* - do this only if istep == 1? Would be ok if it was\n"),
    ("         !> - Convert rainfall deltas from mm to m (on physics timestep); add to inout variables\n",
     "         do ii = 1, ncol\n"
     "            wbh_out = 0.0d0\n"
     "            do kk = 1, nlev\n"
     f"               wbh_out = wbh_out + {Q}\n"
     "            enddo\n"
     "            wbh(1) = wbh(1) + (wbh_out - wbh_in(ii)) + delta_rain_mp(ii)\n"
     "            wbh(2) = wbh(2) + delta_rain_mp(ii)\n"
     "            wbh(3) = wbh(3) + 1.0d0\n"
     "         enddo\n"
     "         !> - Convert rainfall deltas from mm to m (on physics timestep); add to inout variables\n"),
    ("         write(*,'(a,12es17.9)') 'WBT ', wbt\n",
     "         write(*,'(a,12es17.9)') 'WBT ', wbt\n"
     "         write(*,'(a,3es17.9)') 'WBH ', wbh\n"),
]
for old, new in plan:
    if new is None:
        continue
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)
# module-level accumulator, right after the module's own 'implicit none' (first one after 'module mp_thompson')
i = s.index("\nmodule mp_thompson\n")
j = s.index("implicit none\n", i) + len("implicit none\n")
s = s[:j] + "\n      real(kind=8), save :: wbh(3) = 0.0d0\n" + s[j:]
f.with_suffix(f.suffix + ".preWBH").write_text(f.read_text())
f.write_text(s)
print(f"instrumented {f}")
