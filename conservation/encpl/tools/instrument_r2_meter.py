#!/usr/bin/env python3
"""Round-2 meters (diagnostic builds only), after instrument_r2_fix.py on the metered tree.
Usage: instrument_r2_meter.py <ufs-weather-model>
EBQ grows to 46: 17/27/28 now the C1v2 sensible rule (27 precipitation part, 28 residual part);
 35-38 PE released by the precipitation fluxes deep / shallow / Thompson liquid / Thompson ice (gross Pauluis),
 39 by the residual net flux; 40/41 S_cross liquid / ice precipitation part; 42 residual part;
 43 precipitation at the surface from the exported fluxes; 44 E*(cp_v-c_l)*(Tskin-T0); 45 E*cp_v*(Tskin-T1);
 46 E*(Tskin-T1).
SAMF Kirchhoff gap per column (hvap - L_v(T)) * C, C = net rain production + detrained condensate, deep and
shallow, printed by em_p12 as 'EMC kdt gap_deep sum|gap_deep| gap_shal sum|gap_shal|' (J, global sums)."""
import sys
from pathlib import Path

base = Path(sys.argv[1]) / "UFSATM"
atm = base / "fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90"
mapz = base / "fv3/atmos_cubed_sphere/model/fv_mapz.F90"
amod = base / "fv3/atmos_model.F90"
P = base / "ccpp/physics/physics"
dc, sc = P / "CONV/SAMF/samfdeepcnv.f", P / "CONV/SAMF/samfshalcnv.f"
p12 = P / "Interstitials/UFS_SCM_NEPTUNE/em_p12.F90"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


sub(mapz, "  real(kind=8), public, save :: ebq(34) = 0.d0\n", "  real(kind=8), public, save :: ebq(46) = 0.d0\n")
sub(mapz, "      write(*, '(a,i6,34es25.16)') 'EBQ ', kstep, ebq\n", "      write(*, '(a,i6,46es25.16)') 'EBQ ', kstep, ebq\n")
sub(amod, "    if (.not. allocated(ebq_prc)) allocate(ebq_prc(2, size(GFS_intdiag%rain)))\n",
    "    if (.not. allocated(ebq_prc)) allocate(ebq_prc(3, size(GFS_intdiag%rain)))\n"
    "    ebq_prc(3,:) = GFS_sfcprop%tsfc(:)\n")
sub(atm, "   real(kind=8) :: x(34), a, dml,", "   real(kind=8) :: x(46), cmp(5), a, dml,")
OLD = """         if (k1 < npz) then
            dt1 = tk(k1+1) - tk(k1)
            x(26) = x(26) + f*c_liq*dt1
            if (f >= 0.) then
               cb = c_liq
               if (tk(k1) < t_frz) cb = c_ice
               x(17) = x(17) + f*cb*dt1
               x(27) = x(27) + f*cb*dt1
            else
               x(17) = x(17) + f*cp_vapor*dt1
               x(28) = x(28) + f*cp_vapor*dt1
            endif
            phm = 0.5d0*(phib(k1) - phib(k1+2))
         else
            phm = 0.5d0*(phib(k1) + phib(k1+1)) - phib(npz+1)
         endif
         if (f >= 0.) then
            x(29) = x(29) + f*phm
         else
            x(30) = x(30) + f*phm
         endif
"""
NEW = """         k = k1
         if (flip_vc) k = npz+1-k1
         cmp(1) = grav*IPD_Stateout%pflx_dc(im,k)
         cmp(2) = grav*IPD_Stateout%pflx_sc(im,k)
         cmp(3) = grav*IPD_Stateout%pflx_mpl(im,k)
         cmp(4) = grav*IPD_Stateout%pflx_mpi(im,k)
         cmp(5) = f - cmp(1) - cmp(2) - cmp(3) - cmp(4)
         if (k1 < npz) then
            dt1 = tk(k1+1) - tk(k1)
            x(26) = x(26) + f*c_liq*dt1
            x(40) = x(40) + (cmp(1) + cmp(2) + cmp(3))*c_liq*dt1
            x(41) = x(41) + cmp(4)*c_ice*dt1
            x(42) = x(42) + cmp(5)*cp_vapor*dt1
            x(27) = x(27) + ((cmp(1) + cmp(2) + cmp(3))*c_liq + cmp(4)*c_ice)*dt1
            x(28) = x(28) + cmp(5)*cp_vapor*dt1
            x(17) = x(17) + ((cmp(1) + cmp(2) + cmp(3))*c_liq + cmp(4)*c_ice + cmp(5)*cp_vapor)*dt1
            phm = 0.5d0*(phib(k1) - phib(k1+2))
         else
            phm = 0.5d0*(phib(k1) + phib(k1+1)) - phib(npz+1)
            x(43) = x(43) + cmp(1) + cmp(2) + cmp(3) + cmp(4)
         endif
         if (f >= 0.) then
            x(29) = x(29) + f*phm
         else
            x(30) = x(30) + f*phm
         endif
         x(35:39) = x(35:39) + cmp(1:5)*phm
"""
sub(atm, OLD, NEW)
sub(atm, "      x(31) = abs(x(15))\n",
    "      x(44) = ev*(cp_vapor - c_liq)*(ebq_prc(3,im) - t_frz)\n"
    "      x(45) = ev*cp_vapor*(ebq_prc(3,im) - t1)\n"
    "      x(46) = ev*(ebq_prc(3,im) - t1)\n"
    "      x(31) = abs(x(15))\n")

