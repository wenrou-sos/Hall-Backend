import sys
import os

sys.path.append(('%s/../..' % (os.getcwd())))
sys.path.append(('%s/../../utils'%(os.getcwd())))
sys.path.append(('%s/../../dbhelper'%(os.getcwd())))
sys.path.append(('%s/../../proto/dummy/main_cmd'%(os.getcwd())))
sys.path.append(('%s/../../proto/dummy/client_lobby_game'%(os.getcwd())))

from urllib import parse, request
import json
import asyncio
import threading
from queue import Queue
import time
from utils import *
from main_cmd_pb2 import *
from error_pb2 import *
from c_g_game_pb2 import *
from l_g_game_pb2 import *
from c_l_lobby_pb2 import *

from c_g_game_pb2 import *
from tornado.websocket import websocket_connect
import tornado.ioloop
import struct

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
    Info("连接成功，开始登录！")

    send_msg = msg_user_login_ew()
    send_msg.channel = b'apple'
    send_msg.source = b'pc'
    send_msg.timestamp = b'123456789101'
    send_msg.uuid = b"00000001"
    send_msg.token = b'asdfghjkl'
    send_msg.username = b'111'
    stream = send_msg.SerializeToString()
    sWSHDR.write_message(struct.pack('<BBHHH', 102, 0, 8 + len(stream), e_msgid_game_login, e_cg_msgid_login) + stream, binary = True)

def ConnByWS():
    websocket_connect(
        "ws://192.168.1.106:13131/service/",
        callback = WSConnected,
        on_message_callback = RecvMsg
        )
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    # print(DoRequest())
    #ConnByWS()
    print(GetServerTimeMS())

