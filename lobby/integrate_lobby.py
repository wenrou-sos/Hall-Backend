# -*- coding: utf-8 -*-
"""把子代理立起的棋牌映射接进大厅: stub GAMES + core.js BuildLaunchURL, 重启 stub。"""
import os, json, io, sys, glob, subprocess, time, socket
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))

def listening(port):
    try:
        s = socket.create_connection(('127.0.0.1', int(port)), timeout=1)
        s.close()
        return True
    except Exception:
        return False

maps = {}
for f in glob.glob(os.path.join(ROOT, 'cards_map_*.json')):
    try:
        for gid, info in json.load(open(f, encoding='utf-8')).items():
            if listening(info['server_port']):
                maps[gid] = info
            else:
                print('skip (server down):', gid, info['server_port'])
    except Exception as e:
        print('skip', f, e)
print('card mappings:', len(maps))
# stub GAMES
stub = os.path.join(ROOT, 'pslobby_ws_stub.py')
d = open(stub, encoding='utf-8').read()
add = ''
for gid in sorted(maps):
    if "('%s', 0, 'CARD')" % gid not in d:
        add += "    ('%s', 0, 'CARD'),\n" % gid
if add:
    d = d.replace("    ('PSC-ON-00001', 0, 'CARD'),\n]", "    ('PSC-ON-00001', 0, 'CARD'),\n" + add + "]", 1)
    open(stub, 'w', encoding='utf-8').write(d)
    print('stub GAMES +=', add.count('CARD'))
# core.js BuildLaunchURL
core = r'D:\pslobby_wc\trunk\src\core.js'
c = open(core, encoding='utf-8').read()
anchor = '    return "./AutoClosePage/";'
addc = ''
for gid, info in sorted(maps.items()):
    if gid not in c:
        addc += '    if (game_id === "%s") { return "http://127.0.0.1:%s/?access_token=dev&subid=" + subgame_id; }\n' % (gid, info['client_port'])
if addc:
    c = c.replace(anchor, addc + anchor, 1)
    open(core, 'w', encoding='utf-8').write(c)
    print('core.js BuildLaunchURL +=', len(maps))
# restart stub
import urllib.request
pids = subprocess.run(['netstat', '-ano'], capture_output=True, text=True).stdout
for line in pids.splitlines():
    if ':8084' in line and 'LISTENING' in line:
        pid = line.split()[-1]
        subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
time.sleep(1)
subprocess.Popen([sys.executable, os.path.join(ROOT, 'pslobby_ws_stub.py')],
                 stdout=open(os.path.join(ROOT, 'pslobby_ws.log'), 'w'), stderr=subprocess.STDOUT)
print('stub restarted; INTEGRATE_DONE')