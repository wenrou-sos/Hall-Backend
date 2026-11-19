# -*- coding: utf-8 -*-
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ws = os.getcwd()
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
parts = ['# PlayStar 服务器配置快照（82.158.228.38，可直接用于恢复）\n']
i, o, e = c.exec_command('cat /etc/nginx/conf.d/playstar.conf')
parts.append('\n## /etc/nginx/conf.d/playstar.conf\n```nginx\n' + o.read().decode() + '\n```\n')
for u in ['playstar-fish', 'playstar-card89', 'playstar-card52', 'playstar-cardu4', 'playstar-lobby']:
    i, o, e = c.exec_command('cat /etc/systemd/system/%s.service' % u)
    parts.append('\n## /etc/systemd/system/%s.service\n```ini\n' % u + o.read().decode() + '\n```\n')
i, o, e = c.exec_command('cat /data/playstar/lobby_stub/playable_games.json; echo; ss -lnt | grep -E ":(8084|8899|8901|8911|8914|8888)"')
parts.append('\n## 白名单 + 监听端口\n```json\n' + o.read().decode() + '\n```\n')
c.close()
wg = open(os.path.join(ws, 'fish', 'lobby', 'playable_games.json'), encoding='utf-8').read()
parts.append('\n## 本地 fish/lobby/playable_games.json\n```json\n' + wg + '\n```\n')
open(os.path.join(ws, '服务器配置快照.md'), 'w', encoding='utf-8').write(''.join(parts))
print('snapshot bytes', os.path.getsize(os.path.join(ws, '服务器配置快照.md')))