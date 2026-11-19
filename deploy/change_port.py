# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = r'''
sed -i 's/listen 80 default_server;/listen 8888 default_server;/' /etc/nginx/conf.d/playstar.conf
grep -n 'listen' /etc/nginx/conf.d/playstar.conf
nginx -t && nginx -s reload && echo RELOADED
sleep 1
curl -s -o /dev/null -w "local8888:%{http_code}\n" http://127.0.0.1:8888/
ss -lnt | grep -E ':(8888|80)\b' || true
'''
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(), e.read().decode()[-200:])
c.close()
print('PORT_CHANGED')