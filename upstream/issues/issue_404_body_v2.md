# Description

@lisa-bengtsson With `mlm = .true.`, the MLM from #390 does not conserve: in C96 `control_p8` (24 h) the PBL creates 4.4e-4 kg/m² of water per day and removes 1.28 W/m² of energy, while with `mlm` off it closes to round-off. It can also index outside the MLM layer, which gives NaNs, segfaults, or single bottom layers 40–52 K colder than the layer above. Below are the causes, a tested fix, and two results you will want before using it.

## Causes (`mfscuq_mlm.f`, `ufs/dev` 9b65688c)

1. **Smoothing is not conservative.** At cloud base (L524) the `k−1` tendencies of T, q and cloud water are replaced by the mean of their neighbours.
2. **The flux divergence is not mass-weighted.** Tendencies are `−ΔF/dz` of kinematic fluxes with no density (L457–521), and `dz = zm(k+1) − zm(k)` is the thickness of layer `k+1`, not `k`.
3. **`mlmb` can be 0 in an active column.** Only `mlmb = 1` is screened (L270), so the block at `mlmb − 1` writes level −1, and `b` (set only for `k = 2 … km−2`) is read unset at L377/L379.
4. **0/0 in inactive columns.** A column with `krad = 2` that is then switched off keeps `mlmt = 0`, `mlmb = 1`, so the mixed-layer means divide 0 by 0 (L300–307). Release builds don't use the result, but `control_debug_p8` with `mlm` on traps there at step 3 (Intel and GNU).

A latent one: `ntsw` and `ntinc` are full-tracer indices but are used on the vertically diffused arrays. They coincide in P8 as shipped, but not if a non-diffused tracer precedes snow or ice number. We have a tested host-side fix (new interstitial indices in ufsatm) if you want it.

## Fix (diff below)

- Flux form `−g·(ρF(k+1) − ρF(k))/del(k)`, with `del` passed in from `satmedmfvdifq`, including the `mlmb−1` and `mlmt+1` blocks.
- Smoothing kept, but the change at `k−1` is taken from `k` and `k−2` in proportion to their mass.
- Guards: switch the MLM off when `mlmb ≤ 1`, set `b` at every level, and compute the means only where `cnvflg` is true.

Result: the MLM's water and energy close to round-off (~1e-19 of the gross), and `mlm` off is bitwise unchanged. On ufs-weather-model develop 560345cc plus our SAMF/PBL package (#405, #408, #414; 3d0703d2) with `mlm` on, `control_p8` and `control_debug_p8` (Intel and GNU), `control_restart_p8`, `control_decomp_p8` and `control_2threads_p8` all pass.

## Two things to know

**The fix changes the forecast.** At 24 h, against the same build with only the guards, global means move by more than the spread of 10 runs perturbed through `consv_te`: PBL height −0.7 %, precipitation −0.7 %, low cloud −1.2 % cover (8–15 times the noise rms). We have not split this between density, layer thickness and smoothing.

**The MLM makes negative cloud water, with or without the fix.** The explicit update can remove more condensate from a layer than it holds: 0.14 kg/m² per day globally, mostly from the flux divergence inside the mixed layer. Thompson zeroes condensate ≤ 1e-12 on entry (`module_mp_thompson.F90` L2267, `ufs/dev` 7ab37e41), which turns that into a water source of 0.10 kg/m² per day, about 3 % of surface evaporation and over 100 times the imbalance above. Two ways to fix it: limit each condensate flux to what its source layer holds, or have `satmedmfvdifq` solve the MLM fluxes implicitly. Which fits the scheme is your call; we can run either through our budget meters.

<details><summary>Fix against <code>ufs/dev</code> 9b65688c (<code>mfscuq_mlm.f</code>, <code>satmedmfvdifq.F</code>)</summary>

