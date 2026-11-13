#!/usr/bin/env python3
"""add_def1split.py <ufs-weather-model> : (on a copy of t403d, after add_dspm.py) split deform_1 into
 (i) 2*(dw/dz)^2, (ii) (du/dz)^2+(dv/dz)^2, (iii) the w-u cross terms, exported like deform_1
 (sa3dtke_var%deform_1a/b/c -> Statein%uc_d1w/uc_d1s/uc_d1x -> satmedmfvdifq), and meter in the PBL, with prod's
 interface averaging (k=1: 0.5*dku(1)*x(1); k>=2: 0.5*(dku(k-1)*x(k-1) + dku(k)*x(k))), mass-weighted:
 ucb slots 21 (i), 22 (ii), 23 (iii), 24 shr2 (the PBL's own shear, computed always, used only when sa3dtke is off)."""
import sys
from pathlib import Path

A = Path(sys.argv[1]) / "UFSATM"
F3 = A / "fv3/atmos_cubed_sphere"
P = A / "ccpp/physics/physics"


def edit(p, reps):
    t = p.read_text()
    for a, b in reps:
        assert t.count(a) == 1, (p.name, a[:80])
        t = t.replace(a, b)
    p.write_text(t)


edit(F3 / "model/fv_arrays.F90", [
    ("    real, _ALLOCATABLE :: deform_1(:,:,:)   _NULL !< horizontal deformation\n",
     "    real, _ALLOCATABLE :: deform_1(:,:,:)   _NULL !< horizontal deformation\n"
     "    real, _ALLOCATABLE :: deform_1a(:,:,:)  _NULL !< upchk meter: 2*(dw/dz)**2 part of deform_1\n"
     "    real, _ALLOCATABLE :: deform_1b(:,:,:)  _NULL !< upchk meter: (du/dz)**2+(dv/dz)**2 part\n"
     "    real, _ALLOCATABLE :: deform_1c(:,:,:)  _NULL !< upchk meter: w-u cross-term part\n"),
    ("       allocate (   Atm%sa3dtke_var%deform_1(isd:ied  ,jsd:jed  ,npz) )\n",
     "       allocate (   Atm%sa3dtke_var%deform_1(isd:ied  ,jsd:jed  ,npz) )\n"
     "       allocate (   Atm%sa3dtke_var%deform_1a(isd:ied  ,jsd:jed  ,npz) )\n"
     "       allocate (   Atm%sa3dtke_var%deform_1b(isd:ied  ,jsd:jed  ,npz) )\n"
     "       allocate (   Atm%sa3dtke_var%deform_1c(isd:ied  ,jsd:jed  ,npz) )\n"),
    ("                 Atm%sa3dtke_var%deform_1(i,j,k) = 0.\n",
     "                 Atm%sa3dtke_var%deform_1(i,j,k) = 0.\n"
     "                 Atm%sa3dtke_var%deform_1a(i,j,k) = 0.\n"
     "                 Atm%sa3dtke_var%deform_1b(i,j,k) = 0.\n"
     "                 Atm%sa3dtke_var%deform_1c(i,j,k) = 0.\n"),
    ("       deallocate ( Atm%sa3dtke_var%deform_1 )\n",
     "       deallocate ( Atm%sa3dtke_var%deform_1 )\n"
     "       deallocate ( Atm%sa3dtke_var%deform_1a )\n"
     "       deallocate ( Atm%sa3dtke_var%deform_1b )\n"
     "       deallocate ( Atm%sa3dtke_var%deform_1c )\n")])

