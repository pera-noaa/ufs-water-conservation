# sourced: run-arm namelist edits (input.nml sed -E) and exes
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/upchk
X403P=$C/exe/p403.exe; X403M=$C/exe/m403.exe; X390P=$C/exe/p390.exe; X390M=$C/exe/m390.exe
S_3D='s/^(&gfs_physics_nml.*)$/\1\n  sa3dtke = .true./; s/^(&fv_core_nml.*)$/\1\n  sa3dtke_dyco = .true./'
S_ALL='s/^(&gfs_physics_nml.*)$/\1\n  sa3dtke = .true.\n  leonard = .true.\n  coldpool = .true./; s/^(&fv_core_nml.*)$/\1\n  sa3dtke_dyco = .true.\n  leonard_dyco = .true.\n  coldpool_dyco = .true./'
S_MLM='s/^(&gfs_physics_nml.*)$/\1\n  mlm = .true./'
S_C999='s/^(\s*consv_te\s*=).*/\1 0.999/'
FT_ALL=$C/field_table_buoyexcs
