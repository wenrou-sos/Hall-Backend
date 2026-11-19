# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\index.html'
d = open(p, encoding='utf-8').read()
stub = ('<script>(function(){function mk(){var f=function(){};'
        'return new Proxy(f,{get:function(t,k){if(k===Symbol.toPrimitive)return function(){return "";};'
        'if(k==="then")return undefined;return mk();},apply:function(){return mk();}});}'
        'window.sdkbox=mk();window.sdkbox.PluginIAP=mk();window.sdkbox.PluginAnalytics=mk();'
        'window.jsb=window.jsb||mk();})();</script>')
if 'window.sdkbox' not in d:
    d = d.replace('<head>', '<head>' + stub, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('sdkbox stub injected')
else:
    print('already')