# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['curl -s -o /dev/null -w "%{http_code} %{content_type}" http://127.0.0.1/src/core.js',
        'curl -s http://127.0.0.1/src/core.js | grep -c "location.host"',
        'curl -s http://127.0.0.1/src/core.js | head -c 80',
        'curl -s http://127.0.0.1/project.json | head -c 200',
        'curl -s http://127.0.0.1/g/PSF-ON-00001/src/g_message.js | grep -c location.host',
        'curl -s -o /dev/null -w "fish:%{http_code}" http://127.0.0.1/g/PSF-ON-00001/',
        'curl -s -o /dev/null -w " pok:%{http_code}" http://127.0.0.1/g/PSC-ON-00001/']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print(o.read().decode().strip()[:200]); print()
c.close()