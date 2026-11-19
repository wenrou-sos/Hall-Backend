# -*- coding: utf-8 -*-
"""scan4: 流式扫描 svn.tar.gz，实时输出 srv/svn/game 下新出现的工作副本名；
非 game 目录、工作副本名含 dummy、路径含 /199/ 的命中全输出。"""
import tarfile, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
t0 = time.time()
n = 0
wcs = {}
nongame = {}
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
        nm = m.name
        parts = nm.split('/')
        if len(parts) >= 4 and parts[0] == 'srv' and parts[1] == 'svn':
            if parts[2] == 'game':
                wc = parts[3]
                if wc not in wcs:
                    wcs[wc] = 0
                    print('NEWWC', n, int(time.time() - t0), wc, flush=True)
                wcs[wc] += 1
                if 'dummy' in wc.lower() and wcs[wc] <= 30:
                    print('DHIT', nm, m.size, flush=True)
            else:
                key = '/'.join(parts[:4])
                if key not in nongame:
                    nongame[key] = 0
                    print('NONGAME', n, int(time.time() - t0), key, flush=True)
                nongame[key] += 1
        if '/199/' in nm:
            print('H199', nm, m.size, flush=True)
        if n % 500000 == 0:
            print('scan', n, 'elapsed', int(time.time() - t0), 'wcs', len(wcs), flush=True)
print('SCAN4_DONE members', n, 'elapsed', int(time.time() - t0))
print('WORKING_COPIES:')
for k in sorted(wcs):
    print(' ', k, wcs[k])