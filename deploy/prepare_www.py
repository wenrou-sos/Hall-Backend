# -*- coding: utf-8 -*-
"""准备部署用客户端包: 复制到 D:\\deploy_www 并把 WS/launch 地址改为动态主机(location.host/origin)。"""
import os, io, sys, re, shutil, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ST = r'D:\deploy_www'
PORT2ID = {8080:'PSF-ON-00001',8086:'PSF-ON-00002',8087:'PSF-ON-00003',8088:'PSF-ON-00004',8089:'PSF-ON-00005',8090:'PSF-ON-00006',8091:'PSF-ON-00007',
           8085:'PSC-ON-00001',8094:'PSC-ON-00007',8095:'PSC-ON-00008',8099:'PSC-ON-00013',8100:'PSC-ON-00014',8102:'PSC-ON-00016'}
WS = {'fish':('8899','/ws/fish'),'card89':('8901','/ws/card89'),'card52':('8911','/ws/card52'),'cardu4':('8914','/ws/cardu4'),'cardcg':('8916','/ws/cardcg'),'cardfsc':('8912','/ws/cardfsc')}

def copytree(src, dst):
    subprocess.run(['robocopy', src, dst, '/E', '/XD', '.svn', 'node_modules', '/NFL', '/NDL', '/NJH', '/NJS', '/NP'], capture_output=True)

def patch_file(p, subs):
    if not os.path.exists(p):
        return
    d = open(p, encoding='utf-8', errors='replace').read()
    orig = d
    for old, new in subs:
        d = d.replace(old, new)
    d = re.sub(r'"http://127\.0\.0\.1:(\d+)/\?access_token=dev&subid="',
               lambda m: 'window.location.origin + "/g/%s/?access_token=dev&subid="' % PORT2ID.get(int(m.group(1)), 'PSF-ON-00001'), d)
    if d != orig:
        open(p, 'w', encoding='utf-8').write(d)

# lobby
print('copy lobby')
copytree(r'D:\pslobby_wc\trunk', os.path.join(ST, 'lobby'))
patch_file(os.path.join(ST, 'lobby', 'src', 'core.js'), [
    ('new WebSocket("ws://127.0.0.1:8084/lobby")', 'new WebSocket("ws://" + window.location.host + "/ws/lobby")'),
])
# fish clients (patch publish bundle string)
for i in range(1, 8):
    gid = 'PSF-ON-%05d' % i
    src = r'D:\fish_frontend\srv\svn\game\PSF-ON-00001\trunk' if i == 1 else r'D:\games_wc\%s\trunk' % gid
    dst = os.path.join(ST, 'g', gid)
    print('copy', gid)
    copytree(src, dst)
    for bundle in ['publish/main.js', 'publish/common.js', 'publish/vendor.js', 'src/lkmessage.js']:
        patch_file(os.path.join(dst, bundle), [
            ('"ws://127.0.0.1:8899/fish"', '("ws://" + window.location.host + "/ws/fish")'),
            ("'ws://127.0.0.1:8899/fish'", '("ws://" + window.location.host + "/ws/fish")'),
        ])
# card clients
cardmap = {'PSC-ON-00001': (r'D:\psc00001_wc\trunk', 'card89'), 'PSC-ON-00007': (r'D:\games_wc\PSC-ON-00007\trunk', 'card52'),
           'PSC-ON-00008': (r'D:\games_wc\PSC-ON-00008\trunk', 'card52'), 'PSC-ON-00013': (r'D:\games_wc\PSC-ON-00013\trunk', 'cardu4'),
           'PSC-ON-00014': (r'D:\games_wc\PSC-ON-00014\trunk', 'cardu4'), 'PSC-ON-00016': (r'D:\games_wc\PSC-ON-00016\trunk', 'cardcg')}
for gid, (src, wskey) in cardmap.items():
    dst = os.path.join(ST, 'g', gid)
    print('copy', gid)
    copytree(src, dst)
    port, path = WS[wskey]
    for f in ['src/g_message.js', 'src/core.js']:
        patch_file(os.path.join(dst, f), [
            ('"ws://127.0.0.1:%s/card"' % port, '("ws://" + window.location.host + "%s")' % path),
            ("'ws://127.0.0.1:%s/card'" % port, '("ws://" + window.location.host + "%s")' % path),
        ])
# lobby stub + whitelist
os.makedirs(os.path.join(ST, 'lobby_stub'), exist_ok=True)
shutil.copy(r'.\fish\lobby\pslobby_ws_stub.py', os.path.join(ST, 'lobby_stub', 'pslobby_ws_stub.py'))
shutil.copy(r'D:\pslobby_stub\lobby_pb2.py', os.path.join(ST, 'lobby_stub', 'lobby_pb2.py'))
shutil.copy(r'.\fish\lobby\playable_games.json', os.path.join(ST, 'lobby_stub', 'playable_games.json'))
# stub sys.path insert D:\pslobby_stub -> local dir
p = os.path.join(ST, 'lobby_stub', 'pslobby_ws_stub.py')
d = open(p, encoding='utf-8').read().replace("sys.path.insert(0, r'D:\\pslobby_stub')", "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))")
open(p, 'w', encoding='utf-8').write(d)
print('PREPARE_WWW_DONE')