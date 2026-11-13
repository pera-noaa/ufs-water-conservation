#!/usr/bin/env python3
"""Per-scheme column-water meter (WBGC*): snapshot W(gq0), W(qgrs) after every physics scheme, print flagged columns."""
# Usage: instrument_wb_gc.py src <ufs_model.fd>        (after instrument_wb_ep.py; edits GFS_physics_post.F90)
#        instrument_wb_gc.py cap <physics_cap.F90>     (generated cap in the build tree; re-run after any cmake reconfigure)
# Diagnostic only: reads state, writes module arrays and stdout. A column is printed at GFS_physics_post when its WBQ
# residual |R| > 1e-8 kg/m2 or its slmsk/fice changed since the previous step:
#   WBGC  kdt j R E_add H P | WBGCA kdt j attrs(now) | WBGCP kdt j attrs(prev step) | WBGCS kdt j stage dW(gq0) dW(qgrs)
import re
import sys
from pathlib import Path

NC, NS, NA = 8192, 80, 32
mode, target = sys.argv[1], Path(sys.argv[2])


def sub(s, old, new, name):
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    return s.replace(old, new)


WSUM = ("(%(a)s(i,k,ntqv)+%(a)s(i,k,ntcw)+%(a)s(i,k,ntiw)+%(a)s(i,k,ntrw)+%(a)s(i,k,ntsw)"
        "+%(a)s(i,k,ntgl))*(prsi(i,k)-prsi(i,k+1))")

if mode == "src":
    post = target / "FV3/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90"
    s = post.read_text()
    s = sub(s, "  integer, save :: wbq_r = 0\n",
            "  integer, save :: wbq_r = 0\n"
            f"  character(len=40), save :: wbgc_nm({NS}) = ''\n"
            "  integer, save :: wbgc_n = 0\n"
            f"  real(kind=8), save :: wbgc_d(2,{NS},{NC}) = 0.0d0\n"
            f"  real(kind=8), save :: wbgc_w(2,{NC}) = 0.0d0\n"
            f"  real(kind=8), save :: wbgc_a({NA},{NC}) = 0.0d0, wbgc_p({NA},{NC}) = 0.0d0\n"
            "  public wbgc_snap, wbgc_val, wbgc_lval\n", post.name)
    s = sub(s, "    integer :: j\n", "    integer :: j, s\n    real(kind=8) :: wo, wi\n    logical :: wbgc_chg\n",
            post.name)
    s = sub(s, "       wbq_c(:,j) = 0.0d0\n       if (allocated(wbq_h)) wbq_h(j,:) = 0.0d0\n",
            "       wo = 0.0d0\n       wi = 0.0d0\n       do k = 1, nLev\n"
            "          wo = wo + " + WSUM % {"a": "gq0"} + "\n"
            "          wi = wi + " + WSUM % {"a": "qgrs"} + "\n"
            "       enddo\n"
            "       wo = wo/con_g\n       wi = wi/con_g\n"
            "       wbgc_chg = kdt > 1 .and. (wbgc_a(3,j) /= wbgc_p(3,j) .or. wbgc_a(4,j) /= wbgc_p(4,j))\n"
            "       if (abs(wb_r) > 1.0d-8 .or. wbgc_chg) then\n"
            "          write(*,'(a,2i7,4es24.15)') 'WBGC  ', kdt, j, wb_r, wbq_c(1,j), wb_h, wbq_c(3,j)\n"
            f"          write(*,'(a,2i7,{NA}es16.8)') 'WBGCA ', kdt, j, wbgc_a(:,j)\n"
            f"          write(*,'(a,2i7,{NA}es16.8)') 'WBGCP ', kdt, j, wbgc_p(:,j)\n"
            "          if (abs(wb_r) > 1.0d-8) then\n"
            "             do s = 1, wbgc_n\n"
            "                if (abs(wbgc_d(1,s,j)) > 1.0d-13 .or. abs(wbgc_d(2,s,j)) > 1.0d-13) &\n"
            "                   write(*,'(a,2i7,1x,a40,2es24.15)') 'WBGCS ', kdt, j, wbgc_nm(s), wbgc_d(:,s,j)\n"
            "             enddo\n"
            "             write(*,'(a,2i7,1x,a40,2es24.15)') 'WBGCS ', kdt, j, 'stochastics_to_post', &\n"
            "                wo - wbgc_w(1,j), wi - wbgc_w(2,j)\n"
            "          endif\n"
            "       endif\n"
            "       wbq_c(:,j) = 0.0d0\n       if (allocated(wbq_h)) wbq_h(j,:) = 0.0d0\n", post.name)
    snap = f"""
  subroutine wbgc_snap(nm, blk, blk1, im, levs, gq0, qgrs, prsi, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g)
    character(len=*), intent(in) :: nm
    integer, intent(in) :: blk, blk1, im, levs, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl
    real(kind=kind_phys), intent(in) :: gq0(:,:,:), qgrs(:,:,:), prsi(:,:), con_g
    integer :: s, i, j, k
    real(kind=8) :: wo, wi
    s = 0
    do k = 1, wbgc_n
       if (wbgc_nm(k) == nm) s = k
    enddo
    if (s == 0 .and. wbgc_n < {NS}) then
       wbgc_n = wbgc_n + 1
       s = wbgc_n
       wbgc_nm(s) = nm
    endif
    if (s == 0) return
    do i = 1, im
       j = (blk-1)*blk1 + i
       wo = 0.0d0
       wi = 0.0d0
       do k = 1, levs
          wo = wo + {WSUM % {"a": "gq0"}}
          wi = wi + {WSUM % {"a": "qgrs"}}
       enddo
       wo = wo/con_g
       wi = wi/con_g
       if (nm == 'GFS_suite_stateout_reset') then
          wbgc_d(:,:,j) = 0.0d0
       else
          wbgc_d(1,s,j) = wbgc_d(1,s,j) + (wo - wbgc_w(1,j))
          wbgc_d(2,s,j) = wbgc_d(2,s,j) + (wi - wbgc_w(2,j))
       endif
       wbgc_w(1,j) = wo
       wbgc_w(2,j) = wi
    enddo
  end subroutine wbgc_snap

  subroutine wbgc_val(blk, blk1, im, slot, x)
    integer, intent(in) :: blk, blk1, im, slot
    real(kind=kind_phys), intent(in) :: x(:)
    integer :: i, j
    do i = 1, im
       j = (blk-1)*blk1 + i
       if (slot == 1) wbgc_p(:,j) = wbgc_a(:,j)
       wbgc_a(slot,j) = x(i)
    enddo
  end subroutine wbgc_val

  subroutine wbgc_lval(blk, blk1, im, slot, x)
    integer, intent(in) :: blk, blk1, im, slot
    logical, intent(in) :: x(:)
    integer :: i, j
    do i = 1, im
       j = (blk-1)*blk1 + i
       wbgc_a(slot,j) = merge(1.0d0, 0.0d0, x(i))
    enddo
  end subroutine wbgc_lval
"""
    s = sub(s, "contains\n\n! ####", "contains\n" + snap + "\n! ####", post.name)
    post.with_suffix(post.suffix + ".preWBGC").write_text(post.read_text())
    post.write_text(s)
    print(f"instrumented {post}")

