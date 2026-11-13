from spack.spec import Spec
for s in ["fms %fortran=gcc@13.3.0", "fms %fortran=gcc@11.4.0", "fms %fortran=oneapi@2025.3.1",
          "fms %c=gcc@13.3.0 %fortran=oneapi@2025.3.1", "fms %gcc@13.3.0"]:
    print(s, "->", Spec(s).satisfies("%fortran=gcc@12:"))
