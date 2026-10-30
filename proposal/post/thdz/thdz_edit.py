"""thdz_edit.py MODE module_mp_thompson.F90: Thompson density/layer-depth variants on the full10 base.
MODE bad: the density fix reverted (rho recomputed at the three updates, as on develop); dz unchanged.
MODE alt: bad + dz = dm/rho after each density update, and the stored densities rescaled to the new rho."""
import re
import sys

mode, p = sys.argv[1], sys.argv[2]
assert mode in ("bad", "alt")
s = open(p).read()
i0 = s.index("   subroutine mp_thompson (")
i1 = s.index("   end subroutine mp_thompson\n", i0)
head, body, tail = s[:i0], s[i0:i1], s[i1:]


def rep(a, b):
    global body
    assert body.count(a) == 1, (body.count(a), a[:70])
    body = body.replace(a, b)


# site 1: update for TAU+1 before condensation and sedimentation
rep("""         ! rho stays the entry density so sedimentation conserves the host's column mass
         rhon = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))
         rhof(k) = SQRT(RHO_NOT/rhon)
""", """         rho(k) = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))
""" + ("         dzl(k) = dml(k)/rho(k)\n" if mode == "alt" else "") + """         rhof(k) = SQRT(RHO_NOT/rho(k))
""")
rep("         vsc2(k) = SQRT(rhon/visco(k))\n", "         vsc2(k) = SQRT(rho(k)/visco(k))\n")

RESCALE = """            fr = rho(k)/rhoo
            if (rc(k).gt.R1) rc(k) = rc(k)*fr
            if (ri(k).gt.R1) ri(k) = ri(k)*fr
            if (rr(k).gt.R1) rr(k) = rr(k)*fr
            if (rs(k).gt.R1) rs(k) = rs(k)*fr
            if (rg(k).gt.R1) rg(k) = rg(k)*fr
            if (is_aerosol_aware .or. merra2_aerosol_aware) nc(k) = max(2., min(nc(k)*fr, Nt_c_max))
            ni(k) = max(R2, ni(k)*fr)
            nr(k) = max(R2, nr(k)*fr)
            nwfa(k) = nwfa(k)*fr
            nifa(k) = nifa(k)*fr
            dzl(k) = dml(k)/rho(k)
"""
NEWRHO = "            rho(k) = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))\n"

# site 2: after condensation/evaporation of cloud water
a2 = """            qv(k) = max(1.E-10, qv1d(k) + DT*qvten(k))
            temp(k) = t1d(k) + DT*tten(k)
            qvs(k) = rslf(pres(k), temp(k))
            ssatw(k) = qv(k)/qvs(k) - 1.
         endif
      enddo
"""
rep(a2, a2.replace("            temp(k) = t1d(k) + DT*tten(k)\n",
                   "            temp(k) = t1d(k) + DT*tten(k)\n"
                   + ("            rhoo = rho(k)\n" if mode == "alt" else "")
                   + NEWRHO + (RESCALE if mode == "alt" else "")))

# site 3: after rain evaporation
a3 = """            nr(k) = max(R2, (nr1d(k) + DT*nrten(k))*rho(k))
            temp(k) = t1d(k) + DT*tten(k)
         endif
      enddo
"""
rep(a3, a3.replace("            temp(k) = t1d(k) + DT*tten(k)\n",
                   "            temp(k) = t1d(k) + DT*tten(k)\n"
                   + ("            rhoo = rho(k)\n" if mode == "alt" else "")
                   + NEWRHO + (RESCALE if mode == "alt" else "")))

if mode == "alt":
    rep("      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
        "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon, rhoo, fr\n"
        "      real(wp), dimension(kts:kte) :: dml, dzl\n")
    # entry: layer mass from the entry density and the host's depth
    rep("""         rho(k) = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))
         nwfa(k) = max(11.1E6*rho(k), min(9999.E6*rho(k), nwfa1d(k)*rho(k)))
""", """         rho(k) = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))
         dml(k) = rho(k)*dzq(k)
         dzl(k) = dzq(k)
         nwfa(k) = max(11.1E6*rho(k), min(9999.E6*rho(k), nwfa1d(k)*rho(k)))
""")
    # sedimentation uses the current depth
    k = body.index("         dzl(k) = dzq(k)\n") + len("         dzl(k) = dzq(k)\n")
    pre, post = body[:k], body[k:]
    n = len(re.findall(r"\bdzq\b", post))
    post = re.sub(r"\bdzq\b", "dzl", post)
    body = pre + post
    print(f"dzq -> dzl after entry: {n}")

open(p, "w").write(head + body + tail)
print(f"thdz_edit {mode}: ok")