elif mode == "cap":
    s = target.read_text()
    if "wbgc_snap" in s:
        sys.exit(f"ABORT {target.name}: already instrumented")
    s = re.sub(r"(module ccpp_\w+_physics_cap\n)", r"\1\n   use GFS_physics_post, only: wbgc_snap, wbgc_val, wbgc_lval\n", s, count=1)
    D, I, C = "GFS_Data(cdata%blk_no)", "GFS_Interstitial(cdata%thrd_no)", "GFS_Control"
    head = f"cdata%blk_no,{C}%blksz(1),{C}%blksz(cdata%blk_no)"

    def snap(nm):
        return (f"      call wbgc_snap('{nm}',{head},{C}%levs, &\n"
                f"                  {D}%Stateout%gq0,{D}%Statein%qgrs,{D}%Statein%prsi, &\n"
                f"                  {C}%ntqv,{C}%ntcw,{C}%ntiw,{C}%ntrw,{C}%ntsw,{C}%ntgl,con_g)\n")

    def val(slot, x):
        return f"      call wbgc_val({head},{slot},{x})\n"

    def lval(slot, x):
        return f"      call wbgc_lval({head},{slot},{x})\n"

    extra = {
        "GFS_suite_stateout_reset": [val(1, f"{D}%Grid%xlat_d(:)"), val(2, f"{D}%Grid%xlon_d(:)"),
                                     val(3, f"{D}%Sfcprop%slmsk(:)"), val(4, f"{D}%Sfcprop%fice(:)"),
                                     val(5, f"{D}%Sfcprop%landfrac(:)"), val(6, f"{D}%Sfcprop%lakefrac(:)"),
                                     val(7, f"{D}%Sfcprop%oceanfrac(:)"), val(8, f"{D}%Sfcprop%hice(:)"),
                                     val(9, f"{D}%Sfcprop%tisfc(:)"), val(10, f"{D}%Sfcprop%tsfc(:)"),
                                     val(11, f"{D}%Sfcprop%weasd(:)"), val(12, f"{D}%Sfcprop%snowd(:)"),
                                     val(13, f"{D}%Sfcprop%tsfco(:)"), val(14, f"{D}%Sfcprop%zorli(:)")],
        "GFS_surface_composites_pre": [val(15, f"{D}%Sfcprop%slmsk(:)"), val(16, f"{D}%Sfcprop%fice(:)"),
                                       lval(17, f"{I}%dry(:)"), lval(18, f"{I}%icy(:)"), lval(19, f"{I}%wet(:)"),
                                       lval(20, f"{I}%lake(:)"), val(21, f"{I}%frland(:)"),
                                       val(22, f"{D}%Sfcprop%hice(:)")],
        "GFS_surface_composites_post": [val(23, f"{D}%Sfcprop%evap(:)"), val(24, f"{I}%evap_water(:)"),
                                        val(25, f"{I}%evap_land(:)"), val(26, f"{I}%evap_ice(:)"),
                                        val(27, f"{D}%Sfcprop%slmsk(:)"), val(28, f"{D}%Sfcprop%fice(:)")],
        "GFS_MP_generic_post": [val(29, f"{D}%Intdiag%rain(:)"), val(30, f"{D}%Intdiag%rainc(:)")],
    }
    pat = re.compile(r'(      if \(cdata%errflg/=0\) then\n        cdata%errmsg = "An error occured in (\w+)_run: "'
                     r'[^\n]*\n        ierr=cdata%errflg\n        return\n      end if\n)')
    n = [0]

    def rep(m):
        n[0] += 1
        nm = m.group(2)
        if nm == "GFS_suite_interstitial_phys_reset":
            return m.group(1)
        return m.group(1) + snap(nm) + "".join(extra.get(nm, []))
    s = pat.sub(rep, s)
    if "con_g" not in s.split("physics_run_cap")[1][:20000]:
        print("WARN: con_g may not be in scope of the run cap")
    target.with_suffix(target.suffix + ".preWBGC").write_text(target.read_text())
    target.write_text(s)
    print(f"instrumented {target}: {n[0]} scheme calls")
else:
    sys.exit("mode must be src or cap")
