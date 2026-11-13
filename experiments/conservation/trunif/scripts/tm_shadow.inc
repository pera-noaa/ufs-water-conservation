  !> SHADOW METER (diagnostic only). Shadow tracers sh_d, sh_m, sh_p, sh_v are reset to an exactly uniform state
  !! before each process and the departure after it is accumulated per process ip (1..tm_shnp) and quantity iq:
  !! 1 dev_dry  2 dev_moist  3 dev_physbasis  4 frame/species term  5 residual = 1 - 4.
  !! Stats tm_sha(1:6,ip,iq) = sum W dev^2, sum W, max|dev|, k at max, lat, lon (deg); W = dry mass * area.
  subroutine tm_sh_acc(ip, iq, w, dev, k, lat, lon)
    integer, intent(in) :: ip, iq, k
    real(8), intent(in) :: w, dev, lat, lon
    tm_sha(1,ip,iq) = tm_sha(1,ip,iq) + w*dev*dev
    tm_sha(2,ip,iq) = tm_sha(2,ip,iq) + w
    if (abs(dev) > tm_sha(3,ip,iq)) then
      tm_sha(3,ip,iq) = abs(dev); tm_sha(4,ip,iq) = k; tm_sha(5,ip,iq) = lat; tm_sha(6,ip,iq) = lon
    endif
  end subroutine tm_sh_acc

  !> dynamics frame: measure (ip > 0, only if tm_sh_on) then reset (mode 1: sh_v = sum water, 2: sh_v = sphum, 0: none)
  subroutine tm_sh_dyn(ip, isd, jsd, is, ie, js, je, npz, q, delp, area, agrid, mode)
    integer, intent(in) :: ip, isd, jsd, is, ie, js, je, npz, mode
    real(8), intent(inout) :: q(isd:, jsd:, :, :)
    real(8), intent(in) :: delp(isd:, jsd:, :), area(isd:, jsd:), agrid(isd:, jsd:, :)
    real(8) :: sw, sc, w, rd, rp, d(5), lat, lon
    integer :: i, j, k, m, jd, jm, jp, jv
    jd = tm_shi(1); jm = tm_shi(2); jp = tm_shi(3); jv = tm_shi(4)
    if (min(jd, jm, jp, jv) <= 0) return
    do k = 1, npz
      do j = js, je
        do i = is, ie
          sc = 0.d0
          do m = 2, 6
            sc = sc + q(i,j,k,tm_wi(m))
          enddo
          sw = sc + q(i,j,k,tm_wi(1))
          rd = tm_c0*(1.d0 - sw); rp = tm_c0*(1.d0 - sc)
          if (ip > 0 .and. tm_sh_on) then
            w = delp(i,j,k)*(1.d0 - sw)*area(i,j)
            d(1) = q(i,j,k,jd)/rd - 1.d0
            d(2) = q(i,j,k,jm)/tm_c0 - 1.d0
            d(3) = q(i,j,k,jp)/rp - 1.d0
            d(4) = (sw - q(i,j,k,jv))/(1.d0 - sw)
            d(5) = d(1) - d(4)
            lat = agrid(i,j,2)*57.29577951308232d0; lon = agrid(i,j,1)*57.29577951308232d0
            do m = 1, 5
              call tm_sh_acc(ip, m, w, d(m), k, lat, lon)
            enddo
          endif
          if (mode > 0) then
            q(i,j,k,jd) = rd; q(i,j,k,jm) = tm_c0; q(i,j,k,jp) = rp
            if (mode == 1) then
              q(i,j,k,jv) = sw
            else
              q(i,j,k,jv) = q(i,j,k,tm_wi(1))
            endif
          endif
        enddo
      enddo
    enddo
  end subroutine tm_sh_dyn

  !> physics frame (k=1 at surface, dp = prsi(k)-prsi(k+1)); references from qgrs: qv_in, condensate_in.
  !! measure (ip > 0) then reset (mode 1: physics references, 2: write-back references, 0: none)
  subroutine tm_sh_phys(ip, im, levs, gq0, qgrs, prsi, area, mode)
    integer, intent(in) :: ip, im, levs, mode
    real(8), intent(inout) :: gq0(:,:,:)
    real(8), intent(in) :: qgrs(:,:,:), prsi(:,:), area(:)
    real(8) :: qv, sc, w, rd, rm, d(5), wo
    integer :: i, k, m, jd, jm, jp, jv
    jd = tm_shi(1); jm = tm_shi(2); jp = tm_shi(3); jv = tm_shi(4)
    if (min(jd, jm, jp, jv) <= 0 .or. .not. tm_sh_on) return
    do k = 1, levs
      do i = 1, im
        qv = qgrs(i,k,tm_wi(1))
        sc = 0.d0
        do m = 2, 6
          sc = sc + qgrs(i,k,tm_wi(m))
        enddo
        rd = tm_c0*(1.d0 - qv); rm = tm_c0*(1.d0 + sc)
        if (ip > 0) then
          w = (prsi(i,k) - prsi(i,k+1))*(1.d0 - qv)*area(i)
          d(1) = gq0(i,k,jd)/rd - 1.d0
          d(2) = gq0(i,k,jm)/rm - 1.d0
          d(3) = gq0(i,k,jp)/tm_c0 - 1.d0
          d(4) = (qv - gq0(i,k,jv))/(1.d0 - qv)
          d(5) = d(1) - d(4)
          do m = 1, 5
            call tm_sh_acc(ip, m, w, d(m), k, 0.d0, 0.d0)
          enddo
        endif
        if (mode == 1) then
          gq0(i,k,jd) = rd; gq0(i,k,jm) = rm; gq0(i,k,jp) = tm_c0; gq0(i,k,jv) = qv
        elseif (mode == 2) then
          wo = 0.d0
          do m = 1, 6
            wo = wo + gq0(i,k,tm_wi(m))
          enddo
          gq0(i,k,jd) = rd; gq0(i,k,jm) = tm_c0*(1.d0 - qv + wo); gq0(i,k,jp) = tm_c0; gq0(i,k,jv) = wo
        endif
      enddo
    enddo
  end subroutine tm_sh_phys

  !> IC check of pt_udry (dry dev) and pt_umoist (moist dev): r(1:6) dry, r(7:12) moist (sum W dev^2, sum W, max, k, lat, lon)
  subroutine tm_sh_icstat(isd, jsd, is, ie, js, je, npz, iud, ium, q, delp, area, agrid, r)
    integer, intent(in) :: isd, jsd, is, ie, js, je, npz, iud, ium
    real(8), intent(in) :: q(isd:, jsd:, :, :), delp(isd:, jsd:, :), area(isd:, jsd:), agrid(isd:, jsd:, :)
    real(8), intent(out) :: r(12)
    real(8) :: sw, w, dev
    integer :: i, j, k, m
    r = 0.d0
    do k = 1, npz
      do j = js, je
        do i = is, ie
          sw = 0.d0
          do m = 1, 6
            sw = sw + q(i,j,k,tm_wi(m))
          enddo
          w = delp(i,j,k)*(1.d0 - sw)*area(i,j)
          if (iud > 0) then
            dev = q(i,j,k,iud)/(tm_c0*(1.d0 - sw)) - 1.d0
            r(1) = r(1) + w*dev*dev; r(2) = r(2) + w
            if (abs(dev) > r(3)) then
              r(3) = abs(dev); r(4) = k; r(5) = agrid(i,j,2)*57.29577951308232d0; r(6) = agrid(i,j,1)*57.29577951308232d0
            endif
          endif
          if (ium > 0) then
            dev = q(i,j,k,ium)/tm_c0 - 1.d0
            r(7) = r(7) + w*dev*dev; r(8) = r(8) + w
            if (abs(dev) > r(9)) then
              r(9) = abs(dev); r(10) = k; r(11) = agrid(i,j,2)*57.29577951308232d0; r(12) = agrid(i,j,1)*57.29577951308232d0
            endif
          endif
        enddo
      enddo
    enddo
  end subroutine tm_sh_icstat
