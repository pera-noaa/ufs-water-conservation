## Description
Updates `ccpp/physics` for three SAMF/PBL conservation PRs: cloud-base double-counting (#405), four SAMF and PBL budget fixes (#408) and a deep entrainment floor (#414). No ufsatm code change. Answers change in every suite running SAMF.

### Issue(s) addressed
- ufs-community/ufs-weather-model#3404

## Testing
Intel and GNU on Hercules: full `rt.sh`, log in ufs-community/ufs-weather-model#3408. Baselines change.

## Dependencies
ufs-community/ccpp-physics#405, ufs-community/ccpp-physics#408, ufs-community/ccpp-physics#414

## AI use
AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
