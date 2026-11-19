# -*- coding: utf-8 -*-
"""用本地配套 common.js(安全改 WS host) 覆盖服务器 fish publish/common.js, 修 webpack chunk 不配套."""
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
OLD = "'ws://127.0.0.1:8899/fish'"
NEW = "('ws://' + window.location.host + '/ws/fish')"
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=60)
sf = c.open_sftp()
for i in range(1, 8):
    gid = 'PSF-ON-0000%d' % i
    lp = os.path.join(r'D:\games_wc', gid, 'trunk', 'publish', 'common.js')
    if i == 1:
        lp = r'D:\fish_frontend\srv\svn\game\PSF-ON-00001\trunk\publish\common.js'
    if not os.path.exists(lp):
        print('missing local', gid); continue
    s = open(lp, encoding='utf-8', errors='ignore').read()
    n = s.count(OLD)
    s = s.replace(OLD, NEW)
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'common_%s.js' % gid)
    open(tmp, 'w', encoding='utf-8', newline='').write(s)
    sf.put(tmp, '/data/playstar/www/g/%s/publish/common.js' % gid)
    print('uploaded', gid, 'replaced', n, 'size', len(s))
sf.close(); c.close()
print('FISH_COMMON_FIXED')