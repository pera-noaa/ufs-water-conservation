program water_closure_test_v2
  !! water closure of TEMPO calls: residual = sum of q_total * rho_d * dz after - before + precipitation, with rho_d
  !! TEMPO's own entry dry-air density. Build with -DPRE305 for versions whose tempo_init resets tempo_cfgs (9adf9ef),
  !! and with -DWCD against an instrumented module_mp_tempo_main (test/instrument.py) to print its accumulators.
  !! Usage: water_closure_test_v2 column <dt> <steps> <semi 0|1> [state file|-] [relative qv perturbation]
  !!                              early
  !!                              csub <dt> <semi 0|1> <micro 0|1>
  !!                              cap <dt> <semi 0|1>
  use module_mp_tempo_params, only : wp, roverrv, rdry, min_qv
  use module_mp_tempo_cfgs, only : ty_tempo_cfgs
  use module_mp_tempo_driver, only : tempo_init, tempo_run, ty_tempo_driver_diags
#ifdef WCD
  use module_mp_tempo_main, only : wcd
#endif
  implicit none
  integer :: nz
  real(wp), allocatable, dimension(:,:,:) :: qv, t, p, w, dz, qc, qr, qi, qs, qg, ni, nr, ng, qb
  real(wp), allocatable, dimension(:) :: md, qv0, t0c
  type(ty_tempo_cfgs) :: cfgs
  type(ty_tempo_driver_diags) :: diags
  real(wp) :: pert, dt, w0, w1, pr, res, sres, sabs, smax, sprec, pcomp(4), res1, resn
  integer :: steps, semi, micro, n, k, io, nargs
  character(len=32) :: mode, arg
  character(len=256) :: statefile

  pcomp = 0._wp
  call get_command_argument(1, mode)
  nargs = command_argument_count()
  select case (trim(mode))
  case ('column')
    call get_command_argument(2, arg); read(arg, *) dt
    call get_command_argument(3, arg); read(arg, *) steps
    call get_command_argument(4, arg); read(arg, *) semi
    statefile = ''
    if (nargs >= 5) call get_command_argument(5, statefile)
    if (statefile == '-') statefile = ''
    call read_column()
    if (nargs >= 6) then
      call get_command_argument(6, arg); read(arg, *) pert
      qv = qv*(1._wp + pert)
    endif
    call init(semi == 1, .false.)
    sres = 0._wp; sabs = 0._wp; smax = 0._wp; sprec = 0._wp; pcomp = 0._wp
    do n = 1, steps
      call step(n, res, pr)
      sres = sres + res; sabs = sabs + abs(res); smax = max(smax, abs(res)); sprec = sprec + pr
      if (n == 1) res1 = res
      call get_environment_variable('WCT_VERBOSE', arg)
      if (len_trim(arg) > 0) write(*, '(a,i4,3es24.15)') 'step', n, res, pr, sum((qv(1,:,1)+qc(1,:,1)+qr(1,:,1)+qi(1,:,1)+qs(1,:,1)+qg(1,:,1))*md)
      if (arg == 'dump') then
        do k = 1, nz
          write(*, '(a,2i4,8es24.15)') 'lev', n, k, qv(1,k,1), qc(1,k,1), qr(1,k,1), qi(1,k,1), qs(1,k,1), qg(1,k,1), nr(1,k,1), t(1,k,1)
        enddo
      endif
      resn = res
    enddo
    write(*, '(a,f6.1,a,i5,a,i2,a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4)') &
      'dt=', dt, ' steps=', steps, ' semi=', semi, ' P=', sprec, ' sum_res=', sres, ' sum_abs=', sabs, &
      ' mean_step=', sres/steps, ' max_step=', smax, ' first=', res1, ' last=', resn, ' res/P=', sres/max(sprec, 1.e-30_wp)
    write(*, '(a,4es23.15)') '  P rain/ice/snow/graupel=', pcomp
    if (len_trim(statefile) > 0) then
      open(newunit=io, file=trim(statefile), status='replace')
      do k = 1, nz
        write(io, '(i3,12es24.16)') k, qv(1,k,1), qc(1,k,1), qr(1,k,1), qi(1,k,1), qs(1,k,1), qg(1,k,1), &
          ni(1,k,1), nr(1,k,1), ng(1,k,1), qb(1,k,1), t(1,k,1)
      enddo
      write(io, '(a,4es24.16)') 'P', pcomp
      close(io)
    endif

  case ('early')
    ! no hydrometeor above r1 anywhere, subsaturated: tempo_main returns early. Tiny and negative condensate at entry
    nz = 10
    dt = 60._wp
    call alloc()
    do k = 1, nz
      p(1,k,1) = 90000._wp - 2000._wp*(k-1); t(1,k,1) = 285._wp - 1.5_wp*(k-1); qv(1,k,1) = 2.e-3_wp
      dz(1,k,1) = 200._wp
    enddo
    qr(1,:,1) = 5.e-13_wp
    qc(1,3,1) = -1.e-8_wp
    qi(1,9,1) = 4.e-13_wp; qs(1,10,1) = -2.e-12_wp; qg(1,8,1) = 3.e-13_wp
    call init(.false., .false.)
    qv0 = qv(1,:,1); t0c = t(1,:,1)
    call step(1, res, pr)
    write(*, '(a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4)') 'early: W1-W0+P=', res, '  P=', pr, &
      '  entry condensate=', sum((qc0()) * md), '  dqv*md (all)=', sum((qv(1,:,1)-qv0)*md), &
      '  dT(3)=', t(1,3,1)-t0c(3)

  case ('csub')
    ! fog in a thin lowest layer only, falling more than the layer's depth in one step
    call get_command_argument(2, arg); read(arg, *) dt
    call get_command_argument(3, arg); read(arg, *) semi
    call get_command_argument(4, arg); read(arg, *) micro
    nz = 20
    call alloc()
    dz(1,1,1) = 5._wp
    dz(1,2:nz,1) = 50._wp
    p(1,1,1) = 100000._wp - 0.5_wp*dz(1,1,1)*11.8_wp
    t(1,1,1) = 283._wp
    do k = 2, nz
      p(1,k,1) = p(1,k-1,1) - 0.5_wp*(dz(1,k-1,1) + dz(1,k,1))*11.8_wp
      t(1,k,1) = t(1,k-1,1) - 0.0065_wp*0.5_wp*(dz(1,k-1,1) + dz(1,k,1))
    enddo
    do k = 1, nz
      qv(1,k,1) = 0.98_wp*qsat_w(t(1,k,1), p(1,k,1))
    enddo
    qc(1,1,1) = 1.5e-3_wp
    call init(semi == 1, micro == 0)
    qv0 = qv(1,:,1)
    call step(1, res, pr)
    write(*, '(a,i2,a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4)') 'csub micro=', micro, &
      ': W1-W0+P=', res, '  P=', pr, '  P_rain=', pcomp(1), '  dqv(1)*md(1)=', (qv(1,1,1)-qv0(1))*md(1), &
      '  qc(1)=', qc(1,1,1), '  cloud entry mass=', 1.5e-3_wp*md(1)

  case ('cap')
    ! cold rain and snow at every combination of temperature, rain and snow content (one level each)
    call get_command_argument(2, arg); read(arg, *) dt
    call get_command_argument(3, arg); read(arg, *) semi
    nz = 36
    call alloc()
    do k = 1, nz
      t(1,k,1) = 258._wp + 4._wp*mod(k-1, 4)
      qr(1,k,1) = 10._wp**(-5 + mod((k-1)/4, 3))
      qs(1,k,1) = 10._wp**(-5 + (k-1)/12)
      p(1,k,1) = 80000._wp - 300._wp*(k-1)
      dz(1,k,1) = 100._wp
      qv(1,k,1) = qsat_w(t(1,k,1), p(1,k,1))
    enddo
    call init(semi == 1, .false.)
    call step(1, res, pr)
    write(*, '(a,es12.4,a,es12.4)') 'cap: W1-W0+P=', res, '  P=', pr

  case default
    error stop 'unknown mode'
  end select
