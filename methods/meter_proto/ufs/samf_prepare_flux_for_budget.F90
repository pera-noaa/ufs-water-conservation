!> \file samf_prepare_flux_for_budget.F90
!! Budget check (prototype): SAMF's declared water change, deep plus shallow precipitation.
module samf_prepare_flux_for_budget
  use machine, only: kind_phys
  implicit none
  private
  public :: samf_prepare_flux_for_budget_run
contains
!> \section arg_table_samf_prepare_flux_for_budget_run Argument Table
!! \htmlinclude samf_prepare_flux_for_budget_run.html
!!
  subroutine samf_prepare_flux_for_budget_run(im, rainc, flux, errmsg, errflg)
    integer, intent(in) :: im
    real(kind=kind_phys), intent(in) :: rainc(:)
    real(kind=kind_phys), intent(inout) :: flux(:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    errmsg = ''
    errflg = 0
    flux(1:im) = -1000._kind_phys*rainc(1:im)   ! m of liquid water -> kg m-2
  end subroutine samf_prepare_flux_for_budget_run
end module samf_prepare_flux_for_budget
