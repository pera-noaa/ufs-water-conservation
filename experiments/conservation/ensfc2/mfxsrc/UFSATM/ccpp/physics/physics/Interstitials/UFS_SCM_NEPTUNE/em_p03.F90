!> \file em_p03.F90
!! Energy meter probe 3 (diagnostic builds only).
module em_p03
  use machine, only: kind_phys
  use energy_meter_common
  use module_radsw_parameters, only: topfsw_type, sfcfsw_type
  use module_radlw_parameters, only: topflw_type, sfcflw_type
  implicit none
contains
!> \section arg_table_em_p03_run Argument Table
!! \htmlinclude em_p03_run.html
!!
  subroutine em_p03_run(im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, ntqv, ntcw,  &
       ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, xmu, topfsw, topflw,  &
       sfcfsw, sfcflw, adjsfcnsw, adjsfcdlw, errmsg, errflg)
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
    real(kind=kind_phys), intent(in) :: xmu(:)
    type(topfsw_type), intent(in) :: topfsw(:)
    type(topflw_type), intent(in) :: topflw(:)
    type(sfcfsw_type), intent(in) :: sfcfsw(:)
    type(sfcflw_type), intent(in) :: sfcflw(:)
    real(kind=kind_phys), intent(in) :: adjsfcnsw(:)
    real(kind=kind_phys), intent(in) :: adjsfcdlw(:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    integer :: j0, i

    call em_probe(3, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, j0)
    do i = 1, im
       emf(2, j0+i) = dtp*xmu(i)*(topfsw(i)%dnfxc - topfsw(i)%upfxc)
       emf(3, j0+i) = -dtp*topflw(i)%upfxc
       emf(4, j0+i) = dtp*xmu(i)*(sfcfsw(i)%dnfxc - sfcfsw(i)%upfxc)
       emf(5, j0+i) = dtp*(sfcflw(i)%dnfxc - sfcflw(i)%upfxc)
       emf(6, j0+i) = dtp*adjsfcnsw(i)
       emf(7, j0+i) = dtp*adjsfcdlw(i)
       emf(1, j0+i) = emf(2, j0+i) + emf(3, j0+i) - emf(4, j0+i) - emf(5, j0+i)
    enddo

    errmsg = ''
    errflg = 0
  end subroutine em_p03_run
end module em_p03
