# -*- coding: utf-8 -*-
"""一次流式扫描解出 8 个游戏客户端工作副本（PSF-00002..00007, PSS-00001/00002）。"""
import tarfile, io, sys, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
TARGETS = ['PSF-ON-00002', 'PSF-ON-00003', 'PSF-ON-00004', 'PSF-ON-00005', 'PSF-ON-00006', 'PSF-ON-00007', 'PSS-ON-00001', 'PSS-ON-00002']
PREFIXES = ['srv/svn/game/%s/' % t for t in TARGETS]
OUT = r'D:\games_wc'
P = chr(92) * 2 + '?' + chr(92)
seen = set()
last_prefix = None
ext = 0
t0 = time.time()
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        name = m.name
        hit = None
        for pf in PREFIXES:
            if name.startswith(pf):
                hit = pf
                break
        if hit:
            seen.add(hit)
            last_prefix = hit
            rel = name[len(hit):]
            if not rel or rel.startswith('.svn'):
                continue
            gid = hit.split('/')[3]
            dst = os.path.join(OUT, gid, rel.replace('/', os.sep))
            if m.isdir():
                os.makedirs(P + dst, exist_ok=True)
            elif m.isfile():
                os.makedirs(P + os.path.dirname(dst), exist_ok=True)
                open(P + dst, 'wb').write(tf.extractfile(m).read())
                ext += 1
        elif last_prefix and len(seen) == len(TARGETS):
            break
        if ext and ext % 2000 == 0:
            print('ext', ext, 'seen', len(seen), 'elapsed', int(time.time() - t0))
print('GAMES8_DONE extracted', ext, 'seen', sorted(seen), 'elapsed', int(time.time() - t0))