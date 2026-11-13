!> fv3tally meter: per-term tally of FV3's total energy (MOIST_CAPPA cvm form of compute_total_energy)
!! inside fv_dynamics. Instrumentation only: reads state, writes nothing back. On with env FV3_ETALLY=1.
!! Column TE is snapshotted at each probe; the change since the previous probe is booked to the probe's
!! bucket (state snapshots, never tendency arrays). Sums: Neumaier per PE, PEs combined in PE order.
module fv_etally_mod
  use constants_mod,      only: rdgas, rvgas, grav, cp_air, radius, pi=>pi_8
  use fv_arrays_mod,      only: fv_grid_type, R_GRID
  use mpp_mod,            only: mpp_pe, mpp_npes, mpp_sum, mpp_root_pe, mpp_get_current_pelist
  use tracer_manager_mod, only: get_tracer_index
  use field_manager_mod,  only: MODEL_ATMOS
  implicit none
  private
  public :: et_init, et_state, et_flush, et_dsw, et_dcon_sum, et_dcon_cap, et_tsnap, et_theat

  integer, parameter, public :: MODE_T = 1, MODE_TH = 2, MODE_DT = 3
  ! buckets (state differences, 4 components each: IE, PE, KEh, KEw)
  integer, parameter, public :: ET_RAY = 1, ET_CONV = 2, ET_DYN = 3, ET_DCON = 4, ET_DYN2 = 5, &
                                ET_TRC = 6, ET_REMAP = 7, ET_FIX = 8, ET_L2EX = 9, ET_POST = 10
  integer, parameter :: NB = 10, NC = 4
  ! extras: d_sw terms (5) x 3 level groups, dyn_core heat block (4) x 3 groups, cap count x 3
  integer, parameter, public :: XD_LDIV = 1, XD_LVORT = 2, XD_LW = 3, XD_HW = 4, XD_HUV = 5
  integer, parameter, public :: XH_RAW = 1, XH_SMO = 2, XH_APP = 3, XH_CAP = 4, XH_NCAP = 5
  integer, parameter :: ND = 5, NH = 5, NG = 3
  integer, parameter :: NX = ND*NG + NH*NG
  integer, parameter :: NT = NB*NC + NX

  logical, public :: et_on  = .false.   !< FV3_ETALLY=1
  logical, public :: et_act = .false.   !< on and inside a metered fv_dynamics call
  logical :: initd = .false.
  integer :: is, ie, js, je, km, nstep = 0
  integer :: sphum, liq_wat, rainwat, ice_wat, snowwat, graupel
  real(8) :: zvir, cv_air, cv_vap, area_tot
  real(8), parameter :: c_ice = 1972.d0, c_liq = 4.1855d3
  real(8), allocatable :: snap(:,:,:), tsv(:,:,:), cmv(:,:,:)
  real(8) :: bs(NT), bc(NT)
  real(8), allocatable :: xk(:,:), xkc(:,:)   !< (km, ND) d_sw per level (one thread per k)
  real(8) :: tot(NT), totc(NT)

