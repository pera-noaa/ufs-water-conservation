!> \file GFS_budget.F90
!! Budget meters, prototype: host water budget (A), per-scheme hook (C), report of the check schemes (B).
!! Namelist &budget_nml in input.nml; everything is off by default and reads state only.
module GFS_budget

  use mpp_mod,           only: mpp_pe, mpp_root_pe, mpp_max, mpp_error, FATAL, input_nml_file
  use mpp_efp_mod,       only: mpp_reproducing_sum
  use block_control_mod, only: block_control_type
  use physcons,          only: con_g, con_hvap
  use GFS_typedefs,      only: kind_phys
  use CCPP_data,         only: GFS_control, GFS_statein, GFS_stateout, GFS_intdiag, GFS_grid, GFS_interstitial

  implicit none
  private
  public :: budget_init, budget_before_physics, budget_after_physics, budget_post_call_hook

  integer, parameter :: r8 = selected_real_kind(15)
  integer, parameter :: nslot_max = 160

  logical  :: budget_meter = .false.      ! A, and the report of B
  logical  :: budget_hook = .false.       ! C
  real(r8) :: budget_tol_report = 0._r8   ! kg m-2 per window; 0 = none
  real(r8) :: budget_tol_fatal = 0._r8    ! kg m-2 per window; 0 = none
  namelist /budget_nml/ budget_meter, budget_hook, budget_tol_report, budget_tol_fatal

  integer :: nw = 0, iw(7) = 0, nwin = 1
  logical :: have_w1 = .false.
  integer :: nslot = 0
  character(len=64) :: slot_name(nslot_max) = ''
  integer,  allocatable :: slot(:)
  real(r8), allocatable :: w0(:), w1(:), wl(:)
  real(r8), allocatable :: s_dw(:), s_e(:), s_pc(:), s_pl(:), s_h(:), s_np(:), s_gap(:)
  real(r8), allocatable :: c_dw(:,:)

contains

  !> Read &budget_nml and allocate per-column storage (all ranks call it).
  subroutine budget_init()
    integer :: io, n, k, cand(7)
    read(input_nml_file, nml=budget_nml, iostat=io)
    if (io > 0) call mpp_error(FATAL, 'GFS_budget: error reading &budget_nml')
    if (.not. (budget_meter .or. budget_hook)) return
    if (abs(GFS_control%dtf - GFS_control%dtp) > 0.) call mpp_error(FATAL, 'GFS_budget: needs dtf = dtp (frain = 1)')
    cand = (/ GFS_control%ntqv, GFS_control%ntcw, GFS_control%ntiw, GFS_control%ntrw, &
              GFS_control%ntsw, GFS_control%ntgl, GFS_control%nthl /)
    nw = 0
    do k = 1, 7
      if (cand(k) > 0 .and. .not. any(iw(1:nw) == cand(k))) then
        nw = nw + 1
        iw(nw) = cand(k)
      endif
    enddo
    nwin = max(1, GFS_control%nszero)
    n = GFS_control%ncols
    allocate(w0(n), w1(n), wl(n), slot(n), s_dw(n), s_e(n), s_pc(n), s_pl(n), s_h(n), s_np(n), s_gap(n))
    allocate(c_dw(n, nslot_max))
    w0 = 0; w1 = 0; wl = 0; slot = 0; c_dw = 0
    call zero_window()
    if (mpp_pe() == mpp_root_pe()) write(*,'(a,l2,a,l2,a,i0,a,i0)') 'BUDGET init: meter', budget_meter, &
         ' hook', budget_hook, ' water species ', nw, ' window steps ', nwin
  end subroutine budget_init

  subroutine zero_window()
    s_dw = 0; s_e = 0; s_pc = 0; s_pl = 0; s_h = 0; s_np = 0; s_gap = 0
    c_dw = 0
    if (associated(GFS_intdiag%budget_b_dw)) then
      GFS_intdiag%budget_b_dw = 0
      GFS_intdiag%budget_b_decl = 0
    endif
  end subroutine zero_window

  !> Column water (kg m-2) of q in the physics frame, columns i1:i2.
  subroutine colwater(q, i1, i2, w)
    real(kind=kind_phys), intent(in) :: q(:,:,:)
    integer, intent(in) :: i1, i2
    real(r8), intent(out) :: w(i1:i2)
    integer :: i, k, m
    real(r8) :: s
    do i = i1, i2
      s = 0._r8
      do k = 1, GFS_control%levs
        do m = 1, nw
          s = s + q(i, k, iw(m))*(GFS_statein%prsi(i, k) - GFS_statein%prsi(i, k+1))
        enddo
      enddo
      w(i) = s/con_g
    enddo
  end subroutine colwater

  !> Right before CCPP_step("physics"): close non_physics, open physics.
  subroutine budget_before_physics()
    integer :: n
    if (.not. (budget_meter .or. budget_hook)) return
    n = GFS_control%ncols
    call colwater(GFS_statein%qgrs, 1, n, w0)
    if (have_w1) s_np = s_np + (w0 - w1)
    wl = w0
    slot = 0
  end subroutine budget_before_physics

  !> Right after CCPP_step("physics"): close physics, report at window ends.
  subroutine budget_after_physics(Atm_block)
    type(block_control_type), intent(in) :: Atm_block
    real(r8) :: dt
    if (.not. (budget_meter .or. budget_hook)) return
    dt = GFS_control%dtp
    call colwater(GFS_stateout%gq0, 1, GFS_control%ncols, w1)
    have_w1 = .true.
    s_dw = s_dw + (w1 - w0)
    s_gap = s_gap + (w1 - wl)
    s_e = s_e + GFS_intdiag%dqsfci/con_hvap*dt
    s_pc = s_pc + 1000._r8*GFS_intdiag%rainc
    s_pl = s_pl + 1000._r8*(GFS_intdiag%rain - GFS_intdiag%rainc)
    s_h = s_h + GFS_intdiag%budget_h2ophys
    if (mod(GFS_control%kdt, nwin) == 0) then
      call report(Atm_block)
      call zero_window()
    endif
  end subroutine budget_after_physics

  !> C: called by the generated caps after every scheme run call (capgen --post-call-hook).
  subroutine budget_post_call_hook(suite, group, scheme, lb, ub, thread_num, errmsg, errflg)
    character(len=*), intent(in) :: suite, group, scheme
    integer, intent(in) :: lb, ub, thread_num
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    integer :: i, k, m, s
    real(r8) :: w, dt
    errmsg = ''
    errflg = 0
    if (.not. budget_hook) return
    if (group /= 'phys_ps' .and. group /= 'phys_ts') return
    slot(lb:ub) = slot(lb:ub) + 1
    s = slot(lb)
    if (s > nslot_max) then
      errflg = 1
      errmsg = 'GFS_budget: more hook calls per step than nslot_max'
      return
    endif
    if (slot_name(s) == '') then
