!     DEBUG ONLY (SAMF CFL study): shallow |dT| > 4 K events and
!     capped-TKE columns. Print only.
      dbg4s: block
        integer :: ii, kk
        real(kind=conv_wp) :: dtk, cfl
        do ii = 1, im
          if (cnvflg(ii)) then
            if (tkemean(ii) > 28.0_conv_wp)
     &        write(*,'(a,i5,3i4,3es11.3)')
     &        'DBGTKS', ii, kb(ii), kbcon(ii), ktcon(ii), tkemean(ii),
     &        clamt(ii), zi(ii,kb(ii))
            do kk = kb(ii)+1, ktcon(ii)
              dtk = xmb(ii)*dt2*(dellah(ii,kk) - real(hvap,kind=conv_wp)
     &            *dellaq(ii,kk))/real(cp,kind=conv_wp)
              cfl = xmb(ii)*eta(ii,kk)*dt2*real(grav,kind=conv_wp)
     &            /(1000.0_conv_wp*del(ii,kk))
              if (abs(dtk) > 4.0_conv_wp) write(*,'(a,i5,4i4,9es11.3)')
     &          'DBGSHAL', ii, kk, kb(ii), kbcon(ii), ktcon(ii), dtk,
     &          xmb(ii)*dt2*dellaq(ii,kk)*1.e3_conv_wp, xmb(ii),
     &          xmbmax(ii), cfl, eta(ii,kk), del(ii,kk), tkemean(ii),
     &          clamt(ii)
            enddo
          endif
        enddo
        flush(6)
      end block dbg4s
