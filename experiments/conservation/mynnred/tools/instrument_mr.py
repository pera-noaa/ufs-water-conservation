#!/usr/bin/env python3
"""mynnred: add a passive dump around MYNN's moisture_check (module_bl_mynn.F90, in place).

Per rank (SLURM_PROCID): cumulative fill statistics (mynnred_stats_<r>.txt, rewritten every 200 calls)
and verbatim columns (mynnred_col_<r>_<n>.txt: first 3 columns with a liquid/ice fill on ranks < 16;
mynnred_scol_<r>_<n>.txt: first 2 with a snow fill, any rank). Nothing it computes feeds back.
"""
import sys

path = sys.argv[1]
src = open(path).read()

decl_anchor = "    real(kind_phys), dimension(kts:kte) :: a,b,c,d,x\n    real(kind_phys), dimension(kts:kte+1) :: rhoz,"
assert src.count(decl_anchor) == 1, "decl anchor"
src = src.replace(decl_anchor, "    real(kind_phys), dimension(kts:kte) :: a,b,c,d,x\n"
                  "    real(kind_phys), dimension(kts:kte) :: mr_thl0,mr_sqv0,mr_sqc0,mr_sqi0,mr_sqs0, &\n"
                  "         &mr_dqv0,mr_dqc0,mr_dqi0,mr_dqs0\n"
                  "    real(kind_phys), dimension(kts:kte+1) :: rhoz,", 1)

call_anchor = ("    !ensure non-negative moist species\n"
               "    CALL moisture_check(kte, delt, delp, exner,        &\n"
               "                        sqv2, sqc2, sqi2, sqs2, thl,   &\n")
assert src.count(call_anchor) == 1, "call anchor"
src = src.replace(call_anchor,
                  "    mr_thl0=thl; mr_sqv0=sqv2; mr_sqc0=sqc2; mr_sqi0=sqi2; mr_sqs0=sqs2 ! mynnred dump\n"
                  "    mr_dqv0=Dqv; mr_dqc0=Dqc; mr_dqi0=Dqi; mr_dqs0=Dqs\n" + call_anchor, 1)

dth_anchor = ("         Dth(k)=(thl(k)+xlvcp/exner(k)*sqc2(k) - th(k))/delt\n"
              "         !Use form from Tripoli and Cotton (1981) with their\n"
              "         !suggested min temperature to improve accuracy.\n"
              "         !Dth(k)=(thl(k)*(1.+ xlvcp/MAX(tk(k),TKmin)*sqc(k))  &\n"
              "         !&               - th(k))/delt\n"
              "      ENDDO\n"
              "    ENDIF\n")
assert src.count(dth_anchor) == 1, "dth anchor"
src = src.replace(dth_anchor, dth_anchor +
                  "    call mynnred_dump(kts,kte,delt,FLAG_QI,exner,rho,dz,delp,th,mr_thl0,thl, &\n"
                  "         sqv,sqc,sqi,sqs,mr_sqv0,mr_sqc0,mr_sqi0,mr_sqs0,sqv2,sqc2,sqi2,sqs2, &\n"
                  "         mr_dqv0,mr_dqc0,mr_dqi0,mr_dqs0,Dqv,Dqc,Dqi,Dqs,Dth)\n", 1)

