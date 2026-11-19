# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\frameworks\cocos2d-html5\extensions\spine\CCSkeletonAnimation.js'
d = open(p, encoding='utf-8').read()
pat = re.compile(r'(\n    \w+: function \([^)]*\) \{\r?\n)')
n = 0
def rep(m):
    global n
    n += 1
    return m.group(1) + '        if (!this._state) { return; }\r\n'
d2 = pat.sub(rep, d)
open(p, 'w', encoding='utf-8').write(d2)
print('method-entry guards:', n)