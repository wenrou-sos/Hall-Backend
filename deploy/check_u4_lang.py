# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['grep -rl "RES_LANGUAGE" /data/playstar/www/g/PSC-ON-00013/src/ | head',
        'grep -rn "keep chosen" /data/playstar/www/g/PSC-ON-00013/src/ | head',
        'grep -rn "RES_LANGUAGE" /data/playstar/www/g/PSC-ON-00013/src/resource.js | head']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print((o.read().decode() + e.read().decode()).strip()[:600]); print()
c.close()