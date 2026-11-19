# -*- coding: utf-8 -*-
"""定向流式扫描 svn.tar.gz，找到大厅工作副本即停；记录顶层目录。"""
import tarfile, io, sys, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
WANT = re.compile(r'^srv/svn/(game/PS-LOBBY|server/host-pslobby|server/ps_web_lobby|server/platform-frontend|game/PS-LOBBY[^/]*)/')
tops = set()
found = None
t0 = time.time()
n = 0
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
        name = m.name
        mm = re.match(r'^srv/svn/([^/]+)/$', name)
        if mm:
            tops.add(mm.group(1))
        if WANT.match(name):
            found = name
            print('FOUND', name, 'at entry', n, 'elapsed', int(time.time() - t0))
            break
        if n % 500000 == 0:
            print('progress', n, 'tops', sorted(tops), 'elapsed', int(time.time() - t0))
print('SCAN_END found=', found, 'tops=', sorted(tops), 'entries=', n)
open(r'D:\fish_tmp\pslobby_found.txt', 'w').write(found or 'NOT_FOUND')