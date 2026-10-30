! #408 interface: hfus, no Leonard, dt_decay or cold pool
! run samfdeepcnv_run on nc synthetic columns split into blocks of nb; write every output to a text file
! usage: drv <flags: any of cp po ca mg> <nb> <outfile>
program drv
  use machine, only: kind_phys
  use funcphys, only: gpvs
  use samfdeepcnv, only: samfdeepcnv_run
  implicit none
  integer, parameter :: km = 64, nc = 6, ntr = 2, ntc = 1, itc = 0, ntk = 0, nn = ntr + 2
  real(kind_phys), dimension(nc,km) :: t, qv, p, dp, ph, w, bg, om
  real(kind_phys) :: ps(nc), hpbl(nc), cad(nc)
  integer :: slm(nc), i0, nb, u
  character(len=16) :: arg, nbs, nrs
  integer :: nrep, ir, col
  integer(8) :: c0, c1, cr
  character(len=16) :: cols
  character(len=256) :: fout
  logical :: coldpool, progomega, ca, mg, my, me
  call gpvs()
  call get_command_argument(1, arg); call get_command_argument(2, nbs); call get_command_argument(3, fout)
  read(nbs, *) nb
  call get_command_argument(4, nrs); read(nrs, *) nrep
  col = 0; call get_command_argument(5, cols); if (len_trim(cols) > 0) read(cols, *) col
  coldpool = index(arg, 'cp') > 0; progomega = index(arg, 'po') > 0; ca = index(arg, 'ca') > 0; mg = index(arg, 'mg') > 0; my = index(arg, 'my') > 0; me = index(arg, 'me') > 0
  call profiles()
  open(newunit=u, file=fout, status='replace')
  call system_clock(c0, cr)
  do ir = 1, nrep
    if (col > 0) then
      call run(col, col)
    else
      do i0 = 1, nc, nb
        call run(i0, min(i0+nb-1, nc))
      end do
    end if
  end do
  call system_clock(c1)
  write(*,'(a,f12.4)') 'us_per_column ', 1.d6*real(c1-c0,8)/real(cr,8)/real(nrep*merge(1, nc, col > 0),8)
  close(u)
