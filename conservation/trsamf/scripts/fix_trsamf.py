#!/usr/bin/env python3
"""Candidate fixes for SAMF/PBL passive-tracer transport (apply to the base tree = develop + water set incl. SA1).
usage: fix_trsamf.py <mode> <tree>
  mode t1    : T1 - SAMF deep and shallow tracer transport sub-stepped so that the donor-cell Courant number of the
               compensating (TVD) flux is <= 0.5 per sub-step; closure, T, q, u, v untouched.
  mode t1dry : t1 + DRY - chemistry tracers (field_table "tracer_usage","chemistry", i.e. the SAMF itc..itc+ntc-1
               block and the PBL trans_aero block) transported in SAMF deep, SAMF shallow and satmedmfvdifq as dry
               mixing ratios c = q/(1-qv0) with dry layer masses dp*(1-qv0) and fluxes scaled by the interface dry
               fraction; qv0 = physics-step initial specific humidity, the value the write-back keeps dry mass with.
  mode exp   : TEST build, both, switched at run time by env TRSAMF_T1 (0 off, 1 all tracers, 2 only tracers after TKE),
               TRSAMF_CMAX (Courant bound, default 0.5), TRSAMF_DRY (0/1).
Every anchor must match exactly once."""
import sys, re
from pathlib import Path
mode, top = sys.argv[1], Path(sys.argv[2])
SRC_CLEAN = True   # clean modes: parcel sources taken from the donor layer (see SRC in the helpers)
assert mode in ('t1', 't1dry', 'exp'), mode
phys = top / "UFSATM/ccpp/physics/physics"
edits = {}
def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count}, found {n}: {old.strip()[:80]!r}")
    if path.suffix in ('.f', '.F'):
        for ln in new.splitlines():
            body = ln[:72] if (len(ln) >= 73 and ln[72:].strip() == '&') else ln
            if len(body) > 72 and not ln.lstrip().startswith('!') and not ln.startswith(('c', 'C', '!')):
                sys.exit(f"ABORT >72 cols in {path.name}: {ln!r}")
    edits[path] = s.replace(old, new)

if mode == 'exp':
    SW_DECL = ("      integer trsw_t1, trsw_dry, trsw_st, trsw_src\n"
               "      real(kind=conv_wp) trcmax\n      character(len=32) trsw_s\n")
    SW_SET = ("        call get_environment_variable('TRSAMF_T1', trsw_s,\n"
              "     &       status=trsw_st)\n"
              "        trsw_t1 = 0\n"
              "        if (trsw_st == 0) read(trsw_s,*) trsw_t1\n"
              "        call get_environment_variable('TRSAMF_DRY', trsw_s,\n"
              "     &       status=trsw_st)\n"
              "        trsw_dry = 0\n"
              "        if (trsw_st == 0) read(trsw_s,*) trsw_dry\n"
              "        call get_environment_variable('TRSAMF_CMAX', trsw_s,\n"
              "     &       status=trsw_st)\n"
              "        trcmax = 0.5_conv_wp\n"
              "        if (trsw_st == 0) read(trsw_s,*) trcmax\n"
              "        call get_environment_variable('TRSAMF_SRC', trsw_s,\n"
              "     &       status=trsw_st)\n"
              "        trsw_src = 0\n"
              "        if (trsw_st == 0) read(trsw_s,*) trsw_src\n"
              "        trsrc = trsw_src > 0\n")
    T1_ON = "trsw_t1 > 0"
    DRY_ON = "trsw_dry > 0"
    T1_SEL = "(trsw_t1 == 1 .or. n > ntk-2)"
else:
    SW_DECL = "      real(kind=conv_wp), parameter :: trcmax = 0.5_conv_wp\n"
    SW_SET = "        trsrc = .true.\n" if SRC_CLEAN else "        trsrc = .false.\n"
    T1_ON = ".true."
    DRY_ON = ".true." if mode == 't1dry' else ".false."
    T1_SEL = ".true."

def simplify(code):
    """drop dead switches in the clean modes"""
    if mode == 'exp':
        return code
    code = code.replace(" .and. .true.", "").replace("(.true.) .and. ", "")
    return code

# ---------------------------------------------------------------- SAMF deep
f = phys / "CONV/SAMF/samfdeepcnv.f"
sub(f, "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n",
    "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n"
    "      real(kind=conv_wp) trfsc(ntr), trwl(km), trpw(km,ntr), trcm\n"
    "      logical trdo(ntr), trupd(ntr), trdry(ntr), tranyd, trsrc\n"
    "      integer nsub\n" + SW_DECL)
