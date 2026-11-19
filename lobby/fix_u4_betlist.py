# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'.\fish\cards\u-game-server\application\lobbysettingU\service_dev.go'
d = open(p, 'rb').read().decode('utf-8')
old = 'BetList:        "10,20,50,100",'
new = 'BetList:        "10,20,50,100,10,20,50,100,10,20,50,100",'
assert old in d
d = d.replace(old, new, 1)
open(p, 'wb').write(d.encode('utf-8'))
print('u4 BetList -> 12')