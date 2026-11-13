<!-- #406 top-level comment. Draft, not posted. -->
@AndersJensen-NOAA, could you check the graupel commit (41d11ad6)? It's most of this PR's effect: alone, it lowers precipitation in the most affected regional tests by 1.0–4.1 %. Rain–ice and rain–snow collection gains were set before the limiters scaled the losses, so graupel and snow could gain more water than rain, ice and snow lost; now the gains follow the limited losses.

The density and layer-depth commits (45e71be4, 0e22f8c2) have another form; happy to switch. Water closes when density times layer depth equals the layer mass. These commits keep the entry density (except in fall speeds and ventilation) and set `dz = dm/ρ`; the alternative uses the updated density, recomputes `dz` from it and rescales the stored densities at each update. With our other Thompson fixes, both close water to round-off in our meters. In the regional tests they differ by up to 0.36 % of precipitation (0.65 % in `cpld_regional_atm_fbh`), against one-bit noise of up to 0.24 %.

TEMPO has the same graupel limiters, density update and layer depth. I've corrected #407, which said TEMPO fixes were already proposed.
