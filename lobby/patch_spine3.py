# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\frameworks\cocos2d-html5\extensions\spine\CCSkeleton.js'
d = open(p, encoding='utf-8').read()
d2, n = re.subn(r'this\._skeleton\.(\w+)\(', r'(this._skeleton && this._skeleton.\1(', d)
# 上面会多一个左括号，改用更稳妥的逐行守卫：还原并用行级替换
d2 = d
n = 0
out = []
for line in d.split('\n'):
    stripped = line.lstrip()
    if stripped.startswith('this._skeleton.') and '(' in stripped:
        indent = line[:len(line) - len(stripped)]
        line = indent + 'if (this._skeleton) ' + stripped
        n += 1
    out.append(line)
open(p, 'w', encoding='utf-8').write('\n'.join(out))
print('line-level skeleton guards:', n)