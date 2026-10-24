Title: MLM (`mfscuq_mlm`, #390) does not conserve water or energy

@lisa-bengtsson We checked the MLM from #390 with in-model budget meters: C96 `control_p8`, 24 h, `mlm` = .true. vs .false. in the same build (3d2331e3 with NOAA-EMC/ufsatm#1138 and ufs-community/ufs-weather-model#3355). With `mlm` on, the PBL creates 4.4e-4 kg/m² of water per day and removes 1.28 W/m² of energy. With it off, the PBL closes water to round-off. Runs with `mlm` = .false. are unaffected.

From `mfscuq_mlm.f` and `satmedmfvdifq.F` (`ufs/dev` 9b65688c):
1. The cloud-base smoothing (`mfscuq_mlm.f` L524) replaces the `k−1` tendencies of T, q and cloud water with the mean of their neighbours. This is not column-conserving: −0.88 W/m² and −6.0e-4 kg/m² per day.
2. The tendencies are `−ΔF/dz` of kinematic fluxes (L457–521), with no density, so the column sum does not telescope in mass. Also, `dz = zm(k+1) − zm(k)` is the thickness of layer `k+1`, since `satmedmfvdifq` sets `zm(k) = zi(k+1)`. A mass-weighted form, `−g·Δ(ρF)/Δp`, would close it.
3. `ntsw` and `ntinc` are passed as full tracer-array indices (`index_of_snow_mixing_ratio_in_tracer_concentration_array`), but they index `q1` and `rtg`, the vertical-diffusion arrays (`satmedmfvdifq.F` L660, L679; `mfscuq_mlm.f` L178, L472–518). The two orderings coincide in P8's Thompson configuration, not in general.

Also, with `mlm` on, single columns get a lowest layer 40–52 K colder than the layer above. This never happens with `mlm` off; we have not traced it.

Proposed fix (diff attached; compiles, not yet run in the model):
1. Smoothing: keep it, but take the change at `k−1` from `k` and `k−2` in proportion to their masses (`del`), so the column sum is unchanged.
2. Flux divergence: `−g·(ρF(k+1) − ρF(k))/del(k)`, with `ρ` at each interface (the mean of the adjacent layers') and `del` passed in from `satmedmfvdifq`. Every interface flux then leaves one layer and enters the next, and the special cases at `mlmb−1` and `mlmt+1` use the same form.
3. Indices: add `ntswx` and `ntincx` to the host's interstitial vertical-diffusion indices, set where `ntcwx` and `ntiwx` are (NOAA-EMC/ufsatm `CCPP_typedefs.F90`), and pass those to `satmedmfvdifq` in place of `ntsw` and `ntinc`.

We can run it through the same meters if useful.
