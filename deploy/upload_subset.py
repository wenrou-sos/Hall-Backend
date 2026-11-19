# -*- coding: utf-8 -*-
"""精简子集上传+部署: lobby+fish00001+pokdeng -> http://82.158.228.38/"""
import os, io, sys, tarfile, time, paramiko, concurrent.futures as cf
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.abspath(__file__))
ST = r'D:\deploy_sub'
TAR = r'D:\playstar_sub.tar'
HOST = '82.158.228.38'
P = chr(92) * 2 + '?' + chr(92)
def nogit(ti):
    return None if '.git' in ti.name.split('/') else ti
if not (os.path.exists(TAR) and os.path.getsize(TAR) > 1000000):
    with tarfile.open(TAR, 'w') as tf:
        tf.add(P + os.path.abspath(ST), arcname='www')
        tf.add(P + os.path.abspath(os.path.join(ST, 'lobby_stub')), arcname='lobby_stub')
        for b in ['fish', 'card89']:
            tf.add(P + os.path.abspath(os.path.join(ROOT, 'bin', b)), arcname='bin/' + b)
        tf.add(P + os.path.abspath(os.path.join(ROOT, '..', 'Fish-Game-Server')), arcname='srv/fish', filter=nogit)
        tf.add(P + os.path.abspath(os.path.join(ROOT, '..', 'cards', '89-game-server')), arcname='srv/89-game-server', filter=nogit)
print('tar MB', round(os.path.getsize(TAR) / 1e6, 1))
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username='root', password='t3S6GMuGwmWr', timeout=60)
CH = 3
size = os.path.getsize(TAR); chunk = (size + CH - 1) // CH
parts = []
with open(TAR, 'rb') as f:
    for i in range(CH):
        d = f.read(chunk)
        if not d: break
        pp = TAR + '.p%d' % i; open(pp, 'wb').write(d); parts.append(pp)
def up(pp):
    for a in range(3):
        try:
            cc = paramiko.SSHClient(); cc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            cc.connect(HOST, username='root', password='t3S6GMuGwmWr', timeout=60)
            t = cc.get_transport(); t.window_size = 2 ** 26; t.max_packet_size = 2 ** 18
            sf = paramiko.SFTPClient.from_transport(t)
            sf.put(pp, '/data/' + os.path.basename(pp)); sf.close(); cc.close(); return
        except Exception as ex:
            print('retry', ex); time.sleep(3)
    raise RuntimeError('fail ' + pp)
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=CH) as ex:
    list(ex.map(up, parts))
print('upload done', int(time.time() - t0), 's')
i, o, e = c.exec_command('cat ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' > /data/playstar_sub.tar && rm -f ' + ' '.join('/data/' + os.path.basename(p) for p in parts))
o.read(); e.read()
setup = r'''
set -e
mkdir -p /data/playstar
tar -xf /data/playstar_sub.tar -C /data/playstar
chmod +x /data/playstar/bin/* || true
apt-get install -y python3-aiohttp python3-protobuf >/dev/null 2>&1 || pip3 install --break-system-packages aiohttp protobuf >/dev/null 2>&1 || true
rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/conf.d/playstar.conf <<'EOF'
server {
    listen 80 default_server;
    server_name _;
    root /data/playstar/www/lobby;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
    location /g/ { root /data/playstar/www; try_files $uri $uri/ =404; }
    location /ws/lobby { proxy_pass http://127.0.0.1:8084/lobby; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/fish { proxy_pass http://127.0.0.1:8899/fish; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/card89 { proxy_pass http://127.0.0.1:8901/card; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
}
EOF
nginx -t && (systemctl restart nginx || nginx -s reload || true)
pkill -f '/data/playstar/bin/' || true
pkill -f 'pslobby_ws_stub.py' || true
sleep 1
cd /data/playstar/srv/fish
nohup env HTTP_PORT=8899 SERVER_NAME=fish LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/fish > /data/playstar/fish.log 2>&1 &
cd /data/playstar/srv/89-game-server
nohup env HTTP_PORT=8901 SERVER_NAME=card89 LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/card89 > /data/playstar/card89.log 2>&1 &
cd /data/playstar
nohup python3 /data/playstar/lobby_stub/pslobby_ws_stub.py > /data/playstar/lobby_stub.log 2>&1 &
sleep 3
ss -lnt | grep -E ':(80|8084|8899|8901)' || true
echo SETUP_DONE
'''
i, o, e = c.exec_command(setup, timeout=300)
print(o.read().decode()[-1500:]); print('ERR', e.read().decode()[-800:])
c.close()
print('SUBSET_DEPLOY_DONE')