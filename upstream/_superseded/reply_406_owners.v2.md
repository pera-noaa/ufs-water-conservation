<!-- #406 top-level comment. Draft, not posted. Post after the #407 body edit. -->
@AndersJensen-NOAA, could you check the graupel commit (41d11ad6)? On its own it lowers precipitation in the most affected regional tests by 1.0–4.1 %, most of this PR's effect. The rain–ice and rain–snow collection gains are set before the limiters scale the losses, so graupel and snow can gain more water than rain, ice and snow lose. The fix sets the gains from the limited losses.

The density and layer-depth commits (45e71be4, 0e22f8c2) have another form, and I'm happy to switch if you prefer it. Water closes when density times layer depth equals the layer mass. These commits keep the entry density (the fall-speed and ventilation factors use the updated one) and set `dz = dm/ρ`, the hydrostatic depth. The alternative is to use the updated density and recompute `dz` from it each time it changes. I haven't run it.

TEMPO has the same graupel limiters and density update, and `mp_tempo` takes its layer depth from `phii` as `mp_thompson` did. I've corrected #407, which said fixes had already been proposed to NCAR/TEMPO; they haven't been yet.
