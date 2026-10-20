!     DEBUG ONLY (TKE hotspot trace): TKE budget stages, columns with
!     TKE > 100 m2/s2 in k = 15..30. Print only.
      dbgk: block
        integer :: ii, kk
        real(kind=kind_phys) :: tmx
        do ii = 1, im
          tmx = max(maxval(q1(ii,15:30,ntke)), maxval(f1(ii,15:30)))
          if (tmx > 100.) then
            write(*,'(a,i5,i3,2l2,2es11.3)') 'DBGTKH', ii, kpbl(ii),
     &        pcnvflg(ii), scuflg(ii), hpbl(ii), tmx
            do kk = 15, 28
              write(*,'(a,i5,i3,11es11.3)') 'DBGTKP', ii, kk,
     &          zi(ii,kk), q1(ii,kk,ntke), te(ii,kk), f1(ii,kk),
     &          prod(ii,kk)*dt2, diss(ii,kk)*dt2, bf(ii,kk),
     &          shr2(ii,kk), ele(ii,kk), dku(ii,kk), t1(ii,kk)
            enddo
          endif
        enddo
        flush(6)
      end block dbgk
