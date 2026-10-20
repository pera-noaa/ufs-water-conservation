!> Tracer-mass meters (diagnostic builds only): Neumaier double-precision sums of q*dp*area per tracer.
!! Index 0 = air (sum dp*area), 1..nq = tracers, nq+1 = dry air. Units Pa m2. Not thread-safe (OMP_NUM_THREADS=1).
module tm_meter
  implicit none
  private
  public :: tm_nt, tm_np, tm_nslot, tm_pts, tm_acc, tm_neu, tm_dyn_rec, tm_phys_mass, tm_phys_add, &
            tm_pt_zero, tm_pt_add, tm_iu, tm_umax, tm_ucheck, tm_cfl, tm_cfl_deep, &
            tm_iud, tm_icnv, tm_c0, tm_dr, tm_drs, tm_dry_dyn, tm_dry_phys, tm_dry_slot, tm_osc, tm_osc_check, tm_cflh, &
            tm_samf_substep, tm_x
  integer, parameter :: tm_nt = 40, tm_np = 24, tm_nslot = 6
  real(8), save :: tm_pts(2, 0:tm_nt+1, tm_np) = 0.d0
  real(8), save :: tm_acc(2, 0:tm_nt+1, tm_nslot) = 0.d0
  integer, save :: tm_iu = 0                         ! index of the uniform moist test tracer (set by host)
  real(8), save :: tm_cfl(4) = 0.d0                  ! SAMF deep: max donor Courant, level, columns C>1, columns
  real(8), save :: tm_umax(4, tm_nslot) = 0.d0
  integer, save :: tm_iud = 0, tm_icnv = 0           ! indices of pt_udry, pt_cnv (set by host)
  real(8), parameter :: tm_c0 = 1.d-6                ! dry-uniform value
  real(8), save :: tm_dr(3, tm_np) = 0.d0            ! per point: sum D*dev^2, sum D, max|dev|; dev = c_dry/c0 - 1
  real(8), save :: tm_drs(2, tm_nslot) = 0.d0        ! per slot, this step: change of sum D*dev^2, max|dev| after
  real(8), save :: tm_osc(3, 4) = 0.d0               ! DCNV increments k=1..6 for qv, T, pt_umoist, pt_cnv:
                                                     !   columns alternating >=4 times, columns changed, max rel inc k<=5
  real(8), save :: tm_x(100) = 0.d0                 ! trsamf extra accumulators (summed over ranks, printed 'TX')
  real(8), save :: tm_cflh(7) = 0.d0                 ! column-steps by max Courant: <.5 <1 <2 <3 <4 <5 >=5       ! per slot, this step: max rel change, its level, count > 1%, count cells
