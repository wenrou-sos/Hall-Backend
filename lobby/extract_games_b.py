# -*- coding: utf-8 -*-
"""流式扫描 svn.tar.gz，解出 B 组 6 个客户端工作副本的 trunk 到 D:\\games_wc\\<PSCid>\\trunk。"""
import tarfile, sys, os, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
TARGETS = ['PSC-ON-00010', 'PSC-ON-00011', 'PSC-ON-00013', 'PSC-ON-00014', 'PSC-ON-00015', 'PSC-ON-00016']
PREFIXES = ['srv/svn/game/%s/trunk/' % t for t in TARGETS]
OUT = r'D:\games_wc'
P = chr(92) * 2 + '?' + chr(92)
seen = set()
miss = 0
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
            miss = 0
            rel = name[len(hit):]
            if not rel or rel.startswith('.svn') or '/.svn/' in rel or rel.endswith('/.svn'):
                continue
            gid = hit.split('/')[3]
            dst = os.path.join(OUT, gid, 'trunk', rel.replace('/', os.sep))
            if m.isdir():
                os.makedirs(P + dst, exist_ok=True)
            elif m.isfile():
                os.makedirs(P + os.path.dirname(dst), exist_ok=True)
                with open(P + dst, 'wb') as f:
                    f.write(tf.extractfile(m).read())
                ext += 1
        else:
            if len(seen) == len(TARGETS):
                miss += 1
                if miss > 2000:
                    break
        if ext and ext % 2000 == 0:
            print('ext', ext, 'seen', len(seen), 'elapsed', int(time.time() - t0), flush=True)
print('GAMES_B_DONE extracted', ext, 'seen', sorted(seen), 'elapsed', int(time.time() - t0), flush=True)