contains
  subroutine profiles()
    real(kind_phys) :: z, tsfc(nc), qsfc(nc), wv(nc), bs(nc), hq(nc)
    integer :: i, k
    tsfc = (/ 302._kind_phys, 285._kind_phys, 300._kind_phys, 298._kind_phys, 301._kind_phys, 270._kind_phys /)
    qsfc = (/ 0.020_kind_phys, 0.004_kind_phys, 0.018_kind_phys, 0.014_kind_phys, 0.019_kind_phys, 0.002_kind_phys /)
    hq   = (/ 2500._kind_phys, 2500._kind_phys, 2500._kind_phys, 2000._kind_phys, 1200._kind_phys, 2000._kind_phys /)
    wv   = (/ -0.3_kind_phys, 0.2_kind_phys, -0.3_kind_phys, 0._kind_phys, -0.1_kind_phys, 0.1_kind_phys /)
    bs   = (/ 50._kind_phys, 50._kind_phys, 0._kind_phys, 150._kind_phys, 120._kind_phys, 20._kind_phys /)
    cad  = (/ 30._kind_phys, 30._kind_phys, 0._kind_phys, 30._kind_phys, 0._kind_phys, 0._kind_phys /)
    hpbl = (/ 800._kind_phys, 400._kind_phys, 600._kind_phys, 700._kind_phys, 900._kind_phys, 300._kind_phys /)
    slm = (/ 0, 1, 0, 1, 0, 1 /); ps = 101325._kind_phys
    do i = 1, nc
      do k = 1, km
        p(i,k) = ps(i) * (1._kind_phys - (k-0.5_kind_phys)/km*0.98_kind_phys)
        dp(i,k) = ps(i) * 0.98_kind_phys / km
        z = 7400._kind_phys * log(ps(i)/p(i,k))
        ph(i,k) = 9.80665_kind_phys * z
        t(i,k) = max(tsfc(i) - 0.0065_kind_phys*z, 205._kind_phys)
        if (i == 2 .or. i == 6) t(i,k) = max(tsfc(i) + 0.004_kind_phys*min(z,1500._kind_phys) &
                                          - 0.0065_kind_phys*max(z-1500._kind_phys,0._kind_phys), 205._kind_phys)
        qv(i,k) = qsfc(i) * exp(-z/hq(i))
        w(i,k) = wv(i)
        bg(i,k) = 0._kind_phys; if (z < 600._kind_phys) bg(i,k) = bs(i)
        om(i,k) = 0._kind_phys; if ((i == 2 .or. i == 4) .and. k > 10 .and. k < 30) om(i,k) = -2._kind_phys
        if (i == 6 .and. k > 10 .and. k < 30) om(i,k) = -0.5_kind_phys     ! weak memory
        if (me .and. (i == 1 .or. i == 3 .or. i == 5) .and. k > 10 .and. k < 30) om(i,k) = -2._kind_phys
      end do
    end do
  end subroutine
  subroutine run(i0, i1)
    integer, intent(in) :: i0, i1
    integer :: m, kbot(i1-i0+1), ktop(i1-i0+1), kcnv(i1-i0+1), flg, i
    real(kind_phys), dimension(i1-i0+1,km) :: tt, tu, tv, tkeh, q1, t1, u1, v1, udmf, ddmf, dtmf, cnvw, cnvc, &
      qlcn, qicn, wupi, cfupi, mfd, dqldt, clcn, fice, ndrop, nice, sigin, sigout, omin, omout, qmic, prevsq, bex, &
      leou, leov, leot
    real(kind_phys), dimension(i1-i0+1,km,nn) :: tq, qtr, dqtr, tmf, leoq
    real(kind_phys), dimension(i1-i0+1) :: cldwrk, rn, garea, rainev, maxmf, ucp, vcp
    real(kind_phys) :: fscav(ntc)
    character(len=128) :: msg
    m = i1 - i0 + 1
    t1 = t(i0:i1,:); q1 = qv(i0:i1,:); u1 = 5._kind_phys; v1 = -2._kind_phys
    qtr(:,:,1) = 1.e-6_kind_phys; qtr(:,:,2) = 2.e-5_kind_phys; qtr(:,:,3) = 1.e-7_kind_phys; qtr(:,:,4) = 1.e-8_kind_phys
    tmf = 0._kind_phys; qmic = 0._kind_phys; prevsq = q1; tkeh = 0._kind_phys
    sigin = 0.05_kind_phys; sigout = 0.05_kind_phys; omin = om(i0:i1,:); omout = om(i0:i1,:)
    leou = 0._kind_phys; leov = 0._kind_phys; leot = 0._kind_phys; leoq = 0._kind_phys
    cnvw = 0._kind_phys; cnvc = 0._kind_phys; kcnv = 0; garea = 1.e10_kind_phys; maxmf = 0._kind_phys; if (my) maxmf = merge(1._kind_phys, 0._kind_phys, cad(i0:i1) > 0._kind_phys); fscav = 0.5_kind_phys
    qlcn = -9._kind_phys; qicn = -9._kind_phys; wupi = 0; cfupi = 0; mfd = 0; dqldt = 0; clcn = 0; fice = 0; ndrop = 0; nice = 0
    bex = bg(i0:i1,:)
    call samfdeepcnv_run(m, km, nn, .false., .false., tmf, qmic, itc, ntc, 4.1855e3_kind_phys, 1.0046e3_kind_phys, 1.846e3_kind_phys, &
      0.622_kind_phys, -0.378_kind_phys, 0.6077_kind_phys, 9.80665_kind_phys, 2.5e6_kind_phys, 3.3358e5_kind_phys, 287.05_kind_phys, 461.5_kind_phys, &
      273.15_kind_phys, 600._kind_phys, ntk, ntr, dp(i0:i1,:), tt, tu, tv, tq, &
      p(i0:i1,:), ps(i0:i1), ph(i0:i1,:), tkeh, qtr, dqtr, prevsq, q1, q1, t1, u1, v1, fscav, &
      .false., .false., progomega, cldwrk, rn, kbot, ktop, kcnv, &
      slm(i0:i1), garea, w(i0:i1,:), 2, hpbl(i0:i1), udmf, ddmf, dtmf, cnvw, cnvc, &
      qlcn, qicn, wupi, cfupi, mfd, dqldt, clcn, fice, ndrop, nice, merge(10, 11, mg), 10, &
      0.1_kind_phys, 0.002_kind_phys, 0.002_kind_phys, 0.05_kind_phys, 0.05_kind_phys, 0.3_kind_phys, 0.55_kind_phys, 0.958_kind_phys, 1._kind_phys, &
      ca, .false., .false., ca, 18._kind_phys, cad(i0:i1), &
      rainev, sigin, sigout, omin, omout, 2._kind_phys, 1._kind_phys, &
      1._kind_phys, 1._kind_phys, 1._kind_phys, 1._kind_phys, maxmf, my, &
      .true., 1._kind_phys, &
      msg, flg)
    ucp = 0; vcp = 0
    if (ir < nrep) return
    do i = 1, m
      write(u,'(a,i2)') 'col', i0+i-1
      write(u,'(a,4i4,4es24.16)') 'sc', kcnv(i), kbot(i), ktop(i), flg, rn(i), cldwrk(i), rainev(i), ucp(i)
      write(u,'(a,es24.16)') 'vcp', vcp(i)
      call w2('ten_t', tt(i,:)); call w2('ten_u', tu(i,:)); call w2('ten_v', tv(i,:)); call w2('ten_q', tq(i,:,1))
      call w2('dqtr1', dqtr(i,:,1)); call w2('dqtr2', dqtr(i,:,2)); call w2('dqtr3', dqtr(i,:,3)); call w2('dqtr4', dqtr(i,:,4))
      call w2('ud_mf', udmf(i,:)); call w2('dd_mf', ddmf(i,:)); call w2('dt_mf', dtmf(i,:)); call w2('cnvw', cnvw(i,:)); call w2('cnvc', cnvc(i,:))
      call w2('qlcn', qlcn(i,:)); call w2('qicn', qicn(i,:)); call w2('w_upi', wupi(i,:)); call w2('cf_upi', cfupi(i,:))
      call w2('cnv_mfd', mfd(i,:)); call w2('clcn', clcn(i,:)); call w2('cnv_fice', fice(i,:))
      call w2('buoyexcs', bex(i,:)); call w2('sigmaout', sigout(i,:)); call w2('omegaout', omout(i,:))
    end do
  end subroutine
  subroutine w2(name, a)
    character(len=*), intent(in) :: name
    real(kind_phys), intent(in) :: a(:)
    write(u,'(a,1x,*(es24.16))') name, a
  end subroutine
end program
