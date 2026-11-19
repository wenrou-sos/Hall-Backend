# -*- coding: utf-8 -*-
"""流式扫 svn.tar.gz: 枚举 srv/svn/server/ 顶层目录(增量打印), 捕获 dummy-king/tongits 相关路径。"""
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
            if len(parts) >= 4 and parts[3]:
                d = parts[3]
                if d not in server_dirs:
                    server_dirs[d] = 0
                    print('NEWDIR', d, 'at entry', n, 'elapsed', int(time.time() - t0), flush=True)
                server_dirs[d] += 1
        low = nm.lower()
        if ('dummy-king' in low or 'dummyking' in low or 'tongits' in low) and hits < 3000:
            hits += 1
            print('HIT', nm, m.size, flush=True)
        if n % 500000 == 0:
            print('scan', n, 'elapsed', int(time.time() - t0), 'server_dirs', len(server_dirs), flush=True)
print('SCAN3_DONE members', n, 'hits', hits, 'elapsed', int(time.time() - t0), flush=True)
print('SERVER_DIRS_FINAL:')
for k in sorted(server_dirs):
    print(' ', k, server_dirs[k], flush=True)