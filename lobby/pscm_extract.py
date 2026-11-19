# -*- coding: utf-8 -*-
"""按 ZIP64 中央目录偏移提取 ps-scm.zip 指定前缀的全部文件。"""
import struct, sys, io, os, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\ps-scm.zip'
PREFIX = sys.argv[1]
OUT = sys.argv[2]
f = open(SRC, 'rb')
f.seek(-65536, 2)
tail = f.read()
i = tail.rfind(b'PK\x05\x06')
cd_size, cd_off = struct.unpack('<II', tail[i + 12:i + 20])
if cd_off == 0xFFFFFFFF or cd_size == 0xFFFFFFFF:
    j = tail.rfind(b'PK\x06\x07')
    z64_off = struct.unpack('<Q', tail[j + 8:j + 16])[0]
    f.seek(z64_off)
    z = f.read(56)
    cd_size = struct.unpack('<Q', z[40:48])[0]
    cd_off = struct.unpack('<Q', z[48:56])[0]
f.seek(cd_off)
cd = f.read(cd_size)
pos = 0
n = 0
while pos < len(cd):
    if cd[pos:pos + 4] != b'PK\x01\x02':
        break
    (sig, vmade, vneed, flags, method, mt, md, crc, csize, usize, nlen, elen, clen,
     disk, iattr, eattr, lho) = struct.unpack('<IHHHHHHIIIHHHHHII', cd[pos:pos + 46])
    name = cd[pos + 46:pos + 46 + nlen].decode('utf-8', 'replace')
    extra = cd[pos + 46 + nlen:pos + 46 + nlen + elen]
    epos = 0
    while epos + 4 <= len(extra):
        hid, hsz = struct.unpack('<HH', extra[epos:epos + 4])
        body = extra[epos + 4:epos + 4 + hsz]
        if hid == 0x0001:
            k = 0
            if usize == 0xFFFFFFFF:
                usize = struct.unpack('<Q', body[k:k + 8])[0]; k += 8
            if csize == 0xFFFFFFFF:
                csize = struct.unpack('<Q', body[k:k + 8])[0]; k += 8
            if lho == 0xFFFFFFFF:
                lho = struct.unpack('<Q', body[k:k + 8])[0]; k += 8
        epos += 4 + hsz
    pos += 46 + nlen + elen + clen
    if not name.startswith(PREFIX) or name.endswith('/'):
        continue
    rel = name[len(PREFIX):]
    dst = os.path.join(OUT, rel.replace('/', os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    f.seek(lho)
    lh = f.read(30)
    lnlen, lelen = struct.unpack('<HH', lh[26:30])
    f.seek(lho + 30 + lnlen + lelen)
    data = f.read(csize)
    if method == 8:
        data = zlib.decompress(data, -15)
    open(dst, 'wb').write(data)
    n += 1
print('EXTRACT_DONE', n, 'files ->', OUT)