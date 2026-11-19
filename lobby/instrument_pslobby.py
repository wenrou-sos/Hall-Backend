# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\index.html'
d = open(p, encoding='utf-8').read()
hook = ('<script>window.__errs=[];window.__ws=[];'
        'window.addEventListener("error",function(e){window.__errs.push(String(e.message).slice(0,200)+" @ "+String(e.error&&e.error.stack).split("\\n").slice(1,3).join("|"));});'
        '(function(){var OW=window.WebSocket;window.WebSocket=function(u,p){var w=new OW(u,p);window.__ws.push({url:u,state:w.readyState});'
        'w.addEventListener("open",function(){window.__ws.push({ev:"open",url:u});});'
        'w.addEventListener("message",function(m){window.__ws.push({ev:"msg",len:m.data.byteLength||m.data.length});});'
        'w.addEventListener("close",function(){window.__ws.push({ev:"close",url:u});});'
        'w.addEventListener("error",function(){window.__ws.push({ev:"error",url:u});});'
        'var os=w.send.bind(w);w.send=function(x){window.__ws.push({ev:"send",len:x.byteLength||x.length});return os(x);};return w;};'
        'window.WebSocket.prototype=OW.prototype;})();</script>')
if 'window.__ws' not in d:
    d = d.replace('<head>', '<head>' + hook, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('instrumented pslobby index')
else:
    print('already')