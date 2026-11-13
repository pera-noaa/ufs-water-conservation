module budget_probe
  use ccpp_kinds, only: kind_phys
  implicit none
  private
  public :: budget_probe_run
contains
  !> \section arg_table_budget_probe_run Argument Table
  !! \htmlinclude budget_probe_run.html
  subroutine budget_probe_run(nlev, q, dp, budget_col, budget_slot, errmsg, errflg)
    integer, intent(in) :: nlev
    real(kind_phys), intent(in) :: q(:,:), dp(:,:)
    real(kind_phys), optional, intent(inout) :: budget_col(:,:)
    integer, optional, intent(inout) :: budget_slot(:)
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    integer :: i, n, im
    errmsg = ''
    errflg = 0
    if (.not. present(budget_col)) return
    im = size(q, 1)
    do i = 1, im
      n = budget_slot(i) + 1
      if (n > size(budget_col, 2)) then
        errflg = 1
        errmsg = 'budget_probe: more probes than slots'
        return
      end if
      budget_slot(i) = n
      budget_col(i, n) = sum(q(i, 1:nlev)*dp(i, 1:nlev))
    end do
  end subroutine budget_probe_run
end module budget_probe
