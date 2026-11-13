#!/usr/bin/env python3
"""Insert the PBL TKE/KE budget meter (EMT/EMP lines) into satmedmfvdifq + the energy meter.

usage: instrument_pbl.py <ccpp dir>   (UFSATM/ccpp of a tree that already has the energy meters
       and patch 04; edits in place; aborts unless every anchor matches exactly once)
EMT (per step, area-weighted global sums, divide by slot 24 = area for W m-2):
  1 Ps  2 Ps surface term  3 Pb  4 Pb>0  5 floor at entry  6 eps mean over substeps  7 eps clipped
  8 floor in substeps  9 eps last substep (heated by dspheat)  10 dTKE local  11 dTKE transport
  12 TKE content in (J m-2)  13 TKE content out  14 -dKE momentum solve  15 implicit surface work
  16 explicit surface work  17 sum(-dKE_k<0) (local cooling of the KE form)  18 cp*dT heat solve - dtsfc
  19 heating applied by dspheat  20 sum of B&B layer heating < 0  21 sum of interface D < 0
  22 interface D from the EDMF mass-flux transfer  23 sum of (D - D_MF) < 0  24 area
EMP (per step, per level k, W): [old ε | per-layer -dKE | B&B] x [land-day sea-day land-night sea-night]
"""
import sys, os

ccpp = sys.argv[1]
P = os.path.join(ccpp, 'physics/physics')


def edit(path, pairs):
    s = open(path).read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            sys.exit(f'ABORT {path}: anchor count {n}: {old[:70]!r}')
        s = s.replace(old, new)
    open(path, 'w').write(s)


# --- energy_meter_common: storage
edit(os.path.join(P, 'Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90'), [
    ("  public :: em_probe, emc, emg, emx, emkdt, emf\n",
     "  public :: em_probe, emc, emg, emx, emkdt, emf, emt, emtp\n"),
    ("  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1\n",
     "  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1\n"
     "  integer, parameter, public :: emnt = 24, emnl = 128\n"
     "  real(kind=8), save :: emt(emnt) = 0.d0, emtp(12, emnl) = 0.d0\n"),
])

# --- em_p12: reduce and print
edit(os.path.join(P, 'Interstitials/UFS_SCM_NEPTUNE/em_p12.F90'), [
    ("    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)\n",
     "    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)\n"
     "    real(kind=8) :: tbuf(emnt+12*emnl), trbuf(emnt+12*emnl)\n"
     "    integer :: kk\n"),
    ("       emg = 0.d0\n       emx = 0.d0\n",
     "       emg = 0.d0\n       emx = 0.d0\n"
     "       tbuf(1:emnt) = emt\n"
     "       tbuf(emnt+1:) = reshape(emtp, (/12*emnl/))\n"
     "       if (mpirank == mpiroot) then\n"
     "          call MPI_Reduce(MPI_IN_PLACE, tbuf, size(tbuf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
     "          write(*,'(a,i6,24es25.16)') 'EMT ', emkdt(12), tbuf(1:emnt)\n"
     "          do kk = 1, emnl\n"
     "             write(*,'(a,i6,i4,12es17.8)') 'EMP ', emkdt(12), kk, tbuf(emnt+12*(kk-1)+1:emnt+12*kk)\n"
     "          enddo\n"
     "       else\n"
     "          call MPI_Reduce(tbuf, trbuf, size(tbuf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
     "       endif\n"
     "       emt = 0.d0\n"
     "       emtp = 0.d0\n"),
])

# --- satmedmfvdifq.meta: dependency + land mask
edit(os.path.join(P, 'PBL/SATMEDMF/satmedmfvdifq.meta'), [
    ("  dependencies = ../../tools/funcphys.f90,../../tools/canopy_utils_mod.f,../../hooks/machine.F,../mfpbltq.f,mfscuq.f,../tridi.f\n",
     "  dependencies = ../../tools/funcphys.f90,../../tools/canopy_utils_mod.f,../../hooks/machine.F,../mfpbltq.f,mfscuq.f,../tridi.f,"
     "../../Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90\n"),
    ("[dspheat_ke]\n",
     "[islmsk]\n  standard_name = sea_land_ice_mask\n  long_name = sea/land/ice mask (=0/1/2)\n  units = flag\n"
     "  dimensions = (horizontal_loop_extent)\n  type = integer\n  intent = in\n[dspheat_ke]\n"),
])

