# -*- coding: utf-8 -*-
import os, shutil, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = chr(92) * 2 + '?' + chr(92)
src = r'D:\fish_frontend\srv\svn\game\PSF-ON-00001\trunk'
dst = os.path.abspath(r'.\fish\lobby\sd555-app-lobby')
missing = []
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fe.err'), encoding='utf-8', errors='replace'):
    if ' 404 ' in line:
        m = re.search(r'"GET /([^ ]+) HTTP', line)
        if m:
            missing.append(m.group(1))
missing = sorted(set(missing))
ok = 0; fail = []
for rel in missing:
    rel = rel.replace('/', os.sep)
    s = os.path.join(src, rel)
    d = os.path.join(dst, rel)
    if os.path.exists(s):
        os.makedirs(P + os.path.dirname(d), exist_ok=True)
        shutil.copyfile(s, P + d)
        ok += 1
    else:
        fail.append(rel)
print('404 total:', len(missing), 'copied:', ok)
print('still missing in fish engine:', fail[:10])