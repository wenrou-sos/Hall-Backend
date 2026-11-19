# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = [
    'ls -la /data/playstar/bin/ | head',
    'cd /data/playstar/srv/fish && timeout 5 /data/playstar/bin/fish 2>&1 | head -5',
    'python3 -c "import aiohttp, protobuf" 2>&1 | head -2',
    'cd /data/playstar && timeout 5 python3 lobby_stub/pslobby_ws_stub.py 2>&1 | head -3',
    'ps aux | grep -E "playstar/bin|pslobby" | grep -v grep | head',
]
for cmd in cmds:
    i, o, e = c.exec_command(cmd, timeout=30)
    print('$', cmd); print((o.read().decode() + e.read().decode()).strip()[:500]); print()
c.close()