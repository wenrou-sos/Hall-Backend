#!/usr/bin/env python
# coding=utf-8

def doCombinateId(wMainId: int, wSubId: int):
    return wMainId * 10000 + wSubId

class eMsgType(object):
    LINK_TYPE   = 1   # 新连接
    CLOSE_TYPE  = 2   # 关闭连接
    READ_TYPE   = 3   # 收到消息

class stMessage(object):
    def __init__(self, msgType, conn, wMainId=0, wSubId=0, pData=None, nSize=0):
        self.nMsgType = msgType
        self.mConn = conn
        self.wMainId = wMainId
        self.wSubId = wSubId
        self.mData = pData
        self.nSize = nSize


# 消息分发器：注册和处理
class MsgDispatcher(object):
    def __init__(self):
        self._registerd_handlers = {}
        self._default_func = None

    # 未知消息
    def set_default(self, func):
        self._default_func = func

    # 注册消息回调
    def registe(self, wMainId: int, wSubId: int, func):
        combId = doCombinateId(wMainId, wSubId)
        self._registerd_handlers[combId] = func

    # 取消注册
    def unregiste(self, wMainId: int, wSubId: int):
        combId = doCombinateId(wMainId, wSubId)
        if combId in self._registerd_handlers.keys():
            del self._registerd_handlers[combId]

    # 执行
    def dispatch(self, conn, wMainId: int, wSubId: int, data, size):
        combId = doCombinateId(wMainId, wSubId)
        callback_func = self._registerd_handlers.get(combId)
        if (callback_func != None):
            callback_func(conn, data, size)
        else:
            if self._default_func is not None:
                self._default_func(conn, wMainId, wSubId, data, size)


class MsgHandler(object):
    def __init__(self):
        pass

    def Initialize(self, dispatcher):
        pass

    def OnNetClose(self, conn):
        pass

    def OnReloadCfg(self):
        pass
