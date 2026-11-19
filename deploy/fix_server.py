# -*- coding: utf-8 -*-
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
def sh(cmd, t=300):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(), e.read().decode()
o, e = sh('apt-get update -qq && apt-get install -y -qq python3-pip python3-aiohttp python3-protobuf 2>&1 | tail -2', 300)
print('apt:', o[-300:], e[-300:])
o, e = sh('python3 -c "import aiohttp; print(\'aiohttp ok\')" 2>&1 | tail -1')
print(o.strip())
o, e = sh('python3 -c "import google.protobuf; print(\'protobuf ok\')" 2>&1 | tail -1')
print(o.strip())
# if protobuf missing, pip install
o, e = sh('python3 -c "import google.protobuf" 2>/dev/null || pip3 install --break-system-packages -q protobuf aiohttp 2>&1 | tail -1')
print('pipfallback:', o.strip()[:200])
start = r'''
pkill -f '/data/playstar/bin/' || true
pkill -f 'pslobby_ws_stub.py' || true
sleep 1
cd /data/playstar/srv/fish && setsid nohup env HTTP_PORT=8899 SERVER_NAME=fish LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/fish > /data/playstar/fish.log 2>&1 < /dev/null &
cd /data/playstar/srv/89-game-server && setsid nohup env HTTP_PORT=8901 SERVER_NAME=card89 LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/card89 > /data/playstar/card89.log 2>&1 < /dev/null &
cd /data/playstar && setsid nohup python3 /data/playstar/lobby_stub/pslobby_ws_stub.py > /data/playstar/lobby_stub.log 2>&1 < /dev/null &
sleep 4
ss -lnt | grep -E ':(8084|8899|8901)' || true
echo START_DONE
'''
o, e = sh(start, 60)
print(o[-600:], e[-300:])
c.close()
print('FIX_DONE')