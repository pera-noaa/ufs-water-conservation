#!/usr/bin/env python3
"""GWD-segment split meter (diagnostic builds only; needs the em_p01..12 meters of instrument_eb_phys.py).
Usage: instrument_gw_split.py <ufs-weather-model>
Adds probe em_gw after ugwpv1_gsldrag_post. Per step, area-integrated (J), line 'EMG kdt e1..e8':
  e1 sum m dK(Xe; du_gw)      KE change of the whole GWD increment from the effective state Xe = X0 + dtp*pending
  e2 sum m dK(X0; du_gsl)     GSL drag alone, from X0 (= ugrs, the state the scheme sees)
  e3 sum m dK(X0; du_ngw)     UGWP-v1 NGW alone, from X0
  e4 sum m cp dtp dtdt_gsl    GSL heating (dtdt_gw - dtdt_ngw)
  e5 sum m cp dtp dtdt_ngw    NGW heating
  e6 sum m du_gw.(Xe - X0)    cross term: GWD increment x pending process-split increment (PBL)
  e7 sum m du_gsl.du_ngw      cross term: GSL x NGW
  e8 sum m |cp dtp dtdt_gsl + dK(X0; du_gsl)|  per layer (local closure of the GSL term)
Identity e1 = e2 + e3 + e6 + e7; GWD segment residual = e1 + e4 + e5."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp"
phys = root / "physics/physics"
idir = phys / "Interstitials/UFS_SCM_NEPTUNE"
suite = root / "suites/suite_FV3_GFS_v17_p8_ugwpv1.xml"
cfg = root / "config/ccpp_prebuild_config_fv3.py"
metas = sorted(phys.rglob("*.meta")) + sorted((root / "data").glob("*.meta"))


def block(std):
    for m in metas:
        txt = m.read_text(errors="ignore")
        for b in re.split(r"\n(?=\[)", txt):
            if re.search(r"^\s*standard_name\s*=\s*" + re.escape(std) + r"\s*$", b, re.M) and b.startswith("[") \
                    and "ccpp-" not in b.splitlines()[0]:
                return [l for l in b.strip().splitlines() if not l.strip().startswith("intent")
                        and not l.strip().startswith("optional")]
    sys.exit(f"ABORT: no metadata block for {std}")


ARGS = [("im", "horizontal_loop_extent", "integer, intent(in) :: im"),
        ("levs", "vertical_layer_dimension", "integer, intent(in) :: levs"),
        ("dtp", "timestep_for_physics", "real(kind=kind_phys), intent(in) :: dtp"),
        ("gu0", "x_wind", "real(kind=kind_phys), intent(in) :: gu0(:,:)"),
        ("gv0", "y_wind", "real(kind=kind_phys), intent(in) :: gv0(:,:)"),
        ("dudt", "process_split_cumulative_tendency_of_x_wind", "real(kind=kind_phys), intent(in) :: dudt(:,:)"),
        ("dvdt", "process_split_cumulative_tendency_of_y_wind", "real(kind=kind_phys), intent(in) :: dvdt(:,:)"),
        ("dudt_gw", "tendency_of_x_wind", "real(kind=kind_phys), intent(in) :: dudt_gw(:,:)"),
        ("dvdt_gw", "tendency_of_y_wind", "real(kind=kind_phys), intent(in) :: dvdt_gw(:,:)"),
        ("dtdt_gw", "tendency_of_air_temperature", "real(kind=kind_phys), intent(in) :: dtdt_gw(:,:)"),
        ("dudt_ngw", "tendency_of_x_wind_due_to_nonorographic_gravity_wave_drag",
         "real(kind=kind_phys), intent(in) :: dudt_ngw(:,:)"),
        ("dvdt_ngw", "tendency_of_y_wind_due_to_nonorographic_gravity_wave_drag",
         "real(kind=kind_phys), intent(in) :: dvdt_ngw(:,:)"),
        ("dtdt_ngw", "tendency_of_air_temperature_due_to_nonorographic_gravity_wave_drag",
         "real(kind=kind_phys), intent(in) :: dtdt_ngw(:,:)"),
        ("prsi", "air_pressure_at_interface", "real(kind=kind_phys), intent(in) :: prsi(:,:)"),
        ("garea", "cell_area", "real(kind=kind_phys), intent(in) :: garea(:)"),
        ("con_g", "gravitational_acceleration", "real(kind=kind_phys), intent(in) :: con_g"),
        ("con_cp", "specific_heat_of_dry_air_at_constant_pressure", "real(kind=kind_phys), intent(in) :: con_cp"),
        ("errmsg", "ccpp_error_message", "character(len=*), intent(out) :: errmsg"),
        ("errflg", "ccpp_error_code", "integer, intent(out) :: errflg")]

F90 = """!> \\file em_gw.F90
!! GWD-segment split meter (diagnostic builds only).
module em_gw
  use machine, only: kind_phys
  use energy_meter_common, only: emy
  implicit none
contains
!> \\section arg_table_em_gw_run Argument Table
!! \\htmlinclude em_gw_run.html
!!
  subroutine em_gw_run(%s)
