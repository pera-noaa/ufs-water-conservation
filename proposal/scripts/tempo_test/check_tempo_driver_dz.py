#!/usr/bin/env python3
"""Gate for driver fix M4: at every inner step of mp_tempo_run, TEMPO's entry density times the dz the driver passes
must equal the host's dry-air layer mass, rho*dz = dp*(1-spechum)/g.
Usage: check_dz.py <mp_tempo.F90 (the subject)> <TEMPO build dir with libtempo.a and src/*.mod> <run dir with tables>
Takes the dz statement verbatim from the subject, places it where the subject has it (before or inside
`do it = 1, ndt`), and drives the real tempo_run over ndt = 4 inner steps of the 59-level test column, converting
species as the driver does (fix B). Exits 1 if any inner step's largest relative error exceeds 1e-12."""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

drv, build, rundir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
s = drv.read_text()
m = re.search(r"^( *)dz = \(prsi[^\n]*&\n[^\n]*\n", s, re.M)
if m is None or len(re.findall(r"^ *dz = ", s, re.M)) != 1:
    sys.exit("ABORT: expected exactly one dz assignment, from prsi")
stmt = "\n".join(line.strip() for line in m.group(0).splitlines()) + "\n"
loop = s.index("do it = 1, ndt")
inside = m.start() > loop and m.start() < s.index("enddo", loop)
print(f"{drv}: dz computed {'inside' if inside else 'before'} the inner loop")
before, within = ("", stmt) if inside else (stmt, "")

prog = f"""program check_dz
  use module_mp_tempo_params, only : roverrv, rdry, min_qv
  use module_mp_tempo_cfgs, only : ty_tempo_cfgs
  use module_mp_tempo_driver, only : tempo_init, tempo_run, ty_tempo_driver_diags
  implicit none
  integer, parameter :: kind_phys = 8, ncol = 1, nlev = 59, ndt = 4
  real(kind_phys), parameter :: con_g = 9.80665_kind_phys, dtp = 600._kind_phys
  real(kind_phys), dimension(ncol, nlev) :: prsl, spechum, qv, new_tgrs, dz, w, new_qc, new_qr, new_qi, new_qs, &
    new_qg, new_ni, new_nr, rho_tempo, mass_host
  real(kind_phys), dimension(ncol, nlev+1) :: prsi
  real(kind_phys), dimension(nlev) :: kl, qv_in, qc_in, qr_in, qi_in, qs_in, qg_in, ni_in, nr_in, nc_in, nwfa_in, &
    nifa_in, th_in, ng_in, vg_in, p_in, w_in, dz_in
  type(ty_tempo_cfgs) :: cfgs
  type(ty_tempo_driver_diags) :: diags
  real(kind_phys) :: err, worst
  integer :: k, it, io
  open(newunit=io, file='mpas_59lev_test.txt', status='old')
  read(io, *)
  do k = 1, nlev
    read(io, *) kl(k), qv_in(k), qc_in(k), qr_in(k), qi_in(k), qs_in(k), qg_in(k), ni_in(k), nr_in(k), nc_in(k), &
      nwfa_in(k), nifa_in(k), th_in(k), ng_in(k), vg_in(k), p_in(k), w_in(k), dz_in(k)
  enddo
  close(io)
  prsl(1,:) = p_in
  prsi(1,1) = p_in(1) + 0.5_kind_phys*(p_in(1) - p_in(2))
  do k = 2, nlev
    prsi(1,k) = 0.5_kind_phys*(p_in(k-1) + p_in(k))
  enddo
  prsi(1,nlev+1) = max(0._kind_phys, p_in(nlev) - 0.5_kind_phys*(p_in(nlev-1) - p_in(nlev)))
  spechum(1,:) = qv_in/(1._kind_phys + qv_in)
  new_tgrs(1,:) = th_in*(p_in/100000._kind_phys)**0.286_kind_phys
  ! as the driver (fix B): mixing ratios with the input humidity
  qv = spechum/(1._kind_phys - spechum)
  new_qc(1,:) = qc_in; new_qr(1,:) = qr_in; new_qi(1,:) = qi_in; new_qs(1,:) = qs_in; new_qg(1,:) = qg_in
  new_ni(1,:) = ni_in; new_nr(1,:) = nr_in
  w = 0._kind_phys
  mass_host = (prsi(:,1:nlev) - prsi(:,2:nlev+1))*(1._kind_phys - spechum)/con_g
  call tempo_init(tempo_cfgs=cfgs)
  worst = 0._kind_phys
{before}  do it = 1, ndt
{within}    ! TEMPO's entry density, as tempo_main computes it from the state it is given
    rho_tempo = roverrv*prsl/(rdry*new_tgrs*(max(min_qv, qv) + roverrv))
    err = maxval(abs(rho_tempo*dz - mass_host)/mass_host)
    worst = max(worst, err)
    write(*, '(a,i2,a,es10.2,a,es10.2,a,es10.2)') 'inner step ', it, ': max |rho*dz - dp(1-q)/g|/(dp(1-q)/g) =', err, &
      '   max |dT| so far =', maxval(abs(new_tgrs(1,:) - th_in*(p_in/100000._kind_phys)**0.286_kind_phys)), &
      '   max |dqv| so far =', maxval(abs(qv(1,:) - qv_in))
    call tempo_run(tempo_cfgs=cfgs, itimestep=it, dt=dtp/ndt, &
      ids=1, ide=ncol, ims=1, ime=ncol, its=1, ite=ncol, jds=1, jde=1, jms=1, jme=1, jts=1, jte=1, &
      kds=1, kde=nlev, kms=1, kme=nlev, kts=1, kte=nlev, &
      t=new_tgrs, p=prsl, w=w, dz=dz, qv=qv, qc=new_qc, qr=new_qr, qi=new_qi, qs=new_qs, qg=new_qg, &
      ni=new_ni, nr=new_nr, tempo_diags=diags)
  enddo
  if (worst > 1.e-12_kind_phys) then
    write(*, '(a,es10.2)') 'FAIL: worst relative error ', worst
    error stop 1
  endif
  write(*, '(a,es10.2)') 'PASS: worst relative error ', worst
end program check_dz
"""
work = Path(rundir) / ("check_dz_" + hashlib.md5(str(drv.resolve()).encode()).hexdigest()[:8])
work.mkdir(exist_ok=True)
(work / "check_dz.F90").write_text(prog)
fl = "-g -O0 -fcheck=all -ffree-line-length-0 -fdefault-real-8 -fdefault-double-8".split()
subprocess.run(["gfortran", *fl, f"-I{build}/src", "-o", str(work / "check_dz"), str(work / "check_dz.F90"),
                str(Path(build) / "libtempo.a")], check=True)
r = subprocess.run([str(work / "check_dz")], cwd=rundir, capture_output=True, text=True)
print("\n".join(l for l in r.stdout.splitlines() if "tempo" not in l.lower() or "inner" in l), r.stderr.strip()[-200:])
sys.exit(r.returncode)
