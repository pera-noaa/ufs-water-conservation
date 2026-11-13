#!/usr/bin/env python3
"""add_pblw.py <ufs-weather-model> : (after instrument_upchk.py ... mlm) whole-satmedmfvdifq water meter.
UCM slots 17-20: 17 sum m*sum_{vdiff 1..6} (rtg_exit - rtg_entry) - rho_a*evap (kg m-2 s-1, p8 Thompson water = vdiff 1..6),
18 its gross, 19 rain+graupel part (vdiff 4, 6), 20 surface flux rho_a*evap."""
import sys
from pathlib import Path
phys = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
cm = phys / "Interstitials/UFS_SCM_NEPTUNE/upchk_meter_common.F90"
t = cm.read_text()
for a, b in [("ucnv = 16", "ucnv = 20"),
             ("  real(kind=8), allocatable, save :: ucr0(:,:,:)\n",
              "  real(kind=8), allocatable, save :: ucr0(:,:,:), ucre(:,:,:)\n"),
             ("end module upchk_meter_common\n", """  subroutine uc_ent(im, km, rtg)
    integer, intent(in) :: im, km
    real(kind=kind_phys), intent(in) :: rtg(:,:,:)
    if (allocated(ucre)) then
       if (size(ucre, 1) < im .or. size(ucre, 2) < km) deallocate(ucre)
    endif
    if (.not. allocated(ucre)) allocate(ucre(im, km, 6))
    ucre(1:im, 1:km, 1:6) = rtg(1:im, 1:km, 1:6)
  end subroutine uc_ent

  subroutine uc_exit(im, km, del, rtg, rho_a, evap, grav)
    integer, intent(in) :: im, km
    real(kind=kind_phys), intent(in) :: del(:,:), rtg(:,:,:), rho_a(:), evap(:), grav
    integer :: i, k, n
    real(kind=8) :: m, w, g, r
    do i = 1, im
       w = 0.d0
       g = 0.d0
       r = 0.d0
       do k = 1, km
          m = del(i,k)/grav
          do n = 1, 6
             w = w + m*(rtg(i,k,n) - ucre(i,k,n))
             g = g + m*abs(rtg(i,k,n) - ucre(i,k,n))
          enddo
          r = r + m*(rtg(i,k,4) - ucre(i,k,4) + rtg(i,k,6) - ucre(i,k,6))
       enddo
       ucb(17, i) = w - rho_a(i)*evap(i)
       ucb(18, i) = g
       ucb(19, i) = r
       ucb(20, i) = rho_a(i)*evap(i)
    enddo
  end subroutine uc_exit
end module upchk_meter_common
""")]:
    assert t.count(a) == 1, a
    t = t.replace(a, b)
cm.write_text(t)
f = phys / "Interstitials/UFS_SCM_NEPTUNE/uc_fin.F90"
t = f.read_text()
a = "write(*,'(a,i6,16es25.16)') 'UCM '"
assert t.count(a) == 1
f.write_text(t.replace(a, "write(*,'(a,i6,20es25.16)') 'UCM '"))
s = phys / "PBL/SATMEDMF/satmedmfvdifq.F"
t = s.read_text()
for a, b in [("      use upchk_meter_common, only : uc_mlm_pre, uc_mlm_post\n",
              "      use upchk_meter_common, only : uc_mlm_pre, uc_mlm_post,\n     &                               uc_ent, uc_exit\n"),
             ("      ntrac1 = ntrac - 1\n", "      ntrac1 = ntrac - 1\n      call uc_ent(im, km, rtg)\n"),
             ("      return\n      end subroutine satmedmfvdifq_run\n",
              "      call uc_exit(im, km, del, rtg, rho_a, evap, grav)\n      return\n      end subroutine satmedmfvdifq_run\n")]:
    assert t.count(a) == 1, a
    t = t.replace(a, b)
s.write_text(t)
print("pblw hooks added")