contains

  subroutine nadd(s, c, x)
    real(8), intent(inout) :: s, c
    real(8), intent(in) :: x
    real(8) :: t
    t = s + x
    if ( abs(s) >= abs(x) ) then
       c = c + ((s - t) + x)
    else
       c = c + ((x - t) + s)
    endif
    s = t
  end subroutine nadd

  integer function grp(k)
    integer, intent(in) :: k
    grp = min(k, 3)
  end function grp

  subroutine et_init(is_, ie_, js_, je_, km_, gridstruct)
    integer, intent(in) :: is_, ie_, js_, je_, km_
    type(fv_grid_type), intent(in) :: gridstruct
    character(len=16) :: ev
    if ( initd ) return
    initd = .true.
    ev = ' '
    call get_environment_variable('FV3_ETALLY', ev)
    et_on = ( trim(ev) == '1' )
    if ( .not. et_on ) return
    is = is_; ie = ie_; js = js_; je = je_; km = km_
    sphum   = get_tracer_index(MODEL_ATMOS, 'sphum')
    liq_wat = get_tracer_index(MODEL_ATMOS, 'liq_wat')
    rainwat = get_tracer_index(MODEL_ATMOS, 'rainwat')
    ice_wat = get_tracer_index(MODEL_ATMOS, 'ice_wat')
    snowwat = get_tracer_index(MODEL_ATMOS, 'snowwat')
    graupel = get_tracer_index(MODEL_ATMOS, 'graupel')
    zvir   = rvgas/rdgas - 1.d0
    cv_air = cp_air - rdgas
    cv_vap = 3.d0*rvgas
    allocate( snap(is:ie,js:je,NC), tsv(is:ie,js:je,km), cmv(is:ie,js:je,km) )
    allocate( xk(km,ND), xkc(km,ND) )
    snap = 0.d0; xk = 0.d0; xkc = 0.d0; bs = 0.d0; bc = 0.d0; tot = 0.d0; totc = 0.d0
    area_tot = 4.d0*pi*radius**2
  end subroutine et_init

  !> T, cvm and qd (q_con) of one cell from the pt representation in use
  subroutine cell_t(mode, ptv, dp, dz, qq, t, cvm)
    integer, intent(in) :: mode
    real(8), intent(in) :: ptv, dp, dz, qq(6)
    real(8), intent(out) :: t, cvm
    real(8) :: qv, ql, qs, qd, kap
    qv = qq(1); ql = qq(2) + qq(3); qs = qq(4) + qq(5) + qq(6)
    qd = ql + qs
    cvm = (1.d0-(qv+qd))*cv_air + qv*cv_vap + ql*c_liq + qs*c_ice
    select case (mode)
    case (MODE_T)
       t = ptv
    case (MODE_DT)
       t = ptv/((1.d0+zvir*qv)*(1.d0-qd))
    case default
       kap = rdgas/(rdgas + cvm/(1.d0+zvir*qv))
       t = ptv*exp(kap/(1.d0-kap)*log(-rdgas/grav*dp/dz*ptv))/((1.d0+zvir*qv)*(1.d0-qd))
    end select
  end subroutine cell_t

  subroutine getq(q, i, j, k, qq)
    real, intent(in) :: q(:,:,:,:)
    integer, intent(in) :: i, j, k
    real(8), intent(out) :: qq(6)
    qq(1) = q(i,j,k,sphum);   qq(2) = q(i,j,k,liq_wat); qq(3) = q(i,j,k,rainwat)
    qq(4) = q(i,j,k,ice_wat); qq(5) = q(i,j,k,snowwat); qq(6) = q(i,j,k,graupel)
  end subroutine getq

  !> Column TE components (J per column) of the current state; book the change since the last probe to
  !! bucket b (b = 0: reset the snapshot only).
  subroutine et_state(b, mode, isd, ied, jsd, jed, u, v, w, delz, pt, delp, q, phis, gridstruct)
    integer, intent(in) :: b, mode, isd, ied, jsd, jed
    real, intent(in) :: u(isd:ied,jsd:jed+1,km), v(isd:ied+1,jsd:jed,km), w(isd:ied,jsd:jed,km)
    real, intent(in) :: delz(is:ie,js:je,km), pt(isd:ied,jsd:jed,km), delp(isd:ied,jsd:jed,km)
    real, intent(in) :: q(isd:,jsd:,:,:), phis(isd:ied,jsd:jed)
    type(fv_grid_type), intent(in) :: gridstruct
    real(8) :: col(NC), phiz(km+1), qq(6), t, cvm, fac, x
    integer :: i, j, k, n
    if ( .not. et_act ) return
    do j=js,je
       do i=is,ie
          phiz(km+1) = phis(i,j)
          do k=km,1,-1
             phiz(k) = phiz(k+1) - grav*delz(i,j,k)
          enddo
          col = 0.d0
          do k=1,km
             call getq(q, i-isd+1, j-jsd+1, k, qq)
             call cell_t(mode, real(pt(i,j,k),8), real(delp(i,j,k),8), real(delz(i,j,k),8), qq, t, cvm)
             col(1) = col(1) + delp(i,j,k)*cvm*t
             col(2) = col(2) + delp(i,j,k)*0.5d0*(phiz(k)+phiz(k+1))
             col(3) = col(3) + delp(i,j,k)*0.25d0*gridstruct%rsin2(i,j)*(u(i,j,k)**2+u(i,j+1,k)**2 +  &
                      v(i,j,k)**2+v(i+1,j,k)**2-(u(i,j,k)+u(i,j+1,k))*(v(i,j,k)+v(i+1,j,k))*gridstruct%cosa_s(i,j))
             col(4) = col(4) + delp(i,j,k)*0.5d0*w(i,j,k)**2
          enddo
          fac = real(gridstruct%area_64(i,j),8)/grav
          do n=1,NC
             x = col(n)*fac
             if ( b > 0 ) call nadd(bs((b-1)*NC+n), bc((b-1)*NC+n), x - snap(i,j,n))
             snap(i,j,n) = x
          enddo
       enddo
    enddo
  end subroutine et_state

  !> d_sw: KE removed by each damping (remove-last, per call), and the d_con estimate pieces, at level k.
  !! u, v are the circulation-form winds at the end of d_sw; du, dv the divergence-damping increments;
  !! ut, vt the vorticity-damping fluxes (applied as u += vt, v -= ut); dw the w damping, wpre w before it.
  subroutine et_dsw(k, isd, ied, jsd, jed, u, v, w, delp, du, dv, ut, vt, dampv, dw, wpre, gridstruct)
    integer, intent(in) :: k, isd, ied, jsd, jed
    real, intent(in) :: u(isd:ied,jsd:jed+1), v(isd:ied+1,jsd:jed), w(isd:ied,jsd:jed), delp(isd:ied,jsd:jed)
    real, intent(in) :: du(is:ie,js:je+1), dv(is:ie+1,js:je)
    real, intent(in) :: ut(isd:ied+1,jsd:jed), vt(isd:ied,jsd:jed+1)
    real, intent(in) :: dampv
    real, intent(in) :: dw(is:ie,js:je), wpre(is:ie,js:je)
    type(fv_grid_type), intent(in) :: gridstruct
    real(8) :: uf(2), vf(2), a(4), b(4), fac, dp, l_tot, l_vort, h_uv, l_w, h_w, wf
    integer :: i, j
    if ( .not. et_act ) return
    do j=js,je
       do i=is,ie
          uf(1) = u(i,j)*gridstruct%rdx(i,j);   uf(2) = u(i,j+1)*gridstruct%rdx(i,j+1)
          vf(1) = v(i,j)*gridstruct%rdy(i,j);   vf(2) = v(i+1,j)*gridstruct%rdy(i+1,j)
          a(1) = du(i,j)*gridstruct%rdx(i,j);   a(2) = du(i,j+1)*gridstruct%rdx(i,j+1)
          a(3) = dv(i,j)*gridstruct%rdy(i,j);   a(4) = dv(i+1,j)*gridstruct%rdy(i+1,j)
          if ( dampv > 1.e-5 ) then
             b(1) = vt(i,j)*gridstruct%rdx(i,j);   b(2) = vt(i,j+1)*gridstruct%rdx(i,j+1)
             b(3) = -ut(i,j)*gridstruct%rdy(i,j);  b(4) = -ut(i+1,j)*gridstruct%rdy(i+1,j)
          else
             b = 0.d0
          endif
          dp = delp(i,j)
          fac = real(gridstruct%area_64(i,j),8)/grav
          l_tot  = dp*(kec(i,j,uf(1)-a(1)-b(1),uf(2)-a(2)-b(2),vf(1)-a(3)-b(3),vf(2)-a(4)-b(4)) &
                     - kec(i,j,uf(1),uf(2),vf(1),vf(2)))
          l_vort = dp*(kec(i,j,uf(1)-b(1),uf(2)-b(2),vf(1)-b(3),vf(2)-b(4)) - kec(i,j,uf(1),uf(2),vf(1),vf(2)))
          h_uv   = dp*(kec(i,j,uf(1)-b(1),uf(2)-b(2),vf(1)-b(3),vf(2)-b(4)) &
                     - kec(i,j,uf(1)+a(1),uf(2)+a(2),vf(1)+a(3),vf(2)+a(4)))
          wf  = w(i,j)
          l_w = dp*(0.5d0*(wf-dw(i,j))**2 - 0.5d0*wf**2)
          h_w = dp*(-dw(i,j)*(wpre(i,j)+0.5d0*dw(i,j)))
          call nadd(xk(k,XD_LDIV),  xkc(k,XD_LDIV),  (l_tot-l_vort)*fac)
          call nadd(xk(k,XD_LVORT), xkc(k,XD_LVORT), l_vort*fac)
          call nadd(xk(k,XD_LW),    xkc(k,XD_LW),    l_w*fac)
          call nadd(xk(k,XD_HW),    xkc(k,XD_HW),    h_w*fac)
          call nadd(xk(k,XD_HUV),   xkc(k,XD_HUV),   h_uv*fac)
       enddo
    enddo
  contains
    real(8) function kec(ii, jj, u1, u2, v1, v2)
      integer, intent(in) :: ii, jj
      real(8), intent(in) :: u1, u2, v1, v2
      kec = 0.25d0*gridstruct%rsin2(ii,jj)*(u1**2+u2**2+v1**2+v2**2-(u1+u2)*(v1+v2)*gridstruct%cosa_s(ii,jj))
    end function kec
  end subroutine et_dsw

  !> dyn_core heat block: book sum(heat_source)*area/g per level group into XH_RAW or XH_SMO
  subroutine et_dcon_sum(ix, isd, ied, jsd, jed, hs, gridstruct)
    integer, intent(in) :: ix, isd, ied, jsd, jed
    real, intent(in) :: hs(isd:ied,jsd:jed,km)
    type(fv_grid_type), intent(in) :: gridstruct
    integer :: i, j, k, n
    if ( .not. et_act ) return
    do k=1,km
       n = NB*NC + ND*NG + (ix-1)*NG + grp(k)
       do j=js,je
          do i=is,ie
             call nadd(bs(n), bc(n), real(hs(i,j,k),8)*real(gridstruct%area_64(i,j),8)/grav)
          enddo
       enddo
    enddo
  end subroutine et_dcon_sum

  !> dyn_core heat block: heat the code's own cap withholds (code metric cv_air*dtmp*delp) and capped cells
  subroutine et_dcon_cap(isd, ied, jsd, jed, hs, delp, bdt, delt_max, gridstruct)
    integer, intent(in) :: isd, ied, jsd, jed
    real, intent(in) :: hs(isd:ied,jsd:jed,km), delp(isd:ied,jsd:jed,km), bdt, delt_max
    type(fv_grid_type), intent(in) :: gridstruct
    real(8) :: delt, dtmp, fac
    integer :: i, j, k, n1, n2
    if ( .not. et_act ) return
    do k=1,km
       delt = abs(bdt*delt_max)
       if ( k == 1 ) delt = 0.1d0*delt
       if ( k == 2 ) delt = 0.5d0*delt
       n1 = NB*NC + ND*NG + (XH_CAP-1)*NG + grp(k)
       n2 = NB*NC + ND*NG + (XH_NCAP-1)*NG + grp(k)
       do j=js,je
          do i=is,ie
             dtmp = hs(i,j,k)/(cv_air*delp(i,j,k))
             if ( abs(dtmp) > delt ) then
                fac = real(gridstruct%area_64(i,j),8)/grav
                call nadd(bs(n1), bc(n1), (dtmp - sign(delt,dtmp))*cv_air*delp(i,j,k)*fac)
                call nadd(bs(n2), bc(n2), 1.d0)
             endif
          enddo
       enddo
    enddo
  end subroutine et_dcon_cap

  !> snapshot T and cvm*delp*area/g of every cell (pt in mode) before the heat block
  subroutine et_tsnap(mode, isd, ied, jsd, jed, delz, pt, delp, q, gridstruct)
    integer, intent(in) :: mode, isd, ied, jsd, jed
    real, intent(in) :: delz(is:ie,js:je,km), pt(isd:ied,jsd:jed,km), delp(isd:ied,jsd:jed,km)
    real, intent(in) :: q(isd:,jsd:,:,:)
    type(fv_grid_type), intent(in) :: gridstruct
    real(8) :: qq(6), t, cvm
    integer :: i, j, k
    if ( .not. et_act ) return
    do k=1,km
       do j=js,je
          do i=is,ie
             call getq(q, i-isd+1, j-jsd+1, k, qq)
             call cell_t(mode, real(pt(i,j,k),8), real(delp(i,j,k),8), real(delz(i,j,k),8), qq, t, cvm)
             tsv(i,j,k) = t
             cmv(i,j,k) = cvm*delp(i,j,k)*real(gridstruct%area_64(i,j),8)/grav
          enddo
       enddo
    enddo
  end subroutine et_tsnap

  !> applied heat per level group: cvm*(T - T_snap)*delp*area/g (delp, q, delz unchanged by the block)
  subroutine et_theat(mode, isd, ied, jsd, jed, delz, pt, delp, q)
    integer, intent(in) :: mode, isd, ied, jsd, jed
    real, intent(in) :: delz(is:ie,js:je,km), pt(isd:ied,jsd:jed,km), delp(isd:ied,jsd:jed,km)
    real, intent(in) :: q(isd:,jsd:,:,:)
    real(8) :: qq(6), t, cvm
    integer :: i, j, k, n
    if ( .not. et_act ) return
    do k=1,km
       n = NB*NC + ND*NG + (XH_APP-1)*NG + grp(k)
       do j=js,je
          do i=is,ie
             call getq(q, i-isd+1, j-jsd+1, k, qq)
             call cell_t(mode, real(pt(i,j,k),8), real(delp(i,j,k),8), real(delz(i,j,k),8), qq, t, cvm)
             call nadd(bs(n), bc(n), cmv(i,j,k)*(t - tsv(i,j,k)))
          enddo
       enddo
    enddo
  end subroutine et_theat

  !> end of fv_dynamics: combine PEs in PE order (exact gather via a zero-padded mpp_sum), print J/m2
  subroutine et_flush()
    real(8), allocatable :: buf(:)
    integer, allocatable :: pelist(:)
    real(8) :: s(NT), c(NT), v(NT)
    integer :: np, me, p, n, k, g
    character(len=32) :: fmt
    if ( .not. et_act ) return
    ! d_sw per-level accumulators into level groups (k order)
    do n=1,ND
       do k=1,km
          g = NB*NC + (n-1)*NG + grp(k)
          call nadd(bs(g), bc(g), xk(k,n))
          call nadd(bs(g), bc(g), xkc(k,n))
       enddo
    enddo
    xk = 0.d0; xkc = 0.d0
    np = mpp_npes()
    allocate( pelist(np), buf(NT*2*np) )
    call mpp_get_current_pelist(pelist)
    me = 0
    do p=1,np
       if ( pelist(p) == mpp_pe() ) me = p
    enddo
    buf = 0.d0
    buf((me-1)*2*NT+1:(me-1)*2*NT+NT) = bs
    buf((me-1)*2*NT+NT+1:me*2*NT)     = bc
    call mpp_sum(buf, NT*2*np)
    s = 0.d0; c = 0.d0
    do p=1,np
       do n=1,NT
          call nadd(s(n), c(n), buf((p-1)*2*NT+n))
          call nadd(s(n), c(n), buf((p-1)*2*NT+NT+n))
       enddo
    enddo
    v = (s + c)/area_tot
    v(NT-NG+1:NT) = s(NT-NG+1:NT) + c(NT-NG+1:NT)     ! capped-cell counts, not per m2
    nstep = nstep + 1
    if ( mpp_pe() == mpp_root_pe() ) then
       write(fmt,'(a,i0,a)') '(a,i5,', NT, 'es24.15)'
       write(6,fmt) 'ETL', nstep, v
       do n=1,NT
          call nadd(tot(n), totc(n), v(n))
       enddo
       write(6,fmt) 'ETS', nstep, tot + totc
    endif
    bs = 0.d0; bc = 0.d0
    deallocate( pelist, buf )
  end subroutine et_flush

end module fv_etally_mod
