# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\src\core.js'
d = open(p, encoding='utf-8').read()
a = 'new WebSocket("ws://dev-gs.iplaystar.net:81/lobby")'
b = 'new WebSocket("ws://127.0.0.1:8084/lobby")'
assert a in d
d = d.replace(a, b, 1)
old = 'return "http://localhost:63342/"+game_id+"/index.html?subid="+subgame_id;'
new = ('if (game_id === "PSF-ON-00001") { return "http://127.0.0.1:8080/?access_token=dev&subid=" + subgame_id; }\n'
       '    return "./AutoClosePage/";')
assert old in d
d = d.replace(old, new, 1)
open(p, 'w', encoding='utf-8').write(d)
print('core.js patched: WS->8084, launch PSF-ON-00001->8080')