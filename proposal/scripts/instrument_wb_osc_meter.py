#!/usr/bin/env python3
"""Answer-neutral per-scheme column meter for the step-771 oscillation (v1 tree): a read-only CCPP scheme osc_meter, inserted after each scheme of interest, plus dycore prints in fv_dynamics/atmosphere.F90.
Usage: python3 instrument_wb_osc_meter.py <ufs_model.fd>
Run-time env: OSC_MK0 (first step printed; unset = never), OSC_BOX="lon0 lon1 lat0 lat1" (deg, default the 3x3 crash cluster),
OSC_K0 (dycore step offset: step = OSC_K0 + call count of atmosphere_dynamics; set to fhrot*3600/dt for a warm start).
Physics lines: OSM kdt n lon lat + 62 values (n = call number within the step for that column, the order of insertion in the SDF;
fields in FIELDS below). Dycore lines: OSD tag nmap kd lon lat ps + 3 layers (bottom first) x 11 values (DFIELDS).
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root = Path(sys.argv[1])
fv3 = root / "FV3"
cc = fv3 / "ccpp"
phys = cc / "physics/physics/Interstitials/UFS_SCM_NEPTUNE"
sdf = cc / "suites/suite_FV3_GFS_v17_p8_ugwpv1.xml"
cfg = cc / "config/ccpp_prebuild_config.py"
fvd = fv3 / "atmos_cubed_sphere/model/fv_dynamics.F90"
atm = fv3 / "atmos_cubed_sphere/driver/fvGFS/atmosphere.F90"

# scheme after which osc_meter is called (in SDF order); the 2-iteration surface loop calls it twice per entry there
AFTER = ["GFS_suite_stateout_reset", "dcyc2t3", "GFS_suite_interstitial_2", "sfc_diff", "sfc_nst_post",
         "GFS_surface_loop_control_part2", "GFS_surface_composites_post", "GFS_surface_generic_post", "satmedmfvdifq",
         "GFS_PBL_generic_post", "GFS_GWD_generic_post", "GFS_suite_stateout_update", "get_phi_fv3",
         "GFS_DCNV_generic_post", "GFS_SCNV_generic_post", "cnvc90", "mp_thompson_pre", "mp_thompson",
         "mp_thompson_post", "GFS_MP_generic_post", "GFS_physics_post"]

# (local name, standard name, dims, type)
I0, H, HL, HI, HLT = "()", "(horizontal_loop_extent)", "(horizontal_loop_extent,vertical_layer_dimension)", \
    "(horizontal_loop_extent,vertical_interface_dimension)", "(horizontal_loop_extent,vertical_layer_dimension,number_of_tracers)"
ARGS = [
    ("im", "horizontal_loop_extent", I0, "integer"), ("levs", "vertical_layer_dimension", I0, "integer"),
    ("ntrac", "number_of_tracers", I0, "integer"), ("kdt", "index_of_timestep", I0, "integer"),
    ("dtp", "timestep_for_physics", I0, "real"), ("xlon", "longitude", H, "real"), ("xlat", "latitude", H, "real"),
    ("ntqv", "index_of_specific_humidity_in_tracer_concentration_array", I0, "integer"),
    ("ntcw", "index_of_cloud_liquid_water_mixing_ratio_in_tracer_concentration_array", I0, "integer"),
    ("ntrw", "index_of_rain_mixing_ratio_in_tracer_concentration_array", I0, "integer"),
    ("ntiw", "index_of_cloud_ice_mixing_ratio_in_tracer_concentration_array", I0, "integer"),
    ("ntsw", "index_of_snow_mixing_ratio_in_tracer_concentration_array", I0, "integer"),
    ("ntgl", "index_of_graupel_mixing_ratio_in_tracer_concentration_array", I0, "integer"),
    ("tgrs", "air_temperature", HL, "real"), ("ugrs", "x_wind", HL, "real"), ("vgrs", "y_wind", HL, "real"),
    ("qgrs", "tracer_concentration", HLT, "real"),
    ("gt0", "air_temperature_of_new_state", HL, "real"), ("gu0", "x_wind_of_new_state", HL, "real"),
    ("gv0", "y_wind_of_new_state", HL, "real"), ("gq0", "tracer_concentration_of_new_state", HLT, "real"),
    ("dtdt", "process_split_cumulative_tendency_of_air_temperature", HL, "real"),
    ("dqdt", "process_split_cumulative_tendency_of_tracers", HLT, "real"),
    ("prsi", "air_pressure_at_interface", HI, "real"), ("prsl", "air_pressure", HL, "real"),
    ("phii", "geopotential_at_interface", HI, "real"),
    ("tsfc", "surface_skin_temperature", H, "real"), ("tsfc_water", "surface_skin_temperature_over_water", H, "real"),
    ("tsurf_water", "surface_skin_temperature_after_iteration_over_water", H, "real"),
    ("tseal", "surface_skin_temperature_for_nsst", H, "real"), ("tref", "reference_sea_surface_temperature", H, "real"),
    ("xt", "heat_content_in_diurnal_thermocline", H, "real"), ("xz", "diurnal_thermocline_layer_thickness", H, "real"),
    ("dt_cool", "molecular_sublayer_temperature_correction_in_sea_water", H, "real"),
    ("z_c", "molecular_sublayer_thickness_in_sea_water", H, "real"),
    ("qss_water", "surface_specific_humidity_over_water", H, "real"),
    ("cd_water", "surface_drag_coefficient_for_momentum_in_air_over_water", H, "real"),
    ("cdq_water", "surface_drag_coefficient_for_heat_and_moisture_in_air_over_water", H, "real"),
    ("rb_water", "bulk_richardson_number_at_lowest_model_level_over_water", H, "real"),
    ("uustar_water", "surface_friction_velocity_over_water", H, "real"),
    ("wind", "wind_speed_at_lowest_model_layer", H, "real"),
    ("evap_water", "kinematic_surface_upward_latent_heat_flux_over_water", H, "real"),
    ("hflx_water", "kinematic_surface_upward_sensible_heat_flux_over_water", H, "real"),
    ("heat", "kinematic_surface_upward_sensible_heat_flux_reduced_by_surface_roughness_and_vegetation", H, "real"),
    ("evap", "surface_upward_specific_humidity_flux", H, "real"),
    ("rbsoil", "bulk_richardson_number_at_lowest_model_level", H, "real"),
    ("stress", "surface_wind_stress", H, "real"), ("hpbl", "atmosphere_boundary_layer_thickness", H, "real"),
    ("dkt", "atmosphere_heat_diffusivity", HL, "real"), ("oceanfrac", "sea_area_fraction", H, "real"),
    ("kcnv", "flag_deep_convection", H, "integer"),
]
FIELDS = ([f"{v}{k}" for k in (1, 2, 3) for v in ("T", "qv", "qc", "qr", "qisg", "u", "v")]
          + [f"{v}{k}" for k in (1, 2, 3) for v in ("dTps", "dqps")]
          + ["Tgrs1", "qgrs1", "ugrs1", "vgrs1", "prsi1", "prsi2", "prsl1", "dzphii1", "dzhyd1", "rhoth1",
             "tsfc", "tsfc_wat", "tsurf_wat", "tseal", "tref", "xt", "xz", "dt_cool", "z_c", "qss_wat",
             "cd_wat", "cdq_wat", "rb_wat", "ustar_wat", "wind", "evap_wat", "hflx_wat", "heat", "evap", "rbsoil",
             "stress", "hpbl", "dkt1", "oceanfrac", "kcnv"])
assert len(FIELDS) == 62

decl = []
for n, s, d, t in ARGS:
    if t == "integer":
        decl.append(f"    integer, intent(in) :: {n}" + ("(:)" if d == H else ""))
    else:
        rk = {I0: "", H: "(:)", HL: "(:,:)", HI: "(:,:)", HLT: "(:,:,:)"}[d]
        decl.append(f"    real(kind=kind_phys), intent(in) :: {n}{rk}")
names = [a[0] for a in ARGS] + ["errmsg", "errflg"]
arglist, line = "", ""
for nm in names:
    if len(line) + len(nm) > 90:
        arglist += line + "&\n      "
        line = ""
    line += nm + ", "
arglist = (arglist + line).rstrip(", ")
F90 = f"""!> \\file osc_meter.F90
!! Read-only column meter for the step-771 oscillation (prints only; changes no state).
module osc_meter
  use machine, only: kind_phys
  implicit none
  private
  public :: osc_meter_run
  integer, save :: mk0 = -2
  real(kind=kind_phys), save :: box(4) = (/71.7, 74.8, -13.3, -10.2/)
  integer, parameter :: ncmax = 64
  integer, save :: nc = 0, ckey(ncmax) = 0, ckdt(ncmax) = -1, ccnt(ncmax) = 0
