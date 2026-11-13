#!/usr/bin/env python3
"""Port the scheme-internal Thompson water fixes C1, C2, C3, M1 and M2 (ccpp-physics diffs 03, 05, 07, 13) to the WRF
(phys/module_mp_thompson.F) and MPAS (src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F) copies.
Usage: python3 port_thompson_wrf_mpas.py <module_mp_thompson.F>
B (mass basis) and M4 (layer depth) belong to the CCPP driver and do not apply here: WRF and MPAS pass dry mixing
ratios and their own dz. Each edit must match exactly where expected, else nothing is written.
  C1  cloud water settling out of the lowest layer counted as rain
  C2  graupel gains recomputed after the rate limiters (with the graupel volume, where the copy carries one)
  C3  the entry density kept for mass conversions through sedimentation (updated density for fall speeds only)
  M1  condensate the final clip would delete exchanged with vapour (with its latent heat)
  M2  all of the sedimentation flux out of the lowest layer counted as surface precipitation"""
import re
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


# locals
m = re.search(r"\n      REAL:: dtsave, odts, odt, odzq, hgt_agl(, SR)?\n", s)
if not m or len(re.findall(r"\n      REAL:: dtsave, odts, odt, odzq, hgt_agl", s)) != 1:
    sys.exit("ABORT locals: REAL:: dtsave line")
s = s[:m.end()] + "      REAL:: rhon, xcl\n" + s[m.end():]

# C3, site 1: before condensation & sedimentation
a = s.index("!..Update variables for TAU+1 before condensation & sedimention.")
blk_end = s.index("      enddo\n", a)
blk = s[a:blk_end]
for old, new in (("         rho(k) = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))\n",
                  "         ! rho stays the entry density so sedimentation conserves the host's column mass\n"
                  "         rhon = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))\n"),
                 ("         rhof(k) = SQRT(RHO_NOT/rho(k))\n", "         rhof(k) = SQRT(RHO_NOT/rhon)\n"),
                 ("         vsc2(k) = SQRT(rho(k)/visco(k))\n", "         vsc2(k) = SQRT(rhon/visco(k))\n")):
    blk = one(blk, old, new, "C3 site 1")
s = s[:a] + blk + s[blk_end:]
# C3, sites 2 and 3: after the saturation adjustment and after rain evaporation
s = one(s, "          temp(k) = t1d(k) + DT*tten(k)\n          rho(k) = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))\n"
           "          qvs(k) = rslf(pres(k), temp(k))\n",
        "          temp(k) = t1d(k) + DT*tten(k)\n          qvs(k) = rslf(pres(k), temp(k))\n", "C3 site 2")
s = one(s, "          nr(k) = MAX(R2, (nr1d(k) + DT*nrten(k))*rho(k))\n          temp(k) = t1d(k) + DT*tten(k)\n"
           "          rho(k) = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))\n",
        "          nr(k) = MAX(R2, (nr1d(k) + DT*nrten(k))*rho(k))\n          temp(k) = t1d(k) + DT*tten(k)\n",
        "C3 site 3")

# C2: recompute the graupel gains in the re-closure block, under the condition that created prg_rcs
cond = "twet" if "           if (twet(k).lt.T_0) then\n            prr_rcs(k) = -(tmr_racs2" in s else "temp"
if f"           if ({cond}(k).lt.T_0) then\n            prr_rcs(k) = -(tmr_racs2" not in s:
    sys.exit("ABORT C2: cannot find the prg_rcs creation condition")
hail = "pbg_rci(k) = prg_rci(k)/rho_i" in s
c2 = ("         ! graupel gains must match the (possibly limited) losses that feed them\n"
      "         prg_rci(k) = pri_rci(k) + prr_rci(k)\n"
      f"         if ({cond}(k).lt.T_0) prg_rcs(k) = -(prr_rcs(k) + prs_rcs(k))\n")
if hail:
    c2 += "         pbg_rci(k) = prg_rci(k)/rho_i\n         pbg_rcs(k) = prg_rcs(k)/rho_i\n"
s = one(s, "         prr_rcg(k) = ratio * SIGN(1.0, SNGL(prr_rcg(k)))\n         prg_rcg(k) = -prr_rcg(k)\n",
        "         prr_rcg(k) = ratio * SIGN(1.0, SNGL(prr_rcg(k)))\n         prg_rcg(k) = -prr_rcg(k)\n" + c2, "C2")

# C1: cloud water settling out of the lowest layer
s = one(s, "         rc(k) = MAX(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*DT)\n"
           "         nc(k) = MAX(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*DT)\n      enddo\n",
        "         rc(k) = MAX(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*DT)\n"
        "         nc(k) = MAX(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*DT)\n      enddo\n"
        "      ! cloud water settling out of the lowest layer reaches the surface: count it as precipitation\n"
        "      if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*DT\n", "C1")

# M2: the four surface thresholds
pat = re.compile(r"\n( *)if \(r([risg])\(kts\)\.gt\.R1\*1000\.\) &\n *(ppt\w+ = ppt\w+ \+ sed_\2\(kts\)\*DT\*onstep\(\d\))\n")
if len(pat.findall(s)) != 4:
    sys.exit(f"ABORT M2: expected 4 threshold sites, found {len(pat.findall(s))}")
s = pat.sub(lambda m: f"\n{m.group(1)}! all of the flux out of the lowest layer reaches the surface\n{m.group(1)}{m.group(3)}\n", s)

# M1: before the final apply
hdr = "!.. All tendencies computed, apply and pass back final values to parent.\n!+---+-----------------------------------------------------------------+\n"
m1 = "      ! condensate the final clip would delete is exchanged with vapour (with its latent heat) instead\n      do k = kts, kte\n"
for q, lat in (("qc", "lvap(k)"), ("qi", "lsub"), ("qr", "lvap(k)"), ("qs", "lsub"), ("qg", "lsub")):
    m1 += (f"         xcl = {q}1d(k) + {q}ten(k)*DT\n"
           f"         if (xcl .le. R1) then\n"
           f"            {q}ten(k) = {q}ten(k) - xcl*odt\n"
           f"            qvten(k) = qvten(k) + xcl*odt\n"
           f"            tten(k) = tten(k) - {lat}*ocp(k)*xcl*odt*(1-IFDRY)\n"
           f"         endif\n")
m1 += "      enddo\n"
s = one(s, hdr, hdr + m1, "M1")

f.write_text(s)
print(f"patched {f.name}: C1, C2 ({cond}{', with graupel volume' if hail else ''}), C3 (3 sites), M1, M2 (4 sites)")
