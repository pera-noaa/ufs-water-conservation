! NM12 single-column harness: drives the final tree's real noahmpdrv_run on im independent columns.
! Modes (namelist &nm12 on stdin):
!   'single' : one call per column from random states (kind = 'built' melt-out packs or 'random' NM11-like)
!   'season' : nsteps calls per column with a synthetic melt season (diurnal SW, warming air, random storms)
! Per column per step: water meter errW = dW_storage - (P - ET - R)*dt, ground ice, firing meter.
! Output: <out>.cols (per column summary), <out>.ev (per firing), <out>.state (binary end state).
program nm12_main
  use machine, only: kind_phys
  use hv_mod
#ifndef PRISTINE
  use module_sf_noahmplsm, only: nm12_fire, nm12_liq, nm12_ice, nm12_sneqv
  use noahmp_glacier_globals, only: nm12g_fire, nm12g_liq, nm12g_ice, nm12g_sneqv
#endif
  use noahmpdrv, only: noahmpdrv_init, noahmpdrv_run
  use funcphys, only: gpvs
  use noahmp_tables, only: isice_table
  implicit none
#ifdef PRISTINE
  integer, allocatable :: nm12_fire(:), nm12g_fire(:)
  real(kind_phys), allocatable :: nm12_liq(:), nm12_ice(:), nm12_sneqv(:), nm12g_liq(:), nm12g_ice(:), nm12g_sneqv(:)
