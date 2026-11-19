# -*- coding: utf-8 -*-
"""读 ps-scm.zip (ZIP64) 中央目录，列指定前缀文件名/大小/偏移。"""
import struct, sys, io, os
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
SRC = r'D:\BaiduNetdiskDownload\ps-scm.zip'
PREFIX = sys.argv[1] if len(sys.argv) > 1 else 'ps-scm/repositories/svn/'
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
    assert z[:4] == b'PK\x06\x06'
    cd_size = struct.unpack('<Q', z[40:48])[0]
    cd_off = struct.unpack('<Q', z[48:56])[0]
f.seek(cd_off)
cd = f.read(cd_size)
pos = 0
names = []
while pos < len(cd):
    if cd[pos:pos + 4] != b'PK\x01\x02':
        break
    (sig, vmade, vneed, flags, method, mt, md, crc, csize, usize, nlen, elen, clen,
     disk, iattr, eattr, lho) = struct.unpack('<IHHHHHHIIIHHHHHII', cd[pos:pos + 46])
    name = cd[pos + 46:pos + 46 + nlen].decode('utf-8', 'replace')
    extra = cd[pos + 46 + nlen:pos + 46 + nlen + elen]
    # zip64 extra
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
    if name.startswith(PREFIX):
        names.append((name, csize, method, lho))
    pos += 46 + nlen + elen + clen
print('entries under prefix:', len(names))
ext = Counter(os.path.splitext(n)[1].lower() for n, _, _, _ in names)
print('ext top:', ext.most_common(12))
print('total bytes:', sum(c for _, c, _, _ in names))
for n, c, m, o in names[:30]:
    print('  ', n, c)