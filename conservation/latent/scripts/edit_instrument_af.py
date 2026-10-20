import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
old = '''sub(atm, "     enddo\\n\\n\\n     do k = 1, npz\\n       if(flip_vc) then\\n         k1 = npz+1-k !reverse the k direction\\n",
    "     enddo\\n" + TB.format(arr="IPD_Stateout%gq0", s=4) + "\\n\\n     do k = 1, npz\\n       if(flip_vc) then\\n         k1 = npz+1-k !reverse the k direction\\n")'''
new = '''sub(atm, "     enddo\\n\\n\\n     if (Atm(n)%flagstruct%cpl_water_energy > 0) call cpl_water_energy(",
    "     enddo\\n" + TB.format(arr="IPD_Stateout%gq0", s=4) + "\\n\\n     if (Atm(n)%flagstruct%cpl_water_energy > 0) call cpl_water_energy(")'''
assert s.count(old) == 1, s.count(old)
p.write_text(s.replace(old, new)); print("ok")
