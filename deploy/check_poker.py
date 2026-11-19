# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['ls -la /data/playstar/www/g/PSC-ON-00013/res/common/anm/poker/ | head',
        'head -c 400 /data/playstar/www/g/PSC-ON-00013/res/common/anm/poker/unocards.plist',
        'curl -s -o /dev/null -w "plist:%{http_code} " http://127.0.0.1:8888/g/PSC-ON-00013/res/common/anm/poker/unocards.plist',
        'curl -s -o /dev/null -w "png:%{http_code}" http://127.0.0.1:8888/g/PSC-ON-00013/res/common/anm/poker/unocards.png']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print((o.read().decode() + e.read().decode()).strip()[:500]); print()
c.close()