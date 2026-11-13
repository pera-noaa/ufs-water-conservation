!     DEBUG ONLY (SA1 water): per rank, every 20 calls, sums since the
!     last print over parent (garea >= 3.5e9 m2) then nest columns:
!     created water, convective rain, |created| [kg]. Print only.
      dbgw: block
        real(kind=8), save :: acc(6) = 0.d0
        integer, save :: ncall = 0
        real(kind=8) :: loc(6)
        integer :: ii, jp
        loc = 0.d0
        do ii = 1, im
          if (cnvflg(ii)) then
            jp = 0
            if (garea(ii) < 3.5e9_kind_phys) jp = 3
            loc(jp+1) = loc(jp+1) + garea(ii)*xmb(ii)*dt2*dbgwq(ii)
            loc(jp+2) = loc(jp+2) + garea(ii)*rn(ii)*1.d3
            loc(jp+3) = loc(jp+3)
     &        + garea(ii)*xmb(ii)*dt2*abs(dbgwq(ii))
          endif
        enddo
!$omp critical (dbgwS)
        acc = acc + loc
        ncall = ncall + 1
        if (mod(ncall, 20) == 0) then
          write(*,'(a,6es13.5)') 'DBGWS', acc
          acc = 0.d0
        endif
!$omp end critical (dbgwS)
      end block dbgw
