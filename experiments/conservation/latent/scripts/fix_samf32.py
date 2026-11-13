#!/usr/bin/env python3
"""SAMF32 fix: -DSAMFCNV_32BIT=ON must reach all five SAMF files. mo_conv_kind.F90, progsigma_calc.f90 and
progomega_calc.f90 are capgen dependencies (CAPGEN_DEPENDENCIES), not scheme files (SCHEME_FORTRAN_FILES), so the
filter must search both lists; a partial match is a configure error.
usage: fix_samf32.py <ufs-weather-model tree>"""
import sys
from pathlib import Path

p = Path(sys.argv[1]) / "UFSATM/ccpp/CMakeLists.txt"
s = p.read_text()
pairs = [
    ("    set(TMP_LIST ${SCHEME_FORTRAN_FILES})\n",
     "    set(TMP_LIST ${SCHEME_FORTRAN_FILES} ${CAPGEN_DEPENDENCIES})\n"),
    ("  if(SAMF_FORTRAN_FILES)\n    if(CMAKE_Fortran_COMPILER_ID MATCHES \"Intel\")\n",
     "  if(SAMF_FORTRAN_FILES)\n"
     "    list(REMOVE_DUPLICATES SAMF_FORTRAN_FILES)\n"
     "    list(LENGTH SAMF_FORTRAN_FILES N_SAMF_FOUND)\n"
     "    list(LENGTH SAMF_NAMES N_SAMF_NAMES)\n"
     "    if(NOT N_SAMF_FOUND EQUAL N_SAMF_NAMES)\n"
     "      message(FATAL_ERROR \"SAMFCNV_32BIT: found ${N_SAMF_FOUND} of ${N_SAMF_NAMES} SAMF files: ${SAMF_FORTRAN_FILES}\")\n"
     "    endif()\n"
     "    message(STATUS \"SAMFCNV_32BIT files: ${SAMF_FORTRAN_FILES}\")\n"
     "  endif()\n"
     "\n"
     "  if(SAMF_FORTRAN_FILES)\n    if(CMAKE_Fortran_COMPILER_ID MATCHES \"Intel\")\n"),
]
for a, b in pairs:
    n = s.count(a)
    if n != 1:
        sys.exit(f"ABORT {n} x {a[:60]!r}")
    s = s.replace(a, b)
p.write_text(s)
print("patched", p)
