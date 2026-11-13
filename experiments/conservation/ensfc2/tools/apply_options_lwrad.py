#!/usr/bin/env python3
"""Round-3 surface energy OPTIONS (gfs_physics_nml switches, all default off; off = the stock code path).
Apply on top of the bug fixes (SI1 SI2 NP1 QR1 CMC FL1), with or without meters.
Usage: apply_options.py <ufs-weather-model>

  noahmp_canopy_heat = 0|1|2   Noah-MP canopy heat. 1 (CH1): massless canopy, hcv leaves the Newton step, canhs = 0.
                               2 (CH2): canopy heat storage over the whole step, canhs = hcv*(tv_new - tv_start)/dt,
                               and canwater keeps tv (melt/freeze latent heat goes to the soil through CMC).
  precip_phase_host  = T       PH1: GFS_MP_generic_post heats the lowest layer by hfus x the convective precipitation
                               the host calls snow (Thompson branch, tsfc < 273.15). PH2: Noah-MP soil takes that
                               decision for its convective precipitation (instead of NM10's sfctmp < tfrz).
                               PH3: Noah-MP glacier takes srflag as its frozen fraction (instead of its T rule).
  noahmp_sw_radshare = T       SW1: Noah-MP (soil and glacier) absorbs the radiation's share for the land:
                               land-only cells the cell net SW; mixed cells the radiation-time land albedos x this
                               step's band fluxes. sav/sag are rescaled (canopy/ground partition kept).
  lw_sfc_consistent  = T       LW1: the surfaces report the non-solar flux they booked (Noah-MP: its net LW; sea ice:
                               its linearised non-solar flux minus the SH and LH the atmosphere receives) through
                               adjsfculw_land/ice; GFS_surface_composites_post heats the lowest layer by
                               sum_type frac*(booked net up LW) - (radiation-time net up LW).
  sfc_evap_enthalpy  = T       EV1: Noah-MP soil columns report E*(h_land_source - h_v(T1)) in frame F (encpl):
                               the water's enthalpy where the land loses it (liquid c_w(T-tfrz), ice c_i(T-tfrz), canopy
                               water at tfrz) plus the latent heat charged, minus the vapour's h_v(T1) = hvap + cp_v(T1-T0);
                               GFS_surface_composites_post heats the lowest layer by land fraction x that.
  noahmp_heat_advect = T       AD1: soil water moved between layers (soilwater + groundwater) carries c_w (T_upstream);
                               boundary flows keep their layer temperature (booked at that T).
  noahmp_kirchhoff   = T       KF1: phasechange heats the remainder into the layer at its new composition, i.e. latent
                               heat L_f(T) = hfus + (c_w - c_i)(T - tfrz) with Noah-MP's own heat capacities.
Every anchor must match exactly once; nothing is written unless all match."""
import sys
from pathlib import Path

top = Path(sys.argv[1]) / "UFSATM/ccpp"
root = top / "physics/physics"
gtd = top / "data/GFS_typedefs.F90"
gtm = top / "data/GFS_typedefs.meta"
ctd = top / "data/CCPP_typedefs.F90"
ctm = top / "data/CCPP_typedefs.meta"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
drvm = root / "SFC_Models/Land/Noahmp/noahmpdrv.meta"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
icem = root / "SFC_Models/SeaIce/CICE/sfc_sice.meta"
mpp = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90"
mppm = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.meta"
cpo = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.F90"
cpom = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.meta"
edits = {}


def get(p):
    return edits.get(p) or p.read_text()


def sub(path, old, new, after=None, count=1):
    s = get(path)
    if after is not None:
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:70]!r}")
        i = s.index(after)
        j = s.find(old, i)
        if j < 0:
            sys.exit(f"ABORT {path.name}: {old.strip()[:70]!r} not after anchor {after.strip()[:50]!r}")
        edits[path] = s[:j] + new + s[j + len(old):]
        return
    if s.count(old) != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {s.count(old)}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def pre(path, a, t, **kw):
    sub(path, a, t + a, **kw)


def post(path, a, t, **kw):
    sub(path, a, a + t, **kw)


def post_line(path, frag, text):
    """insert text after the unique line containing frag"""
    s = get(path)
    lines = s.splitlines(keepends=True)
    hits = [k for k, l in enumerate(lines) if frag in l]
    if len(hits) != 1:
        sys.exit(f"ABORT {path.name}: line fragment count {len(hits)}: {frag!r}")
    lines.insert(hits[0] + 1, text)
    edits[path] = "".join(lines)


def meta_entry(name, std, long, units, dims="()", typ="real", kind=True, intent=None, optional=False, active=None):
    t = f"[{name}]\n  standard_name = {std}\n  long_name = {long}\n  units = {units}\n  dimensions = {dims}\n  type = {typ}\n"
    if kind and typ == "real":
        t += "  kind = kind_phys\n"
    if active:
        t += f"  active = ({active})\n"
    if intent:
        t += f"  intent = {intent}\n"
    if optional:
        t += "  optional = True\n"
    return t


def meta_append(path, text):
    s = get(path)
    if not s.endswith("\n"):
        s += "\n"
    edits[path] = s + text


# ================================================================== rrtmg_lw_post: radiation-time upward LW for LW1
# (RRTMGP fills surface_upwelling_longwave_flux_on_radiation_timestep; RRTMG did not)
rlp = root / "Radiation/RRTMG/rrtmg_lw_post.F90"
rlpm = root / "Radiation/RRTMG/rrtmg_lw_post.meta"
sub(rlp, "                 errmsg, errflg)\n", "                 errmsg, errflg, sfculw)\n",
    after="      subroutine rrtmg_lw_post_run (")
post(rlp, "      real(kind=kind_phys), dimension(im),         intent(inout) ::  tsflw, sfcdlw\n",
     "      real(kind=kind_phys), dimension(:), optional, intent(inout) ::  sfculw\n")
post(rlp, "        sfcdlw(:) = sfcflw(:)%dnfxc\n", "        if (present(sfculw)) sfculw(:) = sfcflw(:)%upfxc\n")
meta_append(rlpm, meta_entry("sfculw", "surface_upwelling_longwave_flux_on_radiation_timestep",
                             "total sky sfc upward lw flux", "W m-2", dims="(horizontal_loop_extent)",
                             intent="inout", optional=True))

for p, s in edits.items():
    p.write_text(s)
    print("options", p.name)
