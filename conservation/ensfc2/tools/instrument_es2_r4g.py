#!/usr/bin/env python3
"""Round 4g (debug): phasechange per-layer heat check. Before/after each layer's update, H_j = C_j (T_j - tfrz) - hfus*ice_j
(C_j = dt/(fact_j dz_j) before, the new-composition capacity after); prints 'EPC iloc j dH st0 st1 wice0 mice wliq0 mliq
supercool imelt hm heatr' when |dH| > 1e-3 J m-2. Usage: instrument_es2_r4g.py <tree>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = p.read_text()
PC = "  subroutine phasechange (parameters,nsnow   ,nsoil   ,isnow   ,dt      ,fact    , & !in\n"
i = s.index(PC); e = s.index("  end subroutine phasechange", i)
blk = s[i:e]
a_decl = "  real (kind=kind_phys)                            :: svn       !snow ice volume fraction at the new composition\n"
assert blk.count(a_decl) == 1
blk = blk.replace(a_decl, a_decl + "  real (kind=kind_phys) :: es_t0(-nsnow+1:nsoil), es_h0, es_h1, es_c1\n")
a0 = "    do j = isnow+1,nsoil       ! all layers\n         imelt(j)    = 0\n"
assert blk.count(a0) == 1
blk = blk.replace(a0, "    es_t0(isnow+1:nsoil) = stc(isnow+1:nsoil)\n" + a0)
a1 = "    do j = isnow+1,0             ! snow\n       snliq(j) = mliq(j)\n"
assert blk.count(a1) == 1
chk = ("    do j = isnow+1, nsoil\n"
       "       es_h0 = dt/(fact(j)*dzsnso(j))*dzsnso(j)*(es_t0(j)-tfrz) - hfus*wice0(j)\n"
       "       if (j <= 0) then\n"
       "          es_c1 = cice/denice*mice(j) + cwat/denh2o*mliq(j)\n"
       "       else\n"
       "          es_c1 = dt/fact(j) + (cwat*(mliq(j)-wliq0(j)) + cice*(mice(j)-wice0(j)))/1000.\n"
       "       endif\n"
       "       es_h1 = es_c1*(stc(j)-tfrz) - hfus*mice(j)\n"
       "       if (abs(es_h1-es_h0) > 1.e-3) write(*,'(a,2i5,12es14.6)') 'EPC ', iloc, j, es_h1-es_h0, es_t0(j), stc(j), &\n"
       "            wice0(j), mice(j), wliq0(j), mliq(j), supercool(j), real(imelt(j)), hm(j), xm(j), fact(j)\n"
       "    enddo\n")
blk = blk.replace(a1, chk + a1)
p.write_text(s[:i] + blk + s[e:])
print("instrumented", p.name)