# --- satmedmfvdifq.F
F = os.path.join(P, 'PBL/SATMEDMF/satmedmfvdifq.F')
edit(F, [
    ("     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,dspheat_ke,                 &\n",
     "     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,dspheat_ke,islmsk,          &\n"),
    ("      use funcphys , only : fpvs\n",
     "      use funcphys , only : fpvs\n"
     "      use energy_meter_common, only : emt, emtp\n"),
    ("      logical, intent(in)  :: dspheat_ke\n",
     "      logical, intent(in)  :: dspheat_ke\n"
     "      integer, intent(in)  :: islmsk(:)\n"
     "      real(kind=8) emm, emraw, emtb, emte0(im,km), emkel, emo, emn\n"
     "      real(kind=8) emq(km), emtu, emtv, emd, emdm, emb, emxu, emxv\n"
     "      real(kind=8) emc2\n      integer emk\n"
     "      integer emj\n"),
    # floor at entry and TKE content
    ("""      do k=1,km
        do i=1,im
          te(i,k) = max(q1(i,k,ntke), tkmin)
          tkeh(i,k) = 0
          tteh(i,k) = 0
        enddo
      enddo
""", """      do k=1,km
        do i=1,im
          te(i,k) = max(q1(i,k,ntke), tkmin)
          tkeh(i,k) = 0
          tteh(i,k) = 0
        enddo
      enddo
      do k=1,km
        do i=1,im
          emm = garea(i)*del(i,k)*gravi
          emt(5) = emt(5) + emm*(te(i,k)-q1(i,k,ntke))*rdt
          emt(12) = emt(12) + emm*q1(i,k,ntke)
        enddo
      enddo
      do i=1,im
        emt(24) = emt(24) + garea(i)
      enddo
"""),
    # productions
    ("""          if(tte_edmf) then
            if(buop > 0.) then
              prod(i,k) = 2. * buop + shrp
""", """          emm = garea(i)*del(i,k)*gravi
          emt(1) = emt(1) + emm*shrp
          if(k == 1) emt(2) = emt(2) + emm*0.5*tem2
          emt(3) = emt(3) + emm*buop
          emt(4) = emt(4) + emm*max(buop,0.)
          if(tte_edmf) then
            if(buop > 0.) then
              prod(i,k) = 2. * buop + shrp
"""),
    # substep loop (non sa3dtke)
    ("""      else
       dtn = dt2 / float(ndt)
       do n = 1, ndt
       do k = 1,km1
        do i=1,im
           tem = sqrt(te(i,k))
           ptem = ce0 / ele(i,k)
           disste = ptem * te(i,k) * tem
           tem1 = prod(i,k) + te(i,k) / dtn
           disste = max(min(disste, tem1), 0.)
           if(.not. tte_edmf) diss(i,k) = disste
           te(i,k) = te(i,k) + dtn * (prod(i,k)-disste)
           te(i,k) = max(te(i,k), tkmnz(i,k))
""", """      else
       emte0(1:im,1:km) = te(1:im,1:km)
       dtn = dt2 / float(ndt)
       do n = 1, ndt
       do k = 1,km1
        do i=1,im
           tem = sqrt(te(i,k))
           ptem = ce0 / ele(i,k)
           disste = ptem * te(i,k) * tem
           tem1 = prod(i,k) + te(i,k) / dtn
           emraw = disste
           disste = max(min(disste, tem1), 0.)
           if(.not. tte_edmf) diss(i,k) = disste
           te(i,k) = te(i,k) + dtn * (prod(i,k)-disste)
           emtb = te(i,k)
           te(i,k) = max(te(i,k), tkmnz(i,k))
           emm = garea(i)*del(i,k)*gravi
           emt(6) = emt(6) + emm*dtn*disste*rdt
           emt(7) = emt(7) + emm*dtn*(emraw-disste)*rdt
           emt(8) = emt(8) + emm*(te(i,k)-emtb)*rdt
"""),
    # after the TKE local step: eps_last and local change (anchor: updraft TKE properties)
    ("""!>  - Compute updraft & downdraft properties for TKE or TTE
!
""", """!>  - Compute updraft & downdraft properties for TKE or TTE
!
      do k = 1, km1
        do i = 1, im
          emm = garea(i)*del(i,k)*gravi
          emt(9) = emt(9) + emm*diss(i,k)
          emt(10) = emt(10) + emm*(te(i,k)-emte0(i,k))*rdt
        enddo
      enddo
"""),
    # transport and content out
    ("""            qtend = (f1(i,k)-q1(i,k,ntke))*rdt
            rtg(i,k,ntke) = rtg(i,k,ntke)+qtend
""", """            qtend = (f1(i,k)-q1(i,k,ntke))*rdt
            rtg(i,k,ntke) = rtg(i,k,ntke)+qtend
            emm = garea(i)*del(i,k)*gravi
            emt(11) = emt(11) + emm*(f1(i,k)-te(i,k))*rdt
            emt(13) = emt(13) + emm*f1(i,k)
"""),
    # heat solve closure, before any dissipative heating
    ("""        dqsfc(i) = rho_a(i) * hvap * evap(i)
      enddo
""", """        dqsfc(i) = rho_a(i) * hvap * evap(i)
      enddo
      do i = 1,im
        emt(18) = emt(18) - garea(i)*dtsfc(i)
      enddo
      do k = 1,km
        do i = 1,im
          emt(18) = emt(18) + garea(i)*del(i,k)*gravi*cp*ten_t(i,k)
        enddo
      enddo
"""),
    # KE terms and heating profiles, after the momentum tendencies (before dusfc)
    ("""      if (use_oceanuv) then
        do i = 1,im
          spd1_m=""", """      do i = 1,im
        emj = 1
        if(islmsk(i) /= 1) emj = 2
        if(xmu(i) <= 0.) emj = emj + 2
        emm = garea(i)*del(i,1)*gravi/(zi(i,2)-zi(i,1))
        emt(15) = emt(15) + emm*stress(i)/spd1(i)*
     &     ((u1(i,1)+ten_u(i,1)*delt)**2+(v1(i,1)+ten_v(i,1)*delt)**2)
        emt(16) = emt(16) + garea(i)*rho_a(i)*stress(i)*
     &     (u1(i,1)**2+v1(i,1)**2)/spd1(i)
        emq(1:km) = 0.
        emtu = 0.
        emtv = 0.
        do k = km,2,-1
          emtu = emtu - del(i,k)*ten_u(i,k)*delt
          emtv = emtv - del(i,k)*ten_v(i,k)*delt
          emxu = u1(i,k)-u1(i,k-1)+0.5*(ten_u(i,k)-ten_u(i,k-1))*delt
          emxv = v1(i,k)-v1(i,k-1)+0.5*(ten_v(i,k)-ten_v(i,k-1))*delt
          emd = emtu*emxu + emtv*emxv
          emq(k) = emq(k) + 0.5*emd
          emq(k-1) = emq(k-1) + 0.5*emd
          emdm = 0.
          emk = k-1
          emc2 = delt*0.5*(prsl(i,emk)-prsl(i,emk+1))*rdzt(i,emk)
          if(pcnvflg(i) .and. emk < kpbl(i)) then
            emdm = emdm - emc2*xmf(i,emk)*(
     &        (ucko(i,emk)+ucko(i,emk+1)-u1(i,emk)-u1(i,emk+1))*emxu
     &       +(vcko(i,emk)+vcko(i,emk+1)-v1(i,emk)-v1(i,emk+1))*emxv)
          endif
          if(scuflg(i)) then
            if(emk >= mrad(i) .and. emk < krad(i)) then
              emdm = emdm + emc2*xmfd(i,emk)*(
     &          (ucdo(i,emk)+ucdo(i,emk+1)-u1(i,emk)-u1(i,emk+1))*emxu
     &         +(vcdo(i,emk)+vcdo(i,emk+1)-v1(i,emk)-v1(i,emk+1))*emxv)
            endif
          endif
          emt(21) = emt(21) + garea(i)*gravi*min(emd,0.)/delt
          emt(22) = emt(22) + garea(i)*gravi*emdm/delt
          emt(23) = emt(23) + garea(i)*gravi*min(emd-emdm,0.)/delt
        enddo
        emtu = emtu - del(i,1)*ten_u(i,1)*delt
        emtv = emtv - del(i,1)*ten_v(i,1)*delt
        emq(1) = emq(1) + emtu*(u1(i,1)+0.5*ten_u(i,1)*delt)
     &                  + emtv*(v1(i,1)+0.5*ten_v(i,1)*delt)
        do k = 1,km
          emm = garea(i)*del(i,k)*gravi
          emkel = -0.5*(ten_u(i,k)*(2.*u1(i,k)+ten_u(i,k)*delt)
     &                + ten_v(i,k)*(2.*v1(i,k)+ten_v(i,k)*delt))
          emt(14) = emt(14) + emm*emkel
          emt(17) = emt(17) + emm*min(emkel,0.)
          emo = 0.
          if(k < km) emo = dspfac*diss(i,k)
          emn = dspfac*emkel
          emb = dspfac*emq(k)/(del(i,k)*delt)
          emt(20) = emt(20) + emm*min(emb,0.)
          if(dspheat) then
            if(dspheat_ke) then
              emt(19) = emt(19) + emm*emb
            else
              emt(19) = emt(19) + emm*emo
            endif
          endif
          if(k <= 128) then
            emtp(emj,k) = emtp(emj,k) + emm*emo
            emtp(emj+4,k) = emtp(emj+4,k) + emm*emn
            emtp(emj+8,k) = emtp(emj+8,k) + emm*emb
          endif
        enddo
      enddo
      if (use_oceanuv) then
        do i = 1,im
          spd1_m="""),
])
print('instrumented', ccpp)