# SAMF Kirchhoff gap per column (J m-2), always computed; the option still applies only when set
for f, mname, km1 in ((dc, "skc_d", "km"), (sc, "skc_s", "km1")):
    sub(f, "      use mo_conv_kind, only : conv_wp\n",
        f"      use mo_conv_kind, only : conv_wp\n      real(kind=8), public, save :: {mname}(2, 4096) = 0.d0\n")
    sub(f, f"            if (samf_kirchhoff .and. k <= {km1}) then\n", f"            if (k <= {km1}) then\n")
    sub(f, """              new_t1(i,k) = new_t1(i,k) + real((cvap - cliq)
     &           * (t1(i,k) - t0c) * ck / cp, kind=conv_wp)
""", f"""              if (samf_kirchhoff) new_t1(i,k) = new_t1(i,k)
     &           + real((cvap - cliq) * (t1(i,k) - t0c) * ck / cp,
     &           kind=conv_wp)
              {mname}(1,i) = {mname}(1,i) - dble((cvap - cliq)
     &           * (t1(i,k) - t0c) * ck * delp(i,k) / grav)
              {mname}(2,i) = {mname}(2,i) + abs(dble((cvap - cliq)
     &           * (t1(i,k) - t0c) * ck * delp(i,k) / grav))
""")

sub(p12, "  use module_mp_thompson, only: tkc\n",
    "  use module_mp_thompson, only: tkc\n  use samfdeepcnv, only: skc_d\n  use samfshalcnv, only: skc_s\n")
sub(p12, "  real(kind=8), save :: tkm(6, 7) = 0.d0\n",
    "  real(kind=8), save :: tkm(6, 7) = 0.d0\n  real(kind=8), save :: skm(4) = 0.d0\n")
sub(p12, "       tkm = 0.d0\n",
    "       tkm = 0.d0\n"
    "       if (mpirank == mpiroot) then\n"
    "          call MPI_Reduce(MPI_IN_PLACE, skm, 4, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "          write(*,'(a,i6,4es25.16)') 'EMC ', emkdt(12), skm\n"
    "       else\n"
    "          call MPI_Reduce(skm, tbuf(1:4), 4, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "       endif\n"
    "       skm = 0.d0\n")
sub(p12, "       tkc(:,:,i) = 0.d0\n",
    "       tkc(:,:,i) = 0.d0\n       skm(1:2) = skm(1:2) + skc_d(:,i)*a\n       skm(3:4) = skm(3:4) + skc_s(:,i)*a\n"
    "       skc_d(:,i) = 0.d0\n       skc_s(:,i) = 0.d0\n")
for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
