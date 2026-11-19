# -*- coding: utf-8 -*-
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
OLD = 'ws://127.0.0.1:8899/fish'
NEW = 'ws://"+location.host+"/ws/fish'
# local
lp = r'D:\deploy_sub\g\PSF-ON-00001\main.js'
if os.path.exists(lp):
    s = open(lp, encoding='utf-8', errors='ignore').read()
    print('local count', s.count(OLD))
    open(lp, 'w', encoding='utf-8', newline='').write(s.replace(OLD, NEW))
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
sf = c.open_sftp()
if os.path.exists(lp):
    sf.put(lp, '/data/playstar/www/g/PSF-ON-00001/main.js')
sf.close()
i, o, e = c.exec_command('curl -s http://127.0.0.1/g/PSF-ON-00001/main.js | grep -c "ws/fish"')
print('server grep', o.read().decode().strip())
c.close()
print('FISHMAIN_FIXED')