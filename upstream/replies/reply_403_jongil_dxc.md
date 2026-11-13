<!-- POSTED 12 Nov 2026: https://github.com/ufs-community/ccpp-physics/pull/403#issuecomment-6837094612 (red-teamed first). Reply on ufs-community/ccpp-physics#403 to JongilHan66's 12 Nov
     comment 6834768290 ("What are dxc(i,j) and dyc(i,j)? 1/dxc(i,j)=1/dyc(i,j)=rarea(i,j)?"), about the stencil in our
     diff3d reply.
     done = he has the definitions and where they live; no new runs.
     Sources: fv_arrays.F90 L1685-1697 (dx (isd:ied,jsd:jed+1), dy (isd:ied+1,jsd:jed), dxc, dyc bounds); fv_grid_tools
     (dxc/dyc great-circle centre distances, 2x centre-to-edge at tile edges); UFS-pinned FV3 0492f164 (ufsatm develop):
     tp_core.F90 deln_flux L1336/L1365 fx = damp2*(mass(i-1,j)+mass(i,j))*del6_v*(d2(i,j)-d2(i-1,j)); fv_grid_utils.F90
     L804 del6_v = sina_u*dy/dxc. NOT del2_cubed in dyn_core (that filters omega/heat_source, sina_u only under USE_SG).
     damp_Km (variable-K tracer del-2) is in GFDL main tp_core but not in the UFS pin, so not cited.
     Current diff3d gradient: ut = q*dy (cell-centred dy), rarea*(ut(i+1)-ut(i)), i.e. rarea*dy = 1/dx standing in for 1/dxc. -->

@JongilHan66 Not quite. `dxc(i,j)` is the distance between the centres of cells (i−1,j) and (i,j), so it sits on the west face; `dyc(i,j)` is the distance between (i,j−1) and (i,j). `dy(i,j)` and `dx(i,j)` are the lengths of those two faces, and `rarea(i,j)` is 1/(cell area). So `fx` is face-mean K × face-mean `delp` × face length × (difference in q ÷ distance between centres), and `rarea` × the net face flux is the divergence.

All four are in `gridstruct` (`gridstruct%dxc`, `gridstruct%dyc`, or `rdxc` and `rdyc` for the inverses). FV3's tracer del-2 (`deln_flux` in `tp_core.F90`) uses the same face form, `(mass(i−1,j)+mass(i,j))·del6_v·Δq` with `del6_v = sina_u·dy/dxc`; `sina_u` corrects for the non-orthogonal cube and doesn't affect conservation.

Whichever metric you use, the face-flux form conserves; what closes the leak is dividing by `del`.
