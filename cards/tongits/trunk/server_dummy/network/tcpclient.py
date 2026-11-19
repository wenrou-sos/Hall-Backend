#!/usr/bin/env python
# coding=utf-8

from network import connection as conn
from network.message import *
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.queues import Queue
from tornado import gen
from tornado.tcpclient import TCPClient
from utils import *

class MYTCPClient(object):
    def __init__(self, szIp, nPort): 
        INFO("远程连接TCP客户端开始初始化")
        self.mMsgQueue = Queue()  # 消息队列
        self.mMsgDispatcher = MsgDispatcher()
        self.mCloseCallback = None
        self.mLinkCallBack = None
        self.bEnable = False
        self.mC = None
        self.mIP = szIp
        self.mPORT = nPort
        #发送心跳包
        self.mHbTimer = PeriodicCallback(self.OnSendHbMsg,5 * 1000)
        self.mHbTimer.start()

    @gen.coroutine
    def Connect(self)->bool:
        stream = None
        try:
            stream = yield TCPClient().connect( self.mIP, self.mPORT, timeout=2)
        except:
            return False
        if stream is None:
            return False
        self.mC = conn.Connection(self, stream, {self.mIP, self.mPORT}, 1, conn.CT_CLIENT)
        self.HandleMessage()
        return True

    def Close(self):
        if self.mC is not None and self.bEnable:
            self.mC.SafeClose()

    # 参数校验 ip: str, port: int
    def VerifyArgs(self, param):
        if "ip" not in param:
            param["ip"] = "127.0.0.1"
        for p in ["ip", "port"]:
            if p not in param:
                raise ArgsMissingError("远程服务器连接配置参数缺失")
        return True

    # 发送心跳包
    def OnSendHbMsg(self):
        if self.mC is not None and self.bEnable:
            self.mC.SendMsg(0, 1)

    # 设置消息处理初始化函数
    def AddHandler(self, *args):
        for func in args:
            if callable(func) is True:
                func(self.mMsgDispatcher)

    # 设置断开连接回调函数
    def SetCloseHandler(self, close_callback):
        self.mCloseCallback = close_callback

    def SetLinkHandler(self, link_callback):
        self.mLinkCallBack = link_callback

    def OnTMShowMsgQueue(self):
        msgQueueSize = self.mMsgQueue.qsize()
        if msgQueueSize > 10:
            INFO("TCPClient--消息队列长度：%d", msgQueueSize)

    # 消息处理
    @gen.coroutine
    def HandleMessage(self):
        while True:
            try:
                pMsg = yield self.mMsgQueue.get()
                if (pMsg.nMsgType == eMsgType.LINK_TYPE):
                    DEBUG("远程连接TCP客户端连接成功: %s", pMsg.mConn.sAddress)
                    self.bEnable = True
                    if self.mLinkCallBack is not None:
                        self.mLinkCallBack(pMsg.mConn)
                elif (pMsg.nMsgType == eMsgType.CLOSE_TYPE):
                    DEBUG("远程连接TCP客户端断开连接: %s", pMsg.mConn.sAddress)
                    self.bEnable = False
                    if self.mCloseCallback is not None:
                        self.mCloseCallback(pMsg.mConn)
                elif (pMsg.nMsgType == eMsgType.READ_TYPE):
                    #DEBUG("收到消息: %d,%d", pMsg.wMainId, pMsg.wSubId)
                    if self.mMsgDispatcher is not None:
                        self.mMsgDispatcher.dispatch(pMsg.mConn, pMsg.wMainId, pMsg.wSubId, pMsg.mData,
                                                     pMsg.nSize)
            except:
                PrintEXC()
                continue

    @gen.coroutine
    def OnLinkEvent(self, conn):
        yield self.mMsgQueue.put(stMessage(eMsgType.LINK_TYPE, conn))

    @gen.coroutine
    def OnCloseEvent(self, conn):
        yield self.mMsgQueue.put(stMessage(eMsgType.CLOSE_TYPE, conn))

    @gen.coroutine
    def OnReadEvent(self, conn, wMainId, wSubId, pData, size):
        yield self.mMsgQueue.put(stMessage(eMsgType.READ_TYPE, conn, wMainId, wSubId, pData, size))

    # 发送消息
    def SendProtoMsg(self, wMainId, wSubId, sPb):
        if self.mC is not None and self.bEnable:
            self.mC.SendProtoMsg(wMainId, wSubId, sPb)

    # 发送消息
    def SendMsg(self, wMainId, wSubId, pData = None):
        if self.mC is not None and self.bEnable:
            self.mC.SendMsg(wMainId, wSubId, pData)

@gen.coroutine
def CreateConnect():
    c = MYTCPClient("192.168.1.106", 9111)
    yield c.Connect()

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s -%(levelname)s: %(message)s')  # format='%(asctime)s -%(filename)s(line:%(lineno)d) -%(levelname)s: %(message)s')
    logger = logging.getLogger()
    CreateConnect()
    IOLoop.current().start()
