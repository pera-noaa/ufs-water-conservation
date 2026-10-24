# Description

@lisa-bengtsson We checked the MLM from #390 with in-model budget meters: C96 `control_p8`, 24 h, `mlm` = .true. vs .false. in the same build (3d2331e3 with NOAA-EMC/ufsatm#1138 and ufs-community/ufs-weather-model#3355). With `mlm` on, the PBL creates 4.4e-4 kg/m² of water per day and removes 1.28 W/m² of energy. With it off, the PBL closes water to round-off. Runs with `mlm` = .false. are unaffected.

From `mfscuq_mlm.f` and `satmedmfvdifq.F` (`ufs/dev` 9b65688c):
1. The cloud-base smoothing (`mfscuq_mlm.f` L524) replaces the `k−1` tendencies of T, q and cloud water with the mean of their neighbours. This is not column-conserving: −0.88 W/m² and −6.0e-4 kg/m² per day.
2. The tendencies are `−ΔF/dz` of kinematic fluxes (L457–521), with no density, so the column sum does not telescope in mass. Also, `dz = zm(k+1) − zm(k)` is the thickness of layer `k+1`, since `satmedmfvdifq` sets `zm(k) = zi(k+1)`. A mass-weighted form, `−g·Δ(ρF)/Δp`, would close it.
3. `ntsw` and `ntinc` are passed as full tracer-array indices (`index_of_snow_mixing_ratio_in_tracer_concentration_array`), but they index `q1` and `rtg`, the vertical-diffusion arrays (`satmedmfvdifq.F` L660, L679; `mfscuq_mlm.f` L178, L472–518). The two orderings coincide in P8's Thompson configuration, not in general.

Also, with `mlm` on, single columns get a lowest layer 40–52 K colder than the layer above. This never happens with `mlm` off; we have not traced it.

Proposed fix (diff under *Output*; compiles, not yet run in the model):
1. Smoothing: keep it, but take the change at `k−1` from `k` and `k−2` in proportion to their masses (`del`), so the column sum is unchanged.
2. Flux divergence: `−g·(ρF(k+1) − ρF(k))/del(k)`, with `ρ` at each interface (the mean of the adjacent layers') and `del` passed in from `satmedmfvdifq`. Every interface flux then leaves one layer and enters the next, and the special cases at `mlmb−1` and `mlmt+1` use the same form.
3. Indices: add `ntswx` and `ntincx` to the host's interstitial vertical-diffusion indices, set where `ntcwx` and `ntiwx` are (NOAA-EMC/ufsatm `CCPP_typedefs.F90`), and pass those to `satmedmfvdifq` in place of `ntsw` and `ntinc`.

We can run it through the same meters if useful.

## Steps to Reproduce

1. Run `control_p8` (C96, 24 h) with `mlm = .true.` and again with `mlm = .false.`, from the same build.
2. In each, sum the column water (vapour + condensate) and `cp·T` before and after `satmedmfvdifq`, net of the surface fluxes it applies.
3. With `mlm` off the PBL's water change matches the surface flux to round-off; with it on it does not, and the PBL's energy change is 1.28 W/m² lower than with it off.

## Additional Context

* Hercules, Intel
* `FV3_GFS_v17_p8`; `satmedmfvdifq`, `mfscuq_mlm`
* #390, NOAA-EMC/ufsatm#1138, ufs-community/ufs-weather-model#3355

## Output

<details><summary>Proposed fix against <code>ufs/dev</code> 9b65688c</summary>

```diff
--- a/physics/PBL/SATMEDMF/mfscuq_mlm.f	2026-10-23 18:14:29
+++ b/physics/PBL/SATMEDMF/mfscuq_mlm.f	2026-10-23 18:18:53
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
 
@@ -450,83 +453,90 @@
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
--- a/physics/PBL/SATMEDMF/satmedmfvdifq.F	2026-10-23 18:12:53
+++ b/physics/PBL/SATMEDMF/satmedmfvdifq.F	2026-10-23 18:18:53
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