contains
!> \\section arg_table_osc_meter_run Argument Table
!! \\htmlinclude osc_meter_run.html
!!
  subroutine osc_meter_run({arglist})
{chr(10).join(decl)}
    character(len=*), intent(out) :: errmsg
    integer, intent(out) :: errflg
    character(len=64) :: env
    integer :: i, k, key, c, j
    real(kind=kind_phys) :: lo, la, v(62), qsg, qv, rho
    errmsg = ''
    errflg = 0
    if (mk0 < -1) then
      mk0 = huge(1)
      call get_environment_variable('OSC_MK0', env)
      if (len_trim(env) > 0) read(env,*) mk0
      call get_environment_variable('OSC_BOX', env)
      if (len_trim(env) > 0) read(env,*) box
      write(*,'(a,i12,4f9.3)') 'OSC_METER ', mk0, box
    endif
    if (kdt < mk0) return
    do i = 1, im
      lo = xlon(i) * 57.29577951308232_kind_phys
      la = xlat(i) * 57.29577951308232_kind_phys
      if (lo < box(1) .or. lo > box(2) .or. la < box(3) .or. la > box(4)) cycle
      key = nint(lo*100.)*100000 + nint((la+90.)*100.)
      c = 0
      do j = 1, nc
        if (ckey(j) == key) c = j
      enddo
      if (c == 0) then
        if (nc == ncmax) cycle
        nc = nc + 1
        c = nc
        ckey(c) = key
      endif
      if (ckdt(c) /= kdt) then
        ckdt(c) = kdt
        ccnt(c) = 0
      endif
      ccnt(c) = ccnt(c) + 1
      j = 0
      do k = 1, 3
        qsg = 0.
        if (ntiw > 0) qsg = qsg + gq0(i,k,ntiw)
        if (ntsw > 0) qsg = qsg + gq0(i,k,ntsw)
        if (ntgl > 0) qsg = qsg + gq0(i,k,ntgl)
        v(j+1:j+7) = (/gt0(i,k), gq0(i,k,ntqv), gq0(i,k,ntcw), gq0(i,k,ntrw), qsg, gu0(i,k), gv0(i,k)/)
        j = j + 7
      enddo
      do k = 1, 3
        v(j+1:j+2) = (/dtdt(i,k)*dtp, dqdt(i,k,ntqv)*dtp/)
        j = j + 2
      enddo
      qv = gq0(i,1,ntqv)
      rho = 0.622*prsl(i,1) / (287.04*gt0(i,1)*(qv/(1.-qv) + 0.622))
      v(j+1:j+10) = (/tgrs(i,1), qgrs(i,1,ntqv), ugrs(i,1), vgrs(i,1), prsi(i,1), prsi(i,2), prsl(i,1), &
                      (phii(i,2)-phii(i,1))/9.80665, (prsi(i,1)-prsi(i,2))*(1.-qv)/(9.80665*rho), rho/)
      j = j + 10
      v(j+1:j+25) = (/tsfc(i), tsfc_water(i), tsurf_water(i), tseal(i), tref(i), xt(i), xz(i), dt_cool(i), z_c(i), &
                      qss_water(i), cd_water(i), cdq_water(i), rb_water(i), uustar_water(i), wind(i), evap_water(i), &
                      hflx_water(i), heat(i), evap(i), rbsoil(i), stress(i), hpbl(i), dkt(i,1), oceanfrac(i), &
                      real(kcnv(i), kind_phys)/)
      write(*,'(a,i7,i4,2f9.3,62es14.6)') 'OSM ', kdt, ccnt(c), lo, la, v
    enddo
  end subroutine osc_meter_run
