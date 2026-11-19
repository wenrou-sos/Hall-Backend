# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['uname -a', 'head -2 /etc/os-release', 'which docker python3 nginx go',
        'docker ps --format "{{.Names}} {{.Ports}}"', 'free -h | head -2', 'df -h /data | tail -1',
        'python3 --version', 'ls /data']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd)
    print(o.read().decode().strip())
    err = e.read().decode().strip()
    if err:
        print('ERR', err[:200])
c.close()