# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\index.html'
d = open(p, encoding='utf-8').read()
old = 'window.__errs.push(String(e.message).slice(0,300));'
new = ('window.__errs.push(String(e.message).slice(0,200)+" @ "+'
       'String(e.error&&e.error.stack).split("\\n").slice(0,5).join(" | "));')
if old in d:
    d = d.replace(old, new, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('stack hook added')
else:
    print('pattern not found (maybe already replaced)')