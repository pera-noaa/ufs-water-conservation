#!/bin/bash
# PR metadata for both stacks (read-only)
while read repo n; do
  gh pr view "$n" -R "$repo" --json title,state,headRefOid,headRepository,headRepositoryOwner,headRefName,baseRefName,updatedAt,changedFiles \
    -q '"\(.title) | \(.state) | \(.headRepositoryOwner.login)/\(.headRepository.name):\(.headRefName) @ \(.headRefOid) -> \(.baseRefName) | files \(.changedFiles) | \(.updatedAt)"' | sed "s|^|$repo#$n: |"
done <<L
ufs-community/ccpp-physics 403
ufs-community/ccpp-physics 390
ufs-community/ufs-weather-model 3402
ufs-community/ufs-weather-model 3355
NOAA-EMC/ufsatm 1154
NOAA-EMC/ufsatm 1138
NOAA-GFDL/GFDL_atmos_cubed_sphere 429
L