DEEP_CALL = """!
! tracers: transport in nsub sub-steps so that the donor-cell Courant
! number of the compensating flux stays <= trcmax (explicit TVD update)
"""
if mode != 't1':
    DEEP_CALL += "! chemistry tracers as dry mixing ratios (dry mass as the host keeps)\n"
DEEP_CALL += "!\n      if (.not.hwrf_samfdeep) then\n" + SW_SET + """        do n = 1, ntr
          trfsc(n) = 0.0_conv_wp
          trupd(n) = .true.
          trdry(n) = .false.
        enddo
        if (do_aerosols) then
          do n = itc-2+ntc, ntr
            trupd(n) = .false.
          enddo
          do n = 1, ntc
            trfsc(n+itc-3) = real(fscav(n), kind=conv_wp)
            trdry(n+itc-3) = DRYON
          enddo
          if (ntk > 2) then
            trfsc(ntk-2) = 0.0_conv_wp
            trupd(ntk-2) = .true.
            trdry(ntk-2) = .false.
          endif
        endif
        do i = 1, im
          if (cnvflg(i)) then
            trcm = 0.0_conv_wp
            do k = 1, ktcon(i)-1
              tem = 0.0_conv_wp
              if(k >= kb(i)) tem = eta(i,k)
              if(k <= jmin(i)) tem = tem - edto(i) * etad(i,k)
              kk = k
              if(tem > 0.0_conv_wp) kk = k + 1
              trcm = max(trcm, abs(tem) * xmb(i) * dt2
     &          * real(grav, kind=conv_wp) / (1000.0_conv_wp*del(i,kk)))
            enddo
            if (trsrc) trcm = max(trcm, eta(i,kb(i)) * xmb(i) * dt2
     &        * real(grav, kind=conv_wp)/(1000.0_conv_wp*del(i,kb(i))),
     &        edto(i) * etad(i,jmin(i)) * xmb(i) * dt2
     &     * real(grav,kind=conv_wp)/(1000.0_conv_wp*del(i,jmin(i)+1)))
            nsub = 1
            if (T1ON) nsub = max(1, ceiling(trcm / trcmax))
            tranyd = .false.
            do n = 1, ntr
              trdo(n) = trdry(n) .or.
     &                  (nsub > 1 .and. T1SEL)
              tranyd = tranyd .or. trdo(n)
            enddo
            if (tranyd) then
              do k = 1, km
                trwl(k) = 1.0_conv_wp - real(q(i,k), kind=conv_wp)
              enddo
              call samfdeep_trsub(km,ntr,nsub,kb(i),jmin(i),ktcon(i),
     &          kmax(i),eta(i,:),etad(i,:),edto(i),xlamue(i,:),
     &          xlamdet(i),zi(i,:),del(i,:),xmb(i),dt2,
     &          real(grav, kind=conv_wp),cq,trdo,trupd,trdry,trfsc,
     &          c0t(i,:),trwl,trsrc,ctr(i,:,:),trpw)
              do n = 1, ntr
                if (trdo(n)) then
                  do k = 1, km
                    dellae(i,k,n) = 0.0_conv_wp
                  enddo
                endif
              enddo
              if (do_aerosols) then
                do n = 1, ntc
                  if (trdo(n+itc-3)) then
                    do k = 1, km
                      chem_pw(i,k,n) = trpw(k,n+itc-3)
                    enddo
                  endif
                enddo
              endif
            endif
          endif
        enddo
      endif
"""
DEEP_CALL = simplify(DEEP_CALL.replace("DRYON", DRY_ON).replace("T1ON", T1_ON).replace("T1SEL", T1_SEL))
DEEP_CALL = DEEP_CALL.replace("            if (.true.) nsub = max(1, ceiling(trcm / trcmax))\n",
                              "            nsub = max(1, ceiling(trcm / trcmax))\n")
DEEP_CALL = DEEP_CALL.replace("trdo(n) = trdry(n) .or.\n     &                  (nsub > 1)\n",
                              "trdo(n) = trdry(n) .or. nsub > 1\n")
DEEP_CALL = DEEP_CALL.replace("            nsub = 1\n            nsub = max", "            nsub = max")
sub(f, "      if (.not.hwrf_samfdeep) then\n       indx = ntk - 2\n       do n = 1, ntr\n",
    DEEP_CALL + "      if (.not.hwrf_samfdeep) then\n       indx = ntk - 2\n       do n = 1, ntr\n")

