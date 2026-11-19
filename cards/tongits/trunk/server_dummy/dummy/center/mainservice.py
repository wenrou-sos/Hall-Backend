
from tornado import ioloop
from tornado.ioloop import IOLoop
from redisassist import RDSPGuard
from mysqlassist import MYPGuard
from subscribe import *
from c_l_lobby_pb2 import *
from subgame import *
from control import *
from utils import *
from requesthelper import RequestHelper
from network.tcpserver import TCPServer
import signal
import random
import json

class MainService(object):
    sIns = None

    def __init__(self):
        self.sEvePc = None
        self.mTCPServer = None
        self.mHandlers = {
            "subgame": SubGameHandler(self),
            "control": ControlHandler(self)
        }
        self.mLoop = IOLoop.current()
        self.options = {}
        self.mSubscribe = Subscribecb(self)

    @classmethod
    def GetInstance(cls):
        if cls.sIns is None:
            cls.sIns = cls()
        return cls.sIns

    @property
    def TCPServer(self):
        return self.mTCPServer

    def StartService(self, **opts):
        self.options = opts
        Info(self.options)
        self.InitComponent()
        WritePidAndSignal(self.ConcludeService)
        self.mLoop.start()

    def ConcludeService(self, signalnum, frame):
        try:
            Info("[踢掉所有在线玩家]")
            self.mTCPServer.CloseServer()
            self.mLoop.stop()
            Info("[关闭完成] 退出程序")
            exit()
        except:
            exit()

    def OnNetClose(self, conn):
        for h in self.mHandlers.values():
            h.OnNetClose(conn)

    def GetHandler(self, name):
        if name not in self.mHandlers:
            return None
        return self.mHandlers[name]

    def InitComponent(self):
        # 配置日志
        if "dbg_lv" in self.options:
            LOGService.Set(self.options["dbg_lv"])
            DebugLevel.Set(self.options["dbg_lv"])
        if "redis_dbg_lv" in self.options:
            RDSPGuard.SetDebugLevel(self.options["redis_dbg_lv"])
        if "mysql_dbg_lv" in self.options:
            MYPGuard.SetDebugLevel(self.options["mysql_dbg_lv"])

        # 加载redis接口
        RDSPGuard.LoadByFile("cfg/redis.json")
        RDSPGuard.RP("game").PubSub.OnPubMsgCB = self.mSubscribe.OnRedisSubscribeCB
        # 启动redis订阅服务
        OnRedisRunPubSubRecv(self.mLoop)
        OnRedisRunLibGrdRecv(self.mLoop)
        # 启动mysql
        MYPGuard.LoadByFile("cfg/mysql.json")
        self.mLoop.asyncio_loop.create_task(MYPGuard.MYP("game").AsyncUpdate())
        self.mLoop.asyncio_loop.create_task(self.AsyncGenRoomPwd())

        # 开启服务器
        self.mTCPServer = TCPServer()
        self.mTCPServer.InitServer(self.options)
        for h in self.mHandlers.values():
            self.mTCPServer.AddHandler(h.Initialize)
        self.mTCPServer.SetCloseHandler(self.OnNetClose)

        '''
        # 开启公告
        periodic = ioloop.PeriodicCallback(NoticeMgr.OnEventSendNotice,
                                           CfgMgr.GetNoticeTime() * 1000)
        periodic.start()
        '''

        # 设置每日凌晨倒计时
        nowTime = GetServerTime()
        zeroTime = GetServerZeroTime()
        waitTime = 0
        if zeroTime != nowTime:
            waitTime = zeroTime + 86400 - nowTime
        self.sEvePc = ioloop.PeriodicCallback(self.OnEventPerZeroTime, waitTime * 1000)
        self.sEvePc.start()
        # 每10分鐘向PS申請一次取得目前廠商的url位址
        # ioloop.PeriodicCallback(self.OnTMEvt_SharedWalletURL, 600000).start()
        # 启动成功
        self.OnEventServiceStart()

    def OnEventServiceStart(self):
        rp1 = RDSPGuard.RP("gamelist")
        rp1.LibGrd.R.delete("var@serverlist")

    async def AsyncGenRoomPwd(self):
        rp = RDSPGuard.RP("game")
        if await rp.AsyncHelper.Exec("LLEN", "list@roompwdpool") != 50000:
            vPwdLst = random.sample(range(100000, 999999), 50000)
            for pwd in vPwdLst:
                await rp.AsyncHelper.Exec("LPUSH", "list@roompwdpool", pwd)
        if await rp.AsyncHelper.Exec("EXISTS", "var@pwdpoolidx") == 0:
            await rp.AsyncHelper.Exec("SET", "var@pwdpoolidx", 0)
        Info("生成房间密码完成")

    # def OnTMEvt_SharedWalletURL(self):  # 共享錢包更新
    #     try:
    #         print("SharedWalletURL")
    #         rp = RDSPGuard.RP("game")
    #         # 取得sha@chl_xxx資訊
    #         # 取得代理商金鑰
    #         all_host_api_key_list = self.options["host_api_key"]  # cfg的商戶項目應為列表內包所有商戶字串
    #         if str(type(all_host_api_key_list)) == "<class 'str'>":  # 如果cfg商戶項目只有一個字串，沒有列表
    #             str_to_list = []
    #             str_to_list.append(all_host_api_key_list)  # 將字串加入列表
    #             all_host_api_key_list = str_to_list  # 取代回列表內包字串
    #         for host_api_key in all_host_api_key_list:  # 走訪所有商戶，取得每一個商戶代號
    #             chl_resp = rp.LibGrd.R.hget("sha@chl_" + host_api_key, "extra")
    #             if chl_resp:
    #                 ctm_data = json.loads(chl_resp)  # 取得field內的其中extra項目：代理商設定getchl
    #                 # 錢包格式
    #                 wallet_type = ctm_data["wallet_type"]
    #                 if wallet_type:  # 共享錢包
    #                     dl_url = self.options["ps_urls"]["gethostapiinfo"]
    #                     # 正式向PS請求與廠商溝通的通道
    #                     results = RequestHelper.DoGet(dl_url, {"host_id": host_api_key})
    #                     if results["host_api_info"]:
    #                         # 將取得的各通道儲存於sha@chl_的host_url's field內
    #                         rp.LibGrd.R.hset("sha@chl_" + host_api_key, "host_url", json.dumps(results["host_api_info"]))
    #                     else:
    #                         Log("gethostapiinfo ERR")
    #             else:
    #                 Log("channel.GetInfo ERR")
    #     except:
    #         PrintEXC()
    # 刷新每日分数、每日盈亏、每日转出、转入
    def OnEventPerZeroTime(self):
        try:
            waitTime = GetServerZeroTime() + 86400 - GetServerTime()
            self.sEvePc.stop()
            if waitTime <= 5:
                waitTime = 86400
            self.sEvePc = ioloop.PeriodicCallback(self.OnEventPerZeroTime,
                                                  waitTime * 1000)
            self.sEvePc.start()

            rp0 = RDSPGuard.RP("game")
            results = rp0.LibGrd.R.hvals("sha@uuid2sid")
            if results != None and isinstance(results, list) == True:
                for idx in range(len(results)):
                    if (results[idx].isdigit()):
                        online_uuid = int(results[idx])
                        infos = rp0.LibGrd.Call("common.GetInfoBySYS", *(online_uuid, ))
                        if infos == None \
                                or isinstance(infos, list) == False \
                                or infos[0] != 0:
                            continue
                        account_base = db_data_user()
                        account_base.ParseFromString(infos[1])
                        account_base.dailyprofit = 0
                        account_base_ss = account_base.SerializeToString()
                        rp0.LibGrd.Call("common.SetInfoBySYS", *(online_uuid, account_base_ss))
        except:
            PrintEXC()
