# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\psc00001_wc\trunk\src\g_message.js'
d = open(p, encoding='utf-8').read()
a = 'socket= new WebSocket("ws://192.168.10.51:8789/card");//KYE'
b = 'socket= new WebSocket("ws://127.0.0.1:8901/card");'
assert a in d
d = d.replace(a, b, 1)
open(p, 'w', encoding='utf-8').write(d)
print('psc client WS -> 8901/card')