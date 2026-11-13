!> \file energy_meter_common.F90
!! Energy meter storage and probe (diagnostic builds only).
module energy_meter_common
  use machine, only: kind_phys
  implicit none
  private
  public :: em_probe, emc, emg, emx, emkdt, emf
  integer, parameter, public :: emnp = 12, emnc = 8192
  real(kind=8), save :: emc(7, emnp, emnc) = 0.d0
  real(kind=8), allocatable, save :: emd(:,:)
  real(kind=8), save :: emg(10, emnp) = 0.d0, emx(12) = 0.d0, emf(12, emnc) = 0.d0
  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1
contains
  subroutine em_probe(p, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                      ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, j0)
    ! energy meter: effective-state column energy in the physics frame, stored per column
    integer, intent(in) :: p, im, levs, kdt, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl
    real(kind=kind_phys), intent(in) :: dtp, con_g, con_cp, con_hvap, con_hfus
    real(kind=kind_phys), intent(in) :: gt0(:,:), gq0(:,:,:), gu0(:,:), gv0(:,:), prsi(:,:)
    real(kind=kind_phys), intent(in) :: dtdt(:,:), dqdt(:,:,:), dudt(:,:), dvdt(:,:)
    integer, intent(out) :: j0
    real(kind=8) :: x(7), m, t, qv, ql, qi, u, v
    ! dycore-consistent (Kirchhoff) enthalpy, dry mass held at its probe-1 value, FV3 heat capacities
    real(kind=8), parameter :: cpa = 1004.6d0, cpv = 1846.0d0, cl = 4185.5d0, ci = 1972.0d0, t0 = 273.15d0
    real(kind=8) :: lv00, li00
    integer :: i, k
    if (kdt /= emkdt(p)) then
       emkdt(p) = kdt
       emoff(p) = 0
    endif
    j0 = emoff(p)
    lv00 = con_hvap - (cpv - cl)*t0
    li00 = con_hfus - (cl - ci)*t0
    if (.not. allocated(emd)) allocate(emd(levs, emnc))
    do i = 1, im
       x = 0.d0
       do k = 1, levs
          m = (prsi(i,k) - prsi(i,k+1))/con_g
          t = gt0(i,k) + dtp*dtdt(i,k)
          u = gu0(i,k) + dtp*dudt(i,k)
          v = gv0(i,k) + dtp*dvdt(i,k)
          qv = gq0(i,k,ntqv) + dtp*dqdt(i,k,ntqv)
          ql = gq0(i,k,ntcw) + dtp*dqdt(i,k,ntcw) + gq0(i,k,ntrw) + dtp*dqdt(i,k,ntrw)
          qi = gq0(i,k,ntiw) + dtp*dqdt(i,k,ntiw) + gq0(i,k,ntsw) + dtp*dqdt(i,k,ntsw) &
             + gq0(i,k,ntgl) + dtp*dqdt(i,k,ntgl)
          x(1) = x(1) + m*con_cp*t
          x(2) = x(2) + m*con_hvap*qv
          x(3) = x(3) - m*con_hfus*qi
          x(4) = x(4) + m*0.5d0*(u*u + v*v)
          x(5) = x(5) + m*(qv + ql + qi)
          x(6) = x(6) + m*qi
          if (p == 1) emd(k, j0+i) = m*(1.d0 - qv)
          x(7) = x(7) + emd(k, j0+i)*cpa*t + m*((qv*cpv + ql*cl + qi*ci)*t + lv00*qv - li00*qi) &
               + (emd(k, j0+i) + m*(qv + ql + qi))*0.5d0*(u*u + v*v)
       enddo
       emc(:, p, j0+i) = x
    enddo
    emoff(p) = j0 + im
  end subroutine em_probe
end module energy_meter_common
