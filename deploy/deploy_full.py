# -*- coding: utf-8 -*-
"""增量部署全部12游戏: 6捕鱼变体+2四支刀+2色碟 + srv配置 + 白名单12 + nginx ws + systemd."""
import os, io, sys, tarfile, time, json, paramiko, concurrent.futures as cf
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.abspath(__file__))
WWW = r'D:\deploy_www'
TAR = r'D:\playstar_full.tar'
HOST = '82.158.228.38'
FISH = ['PSF-ON-0000%d' % i for i in range(2, 8)]
CARDS = ['PSC-ON-00007', 'PSC-ON-00008', 'PSC-ON-00013', 'PSC-ON-00014']
ALL12 = [['PSF-ON-0000%d' % i, 0, 'FISH'] for i in range(1, 8)] + [['PSC-ON-00001', 0, 'CARD'], ['PSC-ON-00007', 0, 'CARD'], ['PSC-ON-00008', 0, 'CARD'], ['PSC-ON-00013', 0, 'CARD'], ['PSC-ON-00014', 0, 'CARD']]
json.dump(ALL12, open(os.path.join(WWW, 'lobby_stub', 'playable_games.json'), 'w', encoding='utf-8'))
P = chr(92) * 2 + '?' + chr(92)
def nogit(ti):
    return None if '.git' in ti.name.split('/') else ti
with tarfile.open(TAR, 'w') as tf:
    for gid in FISH + CARDS:
        tf.add(P + os.path.join(WWW, 'g', gid), arcname='www/g/' + gid, filter=nogit)
    tf.add(P + os.path.join(WWW, 'lobby_stub'), arcname='lobby_stub')
    tf.add(P + os.path.abspath(os.path.join(ROOT, '..', 'cards', 'u-game-server')), arcname='srv/u-game-server', filter=nogit)
    tf.add(P + os.path.abspath(os.path.join(ROOT, '..', 'cards', 'paikang52')), arcname='srv/paikang52', filter=nogit)
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
        pp = TAR + '.f%d' % i; open(pp, 'wb').write(d); parts.append(pp)
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
    raise RuntimeError(pp)
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=CH) as ex:
    list(ex.map(up, parts))
print('upload', int(time.time() - t0), 's')
i, o, e = c.exec_command('cat ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' > /data/playstar_full.tar && rm -f ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' && tar -xf /data/playstar_full.tar -C /data/playstar && echo EXTRACTED')
print(o.read().decode().strip()[-200:])
setup = r'''
cd /data/playstar/www/g
for gid in PSF-ON-00002 PSF-ON-00003 PSF-ON-00004 PSF-ON-00005 PSF-ON-00006 PSF-ON-00007; do
  if [ -d "$gid/publish/html5" ]; then rm -rf "${gid}_pub"; cp -a "$gid/publish/html5" "${gid}_pub"; rm -rf "$gid"; mv "${gid}_pub" "$gid"; fi
done
python3 - <<'EOF'
p='/etc/nginx/conf.d/playstar.conf'
s=open(p).read()
add=''
for name,port in [('card52',8911),('cardu4',8914)]:
    if '/ws/'+name not in s:
        add+='    location /ws/%s { proxy_pass http://127.0.0.1:%d/card; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 3600s; }\n'%(name,port)
if add:
    s=s.rstrip()
    assert s.endswith('}')
    s=s[:-1]+add+'}\n'
    open(p,'w').write(s)
    print('nginx ws added')
EOF
nginx -t && nginx -s reload
for u in card52:paikang52:8911 cardu4:u-game-server:8914; do
  n=${u%%:*}; rest=${u#*:}; d=${rest%%:*}; port=${rest##*:}
  cat > /etc/systemd/system/playstar-$n.service <<EOF
[Unit]
Description=playstar-$n
After=network.target
[Service]
WorkingDirectory=/data/playstar/srv/$d
Environment=HTTP_PORT=$port SERVER_NAME=$n LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev
ExecStart=/data/playstar/bin/$n
Restart=always
RestartSec=2
[Install]
WantedBy=multi-user.target
EOF
done
systemctl daemon-reload
systemctl enable --now playstar-card52 playstar-cardu4
systemctl restart playstar-lobby
sleep 4
systemctl is-active playstar-fish playstar-card89 playstar-card52 playstar-cardu4 playstar-lobby
ss -lnt | grep -E ':(8084|8899|8901|8911|8914)' || true
echo FULL_SETUP_DONE
'''
i, o, e = c.exec_command(setup, timeout=180)
print(o.read().decode()[-800:]); print('ERR', e.read().decode()[-300:])
c.close()
print('FULL_DEPLOY_DONE')