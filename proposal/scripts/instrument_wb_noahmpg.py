#!/usr/bin/env python3
"""Meter the land-atmosphere latent-energy mismatch in Noah-MP (diagnostic builds only; apply after
instrument_wb_noahmpx.py, which adds the WBE finalize print). Usage: python3 instrument_wb_noahmpg.py <ufs_model.fd>
Soil points, steps > 1, after Noah-MP's error check, in W/m2 per column (summed unweighted, times dt):
  the land pays latent energy fcev + fctr + fgev; the water it hands the atmosphere is ecan + etran + edir (fix D), which
  carries the host's latent heat: con_hvap = 2.5e6 from liquid, con_hvap + con_hfus = 2.83358e6 from ice.
  g_lim = (fcev + fctr + fgev) - (ecan + etran)*L_c - edir*latheag     (Noah-MP's own constants: capped water fluxes)
  g_k   = (ecan + etran)*(L_c - Lhost_c) + edir*(latheag - Lhost_g)    (Noah-MP's constants vs the host's)
  L_c = hsub if frozen_canopy else hvap (as in canwater); latheag as in energy.
WBG | 1 column-steps | 2 sum g_lim*dt | 3 sum g_k*dt | 4 sum |g_lim|*dt | 5 sum (fcev+fctr+fgev)*dt | 6 sum |g_k|*dt (J/m2)"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
mpt = root / "MP/Thompson/mp_thompson.F90"
s, m = lsm.read_text(), mpt.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


i = s.index("  real(kind=8), public, save :: wbe(16) = 0.d0")
j = s.index("\n", i) + 1
s = s[:j] + "  real(kind=8), public, save :: wbg(6) = 0.d0\n  real(kind=8), save :: wbg_lc, wbg_hc, wbg_hg, wbg_l, wbg_k\n" + s[j:]
s = one(s, "\n! urban - jref\n    qfx = etran + ecan + edir\n",
        "\n     if (ist == 1 .and. itime > 1) then\n"
        "       wbg_lc = hvap\n       if (frozen_canopy) wbg_lc = hsub\n"
        "       wbg_hc = 2.5d6\n       if (frozen_canopy) wbg_hc = 2.5d6 + 3.3358d5\n"
        "       wbg_hg = 2.5d6\n       if (latheag > 0.5d0*(hvap + hsub)) wbg_hg = 2.5d6 + 3.3358d5\n"
        "       wbg_l = (fcev + fctr + fgev) - (ecan + etran)*wbg_lc - edir*latheag\n"
        "       wbg_k = (ecan + etran)*(wbg_lc - wbg_hc) + edir*(latheag - wbg_hg)\n"
        "       wbg(1) = wbg(1) + 1.d0\n       wbg(2) = wbg(2) + wbg_l*dt\n       wbg(3) = wbg(3) + wbg_k*dt\n"
        "       wbg(4) = wbg(4) + abs(wbg_l)*dt\n       wbg(5) = wbg(5) + (fcev + fctr + fgev)*dt\n"
        "       wbg(6) = wbg(6) + abs(wbg_k)*dt\n"
        "     endif\n"
        "\n! urban - jref\n    qfx = etran + ecan + edir\n")
m = one(m, "         write(*,'(a,16es24.15)') 'WBE ', wbe\n",
        "         write(*,'(a,16es24.15)') 'WBE ', wbe\n         write(*,'(a,6es24.15)') 'WBG ', wbg\n")
k = m.index("         use module_sf_noahmplsm, only: wbe")
m = m[:k] + "         use module_sf_noahmplsm, only: wbg\n" + m[k:]
for p, t in ((lsm, s), (mpt, m)):
    p.with_suffix(p.suffix + ".preWBG").write_text(p.read_text())
    p.write_text(t)
    print(f"instrumented {p.relative_to(root)}")
