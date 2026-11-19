# -*- coding: utf-8 -*-
"""本地 stub apiserver(:81)：替代依赖 CloudSQL/Firebase/远程PS 的原版 apiserver。
契约与原版一致: {"apiresult":0,"serverdata":{},"clientdata":{...}}。
lobbyserver(原版) 通过 HTTP 调本服务；游戏列表/launchurl 指向本地可跑游戏。
"""
import aiohttp.web as web
import json, urllib.parse

MEMBERID = 10001
FISH_URL = 'http://127.0.0.1:8080/?access_token=devlocaltoken'

GAMELIST = [
    {'gameid': 'PSF-ON-00001', 'gameindex': 1, 'gamename': 'Fish Thunder', 'gametype': 0,
     'chapterid': 1, 'hot': 1, 'new': 1, 'master': 0, 'avatar': 0, 'pic': '', 'status': 0,
     'gameserverUrl': FISH_URL, 'launchurl': FISH_URL},
]

def ok(clientdata=None, serverdata=None):
    return web.json_response({'apiresult': 0, 'serverdata': serverdata or {}, 'clientdata': clientdata or {}})

async def handler(request):
    path = request.rel_url.path
    seg = [s for s in path.split('/') if s]
    op = seg[0] if seg else ''
    q = request.rel_url.query
    if op == 'getmyip':
        return web.Response(text='127.0.0.1', content_type='text/plain')
    if op == 'login':
        return ok({'result': 0, 'memberid': MEMBERID, 'nickname': 'DEV', 'avatar': 0,
                   'coin': 99999, 'silver': 0, 'level': 1, 'ver': 1, 'rer': 0,
                   'channelindex': 0, 'logintoken': seg[2] if len(seg) > 2 else '',
                   'registerflag': 0, 'fbavatar': '', 'fbnickname': 'DEV',
                   'actionnumbers': [], 'card': 0, 'silvercredit': 0, 'isguests': 1,
                   'isbindfb': 0, 'isbindacc': 0, 'isbindphone': 0, 'activenumber': 0,
                   'needtutorialflag': 0, 'specialactionurlnew': [],
                   'gameserverUrl': FISH_URL, 'gameserverUrl_silver': FISH_URL,
                   'lobbyaction': [], 'headline': []})
    if op == 'getgamelist':
        return ok({'gamelist': GAMELIST, 'chapterlist': [{'chapterid': 1, 'chaptername': 'All'}],
                   'normalsort': [1], 'mastersort': [], 'hotsort': [1], 'newsort': [1]})
    if op == 'joingame':
        gid = q.get('gameid', 'PSF-ON-00001')
        return ok({'result': 0, 'gameid': gid, 'gametype': int(q.get('gametype', 0)),
                   'gameserverUrl': FISH_URL, 'launchurl': FISH_URL, 'gameserverUrl_silver': FISH_URL})
    if op == 'getmemberinfo':
        return ok({'memberid': MEMBERID, 'nickname': 'DEV', 'avatar': 0, 'coin': 99999,
                   'silver': 0, 'level': 1, 'ver': 1, 'rer': 0, 'vip': 0})
    if op == 'serverinfo':
        return ok({'serverstate': 0, 'resourceserveruri': '', 'androidver': '1.0.0', 'iosver': '1.0.0',
                   'message_title': '', 'message_detail': '', 'androidurl': '', 'iosurl': '',
                   'rerobject': {'1.4.15': {'1.2.27': {'rer': '1.2.27', 'size': 0}}}, 'needask': 0, 'useagreement': 0, 'privacyagreement': '',
                   'gameagreement': '', 'gameagreement2': '', 'tips': [],
                   'notice': '', 'promotion': '', 'version': '1.0.0'})
    if op == 'setlobbyip':
        return ok()
    if op == 'logout':
        return ok()
    # 其余启动期调用一律回 success + 空/最小 clientdata，前端缺字段再按控制台补
    return ok({'result': 0})

def main():
    app = web.Application()
    app.router.add_route('GET', '/{tail:.*}', handler)
    app.router.add_route('POST', '/{tail:.*}', handler)
    print('stub-apiserver listening 127.0.0.1:81', flush=True)
    web.run_app(app, host='127.0.0.1', port=81, print=None)

if __name__ == '__main__':
    main()