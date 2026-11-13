#!/usr/bin/env python3
"""port_D1.py <ufs-weather-model> : port enpbl/patches/04_ccpp-satmedmfvdifq_dspheat_ke.diff (D1, switch dspheat_ke,
default .false.) onto the #403 tree (ccpp-physics 2a95266, ufsatm 4a91b2b), same text as the develop diff, anchored on
single unique lines (the develop context moved). Also (meter, on the t403s copy): ucb slot 25 = applied D1 heating
sum m*cp*dspq (W m-2), written for the column block just metered by uc_ds (offset ucmoff - im)."""
import sys
from pathlib import Path

A = Path(sys.argv[1]) / "UFSATM"
P = A / "ccpp/physics/physics"


def edit(p, reps):
    t = p.read_text()
    for a, b in reps:
        assert t.count(a) == 1, (p.name, a[:80])
        t = t.replace(a, b)
    p.write_text(t)


edit(A / "ccpp/data/GFS_typedefs.F90", [
    ("    logical              :: dspheat         !< flag for tke dissipative heating\n",
     "    logical              :: dspheat         !< flag for tke dissipative heating\n"
     "    logical              :: dspheat_ke      !< flag for dissipative heating = resolved KE loss of the PBL momentum solve\n"),
    ("    logical              :: dspheat        = .false.                  !< flag for tke dissipative heating\n",
     "    logical              :: dspheat        = .false.                  !< flag for tke dissipative heating\n"
     "    logical              :: dspheat_ke     = .false.                  !< flag for dissipative heating = resolved KE loss of the PBL momentum solve\n"),
    ("shinhong, do_ysu, dspheat, lheatstrg, lseaspray, cnvcld,     &\n",
     "shinhong, do_ysu, dspheat, dspheat_ke, lheatstrg, lseaspray, cnvcld,     &\n"),
    ("    Model%dspheat           = dspheat\n", "    Model%dspheat           = dspheat\n    Model%dspheat_ke        = dspheat_ke\n"),
    ("      print *, ' dspheat           : ', Model%dspheat\n",
     "      print *, ' dspheat           : ', Model%dspheat\n      print *, ' dspheat_ke        : ', Model%dspheat_ke\n")])
KEMETA = ("[dspheat_ke]\n  standard_name = flag_for_kinetic_energy_consistent_dissipation_heating\n"
          "  long_name = flag for dissipative heating equal to the resolved kinetic energy loss of the PBL momentum solve\n"
          "  units = flag\n  dimensions = ()\n  type = logical\n")
