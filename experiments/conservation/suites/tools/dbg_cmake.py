"""DEBUG ONLY: compile samfdeepcnv.f with extra ifort options. usage: dbg_cmake.py <ufs-weather-model> "<opt;opt;...>" """
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/CMakeLists.txt"; s = p.read_text()
a = "#------------------------------------------------------------------------------\n# For CAPS, remove bounds checks"
assert s.count(a) == 1
s = s.replace(a, ('set(DBG_SAMF ${SCHEME_FORTRAN_FILES})\nlist(FILTER DBG_SAMF INCLUDE REGEX ".*samfdeepcnv.f$")\n'
                  f'message(STATUS "DBG_SAMF: ${{DBG_SAMF}}")\nset_property(SOURCE ${{DBG_SAMF}} APPEND PROPERTY COMPILE_OPTIONS "{sys.argv[2]}")\n') + a)
p.write_text(s); print("dbg flags", sys.argv[2])
