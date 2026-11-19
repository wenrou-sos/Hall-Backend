# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\main.js'
d = open(p, encoding='utf-8').read()
a = 'cc.LoaderScene.preload(g_resources, function () {'
b = 'var __started = false;\n    function __go() {\n        if (__started) return;\n        __started = true;'
c = '    }, this);'
e = '    }\n    cc.LoaderScene.preload(g_resources, __go, this);\n    setTimeout(__go, 8000);'
n = 0
if a in d:
    d = d.replace(a, b, 1); n += 1
if c in d:
    d = d.replace(c, e, 1); n += 1
open(p, 'w', encoding='utf-8').write(d)
print('main.js auto-login fallback patched', n)