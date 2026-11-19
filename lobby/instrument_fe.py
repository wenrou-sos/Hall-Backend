# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\index.html'
d = open(p, encoding='utf-8').read()
hook = ('<script>window.__errs=[];window.__logs=[];'
        'window.addEventListener("error",function(e){window.__errs.push(String(e.message).slice(0,300));});'
        'window.addEventListener("unhandledrejection",function(e){window.__errs.push("REJECT:"+String(e.reason).slice(0,300));});'
        '(function(){var ol=console.log,oe=console.error;'
        'console.log=function(){window.__logs.push(Array.map.call(arguments,String).join(" ").slice(0,200));return ol.apply(console,arguments);};'
        'console.error=function(){window.__errs.push(Array.map.call(arguments,String).join(" ").slice(0,300));return oe.apply(console,arguments);};'
        '})();</script>')
if 'window.__errs' not in d:
    d = d.replace('<head>', '<head>' + hook, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('instrumented')
else:
    print('already')