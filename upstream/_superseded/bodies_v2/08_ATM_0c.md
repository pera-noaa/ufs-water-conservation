## Description
Updates `ccpp/physics` for the Thompson and TEMPO-driver fixes. No code change in ufsatm. Answers change in the Thompson and TEMPO suites.

### Issue(s) addressed
- ufs-community/ufs-weather-model#3404

## Testing
Intel and GNU on Hercules: full `rt.sh`, log in ufs-community/ufs-weather-model#TBD-WM_0c. Baselines change.

## Dependencies
ufs-community/ccpp-physics#406 (Thompson), ufs-community/ccpp-physics#407 (TEMPO driver; after ufs-community/ccpp-physics#389)

## AI use
AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
