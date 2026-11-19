#!/usr/bin/env python
# coding=utf-8

from tornado import ioloop
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado.queues import Queue
from tornado import gen
import struct
import sys
import time

CT_CLIENT = 0
CT_SERVER = 1

# 会话
class Connection(object):
    def __init__(self, server_attempter, stream, address, socketId, ct = CT_SERVER):
        self.bEnable = True
        self.bExit = False
        self.nSocketID = socketId
        self.nType = ct  # 1：服务器 0：客户端
        self.mStream = stream
        self.sAddress = address
        self.nSvrID = ""  # 连接附加参数
        self.nTickCount = time.time()  # 心跳检测
        self.mDetectTimer = ioloop.PeriodicCallback(self.onHBCheck, 1000)  # 这里的时间是毫秒
        self.mDetectTimer.start()
        self.mServerAttempter = server_attempter
        self.mSendQueue = Queue()
        self.mStream.set_close_callback(self.OnCloseCallback)
        self.mStream.set_nodelay(True)
        # 事件通知
        self.mServerAttempter.OnLinkEvent(self)
        self.OnReadCoroutine()
        self.OnWriteCoroutine()

    def GetIP(self):
        return self.sAddress[0]

    def GetPort(self):
        return self.sAddress[1]

    def GetID(self):
        return self.nSocketID

    def IsExit(self):
        return self.bExit

    def SetExit(self, ext):
        self.bExit = ext

    def SetServId(self, servId):
        self.nSvrID = servId

    def GetServId(self):
        return self.nSvrID

    @gen.coroutine
    def SafeClose(self):
        yield self.mSendQueue.put("0")

    # 发送PB数据
    @gen.coroutine
    def SendProtoMsg(self, wMainId, wSubId, sPB):
        if self.bEnable == True:
            buffer = sPB.SerializeToString()
            ss = struct.pack('<BBHHH', 102, 0, 8 + len(buffer), wMainId, wSubId)
            ss = ss + buffer
            yield self.mSendQueue.put(ss)

    # 发送Buffer数据
    @gen.coroutine
    def SendMsg(self, wMainId, wSubId, pData=None):
        if self.bEnable == True:
            packLen = 8 if pData == None else (8 + len(pData))
            ss = struct.pack('<BBHHH', 102, 0, packLen, wMainId, wSubId)
            if (pData is not None) and isinstance(pData, bytes) == True:
                ss = ss + pData
            yield self.mSendQueue.put(ss)

    @gen.coroutine
    def OnReadCoroutine(self):
        while True:
            try:
                sInfoBytes = yield self.mStream.read_bytes(8)  # 读包头
                version, checkcode, nSize, wMainId, wSubId = struct.unpack('<BBHHH', sInfoBytes)
                if wMainId == 0 and wSubId == 1:  # 心跳包
                    self.nTickCount = time.time()
                    if self.nType == CT_SERVER:
                        self.SendMsg(0, 1)
                    continue
                sBodyBytes = b''
                nBodySize = nSize - 8
                if nBodySize > 0:
                    sBodyBytes = yield self.mStream.read_bytes(nBodySize)  # 读取包体
                self.mServerAttempter.OnReadEvent(self, wMainId, wSubId, sBodyBytes, nBodySize)
            except StreamClosedError:
                break

    @gen.coroutine
    def OnWriteCoroutine(self):
        while True:
            pMsg = yield self.mSendQueue.get()
            try:
                if len(pMsg) == 1:
                    self.mStream.close()
                else:
                    self.mStream.write(pMsg)
            except StreamClosedError:
                break

    def onHBCheck(self):
        if time.time() - self.nTickCount >= 30:
            self.mStream.close()
            self.mDetectTimer.stop()

    def OnCloseCallback(self):
        self.mServerAttempter.OnCloseEvent(self)
        self.SendMsg(0, 0, b"0")  # 通知写停止,没有这个可能会导致onWriteCoroutine不会退出
        self.bEnable = False
        self.mDetectTimer.stop()


# 服务器
class AppServer(TCPServer):
    idAlloctor = 0

    # @gen.coroutine
    def handle_stream(self, stream, address):
        self.idAlloctor = self.idAlloctor + 1
        if self.idAlloctor >= sys.maxsize:
            self.idAlloctor = 1
        Connection(self.mServerAttempter, stream, address, self.idAlloctor)
        """
        while True:
            try:
                data = yield stream.read_bytes(8) #stream.read_until(b"\n")
                print("recv data : ", data)
                yield stream.write(data)
            except StreamClosedError:
                break
                """

    def SetServerAttemper(self, server_attempter):
        self.mServerAttempter = server_attempter
