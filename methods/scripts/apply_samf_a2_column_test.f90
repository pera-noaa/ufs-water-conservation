! Single-column water closure of v1 SAMF deep (samfdeepcnv_run, one 720 s call) on synthetic tropical-ocean columns.
! Build/run: apply_samf_a2_column_test.sh <samfdeepcnv.f> <dir with v1 machine/physcons/funcphys/progsigma/samfaerosols .mod>
! Per column: kb, jmin, rain, and R = [W(after) - W(before)] + rain (kg/m2), W = sum (q1 + qtr(:,:,1:2))*delp/g;
! R = 0 to round-off when the scheme conserves water. A passive tracer (qtr(:,:,3), ntr = 1) is checked the same way.
program apply_samf_a2_column_test
  use machine, only: kind_phys
  use funcphys, only: gpvs, fpvs
  use samfdeepcnv, only: samfdeepcnv_run
  implicit none
  integer, parameter :: im = 6, km = 64, ntr = 1, nq = ntr + 2
  real(kind_phys), parameter :: g = 9.80665_kind_phys, cp = 1004.6_kind_phys, hvap = 2.5e6_kind_phys, &
       rd = 287.05_kind_phys, rv = 461.50_kind_phys, cliq = 4185.5_kind_phys, cvap = 1846.0_kind_phys, &
       t0c = 273.15_kind_phys, eps = rd/rv, epsm1 = rd/rv - 1._kind_phys, fv = rv/rd - 1._kind_phys
  real(kind_phys) :: delt = 720._kind_phys
  real(kind_phys), dimension(im,km) :: delp, prslp, phil, q1, t1, u1, v1, dot, ud_mf, dd_mf, dt_mf, cnvw, cnvc, &
       qlcn, qicn, w_upi, cnv_mfd, cnv_dqldt, clcn, cnv_fice, cnv_ndrop, cnv_nice, cf_upi, sigmain, sigmaout, &
       qmicro, q, prevsq
  real(kind_phys) :: tmf(im,km,nq), qtr(im,km,nq), pi(km+1), q0(im,km), qtr0(im,km,nq)
  real(kind_phys), dimension(im) :: psp, garea, hpbl, cldwrk, rn, rainevap, ca_deep, maxmf
  real(kind_phys) :: xlon(im), xlat(im)
  real(kind_phys) :: fscav(1), w0, w1, c0, c1v, z, tt, es, qs, rh
  integer :: islimsk(im), kcnv(im), kbot(im), ktop(im), i, k, errflg
  character(len=128) :: errmsg

  call gpvs()
  do k = 1, km + 1                       ! interfaces: 1010 hPa to ~5 hPa, finer near the surface
     pi(k) = 101000._kind_phys * (1._kind_phys - real(k-1, kind_phys)/real(km, kind_phys))**1.6_kind_phys + 500._kind_phys &
             * real(k-1, kind_phys)/real(km, kind_phys)
  enddo
  do i = 1, im
     psp(i) = pi(1)
     z = 0._kind_phys
     do k = 1, km
        delp(i,k) = pi(k) - pi(k+1)
        prslp(i,k) = 0.5_kind_phys*(pi(k) + pi(k+1))
        tt = max(195._kind_phys, (301._kind_phys - 0.6_kind_phys*mod(i-1,3)) * (prslp(i,k)/psp(i))**0.19_kind_phys)
        rh = max(0.05_kind_phys, (0.92_kind_phys - 0.02_kind_phys*mod(i-1,3)) * (prslp(i,k)/psp(i))**1.5_kind_phys)
        es = min(fpvs(tt), prslp(i,k))
        qs = eps*es/(prslp(i,k) + epsm1*es)
        t1(i,k) = tt
        q1(i,k) = rh*qs
        if (i >= 4 .and. i <= 5 .and. mod(k,2) == 0 .and. k < 30) q1(i,k) = q1(i,k)*(1._kind_phys - 0.08_kind_phys*(i-3))  ! jagged
        if (i == 6 .and. k == 2) q1(i,k) = q1(i,k)*0.85_kind_phys                                         ! dry layer 2
        phil(i,k) = z + rd*tt*(1._kind_phys + fv*q1(i,k))*log(pi(k)/prslp(i,k))
        z = z + rd*tt*(1._kind_phys + fv*q1(i,k))*log(pi(k)/pi(k+1))
        dot(i,k) = -0.6_kind_phys*sin(3.14159265_kind_phys*min(1._kind_phys, (psp(i)-prslp(i,k))/85000._kind_phys))
     enddo
  enddo
  u1 = 5._kind_phys; v1 = 0._kind_phys
  qtr = 0._kind_phys
  qtr(:,:,3) = 400.e-6_kind_phys; qtr(:,1:3,3) = 420.e-6_kind_phys            ! passive tracer, higher at the surface
  do k = 1, km
     qtr(:,k,3) = qtr(:,k,3) + 2.e-6_kind_phys*mod(k,3)
  enddo
  garea = 1.0e10_kind_phys; hpbl = 700._kind_phys; islimsk = 0
  tmf = 0._kind_phys; qmicro = 0._kind_phys; q = q1; prevsq = 0._kind_phys; sigmain = 0._kind_phys
  ca_deep = 0._kind_phys; maxmf = 1._kind_phys; fscav = 0._kind_phys; kcnv = 0; cnvw = 0._kind_phys; cnvc = 0._kind_phys
  q0 = q1; qtr0 = qtr
  xlon = 73._kind_phys/57.2957795_kind_phys; xlat = -12._kind_phys/57.2957795_kind_phys

  call samfdeepcnv_run(im, km, .false., .true., tmf, qmicro, 0, 0, cliq, cp, cvap, eps, epsm1, fv, g, hvap, rd, rv, &
       t0c, delt, 0, ntr, delp, prslp, psp, phil, qtr, prevsq, q, q1, t1, u1, v1, fscav, .false., .false., cldwrk, rn, &
       kbot, ktop, kcnv, islimsk, garea, dot, 1, hpbl, ud_mf, dd_mf, dt_mf, cnvw, cnvc, qlcn, qicn, w_upi, cf_upi, &
       cnv_mfd, cnv_dqldt, clcn, cnv_fice, cnv_ndrop, cnv_nice, 8, 10, 0.1_kind_phys, 0.002_kind_phys, 0.002_kind_phys, &
       0.05_kind_phys, 0.05_kind_phys, 0.3_kind_phys, 0.55_kind_phys, 0.958_kind_phys, .false., .false., .false., .false., &
       18._kind_phys, ca_deep, rainevap, sigmain, sigmaout, 0._kind_phys, 0._kind_phys, 0._kind_phys, maxmf, .false., &
#ifdef METERED
       1, xlon, xlat, &
#endif
       errmsg, errflg)
  if (errflg /= 0) print *, 'errflg ', errflg, trim(errmsg)

  do i = 1, im
     w0 = 0._kind_phys; w1 = 0._kind_phys; c0 = 0._kind_phys; c1v = 0._kind_phys
     do k = 1, km
        w0 = w0 + (q0(i,k) + qtr0(i,k,1) + qtr0(i,k,2))*delp(i,k)/g
        w1 = w1 + (q1(i,k) + qtr(i,k,1) + qtr(i,k,2))*delp(i,k)/g
        c0 = c0 + qtr0(i,k,3)*delp(i,k)/g
        c1v = c1v + qtr(i,k,3)*delp(i,k)/g
     enddo
     write(*,'(a,i2,a,i3,a,i3,a,es12.4,a,es12.4,a,es12.4,a,es12.4)') 'COL ', i, ' kcnv', kcnv(i), ' kbot', kbot(i), &
          ' rain(kg/m2) ', rn(i)*1000._kind_phys, ' R_water ', (w1 - w0) + rn(i)*1000._kind_phys, &
          ' R/rain ', ((w1 - w0) + rn(i)*1000._kind_phys)/max(rn(i)*1000._kind_phys, 1.e-30_kind_phys), &
          ' R_tracer ', c1v - c0
  enddo
end program apply_samf_a2_column_test
