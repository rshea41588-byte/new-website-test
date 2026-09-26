#!/usr/bin/env python3
"""PSI-100 pass 2026-09-26 (Bloomview), step 2. Perf only.

The 2026-09-08 loaders start gtag.js and oaiq.min.js at the first idle period (or first interaction).
Idle can arrive BEFORE the first frame is painted, so ~200 KB of third-party JS could compete with
first render. Now: wait for the browser's first paint entry, THEN the same idle callback. Hard cap:
setTimeout(L,4000) -- the same 4 s upper bound the old idle timeout gave -- so the tags always load
(background tabs, no PerformanceObserver). First interaction still loads them immediately. The inline
dataLayer/gtag() and oaiq() queue shims are untouched, so no event is lost.

Root *.html only (Blog/ is protected and excluded). Exact-string, idempotent, count-asserted.
"""
import glob, os, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
OLD = "if('requestIdleCallback'in window){requestIdleCallback(L,{timeout:4000});}else{setTimeout(L,4000);}"
NEW = ("/*psi100-paintgate-20260926*/function I(){if('requestIdleCallback'in window){requestIdleCallback(L,{timeout:4000});}else{setTimeout(L,4000);}}"
       "try{new PerformanceObserver(function(l,o){if(l.getEntries().length){o.disconnect();I();}}).observe({type:'paint',buffered:true});}catch(x){I();}setTimeout(L,4000);")
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
    s = open(f, encoding='utf-8', newline='').read()
    c = s.count(OLD)
    if not c or NEW in s:
        continue
    assert c in (1, 2), (f, c)
    open(f, 'w', encoding='utf-8', newline='').write(s.replace(OLD, NEW))
    n += 1
    print(os.path.basename(f), c)
print(n, 'files changed')
