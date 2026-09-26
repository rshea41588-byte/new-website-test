#!/usr/bin/env python3
"""PSI-100 2026-09-26, Dylan-approved tag delay (psi-harness/AGENT-CONTRACT.md "DYLAN DECISION").
GA4 gtag.js and the OpenAI pixel load on the FIRST of pointerdown/keydown/touchstart/scroll (passive, once)
or 4000 ms after `load`, whichever first, once. Replaces the paint-gate/idle trigger from 5c9d2bb.
Inline dataLayer/gtag() and oaiq() stubs + all config/event calls untouched. Root *.html only
(Blog/ protected; thank-you/ is a conversion page and exempt). Exact-string, count-asserted, idempotent."""
import glob, os, re, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
TAIL_OLD = ("var ev=['pointerdown','keydown','touchstart','scroll','mousemove'];function H(){L();ev.forEach(function(x){removeEventListener(x,H,{passive:true});});}ev.forEach(function(x){addEventListener(x,H,{passive:true});});"
            "/*psi100-paintgate-20260926*/function I(){if('requestIdleCallback'in window){requestIdleCallback(L,{timeout:4000});}else{setTimeout(L,4000);}}try{new PerformanceObserver(function(l,o){if(l.getEntries().length){o.disconnect();I();}}).observe({type:'paint',buffered:true});}catch(x){I();}setTimeout(L,4000);})();")
TAIL_NEW = ("/*psi100-tagdelay-20260926*/['pointerdown','keydown','touchstart','scroll'].forEach(function(x){addEventListener(x,L,{once:true,passive:true});});"
            "function O(){setTimeout(L,4000);}if(document.readyState==='complete'){O();}else{addEventListener('load',O);}})();")
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
    s = open(f, encoding='utf-8', newline='').read()
    c = s.count(TAIL_OLD)
    if not c: continue
    assert c in (1, 2), (f, c)
    open(f, 'w', encoding='utf-8', newline='').write(s.replace(TAIL_OLD, TAIL_NEW)); n += 1
print(n, 'files changed')