!$omp critical (budget_slot_name)
      if (slot_name(s) == '') slot_name(s) = trim(group)//':'//trim(scheme)
      nslot = max(nslot, s)
!$omp end critical (budget_slot_name)
    endif
    dt = GFS_control%dtp
    do i = lb, ub
      w = 0._r8
      do k = 1, GFS_control%levs
        do m = 1, nw
          w = w + (GFS_stateout%gq0(i, k, iw(m)) + dt*GFS_interstitial(thread_num)%dqdt(i, k, iw(m))) &
                  *(GFS_statein%prsi(i, k) - GFS_statein%prsi(i, k+1))
        enddo
      enddo
      w = w/con_g
      c_dw(i, s) = c_dw(i, s) + (w - wl(i))
      wl(i) = w
    enddo
  end subroutine budget_post_call_hook

  !> Area-weighted global mean of a column field (kg m-2), layout-independent (FMS EFP sum).
  real(r8) function gmean(x, Atm_block)
    real(r8), intent(in) :: x(:)
    type(block_control_type), intent(in) :: Atm_block
    real(r8), allocatable :: a(:,:), b(:,:)
    integer :: nb, ix, j
    allocate(a(Atm_block%isc:Atm_block%iec, Atm_block%jsc:Atm_block%jec), &
             b(Atm_block%isc:Atm_block%iec, Atm_block%jsc:Atm_block%jec))
    a = 0; b = 0
    do nb = 1, Atm_block%nblks
      do ix = 1, Atm_block%blksz(nb)
        j = GFS_control%chunk_begin(nb) + ix - 1
        a(Atm_block%index(nb)%ii(ix), Atm_block%index(nb)%jj(ix)) = x(j)*GFS_grid%area(j)
        b(Atm_block%index(nb)%ii(ix), Atm_block%index(nb)%jj(ix)) = GFS_grid%area(j)
      enddo
    enddo
    gmean = mpp_reproducing_sum(a)/mpp_reproducing_sum(b)
  end function gmean

  real(r8) function gmax(x)
    real(r8), intent(in) :: x(:)
    gmax = maxval(abs(x))
    call mpp_max(gmax)
  end function gmax

  subroutine line(qty, seg, chg, decl, res, sabs, mabs)
    character(len=*), intent(in) :: qty, seg
    real(r8), intent(in) :: chg, decl, res, sabs, mabs
    if (mpp_pe() == mpp_root_pe()) write(*,'(a,1x,a,f9.3,1x,a40,5es24.15)') 'BUDGET', qty, GFS_control%fhour, &
         seg, chg, decl, res, sabs, mabs
  end subroutine line

  subroutine report(Atm_block)
    type(block_control_type), intent(in) :: Atm_block
    real(r8), allocatable :: r(:)
    real(r8) :: dw, e, pc, pl, h, res, cd(nslot_max), csum, fam(5), famd(5)
    integer :: s, f
    character(len=64) :: nm
    allocate(r(GFS_control%ncols))
    if (budget_meter) then
      r = s_dw - (s_e - s_pc - s_pl + s_h)
      dw = gmean(s_dw, Atm_block); e = gmean(s_e, Atm_block); pc = gmean(s_pc, Atm_block)
      pl = gmean(s_pl, Atm_block); h = gmean(s_h, Atm_block); res = gmean(r, Atm_block)
      call line('water', 'A:physics', dw, e - pc - pl + h, res, gmean(abs(r), Atm_block), gmax(r))
      call line('water', 'A:E,Pconv,Pls,H', e, pc, pl, h, 0._r8)
      call line('water', 'A:non_physics', gmean(s_np, Atm_block), 0._r8, gmean(s_np, Atm_block), &
                gmean(abs(s_np), Atm_block), gmax(s_np))
      if (budget_tol_fatal > 0._r8 .and. abs(res) > budget_tol_fatal) &
         call mpp_error(FATAL, 'GFS_budget: physics water residual above budget_tol_fatal')
      if (associated(GFS_intdiag%budget_b_dw)) then
        r = GFS_intdiag%budget_b_dw - GFS_intdiag%budget_b_decl
        call line('water', 'B:samf', gmean(GFS_intdiag%budget_b_dw, Atm_block), &
                  gmean(GFS_intdiag%budget_b_decl, Atm_block), gmean(r, Atm_block), gmean(abs(r), Atm_block), gmax(r))
      endif
    endif
    if (budget_hook) then
      csum = 0; fam = 0
      do s = 1, nslot
        cd(s) = gmean(c_dw(:, s), Atm_block)
        csum = csum + cd(s)
        call line('water', 'C:'//trim(slot_name(s)), cd(s), 0._r8, 0._r8, 0._r8, 0._r8)
      enddo
      ! families: 1 PBL (+E), 2 photochemistry (+H), 3 SAMF incl. interstitials 3-4 (-Pconv), 4 MP (-Pls), 5 rest (0)
      f = 5
      do s = 1, nslot
        nm = slot_name(s)(index(slot_name(s), ':')+1:)
        select case (trim(nm))
        case ('satmedmfvdifq', 'GFS_PBL_generic_post');                f = 1
        case ('GFS_photochemistry', 'GFS_photochemistry_post');       f = 2
        case ('GFS_suite_interstitial_3');                             f = 3
        case ('mp_thompson', 'mp_thompson_post', 'GFS_MP_generic_post'); f = 4
        case default
          if (f /= 3) f = 5
        end select
        fam(f) = fam(f) + cd(s)
        if (trim(nm) == 'GFS_suite_interstitial_4') f = 5
      enddo
      e = gmean(s_e, Atm_block); pc = gmean(s_pc, Atm_block); pl = gmean(s_pl, Atm_block); h = gmean(s_h, Atm_block)
      famd = (/ e, h, -pc, -pl, 0._r8 /)
      call line('water', 'C:fam_pbl', fam(1), famd(1), fam(1) - famd(1), 0._r8, 0._r8)
      call line('water', 'C:fam_photochem', fam(2), famd(2), fam(2) - famd(2), 0._r8, 0._r8)
      call line('water', 'C:fam_samf', fam(3), famd(3), fam(3) - famd(3), 0._r8, 0._r8)
      call line('water', 'C:fam_mp', fam(4), famd(4), fam(4) - famd(4), 0._r8, 0._r8)
      call line('water', 'C:fam_rest', fam(5), famd(5), fam(5) - famd(5), 0._r8, 0._r8)
      call line('water', 'C:sum_vs_A', csum, gmean(s_dw, Atm_block), csum - gmean(s_dw, Atm_block), &
                gmean(s_gap, Atm_block), gmax(s_gap))
    endif
  end subroutine report

end module GFS_budget
