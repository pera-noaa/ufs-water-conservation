! mynnred: standalone driver calling the REAL module_bl_mynn::moisture_check on a dumped column (unfixed and 01b)
! usage: mc_driver <col file> ; prints the model-vs-driver check and the frame-P energy of the fill both ways
program mc_driver
  use machine, only: kind_phys
  use bl_mynn_common, only: xlvcp, xlscp
  use module_bl_mynn, only: moisture_check
  implicit none
  real(kind_phys), parameter :: cp = 1004.6d0, xlv = 2.5d6, xlf = 3.3358d5
  character(len=512) :: fn, line
  character(len=8) :: c1, c2, c3, c4, c5, c6, c7
  integer :: kte, ncall, k, kk, u
  logical :: flag_qi
  real(kind_phys) :: delt, a(28)
  real(kind_phys), allocatable :: v(:,:), qv(:), qc(:), qi(:), qs(:), thx(:), dqv(:), dqc(:), dqi(:), dqs(:), dthx(:), m(:)
  real(kind_phys), allocatable :: dth_u(:), dth_f(:), dth_0(:), dqvU(:), dqiU(:), dqsU(:)
  real(kind_phys) :: e_u, e_f, lfill, errmax
  call get_command_argument(1, fn)
  open(newunit=u, file=trim(fn), status='old', action='read')
  read(u,*) c1, c2, c3, c4, c5, c6, c7, kte, delt, flag_qi, ncall, xlvcp, xlscp
  read(u,'(a)') line
  allocate(v(kte,28))
  do k = 1, kte
     read(u,*) kk, a
     v(k,:) = a
  enddo
  close(u)
  ! columns: 1 exner 2 rho 3 dz 4 delp 5 th 6 thl0 7 thl1 8-11 sqv..sqs 12-15 sqv0..sqs0 16-19 sqv2..sqs2
  !          20-23 dqv0..dqs0 24-27 dqv..dqs 28 dth
  allocate(qv(kte), qc(kte), qi(kte), qs(kte), thx(kte), dqv(kte), dqc(kte), dqi(kte), dqs(kte), dthx(kte), m(kte))
  allocate(dth_u(kte), dth_f(kte), dth_0(kte), dqvU(kte), dqiU(kte), dqsU(kte))
  m = v(:,2)*v(:,3)
  ! the reference: tendencies without any fill
  dth_0 = dth(v(:,6), v(:,13), v(:,14))
  ! unfixed: thl handed to moisture_check
  call load(); thx = v(:,6)
  call moisture_check(kte, delt, v(:,4), v(:,1), qv, qc, qi, qs, thx, dqv, dqc, dqi, dqs, dthx)
  dth_u = dth(thx, qc, qi)
  dqvU = dqv; dqiU = dqi; dqsU = dqs
  errmax = max(maxval(abs(thx - v(:,7))), maxval(abs(dth_u - v(:,28)))/maxval(abs(v(:,28))), &
               maxval(abs(dqv - v(:,24)))/maxval(abs(v(:,24))), maxval(abs(qc - v(:,17))))
  ! 01b: scratch copy
  call load(); thx = v(:,6)
  call moisture_check(kte, delt, v(:,4), v(:,1), qv, qc, qi, qs, thx, dqv, dqc, dqi, dqs, dthx)
  dth_f = dth(v(:,6), qc, qi)
  e_u = sum(m*(cp*v(:,1)*(dth_u - dth_0) + xlv*(dqvU - v(:,20)) - xlf*(dqiU - v(:,22) + dqsU - v(:,23))))*delt
  e_f = sum(m*(cp*v(:,1)*(dth_f - dth_0) + xlv*(dqv - v(:,20)) - xlf*(dqi - v(:,22) + dqs - v(:,23))))*delt
  lfill = sum(m*(xlv*max(0d0,-v(:,13)) + (xlv+xlf)*(max(0d0,-v(:,14)) + max(0d0,-v(:,15)))))
  write(*,'(a,a,es10.2,a,3es22.14)') trim(fn(index(fn,'/',.true.)+1:)), ' model-vs-driver max err ', errmax, &
       '  E_fill unfixed, 01b, L*fill (J m-2) ', e_u, e_f, lfill
contains
  subroutine load()
    qv = v(:,12); qc = v(:,13); qi = v(:,14); qs = v(:,15)
    dqv = v(:,20); dqc = v(:,21); dqi = v(:,22); dqs = v(:,23); dthx = 0d0
  end subroutine load
  function dth(thl, sqc2, sqi2) result(r)
    real(kind_phys), intent(in) :: thl(:), sqc2(:), sqi2(:)
    real(kind_phys) :: r(size(thl))
    if (flag_qi) then
       r = (thl + xlvcp/v(:,1)*sqc2 + xlscp/v(:,1)*sqi2 - v(:,5))/delt
    else
       r = (thl + xlvcp/v(:,1)*sqc2 - v(:,5))/delt
    endif
  end function dth
end program mc_driver
