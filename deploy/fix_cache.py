# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = r'''
python3 - <<'EOF'
p='/etc/nginx/conf.d/playstar.conf'
s=open(p).read()
if 'Cache-Control' not in s:
    s=s.replace('server_name _;','server_name _;\n    add_header Cache-Control "no-store" always;')
    open(p,'w').write(s)
    print('header added')
else:
    print('already')
EOF
nginx -t && nginx -s reload && echo RELOADED
curl -s -o /dev/null -w "%{http_code}\n" -H "Cache-Control: no-cache" http://127.0.0.1/src/core.js
curl -s http://127.0.0.1/src/core.js | grep -c "location.host"
'''
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(), e.read().decode()[-200:])
c.close()