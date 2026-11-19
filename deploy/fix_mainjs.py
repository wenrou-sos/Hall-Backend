# -*- coding: utf-8 -*-
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
OLD = "new WebSocket('ws://127.0.0.1:8084/lobby')"
NEW = "new WebSocket((location.hostname==='127.0.0.1'||location.hostname==='localhost')&&location.port==='8083' ? 'ws://127.0.0.1:8084/lobby' : 'ws://'+location.host+'/ws/lobby')"
for base in [r'D:\pslobby_wc\trunk', r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    p = os.path.join(base, 'main.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8', errors='ignore').read()
        if OLD in s:
            open(p, 'w', encoding='utf-8', newline='').write(s.replace(OLD, NEW))
            print('patched', p)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
sf = c.open_sftp()
sf.put(r'D:\deploy_sub\lobby\main.js', '/data/playstar/www/lobby/main.js')
sf.close()
i, o, e = c.exec_command('curl -s http://127.0.0.1:8888/main.js | grep -c "ws/lobby"')
print('server grep', o.read().decode().strip())
c.close()
print('MAINJS_FIXED')