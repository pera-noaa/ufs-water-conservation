@climbfuji The direction is unchanged, only the form: with `qv` from the input `spechum`, `1 + qv = 1/(1 − spechum)`, so dividing by `1 + qv` equals multiplying by `1 − spechum`, which undoes the conversion before `mp_gt_driver`.

The input humidity is the right one because FV3 rebuilds each tracer's mass as the pre-physics layer mass (dry air + vapour, from `Statein%prsi`) times the value physics returns, then recomputes `delp` from the new water ([atmosphere.F90 L1659–1677](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/blob/71ff473b9f4254ee4e436ff4df41be09c6e78dc6/driver/UFS/atmosphere.F90#L1659-L1677)). Dividing by `1 + qv` with the post-microphysics `qv` scales every species by `(1 + qv_in)/(1 + qv_out)`, creating water where Thompson condenses vapour and removing it where it evaporates: the −0.4 % in the description.

@RuiyuSun, with `qv` as the original mixing ratio, `/(1 + qv)` is exactly this line.
