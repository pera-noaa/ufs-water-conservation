!> \file ufs_budget_save.F90
!! Budget check (prototype): column water at the start of a checked segment.
module ufs_budget_save
  use machine, only: kind_phys
  use ufs_budget_common, only: ufs_budget_colwater
  implicit none
  private
  public :: ufs_budget_save_run
contains
!> \section arg_table_ufs_budget_save_run Argument Table
!! \htmlinclude ufs_budget_save_run.html
!!
  subroutine ufs_budget_save_run(im, levs, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, nthl, dtp, con_g, gq0, dqdt, prsi, &
                                 w0, errmsg, errflg)
    integer, intent(in) :: im, levs, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, nthl
    real(kind=kind_phys), intent(in) :: dtp, con_g, gq0(:,:,:), dqdt(:,:,:), prsi(:,:)
    real(kind=kind_phys), intent(inout) :: w0(:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    errmsg = ''
    errflg = 0
    call ufs_budget_colwater(im, levs, (/ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, nthl/), dtp, con_g, gq0, dqdt, prsi, w0)
  end subroutine ufs_budget_save_run
end module ufs_budget_save
