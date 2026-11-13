import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/SeaIce/CICE/sfc_sice.f"
s = p.read_text()
rep = [("      real (kind=kind_phys) :: es_t0(im)\n", "      real (kind=kind_phys) :: es_t0(im), es_tr(im)\n"),
       ("          es_t0(i) = tice(i)\n",
        "          es_t0(i) = tice(i)\n"
        "!         ice3lay linearises hfi about tice reset to min(tice, tsf)\n"
        "          es_tr(i) = min(tice(i), t0c - 0.054d0)\n"
        "          if (snowd(i) > zero) es_tr(i) = min(tice(i), t0c)\n"),
       ("          tem = tice(i) - es_t0(i)\n", "          tem = tice(i) - es_tr(i)\n")]
for a, b in rep:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
p.write_text(s)
print("ice meter linearisation point fixed in", p)
