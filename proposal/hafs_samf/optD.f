!  option D: keep CFL <= 1 in every updraft layer, kb to ktcon (eta can exceed 1 below and above kbcon)
      do k = 1, km
        do i = 1, im
          if(cnvflg(i) .and. k >= kb(i) .and. k < ktcon(i)) then
            dp = 1000.0_conv_wp * del(i,k)
            xmbmax(i) = min(xmbmax(i), dp /
     &        (real(grav, kind=conv_wp) * dt2 * eta(i,k)))
          endif
        enddo
      enddo
