! Calls the real GFDL MP v3 CCPP wrapper on convective columns; reports host water closure and writes the outputs
program test_gmp
  use machine, only: kind_phys
  use gfdl_cloud_microphys_v3_mod, only: gfdl_cloud_microphys_v3_mod_init
  use gfdl_cloud_microphys_v3, only: gfdl_cloud_microphys_v3_run
  implicit none
  integer, parameter :: im = 16, levs = 64, ntr = 9
  real(kind_phys), parameter :: g = 9.80665, rd = 287.05, fvirt = 461.50/287.05 - 1., eps = 287.05/461.50
  real(kind_phys), dimension(im) :: garea, slmsk, snowd, oro, rain0, ice0, snow0, graupel0, prcp0, sr
  real(kind_phys), dimension(im,levs) :: qv, ql, qr, qi, qs, qg, qa, t, u, v, vvl, prsl, del, refl
  real(kind_phys), dimension(im,levs) :: tt, tu, tv, tqv, tql, tqr, tqi, tqs, tqg, tqa, rew, rei, rer, res, reg, pfi, pfl
  real(kind_phys), dimension(im,levs+1) :: prsi, phii
  real(kind_phys) :: aer(im,levs,15), tq(im,levs,ntr), w0(im), w1(im), es, z, dtp
  character(len=1) :: nmlfile(1)
  character(len=64) :: fn
  character(len=512) :: msg
  integer :: i, k, err, step
  fn = 'input.nml'; nmlfile = ' '
  call gfdl_cloud_microphys_v3_mod_init(0, 0, 10, nmlfile, 6, fn, .false., msg, err)
  if (err /= 0) stop 'init'
  dtp = 225.
  do i = 1, im
     prsi(i,1) = 100000.
     do k = 1, levs
        prsi(i,k+1) = 100000. - (100000. - 1000.)*k/levs
     enddo
     phii(i,1) = 0.
     do k = 1, levs
        del(i,k)  = prsi(i,k) - prsi(i,k+1)
        prsl(i,k) = 0.5*(prsi(i,k) + prsi(i,k+1))
        z = rd*288./g*log(1.e5/prsl(i,k))
        t(i,k) = max(205., 300. - 2.*i/im*3. - 0.0065*z)
        es = 611.2*exp(17.67*(t(i,k)-273.15)/(t(i,k)-29.65))
        qv(i,k) = eps*es/prsl(i,k)*(1.02 - 0.3*mod(k+i,3)/3.)
        ql(i,k) = merge(4.e-4, 0., t(i,k) > 255. .and. t(i,k) < 290.)
        qi(i,k) = merge(2.e-4, 0., t(i,k) < 265.)
        qr(i,k) = merge(1.e-3*i/im, 0., z > 2000. .and. z < 6000.)
        qs(i,k) = merge(1.e-3, 0., z > 4000. .and. z < 8000.)
        qg(i,k) = merge(1.e-3, 0., z > 3000. .and. z < 7000. .and. mod(i,2) == 0)
        qa(i,k) = merge(1., 0., ql(i,k) + qi(i,k) > 0.)
        u(i,k) = 10.; v(i,k) = 0.; vvl(i,k) = -2.*sin(3.14159*k/levs)
        phii(i,k+1) = phii(i,k) + rd*t(i,k)*(1. + fvirt*qv(i,k))*log(prsi(i,k)/prsi(i,k+1))
     enddo
  enddo
  garea = 1.e8; slmsk = 1.; snowd = 0.; oro = 0.; aer = 1.e-9
  w0 = water(qv, ql, qr, qi, qs, qg)
  w1 = 0.
  do step = 1, 32
     call gfdl_cloud_microphys_v3_run(.false., levs, im, 1.e-13_kind_phys, g, fvirt, rd, eps, garea, slmsk, snowd, &
        qv, ql, qr, qi, qs, qg, qa, aer, t, u, v, vvl, prsl, phii, del, &
        rain0, ice0, snow0, graupel0, prcp0, sr, oro, dtp, .false., .false., refl, &
        .false., .false., rew, rei, rer, res, reg, .false., pfi, pfl, 1._kind_phys, 0.001_kind_phys, 86400._kind_phys, &
        tt, tu, tv, tqv, tql, tqr, tqi, tqs, tqg, tqa, tq, msg, err)
     if (err /= 0) stop 'run'
     qv = qv + tqv*dtp; ql = ql + tql*dtp; qr = qr + tqr*dtp; qi = qi + tqi*dtp
     qs = qs + tqs*dtp; qg = qg + tqg*dtp; qa = qa + tqa*dtp; t = t + tt*dtp
     w1 = w1 + prcp0*1000.
  enddo
  w1 = w1 + water(qv, ql, qr, qi, qs, qg)
  print '(a,es11.3,a,es11.3,a)', 'precip ', sum(w1 - water(qv,ql,qr,qi,qs,qg))/im, ' kg/m2; residual (after + precip - before) max |.| ', &
        maxval(abs(w1 - w0)), ' kg/m2'
  print '(a,es11.3)', 'residual / precip ', sum(w1 - w0)/sum(w1 - water(qv,ql,qr,qi,qs,qg))
  open (20, file = 'out.bin', form = 'unformatted', access = 'stream', status = 'replace')
  write (20) qv, ql, qr, qi, qs, qg, t, w1 - water(qv,ql,qr,qi,qs,qg)
  close (20)
contains
  function water(qv, ql, qr, qi, qs, qg) result(w)
    real(kind_phys), dimension(im,levs), intent(in) :: qv, ql, qr, qi, qs, qg
    real(kind_phys) :: w(im)
    w = sum((qv + ql + qr + qi + qs + qg)*del, dim = 2)/g
  end function water
end program test_gmp
