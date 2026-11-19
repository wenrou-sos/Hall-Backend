# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\games_wc\PSC-ON-00007\trunk\index.html'
d = open(p, encoding='utf-8').read()
hook = ('<script>window.__errs=[];'
        'window.addEventListener("error",function(e){'
        'window.__errs.push(String(e.message).slice(0,160)+" @ "+String(e.error&&e.error.stack).split("\\n").slice(1,3).join("|"));'
        '});</script>')
if 'window.__errs' not in d:
    d = d.replace('<head>', '<head>' + hook, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('instrumented 8094')
else:
    print('already')