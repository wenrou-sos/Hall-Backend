# -*- coding: utf-8 -*-
import os, shutil, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = chr(92) * 2 + '?' + chr(92)
src = r'D:\fish_frontend\srv\svn\game\PSF-ON-00001\trunk\frameworks\cocos2d-html5'
dst = os.path.abspath(r'.\fish\lobby\sd555-app-lobby\frameworks\cocos2d-html5')
n = 0
for dp, dn, fn in os.walk(src):
    if '.svn' in dp:
        continue
    for f in fn:
        s = os.path.join(dp, f)
        rel = os.path.relpath(s, src)
        d = os.path.join(dst, rel)
        if not os.path.exists(P + d):
            os.makedirs(P + os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, P + d)
            n += 1
print('copied missing files:', n)