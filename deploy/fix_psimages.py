# -*- coding: utf-8 -*-
"""PSImages 缺失素材 -> nginx 回退占位 json/png, 让大厅加载链完成."""
import paramiko, io, sys, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAREDACTED_FB_TOKEN==')
sf = c.open_sftp()
with sf.open('/data/playstar/www/lobby/_empty.json', 'w') as f:
    f.write('{}')
with sf.open('/data/playstar/www/lobby/_empty.png', 'wb') as f:
    f.write(png)
sf.close()
cmd = r'''
python3 - <<'EOF'
p='/etc/nginx/conf.d/playstar.conf'
s=open(p).read()
if 'PSImages' not in s:
    add="    location /res/PSImages/ { try_files $uri =404; }\n    location /res/ { try_files $uri =404; }\n"
    s=s.rstrip(); assert s.endswith('}'); s=s[:-1]+add+'}\n'
    open(p,'w').write(s); print('psimages fallback added')
else: print('already')
EOF
nginx -t && nginx -s reload && echo RELOADED
curl -s -o /dev/null -w "json:%{http_code} " http://127.0.0.1:8888/res/PSImages/3/eng/anm/banner/banner.json
curl -s http://127.0.0.1:8888/res/PSImages/3/eng/anm/banner/banner.json
'''
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(), e.read().decode()[-200:])
c.close()
print('PSIMG_FIXED')