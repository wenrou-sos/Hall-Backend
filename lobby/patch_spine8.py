# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\frameworks\cocos2d-html5\extensions\spine\CCSkeletonWebGLRenderCmd.js'
d = open(p, encoding='utf-8').read()
pat = re.compile(r'(proto\.(uploadData|rendering|_uploadBufferData)\s*=\s*function\s*\([^)]*\)\s*\{\r?\n)')
n = 0
def rep(m):
    global n
    n += 1
    return m.group(1) + '    if (!this._node || !this._node._skeleton) { return; }\n'
d2 = pat.sub(rep, d)
open(p, 'w', encoding='utf-8').write(d2)
print('webgl rendercmd guards:', n)