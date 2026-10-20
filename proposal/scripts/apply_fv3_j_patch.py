#!/usr/bin/env python3
"""Fix J: the FV3 driver builds the physics' layer pressure prsl = dm*rTv/dphi with the physics' gas constants
(con_rd, con_fvirt) instead of the dycore's rdgas and zvir (v1 driver/fvGFS and upstream driver/UFS layouts).
Usage: python3 apply_fv3_j_patch.py <atmos_cubed_sphere dir>
The boundary layer and Noah-MP turn prsl back into density with con_rd = 287.05 (double); in a 32-bit build rdgas is
single precision (287.04998779), so the water they book for surface evaporation, and Noah-MP debits, was 4.25e-8 less
than the water the boundary layer adds (measured +4.11e-8 of E). With matching constants the gap is 1.6e-16."""
import re
import sys
from pathlib import Path

base = Path(sys.argv[1]) / "driver"
cands = [p for p in (base / "UFS/atmosphere.F90", base / "fvGFS/atmosphere.F90") if p.exists()]
if len(cands) != 1:
    sys.exit(f"ABORT: expected one driver atmosphere.F90, found {cands}")
f = cands[0]
s = f.read_text()
use = "use constants_mod,          only: cp_air, rdgas, grav, rvgas, kappa, pstd_mks\n"
if s.count(use) != 1:
    sys.exit("ABORT: constants_mod use line")
# upstream picks constantsR4_mod or constants_mod under #ifdef OVERLOAD_R4: import after the #endif, for both
anchor = use + "#endif\n" if s.count(use + "#endif\n") == 1 else use
s = s.replace(anchor, anchor + "use physcons,               only: con_rd, con_fvirt\n")
pat = re.compile(r"\n( *)rTv = rdgas\*(IPD_(?:Data\(nb\)%)?Statein%tgrs\((?:i|im),k\))\*\(1\.\+zvir\*qgrs_rad\)\n")
m = pat.findall(s)
if len(m) != 1:
    sys.exit(f"ABORT: expected one rTv line, found {len(m)}")
s = pat.sub(lambda m: f"\n{m.group(1)}! the physics' constants: it turns prsl back into density with con_rd\n"
                      f"{m.group(1)}rTv = con_rd*{m.group(2)}*(1.+con_fvirt*qgrs_rad)\n", s)
f.write_text(s)
print(f"patched {f.relative_to(base.parent)} (J: rTv with con_rd, con_fvirt)")
