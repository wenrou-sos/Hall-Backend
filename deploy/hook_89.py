# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HOOK = '<script>window.__errs=[];window.addEventListener("error",function(e){window.__errs.push(String(e.message).slice(0,200)+" @ "+String(e.error&&e.error.stack).split("\\n").slice(1,4).join("|"));});</script>'
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
hook='''%s'''
p='/data/playstar/www/g/PSC-ON-00001/index.html'
s=open(p,encoding='utf-8',errors='ignore').read()
if '__errs' not in s:
    s=s.replace('<head>','<head>'+hook,1) if '<head>' in s else hook+s
    open(p,'w',encoding='utf-8',newline='').write(s); print('hook added')
else: print('already')
EOF""" % HOOK
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()