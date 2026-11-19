# -*- coding: utf-8 -*-
"""从 ps-scm.zip(stored) 按局部文件头 seek walk，只解出指定 SVN 裸库目录。"""
import struct, sys, io, os, zlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\ps-scm.zip'
TARGET_PREFIX = 'ps-scm/repositories/svn/BqS3sgnNvo/'   # game/PS-LOBBY
OUT = r'D:\pslobby_repo'

f = open(SRC, 'rb')
pos = 0
extracted = 0
seen_repos = set()
for i in range(2000000):
    f.seek(pos)
    hdr = f.read(30)
    if len(hdr) < 30 or hdr[:4] != b'PK\x03\x04':
        print('stop at entry', i, 'offset', pos, 'sig', hdr[:4].hex() if hdr else 'EOF')
        break
    (sig, ver, flags, method, mt, md, crc, csize, usize, nlen, elen) = struct.unpack('<IHHHHHIIIHH', hdr)
    name = f.read(nlen).decode('utf-8', 'replace')
    f.read(elen)
    data_start = f.tell()
    if name.startswith('ps-scm/repositories/svn/'):
        rid = name.split('/')[3]
        seen_repos.add(rid)
    if name.startswith(TARGET_PREFIX) and not name.endswith('/'):
        rel = name[len('ps-scm/repositories/svn/BqS3sgnNvo/'):]
        dst = os.path.join(OUT, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        f.seek(data_start)
        data = f.read(csize)
        if method == 8:
            data = zlib.decompress(data, -15)
        open(dst, 'wb').write(data)
        extracted += 1
        if extracted % 200 == 0:
            print('extracted', extracted, 'files; at', name[:80])
    if csize == 0 and (flags & 0x08):
        # data descriptor: scan next PK
        f.seek(data_start)
        buf = f.read(1 << 22)
        idx = buf.find(b'PK\x03\x04')
        if idx < 0:
            print('cannot skip descriptor entry', name); break
        pos = data_start + idx
    else:
        pos = data_start + csize
print('DONE extracted', extracted, 'files; repos seen', len(seen_repos))
print('target repo present:', 'BqS3sgnNvo' in seen_repos)