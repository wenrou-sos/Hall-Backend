# -*- coding: utf-8 -*-
"""恢复 card 客户端语言回退(非tai/eng回eng), 保证中文资源不全的游戏仍可玩; 大厅仍中文+可选语言。"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
roots = [r'D:\games_wc', r'D:\psc00001_wc']
marker = '// dev: keep chosen language (sch/tch/etc), do not force eng'
block = ('if(RES_LANGUAGE!="tai" && RES_LANGUAGE!="eng"){\n'
         '            RES_LANGUAGE = "eng";\n'
         '        }')
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
            if marker in d:
                d = d.replace(marker, block)
                open(p, 'w', encoding='utf-8').write(d)
                n += 1
print('RESTORED_FALLBACK', n)