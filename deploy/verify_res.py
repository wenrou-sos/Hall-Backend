# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
for u in ['/res/PSImages/3/eng/anm/banner/banner.json', '/res/common/nonexist.json', '/']:
    i, o, e = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8888' + u)
    print(u, o.read().decode().strip())
c.close()