```diff
--- a/physics/PBL/SATMEDMF/mfscuq_mlm.f
+++ b/physics/PBL/SATMEDMF/mfscuq_mlm.f
@@ -15,14 +15,15 @@
 !> @{
       subroutine mfscuq_mlm(im,ix,km,ntcw,ntsw,ntiw,
      &   nqni,ntrac1,cnvflg,zl,zm,q1,t1,u1,v1,
-     &   prec,rad,buop,pres,liwse,mse,thlvx,
+     &   prec,rad,buop,pres,del,liwse,mse,thlvx,
      &   radmin, cldtop, krad,              
      &   uflux,vflux,tdt,du,dv,rtg,
      &   eflux,rflux,wflux,pflux)
 !
       use machine,  only : kind_phys
       use physcons, grav => con_g, cp => con_cp,
-     &              hvap => con_hvap, hfus => con_hfus
+     &              hvap => con_hvap, hfus => con_hfus,
+     &              rd => con_rd, fv => con_fvirt
 !
       implicit none
 !
@@ -48,6 +49,7 @@
       real(kind=kind_phys), intent(in) :: prec(im,km)
       real(kind=kind_phys), intent(in) :: rad(im,km)
       real(kind=kind_phys), intent(in) :: pres(im,km)
+      real(kind=kind_phys), intent(in) :: del(im,km)
       real(kind=kind_phys), intent(in) :: liwse(im,km)
       real(kind=kind_phys), intent(in) :: mse(im,km)
       real(kind=kind_phys), intent(in) :: thlvx(im,km)
@@ -81,6 +83,7 @@
 !
       integer :: levs
       real(kind=kind_phys) :: dz
+      real(kind=kind_phys) :: rhoi(im,km), fp, fm, dd, ww
       real(kind=kind_phys) :: hflux(im,km)
       real(kind=kind_phys) :: qflux(im,km)
 
@@ -198,6 +201,13 @@
          buopa(i)     = 0.0
       enddo
 
+!     b is read at mlmb-1 and mlmt+1, outside the loop below: set it everywhere
+      do k = 1, km
+         do i = 1, im
+         b(i,k)    = t1(i,k)*(1.0 + 0.61*q1(i,k,1) - qcloud(i,k) -
+     $        qsnow(i,k) - qice(i,k))
+         enddo
+      enddo
       do k = klim-1, km-2
          do i = 1, im
          dmse(i,k) = ((mse(i,k+1)-mse(i,k))/(zm(i,k+1)-zm(i,k))/cp)
@@ -267,7 +277,7 @@
       enddo
 
       do i = 1, im
-         if (mlmb(i).eq.1)  cnvflg(i) = .false.
+         if (mlmb(i).le.1)  cnvflg(i) = .false.
          if (mlmb(i).ge.mlmt(i)) cnvflg(i) = .false.
       enddo
 
@@ -295,8 +305,9 @@
          enddo
       enddo
 
-!mixed-layer mean values
+!mixed-layer mean values (levs can be 0 in inactive columns)
       do i = 1, im
+         if (cnvflg(i)) then
          levs = mlmt(i)-mlmb(i)+1
          u_mean(i)   = u_mean(i)/levs
          v_mean(i)   = v_mean(i)/levs
@@ -305,6 +316,7 @@
          qni_mean(i) = qni_mean(i)/levs
          mse_mean(i) = mse_mean(i)/levs
          qtx_mean(i) = qtx_mean(i)/levs
+         endif
       enddo
 
       do k = 1, km
@@ -450,83 +462,90 @@
          enddo     !km
       enddo        !icycle
 
-!     update tendencies
-      do k = 1, km
+!     update tendencies: -g*d(rho*F)/dp, so the column sums conserve
+!     (flux k is at the interface between layers k-1 and k)
+      do i = 1, im
+         rhoi(i,1) = pres(i,1)/(rd*t1(i,1)*(1.+fv*max(q1(i,1,1),0.)))
+      enddo
+      do k = 2, km
          do i = 1, im
+            fp = pres(i,k)/(rd*t1(i,k)*(1.+fv*max(q1(i,k,1),0.)))
+            fm = pres(i,k-1)/(rd*t1(i,k-1)*(1.+fv*max(q1(i,k-1,1),0.)))
+            rhoi(i,k) = 0.5*(fp + fm)
+         enddo
+      enddo
+      do k = 1, km-1
+         do i = 1, im
             if (k.ge.mlmb(i).and.k.le.mlmt(i).and.cnvflg(i)) then
-            dz = zm(i,k+1)-zm(i,k)
-            du(i,k)     = du(i,k)    - (uflux(i,k+1) -uflux(i,k))/dz
-            dv(i,k)     = dv(i,k)    - (vflux(i,k+1) -vflux(i,k))/dz
-            tdt(i,k)    = tdt(i,k)   - (tflux(i,k+1) -tflux(i,k))/dz
-            rtg(i,k,1)  = rtg(i,k,1) - (qvflux(i,k+1)-qvflux(i,k))/dz
-            rtg(i,k,ntcw) = rtg(i,k,ntcw)-(qcflux(i,k+1)-qcflux(i,k))/dz
-            rtg(i,k,ntiw) = rtg(i,k,ntiw)-(qiflux(i,k+1)-qiflux(i,k))/dz
+            fp = rhoi(i,k+1)*grav/del(i,k)
+            fm = rhoi(i,k)*grav/del(i,k)
+            du(i,k)  = du(i,k)  - (uflux(i,k+1)*fp - uflux(i,k)*fm)
+            dv(i,k)  = dv(i,k)  - (vflux(i,k+1)*fp - vflux(i,k)*fm)
+            tdt(i,k) = tdt(i,k) - (tflux(i,k+1)*fp - tflux(i,k)*fm)
+            rtg(i,k,1) = rtg(i,k,1)
+     &                 - (qvflux(i,k+1)*fp - qvflux(i,k)*fm)
+            rtg(i,k,ntcw) = rtg(i,k,ntcw)
+     &                 - (qcflux(i,k+1)*fp - qcflux(i,k)*fm)
+            rtg(i,k,ntiw) = rtg(i,k,ntiw)
+     &                 - (qiflux(i,k+1)*fp - qiflux(i,k)*fm)
+            if (ntsw > 0) rtg(i,k,ntsw) = rtg(i,k,ntsw)
+     &                 - (qsflux(i,k+1)*fp - qsflux(i,k)*fm)
+            if (nqni > 0) rtg(i,k,nqni) = rtg(i,k,nqni)
+     &                 - (qniflux(i,k+1)*fp - qniflux(i,k)*fm)
             endif
          enddo
       enddo
-      if (ntsw > 0) then
-         do k = 1, km
-            do i = 1, im
-               if (k.ge.mlmb(i).and.k.le.mlmt(i).and.cnvflg(i)) then
-                  dz = zm(i,k+1)-zm(i,k)
-                  rtg(i,k,ntsw) = rtg(i,k,ntsw) - 
-     &                       (qsflux(i,k+1) -qsflux(i,k))/dz
-               endif
-            enddo
-         enddo
-      endif              
-      if (nqni > 0) then
-         do k = 1, km
-            do i = 1, im
-               if (k.ge.mlmb(i).and.k.le.mlmt(i).and.cnvflg(i)) then
-                  dz = zm(i,k+1)-zm(i,k)
-                  rtg(i,k,nqni) = rtg(i,k,nqni) - 
-     &                       (qniflux(i,k+1) -qniflux(i,k))/dz
-               endif
-            enddo
-         enddo
-      endif              
 
       do i=1,im
          if (cnvflg(i)) then
             k = mlmb(i)-1
-            dz = zm(i,k+1)-zm(i,k)
-            du(i,k)       = du(i,k)      - uflux(i,k+1)/dz
-            dv(i,k)       = dv(i,k)      - vflux(i,k+1)/dz
-            tdt(i,k)      = tdt(i,k)     - tflux(i,k+1)/dz
-            rtg(i,k,1)    = rtg(i,k,1)   - qvflux(i,k+1)/dz
-            rtg(i,k,ntcw) = rtg(i,k,ntcw)- qcflux(i,k+1)/dz
-            rtg(i,k,ntiw) = rtg(i,k,ntiw)- qiflux(i,k+1)/dz
-
+            fp = rhoi(i,k+1)*grav/del(i,k)
+            du(i,k)       = du(i,k)      - uflux(i,k+1)*fp
+            dv(i,k)       = dv(i,k)      - vflux(i,k+1)*fp
+            tdt(i,k)      = tdt(i,k)     - tflux(i,k+1)*fp
+            rtg(i,k,1)    = rtg(i,k,1)   - qvflux(i,k+1)*fp
+            rtg(i,k,ntcw) = rtg(i,k,ntcw)- qcflux(i,k+1)*fp
+            rtg(i,k,ntiw) = rtg(i,k,ntiw)- qiflux(i,k+1)*fp
             if (ntsw > 0) then
-              rtg(i,k,ntsw) = rtg(i,k,ntsw) - qsflux(i,k+1)/dz
+              rtg(i,k,ntsw) = rtg(i,k,ntsw) - qsflux(i,k+1)*fp
             endif
             if (nqni > 0) then
-              rtg(i,k,nqni) = rtg(i,k,nqni) - qniflux(i,k+1)/dz
+              rtg(i,k,nqni) = rtg(i,k,nqni) - qniflux(i,k+1)*fp
             endif
 
             k = mlmt(i)+1
-            dz = zm(i,k+1)-zm(i,k)
-            du(i,k)       = du(i,k)       + uflux(i,k)/dz
-            dv(i,k)       = dv(i,k)       + vflux(i,k)/dz
-            tdt(i,k)      = tdt(i,k)      + tflux(i,k)/dz
-            rtg(i,k,1)    = rtg(i,k,1)    + qvflux(i,k)/dz
-            rtg(i,k,ntcw) = rtg(i,k,ntcw) + qcflux(i,k)/dz
-            rtg(i,k,ntiw) = rtg(i,k,ntiw) + qiflux(i,k)/dz
-                 
+            fm = rhoi(i,k)*grav/del(i,k)
+            du(i,k)       = du(i,k)       + uflux(i,k)*fm
+            dv(i,k)       = dv(i,k)       + vflux(i,k)*fm
+            tdt(i,k)      = tdt(i,k)      + tflux(i,k)*fm
+            rtg(i,k,1)    = rtg(i,k,1)    + qvflux(i,k)*fm
+            rtg(i,k,ntcw) = rtg(i,k,ntcw) + qcflux(i,k)*fm
+            rtg(i,k,ntiw) = rtg(i,k,ntiw) + qiflux(i,k)*fm
             if (ntsw > 0) then
-              rtg(i,k,ntsw) = rtg(i,k,ntsw) + qsflux(i,k)/dz
+              rtg(i,k,ntsw) = rtg(i,k,ntsw) + qsflux(i,k)*fm
             endif
             if (nqni > 0) then
-              rtg(i,k,nqni) = rtg(i,k,nqni) + qniflux(i,k)/dz
+              rtg(i,k,nqni) = rtg(i,k,nqni) + qniflux(i,k)*fm
             endif
 
 !smooth discontinuity at cloud liquid base
             if (cldbase(i).gt.2) then
                k = cldbase(i)
-               tdt(i,k-1)      =  0.5*(tdt(i,k) + tdt(i,k-2))
-               rtg(i,k-1,1)    =  0.5*(rtg(i,k,1) + rtg(i,k-2,1))
-               rtg(i,k-1,ntcw) =  0.5*(rtg(i,k,ntcw) + rtg(i,k-2,ntcw))
+!              mass-weighted: the change at k-1 is taken from k and k-2
+               ww = del(i,k-1)/(del(i,k) + del(i,k-2))
+               dd = 0.5*(tdt(i,k) + tdt(i,k-2)) - tdt(i,k-1)
+               tdt(i,k-1) = tdt(i,k-1) + dd
+               tdt(i,k)   = tdt(i,k)   - ww*dd
+               tdt(i,k-2) = tdt(i,k-2) - ww*dd
+               dd = 0.5*(rtg(i,k,1) + rtg(i,k-2,1)) - rtg(i,k-1,1)
+               rtg(i,k-1,1) = rtg(i,k-1,1) + dd
+               rtg(i,k,1)   = rtg(i,k,1)   - ww*dd
+               rtg(i,k-2,1) = rtg(i,k-2,1) - ww*dd
+               dd = 0.5*(rtg(i,k,ntcw) + rtg(i,k-2,ntcw))
+     &            - rtg(i,k-1,ntcw)
+               rtg(i,k-1,ntcw) = rtg(i,k-1,ntcw) + dd
+               rtg(i,k,ntcw)   = rtg(i,k,ntcw)   - ww*dd
+               rtg(i,k-2,ntcw) = rtg(i,k-2,ntcw) - ww*dd
             endif
          endif
       enddo
--- a/physics/PBL/SATMEDMF/satmedmfvdifq.F
+++ b/physics/PBL/SATMEDMF/satmedmfvdifq.F
@@ -2126,7 +2126,7 @@
       if (mlm) then
          call mfscuq_mlm(im,im,km,ntcw,ntsw,ntiw,ntinc,
      &        ntrac1,mscuflg,zl,zm,q1,t1,u1,v1,
-     &        prec,rad,buoy,prsl,slx,hx,thlvx,
+     &        prec,rad,buoy,prsl,del,slx,hx,thlvx,
      &        radmin, kcld, krad,         
      &        uflux,vflux,tdt,du,dv,rtg,
      &        eflux,rflux,wflux,pflux)
```
</details>
