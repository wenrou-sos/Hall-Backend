# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'.\fish\cards\paikang52\application\lobbysetting52\service_dev.go'
d = open(p, 'rb').read().decode('utf-8')
b12 = ','.join(['10', '20', '50', '100'] * 3)
bal12 = ','.join(['1000'] * 12)
d = d.replace('BetList:        "10,20,50,100",', 'BetList:        "%s",' % b12, 1)
d = d.replace('BalanceLimit:   "1000,1000,1000,1000",', 'BalanceLimit:   "%s",' % bal12, 1)
open(p, 'wb').write(d.encode('utf-8'))
print('52 BetList/BalanceLimit -> 12')