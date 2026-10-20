!  sub-cloud eta can exceed 1 (detrainment > entrainment above ~1 km): keep CFL <= 1 there too
      do k = 1, km
        do i = 1, im
          if(cnvflg(i) .and. k >= kb(i) .and. k < kbcon(i)) then
            dp = 1000.0_conv_wp * del(i,k)
            xmbmax(i) = min(xmbmax(i), dp /
     &        (real(grav, kind=conv_wp) * dt2 * eta(i,k)))
          endif
        enddo
      enddo