edit(A / "ccpp/data/GFS_typedefs.meta", [("[sa3dtke]\n", KEMETA + "[sa3dtke]\n")])
edit(P / "PBL/SATMEDMF/satmedmfvdifq.meta", [("[sa3dtke]\n", KEMETA + "  intent = in\n[sa3dtke]\n")])
D1 = """!
!> ## Dissipative heating = KE loss of the implicit momentum solve (Boville & Bretherton 2003):
!!  interface momentum transfer x time-centred shear, half to each adjacent layer; surface stress work in layer 1
!
      if(dspheat .and. dspheat_ke) then
        do k = 1,km
          do i = 1,im
            dspq(i,k) = 0.
          enddo
        enddo
        do i = 1,im
          dsptu(i) = 0.
          dsptv(i) = 0.
        enddo
        do k = km,2,-1
          do i = 1,im
            dsptu(i) = dsptu(i) - del(i,k)*ten_u(i,k)*delt
            dsptv(i) = dsptv(i) - del(i,k)*ten_v(i,k)*delt
            tem = dsptu(i)*(u1(i,k)-u1(i,k-1)
     &                   +0.5*(ten_u(i,k)-ten_u(i,k-1))*delt)
     &          + dsptv(i)*(v1(i,k)-v1(i,k-1)
     &                   +0.5*(ten_v(i,k)-ten_v(i,k-1))*delt)
            dspq(i,k)   = dspq(i,k)   + 0.5*tem
            dspq(i,k-1) = dspq(i,k-1) + 0.5*tem
          enddo
        enddo
        do i = 1,im
          dsptu(i) = dsptu(i) - del(i,1)*ten_u(i,1)*delt
          dsptv(i) = dsptv(i) - del(i,1)*ten_v(i,1)*delt
          dspq(i,1) = dspq(i,1)
     &              + dsptu(i)*(u1(i,1)+0.5*ten_u(i,1)*delt)
     &              + dsptv(i)*(v1(i,1)+0.5*ten_v(i,1)*delt)
        enddo
        do k = 1,km
          do i = 1,im
            dspq(i,k) = dspfac * dspq(i,k) / (cp*del(i,k)*delt)
            ten_t(i,k) = ten_t(i,k) + dspq(i,k)
          enddo
        enddo
        call uc_dk(im, km, del, dspq, cp, grav)
        if(ldiag3d .and. .not. gen_tend) then
          idtend = dtidx(index_of_temperature,index_of_process_pbl)
          if(idtend>=1) then
            do k = 1,km
              do i = 1,im
                dtend(i,k,idtend) = dtend(i,k,idtend)+dspq(i,k)*delt
              enddo
            enddo
          endif
        endif
      endif
"""
edit(P / "PBL/SATMEDMF/satmedmfvdifq.F", [
    ("     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,                            &\n",
     "     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,dspheat_ke,                 &\n"),
    ("      logical, intent(in)  :: dspheat\n",
     "      logical, intent(in)  :: dspheat\n"
     "!  flag for dissipative heating = resolved KE loss of the momentum solve\n"
     "      logical, intent(in)  :: dspheat_ke\n"),
    ("      real(kind=kind_phys) spd1_m\n",
     "      real(kind=kind_phys) spd1_m\n      real(kind=kind_phys) dspq(im,km), dsptu(im), dsptv(im)\n"),
    ("      if(dspheat) then\n", "      if(dspheat .and. .not. dspheat_ke) then\n"),
    ("      use upchk_meter_common, only : uc_pz, uc_pr, uc_ds, uc_pv\n",
     "      use upchk_meter_common, only : uc_pz, uc_pr, uc_ds, uc_pv, uc_dk\n"),
    ("!           dvsfc(i) = dvsfc(i)+conw*del(i,k)*vtend\n         enddo\n      enddo\n      if (use_oceanuv) then\n",
     "!           dvsfc(i) = dvsfc(i)+conw*del(i,k)*vtend\n         enddo\n      enddo\n" + D1 + "      if (use_oceanuv) then\n")])
edit(P / "Interstitials/UFS_SCM_NEPTUNE/upchk_meter_common.F90", [
    ("ucnv = 24", "ucnv = 25"),
    ("    ucb(17:24, ucmoff+1:ucmoff+im) = 0.d0\n", "    ucb(17:25, ucmoff+1:ucmoff+im) = 0.d0\n"),
    ("  subroutine uc_ds(", """  subroutine uc_dk(im, km, del, dspq, cp, grav)
    ! applied D1 heating, for the block uc_ds has just metered (ucmoff already advanced by im)
    integer, intent(in) :: im, km
    real(kind=kind_phys), intent(in) :: del(:,:), dspq(:,:), cp, grav
    integer :: i, k
    do i = 1, im
       do k = 1, km
          ucb(25, ucmoff-im+i) = ucb(25, ucmoff-im+i) + del(i,k)/grav*cp*dspq(i,k)
       enddo
    enddo
  end subroutine uc_dk

  subroutine uc_ds(""")])
edit(P / "Interstitials/UFS_SCM_NEPTUNE/uc_fin.F90", [
    ("write(*,'(a,i6,24es25.16)') 'UCM '", "write(*,'(a,i6,25es25.16)') 'UCM '")])
print("D1 ported (dspheat_ke, default .false.) + slot 25 meter")
