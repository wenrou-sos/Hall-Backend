# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\index.html'
d = open(p, encoding='utf-8').read()
n = d.count('Array.map.call')
d = d.replace('Array.map.call', 'Array.prototype.map.call')
open(p, 'w', encoding='utf-8').write(d)
print('fixed Array.map occurrences:', n)