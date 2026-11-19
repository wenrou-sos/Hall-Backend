# -*- coding: utf-8 -*-
"""A 组收尾：PSC-ON-00002/00006（Cocos Creator，无 src/g_message.js）的 WS 在
assets/Script/AppManager/NetManager.js login() 内拼接：Constants.wsExtend + ip + ":" + port + "/service/"。
按 g_message.js 同款做法固定为 ws://127.0.0.1:8910/service/（dummy server）。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
old = 'this.url = Constants.wsExtend + ip + ":" + port + "/service/";'
new = 'this.url = "ws://127.0.0.1:8910/service/"; // local dummy server (A组收尾)'
for pid in ('PSC-ON-00002', 'PSC-ON-00006'):
    p = r'D:\games_wc\%s\trunk\assets\Script\AppManager\NetManager.js' % pid
    d = open(p, encoding='utf-8').read()
    if new in d:
        print(pid, 'already patched')
        continue
    assert old in d, pid
    d = d.replace(old, new, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print(pid, 'NetManager.js WS -> ws://127.0.0.1:8910/service/')