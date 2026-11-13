!     DEBUG ONLY (SA1 water): water the kb/jmin subtraction creates
            if(k == kb(i)) dbgwq(i) = dbgwq(i)
     &         + eta(i,k) * (qo(i,k) - tem1)
            if(k == jmin(i)) dbgwq(i) = dbgwq(i)
     &         + edto(i) * etad(i,k) * (qo(i,k) - tem1)
