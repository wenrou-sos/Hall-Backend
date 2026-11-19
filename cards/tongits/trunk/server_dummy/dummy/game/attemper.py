
import json
import math
import random
import importlib
import asyncio
import subgame
from copy import deepcopy
from network.tcpserver import *
from network.tcpclient import *
from mysqlassist import MYPGuard
from mysqlassist.myp_object import ServerMYP
from redisassist import RDSPGuard
from redisassist.rdsproxyguard import UserRP, EventRP
from queue import Queue, PriorityQueue
from stock import Stock
from android import AndroidService
from timer import TimerEngine
from dbexecution import sSqls
from tableframe import TableFrame
from definations import *
from main_cmd_pb2 import *
from error_pb2 import *
from c_g_game_pb2 import *
from center_game_pb2 import *
from c_l_lobby_pb2 import *
from data_struct_pb2 import *
from user import *
from urls import *
from utils import *
from matcher import *
from async import *
from requesthelper import *
from google.protobuf.json_format import MessageToJson
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
from heartbeat_pb2 import *

TIME_GAME_SAVE_LOG = 2  # 定时保存日志
TIME_WAIT_CLOSE = 5  # 检测等待删除的socket时间
TIME_CHECK_TABLE_OFFLINE = 1  # 检测离线玩家
TIME_UPDATE = 10  # 检查命令
TIME_DISTRIBUTE_ANDROID = 3  # 分配机器人时间间隔
TIME_MATCH_USER = 8  # 匹配时间帧
TIME_UPDATE_PLAYER = 60  # 定时更新人数
TIME_GET_RETRY_TIME = 600  # 每10分鐘更新目前的重複請求次數

class stNetBindParams(object):
    def __init__(self):
        self.mSocketID = 0
        self.mISvrUserItem = None
        self.mLoginTime = 0  #上次请求登录时间
        self.mIpAddr = "127.0.0.1"

class AttemperError(Exception):
    pass

