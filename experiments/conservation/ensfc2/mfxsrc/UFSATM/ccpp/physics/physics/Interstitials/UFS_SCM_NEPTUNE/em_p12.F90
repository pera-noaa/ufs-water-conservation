!> \file em_p12.F90
!! Energy meter probe 12 (diagnostic builds only).
module em_p12
  use machine, only: kind_phys
  use energy_meter_common
  use mpi_f08
  implicit none
contains
!> \section arg_table_em_p12_run Argument Table
!! \htmlinclude em_p12_run.html
!!
  subroutine em_p12_run(im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, ntqv, ntcw,  &
       ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, garea, mpicomm,  &
       mpirank, mpiroot, errmsg, errflg)
    integer, intent(in) :: im
    integer, intent(in) :: levs
    integer, intent(in) :: kdt
    real(kind=kind_phys), intent(in) :: dtp
    real(kind=kind_phys), intent(in) :: gt0(:,:)
    real(kind=kind_phys), intent(in) :: gq0(:,:,:)
    real(kind=kind_phys), intent(in) :: gu0(:,:)
    real(kind=kind_phys), intent(in) :: gv0(:,:)
    real(kind=kind_phys), intent(in) :: dtdt(:,:)
    real(kind=kind_phys), intent(in) :: dqdt(:,:,:)
    real(kind=kind_phys), intent(in) :: dudt(:,:)
    real(kind=kind_phys), intent(in) :: dvdt(:,:)
    real(kind=kind_phys), intent(in) :: prsi(:,:)
    integer, intent(in) :: ntqv
    integer, intent(in) :: ntcw
    integer, intent(in) :: ntiw
    integer, intent(in) :: ntrw
    integer, intent(in) :: ntsw
    integer, intent(in) :: ntgl
    real(kind=kind_phys), intent(in) :: con_g
    real(kind=kind_phys), intent(in) :: con_cp
    real(kind=kind_phys), intent(in) :: con_hvap
    real(kind=kind_phys), intent(in) :: con_hfus
    real(kind=kind_phys), intent(in) :: garea(:)
    type(MPI_Comm), intent(in) :: mpicomm
    integer, intent(in) :: mpirank
    integer, intent(in) :: mpiroot
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    integer :: j0, i

    ! segment s = probe s -> s+1; fluxes per segment (J m-2, kg m-2), residual r = dE - F
    real(kind=8) :: d(7), e0, e1, f, w, frad, fpbl, fmp, wpbl, wmp, wcv, a
    integer :: s, jj, ierr
    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)
    if (kdt /= emkdt(12) .and. emkdt(12) >= 0) then
       buf(1:10*emnp) = reshape(emg, (/10*emnp/))
       buf(10*emnp+1:) = emx
       if (mpirank == mpiroot) then
          call MPI_Reduce(MPI_IN_PLACE, buf, size(buf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)
          do s = 1, emnp
             write(*,'(a,i6,i3,10es25.16)') 'EMS ', emkdt(12), s, buf(10*(s-1)+1:10*s)
          enddo
          write(*,'(a,i6,12es25.16)') 'EMF ', emkdt(12), buf(10*emnp+1:)
       else
          call MPI_Reduce(buf, rbuf, size(buf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)
       endif
       emg = 0.d0
       emx = 0.d0
    endif
    call em_probe(12, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, j0)
    do i = 1, im
       jj = j0 + i
       a = garea(i)
       frad = emf(1, jj)
       fpbl = emf(8, jj) + emf(9, jj)
       fmp = con_hfus*emf(11, jj)
       wpbl = emf(9, jj)/con_hvap
       wmp = -emf(10, jj)
       wcv = -emf(12, jj)
       do s = 1, emnp - 1
          d = emc(:, s+1, jj) - emc(:, s, jj)
          f = 0.d0
          w = 0.d0
          if (s == 2) f = frad
          if (s == 4) then
             f = fpbl
             w = wpbl
          endif
          if (s == 10) then
             f = fmp
             w = wmp
          endif
          emg(1, s) = emg(1, s) + (d(1)+d(2)+d(3)+d(4))*a
          emg(2:5, s) = emg(2:5, s) + d(1:4)*a
          emg(6, s) = emg(6, s) + d(5)*a
          emg(7, s) = emg(7, s) + f*a
          emg(8, s) = emg(8, s) + abs(d(1)+d(2)+d(3)+d(4) - f)*a
          emg(9, s) = emg(9, s) + (d(5) - w)*a
          emg(10, s) = emg(10, s) + d(7)*a
       enddo
       ! slot 12: whole physics (probe 1 -> 12), F = rad + pbl + mp, water vs all precip
       d = emc(:, 12, jj) - emc(:, 1, jj)
       emg(1, 12) = emg(1, 12) + (d(1)+d(2)+d(3)+d(4))*a
       emg(2:5, 12) = emg(2:5, 12) + d(1:4)*a
       emg(6, 12) = emg(6, 12) + d(5)*a
       emg(7, 12) = emg(7, 12) + (frad + fpbl + fmp)*a
       emg(8, 12) = emg(8, 12) + abs(d(1)+d(2)+d(3)+d(4) - frad - fpbl - fmp)*a
       emg(9, 12) = emg(9, 12) + (d(5) - wpbl - wmp - wcv)*a
       emg(10, 12) = emg(10, 12) + d(7)*a
       e0 = emc(1,1,jj) + emc(2,1,jj) + emc(3,1,jj) + emc(4,1,jj)
       emx(1) = emx(1) + e0*a
       emx(2) = emx(2) + emc(5,1,jj)*a
       emx(3:10) = emx(3:10) + emf(2:9, jj)*a
       emx(11) = emx(11) + (emf(10, jj) + emf(12, jj))*a
       emx(12) = emx(12) + a
    enddo

    errmsg = ''
    errflg = 0
  end subroutine em_p12_run
end module em_p12
