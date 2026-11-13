#!/usr/bin/env python3
"""apply_spraymeter2.py <ufs-weather-model> : INSTRUMENTATION (after apply_spraymeter.py). With lseaspray = .false., print
the same 'SPR' line for the same cells (lam > 1, lam of the spray the cell would have), fluxes 0, so spray-off runs give
the background 2dt-oscillation count. Print-only."""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Layer/UFS/sfc_nst.f90"
s = f.read_text()
a = "    do i=1,im\n       if(lseaspray .and. flag(i)) then\n"
if s.count(a) != 1:
    sys.exit("ABORT anchor")
b = """    do i=1,im
       if(.not. lseaspray .and. flag(i)) then
          f10m = fm10(i) / fm(i)
          ws10 = sqrt((f10m * u1(i))**2 + (f10m * v1(i))**2)
          ws10 = min(max(ws10,1.),ws10cr)
          tem = .015 * ws10 * ws10
          ru10 = 1. - .087 * log(10./tem)
          qss1 = fpvs(t1(i))
          qss1 = eps * qss1 / (prsl1(i) + epsm1 * qss1)
          bb1 = 1. / (1. + eps * hvap * hvap * qss1 / (rd * cp * t1(i) * t1(i)))
          m_ca = conlf * (ws10**5.4) * ru10 * bb1 * rho_a(i) * hvap
          m_cb = consf * (ws10**3.4) * ru10 * rho_a(i) * cp
          m_e = fpvs(t1(i) + 0.05_kp)
          m_dqs = eps * m_e / (prsl1(i) + epsm1 * m_e)
          m_e = fpvs(t1(i) - 0.05_kp)
          m_dqs = (m_dqs - eps * m_e / (prsl1(i) + epsm1 * m_e)) * 10._kp
          m_at = timestep * con_g / (cp * (prsi(i,1) - prsi(i,2)))
          m_aq = timestep * con_g / (hvap * (prsi(i,1) - prsi(i,2)))
          m_gt = m_at * (bets * m_cb + (alps - gams) * m_ca * m_dqs)
          m_gq = m_aq * alps * m_ca
          m_tr = m_gt + m_gq
          m_det = m_gt * m_gq - (m_at * (alps - gams) * m_ca) * (m_aq * alps * m_ca * m_dqs)
          m_lam = 0.5_kp * (m_tr + sqrt(max(m_tr * m_tr - 4._kp * m_det, 0._kp)))
          if (m_lam > 1._kp) write(*,'(a,i6,2f9.3,f7.2,f8.3,f9.3,es12.4,f9.3,es12.4,3es12.4)') 'SPR ', kdt, &
               xlon(i)*rad2deg, asin(sinlat(i))*rad2deg, ws10, m_lam, t1(i), q0(i), tskin(i), qss1, 0._kp, 0._kp, 0._kp
       endif
    enddo
"""
f.write_text(s.replace(a, b + a))
print("spray meter 2 applied")
