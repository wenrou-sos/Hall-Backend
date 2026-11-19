# -*- coding: utf-8 -*-
"""完整流式扫描 svn.tar.gz：顶层前缀统计 + srv/svn/server 目录清单 + 非 game 前缀 dummy 命中 + '/199/' 路径命中。"""
import tarfile, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
t0 = time.time()
n = 0
prefixes = {}
server_dirs = {}
hits = 0
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
        nm = m.name
        parts = nm.split('/')
        pf = '/'.join(parts[:3])
        prefixes[pf] = prefixes.get(pf, 0) + 1
        if len(parts) >= 4 and parts[1] == 'svn' and parts[2] != 'game':
            server_dirs['/'.join(parts[:4])] = server_dirs.get('/'.join(parts[:4]), 0) + 1
        low = nm.lower()
        if ('dummy' in low and not nm.startswith('srv/svn/game/')) or '/199/' in nm:
            hits += 1
            if hits <= 3000:
                print('HIT', nm, m.size, flush=True)
        if n % 200000 == 0:
            print('scan', n, 'elapsed', int(time.time() - t0), 'prefixes', len(prefixes), 'nongame_dirs', len(server_dirs), flush=True)
print('SCAN3_DONE members', n, 'hits', hits, 'elapsed', int(time.time() - t0))
print('PREFIXES:')
for k in sorted(prefixes):
    print(' ', k, prefixes[k])
print('NONGAME_DIRS:')
for k in sorted(server_dirs):
    print(' ', k, server_dirs[k])