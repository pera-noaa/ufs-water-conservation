# apply_lim.py <tree> : MLM positivity limiter (#404 follow-up) on a tree that has fix_v2/v3 in mfscuq_mlm.f.
# 1) each water flux (qv qc qi qs, ice number) scaled by the limit of the layer it leaves, so no layer exports more than
#    q1 + delt*rtg_entry in one step (conservative: a flux is scaled whole); 2) cloud-base smoothing of qv, qc scaled back
#    so no layer of the three goes negative (T unchanged). Bitwise unchanged wherever no limit binds.
import sys, pathlib
P = pathlib.Path(sys.argv[1]) / 'UFSATM/ccpp/physics/physics/PBL/SATMEDMF'
edits = {}
def sub(path, a, b):
    s = edits.get(path) or path.read_text()
    assert s.count(a) == 1, (path.name, a[:60], s.count(a))
    edits[path] = s.replace(a, b)

m = P / 'mfscuq_mlm.f'
sub(m, "     &   prec,rad,buop,pres,del,liwse,mse,thlvx,\n",
       "     &   prec,rad,buop,pres,del,delt,liwse,mse,thlvx,\n")
sub(m, "      real(kind=kind_phys), intent(in) :: del(im,km)\n",
       "      real(kind=kind_phys), intent(in) :: del(im,km)\n"
       "      real(kind=kind_phys), intent(in) :: delt\n")
sub(m, "      real(kind=kind_phys) :: rhoi(im,km), fp, fm, dd, ww\n",
       "      real(kind=kind_phys) :: rhoi(im,km), fp, fm, dd, ww\n"
       "      real(kind=kind_phys) :: sa, sb, sc\n"
       "      integer :: n, nn\n")
sub(m, "      do k = 1, km-1\n         do i = 1, im\n            if (k.ge.mlmb(i).and.k.le.mlmt(i).and.cnvflg(i)) then\n"
       "            fp = rhoi(i,k+1)*grav/del(i,k)\n",
       "!     no layer exports more water than it holds in one step\n"
       "      call mlm_flxlim(im,ix,km,cnvflg,mlmb,mlmt,rhoi,del,\n"
       "     &   q1(:,:,1),rtg(:,:,1),delt,qvflux)\n"
       "      call mlm_flxlim(im,ix,km,cnvflg,mlmb,mlmt,rhoi,del,\n"
       "     &   q1(:,:,ntcw),rtg(:,:,ntcw),delt,qcflux)\n"
       "      call mlm_flxlim(im,ix,km,cnvflg,mlmb,mlmt,rhoi,del,\n"
       "     &   q1(:,:,ntiw),rtg(:,:,ntiw),delt,qiflux)\n"
       "      if (ntsw > 0) call mlm_flxlim(im,ix,km,cnvflg,mlmb,mlmt,\n"
       "     &   rhoi,del,q1(:,:,ntsw),rtg(:,:,ntsw),delt,qsflux)\n"
       "      if (nqni > 0) call mlm_flxlim(im,ix,km,cnvflg,mlmb,mlmt,\n"
       "     &   rhoi,del,q1(:,:,nqni),rtg(:,:,nqni),delt,qniflux)\n"
       "      do k = 1, km-1\n         do i = 1, im\n            if (k.ge.mlmb(i).and.k.le.mlmt(i).and.cnvflg(i)) then\n"
       "            fp = rhoi(i,k+1)*grav/del(i,k)\n")