class Attemper(object):
    sIns = None
    @classmethod
    def GetInstance(cls, app = None):
        if cls.sIns is None:
            cls.sIns = cls(app)
            cls.sIns.InitComponents()
        return cls.sIns

    def __init__(self, app):
        if Attemper.sIns != None:
            raise AttemperError("Attemper已被创建！")
        self.mApp = app
        self.mServiceOpt = None
        self.mServiceAttr = None
        self.mGModule = None
        self.mTEngine = None
        self.mStock = None
        self.mAndroidService = None     #机器人服务
        self.mServer = None
        self.mAsyncGuard = None
        self.mAsyncService = None
        self.mMatch = None              #匹配服务
        self.vMateWaitTime = []
        # 定时器ID
        self.mReTimer = None
        self.nMaxNotice = 20
        # 寫入dmgamelog的dict，寫入後清除
        self.mLogCaches = {}  # std::unordered_map<std::string, std::vector<std::string>>
        # 寫入dmgamelog→vip_log的dict，寫入後刪除
        self.mVipLog = {}
        # 寫入dmgame→VIP_player的dict，寫入後清除
        self.mVipPlayer = {}
        self.mEduUUIDInc = 100000000   #试玩场UUID自增

        self.mID2Conn = {}
        self.mTables = []
        self.mWaitClose = {}    # std::map<DWORD, int64_t>，等待关闭连接<socketid,time>

        self.mMainProc = {}
        self.mCtrlFunc = {}
        #牌组
        self.vCardShoes = []

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.UpdateGameServerInfo, 'cron', id='hot_update', minute='*/1')

    @property
    def App(self):
        return self.mApp

    @property
    def ServiceOpt(self):
        return self.mServiceOpt

    @property
    def ServiceAttr(self):
        return self.mServiceAttr

    @property
    def GModule(self):
        return self.mGModule

    @property
    def TEngine(self):
        return self.mTEngine

    @property
    def Stock(self):
        return self.mStock

    @property
    def AndroidService(self):
        return self.mAndroidService

    @property
    def Server(self):
        return self.mServer

    def CreateTask(self, co):
        IOLoop.current().asyncio_loop.create_task(co)

    def InitComponents(self):
        if "hash_key" not in self.mApp.mConfigs:
            raise AttemperError("缺少hostapikey&subgameid配置！")
        self.LoadGameServerInfo()
        ServiceOpt.sSvrUUID = GenServerUUID()
        Info("ServiceOpt.sSvrUUID", type(ServiceOpt.sSvrUUID), ServiceOpt.sSvrUUID)

        self.nMaxNotice = self.mApp.mConfigs["max_notice"]
        # 启动服务器
        #if "svr_port_begin" not in self.mApp.mConfigs:
        #    raise AttemperError("配置文件缺失重要参数 'svr_port_begin'")
        #ServiceOpt.sSvrPort = self.mApp.mConfigs["svr_port_begin"] + ServiceOpt.sIndex
        #self.mApp.mConfigs["port"] = ServiceOpt.sSvrPort
        self.mApp.mConfigs["max_connections"] = ServiceOpt.sMaxPlayer + 100
        if "websocket" in self.mApp.mConfigs and self.mApp.mConfigs["websocket"] == 1:
            self.mServer = WebServer.Create(sUrls, **self.mApp.mConfigs)
        else:
            self.mServer = TCPServer()
            self.mServer.InitServer(self.mApp.mConfigs)
        self.mServer.AddHandler(self.OnSrv_MsgRegister)
        self.mServer.SetCloseHandler(self.OnSrv_OnNetClose)
        self.mServer.SetLinkedHandler(self.OnSrv_OnNetLinked)
        self.mServer.SetDefaultHandler(self.OnSrv_SGMessage)

        # 启动客户端连接
        if "gs_ip" in self.mApp.mConfigs:
            self.mGsIp = self.mApp.mConfigs["gs_ip"]
        if "gs_port" in self.mApp.mConfigs:
            self.mGsPort = self.mApp.mConfigs["gs_port"]
        self.InitGS()

        # 初始化组件信息
        self.mTEngine = TimerEngine.GetInstance(self)
        self.mStock = Stock.GetInstance(self)
        self.mAndroidService = AndroidService.GetInstance(self)
        self.mMatcher = Matcher()

        self.mGModule = importlib.import_module("subgame." + ServiceOpt.sModuleName + ".tableframesink")
        self.mGModule.GetServiceAttr(ServiceAttr)
        self.mServiceAttr = ServiceAttr

        Info("加载游戏设定")
        self.OnToolReLoadCfg(None, None)

        # 初始化定时器
        self.InitTimers()
        self.OnCtrlToolFuncRegister()
        # 加载配置文件
        if not self.mGModule.LoadConfig(ServiceOpt.sSvrName):
            raise AttemperError("加载游戏配置文件失败！")
        if not self.InitTables():
            raise AttemperError("初始化房间对象组失败！")
        #异步请求接口，请求牌组和退出
        if "async" in self.mApp.mConfigs:
            self.mAsyncGuard = AsyncGuard(**(self.mApp.mConfigs["async"]))
            self.mAsyncService = AsyncGuard(**(self.mApp.mConfigs["async"]))
        else:
            self.mAsyncGuard = AsyncGuard()
            self.mAsyncService = AsyncGuard()
        self.GetMoreCardShoes()
        self.scheduler.start()  # 避免在 server 沒有啟動時執行線程，在最後才啟動

    def LoadGameServerInfo(self):
        sqlp = MYPGuard.MYP("game")
        sql = sSqls["load_roomcfg"]
        sqlp.Exec(sql = sql.GetSQL(params = { "hash_key" : self.mApp.mConfigs["hash_key"] }),
                  callback = self.ReadGameServerInfo)
        while True:
            sqlp.Update()
            if self.mServiceOpt is not None:
                break
            elif ServiceOpt.sHostApiKey == "-1":
                raise AttemperError(f'hash_key:{self.mApp.mConfigs["hash_key"]} 加载房间参数失败！')

        Log(f'hash_key:{self.mApp.mConfigs["hash_key"]} 加载房间完成')

    def UpdateGameServerInfo(self):
        """熱更新 game 參數

        """
        sqlp = MYPGuard.MYP("game")
        sql = sSqls["load_roomcfg"]
        sqlp.Exec(sql = sql.GetSQL(params = { "hash_key" : self.mApp.mConfigs["hash_key"] }),
                  callback = self.ReadUpdateGameServerInfo)
        sqlp.Update()
        time.sleep(4)  # 避免log先出來，熱更新還沒結束
        Log((f"thinktime: {ServiceOpt.sThinkTime}\n"
             # f"challengetime: {ServiceOpt.sChallengeTime}\n"
             f"win_times: {ServiceOpt.sWinTimes}\n"
             f"bad_draw_rate: {ServiceOpt.sBadDrawRate}\n"
             f"bad_draw_rate_vip: {ServiceOpt.sBadDrawRateVip}\n"
             f"allowrobot: {ServiceOpt.sAllowAndroid}\n"
             f"robot_draw_rate: {ServiceOpt.sRobotDrawRate}\n"
             f"robot_draw_rate_vip: {ServiceOpt.sRobotDrawRateVip}\n"
             f"pre_arbitrage: {ServiceOpt.sPreventArbitrage}\n"
             f"random_robot_rate: {ServiceOpt.sRobotRate}\n"
             ))

    def Conclude(self):
        self.mMatcher.DelAll()
        for wTableID in range(ServiceOpt.sTableCount):
            mTableFrame = self.mTables[wTableID]
            if mTableFrame is not None:
                mTableFrame.DisMissGame()

    #关闭服务器
    def KickAllUser(self):
        sSvrUsrs = deepcopy(SvrUsrMgr.sSvrUsrs)
        for _, srvUserItem in sSvrUsrs.items():
            self.mMatcher.DelMatchItem(srvUserItem)
            if srvUserItem.TableID != INVALID_TABLE and srvUserItem.ChairID != INVALID_CHAIR:
                mTableFrame = self.mTables[srvUserItem.TableID]
                if mTableFrame is not None:
                    mTableFrame.KickUser(srvUserItem.ChairID, logout_kicked)
            else:
                self.OnEventUserKick(srvUserItem, logout_kicked)

    @gen.coroutine
    def InitGS(self, params=None):
        if self.mReTimer is not None:
            self.mTEngine.RemoveTimer(self.mReTimer)
            self.mReTimer = None
        self.mGSClient = MYTCPClient(self.mGsIp, self.mGsPort)
        self.mGSClient.SetCloseHandler(self.OnGS_OnNetClose)
        self.mGSClient.SetLinkHandler(self.OnGS_OnNetLinked)
        self.mGSClient.AddHandler(self.OnGS_MsgRegister)
        nR = yield self.mGSClient.Connect()
        if not nR:
            self.mReTimer = self.mTEngine.AddTimer(30, self.InitGS, None)
            Info("连接失败，30秒后重新连接")

    def InitTimers(self):
        self.mTEngine.AddTimer(TIME_UPDATE_PLAYER, self.OnTMEvt_UpdatePlayer, None)
        self.mTEngine.AddTimer(TIME_GAME_SAVE_LOG, self.OnTMEvt_SaveLogs, None)
        self.mTEngine.AddTimer(TIME_WAIT_CLOSE, self.OnTMEvt_WaitClose, None)
        self.mTEngine.AddTimer(TIME_CHECK_TABLE_OFFLINE, self.OnTMEvt_CheckOffline, None)
        if self.mServiceAttr.sAllowMatch:
            self.mTEngine.AddTimer(TIME_MATCH_USER, self.OnTMEvt_MateUser, None)
        else:
            self.mTEngine.AddTimer(TIME_DISTRIBUTE_ANDROID, self.OnTMEvt_DistributeAndroid, None)
        self.mTEngine.AddTimer(AndroidOptions.sActionTime, self.OnTMEvt_AndroidAction, None)
        self.mTEngine.AddTimer(AndroidOptions.sCheckOpTime, self.OnTMEvt_CheckAndroidOperate, None)
        #self.mTEngine.AddTimer(AndroidOptions.sCheckStTime, self.OnTMEvt_CheckAndroidStatus, None)
        self.mTEngine.AddTimer(TIME_GET_RETRY_TIME, self.OnTMEvt_RetryTime, None)

    def GetMoreCardShoes(self):
        self.CreateTask(self.OnGetCardShoe())

    async def OnGetCardShoe(self):
            if "ps_urls" in self.mApp.mConfigs:
                if "getcardshoe" in self.mApp.mConfigs["ps_urls"]:
                    url = self.mApp.mConfigs["ps_urls"]["getcardshoe"]
                    for c in range(5):
                        results = await self.mAsyncGuard.DoAsync(RequestHelper.ReqGetDeck, url, 1)
                        if results is None:
                            continue
                        self.vCardShoes.append(results)

    def AllokcCardShoe(self):
        mNewShoe = None
        try:
            #是否有测试脚本
            if "test_script" in self.mApp.mConfigs:
                test_script = self.mApp.mConfigs["test_script"]
                try:
                    with open(test_script, "r") as hd:
                        script_json = json.loads(hd.read())
                        return script_json["crds"]
                except:
                    pass

            if len(self.vCardShoes) > 0:
                mNewShoe = self.vCardShoes.pop(0)
            if len(self.vCardShoes) <= 30:
                self.GetMoreCardShoes()
        except:
            return mNewShoe
        return mNewShoe

    def AllocTableFrame(self, nNullChair, vMateUsers = None):
        # if nNullChair is None \
        #         or nNullChair > self.mServiceAttr.sChairCnt \
        #         or nNullChair <= 0:
        #     nNullChair = self.mServiceAttr.sChairCnt
        mExceptTables = {}
        if vMateUsers is not None:
            for usr in vMateUsers:
                if usr.pSvrUserItem.mExceptTableID != INVALID_TABLE:
                    mExceptTables[usr.pSvrUserItem.mExceptTableID] = 1  # 將配對到的玩家加入一個臨時桌子

        mEmptyTableFrame = None
        for wTableID in range(ServiceOpt.sTableCount):  # 從1000個桌子中取出
            mTableFrame = self.mTables[wTableID]
            if mTableFrame is not None:
                if mTableFrame.TableID not in mExceptTables:  # 如果取出的桌子不是臨時桌子
                    nCount = mTableFrame.GetAllUserCount()  # 再確認此桌子裡面有沒有人
                    # if nCount > 0 and mTableFrame.GetWaitCount() >= nNullChair \
                    #         and not mTableFrame.IsCustomTable():
                    #     Log("分配到已经存在玩家的桌子")
                    #     return mTableFrame
                    if mEmptyTableFrame is None and nCount == 0:  # 如果裡面沒人
                        mEmptyTableFrame = mTableFrame  # 那就是可使用的空桌子了
                        return mEmptyTableFrame  # 只要取得一個空桌子就可以回傳了

    def OnTMEvt_MateUser(self, params):
        nMatchTime = TIME_MATCH_USER
        if len(self.vMateWaitTime) == 0:
            self.vMateWaitTime = ServiceOpt.sMatchWaitTime
        if len(self.vMateWaitTime) > 0:
            nIdx = GetRndInt(0, len(self.vMateWaitTime)-1)
            nMatchTime = self.vMateWaitTime[nIdx]
            self.vMateWaitTime.pop(nIdx)

        self.mTEngine.AddTimer(nMatchTime, self.OnTMEvt_MateUser, None)

        # 是否維護
        rp = RDSPGuard.RP("game")
        api_key = ServiceOpt.sHostApiKey
        channel_res = rp.LibGrd.Call("channel.GetInfo", *(api_key,))
        if channel_res[0] == 0:
            chl_data = OnRedisResultParser(channel_res[1])
            ctm_data = json.loads(chl_data["extra"])
            if "status" in ctm_data:
                status = ctm_data["status"]
                if status == 1:  # 維護
                    self.KickAllUser()
                    return

        is_tester_mode = False  # 預設當前不是測試人員配對

        if self.mMatcher.GetCount() > 0:
            nowTime = GetServerTime()
            while True:
                vMateUsers = []
                self.mMatcher.OnMatchGroups(nowTime, self.mServiceAttr.sChairCnt, vMateUsers)
                # 如果沒有玩家，或(玩家只有1人且沒有允許機器人)，則開桌失敗，續下一輪排隊
                if len(vMateUsers) == 0 or (len(vMateUsers) == 1 and not ServiceOpt.sAllowAndroid):
                    break
                # 匹配人數後，先確認其中有沒有vip玩家
                vip = False  # 設置vip玩家規則
                for i in vMateUsers:
                    rp = RDSPGuard.RP("game")
                    results = rp.LibGrd.Call("common.GetInfoBySYS", *(i.pSvrUserItem.UUID,))

                    if not results[1] and ServiceOpt.IsEducateSvr():  # 沒資料卻正常回傳 None
                        vMateUsers.clear()  # 其他人退散，到下一輪匹配
                        vMateUsers.append(i)  # 就只留vip一個人下來
                        break

                    if results != None and results[0] == 0:
                        account_base = db_data_user()
                        account_base.ParseFromString(results[1])

                        if account_base.user_type == 999:
                            is_tester_mode = True # 更改為測試人員配對
                            # 配對中只保留測試人員確保只會配到機器人
                            vMateUsers.clear()
                            vMateUsers.append(i)
                            break

                        if account_base.VIP == 1:  # 若玩家受到vip禮遇
                            vip = True  # vip玩家抽牌反作弊規則啟動
                            vMateUsers.clear()  # 其他人退散，到下一輪匹配
                            vMateUsers.append(i)  # 就只留vip一個人下來
                            break
                #分配桌子
                nNullChair = self.mServiceAttr.sChairCnt - len(vMateUsers)
                mTableFrame = self.AllocTableFrame(nNullChair, vMateUsers)
                if mTableFrame is None:
                    break
                bNewTable = mTableFrame.GetAllUserCount() == 0
                # 匹配中表示重新開始一局，繼續遊戲計數器歸零
                mTableFrame.mcontinue_game_count = 0
                #初始化桌子
                mTableFrame.Dgt.OnInitialize(ServiceOpt.sCellScore, ServiceOpt.sThinkTime,
                                             ServiceOpt.sNoticeScore)  # , sChallengeTime)
                #玩家坐下
                bOk = True
                nFalsePos = INVALID_CHAIR
                for nIdx in range(len(vMateUsers)):
                    wChairID = mTableFrame.GetNullChairID()
                    if wChairID != INVALID_CHAIR:
                        if not mTableFrame.PerformSitDownAction(wChairID, vMateUsers[nIdx].pSvrUserItem):
                            bResult = False
                            nFalsePos = nIdx
                            DEBUG("匹配结果：玩家[%d]坐下失败", vMateUsers[nIdx].pSvrUserItem.UUID)
                            break

                # 如果匹配的真人玩家是1人
                if bOk and len(vMateUsers) == 1:
                    if not self.DistributeTwoAndroid(mTableFrame, False, vip, is_tester_mode):  # 進入分配2個機器人
                        for wChair in range(ServiceAttr.sChairCnt):
                            srvUserItem = mTableFrame.GetTableUserItem(wChair)
                            if srvUserItem is not None:
                                mTableFrame.PerformStandUpAction(srvUserItem)
                        break

                # 如果匹配的真人玩家是2人
                if bOk and len(vMateUsers) == 2:
                    if not self.DistributeOneAndroid(mTableFrame, False,
                                                     vip,
                                                     is_tester_mode):  # 進入分配1個機器人
                        for wChair in range(ServiceAttr.sChairCnt):
                            srvUserItem = mTableFrame.GetTableUserItem(
                                wChair)
                            if srvUserItem is not None:
                                mTableFrame.PerformStandUpAction(
                                    srvUserItem)
                        break

                if bOk:
                    for nIdx in range(len(vMateUsers)):
                        self.mMatcher.DelMatchInfo(vMateUsers[nIdx])
                    for wChair in range(ServiceAttr.sChairCnt):
                        srvUserItem = mTableFrame.GetTableUserItem(wChair)
                        if srvUserItem is not None and not srvUserItem.IsAndroidUser:
                            self.SendUserSitDown(srvUserItem, srvUserItem.TableID, srvUserItem.ChairID)
                else:
                    for nIdx in range(len(vMateUsers)):
                        if nIdx == nFalsePos:
                            self.mMatcher.DelMatchInfo(vMateUsers[nIdx])
                        else:
                            for wChair in range(ServiceAttr.sChairCnt):
                                srvUserItem = mTableFrame.GetTableUserItem(wChair)
                                if srvUserItem is not None:
                                    mTableFrame.PerformStandUpAction(srvUserItem)
                if bOk:
                    #if bNewTable:
                    #    mTableFrame.bCanStart = True
                    for wChair in range(ServiceAttr.sChairCnt):
                        srvUserItem = mTableFrame.GetTableUserItem(wChair)
                        if srvUserItem is not None:
                            mTableFrame.OnEventReady(srvUserItem)

    def OnTMEvt_DistributeAndroid(self, params):
        self.mTEngine.AddTimer(TIME_DISTRIBUTE_ANDROID, self.OnTMEvt_DistributeAndroid, None)
        for wTableID in range(ServiceOpt.sTableCount):
            sTable = self.mTables[wTableID]
            if sTable is None:
                continue
            nAndroidCounts = sTable.GetAndroidCount()
            if ServiceOpt.sPerTableMaxAdr == 0 \
                    or nAndroidCounts >= ServiceOpt.sPerTableMaxAdr:
                continue
            if ServiceOpt.sDistribTimeSp > 0 \
                    and sTable.GetLastAndroidTime() + ServiceOpt.sDistribTimeSp > GetServerTime():
                continue
            # 判断，如果是空桌子，机器人就不占桌了
            self.DistributeOneAndroid(sTable, True)

    def DistributeTwoAndroid(self, mTableFrame, bSendMsg=False, vip=False, is_tester_mode=False):
        """

        Args:
            mTableFrame: 桌子物件
            bSendMsg:
            vip:
            is_tester_mode (bool): True 代表測試人員模式，給予特殊的機器人

        Returns:

        """
        wChairID = mTableFrame.GetTwoNullChairID()  # 一次取得2個空座位
        if is_tester_mode:
            Android_2 = self.AndroidService.get_android_for_tester(2)
        else:
            Android_2 = self.AndroidService.GetTwoAndroid(vip)  # 一次取得2位機器人

        wChairID_dict = {}  # 建立空座位的索引
        for z in range(len(wChairID)):
            wChairID_dict.update({wChairID[z]: z})
        # 空闲的桌子号有效，并且机器人数据有效
        if INVALID_CHAIR != wChairID and Android_2 is not None \
                and (Android_2[0].GetUserStatus() == eUS.US_FREE or Android_2[0].GetUserStatus() == eUS.US_NULL) \
                and (Android_2[1].GetUserStatus() == eUS.US_FREE or Android_2[1].GetUserStatus() == eUS.US_NULL):
            # 第N個機器人分配攜帶金額計數器
            android_assign_carry_money_count = 0
            # 有任何空位一律補上機器人
            for i, j in wChairID_dict.items():  # 走訪每一位機器人
                android_assign_carry_money_count += 1  # 計數第N位機器人
                mAndroid = Android_2[j]  # 每i座號分配一個機器人
                bOk = mTableFrame.PerformSitDownAction(i, mAndroid.GetMeUserItem())  # 該座號對應的機器人座下
                if not bOk:
                    return False
                mAndroid.OnAndroidSitDown(mTableFrame, vip)  # 分配攜帶金額

                # if android_assign_carry_money_count == 2:  # 此機器人為第2個機器人
                #     mAndroid.OnSecondAndroidSitDown(mTableFrame, vip)  # 分配攜帶金額
                # else:  # 此機器人為第1個機器人
                #     mAndroid.OnAndroidSitDown(mTableFrame, vip)  # 分配攜帶金額

                info = mAndroid.GetInfo()
                info.mStatus = eUS.US_SIT

                if bSendMsg:
                    # 通知其他玩家，机器人坐下
                    sendmsgbc = msg_sitdown_ret_bc()
                    sendmsgbc.newuser.uuid = info.mUUID
                    sendmsgbc.newuser.nickname = info.mNickName.encode('utf-8')
                    sendmsgbc.newuser.chair_id = info.mChairID
                    sendmsgbc.newuser.play_status = int(info.mStatus)
                    sendmsgbc.newuser.faceid = info.mFaceID
                    sendmsgbc.newuser.score = info.mScore
                    self.SendToTableClient(info.mTableID, e_msgid_game_action, e_cg_msgid_sitdown_bc, sendmsgbc)
            return True
        return False

    def DistributeOneAndroid(self, mTableFrame, bSendMsg=False, vip=False, is_tester_mode=False):
        wChairID = mTableFrame.GetNullChairID()
        if is_tester_mode:
            mAndroid = self.AndroidService.get_android_for_tester(1)[0] # 回傳值會是串列
        else:
            mAndroid = self.AndroidService.GetFreeAndroid(vip)

        # 空闲的桌子号有效，并且机器人数据有效
        if INVALID_CHAIR != wChairID and mAndroid is not None \
                and (mAndroid.GetUserStatus() == eUS.US_FREE
                      or mAndroid.GetUserStatus() == eUS.US_NULL):
            bOk = mTableFrame.PerformSitDownAction(wChairID, mAndroid.GetMeUserItem())
            if not bOk:
                return False
            mAndroid.OnAndroidSitDown(mTableFrame, vip)  # 分配攜帶金額

            info = mAndroid.GetInfo()
            info.mStatus = eUS.US_SIT

            if bSendMsg:
                # 通知其他玩家，机器人坐下
                sendmsgbc = msg_sitdown_ret_bc()
                sendmsgbc.newuser.uuid = info.mUUID
                sendmsgbc.newuser.nickname = info.mNickName.encode('utf-8')
                sendmsgbc.newuser.chair_id = info.mChairID
                sendmsgbc.newuser.play_status = int(info.mStatus)
                sendmsgbc.newuser.faceid = info.mFaceID
                sendmsgbc.newuser.score = info.mScore
                self.SendToTableClient(info.mTableID, e_msgid_game_action, e_cg_msgid_sitdown_bc, sendmsgbc)
            return True
        return False

    def DistributeThreeAndroid(self, mTableFrame, bSendMsg=False, vip=False, is_tester_mode=False):
        wChairID = mTableFrame.GetMoreNullChairID()  # 一次取得所有空座位
        if is_tester_mode:
            Android_3 = self.AndroidService.get_android_for_tester(3)
        else:
            Android_3 = self.AndroidService.GetThreeAndroid(vip)  # 一次取得3位機器人

        wChairID_dict = {}  # 建立空座位的索引
        for z in range(len(wChairID)):
            wChairID_dict.update({wChairID[z]: z})
        # 空闲的桌子号有效，并且机器人数据有效
        if INVALID_CHAIR != wChairID and Android_3 is not None \
                and (Android_3[0].GetUserStatus() == eUS.US_FREE or Android_3[0].GetUserStatus() == eUS.US_NULL) \
                and (Android_3[1].GetUserStatus() == eUS.US_FREE or Android_3[1].GetUserStatus() == eUS.US_NULL) \
                and (Android_3[2].GetUserStatus() == eUS.US_FREE or Android_3[2].GetUserStatus() == eUS.US_NULL):
            # 第N個機器人分配攜帶金額計數器
            android_assign_carry_money_count = 0
            # 有任何空位一律補上機器人
            for i, j in wChairID_dict.items():
                android_assign_carry_money_count += 1  # 計數第N位機器人
                mAndroid = Android_3[j]  # 每i座號分配一個機器人
                bOk = mTableFrame.PerformSitDownAction(i, mAndroid.GetMeUserItem())  # 該座號對應的機器人座下
                if not bOk:
                    return False
                mAndroid.OnAndroidSitDown(mTableFrame, vip)  # 分配攜帶金額

                # if android_assign_carry_money_count == 2:  # 此機器人為第2個機器人
                #     mAndroid.OnSecondAndroidSitDown(mTableFrame, vip)  # 分配攜帶金額
                # else:  # 此機器人為第1個機器人
                #     mAndroid.OnAndroidSitDown(mTableFrame, vip)  # 分配攜帶金額

                info = mAndroid.GetInfo()
                info.mStatus = eUS.US_SIT

                if bSendMsg:
                    # 通知其他玩家，机器人坐下
                    sendmsgbc = msg_sitdown_ret_bc()
                    sendmsgbc.newuser.uuid = info.mUUID
                    sendmsgbc.newuser.nickname = info.mNickName.encode('utf-8')
                    sendmsgbc.newuser.chair_id = info.mChairID
                    sendmsgbc.newuser.play_status = int(info.mStatus)
                    sendmsgbc.newuser.faceid = info.mFaceID
                    sendmsgbc.newuser.score = info.mScore
                    self.SendToTableClient(info.mTableID, e_msgid_game_action, e_cg_msgid_sitdown_bc, sendmsgbc)
            return True
        return False

    def OnTMEvt_AndroidAction(self, params):
        self.mTEngine.AddTimer(AndroidOptions.sActionTime, self.OnTMEvt_AndroidAction, None)
        if self.mAndroidService is not None:
            self.mAndroidService.OnEventTimerPulse()

    def OnTMEvt_CheckAndroidOperate(self, params):
        nowTime = GetServerTime()
        self.mTEngine.AddTimer(AndroidOptions.sCheckOpTime, self.OnTMEvt_CheckAndroidOperate, None)
        for id, sAndroid in self.mAndroidService.mAndroids.items():
            if sAndroid is None:
                continue
            wTableID = sAndroid.GetTableID()
            if wTableID == INVALID_TABLE:
                continue
            mTableFrame = self.mTables[wTableID]
            # 如果是退出桌子状态，则发送起立指令，并复位机器人数据
            if sAndroid.GetUserStatus() == eUS.US_EXIT \
                    and nowTime >= sAndroid.nLeaveTime:
                INFO("机器人[%s:%d]状态由EXIT->NULL", sAndroid.GetInfo().mNickName, sAndroid.GetInfo().mUUID)
                if mTableFrame.PerformStandUpAction(sAndroid.GetMeUserItem()):
                    sAndroid.OnReposition()
                continue
            '''
            if mTableFrame.GetGameStatus() >= eGameStatus.GAME_STATUS_PLAY \
                    or sAndroid.GetUserStatus() == eUS.US_READY:
                continue
            if mTableFrame.OnEventReady(sAndroid.GetMeUserItem()):
                break
            '''

    def OnTMEvt_CheckAndroidStatus(self, params):
        nRndTime = GetRndInt(60, 120)
        self.mTEngine.AddTimer(nRndTime, self.OnTMEvt_CheckAndroidStatus, None)

        curTicks = GetServerTime()
        for id, sAndroid in self.mAndroidService.mAndroids.items():
            if sAndroid is None:
                continue
            if sAndroid.GetUserStatus() == eUS.US_NULL \
                    and (curTicks - sAndroid.nRepositTime) > GetRndInt(AndroidOptions.sMinWaitTime, AndroidOptions.sMaxWaitTime):
                sAndroid.nRepositTime = 0
                sAndroid.SetUserStatus(eUS.US_FREE)

    def OnTMEvt_SaveLogs(self, params):  # 每2秒寫入dmgame與dmgamelog資料庫
        self.mTEngine.AddTimer(TIME_GAME_SAVE_LOG, self.OnTMEvt_SaveLogs, None)
        try:
            if len(self.mLogCaches) > 0:
                sql = sSqls["save_logs"]
                cursql = ""
                for col, logs in self.mLogCaches.items():
                    for idx in range(len(logs)):
                        cursql += sql.GetSQL(params={"col": col, "json_data": logs[idx]})
                MYPGuard.MYP("log").Exec(cursql)  # 執行寫入game_table_log與game_play_log
                self.mLogCaches.clear()  # 寫入後刪除
            if len(self.mVipLog) > 0:
                sql = sSqls["save_vip_log"]
                cursql = ""
                for col, logs in self.mVipLog.items():  # 走訪只會有1筆的vip_log
                    # 結構為{xxxxx: [{xxx: xxx}]}先取得第i筆再取得各自的keys
                    for i in range(len(logs)):  # 走訪每個玩家
                        cursql += sql.GetSQL(params={"col": col, "apikey": logs[i]["apikey"], "game_id": logs[i]["game_id"], "member_id": logs[i]["member_id"], "add_time": logs[i]["add_time"]})
                MYPGuard.MYP("log").Exec(cursql)  # 執行寫入dmgamelog的vip_log
                self.mVipLog.clear()  # 寫入後刪除
            if len(self.mVipPlayer) > 0:
                sql = sSqls["save_vip_player"]
                cursql = ""
                for col, logs in self.mVipPlayer.items():  # 走訪只會有1筆的VIP_player
                    # 結構為{xxxxx: [{xxx: xxx}]}先取得第i筆再取得各自的keys
                    for i in range(len(logs)):  # 走訪每個玩家
                        cursql += sql.GetSQL(params={"col": col, "apikey": logs[i]["apikey"], "game_id": logs[i]["game_id"], "member_id": logs[i]["member_id"]})
                MYPGuard.MYP("game").Exec(cursql)  # 執行寫入dmgame的VIP_player
                self.mVipPlayer.clear()  # 寫入後刪除
        except:
            PrintEXC()

    def OnTMEvt_WaitClose(self, params):
        self.mTEngine.AddTimer(TIME_WAIT_CLOSE, self.OnTMEvt_WaitClose, None)
        try:
            nowTime = GetServerTime()
            delkeys = []
            for id, t in self.mWaitClose.items():
                if t < nowTime - 3:
                    pNetParams = self.GetNetBindParams(id)
                    if pNetParams is not None:
                        self.mServer.SafeClose(id)
                        del self.mID2Conn[id]
                        delkeys.append(id)
            if len(delkeys) > 0:
                for i in range(len(delkeys)):
                    del self.mWaitClose[delkeys[i]]
        except:
            PrintEXC()

    def OnTMEvt_CheckOffline(self, params):
        self.mTEngine.AddTimer(TIME_CHECK_TABLE_OFFLINE, self.OnTMEvt_CheckOffline, None)
        try:
            nowTime = GetServerTime()
            for i in range(ServiceOpt.sTableCount):
                mTableFrame = self.mTables[i]
                if mTableFrame is not None:
                    mTableFrame.OnCheckOfflineUser(nowTime)
        except:
            PrintEXC()

    def OnTMEvt_UpdatePlayer(self, params):
        try:
            rp = RDSPGuard.RP("gamelist")
            rp.LibGrd.R.hset("sha@onlinenums", ServiceOpt.sSvrUUID, SvrUsrMgr.GetUserItemCount())
            '''
            if SvrUsrMgr.bModify:
                rp = RDSPGuard.RP("gamelist")
                rp.LibGrd.R.hset("sha@onlinenums", ServiceOpt.sSvrUUID, SvrUsrMgr.GetUserItemCount())
                SvrUsrMgr.bModify = False
            '''
            return True
        except:
            PrintEXC()
        return True

    def OnTMEvt_RetryTime(self, params):  # 將從後臺取得的retry_times寫入redis
        try:
            '''
            #新架構須透過判斷不同商戶的db idx, 先暫時寫死次數
            parameters = {"host_api_key": str(ServiceOpt.sHostApiKey)}
            retry_times = self.SlotGame("get_retry_times", parameters, "slotGame")
            rp_re = RDSPGuard.RP("game")
            retry_times = int(retry_times) if retry_times else 3  # 後臺若未設定則預設為3次
            rp_re.LibGrd.R.hset("sha@chl_" + str(ServiceOpt.sHostApiKey), "retry_times", retry_times)
            '''
            
            rp_re = RDSPGuard.RP("game")
            rp_re.LibGrd.R.hset("sha@chl_" + str(ServiceOpt.sHostApiKey), "retry_times", 3)
        except:
            PrintEXC()

    # 共享方反饋正常，向redis撤銷base.txn_id單號(base, game_bet_err_log異常資料, 共享方回應內容)
    def _SuccessRefundbetAndWriteBase(self, account_base, refundbet_error_result, response):
        Warn("--- OnUserTranslate(once bet error) Game to PS member_id=", account_base.sdk_uuid,
             " score=", account_base.score, " - ", account_base.score, f"sn:{account_base.sn}")
        account_base.score = 0  # 改成直接清零
        # 写日志
        data = {"txn": refundbet_error_result["txn_id"], "host": refundbet_error_result["host_api_key"],
                "type": 0, "memberid": account_base.sdk_uuid,
                "amount": response["balance"], "time": GetServerTimeStr()}
        self.TradeLog("add_sharingtradelog", data, refundbet_error_result["host_api_key"])
        account_base.txn_id = "0"
        account_buffer = account_base.SerializeToString()
        rp2 = RDSPGuard.RP("gamelog")
        rp2.LibGrd.Call("common.SetInfoBySYS", *(refundbet_error_result["uuid"], account_buffer))

    ##--------------------------------------------------------
    # 发送消息
    def SendToGameService(self, wMainCmdID, wSubCmdID, pbMsg):
        if self.mGSClient is not None:
            self.mGSClient.SendProtoMsg(wMainCmdID, wSubCmdID, pbMsg)

    def SendDataToGameService(self, wMainCmdID, wSubCmdID, pData=None):
        if self.mGSClient is not None:
            self.mGSClient.SendMsg(wMainCmdID, wSubCmdID, pData)

    def SendToClient(self, socketid, wMainCmdID, wSubCmdID, proto):
        self.mServer.SendProtoMsg(socketid, wMainCmdID, wSubCmdID, proto)

    def SendDataToClient(self, socketid, wMainCmdID, wSubCmdID, pBuffer = None):
        self.mServer.SendMsg(socketid, wMainCmdID, wSubCmdID, pBuffer)

    def SendToTableClient(self, wTableID, wMainCmdID, wSubCmdID, proto):
        if wTableID < 0 or wTableID >= INVALID_CHAIR:
            return
        mTableFrame = self.mTables[wTableID]
        if mTableFrame is None:
            return
        buffer = proto.SerializeToString()
        for wChair in range(ServiceAttr.sChairCnt):
            srvItem = mTableFrame.GetTableUserItem(wChair)
            if srvItem is not None and not srvItem.IsAndroidUser:
                self.mServer.SendMsg(srvItem.SocketID, wMainCmdID, wSubCmdID, buffer)

    def OnGS_MsgRegister(self, dispatcher):
        dispatcher.registe(e_msgid_game_register, e_c_msgid_register_server, self.OnMsgGSRegistResult)
        dispatcher.registe(e_msgid_ctl, e_cl_msgid_ctl_request, self.OnMsgCtrl)
        dispatcher.registe(e_msgid_ctl, e_cl_msgid_ctl_dismissgame, self.registeDisMissGame)
        dispatcher.registe(e_msgid_ctl, e_cl_msgid_ctl_dismissroom, self.registeDisMissRoom)

    def OnSrv_MsgRegister(self, dispatcher):
        dispatcher.registe(e_msgid_game_login, e_cg_msgid_login, self.OnMsgLogon)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet, self.InGameGetBalance)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_transfer_money , self.InGameTranslate)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_sitdown, self.OnMsgSitDown)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_standup, self.OnMsgStandUp)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_enter_table, self.OnMsgEnterTable)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_match, self.OnMsgMatch)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_create_toom, self.OnMsgCreateRoom)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_join_room, self.OnMsgJoinRoom)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_start_game, self.OnMsgStartGame)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_changetable, self.OnMsgChangeTable)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_ready, self.OnMsgReady)
        dispatcher.registe(e_msgid_monitor, e_c_msgid_server_monitor, self.OnMsgMonitor)
        dispatcher.registe(e_msgid_game_action, e_cg_msgid_heartbeat_speed, self.OnMsgHeartBeat)

    def OnCtrlToolFuncRegister(self):
        self.mCtrlFunc[b"kick_user"] = self.OnToolKickUser
        self.mCtrlFunc[b"reload_cfg"] = self.OnToolReLoadCfg
        self.mCtrlFunc[b"enable"] = self.OnToolEnable

    def OnSrv_OnNetLinked(self, conn):
        if not self.mApp.mRunning:
            return

        try:
            id = conn.GetID()
            ip = conn.GetIP()

            INFO("[OnSrv_OnNetLinked-新建连接] IP: %s, ID：%d", ip, id)
            pNetParams = self.GetNetBindParams(id)
            if pNetParams is not None:
                pNetParams.mSocketID = id
                pNetParams.mIpAddr = ip
        except:
            PrintEXC()

    def OnSrv_OnNetClose(self, conn):
        try:
            id = conn.GetID()
            ip = conn.GetIP()
            uuid = ""

            pNetParams = self.GetNetBindParams(id)
            if pNetParams is not None:
                pSvrUserItem = pNetParams.mISvrUserItem
                # 用户处理
                if pSvrUserItem is not None:
                    uuid = pSvrUserItem.mUserInfo.mUUID
                    INFO("[OnSrv_OnNetClose-断开连接] IP:%s, ID:%d, UUID:%s", ip, id, uuid)

                    if pSvrUserItem.bMate:
                        self.mMatcher.DelMatchItem(pSvrUserItem)
                    if pSvrUserItem.TableID != INVALID_TABLE \
                            and pSvrUserItem.ChairID != INVALID_CHAIR:
                        pSvrUserItem.Detach()
                        if self.mTables[pSvrUserItem.TableID].PerformStandUpAction(pSvrUserItem, 0):
                            self.OnEventUserLogout(pSvrUserItem, logout_offline, True)
                        else:
                            self.mTables[pSvrUserItem.TableID].OnEventUserOffLine(pSvrUserItem)
                    else:
                        self.OnEventUserLogout(pSvrUserItem, logout_user, True)

            if not uuid and len(uuid) == 0:
                INFO("[OnSrv_OnNetClose-断开连接] IP:%s, ID:%d", ip, id)

            # 清除信息
            if id in self.mWaitClose:
                del self.mWaitClose[id]
            if id in self.mID2Conn:
                del self.mID2Conn[id]
        except:
            PrintEXC()

    def OnSrv_SGMessage(self, conn, wMainCmdID, wSubCmdID, data, size):
        try:
            #DEBUG("OnSrv_SGMessage, wMainCmdID = %d, subId = %d", wMainCmdID, wSubCmdID)
            if wMainCmdID > e_msgid_child_begin and wMainCmdID < e_msgid_child_end:
                srvUserItem = self.GetNetBindUserItem(conn.GetID())
                if srvUserItem is not None:
                    if srvUserItem.TableID == INVALID_TABLE \
                            or srvUserItem.ChairID == INVALID_CHAIR:
                        return
                    mTableFrame = self.mTables[srvUserItem.TableID]
                    if mTableFrame is not None:
                        mTableFrame.OnEventSocketGame(wSubCmdID, data, srvUserItem)
        except:
            PrintEXC()

    # --------------------------------- Tools ----------------------------------
    def SendGSRegister(self):
        try:
            sendmsg = msg_register_server()
            sendmsg.server_uuid = ServiceOpt.sSvrUUID.encode('utf-8')
            sendmsg.hash_key = ServiceOpt.sHashKey.encode('utf-8')
            sendmsg.host_api_key = ServiceOpt.sHostApiKey.encode('utf-8')
            sendmsg.subgame_id = ServiceOpt.sSubGameId
            sendmsg.server_addr = self.mApp.mConfigs["svr_addr"].encode('utf-8')
            sendmsg.server_port = ServiceOpt.sSvrPort
            sendmsg.server_type = ServiceOpt.sSvrType
            sendmsg.cell_score = ServiceOpt.sCellScore
            sendmsg.admission_score = ServiceOpt.sMinEnterScore
            sendmsg.max_player = ServiceOpt.sMaxPlayer
            sendmsg.cur_player = SvrUsrMgr.GetUserItemCount()
            self.SendToGameService(e_msgid_game_register, e_c_msgid_register_server, sendmsg)
        except:
            PrintEXC()

    def OnMsgGSRegistResult(self, conn, pData, nSize):
        response = msg_register_server_ret()
        response.ParseFromString(pData)
        if response.ret == e_error_ok:
            Info("向游戏服务注册成功")
        else:
            Info("向游戏服务注册失败，错误码：%d" % response.ret)

    def OnToolKickUser(self, contextId, mJsonData):
        nKickUUID = int(mJsonData["uuid"])
        if nKickUUID <= 0:
            self.KickAllUser()
            return
        srvUserItem = SvrUsrMgr.GetSrvUserItem(nKickUUID)
        if srvUserItem is None:
            return
        #删除匹配信息
        self.mMatcher.DelMatchItem(srvUserItem)

        if srvUserItem.TableID != INVALID_TABLE:
            mTableFrame = self.mTables[srvUserItem.TableID]
            if mTableFrame is not None:
                mTableFrame.KickUser(srvUserItem.ChairID, logout_kicked)

    def OnToolReLoadCfg(self, contextId, mJsonData):
        #加载游戏配置文件
        if not self.mGModule.LoadConfig(ServiceOpt.sSvrName):
            raise AttemperError("加载游戏配置文件失败！")
        #加载游戏设定
        self.LoadGameServerInfo()
        #更新游戏列表
        self.SendGSRegister()
        '''
        rp = RDSPGuard.RP("gamelist")
        opts = rp.LibGrd.R.hget("sha@svropts", str(ServiceOpt.sComboLevel))
        if opts is not None:
            options = json.loads(opts.decode())
            ServiceOpt.InitDynOptions(options)
            Info("更新游戏设定", options)
        '''
        Info("重载游戏配置文件完成")

    def OnToolEnable(self, contextId, mJsonData):
        Info("设置游戏是否生效", mJsonData)
        bEnable = True if int(mJsonData["enable"]) == 1 else False
        if (bEnable and self.mApp.mRunning) or (not bEnable and not self.mApp.mRunning):
            return
        self.mApp.mRunning = bEnable
        if not bEnable:
            self.Conclude()
            self.KickAllUser()

    def OnMsgCtrl(self, conn, data, size):
        request = msg_clt_request()
        request.ParseFromString(data)
        try:
            if request.rpc_name in self.mCtrlFunc:
                rpc_name = self.mCtrlFunc[request.rpc_name]
                rpc_name(request.context_id,json.loads(request.json.decode()))
            else:
                Info("OnMsgCtrl", request)
        except:
            PrintEXC()

    # 從center→OnWebEventKickUser進入。準備解散整桌
    def registeDisMissGame(self, conn, data, size):
        request = msg_clt_request()
        request.ParseFromString(data)
        try:
            find_player = False  # 找到目標玩家桌子的標籤
            if request.nick_name != None:  # 送進來的proto有玩家名稱
                for table_id in range(ServiceOpt.sTableCount):  # 走訪此廳的所有桌
                    mTableFrame = self.mTables[table_id]  # 取得整桌資訊
                    for player in range(4):  # 走訪整桌的4個人，無論是否有4人都要走訪4人
                        # 是否有此人的資訊
                        if mTableFrame != None and mTableFrame.mUserItemArr[player] != None:
                            # 檢查此玩家名稱與來源商戶是否為指定目標玩家名稱與來源商戶
                            if mTableFrame.mUserItemArr[player].mUserInfo.mNickName == request.nick_name \
                                    and mTableFrame.mUserItemArr[player].mUserInfo.mChannel == request.channel:
                                # manual_dismiss = True。手動解散，非建置環境或維護時解散
                                # 解散整桌
                                mTableFrame.DisMissGame(manual_dismiss=True)
                                Log("目標商戶{}指定玩家{}所在的整桌成功解散".format(request.channel, request.nick_name))
                                find_player = True
                                break
            if find_player == False:
                Log("指定玩家{}不在遊戲中".format(request.nick_name))
        except:
            PrintEXC()

    # 從center→OnWebEventKickUser進入。準備解散整廳
    def registeDisMissRoom(self, conn, data, size):
        request = msg_clt_request()
        request.ParseFromString(data)
        try:
            find_player = False  # 找到目標玩家桌子的標籤
            for table_id in range(ServiceOpt.sTableCount):  # 走訪此廳的所有桌
                mTableFrame = self.mTables[table_id]  # 取得整桌資訊
                # manual_dismiss = True。手動解散，非建置環境或維護時解散
                # 解散整桌
                mTableFrame.DisMissGame(manual_dismiss=True)
                find_player = True
            if find_player == False:
                Log("指定廳沒有任何玩家在遊戲中")
        except:
            PrintEXC()

    def OnGS_OnNetLinked(self, conn):
        DEBUG("服务器连接成功，开始注册到游戏服务")
        try:
            self.SendGSRegister()
        except:
            PrintEXC()

    def OnGS_OnNetClose(self, conn):
        Info("服务器连接关闭，30秒后重新连接")
        if self.mReTimer is None:
            self.mReTimer = self.mTEngine.AddTimer(30, self.InitGS, None)

    def ReadGameServerInfo(self, hint, result):
        if len(result) == 1:
            try:
                data = result[0]
                ServiceOpt.InitOptions(data)
                #Info("房间配置预览：", data)
                #Info(json.dumps(data, indent = 4))
                self.mServiceOpt = ServiceOpt
            except:
                PrintEXC()
                ServiceOpt.sHostApiKey = "-1"
        else:
            ServiceOpt.sHostApiKey = "-1"

    def ReadUpdateGameServerInfo(self, hint, result):
        """將讀到的資料寫入 ServiceOpt 中

        只寫入允許修改的部份

        Args:
            hint (None): 不清楚代表什麼，但顯示出來看就是  None
            result (list): dict 串列，dict 為此伺服器的設定值

        """
        if len(result) == 1:
            try:
                data = result[0]
                ServiceOpt.HotUpdate(data)
            except:
                PrintEXC()
        else:
            Err('Hot Update Failed, MYSQL 沒有取得到資料')

    def InitTables(self):
        for wTable in range(ServiceOpt.sTableCount):
            mTableFrame = TableFrame()
            if not mTableFrame.Init(wTable, self):
                return False
            #nChairCnt = ServiceAttr.sChairCnt
            #for wChair in range(nChairCnt):
            #    nSeatSig = ((wTable & 0xffff) << 16) | (wChair & 0xffff)
            #    self.mIdleSeats.put(nSeatSig)
            self.mTables.append(mTableFrame)
        return True

    def GetNetBindParams(self, nSocketID):
        if nSocketID in self.mID2Conn:
            return self.mID2Conn[nSocketID]
        sNetParams = stNetBindParams()
        self.mID2Conn[nSocketID] = sNetParams
        return sNetParams

    def GetNetBindUserItem(self, dwSocketID):
        sNetParams = self.GetNetBindParams(dwSocketID)
        if sNetParams is not None:
            return sNetParams.mISvrUserItem
        return None

    def set_wallet_type_2_user_item(self, wallet_type, uuid):
        """設定玩家的錢包類型到 SvrUserItem.SvrUserInfo 中

        Args:
            wallet_type (int): 0 獨立錢包，1 共享錢包
            uuid (int): 玩家的 uuid
        """
        user_item = SvrUsrMgr.GetSrvUserItem(uuid)

        if user_item:
            user_item.mUserInfo.wallet_type = wallet_type

    def InGameGetBalance(self, conn, pData, size):
        try:
            # 关服之后不接受登录
            if not self.mApp.mRunning:
                wallet_after = main_and_dummy_wallet_ret()
                wallet_after.error_code = 1
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet,wallet_after)
                return
            request = main_and_dummy_wallet()
            request.ParseFromString(pData)

            if ServiceOpt.IsEducateSvr():
                wallet_after = main_and_dummy_wallet_ret()
                wallet_after.error_code = 0
                # 金額這樣設定可避免一下子就超出桌子上限
                wallet_after.balance = int(ServiceOpt.sMaxScore//2)
                wallet_after.temp_wallet = 0
                wallet_after.min_admission = int(ServiceOpt.sMaxScore//2)
                wallet_after.max_admission = ServiceOpt.sMaxScore
                wallet_after.subgame_id = ServiceOpt.sSubGameId
                self.SendToClient(conn.GetID(), e_msgid_game_action,
                                  e_cg_msgid_main_and_dummy_wallet,
                                  wallet_after)
                return

            rp = RDSPGuard.RP("game")
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(request.multi_host_uuid,))
            if account_res[0] != 0:
                wallet_after = main_and_dummy_wallet_ret()
                wallet_after.error_code = 1
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet,wallet_after)
                return -1, "error"

            balance = 0
            account_base = db_data_user()
            account_base.ParseFromString(account_res[1])
            host_api_key = account_base.channel

            # 測試人員避開 API，直接傳金額給前端
            if account_base.user_type == 999:
                wallet_after = main_and_dummy_wallet_ret()
                wallet_after.error_code = 0
                wallet_after.balance = 1000000000 # 直接給測試人員 10000000 元，跟 getbalance 一樣
                wallet_after.temp_wallet = account_base.score
                wallet_after.min_admission = ServiceOpt.sMinEnterScore
                wallet_after.max_admission = ServiceOpt.sMaxScore
                wallet_after.subgame_id = ServiceOpt.sSubGameId
                self.SendToClient(conn.GetID(), e_msgid_game_action,
                                  e_cg_msgid_main_and_dummy_wallet,
                                  wallet_after)
                return

            # 錢包類型
            single_host_api_key = account_base.sin_channel

            multi_inf = rp.LibGrd.R.hget("multi@inf_" + host_api_key, single_host_api_key)
            multi_inf = json.loads(multi_inf)

            wallet_type = 0
            if "host_url" in multi_inf.keys():
                wallet_type = 1

            self.set_wallet_type_2_user_item(wallet_type, account_base.uuid)

            chl_resp = rp.LibGrd.Call("channel.GetInfo", *(ServiceOpt.sHostApiKey,))
            if chl_resp[0] == 0:
                # tmp = OnRedisResultParser(chl_resp[1])
                # ctm_data = json.loads(tmp["extra"])
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                #     gs_url = ctm_data["gs_url"]
                #     host_chl = "CARD_" + host_api_key
                #     if host_chl in gs_url:
                #         gs_url = gs_url[host_chl]

                if wallet_type == 0:  # 獨立錢包
                    # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                    #     url = RequestHelper.DoPost(gs_url + "/hosturl", {"host_api_key": account_base.channel})
                    #     url = url["data"]["getbalance"]
                    # else:
                    url = multi_inf["ps_urls"]["getbalance"]
                    response = RequestHelper.DoPost(url, {"host_api_key": account_base.sin_channel,
                                                          "member_id": account_base.sdk_uuid})
                    # response = json.loads(response)
                    if response["status_code"] != 0:
                        wallet_after = main_and_dummy_wallet_ret()
                        wallet_after.error_code = 1
                        self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet,wallet_after)
                        return response["status_code"], ""
                    balance = response["balance"]
                    wallet_after = main_and_dummy_wallet_ret()
                    wallet_after.error_code = 0
                    wallet_after.balance = balance
                    wallet_after.temp_wallet = account_base.score
                    wallet_after.min_admission = ServiceOpt.sMinEnterScore
                    wallet_after.max_admission = ServiceOpt.sMaxScore
                    wallet_after.subgame_id = ServiceOpt.sSubGameId
                    self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet, wallet_after)

                elif wallet_type == 1:  # 共享錢包
                    txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                    host_url = multi_inf["host_url"]
                    dl_url = host_url["base_url"] + "/" + host_url["getbalance"]
                    err_msg = ', memberid: ' + str(account_base.sdk_uuid)
                    data = {"txn": txn_id, "host": account_base.sin_channel, "type": 6, "action": 6,
                            "err_code": 1, "err_descr": 'response error' + err_msg, "time": GetServerTimeStr()}
                    self.TradeLog("add_hosterrlog", data, host_api_key)
                    response = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode()})
                    self.TradeLog("delete_hosterrlog", data, host_api_key)
                    if response == None:
                        err_msg = ", memberid: " + str(account_base.sdk_uuid)
                        data = {"txn": txn_id, "host": account_base.sin_channel, "type": 6, "action": 6,
                                "err_code": 4,
                                "err_descr": "results == None, " + err_msg,
                                "time": GetServerTimeStr()}
                        self.TradeLog("add_hosterrlog", data, host_api_key)
                        wallet_after = main_and_dummy_wallet_ret()
                        wallet_after.error_code = 1
                        self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet,
                                          wallet_after)
                        return -5, "error"
                    elif response["status_code"] != 0:
                        err_msg = ', memberid: ' + str(account_base.sdk_uuid)
                        data = {"txn": txn_id, "host": account_base.sin_channel, "type": 6, "action": 6,
                                "err_code": 4,
                                "err_descr": 'response_status_code: ' + str(response["status_code"]) + err_msg,
                                "time": GetServerTimeStr()}
                        self.TradeLog("add_hosterrlog", data, host_api_key)
                        wallet_after = main_and_dummy_wallet_ret()
                        wallet_after.error_code = 1
                        self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet,
                                          wallet_after)
                        return response["status_code"], ""
                    balance = response["balance"]
                    wallet_after = main_and_dummy_wallet_ret()
                    wallet_after.error_code = 0
                    wallet_after.balance = balance
                    wallet_after.temp_wallet = account_base.score
                    wallet_after.min_admission = ServiceOpt.sMinEnterScore
                    wallet_after.max_admission = ServiceOpt.sMaxScore
                    wallet_after.subgame_id = ServiceOpt.sSubGameId
                    self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_main_and_dummy_wallet, wallet_after)
                    return

                else:
                    return -6, "wallet_type error"

        except:
            PrintEXC()

    def _in_game_translate_for_tester(self, conn, request, account_res, pSvrUserItem, rp):
        """處理測試人員的轉錢操作

        獨立錢包：玩家的錢 = 廳的上限值
        共享錢包：玩家的錢 = 前端選擇的金額

        將帶入廳的金額傳給前端、設定到物件中、存到 redis
        """
        if request.money > ServiceOpt.sMaxScore:
            tranout = ServiceOpt.sMaxScore
        else:
            tranout = request.money

        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])

        account_base.score = tranout
        transfer_money_after = transfer_money_ret()
        transfer_money_after.error_code = 0
        transfer_money_after.temp_wallet = account_base.score
        transfer_money_after.faceid = account_base.faceid
        transfer_money_after.nickname = account_base.nickname
        self.SendToClient(conn.GetID(), e_msgid_game_action,
                          e_cg_msgid_transfer_money,
                          transfer_money_after)

        pSvrUserItem.mUserInfo.mScore = account_base.score
        account_buffer = account_base.SerializeToString()
        rp.LibGrd.Call("common.SetInfoBySYS",
                       *(request.multi_host_uuid, account_buffer))

    def _send_fake_data_to_ps_db(self, account_base, host_id, main_service_url):
        """call API 寫假資料到 PS DB 的 accounting 表

        為了要在 bet 時拿到 sn 所寫的

        Args:
            account_base (proto): 玩家的資料
            host_id (byte): 商戶名稱
            main_service_url (str): service 的網址
        """
        rp = RDSPGuard.RP("game")
        multi_inf = rp.LibGrd.R.hget("multi@inf_" + account_base.channel, account_base.sin_channel)
        multi_inf = json.loads(multi_inf)
        data = {
            "multi_inf":multi_inf,
            "host_id": multi_inf["host_id"] ,
            "game_id": account_base.game_id,
            "subgame_id": ServiceOpt.sSubGameId,
            "member_id": account_base.sdk_uuid,
        }

        response = RequestHelper.DoPost(f'{main_service_url}/writeslotgameaccounting', data)
        if response is not None and response.get("status_code") == 0:
            return True

        return False

    def _get_sn_from_ps_db(self, account_base, host_id, main_service_url):
        """call API 從 PS DB 的 accounting 表拿預先寫好的假資料 SN

        Args:
            account_base (proto): 玩家的資料
            host_id (byte): 商戶名稱
            main_service_url (str): service 的網址
        """
        rp = RDSPGuard.RP("game")
        multi_inf = rp.LibGrd.R.hget("multi@inf_" + account_base.channel, account_base.sin_channel)
        multi_inf = json.loads(multi_inf)
        data = {
            "multi_inf":multi_inf,
            "host_id": multi_inf["host_id"] ,
            "game_id": account_base.game_id,
            "subgame_id": ServiceOpt.sSubGameId,
            "member_id": account_base.sdk_uuid,
        }

        response = RequestHelper.DoPost(f'{main_service_url}/getslotgameaccountingsn', data)
        if response is not None and response.get("status_code") == 0:
            return response.get("sn")

        return None

    def _delete_fake_data_from_ps_db(self, account_base):
        """刪除 PS DB accounting 表內假的資料

        沒有走完正常的流程要刪除資料表資料 & 玩家 base
        """
        rp = RDSPGuard.RP("game")
        multi_inf = rp.LibGrd.R.hget("multi@inf_" + account_base.channel, account_base.sin_channel)
        multi_inf = json.loads(multi_inf)
        sqlp = MYPGuard.MYP(multi_inf["db_id"])
        sql = sSqls["delete_ps_db_accounting"]
        result = sqlp.Exec(sql=sql.GetSQL(params={"sn": account_base.sn}))

        account_base.sn = 0
        UserRP.set_account_base(account_base)

    def InGameTranslate(self, conn, pData, size):
        timeout_flag = None  # 標記發生 timeout error 的區塊
        try:
            request = transfer_money()
            request.ParseFromString(pData)

            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem.mUserInfo == None:
                return 8, "error"

            rp = RDSPGuard.RP("game")
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(request.multi_host_uuid,))
            if account_res[0] != 0:
                transfer_money_after = transfer_money_ret()
                transfer_money_after.error_code = 1
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                                  transfer_money_after)
                return -1, "error"

            if ServiceOpt.IsEducateSvr():
                transfer_money_after = transfer_money_ret()
                transfer_money_after.error_code = 0
                transfer_money_after.temp_wallet = request.money
                transfer_money_after.faceid = 17
                transfer_money_after.nickname = 'GUEST'
                self.SendToClient(conn.GetID(), e_msgid_game_action,
                                  e_cg_msgid_transfer_money,
                                  transfer_money_after)

                pSvrUserItem.mUserInfo.mScore = request.money
                return

            account_base = db_data_user()
            account_base.ParseFromString(account_res[1])

            # 測試人員避開 API，直接傳金額給前端
            if account_base.user_type == 999:
                self._in_game_translate_for_tester(conn, request, account_res, pSvrUserItem, rp)

                return

            host_api_key = account_base.channel
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商維護
            #     rp2 = RDSPGuard.RP("gamelist")
            #     # 單代理商向var@maintain_取得本代理商在多代理商的狀態
            #     host_maintain = rp2.LibGrd.R.get("var@maintain_" + account_base.channel)
            #     # host_maintain = host_maintain.decode("utf-8")  # 取得維護狀態後的解析
            #     if host_maintain:  # 如果狀態是維護
            #         transfer_money_after = transfer_money_ret()
            #         transfer_money_after.error_code = 1
            #         self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
            #                           transfer_money_after)
            #         return -11, "maintain"  # 禁止此商戶的所屬玩家轉錢
            if account_base.banned == 1:
                transfer_money_after = transfer_money_ret()
                transfer_money_after.error_code = 1
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                                  transfer_money_after)
                return -8, "banned"

            # 錢包類型
            single_host_api_key = account_base.sin_channel
            multi_inf = rp.LibGrd.R.hget("multi@inf_" + host_api_key, single_host_api_key)
            multi_inf = json.loads(multi_inf)

            wallet_type = 0
            if "host_url" in multi_inf.keys():
                wallet_type = 1

            # 若遊戲錢包有錢，而且為獨立錢包時
            if account_base.score != 0 and wallet_type == 0:
                transfer_money_after = transfer_money_ret()
                transfer_money_after.error_code = 1
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                                  transfer_money_after)
                return -7, "account_base.score != 0"  # 阻擋重複轉入

            # 取得min_score
            minscore = ServiceOpt.sMinEnterScore
            # 取得max_score
            maxscore = ServiceOpt.sMaxScore

            tranout = 0
            if request.money < minscore or request.money <= 0:
                transfer_money_after = transfer_money_ret()
                transfer_money_after.error_code = 1
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                                  transfer_money_after)
                return -5, "invalid money"
            elif request.money > maxscore:
                tranout = maxscore
            else:
                tranout = request.money

            chl_resp = rp.LibGrd.Call("channel.GetInfo", *(ServiceOpt.sHostApiKey,))
            if chl_resp[0] == 0:
                tmp = OnRedisResultParser(chl_resp[1])
                ctm_data = json.loads(tmp["extra"])

                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                #     gs_url = ctm_data["gs_url"]
                #     host_chl = "CARD_" + host_api_key
                #     if host_chl in gs_url:
                #         gs_url = gs_url[host_chl]

                # 拿單代理的 service 的 url
                main_service_url = ctm_data["gs_url"]["CARD"]

            host_id = rp.LibGrd.R.hget("sha@chl_" + host_api_key, "name")
            # 共享錢包refund
            if account_base.sn and account_base.sn != 0 and wallet_type == 1:
                host_url = multi_inf["host_url"]
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                #     host_url = RequestHelper.DoPost(gs_url + "/hosturl", {"host_api_key": account_base.channel})
                #     host_url = host_url["data"]
                # else:
                #     host_url = rp.LibGrd.R.hget("sha@chl_" + ServiceOpt.sHostApiKey, "host_url")
                #     host_url = json.loads(host_url.decode())
                dl_url = host_url["base_url"] + "/" + host_url["refundbet"]
                response = RequestHelper.DoGet(dl_url,
                                               {"access_token": account_res[4].decode(), "txn_id": account_base.sn})
                txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                if response and response["status_code"] == 0:  # 若共享方反饋正常
                    # 向redis撤銷base.txn_id單號
                    refundbet_error_result = {"txn_id": txn_id, "host_api_key": account_base.sin_channel,
                                              "uuid": request.multi_host_uuid}
                    self._SuccessRefundbetAndWriteBase(account_base, refundbet_error_result, response)
                    self._delete_fake_data_from_ps_db(account_base)
                else:
                    # refundbet失敗
                    status = -100 if response == None else response["status_code"]
                    refundbet_data = {"txn_id": txn_id, "uuid": request.multi_host_uuid,
                                      "member_id": str(account_base.sdk_uuid), "host_api_key": account_base.sin_channel,
                                      "amount": tranout, "status": status, "date": GetServerTimeStr()}
                    # 寫入game_bet_error_log資料表
                    self.TradeLog("insert_once_refundbet_error", refundbet_data, host_api_key)

                    err_msg = ", memberid: " + str(account_base.sdk_uuid) + ", bet: " + str(tranout)
                    data = {"txn": txn_id, "host": account_base.sin_channel, "type": 0, "action": 1,
                            "err_code": 4,
                            "err_descr": "results == None, " + err_msg,
                            "time": GetServerTimeStr()}
                    self.TradeLog("add_hosterrlog", data, host_api_key)
                    transfer_money_after = transfer_money_ret()
                    transfer_money_after.error_code = 1
                    self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                                      transfer_money_after)
                    Warn("--- OnUserTranslate Game to PS Failed member_id=", account_base.sdk_uuid, " score=",
                         account_base.score, " - ", tranout, " response=None", f"sn:{account_base.sn}")

                    return -5, "error"

            send_fake_data_result = self._send_fake_data_to_ps_db(account_base, host_id,
                                                                  main_service_url)
            if send_fake_data_result is False:
                return -14, "send fake data to ps db failed"
            sn = self._get_sn_from_ps_db(account_base, host_id, main_service_url)
            if sn is None:
                self._delete_fake_data_from_ps_db(account_base)
                return -14, "get sn from ps db failed"

            account_base.sn = sn
            UserRP.set_account_base(account_base)
            if wallet_type == 0:  # 獨立錢包
                txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                #     timeout_flag = -1
                #     url = RequestHelper.DoPost(gs_url + "/hosturl", {"host_api_key": account_base.channel})
                #     url = url["data"]["rollout"]
                # else:
                #     url = self.mApp.mConfigs["ps_urls"]["rollout"]
                timeout_flag = 1
                # response = RequestHelper.DoPost(url, {"host_api_key": account_base.channel,
                #                                       "member_id": account_base.sdk_uuid,
                #                                       "txn_id": txn_id, "amount": tranout})
                # # response = json.loads(response)
                # if response["status_code"] != 0:
                #     transfer_money_after = transfer_money_ret()
                #     transfer_money_after.error_code = 1
                #     self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                #                       transfer_money_after)
                #     Warn("--- InGameTranslate PS to Game Failed member_id=", account_base.sdk_uuid, " score=", account_base.score, " - balance=", tranout, " response=", response)
                #     self._delete_fake_data_from_ps_db(account_base)
                #     return response["status_code"], ""

                parameters = {
                    "amount": tranout,
                    "host_id": multi_inf["host_id"],
                    "id": account_base.sdk_uuid
                }
                update_rollout_member = self.SlotGame("update_rollout_member", parameters, multi_inf["db_id"]) # 從slotgame轉出錢

                parameters = {
                    "txn_id": txn_id,
                    "type": 1,
                    "host_id": multi_inf["host_id"],
                    "member_id": account_base.sdk_uuid,
                    "amount": tranout,
                    "note": "RollOut",
                    "id": account_base.sdk_uuid
                }
                insert_funds_log = self.SlotGame("insert_funds_log", parameters, multi_inf["db_id"]) # 寫入fundslog

                response = {}
                response["status_code"] = 0 # 成功後response = 0

                Warn("--- InGameTranslate PS to Game member_id=", account_base.sdk_uuid, " score=", account_base.score, " - balance=", tranout)

            else:  # 共享錢包
                host_url = multi_inf["host_url"]
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                #     timeout_flag = -2
                #     host_url = RequestHelper.DoPost(gs_url + "/hosturl", {"host_api_key": account_base.channel})
                #     host_url = host_url["data"]
                # else:
                #     host_url = rp.LibGrd.R.hget("sha@chl_" + ServiceOpt.sHostApiKey, "host_url")
                #     host_url = json.loads(host_url.decode())

                # 正式轉入
                txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                dl_url = host_url["base_url"] + "/" + host_url["bet"]

                err_msg = ", bet: " + str(tranout) + ", memberid: " + str(account_base.sdk_uuid)
                data = {"txn": txn_id, "host": account_base.sin_channel, "type": 0, "action": 1,
                        "err_code": 1, "err_descr": "response error" + err_msg, "time": GetServerTimeStr()}
                self.TradeLog("add_hosterrlog", data, host_api_key)

                timeout_flag = 3
                response = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode(), "txn_id": sn,
                                                         "total_bet": tranout, "game_id": account_base.game_id,
                                                         "subgame_id": ServiceOpt.sSubGameId,
                                                         "ts": GetServerTime()})

                self.TradeLog("delete_hosterrlog", data, host_api_key)
                if not response:
                    # bet失敗，先進行1次refundbet
                    dl_url = host_url["base_url"] + "/" + host_url["refundbet"]
                    response2 = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode(), "txn_id": sn})
                    self._delete_fake_data_from_ps_db(account_base)

                    if response2 and response2["status_code"] == 0:  # 若共享方反饋正常
                        # 向redis撤銷base.txn_id單號
                        refundbet_error_result = {"txn_id": txn_id, "host_api_key": account_base.sin_channel,
                                                  "uuid": request.multi_host_uuid}
                        self._SuccessRefundbetAndWriteBase(account_base, refundbet_error_result, response2)
                        return -13, "bet error and refundbet correct"
                    else:
                        # refundbet還是失敗
                        status = -100 if response2 == None else response2["status_code"]
                        refundbet_data = {"txn_id": txn_id, "uuid": request.multi_host_uuid,
                                          "member_id": str(account_base.sdk_uuid), "host_api_key": account_base.sin_channel,
                                          "amount": tranout, "status": status, "date": GetServerTimeStr()}
                        # 寫入game_bet_error_log資料表
                        self.TradeLog("insert_once_refundbet_error", refundbet_data, host_api_key)

                        err_msg = ", memberid: " + str(account_base.sdk_uuid) + ", bet: " + str(tranout)
                        data = {"txn": txn_id, "host": account_base.sin_channel, "type": 0, "action": 1,
                                "err_code": 4,
                                "err_descr": "results == None, " + err_msg,
                                "time": GetServerTimeStr()}
                        self.TradeLog("add_hosterrlog", data, host_api_key)
                        transfer_money_after = transfer_money_ret()
                        transfer_money_after.error_code = 1
                        self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                                          transfer_money_after)
                        Warn("--- OnUserTranslate Game to PS Failed member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ", tranout, " response=None", f"sn:{sn}")

                        return -5, "error"

                elif response["status_code"] != 0:
                    # bet失敗，先進行1次refundbet
                    dl_url = host_url["base_url"] + "/" + host_url["refundbet"]
                    response2 = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode(), "txn_id": sn})
                    self._delete_fake_data_from_ps_db(account_base)

                    if response2 and response2["status_code"] == 0:  # 若共享方反饋正常
                        # 向redis撤銷base.txn_id單號
                        refundbet_error_result = {"txn_id": txn_id, "host_api_key": account_base.sin_channel,
                                                  "uuid": request.multi_host_uuid}
                        self._SuccessRefundbetAndWriteBase(account_base, refundbet_error_result, response2)
                        return -13, "bet error and refundbet correct"
                    else:
                        # refundbet還是失敗
                        status = -100 if response2 == None else response2["status_code"]
                        refundbet_data = {"txn_id": txn_id, "uuid": request.multi_host_uuid,
                                          "member_id": str(account_base.sdk_uuid), "host_api_key": account_base.sin_channel,
                                          "amount": tranout, "status": status, "date": GetServerTimeStr()}
                        # 寫入game_bet_error_log資料表
                        self.TradeLog("insert_once_refundbet_error", refundbet_data, host_api_key)

                        err_msg = ", memberid: " + str(account_base.sdk_uuid) + ", bet: " + str(tranout)
                        data = {"txn": txn_id, "host": account_base.sin_channel, "type": 0, "action": 1,
                                "err_code": 4, "err_descr":
                                    "response_status_code: " + str(status) + err_msg,
                                "time": GetServerTimeStr()}
                        self.TradeLog("add_hosterrlog", data, host_api_key)
                        transfer_money_after = transfer_money_ret()
                        transfer_money_after.error_code = 1
                        self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money,
                                          transfer_money_after)
                        Warn("--- OnUserTranslate Game to PS Failed member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ", tranout, " response=", response)
                        return status, ""

            Warn("--- OnUserTranslate Game to PS member_id=", account_base.sdk_uuid, " score=", account_base.score, " + ", account_base.score, " status_code=", response["status_code"], f"sn:{sn}")
            account_base.score += tranout
            account_base.txn_id = txn_id
            pSvrUserItem.mUserInfo.mScore = account_base.score
            account_buffer = account_base.SerializeToString()
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     self.SyncBase(account_base.hostuuid, account_base, account_base.channel)
            rp.LibGrd.Call("common.SetInfoBySYS", *(request.multi_host_uuid, account_buffer))
            Log("auto Translate api", "out", f"sn:{sn} ", response)
            Log("auto Translate rds", "out", f"sn:{sn} ", account_base.score)

            # 写日志
            if wallet_type:
                data = {"txn": txn_id, "host": account_base.sin_channel, "type": 1, "memberid": account_base.sdk_uuid,
                        "amount": tranout,"time": GetServerTimeStr()}
                self.TradeLog( "add_sharingtradelog", data, host_api_key)
            else:
                data = {"txn": txn_id, "host": account_base.sin_channel, "type": 1, "memberid": account_base.sdk_uuid,
                        "amount": tranout,"time": GetServerTimeStr()}
                self.TradeLog("add_tradelog", data, host_api_key)
            transfer_money_after = transfer_money_ret()
            transfer_money_after.error_code = 0
            transfer_money_after.temp_wallet = account_base.score
            transfer_money_after.faceid = account_base.faceid
            transfer_money_after.nickname = account_base.nickname
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_transfer_money, transfer_money_after)

        except Exception as e:
            PrintEXC()
            self._delete_fake_data_from_ps_db(account_base)

            sqlp = MYPGuard.MYP("log")
            sql = sSqls["add_rollout_timeout_err"]

            if timeout_flag in (None, -2):  # 如果發生錯誤時變數為 None or -2 設定預設變數值
                wallet_type = 0
                txn_id = ""
                timeout_flag = timeout_flag if timeout_flag is not None else 0
                tranout = 0

            try:  # 避免沒有 account_base
                host_key = account_base.channel
                member_id = account_base.sdk_uuid
                game_id = account_base.game_id
            except:
                host_key = "no data"
                member_id = "no data"
                game_id = "no data"

            params_dc = {
                "wallet_type": wallet_type,
                "txn_id": txn_id,
                "host_key": account_base.sin_channel,
                "flag": timeout_flag,
                "member_id": member_id,
                "amount": tranout,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            sqlp.Exec(sql=sql.GetSQL(params=params_dc), callback=None)

            mm_url = self.mApp.mConfigs.get("mm_url", "")

            if mm_url and timeout_flag in (1, 3):
                text = f"InGameTranslate {e}| "
                text += f"{game_id}| "
                text += f"member_id: {member_id}| "
                text += f"host_key: {host_key}| "
                text += f"amount: {tranout}"
                try:  # 避免過早跑到 except 沒有 sn 的值
                    text += f"sn: {sn}"
                except:
                    text += f"sn: none"

                RequestHelper.DoPost(mm_url, {"text": text})

    def SyncBase(self, uuid, base, channel):
        try:
            rp = RDSPGuard.RP("gamelog")
            publish_data = {"fnc": "AccountBase", "type": "AccountBase",
                            "data": {"uuid": uuid, "base": MessageToJson(base)}}
            rp.LibGrd.R.publish(channel + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def SyncNewSvrID(self, uuid, channel):
        try:
            rp = RDSPGuard.RP("gamelog")
            publish_data = {"fnc": "AccountNewSvrID", "type": "AccountNewSvrID",
                            "data": {"uuid": uuid, "svr_id": str(ServiceOpt.sSvrUUID)}}
            rp.LibGrd.R.publish(channel + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def SyncDelSvrID(self, uuid, channel):
        try:
            rp = RDSPGuard.RP("gamelog")
            publish_data = {"fnc": "AccountDelSvrID", "type": "AccountDelSvrID",
                            "data": {"uuid": uuid, "svr_id": str(ServiceOpt.sSvrUUID)}}
            rp.LibGrd.R.publish(channel + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def GetTradeLog(self, type):  # 只純粹取得dmgamelog資料庫內容，不寫入不更新，且取得資料不需要多代理商服務
        try:
            sqlp = MYPGuard.MYP("log")
            sql = sSqls[type]
            return sqlp.Exec(sql=sql.GetSQL(params={}), callback=None)
        except:
            PrintEXC()

    def TradeLog(self, type, data, channel):  # 公版寫入或更新dmgamelog資料庫內容
        try:
            sqlp = MYPGuard.MYP("log")
            sql = sSqls[type]
            sqlp.Exec(sql=sql.GetSQL(params=data), callback=None)
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     rp = RDSPGuard.RP("gamelog")
            #     publish_data = {"fnc": "TradeLog", "type": type, "data": data}
            #     rp.LibGrd.R.publish(channel + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def SlotGame(self, type, data, db_id):  # 公版撈取雲端ps db的slot-game資料庫
        try:
            sqlp = MYPGuard.MYP(db_id)
            sql = sSqls[type]
            return sqlp.Exec(sql=sql.GetSQL(params=data), callback=None)
        except:
            Err("SlotGame err, type:{}, db_id:{}".format(type, db_id))
            PrintEXC()

    def GetBanAndVip(self, account_base):  # 取得ban與vip狀態
        rp = RDSPGuard.RP("game")
        chl_resp = rp.LibGrd.Call("channel.GetInfo", *(ServiceOpt.sHostApiKey,))  # 向redis搜尋extra
        tmp = OnRedisResultParser(chl_resp[1])
        ctm_data = json.loads(tmp["extra"])
        card_host_api_key = "CARD_" + str(account_base.channel)  # CARD_xxxxxxx = CARD_ + xxxxxxx
        # 搜尋指定單代理商戶，取得目標單代理商的service server路徑
        single_chl_server_url = ctm_data["gs_url"][card_host_api_key]
        # 向單代理商的sha@chl_請求base裡的banned與vip狀態
        ban_vip = RequestHelper.DoPost(single_chl_server_url + "/singlechlhostuuid",
                                       {"hostuuid": str(account_base.hostuuid)})
        # ban_vip = json.loads(ban_vip)  # 反序列化
        return ban_vip

    def OnMsgHeartBeat(self, conn, pData, size):  # 即時進入計算網路速度功能
        try:
            sUserItem = self.GetNetBindUserItem(conn.GetID())
            if sUserItem == None:  # 若沒有socket連線
                return  # 則不回送封包
            if pData == None:  # 若沒有接收到封包
                return  # 則不回送封包
            request = heartbeat()
            request.ParseFromString(pData)
            if request.status_code != 1:  # 若封包內狀態碼不是1
                return  # 則不回送封包
            response = heartbeat_ret()
            response.status_code = 1  # 準備網路速度的回送封包
            # 發送主分類31, 子分類2201, 內容物status_code給前端
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_heartbeat_speed, response)

            uuid = sUserItem.mUserInfo.mUUID
            if uuid > 0:
                RDSPGuard.RP("game").LibGrd.Call("common.OnKeepAlive", *(uuid, GetServerTime(), 0))
        except Exception as ex:
            Log("網路連線計算失敗原因={}".format(ex))

    def _multi_reuest_single_event(self, uuid, hostuuid, channel):  # 多代理uuid、單代理uuid、商戶代號
        rp = RDSPGuard.RP("game")
        chl_resp = rp.LibGrd.Call("channel.GetInfo", *(ServiceOpt.sHostApiKey,))  # 向redis搜尋extra
        tmp = OnRedisResultParser(chl_resp[1])
        ctm_data = json.loads(tmp["extra"])
        card_host_api_key = "CARD_" + str(channel)  # CARD_xxxxxxx = CARD_ + xxxxxxx
        # 搜尋指定單代理商戶，取得目標單代理商的service server路徑
        single_url = ctm_data["gs_url"][card_host_api_key]
        # 向單代理商的sha@chl_請求event
        event = RequestHelper.DoPost(single_url + "/multireuestsingleevent", {"uuid": str(hostuuid)})
        if event != None and event["status_code"] == 0:
            # 設定sha@data_個人資訊
            rp.LibGrd.R.hset("sha@data_" + str(uuid), "event", json.dumps(event["event"]))

    def OnMsgLogon(self, conn, pData, size):
        try:
            # 关服之后不接受登录
            if not self.mApp.mRunning:
                return
            request = msg_user_login()
            request.ParseFromString(pData)
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     rp = RDSPGuard.RP("game")
            #     acc = request.channel + "_" + request.sdk_uuid
            #     acc_resp = rp.LibGrd.Call("common.GenAcc", *(acc,))
            #     if acc_resp[0] != 0:
            #         Err("common.GenAcc:", acc_resp[0])
            #     account_base = db_data_user()
            #     account_buffer = None
            #     if acc_resp[1] == 1:  # 已有账号、登录
            #         account_base.ParseFromString(acc_resp[2])
            #         if account_base.disable_login > 0:
            #             Err("Forbidden login account:", acc)
            #         account_base.lastlogintime = GetServerTime()
            #         account_base.game_id = request.game_id  # 將遊戲代號存取至redis base
            #         account_base.channel = request.channel  # 將遊戲商戶存取至redis base
            #         # account_base.score = request.score
            #         account_base.faceid = request.faceid
            #         account_base.source = request.source
            #         account_base.jsondata = request.jsondata
            #         if not account_base.lv:  # 改版後第一次玩
            #             account_base.lv = 1  # 初始等級1

            #         # 如果是測試人員，因為在多代理沒有 user_type，所以用名字判斷並給值
            #         if account_base.sdk_uuid == 'play_star_tester':
            #             account_base.user_type = 999
            #             account_base.score = request.score
            #         account_buffer = account_base.SerializeToString()
            #         # ares = rp.LibGrd.Call("common.GetInfoBySYS", *(int(acc_resp[2]),))
            #     elif acc_resp[1] == 2:  # 新建账号、登录
            #         account_base.uuid = int(acc_resp[2])
            #         # 新建帳號要存前端帶入的token
            #         rp.LibGrd.R.hset("sha@data_" + str(account_base.uuid), "token", request.token)
            #         account_base.game_id = request.game_id  # 將遊戲代號存取至redis base
            #         account_base.hostuuid = request.uuid
            #         account_base.account = request.channel + "_" + request.sdk_uuid
            #         account_base.channel = request.channel
            #         account_base.sdk_uuid = request.sdk_uuid
            #         account_base.score = request.score
            #         account_base.lv = 1  # 初始等級1

            #         # 新建帳號要向單代理請求其redis event資料，才能回存此多代理新帳號的redis event
            #         self._multi_reuest_single_event(account_base.uuid, account_base.hostuuid, account_base.channel)

            #         # 如果是測試人員，因為在多代理沒有 user_type，所以用名字判斷並給值
            #         if account_base.sdk_uuid == 'play_star_tester':
            #             account_base.user_type = 999
            #         ban_vip = self.GetBanAndVip(account_base)  # 取得ban與vip狀態
            #         if ban_vip["ban"] != None:
            #             account_base.banned = ban_vip["ban"]  # 從來源單代理商取得的ban狀態最準確
            #         else:
            #             account_base.banned = 0  # 取得不到，就設定0
            #         if ban_vip["vip"] != None:
            #             account_base.VIP = ban_vip["vip"]  # 從來源單代理商取得的vip狀態最準確
            #         else:
            #             account_base.VIP = 0  # 取得不到，就設定0
            #         account_base.faceid = request.faceid
            #         account_base.bankscore = 0
            #         account_base.nickname = request.sdk_uuid
            #         account_base.source = request.source
            #         account_base.jsondata = request.jsondata
            #         account_base.lastlogintime = GetServerTime()
            #         account_base.regtime = request.lastlogintime
            #         account_buffer = account_base.SerializeToString()
            #         ret = rp.LibGrd.Call("common.OnRegAcc", *(account_base.uuid, acc, account_buffer, request.channel))
            #         # ares = rp.LibGrd.Call("common.GetInfoBySYS", *(int(acc_resp[2]),))
            #         if ret != 0:
            #             Err("common.OnRegAcc:", ret)
            #     else:
            #         Err("Unknown account result type:", acc_resp[1])
            #     # 設定sha@data_個人資訊
            #     rp.LibGrd.R.hset("sha@data_" + str(account_base.uuid), "base", account_buffer)
            #     rp.LibGrd.R.hset("sha@data_" + str(account_base.uuid), "acs_token", request.access_token)
            #     rp.LibGrd.R.hset("sha@data_" + str(account_base.uuid), "channel", request.channel)
            #     # 加入var@host_供onlineinfo多代理商取用
            #     rp.LibGrd.R.hset("var@host_" + str(account_base.channel), str(account_base.uuid), account_base.uuid)
            #     # login_resp = rp.LibGrd.Call("common.OnLogin", *(
            #     #     account_base.uuid, account_buffer, request.token, request.access_token, request.channel))
            #     # if login_resp[0] != 0:
            #     #     Err("common.OnLogin:", login_resp[0])
            #     INFO("OnMsgLogon uuid: %s, token: %s", account_base.uuid, request.token)
            # else:
            INFO("OnMsgLogon uuid: %s, token: %s", request.uuid, request.token)
            if (request.uuid == 0 or request.token == 0) \
                    and not ServiceOpt.IsEducateSvr():
                return
            net_params = self.GetNetBindParams(conn.GetID())
            if net_params is None:
                return
            # 重复登录判断(300毫秒内不能重复登录)
            if net_params.mLoginTime > 0 \
                    and net_params.mLoginTime + 300 > GetServerTimeMS():
                return
            net_params.mLoginTime = GetServerTimeMS()

            response = msg_user_login_ret()
            response.server_id = ServiceOpt.sSubGameId

            # 是否維護
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     rp2 = RDSPGuard.RP("gamelist")
            #     # 單代理商向var@maintain_取得本代理商在多代理商的狀態
            #     host_maintain = rp2.LibGrd.R.get("var@maintain_" + request.channel)
            #     # host_maintain = host_maintain.decode("utf-8")  # 取得維護狀態後的解析
            #     host_uuid = account_base.uuid
            #     host_token = request.token
            # else:
            host_maintain = None  # 代表不是多代理商維護
            host_uuid = request.uuid
            host_token = request.token
            # if host_maintain != None:  # 維護中
            #     if int(host_maintain.decode("utf-8")) == 1:  # 維護中
            #         response.ret = e_error_invalid_conn
            #         self.SendToClient(conn.GetID(), e_msgid_game_login, e_cg_msgid_login, response)
            #         return  # 禁止此商戶的所屬玩家登入
            rp = RDSPGuard.RP("game")
            results = rp.LibGrd.Call("common.GetInfoBySYS", *(host_uuid,))
            # 判斷是否在遊戲中，遊戲中被斷線重連的玩家不在容留人數此限
            response.can_enter_room = 1  # 預設可進房
            if results != None and results[2] != None:
                if len(results[2].decode()) <= 0:  # 如果redis的svr_id沒東西，表示不在遊戲中
                    # 判斷目前房間內的連線人數是否超過設定容留連線人數
                    if len(self.mID2Conn) > ServiceOpt.sMaxConnected:
                        response.can_enter_room = 0  # 不可進房，進房進度條完成後，離開回到大廳
            # 試玩桌因為access token網址拿掉，進入，沒有redis資訊，所以無資訊必須避開維護
            if results != None and results[0] == 0 and results[1] != None:
                account_base = db_data_user()
                account_base.ParseFromString(results[1])
                channel_res = rp.LibGrd.Call("channel.GetInfo", *(account_base.channel,))
                if channel_res[0] == 0:
                    chl_data = OnRedisResultParser(channel_res[1])
                    ctm_data = json.loads(chl_data["extra"])
                    if "status" in ctm_data:
                        status = ctm_data["status"]
                        if status == 1:  # 維護
                            response.ret = e_error_invalid_conn
                            self.SendToClient(conn.GetID(), e_msgid_game_login, e_cg_msgid_login, response)
                            return

            account_base = db_data_user()
            if not ServiceOpt.IsEducateSvr():
                rp = RDSPGuard.RP("game")
                results = rp.LibGrd.Call("common.OnLoginSG", *(host_uuid, host_token, ServiceOpt.sSvrUUID))
                if results[0] != e_error_ok:
                    if results[0] == -1 or results[0] == -2:
                        response.ret = e_error_invalid_conn
                    elif results[0] == -4:
                        response.ret = e_error_repeated
                    self.SendToClient(conn.GetID(), e_msgid_game_login, e_cg_msgid_login, response)
                    return
                account_base.ParseFromString(results[1])
                if account_base.banned == 1:  # banned
                    response.ret = e_error_invalid_conn
                    self.SendToClient(conn.GetID(), e_msgid_game_login, e_cg_msgid_login, response)
                    return
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商 同步svr_id
                #     # 同步單代理商的svr_id，讓單代理商知道多代理商正在遊戲中
                #     self.SyncNewSvrID(account_base.hostuuid, account_base.channel)
            else:
                self.mEduUUIDInc += 1
                account_base.uuid = self.mEduUUIDInc if request.uuid == 0 else request.uuid
                # 金額這樣設定可避免一下子就超出房間上限
                account_base.score = int(ServiceOpt.sMaxScore//2)
                account_base.nickname = b'GUEST'
                account_base.faceid = 17
                account_base.jsondata = "{}"

            single_host_api_key = account_base.sin_channel
            # 加入var@host_供onlineinfo多代理商取用
            rp.LibGrd.R.hset("var@host_" + str(single_host_api_key), str(account_base.uuid), account_base.uuid)
            # 游戏登录处理
            response.ret = self.OnGameLogin(conn, account_base, request.token)
            if response.ret != e_error_ok:
                self.SendToClient(conn.GetID(), e_msgid_game_login, e_cg_msgid_login, response)
                return
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     response.uuid = account_base.hostuuid
            #     response.multi_host_uuid = account_base.uuid
            # else:
            response.uuid = account_base.uuid
            response.multi_host_uuid = account_base.uuid
            response.score = account_base.score

            pSvrUserItem = net_params.mISvrUserItem
            if pSvrUserItem.TableID != INVALID_TABLE and pSvrUserItem.ChairID != INVALID_CHAIR:
                response.status = 1
            else:
                matchinfo = self.mMatcher.FindMatchInfo(pSvrUserItem)
                if matchinfo is not None:
                    response.status = 2
                    response.match_time = GetServerTime() - matchinfo.nMateTime
                else:
                    response.status = 3
            self.SendToClient(conn.GetID(), e_msgid_game_login, e_cg_msgid_login, response)
            if response.status == 1:
                self.SendUserSitDown(pSvrUserItem, pSvrUserItem.TableID, pSvrUserItem.ChairID)
            # 若為正式房，非試玩房
            if not ServiceOpt.IsEducateSvr():
                account_base.ip_address = pSvrUserItem.mIpAddr  # 登入時將ip_address更新至redis base
                uuid = account_base.uuid
                account_buffer = account_base.SerializeToString()
                rp.LibGrd.R.hset("sha@data_" + str(uuid), "base", account_buffer)
        except:
            PrintEXC()

    def OnGameLogin(self, conn, account_info, token):
        try:
            pNetParams = self.GetNetBindParams(conn.GetID())
            # 挤号判断
            old_user_ptr = SvrUsrMgr.GetSrvUserItem(account_info.uuid)
            if old_user_ptr is not None:
                if old_user_ptr.SocketID > 0 and old_user_ptr.SocketID != conn.GetID():
                    old_net_params = self.GetNetBindParams(old_user_ptr.SocketID)
                    if old_net_params is not None and old_net_params.mISvrUserItem is not None:
                        msg = msg_user_logout_ret()
                        msg.uuid = old_net_params.mISvrUserItem.mUserInfo.mUUID
                        msg.reason = logout_relogin
                        self.SendToClient(old_user_ptr.SocketID, e_msgid_game_login, e_cg_msgid_logout, msg)
                        # 解除绑定
                        if old_net_params.mISvrUserItem.mUserInfo.mUUID == old_user_ptr.mUserInfo.mUUID:
                            old_net_params.mISvrUserItem = None
                        self.mServer.SafeClose(old_user_ptr.SocketID)
                        INFO("断开玩家[%s] 旧SOCKET[%d],新SOCKET[%d]", old_user_ptr.mUserInfo.mNickName,
                                                old_user_ptr.SocketID, pNetParams.mSocketID)

                # 切换状态
                pNetParams.mISvrUserItem = old_user_ptr
                pNetParams.mISvrUserItem.SetOfflineStatus(0)
                pNetParams.mISvrUserItem.mSocketID = conn.GetID()
                pNetParams.mISvrUserItem.mCliReady = True
                if pNetParams.mISvrUserItem.TableID != INVALID_TABLE:
                    mTableFrame = self.mTables[pNetParams.mISvrUserItem.TableID]
                    if mTableFrame is not None:
                        mTableFrame.OnEventUserReconnect(pNetParams.mISvrUserItem)
                return e_error_ok

            #条件判断
            if ServiceOpt.sMaxEnterScore != 0 and account_info.score > ServiceOpt.sMaxEnterScore:
                return e_error_max_score
            if SvrUsrMgr.GetUserItemCount() > (ServiceOpt.sMaxPlayer - RESERVE_USER_COUNT):
                return e_error_room_full

            #计算盈亏
            servZeroTime = GetServerZeroTime()
            if account_info.lastscoretime == 0 \
                    or account_info.lastscoretime < servZeroTime:
                account_info.dailyprofit = 0
                account_info.lastscoretime = servZeroTime

            # 登陆成功
            info = SvrUserInfo()
            info.mUUID = account_info.uuid
            info.mGameID = 0
            info.mNickName = account_info.nickname
            info.mFaceID = account_info.faceid
            info.mSex = 1
            info.mTableID = INVALID_TABLE
            info.mChairID = INVALID_CHAIR
            info.mStatus = eUS.US_FREE
            info.mScore = account_info.score
            #info.mBankScore = 0
            info.mRecharge = 0
            info.mExchange = 0
            info.mCtrlStatus = account_info.control_status
            info.mCtrlScore = account_info.control_score
            info.mLastDay = account_info.lastscoretime
            info.mTodayProfix = account_info.dailyprofit
            #info.mCardScore = 0
            info.mSource = account_info.source
            info.mChannel = account_info.channel
            info.mSdkUUID = account_info.sdk_uuid
            # 計算此玩家的資歷
            if abs(GetServerTime() - account_info.regtime) >= 0:  # 老手：超過0天
                info.mCanMatchPlayer = 1  # 可匹配玩家
            else:  # 新手：不到0天
                info.mCanMatchPlayer = 0  # 只能對戰機器人

            try:
                info.mJson = json.loads(account_info.jsondata)
            except:
                info.mJson = {}

            if not ServiceOpt.IsEducateSvr():
                #子游戏json数据
                rp2 = RDSPGuard.RP("subgame")
                info.mSubJson = rp2.LibGrd.R.hget("sha@sgjson_" + str(account_info.uuid), str(ServiceOpt.sSubGameId))
                if info.mSubJson is None:
                    info.mSubJson = json.dumps({}).encode('utf-8')
                Log("玩家登陆成功，子游戏Json数据：", info.mSubJson)

            pUserItem = SvrUsrMgr.AddSvrUserItem(info, conn.GetID(), pNetParams.mIpAddr)
            if pUserItem is None:
                return e_error_invalid_token
            pNetParams.mISvrUserItem = pUserItem
            pNetParams.mISvrUserItem.mToken = token
            # 同步信息到游戏服务
            self.OnEventUserLogon(pUserItem)
            return e_error_ok
        except:
            PrintEXC()
            return e_error_failed

    def IsUserSitDown(self, mUUID):
        for i in range(ServiceOpt.sTableCount):
            mTableFrame = self.mTables[i]
            if mTableFrame is None:
                continue
            for wChair in range(ServiceAttr.sChairCnt):
                pUserItem = mTableFrame.GetTableUserItem(wChair)
                if pUserItem is None:
                    continue
                if pUserItem.mUserInfo.mUUID == mUUID:
                    return True
        return False

    def OnMsgSitDown(self, conn, data, size):
        try:
            if self.mServiceAttr.sAllowMatch:
                return
            request = msg_sitdown()
            request.ParseFromString(data)
            response = msg_sitdown_ret()

            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem is None:
                return
            # 判断是否已经坐下
            if self.IsUserSitDown(pSvrUserItem.mUserInfo.mUUID):
                self.SendUserSitDown(pSvrUserItem, pSvrUserItem.TableID, pSvrUserItem.ChairID)
                return
            # 最低积分限制
            if ServiceOpt.sMinEnterScore != 0 \
                    and pSvrUserItem.mUserInfo.mScore < ServiceOpt.sMinEnterScore:
                response.ret = e_error_min_score
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_sitdown)
                return
            # 最高积分限制
            if ServiceOpt.sMaxEnterScore != 0 \
                    and pSvrUserItem.mUserInfo.mScore > ServiceOpt.sMaxEnterScore:
                response.ret = e_error_max_score
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_sitdown)
                return
            if request.table_id < 0 or request.table_id > ServiceOpt.sTableCount \
                    or request.chair_id < 0 or request.chair_id > ServiceAttr.sChairCnt:
                response.ret = e_error_invalid_table
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_sitdown)
                return
            ret = self.DoUserSitDown(pSvrUserItem, request.table_id, request.chair_id, request.table_pwd, False, INVALID_TABLE)
            if ret == 0:
                self.SendUserSitDown(pSvrUserItem, pSvrUserItem.TableID, pSvrUserItem.ChairID)
                return
            response.ret = ret
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_sitdown, response)
        except:
            PrintEXC()

    def DoUserSitDown(self, pSvrUserItem, wTableID, wChairID, pwd, bNeedStandUp = False, wExceptTableID = INVALID_TABLE):
        if bNeedStandUp:
            if pSvrUserItem.mUserInfo.mStatus >= eUS.US_SIT:
                mTableFrame = self.mTables[pSvrUserItem.mUserInfo.mTableID]
                if mTableFrame is not None \
                        and mTableFrame.PerformStandUpAction(pSvrUserItem, False, 1) == False:
                    return e_error_not_leave

        if wTableID == 0:   # 快速坐下
            bFinded = False
            for i in range(ServiceOpt.sTableCount):
                mTableFrame = self.mTables[i]
                if mTableFrame is None or mTableFrame.TableID == wExceptTableID:
                    continue
                wEmptyChairID = mTableFrame.GetNullChairID()
                if wEmptyChairID is None or wEmptyChairID == INVALID_CHAIR:
                    continue
                mTableFrame.PerformSitDownAction(wEmptyChairID, pSvrUserItem)
                bFinded = True
                break
            if not bFinded:
                return e_error_table_full
        else:           # 指定进入
            mTableFrame = self.mTables[wTableID]
            if mTableFrame is not None:
                if mTableFrame.GetTableUserItem(wChairID) is not None:
                    return e_error_invalid_token
                if not mTableFrame.PerformSitDownAction(wChairID, pSvrUserItem):
                    return e_error_table_full
        return 0

    def SendUserSitDown(self, pSvrUserItem, wTableID, wChairID, bBcSelf = True):
        sendmsg = msg_sitdown_ret()
        if wTableID < 0 or wTableID >= ServiceOpt.sTableCount:
            return

        # 取得所有等級所需的勝場數
        upgrade_needs_win = ServerMYP.upgrade_threshold_list

        mTableFrame = self.mTables[wTableID]
        sendmsg.ret = 0
        sendmsg.table_id = wTableID
        sendmsg.chair_id = wChairID
        sendmsg.table_pwd = mTableFrame.AuthCode
        sendmsg.table_owner = mTableFrame.OwnerChairID
        sendmsg.table_status = mTableFrame.mStatus
        sendmsg.start_lefttime = mTableFrame.GetStartLeftTime()
        for wChair in range(ServiceAttr.sChairCnt):
            other = mTableFrame.GetTableUserItem(wChair)
            if other is None:
                continue
            actinfo = sendmsg.active_users.add()
            actinfo.uuid = other.mUserInfo.mUUID
            actinfo.nickname = other.mUserInfo.mNickName.encode()
            actinfo.chair_id = wChair
            actinfo.play_status = int(other.mUserInfo.mStatus)
            actinfo.faceid = other.mUserInfo.mFaceID
            actinfo.score = other.mUserInfo.mScore

            account_base = UserRP.get_account_base(actinfo.uuid)  # 取得玩家base
            if not account_base:  # 取得不到視為機器人
                # 取得商戶名稱
                host_name = UserRP.get_host_name(ServiceOpt.sHostApiKey)
                android_data = UserRP.get_account_android(ServiceOpt.sSubGameId, wTableID, wChair, host_name)  # 取得機器人等級資訊
                if not android_data:  # 機器人沒資訊，表示剛開局
                    lv = random.choices(population=[x for x in range(1, 20 + 1)],
                                   weights=[1, 1, 1, 6, 6, 6, 7, 7, 9, 9, 8, 8, 7, 6, 5, 5, 5, 1, 1, 1],
                                   k=1)[0]

                    # 機器人的生涯勝場數，先取得目前等級與下一等級對應後，再根據範圍內隨機決定
                    the_requirement = 0  # 預設開始計算累積所需勝場數
                    for next in upgrade_needs_win[0: lv]:  # 取得此等所需勝場數
                        the_requirement += next
                    upgrade_requirement = 0  # 預設開始計算累積所需勝場數
                    for next in upgrade_needs_win[0: lv + 1]:  # 取得下一等所需勝場數
                        upgrade_requirement += next

                    # 機器人的生涯勝場數，在目前等級對應勝場數與下一等級勝場數之間決定(-2不要讓機器人升級)
                    all_win_times = GetRndInt(the_requirement, upgrade_requirement - 2)

                    # 機器人的生涯遊玩次數，勝率45%~65%之間隨機決定
                    play_times = random.randint(int(the_requirement * 1.54), int(the_requirement * 2.22))

                    android_data = {
                        "FaceID": actinfo.faceid,
                        "CurHeadFrame": 0,
                        "CurTitle": 0,
                        "MemberLv": lv,
                        "play_times": play_times,
                        "all_win_times": all_win_times,
                        "pokerType": 0
                    }

                    # 取得商戶名稱
                    host_name = UserRP.get_host_name(ServiceOpt.sHostApiKey)
                    # 寫入本局機器人等級資訊
                    UserRP.set_account_android(ServiceOpt.sSubGameId, wTableID, wChair, android_data, host_name)
                    # 寫入actinfo
                    actinfo.CurHeadFrame = android_data["CurHeadFrame"]
                    actinfo.CurTitle = android_data["CurTitle"]
                    actinfo.MemberLv = android_data["MemberLv"]
                    actinfo.play_times = android_data["play_times"]
                    actinfo.all_win_times = android_data["all_win_times"]
                    actinfo.pokerType = android_data["pokerType"]
                    actinfo.UpgradeNeedWins.extend(upgrade_needs_win)

                else:  # 機器人有資訊，直接拿來用
                    actinfo.CurHeadFrame = android_data["CurHeadFrame"]
                    actinfo.CurTitle = android_data["CurTitle"]
                    actinfo.MemberLv = android_data["MemberLv"]
                    actinfo.play_times = android_data["play_times"]
                    actinfo.all_win_times = android_data["all_win_times"]
                    actinfo.pokerType = android_data["pokerType"]
                    actinfo.UpgradeNeedWins.extend(upgrade_needs_win)

            else:  # 取得表示為真人
                actinfo.CurHeadFrame = account_base.frame
                actinfo.CurTitle = account_base.designation
                actinfo.MemberLv = account_base.lv
                actinfo.play_times = account_base.play_times
                actinfo.all_win_times = account_base.all_win_times
                actinfo.pokerType = account_base.card_style
                actinfo.UpgradeNeedWins.extend(upgrade_needs_win)

        self.SendToClient(pSvrUserItem.mSocketID, e_msgid_game_action, e_cg_msgid_sitdown, sendmsg)

        # 是否广播我自己
        if bBcSelf:
            sendmsgbc = msg_sitdown_ret_bc()
            sendmsgbc.newuser.uuid = pSvrUserItem.mUserInfo.mUUID
            sendmsgbc.newuser.nickname = pSvrUserItem.mUserInfo.mNickName.encode()
            sendmsgbc.newuser.chair_id = pSvrUserItem.mUserInfo.mChairID
            sendmsgbc.newuser.play_status = int(pSvrUserItem.mUserInfo.mStatus)
            sendmsgbc.newuser.faceid = pSvrUserItem.mUserInfo.mFaceID
            sendmsgbc.newuser.score = pSvrUserItem.mUserInfo.mScore
            sendmsgbc_buffer = sendmsgbc.SerializeToString()

            for wChair in range(ServiceAttr.sChairCnt):
                other = mTableFrame.GetTableUserItem(wChair)
                if other is None or other.IsAndroidUser \
                        or not other.IsCliReady \
                        or pSvrUserItem.mUserInfo.mChairID == other.mUserInfo.mChairID:
                    continue
                self.SendDataToClient(other.mSocketID, e_msgid_game_action, e_cg_msgid_sitdown_bc, sendmsgbc_buffer)

    def OnMsgStandUp(self, conn, data, size):
        try:
            sUserItem = self.GetNetBindUserItem(conn.GetID())
            if sUserItem is None:
                return
            if sUserItem.Status >= eUS.US_PLAYING:
                return
            if sUserItem.TableID != INVALID_TABLE:
                mTableFrame = self.mTables[sUserItem.TableID]
                if mTableFrame is not None \
                        and not mTableFrame.PerformStandUpAction(sUserItem):
                    return
            self.OnEventUserStandUp(sUserItem)
            #self.OnEventUserLogout(sUserItem, logout_user, False)
        except:
            PrintEXC()

    def OnMsgEnterTable(self, conn, data, size):
        try:
            sUserItem = self.GetNetBindUserItem(conn.GetID())
            if sUserItem is None:
                return
            if sUserItem.TableID != INVALID_TABLE:
                mTableFrame = self.mTables[sUserItem.TableID]
                if mTableFrame is not None:
                    mTableFrame.OnEventEnterTable(sUserItem)
            else:
                sendmsg = msg_enter_table_ret()
                sendmsg.ret = e_error_failed
                self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_enter_table, sendmsg)
        except:
            PrintEXC()

    def GenTablePwd(self):
        rp = RDSPGuard.RP("game")
        pwd_res = rp.LibGrd.Call("common.GetTablePwd", *(0, ))
        if pwd_res is None or len(pwd_res) == 0:
            return str(random.randint(105620, 965325)).encode()
        return pwd_res

    def OnMsgCreateRoom(self,  conn, data, size):
        try:
            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem is None:
                return
            if self.IsUserSitDown(pSvrUserItem.mUserInfo.mUUID):
                return
            sendmsg = msg_createroom_ret()
            sendmsg.ret = e_error_ok
            while True:
                if ServiceOpt.sMinEnterScore != 0 \
                        and pSvrUserItem.mUserInfo.mScore < ServiceOpt.sMinEnterScore:
                    sendmsg.ret = e_error_min_score
                    break
                if ServiceOpt.sMaxEnterScore != 0 \
                        and pSvrUserItem.mUserInfo.mScore > ServiceOpt.sMaxEnterScore:
                    sendmsg.ret = e_error_max_score
                    break
                mTableFrame = self.AllocTableFrame(self.mServiceAttr.sChairCnt)
                if mTableFrame is None:
                    sendmsg.ret = e_error_table_full
                    break
                mTableFrame.Dgt.OnInitialize(ServiceOpt.sCellScore, ServiceOpt.sThinkTime,
                                             ServiceOpt.sNoticeScore)  # , sChallengeTime)
                sbAuthCode = self.GenTablePwd()
                bOk = mTableFrame.DoCreateTable(pSvrUserItem, sbAuthCode)
                if bOk:
                    self.SendUserSitDown(pSvrUserItem, pSvrUserItem.TableID, pSvrUserItem.ChairID)
                    mTableFrame.OnEventReady(pSvrUserItem)
                    self.SaveAuthCode(sbAuthCode)
                sendmsg.ret = e_error_ok if bOk else e_error_failed
                break
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_create_toom, sendmsg)
        except:
            PrintEXC()

    def OnMsgJoinRoom(self,  conn, data, size):
        try:
            request = msg_joinroom()
            request.ParseFromString(data)
            Log(request)
            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem is None:
                return
            sendmsg = msg_joinroom_ret()
            sendmsg.ret = e_error_ok
            while True:
                if self.IsUserSitDown(pSvrUserItem.mUserInfo.mUUID):
                    self.SendUserSitDown(pSvrUserItem, pSvrUserItem.TableID, pSvrUserItem.ChairID)
                    break
                if ServiceOpt.sMinEnterScore != 0 \
                        and pSvrUserItem.mUserInfo.mScore < ServiceOpt.sMinEnterScore:
                    sendmsg.ret = e_error_min_score
                    break
                if ServiceOpt.sMaxEnterScore != 0 \
                        and pSvrUserItem.mUserInfo.mScore > ServiceOpt.sMaxEnterScore:
                    sendmsg.ret = e_error_max_score
                    break
                bOk = False
                for i in range(ServiceOpt.sTableCount):
                    mTableFrame = self.mTables[i]
                    if mTableFrame is not None:
                        bOk = mTableFrame.DoJoinTable(pSvrUserItem, request.authcode)
                        if bOk:
                            self.SendUserSitDown(pSvrUserItem, pSvrUserItem.TableID, pSvrUserItem.ChairID)
                            mTableFrame.OnEventReady(pSvrUserItem)
                            break
                sendmsg.ret = e_error_ok if bOk else e_error_failed
                break
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_join_room, sendmsg)
        except:
            PrintEXC()

    def OnMsgStartGame(self,  conn, data, size):
        try:
            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem is None \
                    or pSvrUserItem.TableID == INVALID_TABLE \
                    or pSvrUserItem.ChairID == INVALID_CHAIR:
                return
            sendmsg = msg_startgame_ret()
            sendmsg.ret = e_error_ok
            mTableFrame = self.mTables[pSvrUserItem.TableID]
            while True:
                if mTableFrame is None:
                    sendmsg.ret = e_error_invalid_table
                    break
                if mTableFrame.OwnerChairID != pSvrUserItem.ChairID:
                    sendmsg.ret = e_error_not_owner
                    break
                if not mTableFrame.EfficacyStartGame():
                    sendmsg.ret = e_error_enough_player
                    break
                mTableFrame.StartGame()
                break
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_start_game, sendmsg)
        except:
            PrintEXC()

    def OnMsgChangeTable(self, conn, data, size):
        try:
            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem is None:
                return
            sendmsg = msg_change_table_ret()
            sendmsg.ret = e_error_ok
            if pSvrUserItem.mUserInfo.mStatus >= eUS.US_SIT:
                mTableFrame = self.mTables[pSvrUserItem.mUserInfo.mTableID]
                if mTableFrame is not None \
                        and mTableFrame.PerformStandUpAction(pSvrUserItem, False, changetable_standup_op) == False:
                    sendmsg.ret = e_error_not_leave
                    self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_changetable, sendmsg)
                    return
                pSvrUserItem.mExceptTableID = mTableFrame.TableID
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_changetable, sendmsg)
            matchmsg = msg_match()
            matchmsg.match = 1
            self.OnMsgMatch(conn, matchmsg.SerializeToString(), 0)
        except:
            PrintEXC()

    def OnMsgMatch(self, conn, data, size):
        try:
            request = msg_match()
            request.ParseFromString(data)

            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem is None:
                Log("************* pSvrUserItem is None *************")
                return
            # 判断是否已经坐下
            if self.IsUserSitDown(pSvrUserItem.mUserInfo.mUUID):
                Log("*************玩家UUID : " + str(pSvrUserItem.mUserInfo.mUUID) + " 已经坐下*************")
                return
            sendmsg = msg_match_ret()
            sendmsg.ret = e_error_ok
            sendmsg.match = request.match
            while True:
                if request.match == 1:
                    #条件判断
                    rp = RDSPGuard.RP("game")
                    account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(pSvrUserItem.mUserInfo.mUUID,))
                    # 試玩桌因為access token網址拿掉，進入，沒有redis資訊，所以無資訊必須避開維護
                    if account_res != None and account_res[0] == 0 and account_res[1] != None:
                        account_base = db_data_user()
                        account_base.ParseFromString(account_res[1])
                        # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商維護
                        #     rp2 = RDSPGuard.RP("gamelist")
                        #     # 單代理商向var@maintain_取得本代理商在多代理商的狀態
                        #     host_maintain = rp2.LibGrd.R.get("var@maintain_" + account_base.channel)
                        #     # host_maintain = host_maintain.decode("utf-8")  # 取得維護狀態後的解析
                        #     if host_maintain:  # 如果狀態是維護
                        #         sendmsg.ret = 6
                        #         break  # 禁止此商戶的所屬玩家加入匹配
                        if ServiceOpt.sMinEnterScore != 0 \
                                and account_base.banned == 1:  # banned
                            sendmsg.ret = 5
                            break
                        if not ServiceOpt.IsEducateSvr():  # 試玩桌：機器人不受房間最大攜入金額限制
                            if ServiceOpt.sMinEnterScore != 0 \
                                    and account_base.score > ServiceOpt.sMaxScore:  # 判斷是否超過最大攜入金額
                                sendmsg.ret = 4
                                break
                        if not ServiceOpt.IsEducateSvr():  # 試玩桌：不受錢包與攜入金額不對等限制
                            if ServiceOpt.sMinEnterScore != 0 \
                                    and pSvrUserItem.mUserInfo.mScore != account_base.score:  # 判斷傳入金額與當前錢包
                                sendmsg.ret = 3
                                break
                        if not ServiceOpt.IsEducateSvr():  # 試玩桌：不受房間最小准入金額限制
                            if ServiceOpt.sMinEnterScore != 0 \
                                    and pSvrUserItem.mUserInfo.mScore < ServiceOpt.sMinEnterScore:
                                sendmsg.ret = 1
                                break
                        if not ServiceOpt.IsEducateSvr():  # 試玩桌：玩家不受房間最大攜入金額限制
                            if ServiceOpt.sMaxEnterScore != 0 \
                                    and pSvrUserItem.mUserInfo.mScore > ServiceOpt.sMaxEnterScore:
                                sendmsg.ret = 2
                                break
                    r = self.AddMatch(pSvrUserItem)
                    sendmsg.ret = e_error_ok if r else e_error_failed
                else:
                    info = self.mMatcher.FindMatchInfo(pSvrUserItem)
                    if info is None:
                        sendmsg.ret = e_error_failed
                        break
                    self.mMatcher.DelMatchInfo(info)
                    pSvrUserItem.bMate = False
                    pSvrUserItem.nMateTime = 0
                break
            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_match, sendmsg)
        except:
            PrintEXC()

    def AddMatch(self, pSrvUserItem)->bool:
        try:
            if pSrvUserItem.UUID in self.mMatcher.match_users_group:
                return False
            if not self.mApp.mRunning:
                return False
            if pSrvUserItem is None:
                return False
            if pSrvUserItem.Status >= eUS.US_PLAYING:
                return False

            mateInfo = stMatchInfo()
            mateInfo.nScore = pSrvUserItem.mUserInfo.mScore
            mateInfo.sIPAddr = pSrvUserItem.mIpAddr
            mateInfo.pSvrUserItem = pSrvUserItem
            mateInfo.nMateTime = GetServerTime()
            mateInfo.nMaxMateTime = GetServerTime() + GetRndInt(5, 10)
            #加入匹配
            bMatchResult = self.mMatcher.AddMatch(mateInfo)
            if not bMatchResult:
                return False
            pSrvUserItem.bMate = True
            pSrvUserItem.nMateTime = GetServerTime()
            return True
        except:
            PrintEXC()
            return False

    def OnMsgReady(self, conn, data, size):
        request = msg_ready()
        request.ParseFromString(data)
        try:
            pSvrUserItem = self.GetNetBindUserItem(conn.GetID())
            if pSvrUserItem is None:
                return
            if pSvrUserItem.TableID != INVALID_TABLE and pSvrUserItem.ChairID != INVALID_CHAIR:
                mTableFrame = self.mTables[pSvrUserItem.TableID]
                if mTableFrame is not None:
                    rp = RDSPGuard.RP("game")
                    ares = rp.LibGrd.Call("common.GetInfoBySYS", pSvrUserItem.mUserInfo.mUUID)
                    # 試玩桌因為access token網址拿掉，進入，沒有redis資訊，所以無資訊必須避開維護
                    if ares != None and ares[0] == 0 and ares[1] != None:
                        account_base = db_data_user()
                        account_base.ParseFromString(ares[1])
                        # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商維護
                        #     rp2 = RDSPGuard.RP("gamelist")
                        #     # 單代理商向var@maintain_取得本代理商在多代理商的狀態
                        #     host_maintain = rp2.LibGrd.R.get("var@maintain_" + account_base.channel)
                        #     # host_maintain = host_maintain.decode("utf-8")  # 取得維護狀態後的解析
                        #     if host_maintain:  # 如果狀態是維護
                        #         bOk = False  # 禁止此商戶的所屬玩家開局
                        #     else:
                        #         bOk = mTableFrame.OnEventReady(pSvrUserItem)
                        if account_base.banned == 1:  # banned
                            bOk = False
                        else:
                            bOk = mTableFrame.OnEventReady(pSvrUserItem)
                        if bOk is False:
                            sendmsg = msg_ready_ret()
                            sendmsg.ret = e_error_ok if bOk else e_error_failed
                            sendmsg.chair_id = pSvrUserItem.ChairID
                            sendmsg.state = request.op
                            self.SendToClient(conn.GetID(), e_msgid_game_action, e_cg_msgid_ready, sendmsg)
        except:
            PrintEXC()

    def GetMoniTableInfo(self):
        nFree = 0
        nGame = 0
        nCreate = 0
        for i in range(ServiceOpt.sTableCount):
            mTableFrame = self.mTables[i]
            if mTableFrame is not None:
                if mTableFrame.IsStarted():
                    nGame += 1
                elif mTableFrame.IsCreateTable():
                    nCreate += 1
                elif mTableFrame.GetAllUserCount() == 0:
                    nFree += 1
        return nFree, nGame, nCreate

    def OnMsgMonitor(self, conn, data, size):
        try:
            nFree, nGame, nCreate = self.GetMoniTableInfo()
            #cpu, mem = GetCpuAndMemory()
            sendmsg = msg_server_monitor_ret()
            sendmsg.json_data = json.dumps({
                "max_table" : ServiceOpt.sTableCount,
                "max_player" : ServiceOpt.sMaxPlayer,
                "cur_player" : SvrUsrMgr.GetUserItemCount(),
                "match_player" : self.mMatcher.GetCount(),
                "free_table" : nFree,
                "create_table" : nCreate,
                "game_table" : nGame,
                #"cpu" : cpu,
                #"memory" : mem,
            }).encode()
            self.SendToClient(conn.GetID(), e_msgid_monitor, e_c_msgid_server_monitor, sendmsg)
        except:
            PrintEXC()

    def OnEventUserStandUp(self, pSrvUserItem, reason = 0):
        if pSrvUserItem.TableID != INVALID_TABLE:
            sendmsg = msg_standup_ret()
            sendmsg.chair_id = pSrvUserItem.ChairID
            sendmsg.ret = 0
            sendmsg.reason = reason
            self.SendToClient(pSrvUserItem.SocketID, e_msgid_game_action,
                              e_cg_msgid_standup, sendmsg)

    def OnEventUserLogon(self, pSrvUserItem):
        self.OnLoginLog(pSrvUserItem, True)

    def AutoTranslateOut(self, uuid, chl, token, name):
        self.CreateTask(self.OnAutoTranslateOut(uuid, chl, token, name))

    async def OnAutoTranslateOut(self, uuid, chl, token, name):
        try:
            INFO("OnAutoTranslateOut uuid:%s, chl: %s", uuid, chl)

            rp = RDSPGuard.RP("game")
            if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(ServiceOpt.sHostApiKey,))
            else:
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(chl,))
            if chl_resp[0] != 0:
                Warn("channel get info error!")
                return -1, "error"
            chl_data = OnRedisResultParser(chl_resp[1])
            ctm_data = json.loads(chl_data["extra"])
            if ctm_data["auto_trans"] != 1:
                return

            gs_url = ctm_data["gs_url"]
            if isinstance(gs_url, dict):
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                #     host_chl = "CARD_" + chl
                #     if host_chl in gs_url:
                #         gs_url = gs_url[host_chl]
                # else:
                if "CARD" in gs_url:
                    gs_url = gs_url["CARD"]
            results = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            # 試玩桌因為access token網址拿掉，進入，沒有redis資訊，所以無資訊必須避開維護
            if results is None or results[0] != 0 or results[1] == None:
                return
            account_base = db_data_user()
            account_base.ParseFromString(results[1])

            # Log("-----------------------------------------AutoTranslateOut Enter1 score=", account_base.score)
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     if account_base.score > 0:
            #         results = await self.mAsyncService.DoAsync(RequestHelper.ReqGetTransMultiHost, gs_url, "trans",
            #                                                account_base.hostuuid, "in", account_base.score, token, account_base.txn_id)
            # else:
            if account_base.score > 0:
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商要使用來源商戶的uuid
                #     results = await self.mAsyncService.DoAsync(RequestHelper.ReqGetTrans, gs_url, "trans",
                #                                                account_base.hostuuid, "in", account_base.score, token)
                # else:  # 單代理商直接使用自己的uuid
                results = await self.mAsyncService.DoAsync(RequestHelper.ReqGetTrans, gs_url, "trans",
                                                               uuid, "in", account_base.score, token)
            if account_base.score > 0:
                if results == None:
                    Warn("auto translate error! member_id= ", name, " uuid=", uuid)
                    return -2, "error"
                if results["error_code"] != 0:
                    Warn("auto translate error! member_id= ", name, " uuid=", uuid, ", error_code=", results["error_code"])
                    return -2, "error"
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     account_base.txn_id = "0"
            #     account_base.score -= account_base.score
            #     account_buffer = account_base.SerializeToString()
            #     rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

                # check score
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                account_base.ParseFromString(account_res[1])
                Warn("--- OnAutoTranslateOut check, member_id=", name, " score=",
                     account_base.score)
            return 0, "success"
        except:
            PrintEXC()
            Warn(" Auto Translate Out error! member_id= ", name, " uuid=", uuid)

    def OnEventUserLogout(self, pSrvUserItem, dwLeaveReason, bClose, dismiss_flag=False):
        try:
            # 如果進入手動強制解散流程，則進入機器人oncludegame流程
            if dismiss_flag == True:
                for id, sAndroid in self.mAndroidService.mAndroids.items():
                    if sAndroid is None:
                        continue
                    wTableID = sAndroid.GetTableID()
                    if wTableID == INVALID_TABLE:
                        continue
                    mTableFrame = self.mTables[wTableID]
                    # 如果是退出桌子状态，则发送起立指令，并复位机器人数据
                    if sAndroid.GetUserStatus() == eUS.US_EXIT:
                        INFO("机器人[%s:%d]状态由EXIT->NULL", sAndroid.GetInfo().mNickName, sAndroid.GetInfo().mUUID)
                        # if mTableFrame.PerformStandUpAction(sAndroid.GetMeUserItem()):
                        sAndroid.OnReposition()  # 機器人重置
                        continue

            sInfo = pSrvUserItem.mUserInfo
            INFO("OnEventUserLogout UUID:%s, Reason: %s, Close: %s, dismiss_flag: %s",
                 sInfo.mUUID, e_user_logout_type.Name(dwLeaveReason), bClose, dismiss_flag)

            # 写退出日志
            self.OnLoginLog(pSrvUserItem, False)
            pSrvUserItem.SetSrvUserStatus(eUS.US_NULL, INVALID_TABLE, INVALID_CHAIR)

            if not ServiceOpt.IsEducateSvr():
                rp = RDSPGuard.RP("game")
                #保存全局json数据
                results = rp.LibGrd.Call("common.GetInfoBySYS", *(sInfo.mUUID,))
                # 試玩桌因為access token網址拿掉，進入，沒有redis資訊，所以無資訊必須避開維護
                if results is None or results[0] != 0 or results[1] == None:
                    return
                # 機器人沒有base，所以機器人強制剔除必須避開account_base
                account_base = db_data_user()
                account_base.ParseFromString(results[1])
                account_base.jsondata = json.dumps(sInfo.mJson)
                account_base_ss = account_base.SerializeToString()
                rp.LibGrd.Call("common.SetInfoBySYS", *(sInfo.mUUID, account_base_ss))
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商 同步base
                #     self.SyncBase(account_base.hostuuid, account_base, account_base.channel)
                #下线
                rp.LibGrd.Call("common.OnLogoutSG", *(sInfo.mUUID,))
                # 下線時，多代理商的var@host_也要將指定商戶的指定玩家，從多代理商移除
                single_host_api_key = account_base.sin_channel
                rp.LibGrd.R.hdel("var@host_" + str(single_host_api_key), str(account_base.uuid), account_base.uuid)
                # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商 同步svr_id
                #     # 同步單代理商的svr_id，讓單代理商知道多代理商已經結束遊戲了
                #     self.SyncDelSvrID(account_base.hostuuid, account_base.channel)

                if not pSrvUserItem.IsAndroidUser:
                    # 保存json数据
                    self.SaveJson(pSrvUserItem.mUserInfo.mUUID, pSrvUserItem.mUserInfo.mSubJson)
                    # auto translate
                    self.AutoTranslateOut(sInfo.mUUID, account_base.sin_channel, results[3].decode(), sInfo.mSdkUUID)

            # 关闭或者/等待关闭链接
            dwSocketID = pSrvUserItem.SocketID
            pNetParams = self.GetNetBindParams(dwSocketID)
            if bClose:
                if pNetParams is not None:
                    del self.mID2Conn[dwSocketID]
                self.mServer.SafeClose(dwSocketID)
                pSrvUserItem.Detach()
            else:
                pSrvUserItem.Detach()
                if pNetParams is not None:
                    pNetParams.mISvrUserItem = None
                    self.mWaitClose[dwSocketID] = GetServerTime()
            SvrUsrMgr.DelSvrUserItem(pSrvUserItem)
        except:
            PrintEXC()

    def OnEventUserKick(self, pSrvUserItem, nReason, bLogout=True):
        if not pSrvUserItem.IsAndroidUser:
            msg_logout = msg_user_logout_ret()
            msg_logout.uuid = pSrvUserItem.mUserInfo.mUUID
            msg_logout.reason = nReason
            self.SendToClient(pSrvUserItem.SocketID, e_msgid_game_login, e_cg_msgid_logout, msg_logout)
            #下线，断开连接
            if bLogout:
                self.OnEventUserLogout(pSrvUserItem, nReason, False)

    def OnLoginLog(self, pSrvUserItem, islogin:bool,):
        # 试玩场不记录日志
        if pSrvUserItem is None or ServiceOpt.IsEducateSvr():
            return
        sInfo = pSrvUserItem.mUserInfo
        mJsonLog = {}
        mJsonLog["uuid"] = sInfo.mUUID
        mJsonLog["server_uuid"] = ServiceOpt.sSvrUUID
        mJsonLog["hashkey"] = ServiceOpt.sHashKey
        mJsonLog["subgame_id"] = ServiceOpt.sSubGameId
        mJsonLog["logType"] = 3 if islogin else 4
        mJsonLog["host_api_key"] = sInfo.mChannel
        mJsonLog["member_id"] = sInfo.mSdkUUID
        if isinstance(sInfo.mNickName, bytes):
            mJsonLog["nickname"] = sInfo.mNickName.decode('utf-8')
        else:
            mJsonLog["nickname"] = sInfo.mNickName
        mJsonLog["ip"] = pSrvUserItem.mIpAddr
        mJsonLog["source"] = sInfo.mSource
        mJsonLog["time"] = GetServerTimeStr()
        mJsonLog["score"] = sInfo.mScore
        try:
            #tableName = "game_login_log_" + time.strftime("%Y%m%d", time.localtime(time.time()))
            #self.WriteLog(tableName, json.dumps(mJsonLog))
            tableName = "game_login_log"
            self.WriteLog(tableName, json.dumps(mJsonLog))
        except:
            PrintEXC()

    def WriteLog(self, colname, jsonstr):  # 寫入dmgamelog
        if ServiceOpt.IsEducateSvr():  # 試玩房不用寫遊戲紀錄
            return
        if colname not in self.mLogCaches:
            self.mLogCaches[colname] = []
        self.mLogCaches[colname].append(jsonstr)

    def WriteVipLogFromAttempter(self, colname, jsonstr):  # 寫入dmgamelog的vip_log
        if ServiceOpt.IsEducateSvr():
            return
        if colname not in self.mVipLog:
            self.mVipLog[colname] = []
        self.mVipLog[colname].append(jsonstr)

    def WriteVipPlayerFromAttempter(self, colname, jsonstr):  # 寫入dmgame的VIP_player
        if ServiceOpt.IsEducateSvr():
            return
        if colname not in self.mVipPlayer:
            self.mVipPlayer[colname] = []
        self.mVipPlayer[colname].append(jsonstr)

    def WriteNotice(self, host_api_key, notice):
        self.CreateTask(self.AsyncWriteNotice(host_api_key, notice))

    async def AsyncWriteNotice(self, host_api_key, notice):
        try:
            rp = RDSPGuard.RP("gamelist")
            if await rp.AsyncHelper.Exec("LLEN", "list@notice_" + host_api_key) >= self.nMaxNotice:
                await rp.AsyncHelper.Exec("RPOP", "list@notice_" + host_api_key)
            await rp.AsyncHelper.Exec("LPUSH", "list@notice_" + host_api_key, notice)
        except:
            PrintEXC()

    def WriteUserScore(self, wChairID, pSrvUserItem, StrRoundSign, tableID=None, modscore=None):
        member_grade_calculation = {}  # 初始先設定沒有等級資訊可回傳時
        sInfo = pSrvUserItem.mUserInfo
        # 即时写分
        #writemsg = msg_write_user_score()
        #writemsg.uuid = sInfo.mUUID

        #writemsg.var_info.score = sInfo.mVarInfo.mScore
        #writemsg.var_info.subgamescore = 0
        nVarScore = sInfo.mVarInfo.mScore
        sInfo.mVarInfo.Clean()

        if not pSrvUserItem.IsAndroidUser:
            if sInfo.mCtrlScore != 0 or sInfo.mCtrlStatus != 0:
                if sInfo.mCtrlScore != 0 and sInfo.mCtrlStatus != 0:
                    if nVarScore != 0:
                        if ((nVarScore * sInfo.mCtrlScore) > 0) \
                                and (abs(nVarScore) >= abs(sInfo.mCtrlScore)):
                            sInfo.mCtrlScore = 0
                            sInfo.mCtrlStatus = 0
                        else:
                            sInfo.mCtrlScore -= nVarScore
                else:
                    sInfo.mCtrlScore = 0
                    sInfo.mCtrlStatus = 0

        if pSrvUserItem.TableID != INVALID_TABLE:
            msg = msg_money_change()
            msg.delta_score = nVarScore
            msg.score = sInfo.mScore
            msg.chair_id = pSrvUserItem.ChairID
            self.SendToTableClient(pSrvUserItem.TableID,
                              e_msgid_game_action, e_cg_msgid_money_change, msg)

        # 训练场、机器人不计入分数
        if not pSrvUserItem.IsAndroidUser and not ServiceOpt.IsEducateSvr():
            #ServiceOpt.sStatusInfo.nTotalProfit += (0 - nVarScore)
            #ServiceOpt.sStatusInfo.nTodayProfit += (0 - nVarScore)

            rp = RDSPGuard.RP("game")
            results = rp.LibGrd.Call("common.GetInfoBySYS", *(sInfo.mUUID,))
            # 試玩桌因為access token網址拿掉，進入，沒有redis資訊，所以無資訊必須避開維護
            if results is None or results[0] != 0 or results[1] == None:
                return
            account_base = db_data_user()
            account_base.ParseFromString(results[1])

            '''
            chl_resp = rp.LibGrd.Call("channel.GetInfo", *(ServiceOpt.sHostApiKey,))
            #tmp = OnRedisResultParser(chl_resp[1])
            ctm_data = json.loads(tmp["extra"])
            if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
                gs_url = ctm_data["gs_url"]
                host_chl = "CARD_" + account_base.channel
                if host_chl in gs_url:
                    gs_url = gs_url[host_chl]
            '''

            servZeroTime = GetServerZeroTime()
            if account_base.lastscoretime == 0 or \
                    account_base.lastscoretime < servZeroTime:
                account_base.dailyprofit = 0
                account_base.lastscoretime = servZeroTime

            # 計算會員等級是否升級
            member_grade_calculation = self.member_grade_calculation(account_base, wChairID, modscore)
            if member_grade_calculation != None:
                account_base.lv = member_grade_calculation["lv"]  # 寫入等級
                account_base.play_times = member_grade_calculation["play_times"]  # 寫入生涯遊玩次數
                account_base.all_win_times = member_grade_calculation["all_win_times"]  # 寫入生涯勝場數

            account_base.dailyprofit += nVarScore
            account_base.profit += nVarScore
            account_base.score = sInfo.mScore
            account_base.control_status = sInfo.mCtrlStatus
            account_base.control_score = sInfo.mCtrlScore
            # account_base_ss = account_base.SerializeToString()
            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     wallet_type = RequestHelper.DoPost(gs_url + "/wallettype", {"host_api_key": account_base.channel})
            #     wallet_type = wallet_type["data"]
            #     if wallet_type == 0:
            #         chl_resp = rp.LibGrd.Call("channel.GetInfo", *(ServiceOpt.sHostApiKey,))
            #         chl_data = OnRedisResultParser(chl_resp[1])
            #         ctm_data = json.loads(chl_data["extra"])
            #         gs_url = ctm_data["gs_url"]
            #         host_chl = "CARD_" + account_base.channel
            #         gs_url = gs_url[host_chl] + "/multihostscore"
            #         data = {
            #             "uuid": account_base.hostuuid,
            #             "lastscoretime": account_base.lastscoretime,
            #             "dailyprofit": account_base.dailyprofit,
            #             "profit": account_base.profit,
            #             "score": account_base.score,
            #             "control_status": account_base.control_status,
            #             "control_score": account_base.control_score
            #         }
            #         results = RequestHelper.DoPost(gs_url, data)

            if account_base.last_game_uuid != StrRoundSign:
                account_base.last_game_uuid = StrRoundSign
                account_base_ss = account_base.SerializeToString()
                rp.LibGrd.Call("common.SetInfoBySYS", *(sInfo.mUUID, account_base_ss))
            else:
                Log(f'桌號相等 桌號:{account_base.last_game_uuid}, 玩家:{sInfo.mUUID}, score: {account_base.score}')

            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商 同步base
            #     self.SyncBase(account_base.hostuuid, account_base, account_base.channel)

        if ServiceOpt.IsEducateSvr():  # 如果是試玩房，還是要隨便給出會員等級
            member_grade_calculation = self.member_grade_calculation(None, wChairID, modscore)
        if pSrvUserItem.IsAndroidUser:  # 如果是機器人，還是要算出會員等級
            member_grade_calculation = self.android_grade_calculation(tableID, wChairID, modscore)

        return member_grade_calculation  # 回傳會員等級資訊

    def member_grade_calculation(self, account_base, chairID, modscore):  # 計算會員等級是否升級(個人資訊, 座號, 本場的輸贏分)
        resp = {}
        resp["chair_id"] = chairID

        if account_base == None:  # 如果是試玩房
            resp["lv"] = 1  # 試玩人員等級最初階
            resp["play_times"] = 1  # 玩了一次這試玩房
            resp["all_win_times"] = 1  # 隨便當她贏了一場

        elif account_base.lv == None or account_base.lv == 0:  # 如果是生涯第一次遊戲結束
            resp["lv"] = 1  # 1等
            resp["play_times"] = 1  # 玩了一次
            if modscore != None and modscore > 0:  # 如果贏了
                resp["all_win_times"] = 1  # 生涯累積1勝
            else:  # 如果沒贏
                resp["all_win_times"] = 0  # 生涯累積0勝
        else:  # 如果早已經玩過遊戲了，而且是正式房
            # 從個人資訊base取得還沒計算的等級、生涯遊玩次數、生涯勝場數---
            resp["lv"] = int(account_base.lv)
            resp["play_times"] = int(account_base.play_times) + 1  # 遊戲結束時，玩完了這一次
            resp["all_win_times"] = int(account_base.all_win_times)
            # 取得下一等級所需的勝場數
            upgrade_requirement = ServerMYP.upgrade_threshold_list
            if modscore != None and modscore > 0 and resp["lv"] < 80:  # 如果贏了
                resp["all_win_times"] = resp["all_win_times"] + 1  # 生涯累積勝場+1，最高到80等(104350)
                next_need_wins = sum(upgrade_requirement[0: resp["lv"] + 1])  # 累積加總從1等至N等，所需勝場數
                if resp["all_win_times"] >= next_need_wins and resp["lv"] < 80:  # 若目前勝場數達成下一級所需勝場數
                    resp["lv"] = resp["lv"] + 1  # 升級，最高到80等
        return resp

    def android_grade_calculation(self, tableID, chairID, modscore):  # 計算機器人等級資訊(桌號, 座號, 本場的輸贏分)
        resp = {}
        resp["chair_id"] = chairID
        # 取得商戶名稱
        host_name = UserRP.get_host_name(ServiceOpt.sHostApiKey)
        android_data = UserRP.get_account_android(ServiceOpt.sSubGameId, tableID, chairID, host_name)  # 取得機器人個人等級資訊

        if android_data:
            resp["lv"] = android_data["MemberLv"]
            if modscore != None and modscore > 0 and resp["lv"] < 80:  # 如果贏了
                resp["play_times"] = android_data["play_times"] + 1  # 生涯累積遊玩場次+1，最高到80等(104350)
                resp["all_win_times"] = android_data["all_win_times"] + 1  # 生涯累積勝場+1
            else:
                resp["play_times"] = android_data["play_times"]
                resp["all_win_times"] = android_data["all_win_times"]
        else:
            resp["lv"] = 1
            resp["play_times"] = 1
            if modscore != None and modscore > 0:  # 如果贏了
                resp["all_win_times"] = 1
            else:
                resp["all_win_times"] = 0
        return resp

    def SaveJson(self, uuid, json_data):
        rp = RDSPGuard.RP("subgame")
        DEBUG("SaveJson, uuid = %d, sComboLevel = %d, json_data = %s", uuid, ServiceOpt.sSubGameId, json_data)
        rp.LibGrd.Call("subgame.SaveData", *(uuid, ServiceOpt.sSubGameId, json_data))

    def SaveAuthCode(self, sbAuthCode):
        rp = RDSPGuard.RP("game")
        rp.LibGrd.R.hset("sha@roompwd", sbAuthCode, json.dumps({
            "server_id" : ServiceOpt.sSvrUUID,
            "subgame_id" : ServiceOpt.sSubGameId,
            "addr" : self.mApp.mConfigs["svr_addr"],
            "port" : ServiceOpt.sSvrPort,
            "access_score" : ServiceOpt.sMinEnterScore,
        }))

    def DelAuthCode(self, sbAuthCode):
        rp = RDSPGuard.RP("game")
        rp.LibGrd.R.hdel("sha@roompwd", sbAuthCode)

    def shutdown_cron_job(self):
        Log('shutdown hot_update cron job')
        self.scheduler.remove_job('hot_update')
        self.scheduler.shutdown(wait=False)
