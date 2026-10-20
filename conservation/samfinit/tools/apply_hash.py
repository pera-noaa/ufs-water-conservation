"""apply_hash.py <ufs-weather-model> : add a bitwise state-hash meter (EMH lines) to the energy meter probes.
Edits energy_meter_common.F90 (hash of gt0,gq0,gu0,gv0,dtdt,dqdt,dudt,dvdt per probe) and em_p12.F90 (MPI BXOR + print)."""
import sys, re, pathlib
d = pathlib.Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE"
c = d / "energy_meter_common.F90"; s = c.read_text()
assert "emh(" not in s
s = s.replace("  public :: em_probe,", "  public :: emh, emhp\n  public :: em_probe,", 1)
s = s.replace("  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1\n",
  "  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1\n"
  "  integer(kind=8), save :: emh(emnp) = 0_8, emhp(emnp) = 0_8\n", 1)
old = "    if (kdt /= emkdt(p)) then\n       emkdt(p) = kdt\n       emoff(p) = 0\n    endif\n"
assert old in s
s = s.replace(old, "    if (kdt /= emkdt(p)) then\n       emkdt(p) = kdt\n       emoff(p) = 0\n"
  "       emhp(p) = emh(p)\n       emh(p) = 0_8\n    endif\n", 1)
old = "    emoff(p) = j0 + im\n"
assert old in s
s = s.replace(old, "    call em_hash(p, im, levs, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt)\n" + old, 1)
s = s.replace("end module energy_meter_common", """  subroutine em_hash(p, im, levs, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt)
    ! bitwise state hash per probe: XOR of position-rotated bit patterns
    integer, intent(in) :: p, im, levs
    real(kind=kind_phys), intent(in) :: gt0(:,:), gq0(:,:,:), gu0(:,:), gv0(:,:)
    real(kind=kind_phys), intent(in) :: dtdt(:,:), dqdt(:,:,:), dudt(:,:), dvdt(:,:)
    integer(kind=8) :: h
    integer :: i, k, n
    h = emh(p)
    do k = 1, levs
       do i = 1, im
          h = ieor(h, ishftc(transfer(real(gt0(i,k),8), 0_8), mod(i+k, 61) + 1))
          h = ieor(h, ishftc(transfer(real(gu0(i,k),8), 0_8), mod(i+k+3, 61) + 1))
          h = ieor(h, ishftc(transfer(real(gv0(i,k),8), 0_8), mod(i+k+5, 61) + 1))
          h = ieor(h, ishftc(transfer(real(dtdt(i,k),8), 0_8), mod(i+k+7, 61) + 1))
          h = ieor(h, ishftc(transfer(real(dudt(i,k),8), 0_8), mod(i+k+11, 61) + 1))
          h = ieor(h, ishftc(transfer(real(dvdt(i,k),8), 0_8), mod(i+k+13, 61) + 1))
          do n = 1, size(gq0, 3)
             h = ieor(h, ishftc(transfer(real(gq0(i,k,n),8), 0_8), mod(i+k+17*n, 61) + 1))
             h = ieor(h, ishftc(transfer(real(dqdt(i,k,n),8), 0_8), mod(i+k+19*n+1, 61) + 1))
          enddo
       enddo
    enddo
    emh(p) = h
  end subroutine em_hash
end module energy_meter_common""", 1)
c.write_text(s)
q = d / "em_p12.F90"; s = q.read_text()
assert "EMH" not in s
s = s.replace("    integer :: s, jj, ierr\n", "    integer :: s, jj, ierr\n    integer(kind=8) :: hb(emnp), hr(emnp)\n", 1)
old = "    if (kdt /= emkdt(12) .and. emkdt(12) >= 0) then\n"
assert old in s
s = s.replace(old, old + """       hb(1:emnp-1) = emhp(1:emnp-1)
       hb(emnp) = emh(emnp)
       call MPI_Reduce(hb, hr, emnp, MPI_INTEGER8, MPI_BXOR, mpiroot, mpicomm, ierr)
       if (mpirank == mpiroot) then
          do s = 1, emnp
             write(*,'(a,i6,i3,1x,z16.16)') 'EMH ', emkdt(12), s, hr(s)
          enddo
       endif
""", 1)
q.write_text(s)
print("hash meter applied to", d)
