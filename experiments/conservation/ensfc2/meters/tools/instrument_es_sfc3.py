#!/usr/bin/env python3
"""Surface energy meters, third layer (apply after instrument_es_sfc.py, instrument_es_sfc2.py, es_static.py,
es_icefix.py):
  - sea ice: heat content change of snow-ice formation (flooding) in ice3lay -> esb(83)
  - Noah-MP glacier segments -> esgl(4:12) -> esb(26:34): dH energy, ssoil, surface residual, dH water,
    qsnow mass, runsrf mass, runsub mass, dH end truncation, start heat content
Usage: instrument_es_sfc3.py <ufs-weather-model>"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def pre(path, anchor, text):
    sub(path, anchor, text + anchor)


def post(path, anchor, text):
    sub(path, anchor, anchor + text)


# sea ice flooding (snowd in m of snow here, stsice in K)
pre(ice, "          if (hice(i) < hdi) then\n            snowd(i) = snowd(i) + hice(i) - hdi\n",
    "          es_h = es_hice(hice(i), ds*snowd(i), stsice(i,1),\n"
    "     &                   stsice(i,2))\n")
post(ice, "            hice (i) = hice(i) + hsni\n          endif\n",
     "          esb(83,i) = esb(83,i) - es_h\n"
     "     &      + es_hice(hice(i), ds*snowd(i), stsice(i,1),\n"
     "     &                stsice(i,2))\n")

# glacier
sub(gla, "  real(kind=8), public, save :: esgl(3) = 0.d0\n",
    "  real(kind=8), public, save :: esgl(12) = 0.d0\n  real(kind=8), save :: es_hg = 0.d0\n")
pre(gla, "  subroutine noahmp_glacier (&\n",
    "  real(kind=8) function es_hgla(nsnow, nsoil, isnow, stc, dzsnso, snice, snliq, sneqv)\n"
    "    ! glacier heat content, J m-2: snow layers and glacier-ice layers (T - tfrz), -hfus per kg of snow ice\n"
    "    integer, intent(in) :: nsnow, nsoil, isnow\n"
    "    real(kind=kind_phys), intent(in) :: stc(-nsnow+1:nsoil), dzsnso(-nsnow+1:nsoil), snice(-nsnow+1:0), &\n"
    "                                        snliq(-nsnow+1:0), sneqv\n"
    "    real(kind=8) :: sv, lv, zmid\n"
    "    integer :: iz, iz2\n"
    "    es_hgla = 0.d0\n"
    "    do iz = isnow+1, 0\n"
    "       sv = min(1.d0, snice(iz)/(dzsnso(iz)*denice))\n"
    "       lv = min(1.d0 - sv, snliq(iz)/(dzsnso(iz)*denh2o))\n"
    "       es_hgla = es_hgla + (cice*sv + cwat*lv)*dzsnso(iz)*(stc(iz) - tfrz) - hfus*snice(iz)\n"
    "    enddo\n"
    "    if (isnow == 0) es_hgla = es_hgla - hfus*sneqv\n"
    "    do iz = 1, nsoil\n"
    "       zmid = 0.5d0*dzsnso(iz)\n"
    "       do iz2 = 1, iz-1\n          zmid = zmid + dzsnso(iz2)\n       enddo\n"
    "       es_hgla = es_hgla + 1.d6*(0.8194d0 + 0.1309d0*zmid)*dzsnso(iz)*(stc(iz) - tfrz)\n"
    "    enddo\n"
    "  end function es_hgla\n")
GH = "es_hgla(nsnow, nsoil, isnow, stc, dzsnso, snice, snliq, sneqv)"
pre(gla, "    call energy_glacier (nsnow     ,nsoil   ,isnow   ,dt      ,qsnow   ,rhoair  , & !in\n",
    f"    es_hg = {GH}\n    esgl(12) = es_hg\n")
pre(gla, "    sice = max(0.0, smc - sh2o)",
    f"    esgl(4) = {GH} - es_hg\n"
    "    es_hg = es_hg + esgl(4)\n"
    "    esgl(5) = ssoil*dt\n"
    "    esgl(6) = (fsa - fira - fsh - fgev - ssoil)*dt\n")
pre(gla, "     esgl(1) = fgev*dt\n",
    f"     esgl(7) = {GH} - es_hg\n"
    "     es_hg = es_hg + esgl(7)\n"
    "     esgl(8) = qsnow*dt\n     esgl(9) = runsrf*dt\n     esgl(10) = runsub*dt\n")
pre(gla, "    if(swdown.ne.0.) then\n      albedo = fsr / swdown\n",
    f"    esgl(11) = {GH} - es_hg\n")
sub(drv, "        esb(23:25,i) = esgl(1:3)\n", "        esb(23:34,i) = esgl(1:12)\n")

for path, s in edits.items():
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
