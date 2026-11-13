!     DEBUG ONLY (#401 reply): largest sub-cloud eta per convective
!     column when > 1.2, and per-call counts. Print only.
      dbgeta: block
        integer :: ii, kk, nc, n12, nt
        real(kind=conv_wp) :: em
        nc = 0
        n12 = 0
        nt = 0
        do ii = 1, im
          if (cnvflg(ii)) then
            nc = nc + 1
            if (tkemean(ii) > tkcrt) nt = nt + 1
            em = 0.0_conv_wp
            do kk = kb(ii), kbcon(ii)-1
              em = max(em, eta(ii,kk))
            enddo
            if (em > 1.2_conv_wp) then
              n12 = n12 + 1
              write(*,'(a,i5,2i4,5es11.3)') 'DBGETA', ii, kb(ii),
     &          kbcon(ii), em, tkemean(ii), clamt(ii), zi(ii,kb(ii)),
     &          zi(ii,kbcon(ii))
            endif
          endif
        enddo
        if (nc > 0) write(*,'(a,3i6)') 'DBGETN', nc, n12, nt
      end block dbgeta