#endif

  character(len=16)  :: mode = 'single', kind = 'built'
  character(len=256) :: out = 'run'
  integer :: ncol = 1000, nsteps = 1, seed = 1, glacier = 0
  real(kind_phys) :: dt = 720., lat0 = 45.
  namelist /nm12/ mode, kind, out, ncol, nsteps, seed, dt, glacier, lat0

  real(kind_phys), parameter :: tfrz = 273.16, hfus = 3.3358e5, pi = 3.14159265358979
  real(kind_phys), parameter :: dzs(4) = (/0.1, 0.3, 0.6, 1.0/)
  real(kind_phys), allocatable :: pores(:), resid(:)
  real(kind_phys), allocatable :: wbeg(:), wend(:), pin(:), etout(:), rout(:), errw(:), ice(:)
  real(kind_phys), allocatable :: sum_errw(:), max_errw(:), sum_abserrw(:), sum_p(:), sum_et(:), sum_r(:)
  real(kind_phys), allocatable :: weasd_b(:), weasd0(:), melt_day(:), sum_firel(:), sum_firei(:), sum_fires(:)
  integer, allocatable :: nfire(:), nfireg(:), nsnowsteps(:), nlay0(:)
  ! season forcing per column
  real(kind_phys), allocatable :: tbase(:), twarm(:), swmax(:), pstorm(:), prate(:), tamp(:)
  integer :: i, k, n, ios, u
  real(kind_phys) :: hour, doy, decl, cz, r, ta, frs, fliq
  character(len=512) :: msg
  integer :: flg

  read(*, nml=nm12, iostat=ios)
  if (ios /= 0) stop 'bad namelist'
  call random_init_seed(seed)

  im = ncol; km = 4; lsnowl = -2; itime = 0
  call hv_alloc()
  allocate(pores(30), resid(30))
  call noahmpdrv_init(2, 2, 0, 1, 1, 99, pores, resid, .false., .false., msg, flg)
  if (flg /= 0) then
    print *, trim(msg); stop 1
  end if
  call gpvs()

  allocate(nm12_fire(im), nm12_liq(im), nm12_ice(im), nm12_sneqv(im))
  allocate(nm12g_fire(im), nm12g_liq(im), nm12g_ice(im), nm12g_sneqv(im))
  allocate(wbeg(im), wend(im), pin(im), etout(im), rout(im), errw(im), ice(im))
  allocate(sum_errw(im), max_errw(im), sum_abserrw(im), sum_p(im), sum_et(im), sum_r(im))
  allocate(weasd_b(im), weasd0(im), melt_day(im), sum_firel(im), sum_firei(im), sum_fires(im))
  allocate(nfire(im), nfireg(im), nsnowsteps(im), nlay0(im))
  allocate(tbase(im), twarm(im), swmax(im), pstorm(im), prate(im), tamp(im))
  sum_errw = 0.; max_errw = 0.; sum_abserrw = 0.; sum_p = 0.; sum_et = 0.; sum_r = 0.
  sum_firel = 0.; sum_firei = 0.; sum_fires = 0.; nfire = 0; nfireg = 0; nsnowsteps = 0
  melt_day = -1.

  ! constants (physcons values)
  con_g = 9.80665; con_hvap = 2.5e6; con_cp = 1004.6; con_jcal = 4.1855; rhoh2o = 1000.
  con_rd = 287.05; con_eps = 287.05/461.50; con_epsm1 = con_eps - 1.; con_fvirt = 461.50/287.05 - 1.
  con_hfus = 3.3358e5
  thsfc_loc = .true.; cpllnd = .false.; cpllnd2atm = .false.; do_mynnsfclay = .false.
  ! UFS RT options (tests/default_vars.sh)
  idveg = 4; iopt_crs = 2; iopt_btr = 1; iopt_run = 1; iopt_sfc = 3; iopt_frz = 1; iopt_inf = 1
  iopt_rad = 3; iopt_alb = 1; iopt_snf = 4; iopt_tbot = 2; iopt_stc = 3; iopt_trs = 2; iopt_diag = 2
  iyrlen = 365; delt = dt

  call init_columns()
  do i = 1, im
    weasd0(i) = weasd(i); nlay0(i) = -nint(snowxy(i))
  end do

  open(newunit=u, file=trim(out)//'.ev', status='replace')
  write(u, '(a)') '# col step isnow0 weasd_in liq_fire ice_fire sneqv_fire errw_step ice_after weasd_after nlay_after'
  do n = 1, nsteps
    doy = 60. + (n-1)*dt/86400.
    hour = mod((n-1)*dt, 86400.d0)/3600.
    julian = doy
    do i = 1, im
      if (mode == 'season') call season_forcing(i, n, doy, hour)
    end do
    nm12_fire = 0; nm12_liq = 0.; nm12_ice = 0.; nm12_sneqv = 0.
    nm12g_fire = 0; nm12g_liq = 0.; nm12g_ice = 0.; nm12g_sneqv = 0.
    do i = 1, im
      wbeg(i) = storage(i); weasd_b(i) = weasd(i)
      nlay0(i) = -nint(snowxy(i))
    end do
#include "hv_call.inc"
    if (errflg /= 0) then
      print *, 'errflg ', trim(errmsg); stop 2
    end if
    do i = 1, im
      wend(i) = storage(i)
      pin(i) = (rainc_mp(i) + rainn_mp(i))*dt
      if (vegtype(i) == isice_table) pin(i) = tprcp(i)*1000.
      etout(i) = (ecan(i) + etran(i) + edir(i))*dt
      rout(i) = (runoff(i) + drain(i))*dt
      errw(i) = (wend(i) - wbeg(i)) - (pin(i) - etout(i) - rout(i))
      ice(i) = groundice(i)
      sum_errw(i) = sum_errw(i) + errw(i); sum_abserrw(i) = sum_abserrw(i) + abs(errw(i))
      max_errw(i) = max(max_errw(i), abs(errw(i)))
      sum_p(i) = sum_p(i) + pin(i); sum_et(i) = sum_et(i) + etout(i); sum_r(i) = sum_r(i) + rout(i)
      if (weasd(i) > 0.) nsnowsteps(i) = nsnowsteps(i) + 1
      if (weasd(i) <= 0. .and. melt_day(i) < 0. .and. weasd0(i) > 0.) melt_day(i) = doy
      if (nm12_fire(i) + nm12g_fire(i) > 0) then
        nfire(i) = nfire(i) + nm12_fire(i); nfireg(i) = nfireg(i) + nm12g_fire(i)
        sum_firel(i) = sum_firel(i) + nm12_liq(i) + nm12g_liq(i)
        sum_firei(i) = sum_firei(i) + nm12_ice(i) + nm12g_ice(i)
        sum_fires(i) = sum_fires(i) + nm12_sneqv(i) + nm12g_sneqv(i)
        write(u, '(i8,i7,i3,8es14.6)') i, n, nlay0(i), weasd_b(i), nm12_liq(i)+nm12g_liq(i), &
             nm12_ice(i)+nm12g_ice(i), nm12_sneqv(i)+nm12g_sneqv(i), errw(i), ice(i), weasd(i), -snowxy(i)
      end if
    end do
  end do
  close(u)

  open(newunit=u, file=trim(out)//'.cols', status='replace')
  write(u, '(a)') '# col veg soil isnow_init weasd_init nfire nfireg sum_errw max_abs_errw sum_abs_errw sumP sumET sumR' // &
                  ' weasd_end ice_end snowsteps melt_day fire_liq fire_ice fire_sneqv'
  do i = 1, im
    write(u, '(i8,3i4,es14.6,2i6,8es14.6,i8,4es14.6)') i, vegtype(i), soiltyp(i), 0, weasd0(i), nfire(i), nfireg(i), &
       sum_errw(i), max_errw(i), sum_abserrw(i), sum_p(i), sum_et(i), sum_r(i), weasd(i), ice(i), &
       nsnowsteps(i), melt_day(i), sum_firel(i), sum_firei(i), sum_fires(i)
  end do
  close(u)

  ! binary end state: every in/out state field, for bitwise comparison between variants
  open(newunit=u, file=trim(out)//'.state', form='unformatted', access='stream', status='replace')
  write(u) weasd, snwdph, tskin, smc, stc, slc, canopy, snowxy, tvxy, tgxy, canicexy, canliqxy, eahxy, tahxy, &
           tsnoxy, zsnsoxy, snicexy, snliqxy, waxy, wtxy, zwtxy, taussxy, alboldxy, sneqvoxy, qsnowxy, &
           gflux, hflx, evap, runoff, drain, ecan, etran, edir, sncovr1, qsurf, sum_errw, ice
  close(u)
  write(*, '(a,i9,a,i9,a,i9)') 'columns ', im, ' firings(lsm) ', sum(nfire), ' firings(glacier) ', sum(nfireg)
  write(*, '(a,es12.4,a,es12.4)') 'sum errw all cols [mm] ', sum(sum_errw), '  max |errw| step [mm] ', maxval(max_errw)
  write(*, '(a,es12.4)') 'sum errw firing cols [mm] ', sum(sum_errw, mask=(nfire+nfireg) > 0)
  write(*, '(a,es12.4)') 'max |errw| non-firing cols [mm] ', maxval(max_errw, mask=(nfire+nfireg) == 0)

contains

  subroutine random_init_seed(s)
    integer, intent(in) :: s
    integer :: nseed
    integer, allocatable :: sd(:)
    call random_seed(size=nseed)
    allocate(sd(nseed)); sd = s*7919 + (/(k*104729, k=1, nseed)/)
    call random_seed(put=sd)
  end subroutine

  real(kind_phys) function urand(a, b)
    real(kind_phys), intent(in) :: a, b
    real(kind_phys) :: x
    call random_number(x); urand = a + (b-a)*x
  end function

  real(kind_phys) function storage_soil(i)
    integer, intent(in) :: i
    storage_soil = sum(smc(i,:)*dzs)*1000. + waxy(i)
  end function

  real(kind_phys) function storage(i)
    integer, intent(in) :: i
    storage = weasd(i) + canicexy(i) + canliqxy(i) + storage_soil(i)
  end function

  real(kind_phys) function groundice(i)
    ! snow ice (layers, or bulk snow when unlayered) + soil ice [mm]
    integer, intent(in) :: i
    integer :: ns
    ns = nint(snowxy(i))
    if (ns < 0) then
      groundice = sum(snicexy(i, ns+1:0))
    else
      groundice = weasd(i)
    end if
    groundice = groundice + sum((smc(i,:) - slc(i,:))*dzs)*1000.
  end function

  subroutine set_pack(i, nl, dz, dens, fl, tsn)
    ! nl layers (top first in dz(1:nl)), density [kg/m3], liquid mass fraction fl, temperature tsn
    integer, intent(in) :: i, nl
    real(kind_phys), intent(in) :: dz(3), dens, fl, tsn
    integer :: j, l
    real(kind_phys) :: z, m
    snicexy(i,:) = 0.; snliqxy(i,:) = 0.; tsnoxy(i,:) = 0.; zsnsoxy(i,:) = 0.
    z = 0.
    do l = 1, nl
      j = -nl + l
      m = dz(l)*dens
      snicexy(i,j) = m*(1.-fl); snliqxy(i,j) = m*fl
      tsnoxy(i,j) = tsn
      z = z - dz(l); zsnsoxy(i,j) = z
    end do
    do k = 1, 4
      zsnsoxy(i,k) = z - sum(dzs(1:k))
    end do
    snowxy(i) = -nl
    weasd(i) = sum(snicexy(i,:)) + sum(snliqxy(i,:))
    snwdph(i) = -z*1000.
    if (nl == 0) then
      weasd(i) = 0.; snwdph(i) = 0.
    end if
  end subroutine

  subroutine init_columns()
    integer :: nl, j
    real(kind_phys) :: dz(3), dens, fl, tsn, depth, qs, es, sw, p, fsnow
    do i = 1, im
      ! land surface type
      vegtype(i) = 1 + int(urand(0.d0, 19.999d0))
      if (vegtype(i) == 15 .or. vegtype(i) == 17) vegtype(i) = 10
      if (glacier == 1) vegtype(i) = 15
      soiltyp(i) = 1 + int(urand(0.d0, 11.999d0))
      soilcol(i) = 4; slopetyp(i) = 1
      sigmaf(i) = urand(0.05d0, 0.8d0); shdmin(i) = 0.01; shdmax(i) = max(sigmaf(i), 0.5)
      snoalb(i) = 0.7; sfalb(i) = 0.3
      dry(i) = .true.; flag_iter(i) = .true.
      xlatin(i) = urand(30.d0, 65.d0)*pi/180.
      garea(i) = 1.e10; rhonewsn1(i) = 100.
      ! soil
      do k = 1, 4
        stc(i,k) = urand(272.d0, 278.d0)
        smc(i,k) = urand(0.15d0, 0.40d0)
        slc(i,k) = smc(i,k)
        if (stc(i,k) < tfrz) slc(i,k) = smc(i,k)*urand(0.2d0, 1.d0)
        smoiseq(i,k) = 0.3
        if (glacier == 1) then
          smc(i,k) = 1.; slc(i,k) = 0.; stc(i,k) = urand(258.d0, 272.d0)
        end if
      end do
      tg3(i) = urand(276.d0, 283.d0)
      ! snow pack
      select case (trim(kind))
      case ('built', 'built1')
        ! a 2- or 3-layer ripe pack, thin enough to melt out in one step ('built1': one layer)
        nl = 2 + int(urand(0.d0, 1.999d0))
        if (trim(kind) == 'built1') nl = 1
        do j = 1, 3
          dz(j) = urand(0.026d0, 0.06d0)
        end do
        dens = urand(60.d0, 250.d0); fl = urand(0.d0, 0.1d0); tsn = tfrz
      case ('wet')
        ! red team only: 2-3 layers holding <= 0.5 mm ice each and mostly liquid, so any melt empties them
        nl = 2 + int(urand(0.d0, 1.999d0))
        do j = 1, 3
          dz(j) = urand(0.026d0, 0.04d0)
        end do
        dens = urand(5.d0, 40.d0); fl = urand(0.5d0, 0.98d0); tsn = tfrz
      case default
        ! NM11-like: anything from bare ground to a deep cold pack
        nl = int(urand(0.d0, 3.999d0))
        depth = urand(0.d0, 1.d0)**2*1.5
        do j = 1, 3
          dz(j) = max(0.026d0, depth/max(nl, 1))
        end do
        dens = urand(60.d0, 450.d0); fl = urand(0.d0, 0.08d0); tsn = urand(255.d0, tfrz)
        if (urand(0.d0, 1.d0) < 0.5) tsn = tfrz
      end select
      call set_pack(i, nl, dz, dens, fl, tsn)
      ! canopy, vegetation, groundwater
      tvxy(i) = 274.; tgxy(i) = 273.5; tahxy(i) = 274.; eahxy(i) = 700.; cmxy(i) = 0.01; chxy(i) = 0.01
      fwetxy(i) = 0.; canicexy(i) = 0.; canliqxy(i) = urand(0.d0, 0.3d0)
      sneqvoxy(i) = weasd(i); alboldxy(i) = 0.65; qsnowxy(i) = 0.; wslakexy(i) = 0.
      zwtxy(i) = 2.5; waxy(i) = 4900.; wtxy(i) = 4900.
      if (glacier == 1) then
        canliqxy(i) = 0.; waxy(i) = 0.; wtxy(i) = 0.   ! the driver zeroes these on land ice
      end if
      lfmassxy(i) = 50.; rtmassxy(i) = 500.; stmassxy(i) = 50.; woodxy(i) = 500.
      stblcpxy(i) = 1000.; fastcpxy(i) = 1000.; xlaixy(i) = urand(0.5d0, 3.d0); xsaixy(i) = 0.3; taussxy(i) = 0.
      smcwtdxy(i) = 0.3; deeprechxy(i) = 0.; rechxy(i) = 0.
      tskin(i) = 274.; tsurf(i) = 274.; zorl(i) = 10.; canopy(i) = canliqxy(i); trans(i) = 0.
      rb1(i) = 0.; fm1(i) = 10.; fh1(i) = 10.; ustar1(i) = 0.3; stress1(i) = 0.1; fm101(i) = 8.; fh21(i) = 6.
      rmol1(i) = 0.; flhc1(i) = 0.; flqc1(i) = 0.
      cm(i) = 0.004; ch(i) = 0.004
      ! single-call forcing: warm, sunny or rainy
      ps(i) = 1.e5; prsl1(i) = 99000.; zf(i) = 10.; pblh(i) = 1000.
      prslk1(i) = (prsl1(i)/1.e5)**0.2857; prsik1(i) = (ps(i)/1.e5)**0.2857; prslki(i) = prsik1(i)/prslk1(i)
      u1(i) = urand(1.d0, 10.d0); v1(i) = urand(-2.d0, 2.d0); wind(i) = sqrt(u1(i)**2 + v1(i)**2)
      if (trim(kind) /= 'random') then
        ta = urand(274.d0, 292.d0); sw = urand(0.d0, 1000.d0)
      else
        ta = urand(255.d0, 292.d0); sw = urand(0.d0, 1000.d0)
      end if
      t1(i) = ta
      es = 611.2*exp(17.67*(ta-273.15)/(ta-29.65)); qs = con_eps*es/(prsl1(i) + con_epsm1*es)
      q1(i) = qs*urand(0.5d0, 1.d0)
      dswsfc(i) = sw; snet(i) = 0.5*sw; xcoszin(i) = max(0.05d0, sw/1100.)
      dlwflx(i) = urand(250.d0, 360.d0)
      p = 0.; fsnow = 0.
      if (urand(0.d0, 1.d0) < 0.5) then
        p = urand(0.d0, 1.d0)**2*20./3600.               ! up to 20 mm/h
        fsnow = 0.
        if (urand(0.d0, 1.d0) < 0.3) fsnow = urand(0.d0, 1.d0)
        if (ta < 273.) fsnow = 1.
      end if
      call set_precip(i, p, fsnow)
    end do
  end subroutine

  subroutine set_precip(i, p, fsnow)
    integer, intent(in) :: i
    real(kind_phys), intent(in) :: p, fsnow
    rainn_mp(i) = p; rainc_mp(i) = 0.; snow_mp(i) = p*fsnow; graupel_mp(i) = 0.; ice_mp(i) = 0.
    tprcp(i) = p*dt/1000.; srflag(i) = fsnow
  end subroutine

  subroutine season_forcing(i, n, doy, hour)
    ! 120-day melt season: air T base + warming trend + diurnal cycle; random storms (rain or snow by T)
    integer, intent(in) :: i, n
    real(kind_phys), intent(in) :: doy, hour
    real(kind_phys) :: es, qs, decl, h, cz, p, fsnow
    if (n == 1) then
      tbase(i) = urand(258.d0, 270.d0); twarm(i) = urand(12.d0, 25.d0); tamp(i) = urand(3.d0, 9.d0)
      swmax(i) = urand(0.6d0, 0.85d0); pstorm(i) = urand(0.01d0, 0.05d0); prate(i) = urand(0.5d0, 6.d0)/3600.
    end if
    decl = 23.45*pi/180.*sin(2.*pi*(284.+doy)/365.)
    h = (hour - 12.)*15.*pi/180.
    cz = sin(xlatin(i))*sin(decl) + cos(xlatin(i))*cos(decl)*cos(h)
    xcoszin(i) = max(cz, 0.d0)
    dswsfc(i) = 1361.*swmax(i)*max(cz, 0.d0)
    snet(i) = 0.4*dswsfc(i)
    t1(i) = tbase(i) + twarm(i)*(doy - 60.)/120. + tamp(i)*sin(2.*pi*(hour - 9.)/24.)
    dlwflx(i) = 0.75*5.67e-8*t1(i)**4
    es = 611.2*exp(17.67*(t1(i)-273.15)/(t1(i)-29.65)); qs = con_eps*es/(prsl1(i) + con_epsm1*es)
    q1(i) = 0.7*qs
    u1(i) = 4.; v1(i) = 1.; wind(i) = sqrt(17.)
    ! storms: start with probability pstorm per hour-equivalent, last until a coin flip ends them
    p = 0.; fsnow = 0.
    if (urand(0.d0, 1.d0) < pstorm(i)*dt/3600.*6.) then
      p = prate(i)*urand(0.2d0, 2.d0)
      fsnow = 0.
      if (t1(i) < 274.15) fsnow = 1.
      dlwflx(i) = 5.67e-8*t1(i)**4; dswsfc(i) = 0.3*dswsfc(i)
    end if
    call set_precip(i, p, fsnow)
  end subroutine

end program nm12_main
