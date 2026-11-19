# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\src\core.js'
d = open(p, encoding='utf-8').read()
a = 'pslb.OpenFreeGame = function(id){\n    document.location.href = "https://tw.yahoo.com/";\n};'
b = 'pslb.OpenFreeGame = function(id){\n    document.location.href = pslb.BuildLaunchURL(id, 0);\n};'
c = 'pslb.OpenRealGame = function(id,sub_id){\n    document.location.href = "https://www.google.com.tw/";\n};'
e = 'pslb.OpenRealGame = function(id,sub_id){\n    document.location.href = pslb.BuildLaunchURL(id, sub_id);\n};'
n = 0
if a in d:
    d = d.replace(a, b, 1); n += 1
if c in d:
    d = d.replace(c, e, 1); n += 1
open(p, 'w', encoding='utf-8').write(d)
print('OpenRealGame/OpenFreeGame -> BuildLaunchURL, patched', n)