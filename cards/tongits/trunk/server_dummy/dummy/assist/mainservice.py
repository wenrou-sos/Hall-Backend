
import os
import sys
import json
import time
import asyncio
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from urls import sMainUrls
from redisassist import RDSPGuard
from mysqlassist import MYPGuard
from dbtask import TaskQueue
from gmproc import ConfigRPRef
from utils import *

class MainServiceError(Exception):
    pass

class MainService(Application):

    @classmethod
    def StartService(cls, **options):
        service = cls(**options)
        service.InitComponents()
        service.Start()

    def __init__(self, **options):
        super(MainService, self).__init__(sMainUrls, **options)

        self.mPort = 55555
        self.mHTTPService = None
        self.mRPGuard = None
        self.mMYPGuard = None
        self.mTaskProcCnt = 1
        self.mRunning = False

    @property
    def Service(self):
        return self.mHTTPService

    @property
    def RPGuard(self):
        return self.mRPGuard

    @property
    def MYPGuard(self):
        return self.mMYPGuard

    def Start(self):
        if self.mRunning:
            Warn("MainService已启动！")

        self.mPort = int(sys.argv[1]) if len(sys.argv) > 1 else self.mPort
        self.mHTTPService = HTTPServer(self)
        self.mHTTPService.listen(self.mPort)
        self.mRunning = True
        Info("[服务启动成功][端口：%d]" % self.mPort)
        IOLoop.instance().start()

    def InitComponents(self):
        data = self.settings

        if "dbg_lv" in data:
            DebugLevel.Set(int(data["dbg_lv"]))

        if "redis_dbg_lv" in data:
            RDSPGuard.SetDebugLevel(int(data["redis_dbg_lv"]))

        if "mysql_dbg_lv" in data:
            MYPGuard.SetDebugLevel(int(data["mysql_dbg_lv"]))

        if "redis_cfg_path" in data:
            if not self.InitRPGuard(data["redis_cfg_path"]):
                raise MainServiceError("初始化Redis失败！")
            RDSPGuard.ProcWith(self.ConfigAllRP)
        else:
            raise MainServiceError("缺少Redis配置路径！")

        if "mysql_cfg_path" in data:
            if not self.InitMYPGuard(data["mysql_cfg_path"]):
                raise MainServiceError("初始化MySQL失败！")
            MYPGuard.ProcWith(self.ConfigAllMYP)
        else:
            raise MainServiceError("缺少MySQL配置路径！")

        if "port" in data:
            self.mPort = int(data["port"])

        if "tsk_proc_cnt" in data:
            self.mTaskProcCnt = int(data["tsk_proc_cnt"])

        ConfigRPRef()
        self.CreateTask(self.ProcTasks())

    def InitRPGuard(self, path):
        if self.mRPGuard is not None:
            return False
        self.mRPGuard = RDSPGuard.LoadByFile(path)
        return self.mRPGuard is not None

    def InitMYPGuard(self, path):
        if self.mMYPGuard is not None:
            return False
        self.mMYPGuard = MYPGuard.LoadByFile(path)
        return self.mMYPGuard is not None

    def OnPubMsg(self, pb_proxy, msg_type, ptn, chl, data):
        if msg_type == "message" or msg_type == "pmessage":
            Log("收到通知：", pb_proxy.Proxy.Name, chl, data)
            TaskQueue.Push(pb_proxy.Proxy.Name, chl, data)

    def ConfigAllRP(self, rp):
        pubsub = rp.PubSub
        if pubsub is not None:
            pubsub.OnPubMsgCB = self.OnPubMsg
            self.CreateTask(pubsub.AsyncUpdate())
        libgrd = rp.LibGrd
        if libgrd is not None:
            self.CreateTask(libgrd.AsyncUpdate())

    def ConfigAllMYP(self, myp):
        self.CreateTask(myp.AsyncUpdate())

    def CreateTask(self, co):
        IOLoop.current().asyncio_loop.create_task(co)

    def ShutdownService(self):
        PeriodicCallback(self.FinalShutdown, 3000).start()

    def FinalShutdown(self):
        Info("服务关闭！")
        IOLoop.current().stop()
        self.mHTTPService.stop()

    async def ProcTasks(self):
        std_cnt = self.mTaskProcCnt
        itvl = 0.02
        last_rec_time = 0
        while True:
            beg_time = time.time()
            proced = TaskQueue.DoAllTask(proc_cnt = std_cnt)

            i_beg_t = int(beg_time)
            if i_beg_t % 300 == 0 and i_beg_t != last_rec_time:
                Info("[TQ:" + str(len(TaskQueue.sQueue)) + "][TPPF:" + str(std_cnt) + "]")
                if i_beg_t % 1800 == 0:
                    TaskQueue.Push("game", "db_save_onlstatus", str(i_beg_t), immed = True)
                last_rec_time = i_beg_t

            elapse = time.time() - beg_time
            if elapse < itvl:
                if proced >= std_cnt and elapse < itvl * (1 - std_cnt / (1 + std_cnt)):
                    std_cnt += 1
                await asyncio.sleep(itvl - elapse)
            else:
                std_cnt = 1
                await asyncio.sleep(0.001)