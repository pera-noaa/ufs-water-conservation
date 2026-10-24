#!/usr/bin/env python3
"""upchk meters (diagnostic builds only; run AFTER energy/meters/tools/instrument_eb_phys2.py, which adds em_p01..12).
Usage: instrument_upchk.py <ufs-weather-model> <mode>[,<mode>...]   modes: tm (always), hd (#403), mlm (#390)
 tm : uc_t01..05 after em_p04, em_p05, em_p07, em_p08, em_p09 store per column, per tracer, sum m*(gq0 + dtp*dqdt);
      uc_fin (after em_p12) prints  'UCT kdt n M dPBL dMID dDCNV dSCNV'  (kg, global; M at probe 1)
 hd : uc_hd after GFS_PBL_generic_pre: horizontal diffusion terms as satmedmfvdifq applies them (f += def*dt2):
      'UCH kdt n Smass Sarea Gmass Garea M'  n = 0 (T; cp-weighted, J) or vdiff index (kg); Smass = sum a m def dtp,
      Sarea = sum a def (telescoping check), G* = gross (|def|), M = sum a m x
 mlm: hooks in satmedmfvdifq (around the mfscuq_mlm call) and mfscuq_mlm (cloud-base smoothing):
      'UCM kdt v(1:16)' global sums of the column integrals of the MLM tendencies (see MLMV below)."""
import re
import sys
from pathlib import Path

wm = Path(sys.argv[1])
modes = set(sys.argv[2].split(",")) | {"tm"}
root = wm / "UFSATM/ccpp"
phys = root / "physics/physics"
idir = phys / "Interstitials/UFS_SCM_NEPTUNE"
suite = root / "suites/suite_FV3_GFS_v17_p8_ugwpv1.xml"
cfg = root / "config/ccpp_prebuild_config_fv3.py"
cm = root / "CMakeLists.txt"
metas = sorted(phys.rglob("*.meta")) + sorted((root / "data").glob("*.meta"))
if "em_p01" not in suite.read_text():
    sys.exit("ABORT: run instrument_eb_phys2.py first")


def block(std):
    for m in metas:
        txt = m.read_text(errors="ignore")
        for b in re.split(r"\n(?=\[)", txt):
            if re.search(r"^\s*standard_name\s*=\s*" + re.escape(std) + r"\s*$", b, re.M) and b.startswith("[") \
                    and "ccpp-" not in b.splitlines()[0]:
                return [l for l in b.strip().splitlines() if not l.strip().startswith("intent")
                        and not l.strip().startswith("optional")]
    sys.exit(f"ABORT: no metadata block for {std}")


