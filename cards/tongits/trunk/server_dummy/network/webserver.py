#!/usr/bin/env python
# coding=utf-8

import struct
from tornado import gen
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.queues import Queue
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from network.message import *
from utils import *


class WSException(Exception):
    pass

class WSConnection(WebSocketHandler):
    nAllocationId = 0
    def __init__(self, *args, **kwargs):
        super(WSConnection, self).__init__(*args, **kwargs)
        self.mIgnOri = int(self.application.settings["ign_ori"]) == 1
        self.__AllocId()
        self.mServer = self.application
        self.mSendQueue = Queue()
        self.bEnable = False
        self.nTickCount = 0
        self.nReceivePacks = 0
        self.nReceiveBytes = 0
        self.nSendPacks = 0
        self.nSendBytes = 0
        self.sAddress = '127.0.0.1'

    def __AllocId(self):
        self.nSocketID = WSConnection.nAllocationId
        WSConnection.nAllocationId += 1

    def GetID(self):
        return self.nSocketID

    def GetIP(self):
        return self.sAddress

    @gen.coroutine
    def SafeClose(self):
        yield self.mSendQueue.put("0")

    # 发送PB数据
    @gen.coroutine
    def SendProtoMsg(self, wMainId, wSubId, sPB):
        if not self.bEnable:
            return
        buffer = sPB.SerializeToString()
        ss = struct.pack('<BBHHH', 102, 0, 8 + len(buffer), wMainId, wSubId)
        ss = ss + buffer
        yield self.mSendQueue.put(ss)

    # 发送Buffer数据
    @gen.coroutine
    def SendMsg(self, wMainId, wSubId, pData=None):
        if not self.bEnable:
            return
        packLen = 8 if pData == None else (8 + len(pData))
        ss = struct.pack('<BBHHH', 102, 0, packLen, wMainId, wSubId)
        if (pData is not None) and isinstance(pData, bytes) == True:
            ss = ss + pData
        yield self.mSendQueue.put(ss)

    @gen.coroutine
    def OnWriteCoroutine(self):
        while True:
            bufferBytes = yield self.mSendQueue.get()
            try:
                if len(bufferBytes) == 1:
                    self.close()
                else:
                    self.write_message(bufferBytes, binary=True)
            except:
                break

    async def open(self):
        try:
            self.bEnable = True
            self.sAddress = self.request.remote_ip
            self.OnWriteCoroutine()
            self.mServer.OnLinkEvent(self)
        except:
            self.close()

    async def on_message(self, message):
        try:
            nVersion, nCheckCode, nSize, wMainId, wSubId = struct.unpack('<BBHHH', message[:8])
            self.nReceivePacks += 1
            self.nReceiveBytes += nSize
            if wMainId == 0 and wSubId == 1:  # 心跳包
                self.nTickCount = GetServerTime()
                self.SendMsg(0, 1)
                return
            self.mServer.OnReadEvent(self, wMainId, wSubId, message[8:], nSize-8)
        except:
            self.close()

    def on_close(self):
        self.SendMsg(0, 0, b"0")
        self.mServer.OnCloseEvent(self)
        self.bEnable = False

    def check_origin(self, ori):
        if self.mIgnOri:
            return True
        else:
            return super(WSConnection, self).check_origin(ori)

