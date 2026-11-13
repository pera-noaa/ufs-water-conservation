!     DEBUG ONLY (#401 reply): largest sub-cloud eta per convective
!     column when > 1.2; per call: columns, eta > 1.2, tkemean > 2,
!     sub-cloud eta <= 0, clamt at its cap. Print only.
      dbgeta: block
        integer :: ii, kk, nc, n12, nt, nn, ncp
        real(kind=conv_wp) :: em, en
        nc = 0
        n12 = 0
        nt = 0
        nn = 0
        ncp = 0
        do ii = 1, im
          if (cnvflg(ii)) then
            nc = nc + 1
            if (ntk > 0 .and. .not. hwrf_samfdeep) then
              if (tkemean(ii) > tkcrt) nt = nt + 1
            endif
            if (clamt(ii) > 0.999_conv_wp*cmxfac
     &          *real(clam,kind=conv_wp)) ncp = ncp + 1
            em = 0.0_conv_wp
            en = 1.0_conv_wp
            do kk = kb(ii), kbcon(ii)-1
              em = max(em, eta(ii,kk))
              en = min(en, eta(ii,kk))
            enddo
            if (en <= 0.0_conv_wp) nn = nn + 1
            if (em > 1.2_conv_wp) then
              n12 = n12 + 1
              write(*,'(a,i5,2i4,5es11.3)') 'DBGETA', ii, kb(ii),
     &          kbcon(ii), em, tkemean(ii), clamt(ii), zi(ii,kb(ii)),
     &          zi(ii,kbcon(ii))
            endif
          endif
        enddo
        if (nc > 0) write(*,'(a,5i6)') 'DBGETN', nc, n12, nt, nn,
     &  ncp
      end block dbgeta
