#!/usr/bin/env python3
"""Whole-physics water meter (WBP) for the upstream layout (ufs-weather-model develop, ccpp-physics ufs/dev); port of
instrument_wb_phys.py. Diagnostic builds only. Usage: python3 instrument_wb_phys_ups.py <ufs-weather-model>
Per step and column, in GFS_physics_post (last scheme of the step): dW = sum over the six water species of
(gq0 - qgrs)*(prsi(k)-prsi(k+1))/g. Cumulative per rank:
  WBP  kdt | 1 sum(dW*area) (kg) | 2 sum(dW) (kg/m2, unweighted) | 3 sum(area) over steps (m2)
printed (cumulative through kdt) when the next step starts, and from mp_thompson_final.
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
post = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90"
meta = post.with_suffix(".meta")
drv = root / "MP/Thompson/mp_thompson.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


SP = ("ntqv", "ntcw", "ntiw", "ntrw", "ntsw", "ntgl")
DQ = " &\n                + ".join(f"gq0(i,k,{t})-qgrs(i,k,{t})" for t in SP)

sub(post, "  public GFS_physics_post_run\n",
    "  public GFS_physics_post_run\n"
    "  real(kind=8), public, save :: wbp(3) = 0.0d0\n"
    "  integer, public, save :: wbp_kdt = -1\n")
sub(post, "       dtend, errmsg, errflg)\n",
    "       dtend, qgrs, gq0, prsi, garea, kdt, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, errmsg, errflg)\n")
sub(post, "    ! Locals\n",
    "    real(kind=kind_phys), intent(in) :: qgrs(:,:,:), gq0(:,:,:), prsi(:,:), garea(:), con_g\n"
    "    integer, intent(in) :: kdt, ntcw, ntiw, ntrw, ntsw, ntgl\n"
    "    real(kind=8) :: wb_s\n"
    "    integer :: i, k\n\n"
    "    ! Locals\n")
sub(post, "    errflg = 0\n\n    if(.not.ldiag3d) then\n",
    "    errflg = 0\n\n"
    "    if (kdt /= wbp_kdt) then\n"
    "       if (wbp_kdt >= 0) write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n"
    "       wbp_kdt = kdt\n"
    "    endif\n"
    "    do i = 1, nCol\n"
    "       wb_s = 0.0d0\n"
    "       do k = 1, nLev\n"
    f"          wb_s = wb_s + ({DQ}) &\n                *(prsi(i,k)-prsi(i,k+1))\n"
    "       enddo\n"
    "       wb_s = wb_s/con_g\n"
    "       wbp(1) = wbp(1) + wb_s*garea(i)\n"
    "       wbp(2) = wbp(2) + wb_s\n"
    "       wbp(3) = wbp(3) + garea(i)\n"
    "    enddo\n\n"
    "    if(.not.ldiag3d) then\n")


def ent(local, std, longn, units, dims, typ, intent, kind=True):
    return (f"[{local}]\n  standard_name = {std}\n  long_name = {longn}\n  units = {units}\n  dimensions = {dims}\n"
            f"  type = {typ}\n" + ("  kind = kind_phys\n" if kind else "") + f"  intent = {intent}\n")


Q3 = "(horizontal_loop_extent,vertical_layer_dimension,number_of_tracers)"
ADD = (ent("qgrs", "physics_timestep_initial_tracer_concentration", "tracers at the start of the physics step",
           "kg kg-1", Q3, "real", "in")
       + ent("gq0", "tracer_concentration", "tracer concentration updated by physics", "kg kg-1", Q3, "real", "in")
       + ent("prsi", "air_pressure_at_interface", "air pressure at model layer interfaces", "Pa",
             "(horizontal_loop_extent,vertical_interface_dimension)", "real", "in")
       + ent("garea", "cell_area", "area of the grid cell", "m2", "(horizontal_loop_extent)", "real", "in")
       + ent("kdt", "index_of_timestep", "current number of time steps", "index", "()", "integer", "in", False)
       + ent("ntcw", "index_of_cloud_liquid_water_mixing_ratio_in_tracer_concentration_array",
             "tracer index for cloud water", "index", "()", "integer", "in", False)
       + ent("ntiw", "index_of_cloud_ice_mixing_ratio_in_tracer_concentration_array", "tracer index for ice water",
             "index", "()", "integer", "in", False)
       + ent("ntrw", "index_of_rain_mixing_ratio_in_tracer_concentration_array", "tracer index for rain water",
             "index", "()", "integer", "in", False)
       + ent("ntsw", "index_of_snow_mixing_ratio_in_tracer_concentration_array", "tracer index for snow water",
             "index", "()", "integer", "in", False)
       + ent("ntgl", "index_of_graupel_mixing_ratio_in_tracer_concentration_array", "tracer index for graupel",
             "index", "()", "integer", "in", False)
       + ent("con_g", "gravitational_acceleration", "gravitational acceleration", "m s-2", "()", "real", "in"))
sub(meta, "[errmsg]\n", ADD + "[errmsg]\n")

# final print (cumulative through the last step)
sub(drv, "      subroutine mp_thompson_final(is_initialized, errmsg, errflg)\n\n         implicit none\n",
    "      subroutine mp_thompson_final(is_initialized, errmsg, errflg)\n\n"
    "         use GFS_physics_post, only: wbp, wbp_kdt\n"
    "         implicit none\n")
sub(drv, "         if (.not.is_initialized) return\n\n         call thompson_final()\n",
    "         if (.not.is_initialized) return\n\n"
    "         write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n"
    "         call thompson_final()\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBP").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
