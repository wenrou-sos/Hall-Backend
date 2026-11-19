# -*- coding: utf-8 -*-
"""dev: 放宽 PokDeng DepositCall 的 in-room 校验, 避免回合结束后自动转账被 Fatal(3601_4) 断连。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'.\fish\cards\89-game-server\application\gameuser89\gameuser_89.go'
d = open(p, 'rb').read().decode('utf-8')
old = ('\t\tif g89.isGaming || g89.isWaiting || g89.gameRoomUuid != "" {\n'
       '\t\t\tlogger.Service.Zap.Errorw(GameUser89_DEPOSIT_CALL_INVALID,\n'
       '\t\t\t\t"GameUser", g89.secWebSocketKey,\n'
       '\t\t\t\t"GameRoomUuid", g89.gameRoomUuid,\n'
       '\t\t\t\t"IsGaming", g89.isGaming,\n'
       '\t\t\t\t"IsWaiting", g89.isWaiting,\n'
       '\t\t\t)\n'
       '\t\t\terrorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_DEPOSIT_CALL_INVALID)\n'
       '\t\t\treturn\n'
       '\t\t}\n')
new = '\t\t// dev: allow deposit even in-room (single-player test), avoid 3601_4 disconnect\n'
assert old in d, 'deposit guard'
d = d.replace(old, new, 1)
open(p, 'wb').write(d.encode('utf-8'))
print('gameuser89 deposit guard relaxed')