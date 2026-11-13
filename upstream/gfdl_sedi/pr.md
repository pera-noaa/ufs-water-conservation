**Title:** gfdl_mp: rain and cloud water fall with the liquid heat capacity

**Base:** NOAA-GFDL/GFDL_atmos_cubed_sphere `main` (8b94b9f3) ← pera-noaa/GFDL_atmos_cubed_sphere `sedi-heat-liquid`

---

**Description**

`terminal_fall` passed `c_ice` to `sedi_heat` for every species; this passes `c_liq` for rain and cloud water. One commit.

Fixes #TBD-GFDL_SEDI_ISSUE

**How Has This Been Tested?**

Standalone, `gfdl_mp.F90` from `main` built with gfortran 16.2 (FMS's `check_nml_error` stubbed; `terminal_fall` made public in a test copy only). Rain or cloud water falls through a 40-layer column for one 300 s step; the check is the column's internal energy plus the potential energy of the water, plus what leaves at the bottom:

| | `main` | this PR |
|---|---|---|
| falling rain or cloud water | 6 × 10⁻⁵ of the column energy | 2 × 10⁻¹⁶ (single precision: 2 × 10⁻⁸, rounding) |
| falling snow (`c_ice`, unchanged) | 0 | 0 |

`-Wall` warnings in `gfdl_mp.F90` are the same before and after (17 in double precision).

In UFS, the same change in its copy (ccpp-physics `gfdl_cloud_microphys_v3_mod.F90`), C96 `control_iovr4_gfdlmpv3`, 24 h, Intel oneAPI 2024.2.1 on Hercules: the microphysics energy residual (GFDL MP's constants, with the potential energy of the water) goes from +0.20 to −0.007 W/m²; temperature −0.003 K, other fields at noise. Full UFS regression test: ufs-community/ccpp-physics#TBD-PR_GMP. Not run in SHiELD.

<details><summary>Test program</summary>

```fortran
! Drops rain or cloud water through a column with terminal_fall; checks internal + water potential energy + outflow
program test_sedi
  use gfdl_mp_mod
  implicit none
  integer, parameter :: ke = 40, r8 = selected_real_kind(15)
  real, parameter :: g = 9.80665
  character(len=80) :: nml(4)
  real, dimension(ke) :: qv, ql, qr, qi, qs, qg, u, v, w, dz, dp, vt, m1, z
  real(kind=r8), dimension(ke) :: tz
  real(kind=r8) :: dte, e0, e1, eout
  real :: x1
  real, dimension(ke) :: q0
  real(kind=r8), dimension(ke) :: t0
  integer :: k, n, nfail
  character(len=2) :: fl(3) = ['qr', 'ql', 'qs']
  nml = [character(len=80) :: '&gfdl_mp_nml', ' do_sedi_w = .false.', ' do_sedi_uv = .false.', '/']
  call gfdl_mp_init(nml, 6, .false.)
  nfail = 0
  do n = 1, 3
    call column()
    if (fl(n) == 'ql') then
      ql = qr; qr = 0.
    endif
    if (fl(n) == 'qs') then
      qs = qr; qr = 0.; vt = 1.
    endif
    e0 = energy(); q0 = qr + ql + qs; t0 = tz
    x1 = 0.; dte = 0.
    call terminal_fall(300., 1, ke, tz, qv, ql, qr, qi, qs, qg, dz, dp, vt, x1, m1, u, v, w, dte, fl(n))
    e1 = energy()
    print '(a,es10.2,a,es10.2,a)', '  moved: max |dq| ', maxval(abs(qr + ql + qs - q0)), ', max |dT| ', maxval(abs(tz - t0)), ' K'
    eout = m1(ke)*(merge(c_ice, c_liq, fl(n) == 'qs')*tz(ke) + g*z(ke))
    print '(a,a2,a,es12.4,a,es12.4,a,es11.3)', 'falling ', fl(n), ': out of the column', m1(ke)/g, ' kg/m2; energy residual ', &
          (e1 + eout - e0)/g, ' J/m2, relative ', (e1 + eout - e0)/abs(e0)
    if (abs(e1 + eout - e0) > 1.e-9*abs(e0)) nfail = nfail + 1
  enddo
  if (nfail > 0) then
    print '(a,i0,a)', 'FAIL: ', nfail, ' case(s)'
  else
    print '(a)', 'PASS'
  endif
contains
  subroutine column()
    do k = 1, ke
      dp(k) = 2500.
      dz(k) = -(250. + 10.*k)
      tz(k) = 220. + 2.*k
      qv(k) = 1.e-3*k/ke
      qr(k) = merge(2.e-3, 0., k > 10 .and. k < 25)
      ql(k) = 0.; qi(k) = 0.; qs(k) = 0.; qg(k) = 0.
      u(k) = 0.; v(k) = 0.; w(k) = 0.
      vt(k) = 6.
    enddo
    z(ke) = -0.5*dz(ke)
    do k = ke - 1, 1, -1
      z(k) = z(k + 1) - 0.5*(dz(k + 1) + dz(k))
    enddo
  end subroutine column
  real(kind=r8) function energy()
    energy = sum(dp*((cv_air + qv*cv_vap + (ql + qr)*c_liq + (qi + qs + qg)*c_ice)*tz + (ql + qr + qi + qs + qg)*g*z))
  end function energy
end program test_sedi
```
</details>

**Checklist:**

- [x] My code follows the style guidelines of this project
- [x] I have performed a self-review of my own code
- [x] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [x] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published in downstream modules

AI-assisted: Claude Opus 5.5; reviewed by author (trailer on the commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
