# -*- coding: utf-8 -*-
"""打包部署物 -> SFTP 上传 -> 服务器解压+nginx+起服务+stub -> 验证。"""
import os, io, sys, tarfile, time, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.abspath(__file__))
ST = r'D:\deploy_www'
BIN = os.path.join(ROOT, 'bin')
TAR = r'D:\playstar_deploy.tar'
HOST = '82.158.228.38'

print('tar staging...')
P = chr(92) * 2 + '?' + chr(92)
def nogit(ti):
    if '.git' in ti.name.split('/'):
        return None
    return ti
if os.path.exists(TAR) and os.path.getsize(TAR) > 1000000:
    print('reuse existing tar')
else:
  with tarfile.open(TAR, 'w') as tf:
    tf.add(P + os.path.abspath(ST), arcname='www')
    tf.add(P + os.path.abspath(BIN), arcname='bin')
    tf.add(P + os.path.abspath(os.path.join(ROOT, '..', 'Fish-Game-Server')), arcname='srv/fish', filter=nogit)
    for cd in ['89-game-server', 'paikang52', 'u-game-server', 'colorgame', 'fishshrimpcrab']:
        tf.add(P + os.path.abspath(os.path.join(ROOT, '..', 'cards', cd)), arcname='srv/' + cd, filter=nogit)
print('tar size MB', round(os.path.getsize(TAR) / 1e6, 1))

c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username='root', password='t3S6GMuGwmWr', timeout=60)
# parallel chunked SFTP upload
import concurrent.futures as cf
CH = 3
size = os.path.getsize(TAR)
chunk = (size + CH - 1) // CH
parts = []
with open(TAR, 'rb') as f:
    for i in range(CH):
        data = f.read(chunk)
        if not data:
            break
        pp = TAR + '.part%d' % i
        open(pp, 'wb').write(data)
        parts.append(pp)
def up(pp):
    for attempt in range(3):
        try:
            cc = paramiko.SSHClient(); cc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            cc.connect(HOST, username='root', password='t3S6GMuGwmWr', timeout=60)
            t = cc.get_transport()
            t.window_size = 2 ** 26
            t.max_packet_size = 2 ** 18
            sf = paramiko.SFTPClient.from_transport(t)
            sf.put(pp, '/data/' + os.path.basename(pp))
            sf.close(); cc.close()
            return pp
        except Exception as ex:
            print('retry', pp, ex)
            time.sleep(3)
    raise RuntimeError('upload failed ' + pp)
print('uploading', len(parts), 'chunks parallel...')
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=CH) as ex:
    list(ex.map(up, parts))
print('upload done', int(time.time() - t0), 's')
i, o, e = c.exec_command('cat ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' > /data/playstar_deploy.tar && rm -f ' + ' '.join('/data/' + os.path.basename(p) for p in parts))
o.read(); e.read()

def sh(cmd):
    i, o, e = c.exec_command(cmd, timeout=300)
    out = o.read().decode(); err = e.read().decode()
    return out, err

setup = r'''
set -e
mkdir -p /data/playstar
tar -xf /data/playstar_deploy.tar -C /data/playstar
chmod +x /data/playstar/bin/* || true
# python deps for lobby stub
apt-get install -y python3-aiohttp python3-protobuf >/dev/null 2>&1 || pip3 install --break-system-packages aiohttp protobuf >/dev/null 2>&1 || true
# nginx conf
rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/conf.d/playstar.conf <<'EOF'
server {
    listen 80 default_server;
    server_name _;
    root /data/playstar/www/lobby;
    index index.html;
    client_max_body_size 50m;
    location / { try_files $uri $uri/ /index.html; }
    location /g/ { root /data/playstar/www; try_files $uri $uri/ =404; }
    location /ws/lobby { proxy_pass http://127.0.0.1:8084/lobby; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/fish { proxy_pass http://127.0.0.1:8899/fish; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/card89 { proxy_pass http://127.0.0.1:8901/card; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/card52 { proxy_pass http://127.0.0.1:8911/card; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/cardu4 { proxy_pass http://127.0.0.1:8914/card; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/cardcg { proxy_pass http://127.0.0.1:8916/card; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
    location /ws/cardfsc { proxy_pass http://127.0.0.1:8912/card; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }
}
EOF
nginx -t
systemctl enable nginx >/dev/null 2>&1 || true
systemctl restart nginx || nginx -s reload || true
# stop old instances
pkill -f '/data/playstar/bin/' || true
pkill -f 'pslobby_ws_stub.py' || true
sleep 1
# run game servers (dev)
cd /data/playstar/srv/fish
nohup env HTTP_PORT=8899 SERVER_NAME=fish LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/fish > /data/playstar/fish.log 2>&1 &
cd /data/playstar/srv/89-game-server
nohup env HTTP_PORT=8901 SERVER_NAME=card89 LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/card89 > /data/playstar/card89.log 2>&1 &
cd /data/playstar/srv/paikang52
nohup env HTTP_PORT=8911 SERVER_NAME=card52 LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/card52 > /data/playstar/card52.log 2>&1 &
cd /data/playstar/srv/u-game-server
nohup env HTTP_PORT=8914 SERVER_NAME=cardu4 LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/cardu4 > /data/playstar/cardu4.log 2>&1 &
cd /data/playstar/srv/colorgame
nohup env HTTP_PORT=8916 SERVER_NAME=cardcg LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/cardcg > /data/playstar/cardcg.log 2>&1 &
cd /data/playstar/srv/fishshrimpcrab
nohup env HTTP_PORT=8912 SERVER_NAME=cardfsc LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev /data/playstar/bin/cardfsc > /data/playstar/cardfsc.log 2>&1 &
cd /data/playstar
nohup python3 /data/playstar/lobby_stub/pslobby_ws_stub.py > /data/playstar/lobby_stub.log 2>&1 &
sleep 3
ss -lnt | grep -E ':(80|8084|8899|8901|8911|8914|8916|8912)' || true
echo SETUP_DONE
'''
out, err = sh(setup)
print(out[-2000:])
print('ERR', err[-1500:])
c.close()
print('DEPLOY_SCRIPT_DONE')