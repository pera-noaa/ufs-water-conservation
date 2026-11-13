#!/usr/bin/env python3
"""Water meters for MYNN-EDMF and GFDL MP v3 (diagnostic builds only), optionally with the two proposed fixes.
Usage: python3 instrument_suites.py <ufs-weather-model dir> meter|fix|meterfix|fix2|meterfix2
  fix/meterfix: MYNN surface-density fix (A) + GFDL MP v3 back-conversion fix; fix2/meterfix2: also the MYNN dew-limiter fix (B)
Every anchor must match exactly once, else nothing is written.

WBM (mynnedmf_wrapper, cumulative per rank, printed after the rank's last block of each step), kg:
  1 sum dW_host*a   MYNN's qv+qc+qi tendencies x delt x (prsi(k)-prsi(k+1))/g      (what the host applies)
  2 sum qfx*dt*a    qfx = qflx*rho1, the flux reported as dqsfc1/XLV (the budget's E)
  3 sum S*a         surface source as solved in mynn_tendencies: delt*rhosfc*qvflux
  4 sum F*a         delt*rho(kts)*flqv (= qfx*delt, the scheme's own copy)
  5 sum dW_mynn*a   tendencies x delt x rho(k)*dz(k), before moisture_check
  6 sum dW_mynn*a   same, after moisture_check
  7 sum qflx*rho_h*dt*a  rho_h = prsl1/(rd*t3d*(1+p608*qv)) from the unadjusted host state
  8 sum a
WBG (gfdl_cloud_microphys_v3_run, same timing), kg:
  1 sum dW_host*a   sum_k (q_new-q_old)*del/g over the six species (what the host applies)
  2 sum dW_mp*a     sum_k (q_new*delp_new - q_old*del)/g, delp_new as returned by mpdrv (the scheme's frame)
  3 sum P_raw*a     (rain+ice+snow+graupel+water) before the rainmin zeroing, kg/m2
  4 sum P*a         prcp0*1000 (what the host books)
  5 sum water*a     settled cloud water (not in prcp0)
  6 sum a
"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
mode = sys.argv[2]
assert mode in ("meter", "fix", "meterfix", "fix2", "meterfix2")
METER, FIX, FIX2 = "meter" in mode, "fix" in mode, mode.endswith("fix2")
mynn = root / "PBL/MYNN_EDMF/module_bl_mynn.F90"
wrap = root / "PBL/MYNN_EDMF/mynnedmf_wrapper.F90"
wmeta = wrap.with_suffix(".meta")
gmod = root / "MP/GFDL/v3_2022/gfdl_cloud_microphys_v3_mod.F90"
gwrap = root / "MP/GFDL/v3_2022/gfdl_cloud_microphys_v3.F90"
gmeta = gwrap.with_suffix(".meta")
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def ent(local, std, longn, units, dims, typ, kind=True):
    return (f"[{local}]\n  standard_name = {std}\n  long_name = {longn}\n  units = {units}\n  dimensions = {dims}\n"
            f"  type = {typ}\n" + ("  kind = kind_phys\n" if kind else "") + "  intent = in\n")


GAREA = ent("garea", "cell_area", "area of the grid cell", "m2", "(horizontal_loop_extent)", "real")
KDT = ent("kdt", "index_of_timestep", "current number of time steps", "index", "()", "integer", False)

if FIX:
    # MYNN: the surface source is rho1*flqv = qfx, not rhosfc*flqv (rhosfc/rho1 = psfc*Tv1/(prsl1*(T1+p608*q1)))
    sub(mynn, "    d(k)=sqv(k)  + dtz(k)*rhosfc*qvflux*rhoinv(k) + qcd(k)*delt &\n",
        "    d(k)=sqv(k)  + dtz(k)*rho(kts)*qvflux*rhoinv(k) + qcd(k)*delt &\n")
    sub(mynn, "    d(k)=sqw(k)  + dtz(k)*rhosfc*flq*rhoinv(k) + qcd(k)*delt",
        "    d(k)=sqw(k)  + dtz(k)*rho(kts)*flq*rhoinv(k) + qcd(k)*delt")
    sub(mynn, "    d(k)=sqc(k)  + dtz(k)*rhosfc*flqc*rhoinv(k) + qcd(k)*delt &\n",
        "    d(k)=sqc(k)  + dtz(k)*rho(kts)*flqc*rhoinv(k) + qcd(k)*delt &\n")
    if FIX2:
        # MYNN: min(0.9*sqv-1e-8, 0) is 0 whenever sqv > 1.1e-8, so every downward (dew) flux was zeroed; bound it instead
        sub(mynn, "       qvflux = max(qvflux, (min(0.9*sqv(kts) - 1e-8, 0.0)/dtz(kts)))\n",
            "       qvflux = max(qvflux, -max(0.9*sqv(kts) - 1e-8, 0.0)/dtz(kts))\n")
    # GFDL MP v3: back to specific ratios with the input humidity, so the host's rebuild (input delp x q) is exact
    sub(gmod, "            else\n                con_r8 = one_r8 + qvz (k)\n            endif\n\n            delp (i, k) = dp (k) * con_r8\n",
        "            else\n                con_r8 = one_r8 / (one_r8 - qv (i, k))\n            endif\n\n            delp (i, k) = dp (k) * con_r8\n")

if METER:
    # ---------------- MYNN core: per-column terms into wbm_t, copied to wbm_col(i,:) by the driver
    sub(mynn, "  logical, parameter :: env_subs = .false.\n",
        "  logical, parameter :: env_subs = .false.\n"
        "  real(kind_phys) :: wbm_t(4) = 0.\n"
        "  real(kind_phys), allocatable :: wbm_col(:,:)\n")
    sub(mynn, "    rhosfc     = psfc/(R_d*(tk(kts)+p608*qv(kts)))\n",
        "    rhosfc     = psfc/(R_d*(tk(kts)+p608*qv(kts)))\n    wbm_t = 0.\n")
    sub(mynn, "!rho-weighted:  rhosfc*X*rhoinv(k)\n",
        "!rho-weighted:  rhosfc*X*rhoinv(k)\n"
        + ("    wbm_t(1) = delt*rho(kts)*qvflux\n" if FIX else "    wbm_t(1) = delt*rhosfc*qvflux\n")
        + "    wbm_t(4) = delt*rho(kts)*flqv\n")
    sub(mynn, "    !ensure non-negative moist species\n    CALL moisture_check(kte, delt, delp, exner,        &\n"
              "                        sqv2, sqc2, sqi2, sqs2, thl,   &\n"
              "                        dqv, dqc, dqi, dqs, dth        )\n",
        "    wbm_t(2) = 0.\n    DO k=kts,kte\n"
        "       wbm_t(2) = wbm_t(2) + (Dqv(k)+Dqc(k)+Dqi(k)+Dqs(k))*delt*rho(k)*dz(k)\n    ENDDO\n"
        "    !ensure non-negative moist species\n    CALL moisture_check(kte, delt, delp, exner,        &\n"
        "                        sqv2, sqc2, sqi2, sqs2, thl,   &\n"
        "                        dqv, dqc, dqi, dqs, dth        )\n"
        "    wbm_t(3) = 0.\n    DO k=kts,kte\n"
        "       wbm_t(3) = wbm_t(3) + (Dqv(k)+Dqc(k)+Dqi(k)+Dqs(k))*delt*rho(k)*dz(k)\n    ENDDO\n")
    sub(mynn, "       rqvblten(i,kts:kte)=dqv1(kts:kte)\n",
        "       rqvblten(i,kts:kte)=dqv1(kts:kte)\n       if (allocated(wbm_col)) wbm_col(i,1:4) = wbm_t(1:4)\n")
    # ---------------- MYNN wrapper: host-weighted sums
    sub(wrap, "     &  lprnt, huge, errmsg, errflg                        )\n",
        "     &  lprnt, huge, garea, kdt, errmsg, errflg            )\n")
    sub(wrap, "     use module_bl_mynn, only: mynn_bl_driver\n",
        "     use module_bl_mynn, only: mynn_bl_driver, wbm_col\n")
    sub(wrap, "      real(kind_phys), dimension(levs) :: kzero\n",
        "      real(kind_phys), dimension(levs) :: kzero\n"
        "      real(kind_phys), intent(in) :: garea(:)\n"
        "      integer, intent(in) :: kdt\n"
        "      real(kind=8), save :: wbm(8) = 0.0d0\n"
        "      integer, save :: wbm_kdt = -1, wbm_n = 0, wbm_nrank = -1\n"
        "      real(kind=8) :: wbm_h\n")
    sub(wrap, "      errflg = 0\n      \n      dtdt = 0.0\n",
        "      errflg = 0\n      \n"
        "      if (kdt /= wbm_kdt) then\n"
        "         if (wbm_nrank < 0 .and. wbm_kdt >= 0) then\n"
        "            wbm_nrank = wbm_n\n"
        "            write(*,'(a,i7,8es24.15)') 'WBM ', wbm_kdt, wbm\n"
        "         endif\n"
        "         wbm_kdt = kdt\n"
        "         wbm_n = 0\n"
        "      endif\n"
        "      if (allocated(wbm_col)) deallocate(wbm_col)\n"
        "      allocate(wbm_col(im,4))\n"
        "      wbm_col = 0.\n"
        "      dtdt = 0.0\n")
    sub(wrap, "       if(allocated(save_qke_adv)) then\n",
        "       do i=1,im\n"
        "          wbm_h = 0.0d0\n"
        "          do k=1,levs\n"
        "             wbm_h = wbm_h + (RQVBLTEN(i,k)+RQCBLTEN(i,k)+RQIBLTEN(i,k))*delp(i,k)\n"
        "          enddo\n"
        "          wbm(1) = wbm(1) + wbm_h*delt/grav*garea(i)\n"
        "          wbm(2) = wbm(2) + qfx(i)*delt*garea(i)\n"
        "          wbm(3) = wbm(3) + wbm_col(i,1)*garea(i)\n"
        "          wbm(4) = wbm(4) + wbm_col(i,4)*garea(i)\n"
        "          wbm(5) = wbm(5) + wbm_col(i,2)*garea(i)\n"
        "          wbm(6) = wbm(6) + wbm_col(i,3)*garea(i)\n"
        "          wbm(7) = wbm(7) + qflx(i)*prsl(i,1)/(r_d*t3d(i,1)*(1.+p608*qgrs_water_vapor(i,1)))*delt*garea(i)\n"
        "          wbm(8) = wbm(8) + garea(i)\n"
        "       enddo\n"
        "       wbm_n = wbm_n + im\n"
        "       if (wbm_n == wbm_nrank) write(*,'(a,i7,8es24.15)') 'WBM ', kdt, wbm\n\n"
        "       if(allocated(save_qke_adv)) then\n")
    HUGE = ("[huge]\n  standard_name = netcdf_float_fillvalue\n  long_name = definition of NetCDF float FillValue\n"
            "  units = none\n  dimensions = ()\n  type = real\n  kind = kind_phys\n  intent = in\n")
    sub(wmeta, HUGE, HUGE + GAREA + KDT)
    # ---------------- GFDL MP v3 wrapper
    sub(gwrap, "      ten_v, ten_qv, ten_ql, ten_qr, ten_qi, ten_qs, ten_qg, ten_cldfrc, ten_q,    &\n      errmsg, errflg)\n",
        "      ten_v, ten_qv, ten_ql, ten_qr, ten_qi, ten_qs, ten_qg, ten_cldfrc, ten_q,    &\n      kdt, errmsg, errflg)\n")
    sub(gwrap, "      real(kind=kind_phys), dimension(:,:), allocatable :: new_qv, new_ql, new_qi, new_qr, new_qs, new_qg, new_qa, new_t\n",
        "      real(kind=kind_phys), dimension(:,:), allocatable :: new_qv, new_ql, new_qi, new_qr, new_qs, new_qg, new_qa, new_t\n"
        "      integer, intent(in) :: kdt\n"
        "      real(kind=8), save :: wbg(6) = 0.0d0\n"
        "      integer, save :: wbg_kdt = -1, wbg_n = 0, wbg_nrank = -1\n"
        "      real(kind=8) :: wbg_h, wbg_m, wbg_pr\n")
    sub(gwrap, "      ! Initialize CCPP error handling variables\n      errmsg = ''\n      errflg = 0\n      \n      ten_t = 0.0\n",
        "      ! Initialize CCPP error handling variables\n      errmsg = ''\n      errflg = 0\n      \n"
        "      if (kdt /= wbg_kdt) then\n"
        "         if (wbg_nrank < 0 .and. wbg_kdt >= 0) then\n"
        "            wbg_nrank = wbg_n\n"
        "            write(*,'(a,i7,6es24.15)') 'WBG ', wbg_kdt, wbg\n"
        "         endif\n"
        "         wbg_kdt = kdt\n"
        "         wbg_n = 0\n"
        "      endif\n"
        "      ten_t = 0.0\n")
    sub(gwrap, "      tem   = dtp*con_p001/con_secinday\n",
        "      tem   = dtp*con_p001/con_secinday\n"
        "      do i = 1, im\n"
        "         wbg_h = 0.0d0\n"
        "         wbg_m = 0.0d0\n"
        "         do k = 1, levs\n"
        "            kk = levs-k+1\n"
        "            wbg_h = wbg_h + ((qv1(i,kk)+ql1(i,kk)+qr1(i,kk)+qi1(i,kk)+qs1(i,kk)+qg1(i,kk)) &\n"
        "                 - (gq0(i,k)+gq0_ntcw(i,k)+gq0_ntrw(i,k)+gq0_ntiw(i,k)+gq0_ntsw(i,k)+gq0_ntgl(i,k)))*del(i,k)\n"
        "            wbg_m = wbg_m + (qv1(i,kk)+ql1(i,kk)+qr1(i,kk)+qi1(i,kk)+qs1(i,kk)+qg1(i,kk))*delp(i,kk) &\n"
        "                 - (gq0(i,k)+gq0_ntcw(i,k)+gq0_ntrw(i,k)+gq0_ntiw(i,k)+gq0_ntsw(i,k)+gq0_ntgl(i,k))*del(i,k)\n"
        "         enddo\n"
        "         wbg_pr = (rain0(i)+ice0(i)+snow0(i)+graupel0(i)+water0(i))*tem*1000.0d0\n"
        "         wbg(1) = wbg(1) + wbg_h/con_g*garea(i)\n"
        "         wbg(2) = wbg(2) + wbg_m/con_g*garea(i)\n"
        "         wbg(3) = wbg(3) + wbg_pr*garea(i)\n"
        "         wbg(5) = wbg(5) + water0(i)*tem*1000.0d0*garea(i)\n"
        "         wbg(6) = wbg(6) + garea(i)\n"
        "      enddo\n")
    sub(gwrap, "      ! convert rain0, ice0, snow0, graupel0 from mm per day to m per physics timestep\n",
        "      do i = 1, im\n"
        "         wbg(4) = wbg(4) + prcp0(i)*1000.0d0*garea(i)\n"
        "      enddo\n"
        "      wbg_n = wbg_n + im\n"
        "      if (wbg_n == wbg_nrank) write(*,'(a,i7,6es24.15)') 'WBG ', kdt, wbg\n\n"
        "      ! convert rain0, ice0, snow0, graupel0 from mm per day to m per physics timestep\n")
    TENQ = "  dimensions = (horizontal_loop_extent,vertical_layer_dimension,number_of_tracers)\n  type = real\n  kind = kind_phys\n  intent = out\n[errmsg]\n"
    sub(gmeta, TENQ, TENQ.replace("[errmsg]\n", KDT + "[errmsg]\n"))

for path, s in edits.items():
    bak = path.with_suffix(path.suffix + ".preWB")
    if not bak.exists():
        bak.write_text(path.read_text())
    path.write_text(s)
    print(f"{mode}: {path.relative_to(root)}")
