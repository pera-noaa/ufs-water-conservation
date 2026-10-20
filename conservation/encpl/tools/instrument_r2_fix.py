#!/usr/bin/env python3
"""Round 2, on a tree with C1 (instrument_cpl_fix.py) and K1 (instrument_thompson_kirchhoff.py).
Usage: instrument_r2_fix.py <ufs-weather-model>
P1  precipitation mass through each layer bottom, per physics step, kg m-2, exported to Stateout:
    pflx_dc / pflx_sc (SAMF deep / shallow rain after evaporation, as the scheme applies it: rn after level k),
    pflx_mpl / pflx_mpi (Thompson liquid r+c / ice i+s+g, from the layer mass change of the sedimentation step).
C1v2 sensible bit (4) uses them: precipitation is brought to the receiving layer's T with c_liq / c_ice, the
    residual net flux (vapour, mostly) with cp_vap, each by its own direction. PE bit unchanged (linear in flux).
S1  option gfs_physics_nml samf_kirchhoff (default .false.): SAMF heats condensate formed in layer k
    (net rain production from its flux profile + detrained cloud condensate) with L_v(T) instead of hvap,
    i.e. adds (cvap - cliq)*(T - t0c)*C/cp. Ice partition/hfus of detrained ice is D3a, not touched.
Anchors must match the stated count."""
import sys
from pathlib import Path

base = Path(sys.argv[1]) / "UFSATM"
td = base / "ccpp/data/GFS_typedefs.F90"
tmeta = base / "ccpp/data/GFS_typedefs.meta"
P = base / "ccpp/physics/physics"
dc, dcm = P / "CONV/SAMF/samfdeepcnv.f", P / "CONV/SAMF/samfdeepcnv.meta"
sc, scm = P / "CONV/SAMF/samfshalcnv.f", P / "CONV/SAMF/samfshalcnv.meta"
mod = P / "MP/Thompson/module_mp_thompson.F90"
drv, dmeta = P / "MP/Thompson/mp_thompson.F90", P / "MP/Thompson/mp_thompson.meta"
atm = base / "fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


def meta(name, sn, ln, dims, intent=None, units="kg m-2", typ="real", kind=True):
    s = f"[{name}]\n  standard_name = {sn}\n  long_name = {ln}\n  units = {units}\n  dimensions = {dims}\n  type = {typ}\n"
    if kind:
        s += "  kind = kind_phys\n"
    if intent:
        s += f"  intent = {intent}\n"
    return s


FL = {"pflx_dc": ("precipitation_mass_through_layer_bottom_from_deep_convection", "deep convective rain through layer bottom per physics step"),
      "pflx_sc": ("precipitation_mass_through_layer_bottom_from_shallow_convection", "shallow convective rain through layer bottom per physics step"),
      "pflx_mpl": ("liquid_precipitation_mass_through_layer_bottom_from_microphysics", "microphysics liquid precipitation through layer bottom per physics step"),
      "pflx_mpi": ("frozen_precipitation_mass_through_layer_bottom_from_microphysics", "microphysics frozen precipitation through layer bottom per physics step")}
KS = ("flag_for_samf_kirchhoff_latent_heat", "flag for SAMF latent heat of condensation L_v(T) of the host energy frame")

# ---- GFS_typedefs: Stateout arrays, namelist flag
sub(td, "    real (kind=kind_phys), pointer :: ten_v_conv(:,:)  => null()  !< Meridional-wind tendency ...\n",
    "    real (kind=kind_phys), pointer :: ten_v_conv(:,:)  => null()  !< Meridional-wind tendency ...\n"
    "    !-- precipitation mass through the bottom of physics layer k in the physics step (kg m-2), for the coupling\n"
    + "".join(f"    real (kind=kind_phys), pointer :: {n}(:,:) => null()\n" for n in FL))
sub(td, "    Stateout%ten_v_conv = clear_val\n",
    "    Stateout%ten_v_conv = clear_val\n"
    + "".join(f"    allocate (Stateout%{n} (IM,Model%levs+1))\n    Stateout%{n} = clear_val\n" for n in FL))
