# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
import json
for i in range(1,8):
    p='/data/playstar/www/g/PSF-ON-0000%d/project.json'%i
    d=json.load(open(p))
    d['jsList']=['src/lib/loader/loader_scene.js']
    json.dump(d,open(p,'w'),indent=4)
print('jslist loader-only set')
EOF"""
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()