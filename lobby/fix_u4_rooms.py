# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'.\fish\cards\u-game-server\application\lobbysettingU\service_dev.go'
d = open(p, 'rb').read().decode('utf-8')
twelve = ','.join(['1000'] * 12)
room12 = ','.join(['10000'] * 12)
d = d.replace('BalanceLimit:   "1000,1000,1000,1000",', 'BalanceLimit:   "%s",' % twelve, 1)
d = d.replace('RoomLimit:      "10000,10000,10000,10000",', 'RoomLimit:      "%s",' % room12, 1)
open(p, 'wb').write(d.encode('utf-8'))
print('u4 dev BalanceLimit/RoomLimit -> 12 entries')