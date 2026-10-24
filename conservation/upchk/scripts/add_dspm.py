#!/usr/bin/env python3
"""add_dspm.py <ufs-weather-model> : sa3dtke double-heating meters, on a copy of t403m (after instrument_upchk.py tm,hd).
PBL (satmedmfvdifq), per column, mass-weighted, into ucb slots 17-20 (UCM line, W m-2 after uc_table scaling):
  17 horizontal shear production as it enters prod: dku_h*def_2 (= 0.5 * 2*dku_h*def_2, the 0.5 of shrp)
  18 vertical shear production as it enters prod: 0.5*(dku(k-1)*def_1(k-1) + dku(k)*def_1(k)) (shr2 when sa3dtke off);
     k = 1: 0.5*dku(1)*def_1(1)
  19 dissipative heating dspfac*diss (zero if dspheat off)
  20 surface-stress production at k = 1: 0.5*stress*ustar*phims/(vk*zl(1))
Dycore (dyn_core), one 'UCD hn ha sdef sdiv' line per dyn_core call:
  hn = sum area*heat_source/g over k <= n_con (J, nominal: the KE d_sw converts to heat, after del2_cubed),
  ha = the same as applied (delt_max clip, non-hydrostatic branch, cv_air), sdef = sum area*delp*dku3d_h*deform_2,
  sdiv = sum area*delp*dku3d_h*(u_x+v_y)^2 (last end_step of the call; sdiv/sdef = divergent fraction of deform_2)."""
import re
import sys
from pathlib import Path

wm = Path(sys.argv[1]) / "UFSATM"
phys = wm / "ccpp/physics/physics"
I = phys / "Interstitials/UFS_SCM_NEPTUNE"


def edit(p, reps):
    t = p.read_text()
    for a, b in reps:
        assert t.count(a) == 1, (p.name, a)
        t = t.replace(a, b)
    p.write_text(t)


edit(I / "upchk_meter_common.F90", [
    ("ucnv = 16", "ucnv = 20"),
    ("  integer, save :: ucsk(ucnc) = 0\n", "  integer, save :: ucsk(ucnc) = 0, ucmoff = 0\n"),
    ("       uckdt(p) = kdt\n       ucoff(p) = 0\n", "       uckdt(p) = kdt\n       ucoff(p) = 0\n       if (p == 1) ucmoff = 0\n"),
    ("end module upchk_meter_common\n", """  subroutine uc_pz(im)
    integer, intent(in) :: im
    ucb(17:20, ucmoff+1:ucmoff+im) = 0.d0
  end subroutine uc_pz

  subroutine uc_pr(i, m, h, v, s)
    integer, intent(in) :: i
    real(kind=kind_phys), intent(in) :: m, h, v, s
    ucb(17, ucmoff+i) = ucb(17, ucmoff+i) + m*h
    ucb(18, ucmoff+i) = ucb(18, ucmoff+i) + m*v
    ucb(20, ucmoff+i) = ucb(20, ucmoff+i) + m*s
  end subroutine uc_pr

  subroutine uc_ds(im, km1, del, diss, f, grav)
    integer, intent(in) :: im, km1
    real(kind=kind_phys), intent(in) :: del(:,:), diss(:,:), f, grav
    integer :: i, k
    do i = 1, im
       do k = 1, km1
          ucb(19, ucmoff+i) = ucb(19, ucmoff+i) + del(i,k)/grav*f*diss(i,k)
       enddo
    enddo
    ucmoff = ucmoff + im
  end subroutine uc_ds
end module upchk_meter_common
""")])
edit(I / "uc_fin.F90", [
    ("write(*,'(a,i6,16es25.16)') 'UCM '", "write(*,'(a,i6,20es25.16)') 'UCM '"),
    ("       ucm = ucm + a*ucb(:, i)\n       ucb(:, i) = 0.d0\n", "       ucm = ucm + a*ucb(:, j0+i)\n       ucb(:, j0+i) = 0.d0\n")])

sat = phys / "PBL/SATMEDMF/satmedmfvdifq.F"
edit(sat, [
    ("      use machine  , only : kind_phys\n",
     "      use machine  , only : kind_phys\n      use upchk_meter_common, only : uc_pz, uc_pr, uc_ds\n"),
    ("      ntrac1 = ntrac - 1\n", "      ntrac1 = ntrac - 1\n      call uc_pz(im)\n"),
    ("            shrp = 0.5 * (tem1 + ptem1 + ptem2 + tem2)\n",
     "            shrp = 0.5 * (tem1 + ptem1 + ptem2 + tem2)\n"
     "            call uc_pr(i, del(i,1)/grav,\n"
     "     &        merge(dku_h(i,1)*def_2(i,1), 0._kind_phys, sa3dtke),\n"
     "     &        0.5*merge(dku(i,1)*def_1(i,1), dku(i,1)*shr2(i,1),\n"
     "     &        sa3dtke), 0.5*tem2)\n"),
    ("            tem  = 0.5 * (tem1 + tem2)\n            tem1 = (u1(i,k+1)-u1(i,k))*rdzt(i,k)\n",
     "            tem  = 0.5 * (tem1 + tem2)\n"
     "            call uc_pr(i, del(i,k)/grav,\n"
     "     &        merge(dku_h(i,k)*def_2(i,k), 0._kind_phys, sa3dtke),\n"
     "     &        tem - merge(dku_h(i,k)*def_2(i,k), 0._kind_phys,\n"
     "     &        sa3dtke), 0._kind_phys)\n"
     "            tem1 = (u1(i,k+1)-u1(i,k))*rdzt(i,k)\n"),
    ("!> ## Add TKE dissipative heating to temperature tendency\n!\n      if(dspheat) then\n",
     "!> ## Add TKE dissipative heating to temperature tendency\n!\n"
     "      call uc_ds(im, km1, del, diss,\n     &     merge(dspfac, 0._kind_phys, dspheat), grav)\n"
     "      if(dspheat) then\n")])
