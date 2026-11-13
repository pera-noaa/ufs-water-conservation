# make variants of #408's samfdeepcnv.f: noret (no early returns, the reference) and proto (pending + single exit)
import re, sys
src, outdir = sys.argv[1], sys.argv[2]
s = open(src).read()

ret = re.compile(r'^( +)if\(totflg\) return\n', re.M)
assert len(ret.findall(s)) == 10, len(ret.findall(s))
open(f'{outdir}/noret408.f', 'w').write(ret.sub(r'\1if(.false.) return\n', s))

# pending(i) replaces caon(i) and adds progomega memory
p = s
assert p.count('caon') == 9, p.count('caon')
p = p.replace('!  columns the CA trigger can turn on again\n      logical caon(im)\n',
              '!  columns the rest of the routine still updates (CA trigger, progomega memory)\n      logical pending(im)\n')
a = ("        caon(i) = .false.\n        if(do_ca .and. ca_trigger) caon(i) =\n"
     "     &    real(ca_deep(i), kind=conv_wp) > real(nthresh, kind=conv_wp)\n")
assert p.count(a) == 1
p = p.replace(a, a.replace('caon', 'pending') +
              "        if(progomega .and. present(omegain)) pending(i) = pending(i)\n"
              "     &    .or. any(omegain(i,:) /= 0.0_kind_phys)\n")
guarded = re.compile(r'^ {6}if\(\.not\.progomega\)then\n +totflg = \.true\.\n +do i ?= ?1, ?im\n'
                     r'(?:!  no early return while the CA trigger can turn a column on\n)?'
                     r' +totflg = totflg \.and\. \(\.not\. cnvflg\(i\)\)\n(?: +& +\.and\. \(\.not\. caon\(i\)\)\n)?'
                     r' +enddo\n +if\(totflg\) return\n {6}endif\n', re.M)
p, k = guarded.subn('      if (.not. any(cnvflg .or. pending)) go to 900\n', p); assert k == 8, k
plain = re.compile(r'^ {6}totflg = \.true\.\n {6}do i=1,im\n +totflg = totflg \.and\. \(\.not\. cnvflg\(i\)\)\n {6}enddo\n {6}if\(totflg\) return\n', re.M)
p, k = plain.subn('      if (.not. any(cnvflg .or. pending)) go to 900\n', p); assert k == 2, k
assert 'caon' not in p and 'if(totflg) return' not in p
# MG outputs move after label 900
mg = re.compile(r'(      if\(mp_phys == mp_phys_mg\) then\n        do k=1,km\n          do i=1,im\n            QLCN\(i,k\)     = .*?\n          enddo\n        enddo\n      endif\n)', re.S)
m = mg.search(p); assert m
mg_txt = m.group(1); p = p[:m.start()] + p[m.end():]
exitblk = ("!  exit: work every column needs, convecting or not\n"
           "  900 continue\n"
           "      if(.not.hwrf_samfdeep) then\n" + mg_txt + "      endif\n")
a = '      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n'
assert p.count(a) == 1
p = p.replace(a, exitblk + a)
open(f'{outdir}/proto408.f', 'w').write(p)
print('ok')
