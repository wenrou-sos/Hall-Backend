# -*- coding: utf-8 -*-
"""scan5: 定向扫描 svn.tar.gz 的 srv/svn/server/git/ 子树：
实时列出其下目录名（parts[4]/parts[5]），解出所有 go.mod 与含 dummy 的路径文件到 fish/scm_git_probe。"""
import tarfile, sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
PF = 'srv/svn/server/git/'
OUT = r'fish\scm_git_probe'
t0 = time.time()
n = 0
seen = set()
entered = False
ext = 0
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
        nm = m.name
        if nm.startswith(PF):
            entered = True
            parts = nm.split('/')
            for depth in (4, 5):
                if len(parts) > depth:
                    key = '/'.join(parts[:depth + 1])
                    if key not in seen:
                        seen.add(key)
                        print('DIR', n, int(time.time() - t0), key, flush=True)
            rel = nm[len(PF):]
            low = rel.lower()
            if m.isfile() and (rel.endswith('go.mod') or 'dummy' in low):
                dst = os.path.join(OUT, rel.replace('/', os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'wb').write(tf.extractfile(m).read())
                ext += 1
                print('EXT', nm, m.size, flush=True)
        elif entered:
            print('LEFT subtree at', n, nm[:80], flush=True)
            break
        if n % 500000 == 0:
            print('scan', n, 'elapsed', int(time.time() - t0), flush=True)
print('SCAN5_DONE members', n, 'ext', ext, 'elapsed', int(time.time() - t0))