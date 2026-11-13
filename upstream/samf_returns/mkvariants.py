# make variants of #403's samfdeepcnv.f: noret (no early returns, the reference) and proto (pending + single exit)
import re, sys
src, outdir = sys.argv[1], sys.argv[2]
s = open(src).read()

def sub1(pat, rep, s, n, flags=0):
    s2, k = re.subn(pat, rep, s, flags=flags)
    assert k == n, (pat[:60], k, n)
    return s2

# reference: every early return disabled
ret = re.compile(r'^( +)if ?\(totflg\) return\n', re.M)
assert len(ret.findall(s)) == 10, len(ret.findall(s))
open(f'{outdir}/noret.f', 'w').write(ret.sub(r'\1if(.false.) return\n', s))

# proto 1: pending(i), columns a later stage can turn on (CA trigger, progomega updraft memory)
p = sub1(r'(      logical do_aerosols, totflg, cnvflg\(im\), asqecflg\(im\), flg\(im\)\n)',
         r'\1!  columns the rest of the routine still updates (CA trigger, progomega memory)\n      logical pending(im)\n', s, 1)
p = sub1(r'(      do i=1,im\n        cnvflg\(i\) = \.true\.\n)',
         "      do i=1,im\n        pending(i) = .false.\n"
         "        if(do_ca .and. ca_trigger) pending(i) =\n"
         "     &    real(ca_deep(i), kind=conv_wp) > real(nthresh, kind=conv_wp)\n"
         "        if(progomega .and. present(omegain)) pending(i) = pending(i)\n"
         "     &    .or. any(omegain(i,:) /= 0.0_kind_phys)\n"
         "      enddo\n"
         r'\1', p, 1)
# proto 2: every early-return block (guarded or not) exits to 900 when no column is or can be active
blk = re.compile(r'^ {6}if\((?:\.not\.progomega \.or\. \.not\.coldpool|\.not\.coldpool)\)then\n'
                 r'(?: +totflg = \.true\.\n +do i ?= ?1, ?im\n +totflg = totflg \.and\. \(\.not\. cnvflg\(i\)\)\n +enddo\n)'
                 r' +if\(totflg\) return\n {6}endif\n', re.M)
p, k = blk.subn('      if (.not. any(cnvflg .or. pending)) go to 900\n', p)
assert k == 10, k
# proto 3: move the all-column work (coldpool relaxation, MG outputs) after label 900
relax = re.compile(r'(        do k = 1, km1\n          do i = 1, im\n            tem = real\(buoyexcs\(i,k\), kind=conv_wp\) \n'
                   r'.*?\n          enddo\n        enddo\n)', re.S)
m = relax.search(p); assert m and 'taucp' in m.group(1)
relax_txt = m.group(1); p = p[:m.start()] + p[m.end():]
mg = re.compile(r'(      if\(mp_phys == mp_phys_mg\) then\n        do k=1,km\n          do i=1,im\n            QLCN\(i,k\)     = .*?\n          enddo\n        enddo\n      endif\n)', re.S)
m = mg.search(p); assert m
mg_txt = m.group(1); p = p[:m.start()] + p[m.end():]
exitblk = ("!  exit: work every column needs, convecting or not\n"
           "  900 continue\n"
           "      if(coldpool) then\n" + relax_txt + "      endif\n"
           "      if(.not.hwrf_samfdeep) then\n" + mg_txt + "      endif\n")
p = sub1(r'(      ten_t = real\(\(new_t1 - real\(t1, kind=conv_wp\)\) / real\(delt,\n)', exitblk.replace('\\', '\\\\') + r'\1', p, 1)
open(f'{outdir}/proto.f', 'w').write(p)
print('ok')
