# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\frameworks\cocos2d-html5\extensions\spine\CCSkeleton.js'
d = open(p, encoding='utf-8').read()
a = 'var data = cc.loader.getRes(argAtlasFile);'
b = 'var data = cc.loader.getRes(argAtlasFile);\n                if (!data) { return false; }'
c = 'var skeletonJson = cc.loader.getRes(argSkeletonFile);'
e = 'var skeletonJson = cc.loader.getRes(argSkeletonFile);\n            if (!skeletonJson) { return false; }'
n = 0
if a in d and 'if (!data) { return false; }' not in d:
    d = d.replace(a, b, 1); n += 1
if c in d and 'if (!skeletonJson) { return false; }' not in d:
    d = d.replace(c, e, 1); n += 1
open(p, 'w', encoding='utf-8').write(d)
print('spine guards added:', n)