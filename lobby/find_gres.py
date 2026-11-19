# -*- coding: utf-8 -*-
import os, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
root = r'D:\pslobby_wc\trunk'
for dp, dn, fn in os.walk(root):
    if '.svn' in dp or 'frameworks' in dp:
        continue
    for f in fn:
        if not f.endswith('.js'):
            continue
        p = os.path.join(dp, f)
        d = open(p, encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'g_resources\s*(=|\.push|\.concat)', d):
            print('DEF', p.replace(root, ''), m.group(0))
        for m in re.finditer(r'https?://[^"\'\s\)]+', d):
            u = m.group(0)
            if 'cocos2d-x.org' not in u and 'w3.org' not in u:
                print('URL', p.replace(root, ''), u[:80])