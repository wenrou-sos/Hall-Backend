# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HOOK = '<script>window.__errs=[];window.__ws=[];window.__mark=(window.__mark||0);window.addEventListener("error",function(e){window.__errs.push(String(e.message).slice(0,120));});(function(){var OW=window.WebSocket;window.WebSocket=function(u,p){var w=new OW(u,p);window.__ws.push({url:u,t:Date.now()});w.addEventListener("open",function(){window.__ws.push({ev:"open",t:Date.now()});});w.addEventListener("close",function(e){window.__ws.push({ev:"close",code:e.code,t:Date.now()});});w.addEventListener("error",function(){window.__ws.push({ev:"error",t:Date.now()});});return w;};window.WebSocket.prototype=OW.prototype;})();</script>'
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
hook='''%s'''
for gid in ['PSC-ON-00013','PSC-ON-00014']:
    p='/data/playstar/www/g/%%s/index.html'%%gid
    s=open(p,encoding='utf-8',errors='ignore').read()
    if '__ws' not in s:
        s=s.replace('<head>','<head>'+hook,1) if '<head>' in s else hook+s
        open(p,'w',encoding='utf-8',newline='').write(s); print('hook',gid)
    else: print('already',gid)
EOF""" % HOOK
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()