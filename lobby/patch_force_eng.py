# -*- coding: utf-8 -*-
"""移除 card 客户端 resource.js 中 '非tai/eng强制回eng' 的判断, 让 sch/tch 等生效。"""
import os, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
roots = [r'D:\games_wc', r'D:\psc00001_wc']
pat = re.compile(r'if\s*\(\s*RES_LANGUAGE\s*!=\s*"tai"\s*&&\s*RES_LANGUAGE\s*!=\s*"eng"\s*\)\s*\{\s*RES_LANGUAGE\s*=\s*"eng";\s*\}')
n = 0
for root in roots:
    for dp, dn, fn in os.walk(root):
        if '.svn' in dp or 'node_modules' in dp or 'frameworks' in dp or 'publish' in dp:
            continue
        for f in fn:
            if not f.endswith('.js'):
                continue
            p = os.path.join(dp, f)
            d = open(p, encoding='utf-8', errors='replace').read()
            d2, k = pat.subn('// dev: keep chosen language (sch/tch/etc), do not force eng', d)
            if k:
                open(p, 'w', encoding='utf-8').write(d2)
                n += k
                print('fixed', p)
print('FORCE_ENG_REMOVED', n)