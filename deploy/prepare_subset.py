# -*- coding: utf-8 -*-
"""精简部署子集: lobby + fish00001 + pokdeng, res 只留 common/eng/sch(+init), 白名单2个。"""
import os, io, sys, shutil, subprocess, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\deploy_www'
ST = r'D:\deploy_sub'
KEEP = {'common', 'eng', 'sch', 'init'}
def copytree(s, d):
    subprocess.run(['robocopy', s, d, '/E', '/XD', '.svn', 'node_modules', '/NFL', '/NDL', '/NJH', '/NJS', '/NP'], capture_output=True)
if os.path.exists(ST):
    shutil.rmtree(ST, ignore_errors=True)
for rel in ['lobby', os.path.join('g', 'PSF-ON-00001'), os.path.join('g', 'PSC-ON-00001')]:
    print('copy', rel)
    copytree(os.path.join(SRC, rel), os.path.join(ST, rel))
    # trim res langs
    for root, dirs, files in os.walk(os.path.join(ST, rel)):
        if os.path.basename(root) == 'res':
            for d in list(dirs):
                if d not in KEEP:
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                    dirs.remove(d)
os.makedirs(os.path.join(ST, 'lobby_stub'), exist_ok=True)
for f in ['pslobby_ws_stub.py', 'lobby_pb2.py']:
    shutil.copy(os.path.join(SRC, 'lobby_stub', f), os.path.join(ST, 'lobby_stub', f))
json.dump([["PSF-ON-00001", 0, "FISH"], ["PSC-ON-00001", 0, "CARD"]], open(os.path.join(ST, 'lobby_stub', 'playable_games.json'), 'w', encoding='utf-8'))
print('SUBSET_PREPARED')