# -*- coding: utf-8 -*-
"""流式扫描 svn.tar.gz：找 dummy 相关路径 + 统计顶层前缀布局。"""
import tarfile, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
t0 = time.time()
n = 0
prefixes = {}
hits = 0
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
        nm = m.name
        parts = nm.split('/')
        pf = '/'.join(parts[:3])
        prefixes[pf] = prefixes.get(pf, 0) + 1
        if 'dummy' in nm.lower() and hits < 500:
            hits += 1
            print('HIT', nm, m.size, flush=True)
        if n % 50000 == 0:
            print('scan', n, 'elapsed', int(time.time() - t0), 'prefixes', len(prefixes), flush=True)
print('SCAN_DONE members', n, 'elapsed', int(time.time() - t0))
print('PREFIXES:')
for k in sorted(prefixes):
    print(' ', k, prefixes[k])