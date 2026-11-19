# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'.\fish\lobby\pslobby_ws_stub.py'
d = open(p, 'rb').read().decode('utf-8')
start = d.find('GAMES = [')
end = d.find(']', start) + 1
assert start >= 0 and end > start
new = ("# 大厅只展示白名单内「已验证可玩」的游戏；修好一个验证一个再往里加。\n"
       "_WHITELIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'playable_games.json')\n"
       "try:\n"
       "    GAMES = [tuple(x) for x in json.load(open(_WHITELIST, encoding='utf-8'))]\n"
       "except Exception:\n"
       "    GAMES = [('PSF-ON-00001', 0, 'FISH'), ('PSC-ON-00001', 0, 'CARD')]")
d = d[:start] + new + d[end:]
d = d.replace('import sys, os, asyncio, time\n', 'import sys, os, asyncio, time, json\n', 1)
d = d.replace('import sys, os, asyncio, time\r\n', 'import sys, os, asyncio, time, json\r\n', 1)
open(p, 'wb').write(d.encode('utf-8'))
print('stub now whitelist-driven')