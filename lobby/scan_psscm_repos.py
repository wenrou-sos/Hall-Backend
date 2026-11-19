# -*- coding: utf-8 -*-
"""列出 ps-scm.zip 中所有 svn/git 仓库名（中央目录第5段前缀），并输出 dummy 相关仓库的全部条目到文件。"""
import struct, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
P = r'D:\BaiduNetdiskDownload\ps-scm.zip'
CD_OFF = 246050450251
CD_SIZE = 156818434
f = open(P, 'rb')
f.seek(CD_OFF)
buf = f.read(CD_SIZE)
pos = 0
n = 0
repos = {}
dummy_entries = []
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
    n += 1
    parts = name.replace('\\', '/').split('/')
    if len(parts) >= 5 and parts[0] == 'ps-scm' and parts[1] == 'repositories':
        key = '/'.join(parts[:5])
        repos[key] = repos.get(key, 0) + 1
    if 'dummy' in name.lower():
        dummy_entries.append((name, usize, lho, method, csize))
    pos += 46 + nlen + elen + clen
print('entries', n, 'repos', len(repos), 'dummy_entries', len(dummy_entries))
for k in sorted(repos):
    print('REPO', k, repos[k])
with open(r'fish\lobby\psscm_dummy_entries.txt', 'w', encoding='utf-8') as out:
    for name, usize, lho, method, csize in dummy_entries:
        out.write('%s\t%d\t%d\t%d\t%d\n' % (name, usize, lho, method, csize))
print('DUMMY_ENTRIES_WRITTEN')