COMMON_F90 = r"""!> \file upchk_meter_common.F90
!! upchk meters: tracer mass per segment, horizontal-diffusion sums, MLM column sums (diagnostic builds only).
module upchk_meter_common
  use machine, only: kind_phys
  implicit none
  public
  integer, parameter :: ucnp = 5, ucnt = 40, ucnc = 8192, ucnv = 16
  real(kind=8), save :: ucc(ucnt, ucnp, ucnc) = 0.d0, uct(6, ucnt) = 0.d0
  integer, save :: ucoff(ucnp) = 0, uckdt(ucnp) = -1, ucfoff = 0, ucfkdt = -1, ucnt_used = 0
  real(kind=8), save :: uch(6, 0:ucnt) = 0.d0, uchp(6, 0:ucnt) = 0.d0
  integer, save :: uchkdt = -1, uchn = 0
  real(kind=8), save :: ucb(ucnv, ucnc) = 0.d0, ucm(ucnv) = 0.d0
  real(kind=8), allocatable, save :: ucr0(:,:,:)
  integer, save :: ucsk(ucnc) = 0
  real(kind=8), save :: ucsd(3, ucnc) = 0.d0
contains
  subroutine uc_tm(p, im, levs, kdt, ntrac, dtp, gq0, dqdt, prsi, con_g)
    integer, intent(in) :: p, im, levs, kdt, ntrac
    real(kind=kind_phys), intent(in) :: dtp, con_g, gq0(:,:,:), dqdt(:,:,:), prsi(:,:)
    integer :: i, k, n, j0
    real(kind=8) :: m
    if (kdt /= uckdt(p)) then
       uckdt(p) = kdt
       ucoff(p) = 0
    endif
    j0 = ucoff(p)
    ucnt_used = min(ntrac, ucnt)
    do i = 1, im
       ucc(:, p, j0+i) = 0.d0
       do n = 1, ucnt_used
          do k = 1, levs
             m = (prsi(i,k) - prsi(i,k+1))/con_g
             ucc(n, p, j0+i) = ucc(n, p, j0+i) + m*(gq0(i,k,n) + dtp*dqdt(i,k,n))
          enddo
       enddo
    enddo
    ucoff(p) = j0 + im
  end subroutine uc_tm

  ! MLM hooks (satmedmfvdifq / mfscuq_mlm)
  subroutine uc_mlm_pre(im, km, rtg, ntcw, ntiw, ntsw)
    integer, intent(in) :: im, km, ntcw, ntiw, ntsw
    real(kind=kind_phys), intent(in) :: rtg(:,:,:)
    if (allocated(ucr0)) then
       if (size(ucr0, 1) < im .or. size(ucr0, 2) < km) deallocate(ucr0)
    endif
    if (.not. allocated(ucr0)) allocate(ucr0(im, km, 4))
    ucr0(1:im, 1:km, 1) = rtg(1:im, 1:km, 1)
    ucr0(1:im, 1:km, 2) = rtg(1:im, 1:km, ntcw)
    ucr0(1:im, 1:km, 3) = rtg(1:im, 1:km, ntiw)
    ucr0(1:im, 1:km, 4) = 0.d0
    if (ntsw > 0) ucr0(1:im, 1:km, 4) = rtg(1:im, 1:km, ntsw)
    ucsk(1:im) = 0
    ucsd(:, 1:im) = 0.d0
  end subroutine uc_mlm_pre

  subroutine uc_sm(i, k, t, qv, qc, stage)
    ! cloud-base smoothing in mfscuq_mlm: stage 0 before, 1 after (records new - old at layer k)
    integer, intent(in) :: i, k, stage
    real(kind=kind_phys), intent(in) :: t, qv, qc
    if (stage == 0) then
       ucsk(i) = k
       ucsd(:, i) = (/ -real(t, 8), -real(qv, 8), -real(qc, 8) /)
    else
       ucsd(:, i) = ucsd(:, i) + (/ real(t, 8), real(qv, 8), real(qc, 8) /)
    endif
  end subroutine uc_sm

  subroutine uc_mlm_post(im, km, del, zm, tdt, du, dv, u1, v1, rtg, ntcw, ntiw, ntsw, grav, cp, hvap, hfus)
    ! per-column integrals of the MLM tendencies (rates); v = see MLMV in instrument_upchk.py
    integer, intent(in) :: im, km, ntcw, ntiw, ntsw
    real(kind=kind_phys), intent(in) :: del(:,:), zm(:,:), tdt(:,:), du(:,:), dv(:,:), u1(:,:), v1(:,:), rtg(:,:,:)
    real(kind=kind_phys), intent(in) :: grav, cp, hvap, hfus
    integer :: i, k
    real(kind=8) :: m, dz, e, w, qs, x(ucnv)
    do i = 1, im
       x = 0.d0
       do k = 1, km - 1
          m = del(i,k)/grav
          dz = zm(i,k+1) - zm(i,k)
          qs = 0.d0
          if (ntsw > 0) qs = rtg(i,k,ntsw) - ucr0(i,k,4)
          e = cp*tdt(i,k) + hvap*(rtg(i,k,1) - ucr0(i,k,1)) - hfus*(rtg(i,k,ntiw) - ucr0(i,k,3) + qs)
          w = (rtg(i,k,1) - ucr0(i,k,1)) + (rtg(i,k,ntcw) - ucr0(i,k,2)) + (rtg(i,k,ntiw) - ucr0(i,k,3)) + qs
          x(1) = x(1) + m*e
          x(2) = x(2) + m*w
          x(3) = x(3) + m*abs(e)
          x(4) = x(4) + m*(abs(rtg(i,k,1) - ucr0(i,k,1)) + abs(rtg(i,k,ntcw) - ucr0(i,k,2)) &
               + abs(rtg(i,k,ntiw) - ucr0(i,k,3)) + abs(qs))
          x(5) = x(5) + dz*e
          x(6) = x(6) + dz*w
          x(11) = x(11) + m*du(i,k)
          x(12) = x(12) + m*dv(i,k)
          x(13) = x(13) + m*(u1(i,k)*du(i,k) + v1(i,k)*dv(i,k))
          x(15) = x(15) + dz*abs(e)
          if (k == ucsk(i)) then
             x(7) = m*(cp*ucsd(1,i) + hvap*ucsd(2,i))
             x(8) = m*(ucsd(2,i) + ucsd(3,i))
             x(9) = dz*(cp*ucsd(1,i) + hvap*ucsd(2,i))
             x(10) = dz*(ucsd(2,i) + ucsd(3,i))
          endif
       enddo
       if (x(3) > 0.d0) x(14) = 1.d0
       x(16) = real(ucsk(i), 8)
       ucb(:, i) = x
    enddo
  end subroutine uc_mlm_post
end module upchk_meter_common
"""


