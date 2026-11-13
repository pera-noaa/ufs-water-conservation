<!-- #407 body edit. Draft, not applied. Replace the OLD paragraph with NEW. -->
OLD:
The fix also exposes TEMPO's own water residual (+0.33 % of grid-scale precipitation in `control_p8_ugwpv1_tempo`), which the driver error was cancelling. Fixes for that are proposed to NCAR/TEMPO separately.

NEW:
The fix also exposes TEMPO's own water residual (+0.33 % of grid-scale precipitation in `control_p8_ugwpv1_tempo`), which the driver error was cancelling. TEMPO has the graupel limiters and density update that #406 fixes in Thompson; I'll report those to NCAR/TEMPO. `mp_tempo` also takes its layer depth from `phii`, as `mp_thompson` did; that can follow here once the form in #406 is settled.