edit(F3 / "model/dyn_core.F90", [
    ("  real, allocatable, save :: uc_d2(:,:,:)  ! upchk meter: (u_x+v_y)**2 from diff3d\n",
     "  real, allocatable, save :: uc_d2(:,:,:)  ! upchk meter: (u_x+v_y)**2 from diff3d\n"
     "  real, allocatable, save :: uc_p1(:,:,:), uc_p2(:,:,:), uc_p3(:,:,:)  ! upchk meter: deform_1 parts\n"),
    ("       if (.not. allocated(uc_d2)) allocate(uc_d2(isd:ied, jsd:jed, npz))\n",
     "       if (.not. allocated(uc_d2)) allocate(uc_d2(isd:ied, jsd:jed, npz))\n"
     "       if (.not. allocated(uc_p1)) allocate(uc_p1(isd:ied, jsd:jed, npz), uc_p2(isd:ied, jsd:jed, npz), &\n"
     "                                            uc_p3(isd:ied, jsd:jed, npz))\n"
     "       uc_p1 = 0.\n       uc_p2 = 0.\n       uc_p3 = 0.\n"),
    ("       uc_sdef = 0.d0\n       uc_sdiv = 0.d0\n       do k=1,npz\n",
     "       sa3dtke_var%deform_1a(is:ie,js:je,:) = uc_p1(is:ie,js:je,:)\n"
     "       sa3dtke_var%deform_1b(is:ie,js:je,:) = uc_p2(is:ie,js:je,:)\n"
     "       sa3dtke_var%deform_1c(is:ie,js:je,:) = uc_p3(is:ie,js:je,:)\n"
     "       uc_sdef = 0.d0\n       uc_sdiv = 0.d0\n       do k=1,npz\n"),
    ("!$OMP              dudx,dudy,dudz,dvdx,dvdy,dvdz,dwdx,dwdy,dwdz,uc_d2) &\n",
     "!$OMP              dudx,dudy,dudz,dvdx,dvdy,dvdz,dwdx,dwdy,dwdz,uc_d2,uc_p1,uc_p2,uc_p3) &\n"),
    ("             deform_1(i,j,k)=  2*dwdz(i,j,k)**2+                   &\n"
     "               dudz(i,j,k)**2+dvdz(i,j,k)**2+tmp\n",
     "             deform_1(i,j,k)=  2*dwdz(i,j,k)**2+                   &\n"
     "               dudz(i,j,k)**2+dvdz(i,j,k)**2+tmp\n"
     "             uc_p1(i,j,k) = 2*dwdz(i,j,k)**2\n"
     "             uc_p2(i,j,k) = dudz(i,j,k)**2+dvdz(i,j,k)**2\n"
     "             uc_p3(i,j,k) = tmp\n")])

edit(F3 / "driver/UFS/atmosphere.F90", [
    ("          IPD_Statein%def_1(im,k) = _DBL_(_RL_(Atm(mygrid)%sa3dtke_var%deform_1(i,j,k1)))\n",
     "          IPD_Statein%def_1(im,k) = _DBL_(_RL_(Atm(mygrid)%sa3dtke_var%deform_1(i,j,k1)))\n"
     "          IPD_Statein%uc_d1w(im,k) = _DBL_(_RL_(Atm(mygrid)%sa3dtke_var%deform_1a(i,j,k1)))\n"
     "          IPD_Statein%uc_d1s(im,k) = _DBL_(_RL_(Atm(mygrid)%sa3dtke_var%deform_1b(i,j,k1)))\n"
     "          IPD_Statein%uc_d1x(im,k) = _DBL_(_RL_(Atm(mygrid)%sa3dtke_var%deform_1c(i,j,k1)))\n")])

edit(A / "ccpp/data/GFS_typedefs.F90", [
    ("    real (kind=kind_phys), pointer :: def_1 (:,:)   => null()  !< deformation\n",
     "    real (kind=kind_phys), pointer :: def_1 (:,:)   => null()  !< deformation\n"
     "    real (kind=kind_phys), pointer :: uc_d1w (:,:)  => null()  !< upchk meter: deform_1 parts\n"
     "    real (kind=kind_phys), pointer :: uc_d1s (:,:)  => null()  !< upchk meter\n"
     "    real (kind=kind_phys), pointer :: uc_d1x (:,:)  => null()  !< upchk meter\n"),
    ("    allocate (Statein%def_1   (IM,Model%levs))\n",
     "    allocate (Statein%def_1   (IM,Model%levs))\n"
     "    allocate (Statein%uc_d1w  (IM,Model%levs))\n"
     "    allocate (Statein%uc_d1s  (IM,Model%levs))\n"
     "    allocate (Statein%uc_d1x  (IM,Model%levs))\n"),
    ("    Statein%def_1   = clear_val\n",
     "    Statein%def_1   = clear_val\n    Statein%uc_d1w  = clear_val\n    Statein%uc_d1s  = clear_val\n"
     "    Statein%uc_d1x  = clear_val\n")])


def metablock(name, std, dims, intent=None):
    s = (f"[{name}]\n  standard_name = {std}\n  long_name = upchk meter part of deform_1\n  units = s-2\n"
         f"  dimensions = ({dims},vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n")
    return s + (f"  intent = {intent}\n" if intent else "")


