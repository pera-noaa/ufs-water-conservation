!> \file em_p05.F90
!! Energy meter probe 5 (diagnostic builds only).
module em_p05
  use machine, only: kind_phys
  use energy_meter_common
  implicit none
contains
!> \section arg_table_em_p05_run Argument Table
!! \htmlinclude em_p05_run.html
!!
  subroutine em_p05_run(im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, ntqv, ntcw,  &
       ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, dtsfc1, dqsfc1,  &
       errmsg, errflg)
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
    real(kind=kind_phys), intent(in) :: dtsfc1(:)
    real(kind=kind_phys), intent(in) :: dqsfc1(:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    integer :: j0, i

    call em_probe(5, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, j0)
    do i = 1, im
       emf(8, j0+i) = dtp*dtsfc1(i)
       emf(9, j0+i) = dtp*dqsfc1(i)
    enddo

    errmsg = ''
    errflg = 0
  end subroutine em_p05_run
end module em_p05
