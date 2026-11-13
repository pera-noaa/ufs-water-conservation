!     DEBUG ONLY (SAMF CFL study): |dT| > 4 K events, capped TKE,
!     sub-cloud profile when CFL > 10. Print only.
      dbg4: block
        integer :: ii, kk, k2
        logical :: pr
        real(kind=conv_wp) :: dtk, cfl
        do ii = 1, im
          if (cnvflg(ii)) then
            pr = .false.
            if (tkemean(ii) > 28.0_conv_wp)
     &        write(*,'(a,i5,3i4,3es11.3)')
     &        'DBGTKE', ii, kb(ii), kbcon(ii), ktcon(ii), tkemean(ii),
     &        clamt(ii), zi(ii,kb(ii))
            do kk = 1, ktcon(ii)
              dtk = xmb(ii)*dt2*(dellah(ii,kk) - real(hvap,kind=conv_wp)
     &            *dellaq(ii,kk))/real(cp,kind=conv_wp)
              cfl = xmb(ii)*eta(ii,kk)*dt2*real(grav,kind=conv_wp)
     &            /(1000.0_conv_wp*del(ii,kk))
              if (abs(dtk) > 4.0_conv_wp) write(*,'(a,i5,5i4,9es11.3)')
     &          'DBGSAMF', ii, kk, kb(ii), kbcon(ii), jmin(ii),
     &          ktcon(ii), dtk, xmb(ii)*dt2*dellaq(ii,kk)*1.e3_conv_wp,
     &          xmb(ii), xmbmax(ii), cfl, eta(ii,kk), del(ii,kk),
     &          tkemean(ii), clamt(ii)
              if (cfl > 10.0_conv_wp .and. kk < kbcon(ii) .and.
     &            .not. pr) then
                pr = .true.
                do k2 = max(1,kb(ii)-1), min(km,kbcon(ii)+1)
                  write(*,'(a,i5,i4,6es11.3)') 'DBGPRF', ii, k2,
     &              zi(ii,k2), xlamue(ii,k2), xlamud(ii,k2),
     &              eta(ii,k2), del(ii,k2),
     &              real(tkeh(ii,k2), kind=conv_wp)
                enddo
              endif
            enddo
          endif
        enddo
        flush(6)
      end block dbg4
