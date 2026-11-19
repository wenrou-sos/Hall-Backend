# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\main.js'
d = open(p, encoding='utf-8').read()
start = d.find('pslb.BuildWebSocket(function(websocket){')
end_marker = '    }\n    cc.LoaderScene.preload(g_resources, __go, this);'
end = d.find(end_marker)
assert start >= 0 and end >= 0, (start, end)
raw = (
    "var ws = new WebSocket('ws://127.0.0.1:8084/lobby');\n"
    "        ws.binaryType = 'arraybuffer';\n"
    "        ws.onopen = function(){ var call = new pslb.proto.LoginCall(); call.token = 'dev'; ws.send(call.toArrayBuffer()); };\n"
    "        ws.onmessage = function(m){\n"
    "            var recall = pslb.proto.LoginRecall.decode(m.data);\n"
    "            if (recall.error_code == pslb.proto.ErrorCode.kSuccess) {\n"
    "                pslb.memberInfo.setWithProto(recall.member_info);\n"
    "                pslb.systemInfo.setWithProto(recall.system_info);\n"
    "                pslb.mail.setWithProto(recall.mail_box);\n"
    "                pslb.bannerInfo.setWithProto(recall.banner_info);\n"
    "                cc.director.runScene(new LobbyScene());\n"
    "            }\n"
    "        };\n"
)
d = d[:start] + raw + d[end:]
open(p, 'w', encoding='utf-8').write(d)
print('main.js __go now uses raw WS login')