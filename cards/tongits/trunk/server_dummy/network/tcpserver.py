#!/usr/bin/env python
# coding=utf-8

from network import connection
from network.message import *
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from tornado import gen
from utils import *

"""
        self.mConnects = [Connection(self, socketId+1) for socketId in range(conns)]     # 连接管理
        self._empty_connects = self.mConnects  # 空闲连接
        self._active_connects = []  # 运行中的连接

        idx = -1
        for i in range(len(self.mConnects)):
            if self.mConnects[i]._address == message._conn._address:
                idx = i
                break
        if idx > 0:
            self._active_connects.pop(idx)
"""


class ArgsMissingError(Exception):
    pass


class TCPServer(object):
    def __init__(self):
        pass

    def InitServer(self, kvargs):  # servport: int, servid: int
        INFO("服务器正在初始化......")
        if self.VerifyArgs(kvargs) == False:
            return
        # self.__servid = kvargs["id"]
        self.nMaxConnection = kvargs["max_connections"]
        self.mMsgQueue = Queue()  # 消息队列
        self.mMsgDispatcher = MsgDispatcher()
        self.mClosedfunc = None
        self.mLinkedfunc = None
        self.mConnects = {}
        self.mServer = connection.AppServer()
        self.mServer.SetServerAttemper(self)
        self.mServer.listen(kvargs["port"])
        self.HandleMessage()
        INFO("TCPServer init complete, port - %d", kvargs["port"])

    def CloseServer(self):
        self.mServer.stop()

    # 参数校验
    def VerifyArgs(self, param):
        if "max_connections" not in param:
            param["max_connections"] = 2048
        for p in ["port", "max_connections"]:
            if p not in param:
                raise ArgsMissingError("服务器配置参数缺失")
        return True

    # 设置消息处理初始化函数
    def AddHandler(self, *args):
        for func in args:
            if callable(func) is True:
                func(self.mMsgDispatcher)

    # 设置断开连接回调函数
    def SetCloseHandler(self, close_callback):
        self.mClosedfunc = close_callback

    def SetLinkedHandler(self, linked_callback):
        self.mLinkedfunc = linked_callback

    def SetDefaultHandler(self, default_callback):
        self.mMsgDispatcher.set_default(default_callback)

    def OnTMShowMsgQueue(self):
        msgQueueSize = self.mMsgQueue.qsize()
        if msgQueueSize > 10:
            INFO("TCPServer--消息队列长度：%d", msgQueueSize)

    def OnShowNetworkStatus(self):
        INFO("当前连接数：%d, 消息队列长度：%d", len(self.mConnects), self.mMsgQueue.qsize())

    # 消息处理

    @gen.coroutine
    def HandleMessage(self):
        while True:
            try:
                message = yield self.mMsgQueue.get()
                if (message.nMsgType == eMsgType.LINK_TYPE):
                    if len(self.mConnects) >= self.nMaxConnection:
                        message.mConn.SafeClose()
                        return
                    self.mConnects[message.mConn.nSocketID] = message.mConn
                    DEBUG("新连接: %s, socketId: %d", message.mConn.sAddress, message.mConn.nSocketID)
                    if self.mLinkedfunc is not None \
                            and callable(self.mLinkedfunc) is True:
                        self.mLinkedfunc(message.mConn)
                elif (message.nMsgType == eMsgType.CLOSE_TYPE):
                    DEBUG("断开连接: %s", message.mConn.sAddress)
                    if self.mClosedfunc is not None \
                            and callable(self.mClosedfunc) is True:
                        self.mClosedfunc(message.mConn)
                    if message.mConn.nSocketID in self.mConnects:
                        self.mConnects.pop(message.mConn.nSocketID)
                elif (message.nMsgType == eMsgType.READ_TYPE):
                    self.mMsgDispatcher.dispatch(message.mConn, message.wMainId, message.wSubId, message.mData,
                                                      message.nSize)
            except:
                continue

    @gen.coroutine
    def OnLinkEvent(self, conn):
        yield self.mMsgQueue.put(stMessage(eMsgType.LINK_TYPE, conn))

    @gen.coroutine
    def OnCloseEvent(self, conn):
        yield self.mMsgQueue.put(stMessage(eMsgType.CLOSE_TYPE, conn))

    @gen.coroutine
    def OnReadEvent(self, conn, wMainId, wSubId, pData, nSize):
        yield self.mMsgQueue.put(stMessage(eMsgType.READ_TYPE, conn, wMainId, wSubId, pData, nSize))

    # 发送广播
    def SendToAllProtoMsg(self, wMainId, wSubId, sPb):
        for socketId, conn in self.mConnects.items():
            conn.SendProtoMsg(wMainId, wSubId, sPb)

    # 发送消息
    def SendProtoMsg(self, socketid, wMainId, wSubId, sPb):
        if socketid in self.mConnects:
            conn = self.mConnects[socketid]
            conn.SendProtoMsg(wMainId, wSubId, sPb)

    def SendMsg(self, socketid, wMainId, wSubId, pData):
        if socketid in self.mConnects:
            conn = self.mConnects[socketid]
            conn.SendMsg(wMainId, wSubId, pData)

    # 发送指定服务器消息
    def SendProtoMsgByServerId(self, serverid, wMainId, wSubId, sPb):
        for socketId, conn in self.mConnects.items():
            if conn.GetServId() == serverid:
                conn.SendProtoMsg(wMainId, wSubId, sPb)

    def SendProtoMsgToAllServer(self, wMainId, wSubId, sPb):
        for socketId, conn in self.mConnects.items():
            if len(conn.GetServId()) > 0:
                conn.SendProtoMsg(wMainId, wSubId, sPb)

    def SafeClose(self, socketid):
        if socketid in self.mConnects:
            conn = self.mConnects[socketid]
            conn.SafeClose()

    # 返回连接
    def Get(self, id):
        if id in self.mConnects:
            return self.mConnects[id]
        return None

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s -%(levelname)s: %(message)s')  # format='%(asctime)s -%(filename)s(line:%(lineno)d) -%(levelname)s: %(message)s')
    logger = logging.getLogger()

    kvargs = {"id": 1, "port": 8000}
    svr = TCPServer()
    svr.InitServer(kvargs)

    IOLoop.current().start()
