from tornado.ioloop import IOLoop
from redisassist import RDSPGuard, EventRP, UserRP
from mysqlassist import MYPGuard
from mysqlassist.myp_object import ServerMYP
from attemper import Attemper
from utils import *
from user import *
from definations import *
import json
import asyncio
import copy
from requesthelper import RequestHelper

class MainServiceError(Exception):
    pass

class MainService(object):
    sIns = None

    @classmethod
    def GetInstance(cls, host_api_key, subgame_id, server_port):
        if cls.sIns is None:
            cls.sIns = cls(host_api_key, subgame_id, server_port)
        return cls.sIns

    def __init__(self, host_api_key, subgame_id, server_port):
        self.mRunning = False
        self.mAttemper = None
        self.mMYPGuard = None

        Info("启动参数：", host_api_key, subgame_id, server_port)

        self.mConfigs = {}
        with open("cfg/main.json", "r") as hd:
            self.mConfigs = json.loads(hd.read())
        self.mConfigs["hash_key"] = GenHostApiHashKey(host_api_key, int(subgame_id))
        Log("hash_key", self.mConfigs["hash_key"])
        ServiceOpt.sSvrPort = server_port
        self.mConfigs["port"] = ServiceOpt.sSvrPort
        if "android" in self.mConfigs:
            AndroidOptions.InitOptions(self.mConfigs["android"])
        #配置日志
        LOGService.Set(int(self.mConfigs["dbg_lv"]))
        DebugLevel.Set(int(self.mConfigs["dbg_lv"]))
        RDSPGuard.SetDebugLevel(int(self.mConfigs["redis_dbg_lv"]))
        MYPGuard.SetDebugLevel(int(self.mConfigs["mysql_dbg_lv"]))
        # 启动逻辑组件
        self.mLoop = IOLoop.current()
        self.InitComponents()

    @property
    def Attemper(self):
        return self.mAttemper

    def StartService(self):
        if self.mRunning:
            Warn("MainService已启动！")
        self.mRunning = True
        Info("[服务启动成功]")
        WritePidAndSignal(self.ConcludeService)
        self.mLoop.start()

    def ConcludeService(self, signalnum, frame):
        try:
            Info("[请求关闭服务器]")
            if not self.mRunning:
                Warn("MainService未开启")
            self.mRunning = False
            self.mAttemper.Conclude()
            self.CreateTask(self.OnWaitClose())
        except:
            exit()

    async def OnWaitClose(self):
        nLoop = 5
        while (nLoop >= 0):
            nLoop = nLoop - 1
            Info("[踢掉所有在线玩家]")
            self.mAttemper.KickAllUser()
            if SvrUsrMgr.GetUserItemCount() == 0:
                break
            await asyncio.sleep(2)
        #删除在线人数
        self.mAttemper.shutdown_cron_job()
        rp = RDSPGuard.RP("gamelist")
        rp.LibGrd.R.hdel("sha@onlinenums", ServiceOpt.sSvrUUID)
        self.mAttemper.mServer.CloseServer()
        self.mLoop.stop()
        await asyncio.sleep(2)
        Info("[关闭完成] 退出程序")

    def InitComponents(self):
        # 加载redis接口
        RDSPGuard.LoadByFile("cfg/redis.json")
        rp = RDSPGuard.RP("game")
        rp.PubSub.OnPubMsgCB = self.OnRedisSubscribeCB
        # 启动redis订阅服务
        self.CreateTask(rp.PubSub.AsyncUpdate())
        self.CreateTask(rp.LibGrd.AsyncUpdate())
        EventRP.load_init()
        UserRP.load_init()
        # 启动mysql
        if not self.InitMYPGuard("cfg/mysql.json", self.mConfigs["server_math_info"]):
            raise MainServiceError("初始化MySQL失败！")

        MYPGuard.ProcWith(self.ConfigAllMYP)
        self.CreateTask(ServerMYP.load_init())

        # MYPGuard.LoadByFile("cfg/mysql.json")
        # self.CreateTask(MYPGuard.MYP("game").AsyncUpdate())
        # self.CreateTask(MYPGuard.MYP("log").AsyncUpdate())
        # self.CreateTask(MYPGuard.MYP("slotgame").AsyncUpdate())
        self.CreateTask(ServerMYP.load_init())
        # 启动逻辑
        self.mAttemper = Attemper.GetInstance(app = self)

    def InitMYPGuard(self, path, server_info_url):
        if self.mMYPGuard is not None:
            Err("mMYPGuard is not None")
            return False

        Info("load dbs")
        results = RequestHelper.DoPost(server_info_url, {"type": 1})
        multi_DB = {}

        with open(path, "r") as hd:
            data = json.loads(hd.read())
            if "dbs" not in data:
                return False

            slotgame_expample = data["dbs"]["slotgame"]
            link_arr = []
            for i in results:
                key = str(i["id"])
                public_ip = i["public_ip"]

                if public_ip is None or \
                    not isinstance(public_ip, str) or \
                    len(public_ip) == 0:
                    continue
                elif multi_DB.__contains__(key):
                    continue
                elif key in link_arr:
                    continue

                link_arr.append(key)

                setting = {}
                setting = copy.deepcopy(slotgame_expample)
                setting["host"] = copy.deepcopy(public_ip)

                multi_DB.update({key:setting})

            dbs={}
            dbs["dbs"] = {**data["dbs"], **multi_DB}

        Info("MYPGuard.LoadByData dbs")
        self.mMYPGuard = MYPGuard.LoadByData(dbs)
        return self.mMYPGuard is not None


    def ConfigAllMYP(self, myp):
        self.CreateTask(myp.AsyncUpdate())

    def CreateTask(self, co):
        self.mLoop.asyncio_loop.create_task(co)

    def OnRedisSubscribeCB(self, pb_proxy, msg, ptn, chl, data):
        pass