def decl(n, std):
    b = block(std)
    t = [l.split("=", 1)[1].strip() for l in b if l.strip().startswith("type")][0]
    dims = [l.split("=", 1)[1].strip() for l in b if l.strip().startswith("dimensions")][0]
    nd = dims.count(",") + 1 if dims != "()" else 0
    kind = [l.split("=", 1)[1].strip() for l in b if l.strip().startswith("kind")]
    if t == "real":
        ty = f"real(kind={kind[0]})"
    elif t == "integer":
        ty = "integer"
    elif t == "logical":
        ty = "logical"
    elif t == "character":
        ty = "character(len=*)"
    elif t == "MPI_Comm":
        ty = "type(MPI_Comm)"
    else:
        sys.exit(f"ABORT type {t}")
    shape = "(" + ",".join([":"] * nd) + ")" if nd else ""
    intent = "out" if n in ("errmsg", "errflg") else "in"
    return f"    {ty}, intent({intent}) :: {n}{shape}"


TAIL = [("errmsg", "ccpp_error_message"), ("errflg", "ccpp_error_code")]
TM = [("im", "horizontal_loop_extent"), ("levs", "vertical_layer_dimension"), ("kdt", "index_of_timestep"),
      ("ntrac", "number_of_tracers"), ("dtp", "timestep_for_physics"), ("gq0", "tracer_concentration"),
      ("dqdt", "process_split_cumulative_tendency_of_tracers"), ("prsi", "air_pressure_at_interface"),
      ("con_g", "gravitational_acceleration")]
FIN = TM + [("garea", "cell_area"), ("mpicomm", "mpi_communicator"), ("mpirank", "mpi_rank"),
            ("mpiroot", "mpi_root")]
HD = [("im", "horizontal_loop_extent"), ("levs", "vertical_layer_dimension"), ("kdt", "index_of_timestep"),
      ("nvdiff", "number_of_vertical_diffusion_tracers"), ("dtp", "timestep_for_physics"),
      ("def4q", "horizontal_turbulent_eddy_diffusion_for_vertically_diffused_tracers"),
      ("def_3", "horizontal_turbulent_eddy_diffusion_for_temperature"),
      ("vdftra", "vertically_diffused_tracer_concentration"), ("tgrs", "air_temperature"),
      ("prsi", "air_pressure_at_interface"), ("garea", "cell_area"), ("con_g", "gravitational_acceleration"),
      ("con_cp", "specific_heat_of_dry_air_at_constant_pressure")]

