!> \file em_p11.F90
!! Energy meter probe 11 (diagnostic builds only).
module em_p11
  use machine, only: kind_phys
  use energy_meter_common
  implicit none
contains
!> \section arg_table_em_p11_run Argument Table
!! \htmlinclude em_p11_run.html
!!
  subroutine em_p11_run(im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, ntqv, ntcw,  &
       ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, prcp, snow, ice,  &
       graupel, rainc, errmsg, errflg)
    integer, intent(in) :: im
    integer, intent(in) :: levs
    integer, intent(in) :: kdt
    real(kind=kind_phys), intent(in) :: dtp
    real(kind=kind_phys), intent(in) :: gt0(:,:)
    real(kind=kind_phys), intent(in) :: gq0(:,:,:)
    real(kind=kind_phys), intent(in) :: gu0(:,:)
    real(kind=kind_phys), intent(in) :: gv0(:,:)
    real(kind=kind_phys), intent(in) :: dtdt(:,:)
    real(kind=kind_phys), intent(in) :: dqdt(:,:,:)
    real(kind=kind_phys), intent(in) :: dudt(:,:)
    real(kind=kind_phys), intent(in) :: dvdt(:,:)
    real(kind=kind_phys), intent(in) :: prsi(:,:)
    integer, intent(in) :: ntqv
    integer, intent(in) :: ntcw
    integer, intent(in) :: ntiw
    integer, intent(in) :: ntrw
    integer, intent(in) :: ntsw
    integer, intent(in) :: ntgl
    real(kind=kind_phys), intent(in) :: con_g
    real(kind=kind_phys), intent(in) :: con_cp
    real(kind=kind_phys), intent(in) :: con_hvap
    real(kind=kind_phys), intent(in) :: con_hfus
    real(kind=kind_phys), intent(in) :: prcp(:)
    real(kind=kind_phys), intent(in) :: snow(:)
    real(kind=kind_phys), intent(in) :: ice(:)
    real(kind=kind_phys), intent(in) :: graupel(:)
    real(kind=kind_phys), intent(in) :: rainc(:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    integer :: j0, i

    call em_probe(11, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, j0)
    do i = 1, im
       emf(10, j0+i) = 1000.d0*prcp(i)
       emf(11, j0+i) = 1000.d0*(snow(i) + ice(i) + graupel(i))
       emf(12, j0+i) = 1000.d0*rainc(i)
    enddo

    errmsg = ''
    errflg = 0
  end subroutine em_p11_run
end module em_p11
