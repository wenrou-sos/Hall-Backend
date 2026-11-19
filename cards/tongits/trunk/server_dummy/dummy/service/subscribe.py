
from redisassist import RDSPGuard
from utils import *
from servlist import *
from c_l_lobby_pb2 import *

class SubscribecbInitError(Exception):
    pass

def OnRedisRunPubSubRecv(loop):
    pub_sub = RDSPGuard.RP("game").PubSub
    if pub_sub is not None:
        loop.asyncio_loop.create_task(pub_sub.AsyncUpdate())

def OnRedisRunLibGrdRecv(loop):
    lib_grd = RDSPGuard.RP("game").LibGrd
    if lib_grd is not None:
        loop.asyncio_loop.create_task(lib_grd.AsyncUpdate())

class SubscribecbHandler(object):
    def __init__(self):
        raise SubscribecbInitError("SubscribecbInitError无法被初始化")

    @classmethod
    def OnRedisSubGameOpenAndClose(cls, data: bytes, open: bool):
        try:
            Log("OnRedisSubGameOpenAndClose ------------", data, open)
            if data == None or isinstance(data, bytes) == False:
                return
            server_data = game_server_data()
            server_data.ParseFromString(data)
            if open == True:
                ServListMgr.AddServ(server_data)
            else:
                ServListMgr.DelServ(server_data)
        except:
            PrintEXC()

    @classmethod
    def OnRedisSubscribeCB(cls, pb_proxy, msg, ptn, chl, data):
        try:
            if chl == "dmsubgameopen":          # 子游戏开启通知
                cls.OnRedisSubGameOpenAndClose(data, True)
            elif chl == "dmsubgameclose":         # 子游戏关闭通知
                cls.OnRedisSubGameOpenAndClose(data, False)
        except:
            PrintEXC()

