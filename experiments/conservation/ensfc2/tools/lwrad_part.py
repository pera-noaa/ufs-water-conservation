# ================================================================== rrtmg_lw_post: radiation-time upward LW for LW1
# (RRTMGP fills surface_upwelling_longwave_flux_on_radiation_timestep; RRTMG did not)
rlp = root / "Radiation/RRTMG/rrtmg_lw_post.F90"
rlpm = root / "Radiation/RRTMG/rrtmg_lw_post.meta"
sub(rlp, "                 errmsg, errflg)\n", "                 errmsg, errflg, sfculw)\n",
    after="      subroutine rrtmg_lw_post_run (")
post(rlp, "      real(kind=kind_phys), dimension(im),         intent(inout) ::  tsflw, sfcdlw\n",
     "      real(kind=kind_phys), dimension(:), optional, intent(inout) ::  sfculw\n")
post(rlp, "        sfcdlw(:) = sfcflw(:)%dnfxc\n", "        if (present(sfculw)) sfculw(:) = sfcflw(:)%upfxc\n")
meta_append(rlpm, meta_entry("sfculw", "surface_upwelling_longwave_flux_on_radiation_timestep",
                             "total sky sfc upward lw flux", "W m-2", dims="(horizontal_loop_extent)",
                             intent="inout", optional=True))
