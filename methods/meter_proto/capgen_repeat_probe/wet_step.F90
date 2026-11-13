module wet_step
  use ccpp_kinds, only: kind_phys
  implicit none
  private
  public :: wet_step_run
contains
  !> \section arg_table_wet_step_run Argument Table
  !! \htmlinclude wet_step_run.html
  subroutine wet_step_run(q, errmsg, errflg)
    real(kind_phys), intent(inout) :: q(:,:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    errmsg = ''
    errflg = 0
    q(:, 1) = q(:, 1) + 1.0e-3_kind_phys
  end subroutine wet_step_run
end module wet_step
