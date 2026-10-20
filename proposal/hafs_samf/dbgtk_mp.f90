      dbgmp: block
        ! DEBUG ONLY (TKE hotspot trace): TKE tracer (index 8) at the end of physics, same columns, with the step number
        integer :: ii
        real(kind=kind_phys) :: rlat, rlon
        do ii = 1, im
          rlat = xlat(ii)*57.29577951308232_kind_phys; rlon = xlon(ii)*57.29577951308232_kind_phys
          if (abs(rlat+34.99_kind_phys) < 2._kind_phys .and. abs(rlon-306.9_kind_phys) < 2._kind_phys .and. size(gq0,3) >= 8) &
            write(*,'(a,i6,i5,2f9.3,3f11.3)') 'DBGTKM', kdt, ii, rlat, rlon, gq0(ii,20,8), gq0(ii,21,8), gq0(ii,22,8)
        enddo
        flush(6)
      end block dbgmp
