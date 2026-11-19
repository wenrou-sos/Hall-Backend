# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
b6 = '10,50,100,500,10,50'
for game in ['colorgame', 'fishshrimpcrab']:
    p = r'.\fish\cards\%s\application\gamesettingFS\service_dev.go' % game
    d = open(p, 'rb').read().decode('utf-8')
    old = 'BetList:   "10,50,100,500",'
    if old in d:
        d = d.replace(old, 'BetList:   "%s",' % b6, 1)
        open(p, 'wb').write(d.encode('utf-8'))
        print(game, 'gamesettingFS BetList -> 6')
    else:
        print(game, 'pattern not found')