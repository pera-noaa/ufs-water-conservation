#!/usr/bin/env python3
"""DEBUG ONLY: per-column hashes of samfdeepcnv's inputs at entry for one step (env SM_DBG_KDT), written to
samf_dbg_<rank>.txt, to find which input differs between layouts. usage: dbg_samf.py <ufs-weather-model>"""
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF"
f = root / "samfdeepcnv.f"; m = root / "samfdeepcnv.meta"
s = f.read_text(); t = m.read_text()
def sub(x, a, b):
    assert x.count(a) == 1, a; return x.replace(a, b)
s = sub(s, "     &    pflx,samf_kirchhoff,tgrs,errmsg,errflg)\n", "     &    pflx,samf_kirchhoff,tgrs,kdtdbg,errmsg,errflg)\n")
s = sub(s, "      use funcphys , only : fpvs\n", "      use funcphys , only : fpvs\n      use mpi_f08\n")
s = sub(s, "      real(kind_phys), intent(in) :: cat_adj_deep\n",
        "      real(kind_phys), intent(in) :: cat_adj_deep\n      integer, intent(in) :: kdtdbg\n"
        "      integer(kind=8) :: hdb(24)\n      integer :: kdb, ndb, idb, rdb, udb, ierdb\n"
        "      character(len=32) :: fdb, edb\n")
A2 = ["delp", "prslp", "phil", "tkeh", "q", "q1", "t1", "u1", "v1", "dot", "cnvw", "cnvc", "tgrs", "pflx"]
A1 = ["psp", "garea", "hpbl"]
code = ["      call get_environment_variable('SM_DBG_KDT', edb, status=ierdb)",
        "      kdb = -1",
        "      if (ierdb == 0) read(edb, *) kdb",
        "      if (kdtdbg == kdb) then",
        "       call MPI_Comm_rank(MPI_COMM_WORLD, rdb, ierdb)",
        "       write(fdb, '(a,i5.5,a)') 'samf_dbg_', rdb, '.txt'",
        "       open(newunit=udb, file=trim(fdb), position='append')",
        "       do idb = 1, im",
        "        hdb = 0"]
n = 0
for a in A1:
    n += 1; code.append(f"        hdb({n}) = transfer({a}(idb), 0_8)")
for a in A2:
    n += 1; code += [f"        do kdb = 1, km", f"         hdb({n}) = hdb({n}) + transfer({a}(idb,kdb), 0_8)", "        enddo"]
n += 1; code += [f"        do ndb = 1, size(tmf,3)", "         do kdb = 1, km", f"          hdb({n}) = hdb({n}) + transfer(tmf(idb,kdb,ndb), 0_8)", "         enddo", "        enddo"]
n += 1; code += [f"        do ndb = 1, size(qtr,3)", "         do kdb = 1, km", f"          hdb({n}) = hdb({n}) + transfer(qtr(idb,kdb,ndb), 0_8)", "         enddo", "        enddo"]
n += 1; code += [f"        if (present(maxMF)) hdb({n}) = transfer(maxMF(idb), 0_8)"]
n += 1; code += [f"        if (present(ca_deep)) hdb({n}) = transfer(ca_deep(idb), 0_8)"]
n += 1; code += [f"        hdb({n}) = islimsk(idb)*1000 + kcnv(idb)"]
assert n <= 24
code += ["        write(udb, '(24z17)') hdb", "       enddo", "       close(udb)", "      endif"]
NAMES = A1 + A2 + ["tmf", "qtr", "maxMF", "ca_deep", "islimsk*1000+kcnv"]
s = sub(s, "      endif\n      \n      km1 = km - 1\n", "      endif\n" + "\n".join(code) + "\n      km1 = km - 1\n")
i_ = t.rindex("[errmsg]\n")
t = t[:i_] + ("[kdtdbg]\n  standard_name = index_of_timestep\n  long_name = current timestep index\n  units = index\n"
              "  dimensions = ()\n  type = integer\n  intent = in\n") + t[i_:]
f.write_text(s); m.write_text(t)
print("dbg_samf:", n, "hashes:", " ".join(NAMES))