sub(tmeta, "[ten_v_conv]\n  standard_name = tendency_of_y_wind_due_to_convection\n  long_name = tendency of y wind calculated by one physics scheme\n"
    "  units = m s-2\n  dimensions = (horizontal_dimension,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n",
    "[ten_v_conv]\n  standard_name = tendency_of_y_wind_due_to_convection\n  long_name = tendency of y wind calculated by one physics scheme\n"
    "  units = m s-2\n  dimensions = (horizontal_dimension,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n"
    + "".join(meta(n, a, b, "(horizontal_dimension,vertical_interface_dimension)") for n, (a, b) in FL.items()))
sub(td, "    logical              :: thompson_kirchhoff !< Thompson latent heats/heat capacity of the host energy frame\n",
    "    logical              :: thompson_kirchhoff !< Thompson latent heats/heat capacity of the host energy frame\n"
    "    logical              :: samf_kirchhoff  !< SAMF latent heat of condensation L_v(T) of the host energy frame\n")
sub(td, "    logical              :: thompson_kirchhoff = .false.        !< Thompson latent heats/heat capacity of the host energy frame\n",
    "    logical              :: thompson_kirchhoff = .false.        !< Thompson latent heats/heat capacity of the host energy frame\n"
    "    logical              :: samf_kirchhoff = .false.            !< SAMF latent heat of condensation L_v(T) of the host energy frame\n")
sub(td, "sedi_semi, decfl, thompson_kirchhoff,     ", "sedi_semi, decfl, thompson_kirchhoff, samf_kirchhoff,")
sub(td, "    Model%thompson_kirchhoff = thompson_kirchhoff\n",
    "    Model%thompson_kirchhoff = thompson_kirchhoff\n    Model%samf_kirchhoff = samf_kirchhoff\n")
sub(tmeta, "[thompson_kirchhoff]\n",
    meta("samf_kirchhoff", *KS, "()", units="flag", typ="logical", kind=False) + "[thompson_kirchhoff]\n")

# ---- SAMF deep and shallow (fixed form, columns <= 72)
for f, fm, last, rname, cond, km1, evtail in (
        (dc, dcm, "[cat_adj_deep]\n  standard_name = adjustment_for_convective_advection_time_for_deep\n"
                  "  long_name = adjustment for convective advection time for deep\n  units = none\n  dimensions = ()\n"
                  "  type = real\n  kind = kind_phys\n  intent = in\n", "pflx_dc",
         "          if (cnvflg(i) .and. rn(i) > 0.0_kind_phys) then\n", "km",
         "              delqbar(i) = delqbar(i) + delq(i) * tem1\n              deltbar(i) = deltbar(i) + deltv(i) * tem1\n"
         "            endif\n          endif\n"),
        (sc, scm, "[cat_adj_shal]\n  standard_name = adjustment_for_convective_advection_time_for_shallow\n"
                  "  long_name = adjustment for convective advection time for shallow\n  units = none\n  dimensions = ()\n"
                  "  type = real\n  kind = kind_phys\n  intent = in\n", "pflx_sc",
         "          if (cnvflg(i)) then\n", "km1",
         "              delqbar(i) = delqbar(i) + delq(i)  * factor\n              deltbar(i) = deltbar(i) + deltv(i) * factor\n"
         "            endif\n          endif\n")):
    sub(fm, last, last + meta("pflx", *FL[rname], "(horizontal_loop_extent,vertical_interface_dimension)", "inout")
        + meta("samf_kirchhoff", *KS, "()", "in", units="flag", typ="logical", kind=False))
    if f == dc:
        sub(f, "     &    errmsg,errflg)\n", "     &    pflx,samf_kirchhoff,errmsg,errflg)\n")
        sub(f, "      real(kind=kind_phys), intent(out) :: ud_mf(:,:)\n",
            "      real(kind=kind_phys), intent(out) :: ud_mf(:,:)\n"
            "      real(kind=kind_phys), intent(inout) :: pflx(:,:)\n"
            "      logical, intent(in) :: samf_kirchhoff\n"
            "      real(kind=kind_phys) :: pfk(im,km+1), ck\n")
    else:
        l1 = "     &     lbb1,lbb2,lbb3,dt_decay,cat_adj_shal,pflx,"
        sub(f, "     &     lbb1,lbb2,lbb3,dt_decay,cat_adj_shal,errmsg,errflg)",
            l1.ljust(72) + "&\n     &     samf_kirchhoff,errmsg,errflg)")
        sub(f, "      real(kind=kind_phys), intent(out) :: ud_mf(:,:)\n",
            "      real(kind=kind_phys), intent(out) :: ud_mf(:,:)\n"
            "      real(kind=kind_phys), intent(inout) :: pflx(:,:)\n"
            "      logical, intent(in) :: samf_kirchhoff\n"
            "      real(kind=kind_phys) :: pfk(im,km+1), ck\n")
    sub(f, "      errmsg = ''\n      errflg = 0\n",
        "      errmsg = ''\n      errflg = 0\n      pflx = 0.0_kind_phys\n      pfk = 0.0_kind_phys\n")
    # rain through the bottom of layer k as the evaporation loop leaves it (m)
    sub(f, evtail + "        enddo\n      enddo\n",
        evtail + "          pfk(i,k) = max(rn(i), 0.0_kind_phys)\n        enddo\n      enddo\n")
    sub(f, "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,",
        f"""!  rain mass through layer bottoms (kg m-2); option: condensate formed
!  in layer k (net rain production + detrained cloud) at L_v(T), not hvap
      do k = 1, km
        do i = 1, im
{cond}            pflx(i,k) = 1000.0_kind_phys * pfk(i,k)
            if (samf_kirchhoff .and. k <= {km1}) then
              ck = 1000.0_kind_phys * (pfk(i,k) - pfk(i,k+1))
     &           * grav / delp(i,k)
              if (ncloud > 0 .and. k >= kbcon(i) .and. k <= ktcon(i))
     &          ck = ck + real(dellal(i,k) * xmb(i) * dt2, kind_phys)
              new_t1(i,k) = new_t1(i,k) + real((cvap - cliq)
     &           * (t1(i,k) - t0c) * ck / cp, kind=conv_wp)
            endif
          endif
        enddo
      enddo
      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,""")

