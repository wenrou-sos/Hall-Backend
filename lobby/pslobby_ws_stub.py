# -*- coding: utf-8 -*-
"""本地 PS-LOBBY WS 后端 stub(:8084/lobby)，按 lib/lobby.proto 契约回 LoginRecall(含游戏列表)。"""
import sys, os, asyncio, time, json
sys.path.insert(0, r'D:\pslobby_stub')
import lobby_pb2 as pb
from aiohttp import web

# 大厅只展示白名单内「已验证可玩」的游戏；修好一个验证一个再往里加。
_WHITELIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'playable_games.json')
try:
    GAMES = [tuple(x) for x in json.load(open(_WHITELIST, encoding='utf-8'))]
except Exception:
    GAMES = [('PSF-ON-00001', 0, 'FISH'), ('PSC-ON-00001', 0, 'CARD')]

def member_info():
    mi = pb.MemberInfo()
    mi.id = 'DEV'
    mi.level.code = 3
    mi.level.percentage = 50
    mi.cent = 99999
    mi.ps_coin = 100
    mi.psaward_deadline = int(time.time()) + 86400
    mi.spin_times = 3
    for i, (gid, sub, typ) in enumerate(GAMES):
        g = mi.game_info_group.add()
        g.id = gid; g.subid = sub; g.label = 2; setattr(g, 'class', 0)
        g.required_level = 0; g.type = typ; g.order = i
    return mi

def system_info():
    si = pb.SystemInfo()
    si.ps_coin_value = 1
    si.accounting_unit = 1
    si.degrade_check_bet = 500
    return si

def login_recall():
    r = pb.LoginRecall()
    r.msg_id = pb.kLoginRecall
    r.error_code = pb.kSuccess
    r.token = 'dev-lobby-token'
    r.member_info.CopyFrom(member_info())
    r.system_info.CopyFrom(system_info())
    return r

async def handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type != web.WSMsgType.BINARY:
            continue
        hdr = pb.Header()
        try:
            hdr.ParseFromString(msg.data)
        except Exception:
            continue
        mid = hdr.msg_id
        if mid == pb.kLoginCall:
            await ws.send_bytes(login_recall().SerializeToString())
        elif mid == pb.kMailCall:
            c = pb.MailCall(); c.ParseFromString(msg.data)
            r = pb.MailRecall(); r.msg_id = pb.kMailRecall; r.error_code = pb.kSuccess; r.mail_id = c.mail_id
            await ws.send_bytes(r.SerializeToString())
        elif mid == pb.kBigChallengeCall:
            r = pb.BigChallengeRecall(); r.msg_id = pb.kBigChallengeRecall; r.error_code = pb.kSuccess
            r.member_info.CopyFrom(member_info())
            await ws.send_bytes(r.SerializeToString())
        elif mid == pb.kSuicideCall:
            pass
    return ws

def main():
    app = web.Application()
    app.router.add_get('/lobby', handler)
    print('ps-lobby ws stub listening 127.0.0.1:8084/lobby', flush=True)
    web.run_app(app, host='127.0.0.1', port=8084, print=None)

if __name__ == '__main__':
    main()