sm = phys / "PBL/SATMEDMF/satmedmfvdifq.meta"
t = sm.read_text()
m = re.search(r"^(\s*dependencies\s*=\s*)(.*)$", t, re.M)
assert m and "upchk" not in m.group(2)
sm.write_text(t[:m.start(2)] + "../../Interstitials/UFS_SCM_NEPTUNE/upchk_meter_common.F90," + t[m.start(2):])

dc = wm / "fv3/atmos_cubed_sphere/model/dyn_core.F90"
edit(dc, [
    ("  use fv_mp_mod,          only: is_master\n", "  use fv_mp_mod,          only: is_master, mp_reduce_sum\n"),
    ("  real, allocatable ::  rf(:)\n",
     "  real, allocatable ::  rf(:)\n"
     "  real, allocatable, save :: uc_d2(:,:,:)  ! upchk meter: (u_x+v_y)**2 from diff3d\n"
     "  real(kind=8), save :: uc_hn = 0.d0, uc_ha = 0.d0, uc_dt = 0.d0, uc_dl = 0.d0, uc_sdef = 0.d0, uc_sdiv = 0.d0\n"),
    ("       call diff3d(npx, npy, npz, nq, ua, va, w, tx, q,       &\n"
     "                  sa3dtke_var%deform_1, sa3dtke_var%deform_2, &\n"
     "                  sa3dtke_var%deform_3, sa3dtke_var%deform_4, &\n"
     "                  sa3dtke_var%dku3d_e, zh, gridstruct, bd)\n",
     "       if (.not. allocated(uc_d2)) allocate(uc_d2(isd:ied, jsd:jed, npz))\n"
     "       uc_d2 = 0.\n"
     "       call diff3d(npx, npy, npz, nq, ua, va, w, tx, q,       &\n"
     "                  sa3dtke_var%deform_1, sa3dtke_var%deform_2, &\n"
     "                  sa3dtke_var%deform_3, sa3dtke_var%deform_4, &\n"
     "                  sa3dtke_var%dku3d_e, zh, gridstruct, bd)\n"
     "       uc_sdef = 0.d0\n       uc_sdiv = 0.d0\n"
     "       do k=1,npz\n         do j=js,je\n           do i=is,ie\n"
     "             uc_sdef = uc_sdef + gridstruct%area(i,j)*delp(i,j,k)*sa3dtke_var%dku3d_h(i,j,k)*sa3dtke_var%deform_2(i,j,k)\n"
     "             uc_sdiv = uc_sdiv + gridstruct%area(i,j)*delp(i,j,k)*sa3dtke_var%dku3d_h(i,j,k)*uc_d2(i,j,k)\n"
     "           enddo\n         enddo\n       enddo\n"),
    ("!$OMP              dudx,dudy,dudz,dvdx,dvdy,dvdz,dwdx,dwdy,dwdz) &\n!$OMP              private(tmp,tmp1,tmp2)\n",
     "!$OMP              dudx,dudy,dudz,dvdx,dvdy,dvdz,dwdx,dwdy,dwdz,uc_d2) &\n!$OMP              private(tmp,tmp1,tmp2)\n"),
    ("               dwdx(i,j,k)**2+dwdy(i,j,k)**2+tmp\n",
     "               dwdx(i,j,k)**2+dwdy(i,j,k)**2+tmp\n             uc_d2(i,j,k) = (dudx(i,j,k)+dvdy(i,j,k))**2\n"),
    ("    endif\n\n  endif\n  if (allocated(heat_source)) deallocate( heat_source )",
     "    endif\n"
     "    uc_hn = 0.d0\n    uc_ha = 0.d0\n"
     "    do k=1,n_con\n       uc_dl = abs(bdt*flagstruct%delt_max)\n"
     "       if ( k == 1 ) uc_dl = 0.1*uc_dl\n       if ( k == 2 ) uc_dl = 0.5*uc_dl\n"
     "       do j=js,je\n          do i=is,ie\n"
     "             uc_hn = uc_hn + gridstruct%area(i,j)*heat_source(i,j,k)/grav\n"
     "             uc_dt = heat_source(i,j,k)/(cv_air*delp(i,j,k))\n"
     "             uc_ha = uc_ha + gridstruct%area(i,j)*cv_air*delp(i,j,k)*sign(min(uc_dl,abs(uc_dt)),uc_dt)/grav\n"
     "          enddo\n       enddo\n    enddo\n"
     "    call mp_reduce_sum(uc_hn)\n    call mp_reduce_sum(uc_ha)\n"
     "    call mp_reduce_sum(uc_sdef)\n    call mp_reduce_sum(uc_sdiv)\n"
     "    if (is_master()) write(*,'(a,4es25.16)') 'UCD ', uc_hn, uc_ha, uc_sdef, uc_sdiv\n"
     "    uc_sdef = 0.d0\n    uc_sdiv = 0.d0\n"
     "\n  endif\n  if (allocated(heat_source)) deallocate( heat_source )")])
print("dspm meters added")
