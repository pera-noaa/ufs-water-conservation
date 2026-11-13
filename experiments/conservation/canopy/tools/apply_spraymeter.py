#!/usr/bin/env python3
"""apply_spraymeter.py <ufs-weather-model> : INSTRUMENTATION (after apply_e1.py). In sfc_nst's spray loop, for open-water
cells whose explicit spray gain lam > 1 (largest eigenvalue of the spray-only lowest-layer Jacobian x dt; explicit is
unstable for lam > 2), print
 'SPR kdt lon lat ws10 lam t1 q1 tskin qss1 evaps_explicit evaps_used hflxs_used' (fluxes W m-2, before alps/bets).
Print-only: no model variable is written."""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Layer/UFS/sfc_nst.f90"
s = f.read_text()


def sub(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"ABORT anchor {s.count(old)}x: {old[:100]}")
    s = s.replace(old, new)


sub("    real (kind=kind_phys) :: windrel\n",
    "    real (kind=kind_phys) :: windrel\n"
    "    real (kind=kind_phys) :: m_ca, m_cb, m_dqs, m_at, m_aq, m_gt, m_gq, m_tr, m_det, m_lam, m_ex, m_e\n")
sub("          hflx(i) = hflx(i) + bets * hflxs - ptem * evaps\n",
    "          hflx(i) = hflx(i) + bets * hflxs - ptem * evaps\n"
    "          m_ca = conlf * (ws10**5.4) * ru10 * bb1 * rho_a(i) * hvap\n"
    "          m_cb = consf * (ws10**3.4) * ru10 * rho_a(i) * cp\n"
    "          m_e = fpvs(t1(i) + 0.05_kp)\n"
    "          m_dqs = eps * m_e / (prsl1(i) + epsm1 * m_e)\n"
    "          m_e = fpvs(t1(i) - 0.05_kp)\n"
    "          m_dqs = (m_dqs - eps * m_e / (prsl1(i) + epsm1 * m_e)) * 10._kp\n"
    "          m_at = timestep * con_g / (cp * (prsi(i,1) - prsi(i,2)))\n"
    "          m_aq = timestep * con_g / (hvap * (prsi(i,1) - prsi(i,2)))\n"
    "          m_gt = m_at * (bets * m_cb + (alps - gams) * m_ca * m_dqs)\n"
    "          m_gq = m_aq * alps * m_ca\n"
    "          m_tr = m_gt + m_gq\n"
    "          m_det = m_gt * m_gq - (m_at * (alps - gams) * m_ca) * (m_aq * alps * m_ca * m_dqs)\n"
    "          m_lam = 0.5_kp * (m_tr + sqrt(max(m_tr * m_tr - 4._kp * m_det, 0._kp)))\n"
    "          m_ex = m_ca * (qss1 - q0(i))\n"
    "          if (m_lam > 1._kp) write(*,'(a,i6,2f9.3,f7.2,f8.3,f9.3,es12.4,f9.3,es12.4,3es12.4)') 'SPR ', kdt, &\n"
    "               xlon(i)*rad2deg, asin(sinlat(i))*rad2deg, ws10, m_lam, t1(i), q0(i), tskin(i), qss1, m_ex, evaps, hflxs\n")
f.write_text(s)
print("spray meter applied")
