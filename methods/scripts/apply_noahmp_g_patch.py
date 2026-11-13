#!/usr/bin/env python3
"""Fix G: initialise Noah-MP's snow layers from the land snow (weasdl, snodl), not the cell-mean composite (weasd,
snowd), in GFS_phys_time_vary_init (v1 snapshot and ufs/dev layouts).
Usage: python3 apply_noahmp_g_patch.py <dir containing physics/Interstitials/UFS_SCM_NEPTUNE>
With frac_grid the cold start derives weasdl = weasd/(landfrac + fice*(1-landfrac)) (fv3atm_sfc_io), and noahmpdrv is
given weasdl, but the layers were built from weasd. Noah-MP rebuilds its snow total from the layers on its first step,
so coastal (and glacier) land lost weasdl - weasd: -0.29 kg/m2 as a global mean in our C96 case.
Inside the Noah-MP block only, weasd(ix) -> weasdl(ix) and snowd(ix) -> snodl(ix); every edit must match as expected."""
import sys
from pathlib import Path

base = Path(sys.argv[1]) / "physics/Interstitials/UFS_SCM_NEPTUNE"
f90, meta = base / "GFS_phys_time_vary.fv3.F90", base / "GFS_phys_time_vary.fv3.meta"
s, m = f90.read_text(), meta.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


s = one(s, "fice, landfrac, vtype, weasd, lsoil,", "fice, landfrac, vtype, weasd, weasdl, snodl, lsoil,")
s = one(s, "         real(kind_phys),      intent(inout) :: weasd(:)\n",
        "         real(kind_phys),      intent(inout) :: weasd(:)\n"
        "         real(kind_phys),      intent(inout) :: weasdl(:), snodl(:)\n")
s = one(s, "shared(fwetxy,sneqvoxy,weasd,alboldxy,qsnowxy,wslakexy)",
        "shared(fwetxy,sneqvoxy,weasd,weasdl,snodl,alboldxy,qsnowxy,wslakexy)")
a = s.index("shared(snowd,canicexy,canliqxy,canopy,eahxy,cmxy,chxy)")
b = s.index("snicexy(ix,is) = one * dzsno(is) * weasd(ix)/snd", a) + len("snicexy(ix,is) = one * dzsno(is) * weasd(ix)/snd")
blk = s[a:b]
nw, ns = blk.count("weasd(ix)"), blk.count("snowd(ix)")
if nw < 4 or ns != 2:
    sys.exit(f"ABORT: unexpected Noah-MP block ({nw} weasd(ix), {ns} snowd(ix))")
blk = blk.replace("weasd(ix)", "weasdl(ix)").replace("snowd(ix)", "snodl(ix)")
s = s[:a] + blk + s[b:]

ENT = ("[weasd]\n  standard_name = lwe_thickness_of_surface_snow_amount\n  long_name = water equiv of acc snow depth over land "
       "and sea ice\n  units = mm\n  dimensions = (horizontal_dimension)\n  type = real\n  kind = kind_phys\n  intent = inout\n")
i = m.index("[ccpp-arg-table]\n  name = GFS_phys_time_vary_init\n")
j = m.index(ENT, i)
m = m[:j + len(ENT)] + (
    "[weasdl]\n  standard_name = water_equivalent_accumulated_snow_depth_over_land\n"
    "  long_name = water equiv of acc snow depth over land\n  units = mm\n  dimensions = (horizontal_dimension)\n"
    "  type = real\n  kind = kind_phys\n  intent = inout\n"
    "[snodl]\n  standard_name = surface_snow_thickness_water_equivalent_over_land\n"
    "  long_name = water equivalent snow depth over land\n  units = mm\n  dimensions = (horizontal_dimension)\n"
    "  type = real\n  kind = kind_phys\n  intent = inout\n") + m[j + len(ENT):]
f90.write_text(s)
meta.write_text(m)
print(f"patched {f90.name} ({nw} weasd, {ns} snowd in the Noah-MP block) and {meta.name} (G)")
