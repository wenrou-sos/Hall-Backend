# -*- coding: utf-8 -*-
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
time.sleep(3)
cmds = ['systemctl is-active playstar-fish playstar-card89 playstar-lobby',
        'ss -lnt | grep -E ":(8084|8899|8901)"',
        'journalctl -u playstar-fish -n 6 --no-pager',
        'journalctl -u playstar-lobby -n 6 --no-pager']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print((o.read().decode() + e.read().decode()).strip()[:600]); print()
c.close()