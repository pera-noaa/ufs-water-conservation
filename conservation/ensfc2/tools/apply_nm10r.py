#!/usr/bin/env python3
"""NM10r: revised NM10 (water diff 17). Noah-MP's convective precipitation phase is the host's decision, recovered
from srflag (GFS_MP_generic_post, Thompson branch: csnow = rainc when the surface composite tsfc < 273.15), instead
of NM10's sfctmp < tfrz. The surface then receives frozen exactly what the host classifies as frozen.
Usage: apply_nm10r.py <ufs-weather-model>   (on fx; not combined with apply_options.py, which carries the same code as PH2)"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
edits = {}


def sub(path, old, new, after=None):
    s = edits.get(path) or path.read_text()
    if after is not None:
        assert s.count(after) == 1, after
        i = s.index(after)
        j = s.find(old, i)
        assert j >= 0, old
        edits[path] = s[:j] + new + s[j + len(old):]
        return
    assert s.count(old) == 1, old
    edits[path] = s.replace(old, new)


SF = "  subroutine noahmp_sflx (parameters, &\n"
sub(lsm, "                   ,errmsg, errflg)\n", "                   ,errmsg, errflg, fpcv_host)\n", after=SF)
sub(lsm, "  character(len=*), intent(inout)    :: errmsg\n  integer,          intent(inout)    :: errflg\n",
    "  character(len=*), intent(inout)    :: errmsg\n  integer,          intent(inout)    :: errflg\n"
    "  real (kind=kind_phys), optional, intent(in)  :: fpcv_host !< host frozen fraction of convective precipitation\n",
    after=SF)
sub(lsm, "  real (kind=kind_phys)              :: q1\n", "  real (kind=kind_phys)              :: q1\n"
    "  real (kind=kind_phys)              :: fpcvh\n", after=SF)
sub(lsm, "   call atm (parameters,ep_2, epsm1, sfcprs  ,sfctmp   ,q2      ,    &\n",
    "   fpcvh = -1.\n   if (present(fpcv_host)) fpcvh = fpcv_host\n\n"
    "   call atm (parameters,ep_2, epsm1, sfcprs  ,sfctmp   ,q2      ,    &\n")
sub(lsm, "             swdown  ,bdfall   ,rain    ,snow    ,fp      ,fpice   , prcp )     \n",
    "             swdown  ,bdfall   ,rain    ,snow    ,fp      ,fpice   , prcp, fpcvh )\n")
AT = "  subroutine atm (parameters,ep_2,epsm1,sfcprs  ,sfctmp   ,q2      ,       &\n"
sub(lsm, "                  swdown  ,bdfall   ,rain    ,snow    ,fp      , fpice   ,prcp )     \n",
    "                  swdown  ,bdfall   ,rain    ,snow    ,fp      , fpice   ,prcp, fpcvh )\n", after=AT)
sub(lsm, "  real (kind=kind_phys)                          , intent(in)  :: cosz     !< cosine solar zenith angle [0-1]\n",
    "  real (kind=kind_phys)                          , intent(in)  :: cosz     !< cosine solar zenith angle [0-1]\n"
    "  real (kind=kind_phys)                          , intent(in)  :: fpcvh    !< host frozen fraction of convective precipitation (< 0: sfctmp rule)\n",
    after=AT)
sub(lsm, "        ! the microphysics fraction is for grid-scale precipitation; convective precipitation is snow below freezing\n"
         "        if(prcpconv + prcpshcv > 0.) then\n          fpcv = 0.0\n          if(sfctmp < tfrz) fpcv = 1.0\n",
    "        ! the microphysics fraction is for grid-scale precipitation; convective precipitation takes the host's\n"
    "        ! decision (srflag), or is snow below freezing when the host gives none\n"
    "        if(prcpconv + prcpshcv > 0.) then\n          fpcv = 0.0\n          if(sfctmp < tfrz) fpcv = 1.0\n"
    "          if(fpcvh >= 0.) fpcv = fpcvh\n")
sub(drv, "  type(noahmp_parameters) :: parameters\n", "  type(noahmp_parameters) :: parameters\n  real(kind=kind_phys) :: fpcvh\n",
    after="  subroutine noahmpdrv_run ")
SC = "        call noahmp_sflx (parameters                                          , &\n"
sub(drv, SC,
    "        ! the host's convective decision (GFS_MP_generic_post: csnow = rainc when tsfc < 273.15), from srflag\n"
    "        fpcvh = -1.\n"
    "        if (precip_convective > 0.) then\n"
    "          fpcvh = 0.\n"
    "          if (srflag(i)*precipitation_forcing - (precip_snow + precip_graupel + precip_hail) &\n"
    "              > 0.5*precip_convective) fpcvh = 1.\n"
    "        endif\n" + SC)
sub(drv, "          errmsg                ,errflg                )\n",
    "          errmsg                ,errflg                ,                        &\n"
    "          fpcv_host=fpcvh)\n", after=SC)
for p, s in edits.items():
    p.write_text(s)
    print("nm10r", p.name)
