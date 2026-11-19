# -*- coding: utf-8 -*-
"""语言相关布局表只有 eng/tai: 给 [this._language()]/[language(RES_LANGUAGE)] 查表加 eng 回退, 中文文本+eng布局。"""
import os, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
roots = [r'D:\games_wc', r'D:\psc00001_wc']
pats = [
    (re.compile(r'([A-Za-z_][\w\.]*)\[(this\._language\(\))\]'), r'(\1[\2] || \1["eng"])'),
    (re.compile(r'([A-Za-z_][\w\.]*)\[(language\(RES_LANGUAGE\))\]'), r'(\1[\2] || \1["eng"])'),
]
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
            orig = d
            for pat, rep in pats:
                d = pat.sub(rep, d)
            if d != orig:
                open(p, 'w', encoding='utf-8').write(d)
                n += 1
print('LANG_LAYOUT_FALLBACK files', n)