DEEP_SUB = """!> Tracer transport of samfdeepcnv for one column in nsub equal
!! sub-steps, mass fluxes held: every sub-step recomputes interface,
!! updraft and downdraft tracer values and the TVD compensating flux.
!! trdry tracers are moved as c = q/wl with each interface flux
!! scaled by the interface dry fraction (wl = 1 - initial qv).
      subroutine samfdeep_trsub(km,ntr,nsub,kb,jmin,ktcon,kmax,
     &   eta,etad,edto,xlamue,xlamdet,zi,del,xmb,dt2,grav,cq,
     &   trdo,trupd,trdry,trfsc,c0t,wl,trsrc,ctr,trpw)
      implicit none
      integer, intent(in) :: km,ntr,nsub,kb,jmin,ktcon,kmax
      real(kind=conv_wp), intent(in) :: eta(km),etad(km),edto,
     &   xlamue(km),xlamdet,zi(km),del(km),xmb,dt2,grav,cq,
     &   trfsc(ntr),c0t(km),wl(km)
      logical, intent(in) :: trdo(ntr),trupd(ntr),trdry(ntr),trsrc
      real(kind=conv_wp), intent(inout) :: ctr(km,ntr)
      real(kind=conv_wp), intent(out) :: trpw(km,ntr)
      real(kind=conv_wp) c(km),cto(km),eck(km),erk(km),ecd(km),
     &   dl(km),flx(0:km),ed(0:km),wf(km),wc(km),tem,tem1,tem2,
     &   ptem1,ptem2,rrkp,phkp,aup,adw,dz,dp,factor,chc,dts,rns
      integer n,it,k,km1
      km1 = km - 1
      rns = 1.0_conv_wp / real(nsub, kind=conv_wp)
      dts = dt2 * rns
      trpw = 0.0_conv_wp
      do n = 1, ntr
        if (.not. trdo(n)) cycle
        do k = 1, km
          wc(k) = 1.0_conv_wp
          wf(k) = 1.0_conv_wp
        enddo
        if (trdry(n)) then
          do k = 1, kmax
            wc(k) = wl(k)
          enddo
          do k = 1, min(kmax, km1)
            wf(k) = 0.5_conv_wp * (wl(k) + wl(k+1))
          enddo
        endif
        do it = 1, nsub
          do k = 1, km
            c(k) = 0.0_conv_wp
            eck(k) = 0.0_conv_wp
            erk(k) = 0.0_conv_wp
            ecd(k) = 0.0_conv_wp
            dl(k) = 0.0_conv_wp
          enddo
          do k = 1, kmax
            c(k) = ctr(k,n) / wc(k)
            cto(k) = c(k)
          enddo
          do k = 1, km1
            if (k <= kmax-1) cto(k) = 0.5_conv_wp * (c(k) + c(k+1))
          enddo
! updraft (and scavenging); trsrc: starts from the source layer kb
          eck(kb) = cto(kb)
          if (trsrc) eck(kb) = c(kb)
          erk(kb) = eck(kb)
          if (trupd(n)) then
            do k = kb+1, min(kmax-1, km1)
              dz = zi(k) - zi(k-1)
              tem = 0.25_conv_wp * (xlamue(k)+xlamue(k-1)) * dz
              tem = cq * tem
              factor = 1.0_conv_wp + tem
              eck(k) = ((1.0_conv_wp-tem)*eck(k-1)+tem*
     &                 (cto(k)+cto(k-1)))/factor
              erk(k) = eck(k)
              if (trfsc(n) /= 0.0_conv_wp) then
                chc = trfsc(n) * eck(k)
                tem = chc / (1.0_conv_wp + c0t(k) * dz)
                trpw(k,n) = trpw(k,n) + c0t(k) * dz * tem
     &                    * eta(k-1) * wf(k-1) * rns
                eck(k) = tem + eck(k) - chc
              endif
            enddo
          endif
! downdraft; trsrc: starts from layer jmin+1, which loses its air
          ecd(jmin) = cto(jmin)
          if (trsrc) ecd(jmin) = c(jmin+1)
          do k = jmin-1, 1, -1
            dz = zi(k+1) - zi(k)
            tem = 0.5_conv_wp * xlamdet * dz
            tem = cq * tem
            factor = 1.0_conv_wp + tem
            ecd(k) = ((1.0_conv_wp-tem)*ecd(k+1)+tem*
     &              (cto(k)+cto(k+1)))/factor
          enddo
! up/downdraft exchange per unit cloud-base mass flux
          dp = 1000.0_conv_wp * del(1)
          dl(1) = edto * etad(1) * ecd(1) * wf(1) * grav / dp
          do k = 2, km1
            if (k < ktcon) then
              aup = 1.0_conv_wp
              if(k <= kb) aup = 0.0_conv_wp
              adw = 1.0_conv_wp
              if(k > jmin) adw = 0.0_conv_wp
              dp = 1000.0_conv_wp * del(k)
              tem1 = -eta(k) * erk(k) * wf(k)
              tem2 = -eta(k-1) * eck(k-1) * wf(k-1)
              ptem1 = -etad(k) * ecd(k) * wf(k)
              ptem2 = -etad(k-1) * ecd(k-1) * wf(k-1)
              dl(k) = dl(k) + (aup*(tem1-tem2)-adw*
     &                edto*(ptem1-ptem2))*grav/dp
            endif
          enddo
          dp = 1000.0_conv_wp * del(ktcon)
          dl(ktcon) = eta(ktcon-1) * eck(ktcon-1) * wf(ktcon-1)
     &              * grav / dp
! compensating subsidence/uplift, TVD (cloud-base faces as SA1)
          do k = 0, km
            ed(k) = 0.0_conv_wp
            flx(k) = 0.0_conv_wp
          enddo
          do k = 1, km1
            if (k <= ktcon) ed(k) = c(k) - c(k+1)
          enddo
          if (c(1) >= 0.0_conv_wp) then
            ed(0) = max(0.0_conv_wp,2.0_conv_wp*c(1)-c(2))-c(1)
          else
            ed(0) = min(0.0_conv_wp,2.0_conv_wp*c(1)-c(2))-c(1)
          endif
          do k = 1, km1
            if (k < ktcon) then
              tem = 0.0_conv_wp
              if(k >= kb) tem = eta(k)
              if(k <= jmin) tem = tem - edto * etad(k)
              if(tem > 0.0_conv_wp) then
                rrkp = 0.0_conv_wp
                if(abs(ed(k)) > 1.e-22_conv_wp) rrkp = ed(k+1)/ed(k)
                phkp = (rrkp+abs(rrkp)) / (1.0_conv_wp+abs(rrkp))
                tem1 = c(k+1) + phkp*(cto(k)-c(k+1))
                flx(k) = tem * tem1
              elseif(tem < 0.0_conv_wp) then
                rrkp = 0.0_conv_wp
                if(abs(ed(k)) > 1.e-22_conv_wp) rrkp = ed(k-1)/ed(k)
                phkp = (rrkp+abs(rrkp)) / (1.0_conv_wp+abs(rrkp))
                tem1 = c(k) + phkp*(cto(k)-c(k))
                flx(k) = tem * tem1
              else
                tem1 = cto(k)
                flx(k) = 0.0_conv_wp
              endif
              if (.not. trsrc) then
                if(k == kb) flx(k) = flx(k) + eta(k) * (cto(k) - tem1)
                if(k == jmin) flx(k) = flx(k)
     &            - edto * etad(k) * (cto(k) - tem1)
              endif
              flx(k) = flx(k) * wf(k)
              if(k == jmin) then
                dp = 1000.0_conv_wp * del(k+1)
                dl(k+1) = dl(k+1) - edto * etad(k) * ecd(k) * wf(k)
     &                  * grav / dp
              endif
              if(k == kb) then
                dp = 1000.0_conv_wp * del(k)
                dl(k) = dl(k) - eta(k) * eck(k) * wf(k) * grav / dp
              endif
            endif
          enddo
          do k = 1, km1
            if (k <= ktcon) then
              dp = 1000.0_conv_wp * del(k)
              dl(k) = dl(k) + (flx(k) - flx(k-1)) * grav / dp
            endif
          enddo
          do k = 1, min(ktcon, kmax)
            ctr(k,n) = ctr(k,n) + dl(k) * xmb * dts
          enddo
        enddo
      enddo
      end subroutine samfdeep_trsub
"""
sub(f, "      end subroutine samfdeepcnv_run\n", "      end subroutine samfdeepcnv_run\n\n" + DEEP_SUB)

