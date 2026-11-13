<!-- POSTED 12 Nov 2026: body edited, comment https://github.com/ufs-community/ccpp-physics/issues/404#issuecomment-6829705001 (after rt -m 10451359 SUCCESS). Plan for ufs-community/ccpp-physics#404 (no replies; live body unedited since 24 Oct, so edit in place):
     1. Replace the issue description with issue_404_body_v2.md (trimmed rewrite: 4 causes + latent index note, fix_v3,
        RT result, forecast impact, negative condensate). Index-fix diffs kept in runs_29oct/r15_mlm/ and offered, not posted.
     2. Post the comment below so subscribers are notified of the edit.
     Evidence: experiments/runs_29oct/r15_mlm/ (PREREG.md + addendum, results.md, trace.md); mlm_diff3d.md (#404, 29 Oct).
     Line numbers: ccpp-physics ufs/dev 9b65688c (mfscuq_mlm.f, identical at 7ab37e41), 7ab37e41 (Thompson). -->

@lisa-bengtsson I've rewritten the description. The fix as first posted could go NaN; the updated one adds guards and passes the `control_p8` regression tests with `mlm` on. Two new results are at the end: the fix changes the forecast, and the MLM makes negative cloud water that Thompson turns into a water source.
