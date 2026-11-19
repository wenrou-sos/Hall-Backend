# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'.\fish\cards\u-game-server\application\lobbysettingU\service_dev.go'
d = open(p, 'rb').read().decode('utf-8')
d = d.replace('s.setDefaultAvailableGame(ls, models.PSC_ON_00014)', 's.setDefaultAvailableGame(ls, "PSC-ON-00014")', 1)
open(p, 'wb').write(d.encode('utf-8'))
print('use literal id')