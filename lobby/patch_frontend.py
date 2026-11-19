# -*- coding: utf-8 -*-
import re, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sd555-app-lobby', 'src', 'build_setting.js')
d = open(p, encoding='utf-8').read()
d = re.sub(r'SW\.URL_LobbyServerUrl\s*=\s*"[^"]*"', 'SW.URL_LobbyServerUrl="ws://127.0.0.1:80/lobbyserver"', d)
d = re.sub(r'SW\.URL_GetIP\s*=\s*"[^"]*"', 'SW.URL_GetIP="http://127.0.0.1:81/getmyip"', d)
open(p, 'w', encoding='utf-8').write(d)
print('build_setting patched:')
for l in d.splitlines():
    if 'URL_LobbyServerUrl=' in l or 'URL_GetIP=' in l:
        print('  ', l.strip())