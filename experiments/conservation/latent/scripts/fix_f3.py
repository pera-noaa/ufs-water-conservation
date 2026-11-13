#!/usr/bin/env python3
"""F3 fix for SAMF deep/shallow wet scavenging of chemical tracers.
  booking: chem_pw booked with eta(k) (the flux-form loss uses eta(k)*(ercko-ecko)); borrowing else-branch adds the
           layer's wet_dep back to the tracer before zeroing it (base zeroes it first, losing that mass).
  export:  new bucket accumulator Diag%cnv_wetdep(im,ntchm) [kg m-2], filled by both schemes with the column sum of
           the final wet_dep, zeroed with the other buckets, written as 'cnv_wetdep_<tracer>'.
usage: fix_f3.py <ufs-weather-model tree> booking|export|both"""
import sys
from pathlib import Path

top = Path(sys.argv[1]) / "UFSATM/ccpp"
mode = sys.argv[2]
SAMF = top / "physics/physics/CONV/SAMF"


def rep(path, pairs):
    s = path.read_text()
    for a, b in pairs:
        n = s.count(a)
        if n != 1:
            sys.exit(f"ABORT {path.name}: {n} x {a[:70]!r}")
        s = s.replace(a, b)
    path.write_text(s)
    print("patched", path)


BOOK = ("                   chem_pw(i,k,n) = c0t(i,k) * dz * tem * eta(i,k-1)\n",
        "                   chem_pw(i,k,n) = c0t(i,k) * dz * tem * eta(i,k)\n")

if mode in ("booking", "both"):
    rep(SAMF / "samfdeepcnv.f", [BOOK, (
        "                      wet_dep(i,k,n) = 0.0_conv_wp\n"
        "                      new_qtr(i,k,kk) = new_qtr(i,k,kk)\n"
        "     &                                + wet_dep(i,k,n) / dp\n",
        "                      new_qtr(i,k,kk) = new_qtr(i,k,kk)\n"
        "     &                                + wet_dep(i,k,n) / dp\n"
        "                      wet_dep(i,k,n) = 0.0_conv_wp\n")])
    rep(SAMF / "samfshalcnv.f", [BOOK, (
        "                      wet_dep(i,k,n) = 0.0_conv_wp\n"
        "                      new_qtr(i,k,kk) = new_qtr(i,k,kk) + wet_dep(i,k,n)\n"
        "     &                                / dp\n",
        "                      new_qtr(i,k,kk) = new_qtr(i,k,kk) + wet_dep(i,k,n)\n"
        "     &                                / dp\n"
        "                      wet_dep(i,k,n) = 0.0_conv_wp\n")])

ACC = ("!  column wet deposition of chemical tracers into the bucket (kg m-2)\n"
       "      if (do_aerosols) then\n"
       "        do n = 1, ntc\n"
       "          do i = 1, im\n"
       "            wdsum = 0.0_conv_wp\n"
       "            do k = 1, km\n"
       "              wdsum = wdsum + wet_dep(i,k,n)\n"
       "            enddo\n"
       "            cnv_wetdep(i,n) = cnv_wetdep(i,n)\n"
       "     &                      + real(wdsum, kind=kind_phys) / grav\n"
       "          enddo\n"
       "        enddo\n"
       "      endif\n"
       "!\n")
META = """[cnv_wetdep]
  standard_name = cumulative_convective_wet_deposition_of_chemical_tracers_in_bucket
  long_name = cumulative convective (SAMF) wet deposition of chemical tracers in bucket
  units = kg m-2
  dimensions = (horizontal_loop_extent,number_of_chemical_tracers)
  type = real
  kind = kind_phys
  intent = inout
"""
FSC = """[fscav]
  standard_name = chemical_tracer_scavenging_fractions
  long_name = array of aerosol scavenging coefficients
  units = none
  dimensions = (number_of_chemical_tracers)
  type = real
  kind = kind_phys
  intent = in
"""
DECL_OLD = "      real(kind=kind_phys), dimension(:), intent(in) :: fscav\n"
DECL_NEW = (DECL_OLD + "      real(kind=kind_phys), dimension(:,:), intent(inout) :: cnv_wetdep\n"
            "      real(kind=conv_wp) wdsum\n")

