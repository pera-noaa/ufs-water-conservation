import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
s = p.read_text()
old1 = "  real(kind=8), allocatable, save :: esb(:,:)\n"
new1 = "  real(kind=8), save :: esb(esnb, 1024) = 0.d0\n"
old2 = ("    if (allocated(esb)) then\n       if (size(esb, 2) < im) deallocate(esb)\n    endif\n"
        "    if (.not. allocated(esb)) allocate(esb(esnb, max(im, 256)))\n")
new2 = "    if (im > size(esb, 2)) stop 'es_zero: block larger than esb'\n"
assert s.count(old1) == 1 and s.count(old2) == 1
p.write_text(s.replace(old1, new1).replace(old2, new2))
print("esb static in", p)
