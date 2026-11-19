# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['ps -eo rss,args | grep -E "playstar/bin|pslobby_ws_stub" | grep -v grep',
        'nproc; free -m | head -2; df -h /data | tail -1',
        'ps -eo rss,comm,args --sort=-rss | grep -E "playstar/bin|pslobby|nginx|mysqld" | grep -v grep | awk "{printf \"%.0fMB %s %s\\n\", \\$1/1024, \\$2, \\$3}" | head -12',
        'du -sh /data/playstar/www /data/playstar/srv /data/playstar/bin 2>/dev/null',
        'uptime; cat /proc/loadavg',
        'ls /data/playstar/www/g | wc -l']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print(o.read().decode().strip()[:900]); print()
c.close()