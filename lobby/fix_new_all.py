# -*- coding: utf-8 -*-
import os, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
root = r'D:\lobby_fe\src'
pat = re.compile(r'(?<!new )(?<![\w.])((?:cc|ccui|sp)\.[A-Z]\w*)\(')
total = 0; files = 0
for dp, dn, fn in os.walk(root):
    if '.svn' in dp:
        continue
    for f in fn:
        if not f.endswith('.js'):
            continue
        p = os.path.join(dp, f)
        d = open(p, encoding='utf-8').read()
        d2, n = pat.subn(lambda m: 'new ' + m.group(1) + '(', d)
        if n:
            open(p, 'w', encoding='utf-8').write(d2)
            total += n; files += 1
print('added new to class calls:', total, 'in', files, 'files')