TM_BODY = "    call uc_tm({p}, im, levs, kdt, ntrac, dtp, gq0, dqdt, prsi, con_g)\n"
HD_BODY = r"""    integer :: i, k, n
    real(kind=8) :: m, a, x
    if (kdt /= uchkdt) then
       uchp = uch
       uch = 0.d0
       uchkdt = kdt
    endif
    uchn = min(nvdiff, ucnt)
    do i = 1, im
       a = garea(i)
       do k = 1, levs
          m = (prsi(i,k) - prsi(i,k+1))/con_g
          x = con_cp*def_3(i,k)
          uch(1, 0) = uch(1, 0) + a*m*x*dtp
          uch(2, 0) = uch(2, 0) + a*def_3(i,k)
          uch(3, 0) = uch(3, 0) + a*m*abs(x)*dtp
          uch(4, 0) = uch(4, 0) + a*abs(def_3(i,k))
          uch(5, 0) = uch(5, 0) + a*m*con_cp*tgrs(i,k)
          do n = 1, uchn
             x = def4q(i,k,n)
             uch(1, n) = uch(1, n) + a*m*x*dtp
             uch(2, n) = uch(2, n) + a*x
             uch(3, n) = uch(3, n) + a*m*abs(x)*dtp
             uch(4, n) = uch(4, n) + a*abs(x)
             uch(5, n) = uch(5, n) + a*m*vdftra(i,k,n)
          enddo
       enddo
    enddo
"""
FIN_BODY = r"""    integer :: i, n, j0, ierr, nb
    real(kind=8) :: a
    real(kind=8), allocatable :: buf(:), rbuf(:)
    if (kdt /= ucfkdt .and. ucfkdt >= 0) then
       nb = 6*ucnt + 6*(ucnt+1) + ucnv
       allocate(buf(nb), rbuf(nb))
       buf(1:6*ucnt) = reshape(uct, (/6*ucnt/))
       buf(6*ucnt+1:6*ucnt+6*(ucnt+1)) = reshape(uchp, (/6*(ucnt+1)/))
       buf(nb-ucnv+1:nb) = ucm
       if (mpirank == mpiroot) then
          call MPI_Reduce(MPI_IN_PLACE, buf, nb, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)
          do n = 1, ucnt_used
             write(*,'(a,i6,i3,5es25.16)') 'UCT ', ucfkdt, n, buf(6*(n-1)+1:6*(n-1)+5)
          enddo
          if (uchn > 0) then
             do n = 0, uchn
                write(*,'(a,i6,i3,5es25.16)') 'UCH ', ucfkdt, n, buf(6*ucnt+6*n+1:6*ucnt+6*n+5)
             enddo
          endif
          write(*,'(a,i6,16es25.16)') 'UCM ', ucfkdt, buf(nb-ucnv+1:nb)
       else
          call MPI_Reduce(buf, rbuf, nb, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)
       endif
       deallocate(buf, rbuf)
       uct = 0.d0
       ucm = 0.d0
    endif
    if (kdt /= ucfkdt) then
       ucfkdt = kdt
       ucfoff = 0
    endif
    j0 = ucfoff
    do i = 1, im
       a = garea(i)
       do n = 1, ucnt_used
          uct(1, n) = uct(1, n) + a*ucc(n, 1, j0+i)
          uct(2, n) = uct(2, n) + a*(ucc(n, 2, j0+i) - ucc(n, 1, j0+i))
          uct(3, n) = uct(3, n) + a*(ucc(n, 3, j0+i) - ucc(n, 2, j0+i))
          uct(4, n) = uct(4, n) + a*(ucc(n, 4, j0+i) - ucc(n, 3, j0+i))
          uct(5, n) = uct(5, n) + a*(ucc(n, 5, j0+i) - ucc(n, 4, j0+i))
       enddo
       ucm = ucm + a*ucb(:, i)
       ucb(:, i) = 0.d0
    enddo
    ucfoff = j0 + im
"""


def scheme(nm, args, body, final=False):
    uses = "  use machine, only: kind_phys\n  use upchk_meter_common\n" + ("  use mpi_f08\n" if final else "")
    names = [n for n, _ in args + TAIL]
    decls = "\n".join(decl(n, s) for n, s in args + TAIL)
    al, cur = [], ""
    for n in names:
        if len(cur) + len(n) > 80:
            al.append(cur)
            cur = ""
        cur += n + ", "
    al.append(cur.rstrip(", "))
    f90 = (f"!> \\file {nm}.F90\n!! upchk meter probe (diagnostic builds only).\nmodule {nm}\n{uses}  implicit none\n"
           f"contains\n!> \\section arg_table_{nm}_run Argument Table\n!! \\htmlinclude {nm}_run.html\n!!\n"
           f"  subroutine {nm}_run({' &'.join(chr(10) + '       ' + a if i else a for i, a in enumerate(al))})\n"
           f"{decls}\n{body}\n    errmsg = ''\n    errflg = 0\n  end subroutine {nm}_run\nend module {nm}\n")
    meta = [f"[ccpp-table-properties]\n  name = {nm}\n  type = scheme\n"
            f"  dependencies = ../../hooks/machine.F,upchk_meter_common.F90\n",
            f"[ccpp-arg-table]\n  name = {nm}_run\n  type = scheme"]
    for n, std in args + TAIL:
        b = block(std)
        b[0] = f"[{n}]"
        meta.append("\n".join(b) + f"\n  intent = {'out' if n in ('errmsg', 'errflg') else 'in'}")
    (idir / f"{nm}.F90").write_text(f90)
    (idir / f"{nm}.meta").write_text("\n".join(meta) + "\n")
    return nm


