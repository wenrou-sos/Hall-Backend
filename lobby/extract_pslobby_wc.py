# -*- coding: utf-8 -*-
"""流式解出 svn.tar.gz 中 PS-LOBBY 工作副本，离开该目录即停。"""
import tarfile, io, sys, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
PREFIX = 'srv/svn/game/PS-LOBBY/'
OUT = r'D:\pslobby_wc'
P = chr(92) * 2 + '?' + chr(92)
n = 0
ext = 0
t0 = time.time()
seen = False
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
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
                f = tf.extractfile(m)
                data = f.read()
                open(P + dst, 'wb').write(data)
                ext += 1
                if ext % 500 == 0:
                    print('extracted', ext, 'elapsed', int(time.time() - t0))
        elif seen:
            break
print('WC_DONE extracted', ext, 'entries', n, 'elapsed', int(time.time() - t0))