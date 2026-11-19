# -*- coding: utf-8 -*-
"""从 ps-scm.zip 中央目录收集指定前缀条目并解出文件。
用法: python extract_psscm_any.py <repo-prefix> [name-filter ...]
repo-prefix 例: ps-scm/repositories/svn/server/game-server/
name-filter: 只解出路径含这些子串的文件（缺省全解）"""
import struct, sys, io, os, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
P = r'D:\BaiduNetdiskDownload\ps-scm.zip'
CD_OFF = 246050450251
CD_SIZE = 156818434
prefix = sys.argv[1]
filters = sys.argv[2:]
OUT = r'fish\svn_repos'
f = open(P, 'rb')
f.seek(CD_OFF)
buf = f.read(CD_SIZE)
pos = 0
entries = []
while pos + 46 <= len(buf):
    if buf[pos:pos+4] != b'PK\x01\x02':
        break
    (vmade, vneed, flags, method, mtime, mdate, crc, csize, usize,
     nlen, elen, clen, disk, iattr, eattr, lho) = struct.unpack('<HHHHHHIIIHHHHHII', buf[pos+4:pos+46])
    name = buf[pos+46:pos+46+nlen].decode('utf-8', errors='replace')
    extra = buf[pos+46+nlen:pos+46+nlen+elen]
    if csize == 0xFFFFFFFF or usize == 0xFFFFFFFF or lho == 0xFFFFFFFF:
        ep = 0
        while ep + 4 <= len(extra):
            hid, hsz = struct.unpack('<HH', extra[ep:ep+4])
            if hid == 1:
                vals = extra[ep+4:ep+4+hsz]
                vp = 0
                if usize == 0xFFFFFFFF:
                    usize = struct.unpack('<Q', vals[vp:vp+8])[0]; vp += 8
                if csize == 0xFFFFFFFF:
                    csize = struct.unpack('<Q', vals[vp:vp+8])[0]; vp += 8
                if lho == 0xFFFFFFFF:
                    lho = struct.unpack('<Q', vals[vp:vp+8])[0]; vp += 8
                break
            ep += 4 + hsz
    if name.startswith(prefix):
        entries.append((name, usize, lho, method, csize))
    pos += 46 + nlen + elen + clen
print('matched entries', len(entries))
ext = 0
for name, usize, lho, method, csize in entries:
    rel = name[len('ps-scm/repositories/'):]
    if filters and not any(fl in name for fl in filters):
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