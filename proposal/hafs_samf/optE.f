!  option E: no layer loses more vapour in one step than it holds
      do k = 1, km
        do i = 1, im
          if(cnvflg(i) .and. k <= ktcon(i)) then
            if(dellaq(i,k) < 0.0_conv_wp) then
              xmb(i) = min(xmb(i), real(q1(i,k), kind=conv_wp) /
     &          (-dellaq(i,k) * dt2))
            endif
          endif
        enddo
      enddo