#ifdef WCD
  write(*, '(a,7es12.4)') '  wcd(1:7)=', wcd(1:7)
#endif

contains

  subroutine alloc()
    allocate(qv(1,nz,1), t(1,nz,1), p(1,nz,1), w(1,nz,1), dz(1,nz,1), qc(1,nz,1), qr(1,nz,1), qi(1,nz,1), &
      qs(1,nz,1), qg(1,nz,1), ni(1,nz,1), nr(1,nz,1), ng(1,nz,1), qb(1,nz,1), source=0._wp)
    allocate(md(nz), qv0(nz), t0c(nz), source=0._wp)
  end subroutine alloc

  subroutine read_column()
    real(wp), allocatable, dimension(:) :: klev, qv_in, qc_in, qr_in, qi_in, qs_in, qg_in, ni_in, nr_in, nc_in, &
      nwfa_in, nifa_in, theta_in, ng_in, volg_in, p_in, w_in, dz_in
    nz = 59
    call alloc()
    allocate(klev(nz), qv_in(nz), qc_in(nz), qr_in(nz), qi_in(nz), qs_in(nz), qg_in(nz), ni_in(nz), nr_in(nz), &
      nc_in(nz), nwfa_in(nz), nifa_in(nz), theta_in(nz), ng_in(nz), volg_in(nz), p_in(nz), w_in(nz), dz_in(nz))
    open(newunit=io, file='mpas_59lev_test.txt', status='old')
    read(io, *)
    do k = 1, nz
      read(io, *) klev(k), qv_in(k), qc_in(k), qr_in(k), qi_in(k), qs_in(k), qg_in(k), ni_in(k), nr_in(k), &
        nc_in(k), nwfa_in(k), nifa_in(k), theta_in(k), ng_in(k), volg_in(k), p_in(k), w_in(k), dz_in(k)
    enddo
    close(io)
    qv(1,:,1) = qv_in; qc(1,:,1) = qc_in; qr(1,:,1) = qr_in; qi(1,:,1) = qi_in; qs(1,:,1) = qs_in
    qg(1,:,1) = qg_in; ni(1,:,1) = ni_in; nr(1,:,1) = nr_in; ng(1,:,1) = ng_in; qb(1,:,1) = volg_in*1000._wp
    t(1,:,1) = theta_in*(p_in/100000._wp)**0.286_wp
    p(1,:,1) = p_in; w(1,:,1) = w_in; dz(1,:,1) = dz_in
  end subroutine read_column

  subroutine init(semi_flag, micro_off)
    logical, intent(in) :: semi_flag, micro_off
