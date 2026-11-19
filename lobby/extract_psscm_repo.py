# -*- coding: utf-8 -*-
"""从 ps-scm.zip 按中央目录偏移解出指定 svn 仓库目录（默认 dummy_server_sync）。"""
import struct, sys, io, os, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
P = r'D:\BaiduNetdiskDownload\ps-scm.zip'
OUT = r'fish\svn_repos'
PREFIX = 'ps-scm/repositories/svn/server/'
want = sys.argv[1:] or ['dummy_server_sync']
entries = []
for line in open(r'fish\lobby\psscm_dummy_entries.txt', encoding='utf-8'):
    name, usize, lho, method, csize = line.rstrip('\n').split('\t')
    entries.append((name, int(usize), int(lho), int(method), int(csize)))
# dummy_entries 只含 dummy 命中；若目标仓库不含 dummy 名则需全量 CD（此脚本仅处理 dummy 相关仓库）
f = open(P, 'rb')
ext = 0
for name, usize, lho, method, csize in entries:
    rel = None
    for w in want:
        pf = PREFIX + w + '/'
        if name.startswith(pf):
            rel = name[len(PREFIX):]
            break
    if rel is None:
        continue
    dst = os.path.join(OUT, rel.replace('/', os.sep))
    if name.endswith('/'):
        os.makedirs(dst, exist_ok=True)
        continue
    f.seek(lho)
    lh = f.read(30)
    assert lh[:4] == b'PK\x03\x04', (name, lh[:4])
    nlen, elen = struct.unpack('<HH', lh[26:30])
    f.seek(lho + 30 + nlen + elen)
    data = f.read(csize)
    if method == 8:
        data = zlib.decompress(data, -15)
    elif method != 0:
        raise SystemExit('unsupported method %d %s' % (method, name))
    assert len(data) == usize, (name, len(data), usize)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(data)
    ext += 1
print('EXTRACTED', ext, 'files to', OUT)