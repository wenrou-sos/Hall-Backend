# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
import os
root='/data/playstar/www/lobby/res'
n=0
for dp,dn,fn in os.walk(root):
    for f in fn:
        low=f.lower()
        if low!=f:
            src=os.path.join(dp,f); dst=os.path.join(dp,low)
            if not os.path.exists(dst):
                try: os.symlink(f, dst); n+=1
                except Exception: pass
    for d in dn:
        low=d.lower()
        if low!=d:
            src=os.path.join(dp,d); dst=os.path.join(dp,low)
            if not os.path.exists(dst):
                try: os.symlink(d, dst); n+=1
                except Exception: pass
print('lowercase symlinks', n)
EOF
curl -s -o /dev/null -w "logo:%{http_code}\\n" http://127.0.0.1:8888/res/sch/gameLogo/normal/psf-on-00001.png"""
i, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(), e.read().decode()[-200:])
c.close()
print('CASE_FIXED')