# ---------------------------------------------------------------- SAMF shallow
f = phys / "CONV/SAMF/samfshalcnv.f"
sub(f, "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n",
    "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n"
    "      real(kind=conv_wp) trfsc(ntr), trwl(km), trpw(km,ntr), trcm\n"
    "      logical trdo(ntr), trupd(ntr), trdry(ntr), tranyd, trsrc\n"
    "      integer nsub\n" + SW_DECL)
SHAL_CALL = DEEP_CALL.replace("hwrf_samfdeep", "hwrf_samfshal")
SHAL_CALL = SHAL_CALL.replace("trfsc(n+itc-3) = real(fscav(n), kind=conv_wp)",
                              "trfsc(n+itc-3) = escav * real(fscav(n), kind=conv_wp)")
SHAL_CALL = SHAL_CALL.replace("""            do k = 1, ktcon(i)-1
              tem = 0.0_conv_wp
              if(k >= kb(i)) tem = eta(i,k)
              if(k <= jmin(i)) tem = tem - edto(i) * etad(i,k)
              kk = k
              if(tem > 0.0_conv_wp) kk = k + 1
              trcm = max(trcm, abs(tem) * xmb(i) * dt2
     &          * real(grav, kind=conv_wp) / (1000.0_conv_wp*del(i,kk)))
            enddo
            if (trsrc) trcm = max(trcm, eta(i,kb(i)) * xmb(i) * dt2
     &        * real(grav, kind=conv_wp)/(1000.0_conv_wp*del(i,kb(i))),
     &        edto(i) * etad(i,jmin(i)) * xmb(i) * dt2
     &     * real(grav,kind=conv_wp)/(1000.0_conv_wp*del(i,jmin(i)+1)))
""", """            do k = kb(i), ktcon(i)-1
              trcm = max(trcm, eta(i,k) * xmb(i) * dt2
     &          * real(grav, kind=conv_wp)/(1000.0_conv_wp*del(i,k+1)))
            enddo
            if (trsrc) trcm = max(trcm, eta(i,kb(i)) * xmb(i) * dt2
     &        * real(grav, kind=conv_wp)/(1000.0_conv_wp*del(i,kb(i))))
""")
SHAL_CALL = SHAL_CALL.replace("""              call samfdeep_trsub(km,ntr,nsub,kb(i),jmin(i),ktcon(i),
     &          kmax(i),eta(i,:),etad(i,:),edto(i),xlamue(i,:),
     &          xlamdet(i),zi(i,:),del(i,:),xmb(i),dt2,
     &          real(grav, kind=conv_wp),cq,trdo,trupd,trdry,trfsc,
     &          c0t(i,:),trwl,trsrc,ctr(i,:,:),trpw)
""", """              call samfshal_trsub(km,ntr,nsub,kb(i),ktcon(i),kmax(i),
     &          eta(i,:),xlamue(i,:),zi(i,:),del(i,:),xmb(i),dt2,
     &          real(grav, kind=conv_wp),cq,trdo,trupd,trdry,trfsc,
     &          c0t(i,:),trwl,trsrc,ctr(i,:,:),trpw)
              if (trsrc) then
                do n = 1, ntr
                  if (trdo(n)) new_qtr(i,kb(i),n+2) = ctr(i,kb(i),n)
                enddo
              endif
""")
assert "samfshal_trsub" in SHAL_CALL and "do k = kb(i), ktcon(i)-1" in SHAL_CALL
sub(f, "      if (.not.hwrf_samfshal) then\n!\n      indx = ntk - 2\n      do n = 1, ntr\n",
    SHAL_CALL + "      if (.not.hwrf_samfshal) then\n!\n      indx = ntk - 2\n      do n = 1, ntr\n")