PARTS = [("uc_d1w", "upchk_deform1_w_stretching_part"), ("uc_d1s", "upchk_deform1_horizontal_wind_shear_part"),
         ("uc_d1x", "upchk_deform1_w_u_cross_part")]
edit(A / "ccpp/data/GFS_typedefs.meta", [
    ("[def_2]\n  standard_name = square_of_horizontal_shear_due_to_dynamics\n",
     "".join(metablock(n, s, "horizontal_dimension") for n, s in PARTS) +
     "[def_2]\n  standard_name = square_of_horizontal_shear_due_to_dynamics\n")])
edit(P / "PBL/SATMEDMF/satmedmfvdifq.meta", [
    ("[def_2]\n  standard_name = square_of_horizontal_shear_due_to_dynamics\n",
     "".join(metablock(n, s, "horizontal_loop_extent", "in") for n, s in PARTS) +
     "[def_2]\n  standard_name = square_of_horizontal_shear_due_to_dynamics\n")])

edit(P / "PBL/SATMEDMF/satmedmfvdifq.F", [
    ("     &     def_1,def_2,def_3,def4q,sa3dtke,dku3d_h,dku3d_e,             &\n",
     "     &     def_1,def_2,def_3,def4q,sa3dtke,dku3d_h,dku3d_e,             &\n"
     "     &     uc_d1w,uc_d1s,uc_d1x,                                        &\n"),
    ("     &                     def_1(:,:),  def_2(:,:),                     &\n",
     "     &                     def_1(:,:),  def_2(:,:),                     &\n"
     "     &                     uc_d1w(:,:), uc_d1s(:,:), uc_d1x(:,:),       &\n"),
    ("      use upchk_meter_common, only : uc_pz, uc_pr, uc_ds\n",
     "      use upchk_meter_common, only : uc_pz, uc_pr, uc_ds, uc_pv\n"),
    ("     &        sa3dtke), 0.5*tem2)\n",
     "     &        sa3dtke), 0.5*tem2)\n"
     "            call uc_pv(i, del(i,1)/grav, 0.5*dku(i,1)*uc_d1w(i,1),\n"
     "     &        0.5*dku(i,1)*uc_d1s(i,1), 0.5*dku(i,1)*uc_d1x(i,1),\n"
     "     &        0.5*dku(i,1)*shr2(i,1))\n"),
    ("            tem  = 0.5 * (tem1 + tem2)\n            call uc_pr(i, del(i,k)/grav,\n",
     "            tem  = 0.5 * (tem1 + tem2)\n"
     "            call uc_pv(i, del(i,k)/grav,\n"
     "     &        0.5*(dku(i,k-1)*uc_d1w(i,k-1)+dku(i,k)*uc_d1w(i,k)),\n"
     "     &        0.5*(dku(i,k-1)*uc_d1s(i,k-1)+dku(i,k)*uc_d1s(i,k)),\n"
     "     &        0.5*(dku(i,k-1)*uc_d1x(i,k-1)+dku(i,k)*uc_d1x(i,k)),\n"
     "     &        0.5*(dku(i,k-1)*shr2(i,k-1)+dku(i,k)*shr2(i,k)))\n"
     "            call uc_pr(i, del(i,k)/grav,\n")])

edit(P / "Interstitials/UFS_SCM_NEPTUNE/upchk_meter_common.F90", [
    ("ucnv = 20", "ucnv = 24"),
    ("    ucb(17:20, ucmoff+1:ucmoff+im) = 0.d0\n", "    ucb(17:24, ucmoff+1:ucmoff+im) = 0.d0\n"),
    ("  subroutine uc_ds(", """  subroutine uc_pv(i, m, a, b, c, s)
    integer, intent(in) :: i
    real(kind=kind_phys), intent(in) :: m, a, b, c, s
    ucb(21, ucmoff+i) = ucb(21, ucmoff+i) + m*a
    ucb(22, ucmoff+i) = ucb(22, ucmoff+i) + m*b
    ucb(23, ucmoff+i) = ucb(23, ucmoff+i) + m*c
    ucb(24, ucmoff+i) = ucb(24, ucmoff+i) + m*s
  end subroutine uc_pv

  subroutine uc_ds(""")])
edit(P / "Interstitials/UFS_SCM_NEPTUNE/uc_fin.F90", [
    ("write(*,'(a,i6,20es25.16)') 'UCM '", "write(*,'(a,i6,24es25.16)') 'UCM '")])
print("deform_1 split meters added")