# ---- Thompson: layer-bottom fluxes of the sedimentation step, per column, to the wrapper
sub(mod, "   logical                      :: thompson_kirchhoff = .false.\n",
    "   logical                      :: thompson_kirchhoff = .false.\n"
    "   real(wp), public, save :: tsf(2, 200, 4096) = 0.   ! sedimented mass through layer bottoms (kg m-2): liquid, ice\n")
sub(mod, "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
    "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n"
    "      real(wp) :: msl0(kts:kte), msi0(kts:kte), fsl, fsi\n")
sub(mod, "      dtsave = dt\n      odt = 1./dt\n", "      tsf(:,:,ii) = 0.\n      dtsave = dt\n      odt = 1./dt\n")
ML = "(qr1d(k) + qrten(k)*DT + qc1d(k) + qcten(k)*DT)*rho(k)*dzq(k)"
MI = "(qi1d(k) + qiten(k)*DT + qs1d(k) + qsten(k)*DT + qg1d(k) + qgten(k)*DT)*rho(k)*dzq(k)"
sub(mod, "      if (ANY(L_qr .eqv. .true.)) then\n         nstep = nint(1./onstep(1))\n",
    f"      do k = kts, kte\n         msl0(k) = {ML}\n         msi0(k) = {MI}\n      enddo\n"
    "      if (ANY(L_qr .eqv. .true.)) then\n         nstep = nint(1./onstep(1))\n")
sub(mod, "!> - Instantly melt any cloud ice into cloud water if above 0C and\n",
    f"      ! mass through the bottom of layer k = sedimentation loss of the layers above and of k\n"
    f"      fsl = 0.\n      fsi = 0.\n      do k = kte, kts, -1\n         fsl = fsl + msl0(k) - {ML}\n"
    f"         fsi = fsi + msi0(k) - {MI}\n         tsf(1,k,ii) = fsl\n         tsf(2,k,ii) = fsi\n      enddo\n"
    "!> - Instantly melt any cloud ice into cloud water if above 0C and\n")
sub(drv, "      use module_mp_thompson, only : thompson_init, mp_gt_driver, thompson_final, calc_effectRad\n",
    "      use module_mp_thompson, only : thompson_init, mp_gt_driver, thompson_final, calc_effectRad, tsf\n")