end module osc_meter
"""
UNITS = {}
for mf in sorted((cc / "data").glob("*.meta")):
    sn = None
    for ln in mf.read_text().split("\n"):
        t = ln.strip()
        if t.startswith("["):
            sn = None
        elif t.startswith("standard_name") and "=" in t:
            sn = t.split("=", 1)[1].strip()
        elif t.startswith("units") and "=" in t and sn:
            UNITS.setdefault(sn, t.split("=", 1)[1].strip())
missing = [s_ for _, s_, _, _ in ARGS if s_ not in UNITS]
if missing:
    sys.exit(f"ABORT: no host units for {missing}")
META = ["[ccpp-table-properties]", "  name = osc_meter", "  type = scheme", "  dependencies = ../../hooks/machine.F", "",
        "[ccpp-arg-table]", "  name = osc_meter_run", "  type = scheme"]
for n, s, d, t in ARGS:
    META += [f"[{n}]", f"  standard_name = {s}", f"  long_name = {s.replace('_', ' ')}", f"  units = {UNITS[s]}", f"  dimensions = {d}", f"  type = {t}"]
    if t == "real":
        META.append("  kind = kind_phys")
    META.append("  intent = in")
META += ["[errmsg]", "  standard_name = ccpp_error_message", "  long_name = error message", "  units = none",
         "  dimensions = ()", "  type = character", "  kind = len=*", "  intent = out",
         "[errflg]", "  standard_name = ccpp_error_code", "  long_name = error code", "  units = 1",
         "  dimensions = ()", "  type = integer", "  intent = out", ""]

edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match(es), found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


# suite: osc_meter after each listed scheme (all occurrences inside <scheme> tags are unique in this SDF)
for sch in AFTER:
    tag = f"<scheme>{sch}</scheme>\n"
    s = edits.get(sdf) or sdf.read_text()
    i = s.find(tag)
    if s.count(tag) != 1:
        sys.exit(f"ABORT SDF: {sch} found {s.count(tag)} times")
    j = i + len(tag)
    ind = s[s.rfind("\n", 0, i) + 1:i]
    edits[sdf] = s[:j] + f"{ind}<scheme>osc_meter</scheme>\n" + s[j:]
sub(cfg, "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_debug.F90',\n",
    "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_debug.F90',\n"
    "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/osc_meter.F90',\n")

# dycore: a print routine in fv_dynamics_mod, called inside fv_dynamics and from atmosphere.F90
DPRINT = """
 subroutine osc_dprint(tag, nm, bd, npz, ncnst, agrid, u, v, w, pt, delp, q, delz, ua, va, ps)
   use tracer_manager_mod, only: osc_gti => get_tracer_index
   use field_manager_mod,  only: osc_ma => MODEL_ATMOS
   character(len=*), intent(in) :: tag
   integer, intent(in) :: nm, npz, ncnst
   type(fv_grid_bounds_type), intent(in) :: bd
   real, intent(in) :: agrid(bd%isd:bd%ied,bd%jsd:bd%jed,2)
   real, intent(in), dimension(bd%isd:bd%ied  ,bd%jsd:bd%jed+1,npz) :: u
   real, intent(in), dimension(bd%isd:bd%ied+1,bd%jsd:bd%jed  ,npz) :: v
   real, intent(in) :: w(bd%isd:,bd%jsd:,1:)
   real, intent(in) :: pt(bd%isd:bd%ied,bd%jsd:bd%jed,npz), delp(bd%isd:bd%ied,bd%jsd:bd%jed,npz)
   real, intent(in) :: q(bd%isd:bd%ied,bd%jsd:bd%jed,npz,ncnst)
   real, intent(in) :: delz(bd%is:,bd%js:,1:)
   real, intent(in), dimension(bd%isd:bd%ied,bd%jsd:bd%jed,npz) :: ua, va
   real, intent(in) :: ps(bd%isd:bd%ied,bd%jsd:bd%jed)
   character(len=64) :: env
   integer :: i, j, k, m, liq, rain
   real(kind=8) :: lo, la, x(33)
   if (osc_mk0 < -1) then
     osc_mk0 = huge(1)
     call get_environment_variable('OSC_MK0', env)
     if (len_trim(env) > 0) read(env,*) osc_mk0
     call get_environment_variable('OSC_BOX', env)
     if (len_trim(env) > 0) read(env,*) osc_box
     osc_k0 = 0
     call get_environment_variable('OSC_K0', env)
     if (len_trim(env) > 0) read(env,*) osc_k0
   endif
   if (osc_k0 + osc_kd < osc_mk0) return
   liq = osc_gti(osc_ma, 'liq_wat')
   rain = osc_gti(osc_ma, 'rainwat')
   do j = bd%js, bd%je
     do i = bd%is, bd%ie
       lo = agrid(i,j,1) * 57.29577951308232d0
       la = agrid(i,j,2) * 57.29577951308232d0
       if (lo < osc_box(1) .or. lo > osc_box(2) .or. la < osc_box(3) .or. la > osc_box(4)) cycle
       m = 0
       do k = npz, npz-2, -1
         x(m+1:m+11) = (/ real(pt(i,j,k),8), real(delp(i,j,k),8), real(delz(i,j,k),8), real(w(i,j,k),8), &
                          real(ua(i,j,k),8), real(va(i,j,k),8), real(u(i,j,k),8), real(v(i,j,k),8), &
                          real(q(i,j,k,1),8), real(q(i,j,k,liq),8), real(q(i,j,k,rain),8) /)
         m = m + 11
       enddo
       write(*,'(a,a8,i3,i7,2f9.3,es15.7,33es15.7)') 'OSD ', tag, nm, osc_k0 + osc_kd, lo, la, real(ps(i,j),8), x
     enddo
   enddo
 end subroutine osc_dprint
