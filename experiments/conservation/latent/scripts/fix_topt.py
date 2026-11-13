#!/usr/bin/env python3
"""TOPT fix: the process-split tendency sum is applied exactly once whatever tend_opt_pbl/gwd say.
(a) GFS_suite_interstitial_3 applies any still-pending process-split sum before convection;
(b) tend_opt_pbl/gwd/rad_scaler = 4 return a CCPP error (they discard a tendency nothing else applies).
usage: fix_topt.py <ufs-weather-model tree>"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp"
I3 = root / "physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_suite_interstitial_3"


def rep(path, pairs):
    s = path.read_text()
    for a, b in pairs:
        n = s.count(a)
        if n != 1:
            sys.exit(f"ABORT {path.name}: {n} x {a[:70]!r}")
        s = s.replace(a, b)
    path.write_text(s)
    print("patched", path)


rep(I3.with_suffix(".F90"), [
    ("               xlon, xlat, gt0, gq0, sigmain,sigmaout,qmicro,           &\n",
     "               xlon, xlat, gt0, gq0, gu0, gv0, dtp, dtdt, dudt, dvdt,   &\n"
     "               dqdt, sigmain,sigmaout,qmicro,                           &\n"),
    ("      real(kind=kind_phys), intent(in   ), dimension(:,:)   :: gt0\n"
     "      real(kind=kind_phys), intent(in   ), dimension(:,:,:) :: gq0\n",
     "      real(kind=kind_phys), intent(inout), dimension(:,:)   :: gt0, gu0, gv0\n"
     "      real(kind=kind_phys), intent(inout), dimension(:,:,:) :: gq0\n"
     "      real(kind=kind_phys), intent(in   )                   :: dtp\n"
     "      real(kind=kind_phys), intent(inout), dimension(:,:)   :: dtdt, dudt, dvdt\n"
     "      real(kind=kind_phys), intent(inout), dimension(:,:,:) :: dqdt\n"),
    ("      ! Initialize CCPP error handling variables\n      errmsg = ''\n      errflg = 0\n",
     "      ! Initialize CCPP error handling variables\n      errmsg = ''\n      errflg = 0\n"
     "\n"
     "      ! apply the process-split sum still pending (a tend_opt_* = 2 with no later 3), once, before convection\n"
     "      do k=1,levs\n"
     "        do i=1,im\n"
     "          if (dtdt(i,k) /= zero) gt0(i,k) = gt0(i,k) + dtp*dtdt(i,k)\n"
     "          if (dudt(i,k) /= zero) gu0(i,k) = gu0(i,k) + dtp*dudt(i,k)\n"
     "          if (dvdt(i,k) /= zero) gv0(i,k) = gv0(i,k) + dtp*dvdt(i,k)\n"
     "          dtdt(i,k) = zero\n"
     "          dudt(i,k) = zero\n"
     "          dvdt(i,k) = zero\n"
     "          do n=1,ntrac\n"
     "            if (dqdt(i,k,n) /= zero) gq0(i,k,n) = gq0(i,k,n) + dtp*dqdt(i,k,n)\n"
     "            dqdt(i,k,n) = zero\n"
     "          enddo\n"
     "        enddo\n"
     "      enddo\n"),
])

META_GT0 = """[gt0]
  standard_name = air_temperature
  long_name = air temperature
  units = K
  dimensions = (horizontal_loop_extent,vertical_layer_dimension)
  type = real
  kind = kind_phys
  intent = in
[gq0]
  standard_name = tracer_concentration
  long_name = tracer concentration
  units = kg kg-1
  dimensions = (horizontal_loop_extent,vertical_layer_dimension,number_of_tracers)
  type = real
  kind = kind_phys
  intent = in
"""
NEW = META_GT0.replace("intent = in\n", "intent = inout\n") + """[gu0]
  standard_name = x_wind
  long_name = zonal wind
  units = m s-1
  dimensions = (horizontal_loop_extent,vertical_layer_dimension)
  type = real
  kind = kind_phys
  intent = inout
[gv0]
  standard_name = y_wind
  long_name = meridional wind
  units = m s-1
  dimensions = (horizontal_loop_extent,vertical_layer_dimension)
  type = real
  kind = kind_phys
  intent = inout
[dtp]
  standard_name = timestep_for_physics
  long_name = physics timestep
  units = s
  dimensions = ()
  type = real
  kind = kind_phys
  intent = in
[dtdt]
  standard_name = process_split_cumulative_tendency_of_air_temperature
  long_name = air temperature tendency due to model physics
  units = K s-1
  dimensions = (horizontal_loop_extent,vertical_layer_dimension)
  type = real
  kind = kind_phys
  intent = inout
[dudt]
  standard_name = process_split_cumulative_tendency_of_x_wind
  long_name = zonal wind tendency due to model physics
  units = m s-2
  dimensions = (horizontal_loop_extent,vertical_layer_dimension)
  type = real
  kind = kind_phys
  intent = inout
[dvdt]
  standard_name = process_split_cumulative_tendency_of_y_wind
  long_name = meridional wind tendency due to model physics
  units = m s-2
  dimensions = (horizontal_loop_extent,vertical_layer_dimension)
  type = real
  kind = kind_phys
  intent = inout
[dqdt]
  standard_name = process_split_cumulative_tendency_of_tracers
  long_name = tendency of the tracers due to model physics
  units = kg kg-1 s-1
  dimensions = (horizontal_loop_extent,vertical_layer_dimension,number_of_tracers)
  type = real
  kind = kind_phys
  intent = inout
"""
rep(I3.with_suffix(".meta"), [(META_GT0, NEW)])

N = root / "physics/physics/Interstitials/UFS_SCM_NEPTUNE"


def err4(ind, opt, what):
    return (f"{ind}errflg = 1\n"
            f"{ind}errmsg = '{opt} = 4 would discard the {what} (no other scheme applies them): use 1, 2 or 3'\n"
            f"{ind}return\n")


rep(N / "GFS_PBL_generic_post.F90", [("          exit case_PBL_ten\n", err4("          ", "tend_opt_pbl", "PBL tendencies"))])
rep(N / "GFS_GWD_generic_post.F90", [("          exit case_GWD_ten\n", err4("          ", "tend_opt_gwd", "GWD tendencies"))])
rep(root / "physics/physics/PBL/MYNN_EDMF/mynnedmf_wrapper_post.F90",
    [("        exit case_pbl_ten\n", err4("        ", "tend_opt_pbl", "PBL tendencies"))])
rep(N / "dcyc2t3.f", [("          exit case_rad_scaler_ten\n",
                       "          errflg = 1\n"
                       "          errmsg = 'tend_opt_rad_scaler = 4 would discard the '//\n"
                       "     &             'radiative heating: use 1, 2 or 3'\n"
                       "          return\n")])
