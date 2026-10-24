!  option A1: CFL <= 1 where the updraft mass flux exceeds xmb (eta > 1), kb to ktcon
      do k = 1, km
        do i = 1, im
          if(cnvflg(i) .and. k >= kb(i) .and. k < ktcon(i)) then
            if(eta(i,k) > 1.0_conv_wp) then
              dp = 1000.0_conv_wp * del(i,k)
              xmbmax(i) = min(xmbmax(i), dp /
     &          (real(grav, kind=conv_wp) * dt2 * eta(i,k)))
            endif
          endif
        enddo
      enddo
