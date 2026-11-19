# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
for cmd in ['ss -lnt | grep -E ":(80|8084|8899|8901)"',
            'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/',
            'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/g/PSF-ON-00001/',
            'tail -3 /data/playstar/fish.log', 'tail -3 /data/playstar/lobby_stub.log', 'tail -3 /data/playstar/card89.log']:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print(o.read().decode().strip()[:600]); print()
c.close()