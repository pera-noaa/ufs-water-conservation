<!-- #406 top-level comment. Draft, not posted. -->
@gthompsnWRF @AndersJensen-NOAA, could one of you check the graupel commit (41d11ad6)? It's most of this PR's effect on regional precipitation (−1.0 to −4.1 %). The rain–ice and rain–snow collection gains are set before the limiters scale the losses, so graupel and snow can gain more water than rain, ice and snow lose. The fix sets the gains from the limited losses.

Two commits have another form that also conserves water, and I'm happy to switch if you prefer it:
- Density (45e71be4): mass conversions keep the entry density and fall speeds use the updated one. Alternatively, use the updated density everywhere and recompute the layer depth from it.
- Layer depth (0e22f8c2): `dz = dm/ρ` from the layer mass. Alternatively, recompute the geometric depth and derive the density from it.

I haven't run the alternatives.

TEMPO has the same graupel and density code, and `mp_tempo` takes its layer depth from `phii` as `mp_thompson` did. I've corrected #407, which said fixes had already been proposed to NCAR/TEMPO; they haven't been yet.