contains
  pure subroutine tm_neu(s, x)
    real(8), intent(inout) :: s(2)
    real(8), intent(in) :: x
    real(8) :: t
    t = s(1) + x
    if (abs(s(1)) >= abs(x)) then
      s(2) = s(2) + ((s(1) - t) + x)
    else
      s(2) = s(2) + ((x - t) + s(1))
    endif
    s(1) = t
  end subroutine tm_neu

  !> dynamics frame: dp = delp, compute domain; stores rank sums at point ip
  subroutine tm_dyn_rec(ip, isd, jsd, is, ie, js, je, npz, nq, nwat, q, delp, area)
    integer, intent(in) :: ip, isd, jsd, is, ie, js, je, npz, nq, nwat
    real(8), intent(in) :: q(isd:, jsd:, :, :), delp(isd:, jsd:, :), area(isd:, jsd:)
    real(8) :: s(2, 0:nq+1), x
    integer :: i, j, k, m
    s = 0.d0
    do k = 1, npz
      do j = js, je
        do i = is, ie
          x = delp(i,j,k)*area(i,j)
          call tm_neu(s(:,0), x)
          call tm_neu(s(:,nq+1), delp(i,j,k)*(1.d0 - sum(q(i,j,k,1:nwat)))*area(i,j))
          do m = 1, nq
            call tm_neu(s(:,m), q(i,j,k,m)*x)
          enddo
        enddo
      enddo
    enddo
    tm_pts(:, 0:nq+1, ip) = s
    call tm_dry_dyn(ip, isd, jsd, is, ie, js, je, npz, nwat, q, delp, area)
  end subroutine tm_dyn_rec

  !> physics frame (k=1 at surface): dp = prsi(k) - prsi(k+1); dry = dp*(1 - qv)
  subroutine tm_phys_mass(im, levs, ntrac, gq0, prsi, area, s)
    integer, intent(in) :: im, levs, ntrac
    real(8), intent(in) :: gq0(:,:,:), prsi(:,:), area(:)
    real(8), intent(out) :: s(2, 0:ntrac+1)
    real(8) :: x
    integer :: i, k, m
    s = 0.d0
    do k = 1, levs
      do i = 1, im
        x = (prsi(i,k) - prsi(i,k+1))*area(i)
        call tm_neu(s(:,0), x)
        call tm_neu(s(:,ntrac+1), (prsi(i,k) - prsi(i,k+1))*(1.d0 - gq0(i,k,1))*area(i))
        do m = 1, ntrac
          call tm_neu(s(:,m), gq0(i,k,m)*x)
        enddo
      enddo
    enddo
  end subroutine tm_phys_mass

  !> cumulative physics change in slot: acc += s1 - s0
  subroutine tm_phys_add(slot, ntrac, s0, s1)
    integer, intent(in) :: slot, ntrac
    real(8), intent(in) :: s0(2, 0:ntrac+1), s1(2, 0:ntrac+1)
    integer :: m
    do m = 0, ntrac+1
      call tm_neu(tm_acc(:,m,slot), s1(1,m))
      call tm_neu(tm_acc(:,m,slot), s1(2,m))
      call tm_neu(tm_acc(:,m,slot), -s0(1,m))
      call tm_neu(tm_acc(:,m,slot), -s0(2,m))
    enddo
  end subroutine tm_phys_add

  subroutine tm_pt_zero(ip)
    integer, intent(in) :: ip
    tm_pts(:,:,ip) = 0.d0
  end subroutine tm_pt_zero

  !> point ip += s (block-wise accumulation of a physics-frame point)
  subroutine tm_pt_add(ip, n, s)
    integer, intent(in) :: ip, n
    real(8), intent(in) :: s(2, 0:n+1)
    integer :: m
    do m = 0, n+1
      call tm_neu(tm_pts(:,m,ip), s(1,m))
      call tm_neu(tm_pts(:,m,ip), s(2,m))
    enddo
  end subroutine tm_pt_add
  !> uniform-tracer check: relative change of tracer tm_iu between q0 (before) and gq0 (after) in slot
  subroutine tm_ucheck(slot, im, levs, q0, gq0)
    integer, intent(in) :: slot, im, levs
    real(8), intent(in) :: q0(:,:), gq0(:,:)
    real(8) :: r
    integer :: i, k
    do k = 1, levs
      do i = 1, im
        tm_umax(4,slot) = tm_umax(4,slot) + 1.d0
        if (q0(i,k) == 0.d0) cycle
        r = abs(gq0(i,k) - q0(i,k))/abs(q0(i,k))
        if (r > 0.01d0) tm_umax(3,slot) = tm_umax(3,slot) + 1.d0
        if (r > tm_umax(1,slot)) then
          tm_umax(1,slot) = r; tm_umax(2,slot) = k
        endif
      enddo
    enddo
  end subroutine tm_ucheck
  !> SAMF deep: donor-cell Courant number of the explicit environmental (TVD) flux, xmb*dt*g/dp*|net flux|
  subroutine tm_cfl_deep(im, km, cnvflg, kb, jmin, ktcon, eta, etad, edto, xmb, del, dt2)
    integer, intent(in) :: im, km, kb(:), jmin(:), ktcon(:)
    logical, intent(in) :: cnvflg(:)
    real(8), intent(in) :: eta(:,:), etad(:,:), edto(:), xmb(:), del(:,:), dt2
    real(8) :: tem, c, cmx
    integer :: i, k, kd
    do i = 1, im
      if (.not. cnvflg(i)) cycle
      tm_cfl(4) = tm_cfl(4) + 1.d0
      cmx = 0.d0
      do k = 1, ktcon(i) - 1
        tem = 0.d0
        if (k >= kb(i)) tem = eta(i,k)
        if (k <= jmin(i)) tem = tem - edto(i)*etad(i,k)
        kd = k
        if (tem > 0.d0) kd = k + 1
        c = abs(tem)*xmb(i)*dt2*9.80665d0/(1000.d0*del(i,kd))
        cmx = max(cmx, c)
        if (c > tm_cfl(1)) then
          tm_cfl(1) = c; tm_cfl(2) = kd
        endif
      enddo
      if (cmx > 1.d0) tm_cfl(3) = tm_cfl(3) + 1.d0
      if (cmx < 0.5d0) then
        tm_cflh(1) = tm_cflh(1) + 1.d0
      elseif (cmx < 1.d0) then
        tm_cflh(2) = tm_cflh(2) + 1.d0
      else
        k = min(7, 2 + int(cmx))
        tm_cflh(k) = tm_cflh(k) + 1.d0
      endif
    enddo
  end subroutine tm_cfl_deep
  !> dry-ratio stats, dynamics frame: D = delp*(1-sum water)*area, c = q/(1-sum water)
  subroutine tm_dry_dyn(ip, isd, jsd, is, ie, js, je, npz, nwat, q, delp, area)
    integer, intent(in) :: ip, isd, jsd, is, ie, js, je, npz, nwat
    real(8), intent(in) :: q(isd:, jsd:, :, :), delp(isd:, jsd:, :), area(isd:, jsd:)
    real(8) :: w, d, dev
    integer :: i, j, k
    tm_dr(:, ip) = 0.d0
    if (tm_iud <= 0) return
    do k = 1, npz
      do j = js, je
        do i = is, ie
          w = 1.d0 - sum(q(i,j,k,1:nwat))
          d = delp(i,j,k)*w*area(i,j)
          dev = q(i,j,k,tm_iud)/w/tm_c0 - 1.d0
          tm_dr(1,ip) = tm_dr(1,ip) + d*dev*dev
          tm_dr(2,ip) = tm_dr(2,ip) + d
          tm_dr(3,ip) = max(tm_dr(3,ip), abs(dev))
        enddo
      enddo
    enddo
  end subroutine tm_dry_dyn

  !> dry-ratio stats, physics frame: dry mass D = dp*(1 - qv_in) is fixed through the physics (as the write-back keeps it);
  !! c = tracer mass / D = qt/(1 - qv_in). Returns (sum D*dev^2, sum D, max|dev|).
  subroutine tm_dry_phys(im, levs, qt, qvin, prsi, area, r)
    integer, intent(in) :: im, levs
    real(8), intent(in) :: qt(:,:), qvin(:,:), prsi(:,:), area(:)
    real(8), intent(out) :: r(3)
    real(8) :: d, dev
    integer :: i, k
    r = 0.d0
    do k = 1, levs
      do i = 1, im
        d = (prsi(i,k) - prsi(i,k+1))*(1.d0 - qvin(i,k))*area(i)
        dev = qt(i,k)/(1.d0 - qvin(i,k))/tm_c0 - 1.d0
        r(1) = r(1) + d*dev*dev
        r(2) = r(2) + d
        r(3) = max(r(3), abs(dev))
      enddo
    enddo
  end subroutine tm_dry_phys

  subroutine tm_dry_slot(slot, r0, r1)
    integer, intent(in) :: slot
    real(8), intent(in) :: r0(3), r1(3)
    tm_drs(1,slot) = tm_drs(1,slot) + (r1(1) - r0(1))
    tm_drs(2,slot) = max(tm_drs(2,slot), r1(3))
  end subroutine tm_dry_slot

  !> DCNV increment shape in levels 1..6 (k=1 at surface): sign alternations and max relative increment
  subroutine tm_osc_check(iv, im, x0, x1)
    integer, intent(in) :: iv, im
    real(8), intent(in) :: x0(:,:), x1(:,:)
    real(8) :: inc(6), thr
    integer :: i, k, nalt
    do i = 1, im
      inc = x1(i,1:6) - x0(i,1:6)
      if (all(inc == 0.d0)) cycle
      tm_osc(2,iv) = tm_osc(2,iv) + 1.d0
      thr = 1.d-6*maxval(abs(x0(i,1:6)))
      nalt = 0
      do k = 1, 5
        if (abs(inc(k)) > thr .and. abs(inc(k+1)) > thr .and. inc(k)*inc(k+1) < 0.d0) nalt = nalt + 1
      enddo
      if (nalt >= 4) tm_osc(1,iv) = tm_osc(1,iv) + 1.d0
      do k = 1, 5
        if (x0(i,k) /= 0.d0) tm_osc(3,iv) = max(tm_osc(3,iv), abs(inc(k)/x0(i,k)))
      enddo
    enddo
  end subroutine tm_osc_check
  !> TEST ONLY: SAMF deep tracer update ctr += dellae*xmb*dt2 done in N = ceiling(max donor Courant) sub-steps per column,
  !! recomputing the environmental (TVD) and up/downdraft flux divergence from the current ctr each sub-step
  !! (updraft/downdraft tracer values ecko/ercko/ecdo held at their computed values). Replicates samfdeepcnv's
  !! generic-tracer dellae; on return dellae = 0 so the scheme's own single update adds nothing.
  subroutine tm_samf_substep(im, km, ntr, cnvflg, kb, jmin, ktcon, kmax, eta, etad, edto, ecko, ercko, ecdo, &
                             ctr, del, xmb, dt2, dellae, grav)
    integer, intent(in) :: im, km, ntr, kb(:), jmin(:), ktcon(:), kmax(:)
    logical, intent(in) :: cnvflg(:)
    real(8), intent(in) :: eta(:,:), etad(:,:), edto(:), ecko(:,:,:), ercko(:,:,:), ecdo(:,:,:), del(:,:), xmb(:), dt2, grav
    real(8), intent(inout) :: ctr(:,:,:), dellae(:,:,:)
    real(8) :: dl(km), flx(0:km), ed(0:km), cto(km), tem, tem1, tem2, ptem1, ptem2, rrkp, phkp, aup, adw, c, cmx, dp
    integer :: i, k, n, it, ns, kd
    do i = 1, im
      if (.not. cnvflg(i)) cycle
      cmx = 0.d0
      do k = 1, ktcon(i) - 1
        tem = 0.d0
        if (k >= kb(i)) tem = eta(i,k)
        if (k <= jmin(i)) tem = tem - edto(i)*etad(i,k)
        kd = k
        if (tem > 0.d0) kd = k + 1
        cmx = max(cmx, abs(tem)*xmb(i)*dt2*grav/(1000.d0*del(i,kd)))
      enddo
      ns = max(1, ceiling(cmx))
      do n = 1, ntr
        do it = 1, ns
          do k = 1, km
            cto(k) = ctr(i,k,n)
          enddo
          do k = 1, min(kmax(i), km) - 1
            cto(k) = 0.5d0*(ctr(i,k,n) + ctr(i,k+1,n))
          enddo
          dl = 0.d0
          dl(1) = edto(i)*etad(i,1)*ecdo(i,1,n)*grav/(1000.d0*del(i,1))
          do k = 2, km - 1
            if (k < ktcon(i)) then
              aup = 1.d0; if (k <= kb(i)) aup = 0.d0
              adw = 1.d0; if (k > jmin(i)) adw = 0.d0
              tem1 = -eta(i,k)*ercko(i,k,n); tem2 = -eta(i,k-1)*ecko(i,k-1,n)
              ptem1 = -etad(i,k)*ecdo(i,k,n); ptem2 = -etad(i,k-1)*ecdo(i,k-1,n)
              dl(k) = dl(k) + (aup*(tem1-tem2) - adw*edto(i)*(ptem1-ptem2))*grav/(1000.d0*del(i,k))
            endif
          enddo
          k = ktcon(i)
          dl(k) = eta(i,k-1)*ecko(i,k-1,n)*grav/(1000.d0*del(i,k))
          ed = 0.d0
          do k = 1, km - 1
            if (k <= ktcon(i)) ed(k) = ctr(i,k,n) - ctr(i,k+1,n)
          enddo
          if (ctr(i,1,n) >= 0.d0) then
            ed(0) = max(0.d0, 2.d0*ctr(i,1,n) - ctr(i,2,n)) - ctr(i,1,n)
          else
            ed(0) = min(0.d0, 2.d0*ctr(i,1,n) - ctr(i,2,n)) - ctr(i,1,n)
          endif
          flx = 0.d0
          do k = 1, km - 1
            if (k < ktcon(i)) then
              tem = 0.d0
              if (k >= kb(i)) tem = eta(i,k)
              if (k <= jmin(i)) tem = tem - edto(i)*etad(i,k)
              if (tem > 0.d0) then
                rrkp = 0.d0; if (abs(ed(k)) > 1.d-22) rrkp = ed(k+1)/ed(k)
                phkp = (rrkp + abs(rrkp))/(1.d0 + abs(rrkp))
                tem1 = ctr(i,k+1,n) + phkp*(cto(k) - ctr(i,k+1,n))
                flx(k) = tem*tem1
              elseif (tem < 0.d0) then
                rrkp = 0.d0; if (abs(ed(k)) > 1.d-22) rrkp = ed(k-1)/ed(k)
                phkp = (rrkp + abs(rrkp))/(1.d0 + abs(rrkp))
                tem1 = ctr(i,k,n) + phkp*(cto(k) - ctr(i,k,n))
                flx(k) = tem*tem1
              else
                tem1 = cto(k); flx(k) = 0.d0
              endif
              if (k == kb(i)) flx(k) = flx(k) + eta(i,k)*(cto(k) - tem1)
              if (k == jmin(i)) flx(k) = flx(k) - edto(i)*etad(i,k)*(cto(k) - tem1)
              if (k == jmin(i)) dl(k+1) = dl(k+1) - edto(i)*etad(i,k)*cto(k)*grav/(1000.d0*del(i,k+1))
              if (k == kb(i)) dl(k) = dl(k) - eta(i,k)*cto(k)*grav/(1000.d0*del(i,k))
            endif
          enddo
          do k = 1, km - 1
            if (k <= ktcon(i)) dl(k) = dl(k) + (flx(k) - flx(k-1))*grav/(1000.d0*del(i,k))
          enddo
          do k = 1, min(ktcon(i), kmax(i))
            ctr(i,k,n) = ctr(i,k,n) + dl(k)*xmb(i)*dt2/dble(ns)
          enddo
        enddo
        do k = 1, km
          dellae(i,k,n) = 0.d0
        enddo
      enddo
    enddo
  end subroutine tm_samf_substep
end module tm_meter