class WebServer(Application):
    @classmethod
    def Create(cls, sUrls, **options):
        server = cls(sUrls, **options)
        server.Initizlize()
        return server

    def __init__(self, sUrls, **options):
        super(WebServer, self).__init__(sUrls, **options)
        self.mHTTPService = None
        self.mMsgQueue = Queue()    # 消息队列
        self.mConnects = {}
        self.mMsgDispatcher = MsgDispatcher()
        self.mLinkedfunc = None
        self.mClosedfunc = None
        self.mPort = 5555
        self.mMaxConnection = 2048

    def Initizlize(self):
        mConfigs = self.settings
        if "port" not in mConfigs:
            raise WSException("缺少port配置")
        if "max_connections" in mConfigs:
            self.mMaxConnection = mConfigs["max_connections"]
        self.mPort = mConfigs["port"]
        if "ssl" in self.settings:
            self.mHTTPService = HTTPServer(self, ssl_options = self.settings["ssl"])
        else:
            self.mHTTPService = HTTPServer(self)
        self.mHTTPService.listen(mConfigs["port"])
        self.HandleMessage()
        INFO("WSServer init complete, port - %d", self.mPort)

    def CloseServer(self):
        self.mHTTPService.stop()

    # 设置消息处理初始化函数
    def AddHandler(self, *args):
        for func in args:
            if callable(func) is True:
                func(self.mMsgDispatcher)

    def SetCloseHandler(self, close_callback):
        self.mClosedfunc = close_callback

    def SetLinkedHandler(self, linked_callback):
        self.mLinkedfunc = linked_callback

    def SetDefaultHandler(self, default_callback):
        self.mMsgDispatcher.set_default(default_callback)

    # 消息处理
    @gen.coroutine
    def HandleMessage(self):
        while True:
            try:
                pMsg = yield self.mMsgQueue.get()
                if (pMsg.nMsgType == eMsgType.LINK_TYPE):
                    if len(self.mConnects) >= self.mMaxConnection:
                        pMsg.mConn.SafeClose()
                        return
                    self.mConnects[pMsg.mConn.GetID()] = pMsg.mConn
                    if self.mLinkedfunc is not None \
                            and callable(self.mLinkedfunc) is True:
                        self.mLinkedfunc(pMsg.mConn)
                elif (pMsg.nMsgType == eMsgType.CLOSE_TYPE):
                    if self.mClosedfunc is not None \
                            and callable(self.mClosedfunc) is True:
                        self.mClosedfunc(pMsg.mConn)
                    if pMsg.mConn.GetID() in self.mConnects:
                        self.mConnects.pop(pMsg.mConn.GetID())
                elif (pMsg.nMsgType == eMsgType.READ_TYPE):
                    self.mMsgDispatcher.dispatch(pMsg.mConn, pMsg.wMainId, pMsg.wSubId, pMsg.mData,
                                                 pMsg.nSize)
            except:
                continue

    @gen.coroutine
    def OnLinkEvent(self, ws):
        yield self.mMsgQueue.put(stMessage(eMsgType.LINK_TYPE, ws))

    @gen.coroutine
    def OnCloseEvent(self, ws):
        yield self.mMsgQueue.put(stMessage(eMsgType.CLOSE_TYPE, ws))

    @gen.coroutine
    def OnReadEvent(self, ws, wMainId, wSubId, pData, nSize):
        yield self.mMsgQueue.put(stMessage(eMsgType.READ_TYPE, ws, wMainId, wSubId, pData, nSize))

    def Get(self, id):
        if id in self.mConnects:
            return self.mConnects[id]
        return None

    def SafeClose(self, id):
        if id in self.mConnects:
            self.mConnects[id].SafeClose()

    def SendMsg(self, id, wMainId, wSubId, pData):
        if id in self.mConnects:
            self.mConnects[id].SendMsg(wMainId, wSubId, pData)

    def SendProtoMsg(self, id, wMainId, wSubId, sPb):
        if id in self.mConnects:
            self.mConnects[id].SendProtoMsg(wMainId, wSubId, sPb)

    def SendToAllProtoMsg(self, wMainId, wSubId, sPb):
        for id, ws in self.mConnects.items():
            ws.SendProtoMsg(wMainId, wSubId, sPb)

if __name__ == "__main__":
    mConfigs = {"port" : 5555, "max_connections" : 10}
    serv = WebServer.Create([(r"/service/", WSConnection)], **mConfigs)
    IOLoop.instance().start()

