#!/usr/bin/env python3
"""TAGGED TRACERS (diagnostic; apply after instrument_shadow.py). Usage: instrument_tags.py <tree>
field_table tracers tg_adv tg_rmp tg_pbl tg_dcv tg_scv start exactly dry-uniform at the first dynamics call. Each carries
only ONE generator's dry-ratio departure: after every metered process P other than its own, the departure that P creates
from an exactly uniform field (the sh_d shadow's dev) is subtracted in dry-ratio space, q -= dev_P * c0*(1-sum water).
Their own generator's increments, and transport/mixing of what they carry, are kept. Linear attribution of the dry spread:
sum over tags ~ pt_udry (printed as tag 7 = sum - pt_udry). Prints 'TG step n ms max k lat lon' (n 1..5 tags, 6 pt_udry,
7 sum-check) at the end of each step (after fv_update_phys)."""
import sys
from pathlib import Path
top = Path(sys.argv[1])
fv3 = top / "UFSATM/fv3/atmos_cubed_sphere"; atm = fv3 / "driver/UFS/atmosphere.F90"
met = top / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/tm_meter.F90"
edits = {}
def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count}, found {n}: {old.strip()[:90]!r}")
    edits[path] = s.replace(old, new)
sub(met, "tm_sh_dyn, tm_sh_phys, tm_sh_icstat\n", "tm_sh_dyn, tm_sh_phys, tm_sh_icstat, tm_tgi, tm_tga\n")
sub(met, "  real(8), save :: tm_sha(6, tm_shnp, 5) = 0.d0\n",
    "  real(8), save :: tm_sha(6, tm_shnp, 5) = 0.d0\n"
    "  integer, save :: tm_tgi(6) = 0                      ! tags adv rmp pbl dcv scv; 6 = pt_udry\n"
    "  integer, parameter :: tm_tgp(5) = (/ 3, 4, 12, 14, 15 /)   ! the process each tag keeps\n"
    "  real(8), save :: tm_tga(6, 7) = 0.d0\n")
# dynamics: declarations, subtraction after measuring, stats at ip 18, init when off
sub(met, "    real(8) :: sw, sc, w, rd, rp, d(5), lat, lon\n    integer :: i, j, k, m, jd, jm, jp, jv\n",
    "    real(8) :: sw, sc, w, rd, rp, d(5), lat, lon, dt(7)\n    integer :: i, j, k, m, jd, jm, jp, jv, n\n")
sub(met, """            do m = 1, 5
              call tm_sh_acc(ip, m, w, d(m), k, lat, lon)
            enddo
          endif
""", """            do m = 1, 5
              call tm_sh_acc(ip, m, w, d(m), k, lat, lon)
            enddo
            do n = 1, 5
              if (tm_tgi(n) > 0 .and. tm_tgp(n) /= ip) q(i,j,k,tm_tgi(n)) = q(i,j,k,tm_tgi(n)) - d(1)*rd
            enddo
            if (ip == 18) then
              dt = 0.d0
              do n = 1, 6
                if (tm_tgi(n) > 0) dt(n) = q(i,j,k,tm_tgi(n))/rd - 1.d0
              enddo
              dt(7) = sum(dt(1:5)) - dt(6)
              do n = 1, 7
                tm_tga(1,n) = tm_tga(1,n) + w*dt(n)*dt(n); tm_tga(2,n) = tm_tga(2,n) + w
                if (abs(dt(n)) > tm_tga(3,n)) then
                  tm_tga(3,n) = abs(dt(n)); tm_tga(4,n) = k; tm_tga(5,n) = lat; tm_tga(6,n) = lon
                endif
              enddo
            endif
          endif
          if (mode > 0 .and. .not. tm_sh_on) then
            do n = 1, 5
              if (tm_tgi(n) > 0) q(i,j,k,tm_tgi(n)) = rd
            enddo
          endif
""")
# physics: subtraction
sub(met, "    real(8) :: qv, sc, w, rd, rm, d(5), wo\n    integer :: i, k, m, jd, jm, jp, jv\n",
    "    real(8) :: qv, sc, w, rd, rm, d(5), wo\n    integer :: i, k, m, jd, jm, jp, jv, n\n")
sub(met, """          do m = 1, 5
            call tm_sh_acc(ip, m, w, d(m), k, 0.d0, 0.d0)
          enddo
""", """          do m = 1, 5
            call tm_sh_acc(ip, m, w, d(m), k, 0.d0, 0.d0)
          enddo
          if (mode > 0) then
            do n = 1, 5
              if (tm_tgi(n) > 0 .and. tm_tgp(n) /= ip) gq0(i,k,tm_tgi(n)) = gq0(i,k,tm_tgi(n)) - d(1)*rd
            enddo
          endif
""")
# host: indices and report
sub(atm, "tm_sh_on, tm_sha, tm_shnp\n", "tm_sh_on, tm_sha, tm_shnp, tm_tgi, tm_tga\n")
sub(atm, "   tm_wi(5) = get_tracer_index(MODEL_ATMOS, 'snowwat'); tm_wi(6) = get_tracer_index(MODEL_ATMOS, 'graupel')\n",
    "   tm_wi(5) = get_tracer_index(MODEL_ATMOS, 'snowwat'); tm_wi(6) = get_tracer_index(MODEL_ATMOS, 'graupel')\n"
    "   tm_tgi(1) = max(get_tracer_index(MODEL_ATMOS, 'tg_adv'), 0); tm_tgi(2) = max(get_tracer_index(MODEL_ATMOS, 'tg_rmp'), 0)\n"
    "   tm_tgi(3) = max(get_tracer_index(MODEL_ATMOS, 'tg_pbl'), 0); tm_tgi(4) = max(get_tracer_index(MODEL_ATMOS, 'tg_dcv'), 0)\n"
    "   tm_tgi(5) = max(get_tracer_index(MODEL_ATMOS, 'tg_scv'), 0); tm_tgi(6) = max(get_tracer_index(MODEL_ATMOS, 'pt_udry'), 0)\n")
sub(atm, "   tm_sha = 0.d0\n end subroutine tm_sh_report\n", """   tm_sha = 0.d0
   s(1:14) = reshape(tm_tga(1:2,1:7), (/14/)); call mpp_sum(s(1:14), 14)
   v(1:7) = tm_tga(3,1:7); vl(1:7) = v(1:7); call mpp_max(v(1:7), 7)
   lk(1:7) = tm_tga(4,1:7); la(1:7) = tm_tga(5,1:7); lo(1:7) = tm_tga(6,1:7)
   do ix = 1, 7
     if (vl(ix) /= v(ix)) then
       lk(ix) = -1.d30; la(ix) = -1.d30; lo(ix) = -1.d30
     endif
   enddo
   call mpp_max(lk(1:7), 7); call mpp_max(la(1:7), 7); call mpp_max(lo(1:7), 7)
   if (mpp_pe() == mpp_root_pe()) then
     do ix = 1, 7
       if (s(2*ix) > 0.d0) write(*,'(a,i5,i3,2es12.4,f6.0,2f9.2)') 'TG ', st, ix, sqrt(s(2*ix-1)/s(2*ix)), v(ix), lk(ix), la(ix), lo(ix)
     enddo
   endif
   tm_tga = 0.d0
 end subroutine tm_sh_report
""")
for path, s in edits.items():
    path.write_text(s)
    print("tags", path.relative_to(top))
