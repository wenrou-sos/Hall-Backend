# -*- coding: utf-8 -*-
"""重扫 svn.tar.gz：非 game 前缀的 dummy 命中 + srv/svn/server 顶层目录清单。"""
import tarfile, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
t0 = time.time()
n = 0
server_dirs = {}
hits = 0
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
        nm = m.name
        if nm.startswith('srv/svn/server/'):
            parts = nm.split('/')
            if len(parts) >= 4:
                d = parts[3]
                server_dirs[d] = server_dirs.get(d, 0) + 1
        if 'dummy' in nm.lower() and not nm.startswith('srv/svn/game/'):
            hits += 1
            if hits <= 2000:
                print('HIT', nm, m.size, flush=True)
        if n % 200000 == 0:
            print('scan', n, 'elapsed', int(time.time() - t0), 'server_dirs', len(server_dirs), flush=True)
print('SCAN2_DONE members', n, 'hits', hits, 'elapsed', int(time.time() - t0))
print('SERVER_DIRS:')
for k in sorted(server_dirs):
    print(' ', k, server_dirs[k])