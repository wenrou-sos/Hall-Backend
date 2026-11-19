import sys
import os
import hashlib

sys.path.append(('%s/../..' % (os.getcwd())))
sys.path.append(('%s/../../dbhelper'%(os.getcwd())))
sys.path.append(('%s/../../proto/dummy/main_cmd'%(os.getcwd())))
sys.path.append(('%s/../../proto/dummy/client_lobby_game'%(os.getcwd())))

from urllib import parse, request
import json
import asyncio
import threading
from queue import Queue
import time

from c_g_game_pb2 import *
from tornado.websocket import websocket_connect
import tornado.ioloop
import struct

def DoRequest():
    params = {
        "op" : 17,
        "ex" : json.dumps({"uid":1008, "t":0, "addr":"8.8.8.8"})
    }
    d = parse.urlencode(params).encode(encoding='utf-8')

    header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}
    url='http://192.168.1.106:9100/gmproc/'
    req = request.Request(url = url, data = d, headers = header_dict)
    res = request.urlopen(req)
    res = res.read()
    jdata = json.loads(res.decode(encoding='utf-8'))
    return jdata

sWSHDR = None

def RecvMsg(msg):
    print("Server back:", msg)
    try:
        if len(msg) < 8:
            return
        head_stream = msg[:8]
        ver, chk, size, main, sub = struct.unpack('<BBHHH', head_stream)
        body = msg[8:]
        print("Head：", ver, chk, size, main, sub)
        recv_msg = msg_user_login_ret()
        recv_msg.ParseFromString(body)
        print("Body：", recv_msg)
    except:
        pass

def WSConnected(*args, **kwargs):
    global sWSHDR
    sWSHDR = args[0].result()
    print("连接成功，开始验证！")
    main = 30
    sub = 2001
    send_msg = msg_user_login()
    send_msg.uuid = 1001
    send_msg.token = 1001
    stream = send_msg.SerializeToString()
    sWSHDR.write_message(struct.pack('<BBHHH', 102, 0, 8 + len(stream), main, sub) + stream, binary = True)

def ConnByWS():
    websocket_connect(
        "ws://192.168.1.106:10025/service/",
        callback = WSConnected,
        on_message_callback = RecvMsg
        )
    tornado.ioloop.IOLoop.instance().start()

sCode = '''
return 1 + 2
'''
def DoSupop():
    key = "imaohw"
    tmp1 = hashlib.md5(sCode.encode()).hexdigest()
    tmp2 = hashlib.md5(key.encode()).hexdigest()

    send_sign = ""
    if tmp1 > tmp2:
        send_sign = tmp2[:16] + tmp1[16:]
    else:
        send_sign = tmp1[:16] + tmp2[16:]

    params = {
        "sign" : send_sign,
        "ctn" : sCode
    }

    d = parse.urlencode(params).encode(encoding='utf-8')

    header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}
    url='http://192.168.1.106:9098/supop/'
    req = request.Request(url = url, data = d, headers = header_dict)
    res = request.urlopen(req)
    jdata = json.loads(res.read().decode(encoding='utf-8'))
    return jdata

import requests

def DoHTTPSRequest():
    '''
    header_dict = {
    'Host' : '192.168.1.106',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'
    }
    url='https://192.168.1.106:9159/?_input_charset=utf-8&action=serverlist&channel=apple&gameid=1'
    req = request.Request(url = url, headers = header_dict)
    res = request.urlopen(req)
    res = res.read()
    jdata = json.loads(res.decode(encoding='utf-8'))
    return jdata
    '''
    header_dict = {
    'Host' : 'jinle-api.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'
    }
    res = requests.get('https://192.168.1.106:9159/?_input_charset=utf-8&action=serverlist&channel=apple&gameid=1', headers = header_dict, verify = False)
    res = res.content
    jdata = json.loads(res.decode(encoding='utf-8'))
    return jdata

if __name__ == "__main__":
    # print(DoRequest())
    # ConnByWS()
    # print(DoSupop())
    print(DoHTTPSRequest())

