# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
p='/data/playstar/www/lobby/index.html'
s=open(p).read()
if 'main.js?v=2' not in s:
    s=s.replace('src="main.js"','src="main.js?v=2"')
    open(p,'w').write(s)
    print('busted')
else:
    print('already')
EOF"""
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()