(idir / "upchk_meter_common.F90").write_text(COMMON_F90)
probes = {}  # name -> scheme it follows
for p, em in enumerate((4, 5, 7, 8, 9), start=1):
    probes[scheme(f"uc_t{p:02d}", TM, TM_BODY.format(p=p))] = f"em_p{em:02d}"
if "hd" in modes:
    probes[scheme("uc_hd", HD, HD_BODY)] = "GFS_PBL_generic_pre"
probes[scheme("uc_fin", FIN, FIN_BODY, final=True)] = "em_p12"

s = suite.read_text()
for nm, after in probes.items():
    old = f"<scheme>{after}</scheme>"
    assert s.count(old) == 1, old
    s = s.replace(old, old + f"\n      <scheme>{nm}</scheme>")
suite.write_text(s)
if cfg.exists():
    c = cfg.read_text()
    old = "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90',\n"
    assert c.count(old) == 1
    c = c.replace(old, old + "".join(f"    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/{n}.F90',\n" for n in probes))
    cfg.write_text(c)
c = cm.read_text()
old = '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.meta"\n'
assert c.count(old) == 1
c = c.replace(old, old + "".join(f'  "${{SCHEME_FILES_DIR}}/Interstitials/UFS_SCM_NEPTUNE/{n}.meta"\n' for n in probes))
cm.write_text(c)

if "mlm" in modes:
    sat = phys / "PBL/SATMEDMF/satmedmfvdifq.F"
    t = sat.read_text()
    old = "      use mfscuq_mlm_mod, only : mfscuq_mlm\n"
    assert t.count(old) == 1
    t = t.replace(old, old + "      use upchk_meter_common, only : uc_mlm_pre, uc_mlm_post\n")
    old = "         call mfscuq_mlm(im,im,km,ntcw,ntsw,ntiw,ntinc,\n"
    assert t.count(old) == 1
    t = t.replace(old, "         call uc_mlm_pre(im, km, rtg, ntcw, ntiw, ntsw)\n" + old)
    old = ("     &        uflux,vflux,tdt,du,dv,rtg,\n"
           "     &        eflux,rflux,wflux,pflux)\n")
    assert t.count(old) == 1
    t = t.replace(old, old + "         call uc_mlm_post(im, km, del, zm, tdt, du, dv, u1, v1, rtg,\n"
                             "     &        ntcw, ntiw, ntsw, grav, cp, hvap, hfus)\n")
    sat.write_text(t)
    mlm = phys / "PBL/SATMEDMF/mfscuq_mlm.f"
    t = mlm.read_text()
    old = "      use machine,  only : kind_phys\n"
    assert t.count(old) == 1
    t = t.replace(old, old + "      use upchk_meter_common, only : uc_sm\n")
    old = ("               tdt(i,k-1)      =  0.5*(tdt(i,k) + tdt(i,k-2))\n"
           "               rtg(i,k-1,1)    =  0.5*(rtg(i,k,1) + rtg(i,k-2,1))\n"
           "               rtg(i,k-1,ntcw) =  0.5*(rtg(i,k,ntcw) + rtg(i,k-2,ntcw))\n")
    assert t.count(old) == 1
    t = t.replace(old, "               call uc_sm(i, k-1, tdt(i,k-1), rtg(i,k-1,1),\n"
                       "     &              rtg(i,k-1,ntcw), 0)\n" + old +
                       "               call uc_sm(i, k-1, tdt(i,k-1), rtg(i,k-1,1),\n"
                       "     &              rtg(i,k-1,ntcw), 1)\n")
    mlm.write_text(t)
    # build order: the common module before mfscuq_mlm.f and satmedmfvdifq.F
    sm = phys / "PBL/SATMEDMF/satmedmfvdifq.meta"
    t = sm.read_text()
    m = re.search(r"^(\s*dependencies\s*=\s*)(.*)$", t, re.M)
    assert m and "mfscuq_mlm" in m.group(2), "satmedmfvdifq.meta dependencies"
    t = t[:m.start(2)] + "../../Interstitials/UFS_SCM_NEPTUNE/upchk_meter_common.F90," + t[m.start(2):]
    sm.write_text(t)
print("upchk probes:", " ".join(probes), "modes:", ",".join(sorted(modes)))
