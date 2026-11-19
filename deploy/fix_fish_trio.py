# -*- coding: utf-8 -*-
"""上传同源配套 webpack trio(vendor/common/main) 到服务器, common 安全改 WS host."""
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
OLD = "'ws://127.0.0.1:8899/fish'"
NEW = "('ws://' + window.location.host + '/ws/fish')"
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=60)
sf = c.open_sftp()
for i in range(1, 8):
    gid = 'PSF-ON-0000%d' % i
    src = os.path.join(r'D:\games_wc', gid, 'trunk', 'publish')
    if i == 1:
        src = r'D:\fish_frontend\srv\svn\game\PSF-ON-00001\trunk\publish'
    for f in ['vendor.js', 'common.js', 'main.js']:
        lp = os.path.join(src, f)
        if not os.path.exists(lp):
            print('missing', gid, f); continue
        data = open(lp, 'rb').read()
        if f == 'common.js':
            s = data.decode('utf-8', errors='ignore').replace(OLD, NEW)
            data = s.encode('utf-8')
        tmp = os.path.join(os.environ.get('TEMP', '.'), 'trio_%s_%s' % (gid, f))
        open(tmp, 'wb').write(data)
        sf.put(tmp, '/data/playstar/www/g/%s/publish/%s' % (gid, f))
    print('trio uploaded', gid)
sf.close(); c.close()
print('TRIO_DONE')