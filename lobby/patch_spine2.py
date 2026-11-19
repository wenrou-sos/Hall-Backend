# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\frameworks\cocos2d-html5\extensions\spine\CCSkeleton.js'
d = open(p, encoding='utf-8').read()
# 给所有直接读 this._skeleton. 的方法加 null 守卫
pat = re.compile(r'(\n    (\w+): function \([^)]*\) \{\n)(        this\._skeleton\.)')
n = 0
def rep(m):
    global n
    n += 1
    return m.group(1) + '        if (!this._skeleton) { return; }\n' + m.group(3)
d2 = pat.sub(rep, d)
open(p, 'w', encoding='utf-8').write(d2)
print('skeleton null guards:', n)