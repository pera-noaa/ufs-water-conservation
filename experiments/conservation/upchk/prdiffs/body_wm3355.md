<!-- INSTRUCTIONS: 
- READ/FOLLOW THE DIRECTIONS IN EACH SECTION
- Complete the 'Commit Queue Requirements' below
- Use GitHub markup as much as possible (https://docs.github.com/en/get-started/writing-on-github)
- Leave your PR in a draft state until all underlying work is completed.
-->

## Commit Queue Requirements:
<!--
- Check off completed items. Use [X] for a filled in checkbox or leave it [ ] for an empty checkbox
- Your pull request (PR) will not be considered until all requirements are met.
- THIS IS YOUR RESPONSIBILITY
 -->
- [x] This PR addresses a relevant WM issue (if not, create an issue). 
- [x] All subcomponent pull requests (if any) have been reviewed by their code managers.
- [x] Run the full Intel+GNU RT suite (compared to current baselines), preferably on Ursa (Derecho or Hercules are acceptable alternatives). **Exceptions:** documentation-only PRs, CI-only PRs, etc.
   - [x] Commit log file w/full results from RT suite run (if applicable).
   - [x] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR. Commit `test_changes.list`, even if it is empty.
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [ ] No.
   - [x] Yes. ChatGPT was used to assist in code cleaning
     - [ ] The code has been reviewed, edited, and validated by NWS staff. (Note: If the code has not yet been reviewed by NWS staff, leave unchecked, and OMD CMs will review as part of the PR review process.)
- [x] Fill out all sections of this template.

---

## Description:

### #3355
This PR introduces a Mixed-Layer Model (MLM) formulation for cloud-driven, top-down turbulent mixing in the TKE-EDMF PBL scheme. The MLM provides an alternative to the existing mass-flux treatment of stratocumulus-top-driven turbulence, which is based on a parameterization of surface-forced thermal plumes.

The formulation is based on Solomon et al. (2026), where it was evaluated against turbulence-resolving simulations of Arctic stratocumulus and shown to improve the representation of cloud-driven turbulent energy and water fluxes.

The MLM is implemented as an optional (mlm = .true.) component of TKE-EDMF and uses cloud-top radiative cooling and large-scale precipitation information from the physics suite to represent turbulent mixing driven from cloud top.

### #3388 
- Updates the CATChem submodule pointer to support full reproduction of GCAFSv1 baselines.
- The CATChem version bump also supports a "CATChem version 2" publication.

### Commit Message:
<!--
Provide a concise commit message for the UFS WM and any subcomponents; delete unnecessary info.
-->
```
* UFSWM - Update submodule pointers and conduct regression tests related to the MLM scheme 
* UFSWM - feat: update CATChem to reproduce GCAFSv1 baselines
  * CATChem - Update CATChem main hash
  * UFSATM - Create a namelist option (mlm) to run the new MLM scheme in TKE-EDMF, add diagnostics
    * ccpp-physics - Introduce an option to run the Mixed-Layer Model inside the TKE-EDMF PBL scheme
```

### Priority:
<!--
Indicate PR priority and include a justification for high/critical priority PRs; delete options that are not applicable. 
-->
- [ ] Critical Bugfix: Reason
- [x] High: To be included in the CCPPv8 release tag
- [ ] Normal

## Git Tracking
### UFSWM:
<!--
Add the related UFS WM Github Issue here:
-->
* Closes # https://github.com/ufs-community/ufs-weather-model/issues/3354
* Closes https://github.com/ufs-community/CATChem/issues/211

### Sub component Pull Requests:
<!--
Provide a list of subcomponents involved with this PR and include links to subcomponent PRs.
Example:
* UFSATM: NOAA-EMC/UFSATM#734
  * ccpp-physics: ufs-community/ccpp-physics#33
* WW3: NOAA-EMC/WW3#321
Delete sections that are not needed.
-->
  * UFSATM - https://github.com/NOAA-EMC/ufsatm/pull/1138
    * ccpp-physics - https://github.com/ufs-community/ccpp-physics/pull/390
  * CATChem - https://github.com/ufs-community/CATChem/pull/210
  
### UFSWM Blocking Dependencies:
<!--
Please include any UFS WM PRs (with links) that need to be completed before this one; delete what is not needed.
-->
- [ ] Blocked by #
- [x] None

### Documentation:
<!--
Indicate what documentation, if any, is needed for this PR and who will add it (if applicable).
Delete what is not needed.
-->
- [ ] Documentation update required. 
   - [ ] Relevant updates are included with this PR. 
   - [ ] A WM issue has been opened to track the need for a documentation update; a person responsible for submitting the update has been assigned to the issue (link issue).
- [x] Documentation update NOT required. 


---
## Changes
### Regression Test Changes (Please commit test_changes.list):
<!--
Indicate whether this PR creates new baselines, changes baselines, or not. Delete what is not needed.
For baseline changes, make sure to submit the test_changes.list file generated by a full RT run (Intel+GNU)
-->
- [ ] PR Adds New Tests/Baselines.
- [x] PR Updates/Changes Baselines. --> CATChem baselines change in combined PR
- [x] No Baseline Changes.

### Input data Changes:
<!--
If there are changes to input data for a test, provide information here. Delete options that are not needed.
-->
- [x] None.
- [ ] PR adds input data.
- [ ] PR changes existing input data.

### Library Changes/Upgrades:
<!-- Library updates take time. Provide library and version information here, and delete what is not needed. 
** SPECIAL INSTRUCTIONS **
- Create a separate issue in (https://github.com/JCSDA/spack-stack) asking for update to library. Include library name, library version.
- Add issue link from JCSDA/spack-stack following this item <!-- for example: "* JCSDA/spack-stack#1757"
-->
- [ ] Required
  * Library names w/versions:
  * Git Stack Issue (JCSDA/spack-stack#)
- [x] No Updates
  
---
<!-- STOP!!! THE FOLLOWING IS FOR CODE MANAGERS ONLY. PLEASE DO NOT FILL OUT -->
## Testing Log:
- RDHPCS
  - [ ] Orion
  - [ ] Hercules
  - [ ] GaeaC6
  - [ ] Derecho
  - [ ] Ursa
- WCOSS2
  - [ ] Dogwood/Cactus
  - [ ] Acorn
- [ ] CI
- [ ] opnReqTest (complete task if unnecessary)

## Testing Remarks:
<!-- Lead CM: List (1) testing issues that we are bypassing (e.g., failing CI due to remarks or an early-merged component PR) 
(2) Issues that have been opened based on testing results (3) any other relevant info -->
- 

