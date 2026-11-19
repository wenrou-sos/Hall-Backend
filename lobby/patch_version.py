# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\src\lib\lib_func.js'
d = open(p, encoding='utf-8').read()
old = 'function compareVersionNumber('
i = d.find(old)
if i >= 0:
    j = d.find('{', i)
    guard = '\n    if (serverVersion == null || localVersion == null) { return 0; }'
    # insert guard after opening brace of function
    d = d[:j + 1] + guard + d[j + 1:]
    open(p, 'w', encoding='utf-8').write(d)
    print('compareVersionNumber guarded')
else:
    print('not found')