SHAL_SUB = """!> Tracer transport of samfshalcnv for one column in nsub equal
!! sub-steps (as samfdeep_trsub, without downdraft).
      subroutine samfshal_trsub(km,ntr,nsub,kb,ktcon,kmax,
     &   eta,xlamue,zi,del,xmb,dt2,grav,cq,
     &   trdo,trupd,trdry,trfsc,c0t,wl,trsrc,ctr,trpw)
      implicit none
      integer, intent(in) :: km,ntr,nsub,kb,ktcon,kmax
      real(kind=conv_wp), intent(in) :: eta(km),
     &   xlamue(km),zi(km),del(km),xmb,dt2,grav,cq,
     &   trfsc(ntr),c0t(km),wl(km)
      logical, intent(in) :: trdo(ntr),trupd(ntr),trdry(ntr),trsrc
      real(kind=conv_wp), intent(inout) :: ctr(km,ntr)
      real(kind=conv_wp), intent(out) :: trpw(km,ntr)
      real(kind=conv_wp) c(km),cto(km),eck(km),erk(km),
     &   dl(km),flx(0:km),ed(0:km),wf(km),wc(km),tem,tem1,tem2,
     &   rrkp,phkp,dz,dp,factor,chc,dts,rns
      integer n,it,k,km1
      km1 = km - 1
      rns = 1.0_conv_wp / real(nsub, kind=conv_wp)
      dts = dt2 * rns
      trpw = 0.0_conv_wp
      do n = 1, ntr
        if (.not. trdo(n)) cycle
        do k = 1, km
          wc(k) = 1.0_conv_wp
          wf(k) = 1.0_conv_wp
        enddo
        if (trdry(n)) then
          do k = 1, kmax
            wc(k) = wl(k)
          enddo
          do k = 1, min(kmax, km1)
            wf(k) = 0.5_conv_wp * (wl(k) + wl(k+1))
          enddo
        endif
        do it = 1, nsub
          do k = 1, km
            c(k) = 0.0_conv_wp
            eck(k) = 0.0_conv_wp
            erk(k) = 0.0_conv_wp
            dl(k) = 0.0_conv_wp
          enddo
          do k = 1, kmax
            c(k) = ctr(k,n) / wc(k)
            cto(k) = c(k)
          enddo
          do k = 1, km1
            if (k <= kmax-1) cto(k) = 0.5_conv_wp * (c(k) + c(k+1))
          enddo
          eck(kb) = cto(kb)
          if (trsrc) eck(kb) = c(kb)
          erk(kb) = eck(kb)
          if (trupd(n)) then
            do k = kb+1, min(kmax-1, km1)
              dz = zi(k) - zi(k-1)
              tem = 0.25_conv_wp * (xlamue(k)+xlamue(k-1)) * dz
              tem = cq * tem
              factor = 1.0_conv_wp + tem
              eck(k) = ((1.0_conv_wp-tem)*eck(k-1)+tem*
     &                 (cto(k)+cto(k-1)))/factor
              erk(k) = eck(k)
              if (trfsc(n) /= 0.0_conv_wp) then
                chc = trfsc(n) * eck(k)
                tem = chc / (1.0_conv_wp + c0t(k) * dz)
                trpw(k,n) = trpw(k,n) + c0t(k) * dz * tem
     &                    * eta(k-1) * wf(k-1) * rns
                eck(k) = tem + eck(k) - chc
              endif
            enddo
          endif
          do k = 2, km1
            if (k > kb .and. k < ktcon) then
              dp = 1000.0_conv_wp * del(k)
              tem1 = -eta(k) * erk(k) * wf(k)
              tem2 = -eta(k-1) * eck(k-1) * wf(k-1)
              dl(k) = dl(k) + (tem1-tem2) * grav / dp
            endif
          enddo
          dp = 1000.0_conv_wp * del(ktcon)
          dl(ktcon) = eta(ktcon-1) * eck(ktcon-1) * wf(ktcon-1)
     &              * grav / dp
          do k = 0, km
            ed(k) = 0.0_conv_wp
            flx(k) = 0.0_conv_wp
          enddo
          do k = 1, km1
            if (k <= ktcon) ed(k) = c(k) - c(k+1)
          enddo
          do k = 1, km1
            if (k >= kb .and. k < ktcon) then
              if(eta(k) > 0.0_conv_wp) then
                rrkp = 0.0_conv_wp
                if(abs(ed(k)) > 1.e-22_conv_wp) rrkp = ed(k+1)/ed(k)
                phkp = (rrkp+abs(rrkp)) / (1.0_conv_wp+abs(rrkp))
                tem1 = c(k+1) + phkp*(cto(k)-c(k+1))
                flx(k) = eta(k) * tem1
                if(k == kb .and. .not. trsrc) flx(k) = eta(k) * cto(k)
                flx(k) = flx(k) * wf(k)
              endif
            endif
          enddo
          do k = 2, km1
            if (k > kb .and. k <= ktcon) then
              dp = 1000.0_conv_wp * del(k)
              dl(k) = dl(k) + (flx(k) - flx(k-1)) * grav / dp
            endif
          enddo
          if (trsrc) then
            dp = 1000.0_conv_wp * del(kb)
            dl(kb) = (flx(kb) - eta(kb) * eck(kb) * wf(kb)) * grav / dp
          endif
          do k = 1, km
            if ((k > kb .or. (trsrc .and. k == kb)) .and.
     &          k <= ktcon) then
              ctr(k,n) = ctr(k,n) + dl(k) * xmb * dts
            endif
          enddo
        enddo
      enddo
      end subroutine samfshal_trsub
"""
sub(f, "      end subroutine samfshalcnv_run\n", "      end subroutine samfshalcnv_run\n\n" + SHAL_SUB)