sub(drv, "                              dnifa, dtgrs, ten_u, ten_v, errmsg, errflg)\n",
    "                              dnifa, dtgrs, ten_u, ten_v, pflx_mpl, pflx_mpi, errmsg, errflg)\n")
sub(drv, "         real(kind=kind_phys), intent(inout), dimension(:,:), optional :: pfl_lsan\n",
    "         real(kind=kind_phys), intent(inout), dimension(:,:), optional :: pfl_lsan\n"
    "         real(kind=kind_phys), intent(inout) :: pflx_mpl(:,:), pflx_mpi(:,:)\n")
sub(drv, "         !> - Call mp_gt_driver() with or without aerosols, with or without effective radii, ...\n",
    "         if (istep == 1) then\n            pflx_mpl = 0.\n            pflx_mpi = 0.\n         endif\n"
    "         tsf(:,:,1:ncol) = 0.\n"
    "         !> - Call mp_gt_driver() with or without aerosols, with or without effective radii, ...\n")
sub(drv, "         if (errflg/=0) return\n\n         ! DH* - do this only if istep == nsteps?",
    "         if (errflg/=0) return\n         pflx_mpl(:,1:nlev) = pflx_mpl(:,1:nlev) + transpose(tsf(1,1:nlev,1:ncol))\n"
    "         pflx_mpi(:,1:nlev) = pflx_mpi(:,1:nlev) + transpose(tsf(2,1:nlev,1:ncol))\n"
    "\n         ! DH* - do this only if istep == nsteps?")
sub(dmeta, "[ten_v]\n  standard_name = tendency_of_y_wind\n  long_name = tendency of y wind calculated by one physics scheme\n"
    "  units = m s-2\n  dimensions = (horizontal_loop_extent,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n  intent = out\n",
    "[ten_v]\n  standard_name = tendency_of_y_wind\n  long_name = tendency of y wind calculated by one physics scheme\n"
    "  units = m s-2\n  dimensions = (horizontal_loop_extent,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n  intent = out\n"
    + meta("pflx_mpl", *FL["pflx_mpl"], "(horizontal_loop_extent,vertical_interface_dimension)", "inout")
    + meta("pflx_mpi", *FL["pflx_mpi"], "(horizontal_loop_extent,vertical_interface_dimension)", "inout"))

# ---- C1 v2: sensible bit from the precipitation fluxes + residual
sub(atm, "   real(kind=kind_phys) :: qpe(npz), qfw(npz), qse(npz), qp, cb, e\n",
    "   real(kind=kind_phys) :: qpe(npz), qfw(npz), qse(npz), qp, cb, e\n"
    "   real(kind=kind_phys) :: fpl(npz+1), fpi(npz+1), fr\n")
sub(atm, """      do k1 = 1, npz-1
         if (ftop(k1+1) >= 0.) then
            cb = c_liq
            if (tk(k1) < t_frz) cb = c_ice
            qse(k1+1) = qse(k1+1) - ftop(k1+1)*cb*(tk(k1+1) - tk(k1))
         else
            qse(k1) = qse(k1) - ftop(k1+1)*cp_vapor*(tk(k1+1) - tk(k1))
         endif
      enddo
""", """      ! precipitation through the bottom of dycore layer k1 (Pa); residual net flux (vapour) by its direction
      do k1 = 1, npz
         k = k1
         if (flip_vc) k = npz+1-k1
         fpl(k1+1) = grav*(IPD_Stateout%pflx_dc(im,k) + IPD_Stateout%pflx_sc(im,k) + IPD_Stateout%pflx_mpl(im,k))
         fpi(k1+1) = grav*IPD_Stateout%pflx_mpi(im,k)
      enddo
      do k1 = 1, npz-1
         qse(k1+1) = qse(k1+1) - (fpl(k1+1)*c_liq + fpi(k1+1)*c_ice)*(tk(k1+1) - tk(k1))
         fr = ftop(k1+1) - fpl(k1+1) - fpi(k1+1)
         if (fr >= 0.) then
            qse(k1+1) = qse(k1+1) - fr*cp_vapor*(tk(k1+1) - tk(k1))
         else
            qse(k1) = qse(k1) - fr*cp_vapor*(tk(k1+1) - tk(k1))
         endif
      enddo
""")
for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
