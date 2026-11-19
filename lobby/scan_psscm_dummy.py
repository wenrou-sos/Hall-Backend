# -*- coding: utf-8 -*-
"""解析 ps-scm.zip 中央目录：找 dummy 相关条目 + 顶层布局。不解压数据。"""
import struct, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
P = r'D:\BaiduNetdiskDownload\ps-scm.zip'
CD_OFF = 246050450251
CD_SIZE = 156818434
f = open(P, 'rb')
f.seek(CD_OFF)
buf = f.read(CD_SIZE)
pos = 0
n = 0
tops = {}
hits = 0
while pos + 46 <= len(buf):
    if buf[pos:pos+4] != b'PK\x01\x02':
        print('BAD sig at', pos); break
    (vmade, vneed, flags, method, mtime, mdate, crc, csize, usize,
     nlen, elen, clen, disk, iattr, eattr, lho) = struct.unpack('<HHHHHHIIIHHHHHII', buf[pos+4:pos+46])
    name = buf[pos+46:pos+46+nlen].decode('utf-8', errors='replace')
    extra = buf[pos+46+nlen:pos+46+nlen+elen]
    # zip64 extra
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
    n += 1
    parts = name.replace('\\', '/').split('/')
    top = '/'.join(parts[:2]) if len(parts) > 1 else parts[0]
    tops[top] = tops.get(top, 0) + 1
    if 'dummy' in name.lower():
        hits += 1
        if hits <= 400:
            print('HIT', name, usize, lho, method)
    pos += 46 + nlen + elen + clen
print('CD_DONE entries', n, 'hits', hits)
print('TOPS:')
for k in sorted(tops):
    print(' ', k, tops[k])