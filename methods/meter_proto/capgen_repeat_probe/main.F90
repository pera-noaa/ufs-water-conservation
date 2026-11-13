program test_budget
  use, intrinsic :: iso_fortran_env, only: error_unit
  use omp_lib
  use ccpp_kinds, only: kind_phys
  use data, only: nchunks, chunk_begin, chunk_end, ncols, nlev, nslot, q, dp, budget_on, budget_col, budget_slot
  use test_host_ccpp_cap, only: ccpp_register, ccpp_init, ccpp_physics_init, ccpp_physics_timestep_init, &
      ccpp_physics_run, ccpp_physics_timestep_final, ccpp_physics_final, ccpp_final
  implicit none
  character(len=*), parameter :: suite = 'budget_suite'
  character(len=512) :: errmsg
  integer :: errflg, ierr, ic, pass, nt, i
  real(kind_phys) :: d1, d2, qref(ncols, nlev)
  logical :: ok

  allocate(q(ncols, nlev), dp(ncols, nlev))
  call ccpp_register(suite_name=suite, errmsg=errmsg, errflg=errflg); call chk('register')
  call ccpp_init(suite_name=suite, errmsg=errmsg, errflg=errflg); call chk('init')
  nt = omp_get_max_threads()
  call ccpp_physics_init(lb=1, ub=ncols, nthreads=nt, nphys_threads=1, thread_num=1, suite_name=suite, &
       group_name='all', errmsg=errmsg, errflg=errflg); call chk('physics_init')
  ok = .true.
  do pass = 1, 2
    budget_on = (pass == 1)
    do i = 1, ncols
      q(i, :) = 1.0e-2_kind_phys*i
      dp(i, :) = 100._kind_phys + i
    end do
    if (budget_on) then
      allocate(budget_col(ncols, nslot), budget_slot(ncols))
      budget_col = 0; budget_slot = 0
    end if
    call ccpp_physics_timestep_init(lb=1, ub=ncols, nthreads=nt, nphys_threads=1, thread_num=1, suite_name=suite, &
         group_name='all', errmsg=errmsg, errflg=errflg); call chk('timestep_init')
    ierr = 0
!$omp parallel do schedule(dynamic,1) private(ic, errmsg, errflg) reduction(+:ierr)
    do ic = 1, nchunks
      call ccpp_physics_run(lb=chunk_begin(ic), ub=chunk_end(ic), nthreads=nt, nphys_threads=1, &
           thread_num=omp_get_thread_num()+1, suite_name=suite, group_name='physics', errmsg=errmsg, errflg=errflg)
      if (errflg /= 0) then
        write(error_unit, *) 'run error chunk', ic, trim(errmsg)
        ierr = ierr + 1
      end if
    end do
!$omp end parallel do
    if (ierr /= 0) stop 1
    call ccpp_physics_timestep_final(lb=1, ub=ncols, nthreads=nt, nphys_threads=1, thread_num=1, suite_name=suite, &
         group_name='all', errmsg=errmsg, errflg=errflg); call chk('timestep_final')
    if (any(abs(q(:, 1) - (1.0e-2_kind_phys*[(i, i=1, ncols)] + 2.0e-3_kind_phys)) > 1e-12_kind_phys)) then
      write(error_unit, *) 'pass', pass, ': wet_step not applied twice'; ok = .false.
    end if
    if (budget_on) then
      if (any(budget_slot /= 3)) then
        write(error_unit, *) 'slot counts wrong:', budget_slot; ok = .false.
      end if
      do i = 1, ncols
        d1 = budget_col(i, 2) - budget_col(i, 1)
        d2 = budget_col(i, 3) - budget_col(i, 2)
        if (abs(d1 - 1.0e-3_kind_phys*dp(i, 1)) > 1e-10_kind_phys .or. abs(d2 - 1.0e-3_kind_phys*dp(i, 1)) > 1e-10_kind_phys) then
          write(error_unit, *) 'segment change wrong at column', i, d1, d2; ok = .false.
        end if
      end do
      write(*, '(a,i0,a)') 'PASS-ON: 3 probes per column, segment changes exact, threads=', nt, ''
      deallocate(budget_col, budget_slot)
    else
      write(*, '(a,l1,a)') 'PASS-OFF: ran with budget arrays unallocated (allocated=', allocated(budget_col), ')'
    end if
  end do
  call ccpp_physics_final(lb=1, ub=ncols, nthreads=nt, nphys_threads=1, thread_num=1, suite_name=suite, &
       group_name='all', errmsg=errmsg, errflg=errflg); call chk('physics_final')
  call ccpp_final(suite_name=suite, errmsg=errmsg, errflg=errflg)
  if (.not. ok) stop 2
  write(*, '(a)') 'ALL OK'
contains
  subroutine chk(s)
    character(len=*), intent(in) :: s
    if (errflg /= 0) then
      write(error_unit, *) 'error in ', s, ': ', trim(errmsg); stop 1
    end if
  end subroutine chk
end program test_budget