# ---------------------------------------------------------------- satmedmfvdifq (DRY only)
if mode in ('t1dry', 'exp'):
    f = phys / "PBL/SATMEDMF/satmedmfvdifq.F"
    m = phys / "PBL/SATMEDMF/satmedmfvdifq.meta"
    sub(f, "     &     ten_t, ten_u, ten_v,                                         &\n     &     errmsg,errflg)\n",
        "     &     ten_t, ten_u, ten_v, trans_aero, ntchm,                      &\n     &     errmsg,errflg)\n")
    s = edits.get(m) or m.read_text()
    i = s.index("[errmsg]", s.index("[errmsg]") + 1)
    edits[m] = s[:i] + """[trans_aero]
  standard_name = flag_for_aerosol_convective_transport_and_PBL_diffusion
  long_name = flag for aerosol convective transport and PBL diffusion
  units = flag
  dimensions = ()
  type = logical
  intent = in
[ntchm]
  standard_name = number_of_chemical_tracers
  long_name = number of chemical tracers
  units = count
  dimensions = ()
  type = integer
  intent = in
""" + s[i:]
    PDECL = ("      logical, intent(in) :: trans_aero\n      integer, intent(in) :: ntchm\n"
             "      logical trdry(ntrac)\n      integer ndry, nd, is0\n"
             "      real(kind=kind_phys) q1c(im,km,ntrac), trwl(im,km),\n"
             "     &   tral(im,km), trad(im,km), trau(im,km), trf3(im,km*ntrac),\n"
             "     &   trwf, trdd, trdu\n")
    if mode == 'exp':
        PDECL += "      integer trsw_dry, trsw_st\n      character(len=32) trsw_s\n"
    sub(f, "      integer i,is,k,n,ndt,km1,kmpbl,kmscu,ntrac1,idtend\n",
        "      integer i,is,k,n,ndt,km1,kmpbl,kmscu,ntrac1,idtend\n" + PDECL)
    PSET = """!
! chemistry tracers (the ntchm before TKE) as dry mixing ratios
! c = q/(1-qv), qv = q1(:,:,1) = physics-step initial vapour
!
      do n = 1, ntrac
        trdry(n) = .false.
      enddo
"""
    if mode == 'exp':
        PSET += """      call get_environment_variable('TRSAMF_DRY', trsw_s,
     &     status=trsw_st)
      trsw_dry = 0
      if (trsw_st == 0) read(trsw_s,*) trsw_dry
      if (trsw_dry > 0 .and. trans_aero .and. ntchm > 0) then
"""
    else:
        PSET += "      if (trans_aero .and. ntchm > 0) then\n"
    PSET += """        do n = max(2, ntke-ntchm), ntke-1
          trdry(n) = .true.
        enddo
      endif
      ndry = 0
      do n = 1, ntrac
        if (trdry(n)) ndry = ndry + 1
      enddo
      do k = 1, km
        do i = 1, im
          trwl(i,k) = 1. - q1(i,k,1)
        enddo
      enddo
      do n = 1, ntrac
        do k = 1, km
          do i = 1, im
            q1c(i,k,n) = q1(i,k,n)
            if (trdry(n)) q1c(i,k,n) = q1(i,k,n) / trwl(i,k)
          enddo
        enddo
      enddo
"""
    sub(f, "      ntrac1 = ntrac - 1\n      km1 = km - 1\n", "      ntrac1 = ntrac - 1\n      km1 = km - 1\n" + PSET)
    sub(f, "            qcko(i,k,n) = q1(i,k,n)\n", "            qcko(i,k,n) = q1c(i,k,n)\n")
    sub(f, "            qcdo(i,k,n) = q1(i,k,n)\n", "            qcdo(i,k,n) = q1c(i,k,n)\n")
    sub(f, "     &    pcnvflg,zl,zm,q1,t1,u1,v1,plyr,pix,thlx,thvx,\n", "     &    pcnvflg,zl,zm,q1c,t1,u1,v1,plyr,pix,thlx,thvx,\n")
    sub(f, "     &    scuflg,zl,zm,q1,t1,u1,v1,plyr,pix,\n", "     &    scuflg,zl,zm,q1c,t1,u1,v1,plyr,pix,\n")
    s = edits[f]
    a = s.index("      kps = max(kmpbl, kmscu)\n!\n! for moisture and tracers including hydrometeors\n")
    b = s.index("! for TKE or TTE\n", a)
    blk = s[a:b]
    assert blk.count("q1(") == 15, blk.count("q1(")
    edits[f] = s[:a] + blk.replace("q1(", "q1c(") + s[b:]
    sub(f, "            f2(i,1+is) = q1(i,1,n)\n", "            f2(i,1+is) = q1c(i,1,n)\n")
    sub(f, "                f2(i,k+1+is)= q1(i,k+1,n) + ptem * ptem2\n", "                f2(i,k+1+is)= q1c(i,k+1,n) + ptem * ptem2\n")
    sub(f, "                f2(i,k+1+is) = q1(i,k+1,n)\n", "                f2(i,k+1+is) = q1c(i,k+1,n)\n")
    PSOLVE = """!
! dry tracers: same transport for c with dry layer masses del*(1-qv)
! and interface fluxes scaled by the interface dry fraction
!
      if (ndry > 0) then
        do i = 1, im
          trad(i,1) = 1.
        enddo
        do k = 1, km1
          do i = 1, im
            trwf = 0.5 * (trwl(i,k) + trwl(i,k+1))
            trdd = dt2 / (del(i,k) * trwl(i,k))
            trdu = dt2 / (del(i,k+1) * trwl(i,k+1))
            dsig = prsl(i,k)-prsl(i,k+1)
            rdz = rdzt(i,k)
            tem1 = dsig * dkt(i,k) * rdz
            dsdz2 = tem1 * rdz * trwf
            trau(i,k) = -trdd*dsdz2
            tral(i,k) = -trdu*dsdz2
            trad(i,k) = trad(i,k)-trau(i,k)
            trad(i,k+1)= 1.-tral(i,k)
          enddo
        enddo
        nd = 0
        do n = 2, ntrac1
          if (.not. trdry(n)) cycle
          nd = nd + 1
          is = (nd-1) * km
          do i = 1, im
            trf3(i,1+is) = q1c(i,1,n)
          enddo
          do k = 1, km1
            do i = 1, im
              trwf = 0.5 * (trwl(i,k) + trwl(i,k+1))
              trdd = dt2 / (del(i,k) * trwl(i,k))
              trdu = dt2 / (del(i,k+1) * trwl(i,k+1))
              dsig  = prsl(i,k)-prsl(i,k+1)
              tem2  = dsig * rdzt(i,k) * trwf
              if(pcnvflg(i) .and. k < kpbl(i)) then
                ptem  = 0.5 * tem2 * xmf(i,k)
                ptem1 = trdd * ptem
                ptem2 = trdu * ptem
                ptem  = qcko(i,k,n) + qcko(i,k+1,n)
                trf3(i,k+is) = trf3(i,k+is) - ptem * ptem1
                trf3(i,k+1+is)= q1c(i,k+1,n) + ptem * ptem2
              else
                trf3(i,k+1+is) = q1c(i,k+1,n)
              endif
              if(scuflg(i)) then
                if(k >= mrad(i) .and. k < krad(i)) then
                  ptem  = 0.5 * tem2 * xmfd(i,k)
                  ptem1 = trdd * ptem
                  ptem2 = trdu * ptem
                  ptem  = qcdo(i,k,n) + qcdo(i,k+1,n)
                  trf3(i,k+is)  = trf3(i,k+is) + ptem * ptem1
                  trf3(i,k+1+is)= trf3(i,k+1+is) - ptem * ptem2
                endif
              endif
              kmx = max(kpbl(i), krad(i))
              if((pcnvflg(i) .or. scuflg(i)) .and. (k < kmx)) then
                ptem  = tem2 * (xmf(i,k) - xmfd(i,k))
                ptem1 = trdd * ptem
                ptem2 = trdu * ptem
                trf3(i,k+is)   = trf3(i,k+is) + q_half(i,k,n) * ptem1
                trf3(i,k+1+is) = trf3(i,k+1+is) - q_half(i,k,n) * ptem2
              endif
            enddo
          enddo
        enddo
        call tridit(im,km,ndry,tral,trad,trau,trf3,trau,trf3)
        nd = 0
        do n = 2, ntrac1
          if (.not. trdry(n)) cycle
          nd = nd + 1
          is = (nd-1) * km
          is0 = (n-1) * km
          do k = 1, km
            do i = 1, im
              f2(i,k+is0) = trf3(i,k+is) * trwl(i,k)
            enddo
          enddo
        enddo
      endif
"""
    sub(f, "      call tridin(im,km,ntrac1,al,ad,au,f1,f2,au,f1,f2)\n",
        "      call tridin(im,km,ntrac1,al,ad,au,f1,f2,au,f1,f2)\n" + PSOLVE)

for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