"""
sub(fvd, "\ncontains\n", "\n  integer, public, save :: osc_kd = 0, osc_k0 = 0, osc_mk0 = -2\n"
                         "  real(kind=8), public, save :: osc_box(4) = (/71.7d0, 74.8d0, -13.3d0, -10.2d0/)\n"
                         "  public :: osc_dprint\ncontains\n" + DPRINT)
CALLARGS = "bd, npz, ncnst, gridstruct%agrid, u, v, w, pt, delp, q, delz, ua, va, ps)"
sub(fvd, "      call dyn_core(", "      call osc_dprint('PRE_DYN', n_map, " + CALLARGS + "\n      call dyn_core(")
sub(fvd, "         call Lagrangian_to_Eulerian(",
    "         call osc_dprint('DYN', n_map, " + CALLARGS + "\n         call Lagrangian_to_Eulerian(")
sub(fvd, "  enddo    ! n_map loop\n", "         call osc_dprint('REMAP', n_map, " + CALLARGS + "\n  enddo    ! n_map loop\n")
sub(fvd, "  end subroutine fv_dynamics\n", "  call osc_dprint('FVEND', 0, " + CALLARGS + "\n  end subroutine fv_dynamics\n")
s = fvd.read_text()
if s.count("\n911  call cubed_to_latlon") != 1:
    sys.exit("ABORT fv_dynamics: 911 label")

ATMARGS = ("Atm(n)%bd, Atm(n)%npz, Atm(n)%ncnst, Atm(n)%gridstruct%agrid, Atm(n)%u, Atm(n)%v, Atm(n)%w, Atm(n)%pt, "
           "Atm(n)%delp, Atm(n)%q, Atm(n)%delz, Atm(n)%ua, Atm(n)%va, Atm(n)%ps)")


def atmcall(tag):
    a = f"call osc_dprint('{tag}', 0, " + ATMARGS
    out, line = [], "   "
    for tok in a.split(" "):
        if len(line) + len(tok) > 100:
            out.append(line + "&")
            line = "        "
        line += tok + " "
    out.append(line.rstrip())
    return "\n".join(out) + "\n"


sub(atm, "   a_step = a_step + 1\n", "   a_step = a_step + 1\n   osc_kd = a_step\n" + atmcall("ATM_IN"))
sub(atm, "    call mpp_clock_end (id_dynam)\n", atmcall("ATM_FVD") + "    call mpp_clock_end (id_dynam)\n")
sub(atm, "   call mpp_clock_end (id_subgridz)\n", atmcall("ATM_SGZ") + "   call mpp_clock_end (id_subgridz)\n")
if atm.read_text().count("    call fv_update_phys( dt_atmos,") != 1:
    sys.exit("ABORT atmosphere.F90: fv_update_phys call")
# state update: print at entry (once n is set) and after fv_update_phys
A0 = "   nq_adv = nq - dnats\n\n   if( nq<3 ) call mpp_error(FATAL, 'GFS phys must have 3 interactive tracers')\n"
sub(atm, A0, A0 + atmcall("SU_IN"))
# the fv_update_phys call ends at the first line after it that does not end with '&'
s = edits[atm]
i = s.find("    call fv_update_phys( dt_atmos,")
lines = s[i:].split("\n")
n = 0
while lines[n].rstrip().endswith("&"):
    n += 1
end = i + len("\n".join(lines[:n + 1])) + 1
edits[atm] = s[:end] + atmcall("SU_UPD") + s[end:]
sub(atm, "use fv_dynamics_mod,    only: fv_dynamics, wbd, wb_water\n",
    "use fv_dynamics_mod,    only: fv_dynamics, wbd, wb_water, osc_dprint, osc_kd\n")

for txt in [F90, edits[fvd], edits[atm]]:
    for ln in txt.split("\n"):
        if len(ln) > 132 and "osc" in ln:
            sys.exit(f"ABORT: line > 132: {ln[:60]!r}")
(phys / "osc_meter.F90").write_text(F90)
(phys / "osc_meter.meta").write_text("\n".join(META))
for p, s in edits.items():
    p.with_suffix(p.suffix + ".preOSC").write_text(p.read_text())
    p.write_text(s)
print("osc meter installed:", ", ".join(p.name for p in edits), "+ osc_meter.F90/.meta;", len(AFTER), "insertions")
