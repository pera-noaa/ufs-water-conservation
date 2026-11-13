!> \file ufs_budget_common.F90
!! Column water for the budget check schemes (prototype).
module ufs_budget_common
  use machine, only: kind_phys
  implicit none
  private
  public :: ufs_budget_colwater
contains
  !> Column water (kg m-2) of the effective state gq0 + dtp*dqdt, over the water species present.
  subroutine ufs_budget_colwater(im, levs, idx, dtp, con_g, gq0, dqdt, prsi, w)
    integer, intent(in) :: im, levs, idx(:)
    real(kind=kind_phys), intent(in) :: dtp, con_g, gq0(:,:,:), dqdt(:,:,:), prsi(:,:)
    real(kind=kind_phys), intent(out) :: w(:)
    integer :: i, k, m
    real(kind=8) :: s
    do i = 1, im
      s = 0.d0
      do k = 1, levs
        do m = 1, size(idx)
          if (idx(m) > 0 .and. .not. any(idx(1:m-1) == idx(m))) &
            s = s + (gq0(i,k,idx(m)) + dtp*dqdt(i,k,idx(m)))*(prsi(i,k) - prsi(i,k+1))
        enddo
      enddo
      w(i) = s/con_g
    enddo
  end subroutine ufs_budget_colwater
end module ufs_budget_common
