#!/usr/bin/env python3
"""Thompson layer meter (WBGCT): print each layer whose vapour the final clip raises, with per-species stage tendencies."""
# Usage: instrument_wb_gc_mp.py <module_mp_thompson.F90>  (after the M5 patch and the WBT meter; diagnostic only)
# A layer prints when qv1d+qvten*DT < 1e-10 after the R1 exchange (the MAX(1e-10) clip then creates water):
#   WBGCT  k T p rho*dz qv1d qvten*DT clip(kg/m2)
#   WBGCTS k m q1d a b c x   m=1..6 qv,qc,qi,qr,qs,qg; *DT mixing-ratio increments of: a process rates,
#          b condensation/evaporation block, c sedimentation + instant melt/freeze, x the R1-to-vapour exchange
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def sub(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {f.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)


TEN = "(/qvten(k),qcten(k),qiten(k),qrten(k),qsten(k),qgten(k)/)*DT"
sub("      REAL:: wb_x, wb_rho(kts:kte)\n",
    "      REAL:: wb_x, wb_rho(kts:kte)\n"
    "      REAL(KIND=8):: wbgc_t(6,3,kts:kte), wbgc_tx(6), wbgc_qx\n      INTEGER:: wbgc_m\n")
for tag, slot in (("wb_ta", 1), ("wb_tb", 2), ("wb_tc", 3)):
    old = (f"      {tag} = 0.0D0\n      do k = kts, kte\n"
           f"         {tag} = {tag} + (qvten(k)+qcten(k)+qiten(k)+qrten(k)+qsten(k)+qgten(k))*DT*wb_rho(k)*dzq(k)\n")
    sub(old, old + f"         wbgc_t(:,{slot},k) = {TEN}\n")
sub("!+---+-----------------------------------------------------------------+\n"
    "      do k = kts, kte\n         t1d(k)  = t1d(k) + tten(k)*DT\n",
    "      do k = kts, kte\n"
    "         wbgc_qx = qv1d(k) + qvten(k)*DT\n"
    "         if (wbgc_qx < 1.0D-10) then\n"
    f"            wbgc_tx = {TEN}\n"
    "            write(*,'(a,i4,6es13.5)') 'WBGCT  ', k, temp(k), p1d(k), wb_rho(k)*dzq(k), qv1d(k), &\n"
    "               qvten(k)*DT, (1.0D-10-wbgc_qx)*wb_rho(k)*dzq(k)\n"
    "            do wbgc_m = 1, 6\n"
    "               write(*,'(a,2i4,5es13.5)') 'WBGCTS ', k, wbgc_m, &\n"
    "                  (/qv1d(k),qc1d(k),qi1d(k),qr1d(k),qs1d(k),qg1d(k)/)*(wbgc_m==1) , wbgc_t(wbgc_m,1,k), &\n"
    "                  wbgc_t(wbgc_m,2,k)-wbgc_t(wbgc_m,1,k), wbgc_t(wbgc_m,3,k)-wbgc_t(wbgc_m,2,k), &\n"
    "                  wbgc_tx(wbgc_m)-wbgc_t(wbgc_m,3,k)\n"
    "            enddo\n"
    "         endif\n"
    "      enddo\n"
    "!+---+-----------------------------------------------------------------+\n"
    "      do k = kts, kte\n         t1d(k)  = t1d(k) + tten(k)*DT\n")
# q1d of species m (no array-valued expression in the item list)
s = s.replace("(/qv1d(k),qc1d(k),qi1d(k),qr1d(k),qs1d(k),qg1d(k)/)*(wbgc_m==1) ,",
              "merge(qv1d(k),merge(qc1d(k),merge(qi1d(k),merge(qr1d(k),merge(qs1d(k),qg1d(k), &\n"
              "                  wbgc_m==5),wbgc_m==4),wbgc_m==3),wbgc_m==2),wbgc_m==1),")
f.with_suffix(f.suffix + ".preWBGCT").write_text(f.read_text())
f.write_text(s)
print(f"instrumented {f}")
