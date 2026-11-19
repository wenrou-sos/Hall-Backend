# -*- coding: utf-8 -*-
"""给公网捕鱼 index.html 注入错误捕获钩子, 抓 boot 报错."""
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HOOK = '<script>window.__errs=[];window.__ws=[];window.addEventListener("error",function(e){window.__errs.push(String(e.message).slice(0,200)+" @ "+String(e.error&&e.error.stack).split("\\n").slice(1,4).join("|"));});(function(){var OW=window.WebSocket;window.WebSocket=function(u,p){var w=new OW(u,p);window.__ws.push({url:u});w.addEventListener("open",function(){window.__ws.push({ev:"open",url:u});});w.addEventListener("message",function(m){window.__ws.push({ev:"msg",len:m.data.byteLength||m.data.length});});w.addEventListener("close",function(){window.__ws.push({ev:"close",url:u});});return w;};window.WebSocket.prototype=OW.prototype;})();</script>'
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
hook = '''%s'''
n=0
for i in range(1,8):
    p='/data/playstar/www/g/PSF-ON-0000%%d/index.html'%%i
    s=open(p,encoding='utf-8',errors='ignore').read()
    if '__errs' not in s:
        if '<head>' in s:
            s=s.replace('<head>','<head>'+hook,1)
        else:
            s=hook+s
        open(p,'w',encoding='utf-8',newline='').write(s); n+=1
print('hook added',n)
EOF""" % HOOK
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-300:])
c.close()
print('HOOK_DONE')