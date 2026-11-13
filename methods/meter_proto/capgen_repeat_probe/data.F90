module data
  use ccpp_kinds, only: kind_phys
  implicit none
  private
  public :: nchunks, chunk_begin, chunk_end, ncols, nlev, nslot
  public :: q, dp, budget_on, budget_col, budget_slot
  integer, parameter :: nchunks = 4
  integer, parameter, dimension(nchunks) :: chunk_begin = (/1, 7, 13, 19/)
  integer, parameter, dimension(nchunks) :: chunk_end = (/6, 12, 18, 21/)
  integer, parameter :: ncols = 21, nlev = 3
  integer :: nslot = 3
  real(kind_phys), allocatable :: q(:,:), dp(:,:)
  logical :: budget_on = .false.
  real(kind_phys), allocatable, target :: budget_col(:,:)
  integer, allocatable, target :: budget_slot(:)
end module data
