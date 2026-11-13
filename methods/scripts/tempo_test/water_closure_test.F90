program water_closure_test
  !! water closure of one TEMPO call per step on the 59-level test column: residual = sum of q_total * rho_d * dz
  !! after - before - precipitation, with rho_d TEMPO's own entry dry-air density. Usage: water_closure_test <dt> <steps> <semi_sedi 0|1>
  use module_mp_tempo_params, only : wp, roverrv, rdry, min_qv
  use module_mp_tempo_cfgs, only : ty_tempo_cfgs
  use module_mp_tempo_driver, only : tempo_init, tempo_run, ty_tempo_driver_diags
  implicit none
  integer, parameter :: nz = 59
  integer, parameter :: ids = 1, ide = 1, ims = 1, ime = 1, its = 1, ite = 1
  integer, parameter :: jds = 1, jde = 1, jms = 1, jme = 1, jts = 1, jte = 1
  integer, parameter :: kds = 1, kde = nz, kms = 1, kme = nz, kts = 1, kte = nz
  real(wp), dimension(1, nz, 1) :: qv, t, p, w, dz, qc, qr, qi, qs, qg, ni, nr, ng, qb
  real(wp), dimension(nz) :: klev, qv_in, qc_in, qr_in, qi_in, qs_in, qg_in, ni_in, nr_in, nc_in, nwfa_in, &
    nifa_in, theta_in, ng_in, volg_in, p_in, w_in, dz_in, md
  type(ty_tempo_cfgs) :: cfgs
  type(ty_tempo_driver_diags) :: diags
  real(wp) :: dt, w0, w1, pr, res, sres, sabs, smax, sprec
  integer :: steps, semi, n, k, io
  character(len=32) :: arg

  call get_command_argument(1, arg); read(arg, *) dt
  call get_command_argument(2, arg); read(arg, *) steps
  call get_command_argument(3, arg); read(arg, *) semi

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

  cfgs%semi_sedi_flag = (semi == 1)
  call tempo_init(tempo_cfgs=cfgs)

  sres = 0._wp; sabs = 0._wp; smax = 0._wp; sprec = 0._wp
  do n = 1, steps
    md = roverrv*p(1,:,1)/(rdry*t(1,:,1)*(max(min_qv, qv(1,:,1))+roverrv))*dz(1,:,1)
    w0 = sum((qv(1,:,1)+qc(1,:,1)+qr(1,:,1)+qi(1,:,1)+qs(1,:,1)+qg(1,:,1))*md)
    call tempo_run(tempo_cfgs=cfgs, itimestep=n, dt=dt, &
      ids=ids, ide=ide, ims=ims, ime=ime, its=its, ite=ite, jds=jds, jde=jde, jms=jms, jme=jme, &
      jts=jts, jte=jte, kds=kds, kde=kde, kms=kms, kme=kme, kts=kts, kte=kte, &
      t=t, p=p, w=w, dz=dz, qv=qv, qc=qc, qr=qr, qi=qi, qs=qs, qg=qg, ni=ni, nr=nr, ng=ng, qb=qb, &
      tempo_diags=diags)
    w1 = sum((qv(1,:,1)+qc(1,:,1)+qr(1,:,1)+qi(1,:,1)+qs(1,:,1)+qg(1,:,1))*md)
    pr = diags%rain_precip(1,1) + diags%ice_liquid_equiv_precip(1,1) + diags%snow_liquid_equiv_precip(1,1) + &
      diags%graupel_liquid_equiv_precip(1,1)
    res = w1 - w0 + pr
    sres = sres + res; sabs = sabs + abs(res); smax = max(smax, abs(res)); sprec = sprec + pr
  enddo
  write(*, '(a,f6.1,a,i5,a,i2,a,es12.4,a,es12.4,a,es12.4,a,es12.4,a,es12.4)') 'dt=', dt, ' steps=', steps, &
    ' semi=', semi, ' P=', sprec, ' sum_res=', sres, ' sum_abs=', sabs, ' max_step=', smax, ' res/P=', sres/max(sprec, 1.e-30_wp)
end program water_closure_test
