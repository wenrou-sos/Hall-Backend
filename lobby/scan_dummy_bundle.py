# -*- coding: utf-8 -*-
"""流式列出 gitlab backup tar 中含 dummy 或 5a39cadd 哈希的成员，定位 dummy(199) bundle。"""
import tarfile, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\1684674626_2023_05_21_13.3.2_gitlab_backup.tar'
t0 = time.time()
n = 0
with tarfile.open(SRC, 'r|') as tf:
    for m in tf:
        n += 1
        nm = m.name
        if 'dummy' in nm.lower() or '5a39cadd' in nm:
            print('HIT', nm, m.size, flush=True)
        if n % 20000 == 0:
            print('scan', n, 'elapsed', int(time.time() - t0), 'last', nm[:80], flush=True)
print('SCAN_DONE members', n, 'elapsed', int(time.time() - t0))