# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
p='/etc/nginx/conf.d/playstar.conf'
s=open(p).read()
old='location / { try_files $uri $uri/ /index.html; }'
new='location = / { try_files /index.html =404; }\\n    location / { try_files $uri $uri/ =404; }'
if old in s:
    s=s.replace(old,new); open(p,'w').write(s); print('spa fallback narrowed')
else:
    print('already', 'location = /' in s)
EOF
nginx -t && nginx -s reload && echo RELOADED"""
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(), e.read().decode()[-200:])
c.close()
print('SPA_FIXED')