#ifdef PRE305
    call tempo_init(semi_sedi_flag=semi_flag, tempo_cfgs=cfgs)  ! before v3.0.5 tempo_init resets tempo_cfgs
#else
    cfgs%semi_sedi_flag = semi_flag
    call tempo_init(tempo_cfgs=cfgs)
#endif
    cfgs%turn_off_micro_flag = micro_off
  end subroutine init

  subroutine step(n, res, pr)
    integer, intent(in) :: n
    real(wp), intent(out) :: res, pr
    md = roverrv*p(1,:,1)/(rdry*t(1,:,1)*(max(min_qv, qv(1,:,1))+roverrv))*dz(1,:,1)
    w0 = sum((qv(1,:,1)+qc(1,:,1)+qr(1,:,1)+qi(1,:,1)+qs(1,:,1)+qg(1,:,1))*md)
    call tempo_run(tempo_cfgs=cfgs, itimestep=n, dt=dt, &
      ids=1, ide=1, ims=1, ime=1, its=1, ite=1, jds=1, jde=1, jms=1, jme=1, &
      jts=1, jte=1, kds=1, kde=nz, kms=1, kme=nz, kts=1, kte=nz, &
      t=t, p=p, w=w, dz=dz, qv=qv, qc=qc, qr=qr, qi=qi, qs=qs, qg=qg, ni=ni, nr=nr, ng=ng, qb=qb, &
      tempo_diags=diags)
    w1 = sum((qv(1,:,1)+qc(1,:,1)+qr(1,:,1)+qi(1,:,1)+qs(1,:,1)+qg(1,:,1))*md)
    pr = diags%rain_precip(1,1) + diags%ice_liquid_equiv_precip(1,1) + diags%snow_liquid_equiv_precip(1,1) + &
      diags%graupel_liquid_equiv_precip(1,1)
    pcomp = pcomp + [diags%rain_precip(1,1), diags%ice_liquid_equiv_precip(1,1), &
      diags%snow_liquid_equiv_precip(1,1), diags%graupel_liquid_equiv_precip(1,1)]
    res = w1 - w0 + pr
  end subroutine step

  function qc0() result(c)
    real(wp) :: c(nz)
    c = 5.e-13_wp
    c(3) = c(3) - 1.e-8_wp
    c(9) = c(9) + 4.e-13_wp; c(10) = c(10) - 2.e-12_wp; c(8) = c(8) + 3.e-13_wp
  end function qc0

  real(wp) function qsat_w(tk, pa)
    real(wp), intent(in) :: tk, pa
    real(wp) :: es
    es = 611.2_wp*exp(17.67_wp*(tk - 273.15_wp)/(tk - 29.65_wp))
    qsat_w = 0.622_wp*es/(pa - es)
  end function qsat_w
end program water_closure_test_v2