sub(m, "               dd = 0.5*(rtg(i,k,1) + rtg(i,k-2,1)) - rtg(i,k-1,1)\n"
       "               rtg(i,k-1,1) = rtg(i,k-1,1) + dd\n"
       "               rtg(i,k,1)   = rtg(i,k,1)   - ww*dd\n"
       "               rtg(i,k-2,1) = rtg(i,k-2,1) - ww*dd\n"
       "               dd = 0.5*(rtg(i,k,ntcw) + rtg(i,k-2,ntcw))\n"
       "     &            - rtg(i,k-1,ntcw)\n"
       "               rtg(i,k-1,ntcw) = rtg(i,k-1,ntcw) + dd\n"
       "               rtg(i,k,ntcw)   = rtg(i,k,ntcw)   - ww*dd\n"
       "               rtg(i,k-2,ntcw) = rtg(i,k-2,ntcw) - ww*dd\n",
       "!              qv, qc: scaled back so none of the three layers goes negative\n"
       "               do nn = 1, 2\n"
       "                  n = 1\n"
       "                  if (nn.eq.2) n = ntcw\n"
       "                  dd = 0.5*(rtg(i,k,n) + rtg(i,k-2,n)) - rtg(i,k-1,n)\n"
       "                  sa = max(q1(i,k,n)+delt*rtg(i,k,n),0.0_kind_phys)\n"
       "                  sb = max(q1(i,k-2,n)+delt*rtg(i,k-2,n),0.0_kind_phys)\n"
       "                  sc = max(q1(i,k-1,n)+delt*rtg(i,k-1,n),0.0_kind_phys)\n"
       "                  if (dd.gt.0.) then\n"
       "                     dd = min(dd, sa/(delt*ww), sb/(delt*ww))\n"
       "                  else\n"
       "                     dd = max(dd, -sc/delt)\n"
       "                  endif\n"
       "                  rtg(i,k-1,n) = rtg(i,k-1,n) + dd\n"
       "                  rtg(i,k,n)   = rtg(i,k,n)   - ww*dd\n"
       "                  rtg(i,k-2,n) = rtg(i,k-2,n) - ww*dd\n"
       "               enddo\n")
sub(m, "      end module mfscuq_mlm_mod",
       "!> Scales each MLM interface flux of one tracer (flux k between layers k-1\n"
       "!! and k, upward positive) by the limit of the layer it leaves, so that no\n"
       "!! layer exports more than qx + delt*tx in one step\n"
       "      subroutine mlm_flxlim(im,ix,km,cnvflg,mlmb,mlmt,rhoi,del,\n"
       "     &   qx,tx,delt,flx)\n"
       "      use machine,  only : kind_phys\n"
       "      use physcons, grav => con_g\n"
       "      implicit none\n"
       "      integer, intent(in) :: im, ix, km, mlmb(im), mlmt(im)\n"
       "      logical, intent(in) :: cnvflg(im)\n"
       "      real(kind=kind_phys), intent(in) :: rhoi(im,km), del(im,km)\n"
       "      real(kind=kind_phys), intent(in) :: qx(ix,km), tx(im,km), delt\n"
       "      real(kind=kind_phys), intent(inout) :: flx(im,km)\n"
       "      integer :: i, k\n"
       "      real(kind=kind_phys) :: rl(km), outm, avail\n"
       "      do i = 1, im\n"
       "         if (cnvflg(i)) then\n"
       "            do k = mlmb(i)-1, mlmt(i)+1\n"
       "               outm = 0.0_kind_phys\n"
       "               if (k+1.le.mlmt(i)+1) outm = outm\n"
       "     &            + max(flx(i,k+1),0.0_kind_phys)*rhoi(i,k+1)\n"
       "               if (k.ge.mlmb(i)) outm = outm\n"
       "     &            + max(-flx(i,k),0.0_kind_phys)*rhoi(i,k)\n"
       "               outm  = outm*delt\n"
       "               avail = max(qx(i,k)+delt*tx(i,k),0.0_kind_phys)\n"
       "     &            *del(i,k)/grav\n"
       "               rl(k) = 1.0_kind_phys\n"
       "               if (outm.gt.avail) rl(k) = avail/outm\n"
       "            enddo\n"
       "            do k = mlmb(i), mlmt(i)+1\n"
       "               if (flx(i,k).gt.0.) then\n"
       "                  flx(i,k) = flx(i,k)*rl(k-1)\n"
       "               else\n"
       "                  flx(i,k) = flx(i,k)*rl(k)\n"
       "               endif\n"
       "            enddo\n"
       "         endif\n"
       "      enddo\n"
       "      end subroutine mlm_flxlim\n"
       "      end module mfscuq_mlm_mod")

v = P / 'satmedmfvdifq.F'
sub(v, "     &        prec,rad,buoy,prsl,del,slx,hx,thlvx,\n",
       "     &        prec,rad,buoy,prsl,del,delt,slx,hx,thlvx,\n")

for p, s in edits.items():
    p.write_text(s)
    print("patched", p)