sub = r'''
  subroutine mynnred_dump(kts,kte,delt,flag_qi,exner,rho,dz,delp,th,thl0,thl1, &
       sqv,sqc,sqi,sqs,sqv0,sqc0,sqi0,sqs0,sqv2,sqc2,sqi2,sqs2, &
       dqv0,dqc0,dqi0,dqs0,dqv,dqc,dqi,dqs,dth)
    ! mynnred: passive dump of moisture_check's inputs and outputs (red-team replay)
    integer, intent(in) :: kts,kte
    real(kind_phys), intent(in) :: delt
    logical, intent(in) :: flag_qi
    real(kind_phys), dimension(kts:kte), intent(in) :: exner,rho,dz,delp,th,thl0,thl1, &
         sqv,sqc,sqi,sqs,sqv0,sqc0,sqi0,sqs0,sqv2,sqc2,sqi2,sqs2, &
         dqv0,dqc0,dqi0,dqs0,dqv,dqc,dqi,dqs,dth
    integer, save :: rank = -1, ncall = 0, ncol = 0, nscol = 0
    integer, save :: nfc = 0, nfi = 0, nfs = 0, nfv = 0, nneg_in = 0
    real(kind=8), save :: s(8) = 0.d0
    real(kind=8) :: m, fc, fi, fs, fv, hth, ni
    character(len=32) :: buf
    character(len=64) :: fn
    integer :: k, u, st
    if (rank < 0) then
       call get_environment_variable('SLURM_PROCID', buf, status=st)
       rank = 0
       if (st == 0) read(buf,*) rank
    endif
    ncall = ncall + 1
    fc = 0.d0; fi = 0.d0; fs = 0.d0; fv = 0.d0; hth = 0.d0; ni = 0.d0
    do k = kts, kte
       m = rho(k)*dz(k)
       fc = fc + m*max(0.d0, -sqc0(k))
       fi = fi + m*max(0.d0, -sqi0(k))
       fs = fs + m*max(0.d0, -sqs0(k))
       fv = fv + m*max(0.d0, 1.d-20 - (sqv0(k) - max(0.d0,-sqc0(k)) - max(0.d0,-sqi0(k)) - max(0.d0,-sqs0(k))))
       hth = hth + m*exner(k)*(thl1(k) - thl0(k))
       ni = ni + m*(max(0.d0,-sqc(k)) + max(0.d0,-sqi(k)) + max(0.d0,-sqs(k)))
    enddo
    if (fc > 0.d0) nfc = nfc + 1
    if (fi > 0.d0) nfi = nfi + 1
    if (fs > 0.d0) nfs = nfs + 1
    if (fv > 0.d0) nfv = nfv + 1
    if (ni > 0.d0) nneg_in = nneg_in + 1
    s(1) = s(1) + fc; s(2) = s(2) + fi; s(3) = s(3) + fs; s(4) = s(4) + fv
    s(5) = s(5) + hth; s(6) = s(6) + ni
    s(7) = s(7) + sum(rho(kts:kte)*dz(kts:kte))
    s(8) = s(8) + sum(delp(kts:kte))
    if (mod(ncall,200) == 0) then
       write(fn,'(a,i4.4,a)') 'mynnred_stats_', rank, '.txt'
       open(newunit=u, file=trim(fn), status='replace', action='write')
       write(u,'(a)') 'ncall nfc nfi nfs nfv nneg_in | fill_c fill_i fill_s fill_v sum_m_exner_dthl neg_in sum_rhodz sum_delp'
       write(u,'(6i10,8es25.16e3)') ncall, nfc, nfi, nfs, nfv, nneg_in, s
       close(u)
    endif
    if ((fc + fi > 0.d0 .and. rank < 16 .and. ncol < 3) .or. (fs > 0.d0 .and. nscol < 2)) then
       if (fs > 0.d0 .and. nscol < 2) then
          nscol = nscol + 1
          write(fn,'(a,i4.4,a,i1,a)') 'mynnred_scol_', rank, '_', nscol, '.txt'
       else
          ncol = ncol + 1
          write(fn,'(a,i4.4,a,i1,a)') 'mynnred_col_', rank, '_', ncol, '.txt'
       endif
       open(newunit=u, file=trim(fn), status='replace', action='write')
       write(u,'(a,i5,es25.16e3,l2,i8,2es25.16e3)') '# kte delt flag_qi ncall xlvcp xlscp', kte, delt, flag_qi, ncall, xlvcp, xlscp
       write(u,'(a)') '# k exner rho dz delp th thl0 thl1 sqv sqc sqi sqs sqv0 sqc0 sqi0 sqs0 sqv2 sqc2 sqi2 sqs2'// &
            ' dqv0 dqc0 dqi0 dqs0 dqv dqc dqi dqs dth'
       do k = kts, kte
          write(u,'(i4,29es25.16e3)') k, exner(k),rho(k),dz(k),delp(k),th(k),thl0(k),thl1(k), &
               sqv(k),sqc(k),sqi(k),sqs(k),sqv0(k),sqc0(k),sqi0(k),sqs0(k),sqv2(k),sqc2(k),sqi2(k),sqs2(k), &
               dqv0(k),dqc0(k),dqi0(k),dqs0(k),dqv(k),dqc(k),dqi(k),dqs(k),dth(k)
       enddo
       close(u)
    endif
  end subroutine mynnred_dump

END MODULE module_bl_mynn
'''
end_anchor = "END MODULE module_bl_mynn"
assert src.count(end_anchor) == 1, "end anchor"
src = src.replace(end_anchor, sub.strip("\n").replace("END MODULE module_bl_mynn", "") + "\nEND MODULE module_bl_mynn", 1)
open(path, "w").write(src)
print("instrumented", path)