%s
    integer :: i, k
    real(kind=8) :: m, a, u0, v0, ue, ve, du, dv, dug, dvg, dun, dvn, kg, hg, e(8)
    do i = 1, im
       e = 0.d0
       a = garea(i)
       do k = 1, levs
          m = (prsi(i,k) - prsi(i,k+1))/con_g
          u0 = gu0(i,k)
          v0 = gv0(i,k)
          ue = u0 + dtp*dudt(i,k)
          ve = v0 + dtp*dvdt(i,k)
          du = dtp*dudt_gw(i,k)
          dv = dtp*dvdt_gw(i,k)
          dun = dtp*dudt_ngw(i,k)
          dvn = dtp*dvdt_ngw(i,k)
          dug = dtp*(dudt_gw(i,k) - dudt_ngw(i,k))
          dvg = dtp*(dvdt_gw(i,k) - dvdt_ngw(i,k))
          kg = dug*(u0 + 0.5d0*dug) + dvg*(v0 + 0.5d0*dvg)
          hg = con_cp*dtp*(dtdt_gw(i,k) - dtdt_ngw(i,k))
          e(1) = e(1) + m*(du*(ue + 0.5d0*du) + dv*(ve + 0.5d0*dv))
          e(2) = e(2) + m*kg
          e(3) = e(3) + m*(dun*(u0 + 0.5d0*dun) + dvn*(v0 + 0.5d0*dvn))
          e(4) = e(4) + m*hg
          e(5) = e(5) + m*con_cp*dtp*dtdt_ngw(i,k)
          e(6) = e(6) + m*(du*(ue - u0) + dv*(ve - v0))
          e(7) = e(7) + m*(dug*dun + dvg*dvn)
          e(8) = e(8) + m*abs(hg + kg)
       enddo
       emy = emy + e*a
    enddo
    errmsg = ''
    errflg = 0
  end subroutine em_gw_run
end module em_gw
"""


def sub(p, old, new, count=1):
    s = p.read_text()
    if s.count(old) != count:
        sys.exit(f"ABORT {p.name}: {old.strip()[:60]!r} found {s.count(old)}")
    p.write_text(s.replace(old, new))


common = idir / "energy_meter_common.F90"
if "emy" not in common.read_text():
    sub(common, "  public :: em_probe, emc, emg, emx, emkdt, emf\n",
        "  public :: em_probe, emc, emg, emx, emkdt, emf, emy\n")
    sub(common, "  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1\n",
        "  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1\n  real(kind=8), save :: emy(8) = 0.d0\n")
    p12 = idir / "em_p12.F90"
    sub(p12, "    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)\n",
        "    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)\n    real(kind=8) :: gbuf(8), grbuf(8)\n"
        "    if (kdt /= emkdt(12) .and. emkdt(12) >= 0) then\n"
        "       gbuf = emy\n"
        "       if (mpirank == mpiroot) then\n"
        "          call MPI_Reduce(MPI_IN_PLACE, gbuf, 8, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
        "          write(*,'(a,i6,8es25.16)') 'EMG ', emkdt(12), gbuf\n"
        "       else\n"
        "          call MPI_Reduce(gbuf, grbuf, 8, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
        "       endif\n"
        "       emy = 0.d0\n"
        "    endif\n")

names = [n for n, _, _ in ARGS]
lines, cur = [], ""
for n in names:
    if len(cur) + len(n) > 80:
        lines.append(cur)
        cur = ""
    cur += n + ", "
lines.append(cur.rstrip(", "))
(idir / "em_gw.F90").write_text(F90 % (" &\n       ".join(lines), "\n".join("    " + d for _, _, d in ARGS)))
meta = ["[ccpp-table-properties]\n  name = em_gw\n  type = scheme\n  dependencies = ../../hooks/machine.F,energy_meter_common.F90\n",
        "[ccpp-arg-table]\n  name = em_gw_run\n  type = scheme"]
for n, std, _ in ARGS:
    b = block(std)
    b[0] = f"[{n}]"
    meta.append("\n".join(b) + "\n  intent = " + ("out" if n in ("errmsg", "errflg") else "in"))
(idir / "em_gw.meta").write_text("\n".join(meta) + "\n")

s = suite.read_text()
if "em_gw" not in s:
    old = "<scheme>ugwpv1_gsldrag_post</scheme>"
    if s.count(old) != 1:
        sys.exit("ABORT suite anchor")
    suite.write_text(s.replace(old, old + "\n      <scheme>em_gw</scheme>"))
c = cfg.read_text()
if "em_gw" not in c:
    old = "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/em_p12.F90',\n"
    if c.count(old) != 1:
        sys.exit("ABORT cfg anchor")
    cfg.write_text(c.replace(old, old + "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/em_gw.F90',\n"))
cm = root / "CMakeLists.txt"
c = cm.read_text()
if "em_gw" not in c:
    old = '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/em_p12.meta"\n'
    if c.count(old) != 1:
        sys.exit("ABORT cmake anchor")
    cm.write_text(c.replace(old, old + '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/em_gw.meta"\n'))
print("em_gw added")