if mode in ("export", "both"):
    rep(SAMF / "samfdeepcnv.f", [
        ("     &    prslp,psp,phil,tkeh,qtr,dqtr,prevsq,q,q1,t1,u1,v1,fscav,      \n",
         "     &    prslp,psp,phil,tkeh,qtr,dqtr,prevsq,q,q1,t1,u1,v1,fscav,      \n"
         "     &    cnv_wetdep,\n"),
        (DECL_OLD, DECL_NEW),
        ("      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n",
         ACC + "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n")])
    rep(SAMF / "samfshalcnv.f", [
        ("     &     prslp,psp,phil,tkeh,qtr,dqtr,prevsq,q,q1,t1,u1,v1,fscav,     &\n",
         "     &     prslp,psp,phil,tkeh,qtr,dqtr,prevsq,q,q1,t1,u1,v1,fscav,     &\n"
         "     &     cnv_wetdep,                                                  &\n"),
        (DECL_OLD, DECL_NEW),
        ("      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n",
         ACC + "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n")])
    for m in ("samfdeepcnv.meta", "samfshalcnv.meta"):
        rep(SAMF / m, [(FSC, FSC + META)])
    T = top / "data/GFS_typedefs.F90"
    rep(T, [
        ("    real (kind=kind_phys), pointer :: cnvprcpb(:,:)  => null()   !< accumulated convective precipitation in bucket (kg/m2)\n",
         "    real (kind=kind_phys), pointer :: cnvprcpb(:,:)  => null()   !< accumulated convective precipitation in bucket (kg/m2)\n"
         "    real (kind=kind_phys), pointer :: cnv_wetdep(:,:) => null()  !< accumulated SAMF wet deposition of chemical tracers in bucket (kg/m2)\n"),
        ("    allocate (Diag%cnvprcpb(IM,ndb))\n",
         "    allocate (Diag%cnvprcpb(IM,ndb))\n"
         "    allocate (Diag%cnv_wetdep(IM,Model%ntchm))\n"),
        ("    Diag%cnvprcpb   = zero\n",
         "    Diag%cnvprcpb   = zero\n"
         "    Diag%cnv_wetdep = zero\n"),
    ])
    rep(top / "data/GFS_typedefs.meta", [(
        "[cnvprcpb]\n"
        "  standard_name = cumulative_lwe_thickness_of_convective_precipitation_amount_in_bucket\n"
        "  long_name = cumulative convective precipitation in bucket\n"
        "  units = m\n"
        "  dimensions = (horizontal_dimension,number_of_diagnostic_buckets)\n"
        "  type = real\n"
        "  kind = kind_phys\n",
        "[cnvprcpb]\n"
        "  standard_name = cumulative_lwe_thickness_of_convective_precipitation_amount_in_bucket\n"
        "  long_name = cumulative convective precipitation in bucket\n"
        "  units = m\n"
        "  dimensions = (horizontal_dimension,number_of_diagnostic_buckets)\n"
        "  type = real\n"
        "  kind = kind_phys\n"
        "[cnv_wetdep]\n"
        "  standard_name = cumulative_convective_wet_deposition_of_chemical_tracers_in_bucket\n"
        "  long_name = cumulative convective (SAMF) wet deposition of chemical tracers in bucket\n"
        "  units = kg m-2\n"
        "  dimensions = (horizontal_dimension,number_of_chemical_tracers)\n"
        "  type = real\n"
        "  kind = kind_phys\n")])
    rep(top / "driver/GFS_diagnostics.F90", [(
        "    idx = idx + 1\n"
        "    ExtDiag(idx)%axes = 2\n"
        "    ExtDiag(idx)%name = 'cnvprcp'\n",
        "    do num = 1, Model%ntchm\n"
        "      idx = idx + 1\n"
        "      ExtDiag(idx)%axes = 2\n"
        "      ExtDiag(idx)%name = 'cnv_wetdep_'//trim(Model%tracer_names(Model%ntchs+num-1))\n"
        "      ExtDiag(idx)%desc = 'bucket SAMF wet deposition of '//trim(Model%tracer_names(Model%ntchs+num-1))\n"
        "      ExtDiag(idx)%unit = 'kg/m**2'\n"
        "      ExtDiag(idx)%mod_name = 'gfs_phys'\n"
        "      ExtDiag(idx)%data%var2 => IntDiag%cnv_wetdep(:,num)\n"
        "    enddo\n"
        "\n"
        "    idx = idx + 1\n"
        "    ExtDiag(idx)%axes = 2\n"
        "    ExtDiag(idx)%name = 'cnvprcp'\n")])
