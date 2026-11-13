#!/usr/bin/env python3
"""apply_d3d45.py <dyn_core.F90> <atmosphere.F90> : variants 4/5 = Jongil's diff3d stencil (GFDL_atmos_cubed_sphere#429
@8460b55b: the original stencil with K_face * delp_face), 4 divided by FV3 delp in the dycore (his code), 5 divided by
the physics' layer mass in the driver (as variant 3). Plus a passive 'D3J' line: his stencil on q = 1."""
import sys
from pathlib import Path
dc, at = Path(sys.argv[1]), Path(sys.argv[2])
t = dc.read_text()
a = ("   if (uc_v >= 1) then\n"
     "      do k = 1, npz\n"
     "         call uc_mwdiv(bd, gridstruct, tx(:,:,k), dku3d_e(:,:,k), uc_dpd(:,:,k), uc_v, deform_3(:,:,k))\n")
assert t.count(a) == 1
b = ("   if (uc_v == 4 .or. uc_v == 5) then\n"
     "      call uc_jh_diag(bd, gridstruct, npz, dku3d_e, uc_dpd)\n"
     "      do k = 1, npz\n"
     "         call uc_jhdiv(bd, gridstruct, tx(:,:,k), dku3d_e(:,:,k), uc_dpd(:,:,k), uc_v == 4, deform_3(:,:,k))\n"
     "         do iq = 1, nq\n"
     "            call uc_jhdiv(bd, gridstruct, q(:,:,k,iq), dku3d_e(:,:,k), uc_dpd(:,:,k), uc_v == 4, deform_4(:,:,k,iq))\n"
     "         enddo\n"
     "      enddo\n"
     "   endif\n"
     "   if (uc_v >= 1 .and. uc_v <= 3) then\n"
     "      do k = 1, npz\n"
     "         call uc_mwdiv(bd, gridstruct, tx(:,:,k), dku3d_e(:,:,k), uc_dpd(:,:,k), uc_v, deform_3(:,:,k))\n")
t = t.replace(a, b)
a2 = "subroutine uc_orig(bd, gridstruct, f, kk, tend)\n"
assert t.count(a2) == 1
sub = '''subroutine uc_jhdiv(bd, gridstruct, f, kk, dp, divide, tend)
! upchk r14: Jongil's diff3d stencil (#429 @8460b55b): original stencil, K_face * dp_face; divide = / dp (his code)
   use fv_arrays_mod, only: fv_grid_type
   type(fv_grid_bounds_type), intent(in) :: bd
   type(fv_grid_type), intent(in) :: gridstruct
   real, intent(in) :: f(bd%isd:bd%ied, bd%jsd:bd%jed), kk(bd%isd:bd%ied, bd%jsd:bd%jed)
   real, intent(in) :: dp(bd%isd:bd%ied, bd%jsd:bd%jed)
   logical, intent(in) :: divide
   real, intent(inout) :: tend(bd%isd:bd%ied, bd%jsd:bd%jed)
   real :: ut(bd%isd:bd%ied, bd%jsd:bd%jed), vt(bd%isd:bd%ied, bd%jsd:bd%jed)
   real :: kx(bd%isd:bd%ied, bd%jsd:bd%jed), ky(bd%isd:bd%ied, bd%jsd:bd%jed), dyy(bd%isd:bd%ied, bd%jsd:bd%jed)
   real :: tmp, tmp1
   integer :: i, j, is, ie, js, je
   is = bd%is; ie = bd%ie; js = bd%js; je = bd%je
   do j = js-1, je+1
      do i = is, ie
         vt(i,j) = f(i,j)*gridstruct%dx(i,j)
      enddo
   enddo
   do j = js-1, je
      do i = is, ie
         tmp = 0.5*(kk(i,j)+kk(i,j+1))
         tmp1 = 0.5*(dp(i,j)+dp(i,j+1))
         ky(i,j) = gridstruct%rarea(i,j)*tmp*tmp1*(vt(i,j+1)-vt(i,j))
      enddo
   enddo
   do j = js-1, je
      do i = is, ie
         vt(i,j) = ky(i,j)*gridstruct%dx(i,j)
      enddo
   enddo
   do j = js, je
      do i = is, ie
         dyy(i,j) = gridstruct%rarea(i,j)*(vt(i,j)-vt(i,j-1))
      enddo
   enddo
   do j = js, je
      do i = is-1, ie+1
         ut(i,j) = f(i,j)*gridstruct%dy(i,j)
      enddo
   enddo
   do j = js, je
      do i = is-1, ie
         tmp = 0.5*(kk(i,j)+kk(i+1,j))
         tmp1 = 0.5*(dp(i,j)+dp(i+1,j))
         kx(i,j) = gridstruct%rarea(i,j)*tmp*tmp1*(ut(i+1,j)-ut(i,j))
      enddo
   enddo
   do j = js, je
      do i = is-1, ie
         ut(i,j) = kx(i,j)*gridstruct%dy(i,j)
      enddo
   enddo
   do j = js, je
      do i = is, ie
         tend(i,j) = gridstruct%rarea(i,j)*(ut(i,j)-ut(i-1,j)) + dyy(i,j)
         if (divide) tend(i,j) = tend(i,j)/dp(i,j)
      enddo
   enddo
end subroutine uc_jhdiv

subroutine uc_jh_diag(bd, gridstruct, npz, kk, dp)
! upchk r14 (passive): 'D3J ncall' + his stencil / dp on q = 1: sum area*|t|, sum area, sum area*dp*t, max |t|
   use fv_arrays_mod, only: fv_grid_type
   use mpp_mod, only: mpp_sum, mpp_max
   type(fv_grid_bounds_type), intent(in) :: bd
   type(fv_grid_type), intent(in) :: gridstruct
   integer, intent(in) :: npz
   real, intent(in) :: kk(bd%isd:bd%ied, bd%jsd:bd%jed, npz), dp(bd%isd:bd%ied, bd%jsd:bd%jed, npz)
   real :: one(bd%isd:bd%ied, bd%jsd:bd%jed), t1(bd%isd:bd%ied, bd%jsd:bd%jed)
   real(kind=8) :: s(3), x
   integer, save :: ncall = 0
   integer :: i, j, k
   one = 1.
   t1 = 0.
   s = 0.d0
   x = 0.d0
   do k = 1, npz
      call uc_jhdiv(bd, gridstruct, one, kk(:,:,k), dp(:,:,k), .true., t1)
      do j = bd%js, bd%je
         do i = bd%is, bd%ie
            s(1) = s(1) + gridstruct%area(i,j)*abs(t1(i,j))
            s(2) = s(2) + gridstruct%area(i,j)
            s(3) = s(3) + gridstruct%area(i,j)*dp(i,j,k)*t1(i,j)
            x = max(x, abs(real(t1(i,j), 8)))
         enddo
      enddo
   enddo
   call mpp_sum(s, 3)
   call mpp_max(x)
   ncall = ncall + 1
   if (is_master()) write(*,'(a,i6,4es25.16)') 'D3J ', ncall, s, x
end subroutine uc_jh_diag

'''
t = t.replace(a2, sub + a2)
dc.write_text(t)
u = at.read_text()
a3 = "         if (Atm(mygrid)%flagstruct%sa3dtke_dyco .and. upchk_d3d_variant() == 3) then\n"
assert u.count(a3) == 1
u = u.replace(a3, "         if (Atm(mygrid)%flagstruct%sa3dtke_dyco .and. (upchk_d3d_variant() == 3 .or. upchk_d3d_variant() == 5)) then\n")
at.write_text(u)
print("APPLY_D3D45_OK")
