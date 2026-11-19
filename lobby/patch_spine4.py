# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\frameworks\cocos2d-html5\extensions\spine\CCSkeletonAnimation.js'
d = open(p, encoding='utf-8').read()
n = 0
out = []
for line in d.split('\n'):
    s = line.lstrip()
    if (s.startswith('this._state.') or s.startswith('this._skeleton.')) and '(' in s:
        indent = line[:len(line) - len(s)]
        guard = 'this._state' if s.startswith('this._state.') else 'this._skeleton'
        line = indent + 'if (' + guard + ') ' + s
        n += 1
    out.append(line)
open(p, 'w', encoding='utf-8').write('\n'.join(out))
print('CCSkeletonAnimation guards:', n)