"""nofma.py <ufs-weather-model> : add -no-fma to the ifort release flags (cmake/IntelMixed.cmake, used on Hercules)."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "cmake/IntelMixed.cmake"; s = p.read_text()
old = 'set(CMAKE_Fortran_FLAGS_RELEASE "${CMAKE_Fortran_FLAGS_RELEASE} -march=core-avx2")'
assert s.count(old) == 1
p.write_text(s.replace(old, 'set(CMAKE_Fortran_FLAGS_RELEASE "${CMAKE_Fortran_FLAGS_RELEASE} -march=core-avx2 -no-fma")'))
print("no-fma applied", p)
