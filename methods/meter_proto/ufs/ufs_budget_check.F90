!> \file ufs_budget_check.F90
!! Budget check (prototype): column water change of the checked segment against its declared change.
module ufs_budget_check
  use machine, only: kind_phys
  use ufs_budget_common, only: ufs_budget_colwater
  implicit none
  private
  public :: ufs_budget_check_run
contains
!> \section arg_table_ufs_budget_check_run Argument Table
!! \htmlinclude ufs_budget_check_run.html
!!
  subroutine ufs_budget_check_run(im, levs, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, nthl, dtp, con_g, gq0, dqdt, prsi, &
                                  w0, flux, dw, decl, errmsg, errflg)
    integer, intent(in) :: im, levs, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, nthl
    real(kind=kind_phys), intent(in) :: dtp, con_g, gq0(:,:,:), dqdt(:,:,:), prsi(:,:), flux(:)
    real(kind=kind_phys), intent(inout) :: w0(:), dw(:), decl(:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    real(kind=kind_phys) :: w(im)
    errmsg = ''
    errflg = 0
    call ufs_budget_colwater(im, levs, (/ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, nthl/), dtp, con_g, gq0, dqdt, prsi, w)
    dw(1:im) = dw(1:im) + (w - w0(1:im))
    decl(1:im) = decl(1:im) + flux(1:im)
  end subroutine ufs_budget_check_run
end module ufs_budget_check
