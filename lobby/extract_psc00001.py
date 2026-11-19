# -*- coding: utf-8 -*-
"""流式解出 svn.tar.gz 中 PSC-ON-00001 工作副本，离开即停。"""
import tarfile, io, sys, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
PREFIX = 'srv/svn/game/PSC-ON-00001/'
OUT = r'D:\psc00001_wc'
P = chr(92) * 2 + '?' + chr(92)
ext = 0; seen = False; t0 = time.time()
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        name = m.name
        if name.startswith(PREFIX):
            seen = True
            rel = name[len(PREFIX):]
            if not rel or rel.startswith('.svn'):
                continue
            dst = os.path.join(OUT, rel.replace('/', os.sep))
            if m.isdir():
                os.makedirs(P + dst, exist_ok=True)
            elif m.isfile():
                os.makedirs(P + os.path.dirname(dst), exist_ok=True)
                open(P + dst, 'wb').write(tf.extractfile(m).read())
                ext += 1
        elif seen:
            break
print('PSC00001_DONE extracted', ext, 'elapsed', int(time.time() - t0))