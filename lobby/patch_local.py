# -*- coding: utf-8 -*-
import io, sys, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)))

def patch(rel, old, new, count=1):
    p = os.path.join(BASE, rel)
    d = open(p, 'rb').read().decode('utf-8')
    if old not in d:
        print('!! 未找到:', rel, old[:50]); return False
    d = d.replace(old, new, count)
    open(p, 'wb').write(d.encode('utf-8'))
    print('patched:', rel, old[:40].replace('\n', ' '))
    return True

for srv in ['lobbyserver', 'apiserver']:
    patch(srv + '/pg_redis.py', 'import aredis', 'import redis.asyncio as aredis')
    patch(srv + '/pg_redis.py', "REDIS_HOST = '34.80.168.83'", "REDIS_HOST = '127.0.0.1'")
    patch(srv + '/lobbyserver.py' if srv == 'lobbyserver' else srv + '/apiserver.py',
          'loop = asyncio.get_event_loop()',
          'loop = asyncio.new_event_loop()\n        asyncio.set_event_loop(loop)')

# pg_ga 空实现（去掉 pyga / 远程 GA 依赖）
ga = '''# -*- coding: utf-8 -*-
"""本地化空实现：原版依赖 pyga 向远程 Google Analytics 上报，本地 stub 掉。"""
import env_setting

class PG_GA(object):
    def __init__(self, ip, memberid=0):
        self.ip = ip
        self.memberid = memberid
    def send_page_view(self, page, title):
        pass
    def send_event(self, *a, **kw):
        pass
'''
for srv in ['lobbyserver', 'apiserver']:
    p = os.path.join(BASE, srv, 'pg_ga.py')
    if os.path.exists(p):
        open(p, 'wb').write(ga.encode('utf-8')); print('stubbed:', srv + '/pg_ga.py')
print('done')