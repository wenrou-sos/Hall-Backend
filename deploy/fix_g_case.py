# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
import os
n=0
for root in ['/data/playstar/www/g']:
    for dp,dn,fn in os.walk(root):
        for f in fn:
            low=f.lower()
            if low!=f:
                dst=os.path.join(dp,low)
                if not os.path.lexists(dst):
                    try: os.symlink(f,dst); n+=1
                    except Exception: pass
        for d in dn:
            low=d.lower()
            if low!=d:
                dst=os.path.join(dp,low)
                if not os.path.lexists(dst):
                    try: os.symlink(d,dst); n+=1
                    except Exception: pass
print('g lowercase symlinks',n)
EOF"""
i, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()
print('G_CASE_FIXED')