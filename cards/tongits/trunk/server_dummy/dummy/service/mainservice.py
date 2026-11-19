import os
import asyncio
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado import ioloop
from tornado.ioloop import IOLoop
from urls import sUrls
from redisassist import RDSPGuard, UserRP, EventRP
from mysqlassist import MYPGuard
import subscribe
from servlist import *
from c_l_lobby_pb2 import *
from xxt_encrypt import *
from handlers import *
from dblogmgr import DBLogMgr
from async import AsyncGuard
from requesthelper import RequestHelper
from utils import *
import json
import handlers
import copy

program_version_data = {}  # 設置全域變數，在開啟遊戲時即存入版本，避免重複開啟json影響效能

class MainServiceError(Exception):
    pass

class MainService(Application):

    @classmethod
    def StartService(cls, **options):
        service = cls(**options)
        service.InitComponents()
        service.Start()

    def __init__(self, **options):
        super(MainService, self).__init__(sUrls, **options)

        self.mPort = 9800
        self.mHTTPService = None
        self.mRPGuard = None
        self.mMYPGuard = None
        self.mAsyncGuard = None
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

    @property
    def AsyncGuard(self):
        return self.mAsyncGuard

    def Start(self):
        if self.mRunning:
            Warn("MainService已启动！")

        if "ssl" in self.settings:
            self.mHTTPService = HTTPServer(self, ssl_options = self.settings["ssl"])
        else:
            self.mHTTPService = HTTPServer(self)
        self.mHTTPService.listen(self.mPort)
        self.mRunning = True
        self.CreateTask(self.OnAsyncKeepAlive())
        self.CreateTask(self.OnAsyncUpdateOnline())
        Info("[服务启动成功][端口：%d]" % self.mPort)
        WritePidAndSignal(self.ConcludeService)
        IOLoop.instance().start()

    def ConcludeService(self, signalnum, frame):
        try:
            Info("[请求关闭服务器]")
            self.mRunning = False
            self.CreateTask(self.OnWaitClose())
        except:
            exit()

    async def OnWaitClose(self):
        # 全部执行下线
        rp = RDSPGuard.RP("game")
        results = await rp.AsyncHelper.Exec("HGETALL", "sha@keepalive")
        if results != None and isinstance(results, dict) == True:
            for kv in results.items():
                if kv[0].isdigit() and kv[1].isdigit():
                    uuid, lasttime = int(kv[0]), int(kv[1])
                    DEBUG("玩家[%d]下线", uuid)
                    account_res = await rp.LibGrd.AsyncCall("common.GetInfoBySYS", *(uuid,))
                    if account_res[0] != 0 or len(account_res) < 5:
                        continue
                    account_base = db_data_user()
                    account_base.ParseFromString(account_res[1])
                    access_token = account_res[4].decode()

                    await self.OnLogout(uuid, account_base.sin_channel, access_token)
        await rp.AsyncHelper.Exec("DEL", "sha@keepalive")

        starttime = GetServerTime()
        while True:
            if self.mAsyncGuard.GetCount() == 0 \
                    or GetServerTime() - starttime > 5:
                break
            asyncio.sleep(0.02)
        IOLoop.current().stop()
        self.mHTTPService.stop()
        Info("【服务器关闭完成】")

    def VersionJson(self):
        # 設定全域變數，在開啟遊戲時即存入版本，避免重複開啟json影響效能
        global program_version_data
        # 開啟Version.json取得目前的後端程式版本
        if os.path.isfile('Version.json'):
            Log("Version.json檔案存在。")
            # 檔案存在才打開檔案
            with open('Version.json', 'r') as f:
                program_version_data = f.read()
                Log("Program_Version={}".format(program_version_data))
            f.close()
        else:
            Log("Version.json檔案不存在。")

    def InitComponents(self):
        data = self.settings

        if "dbg_lv" in data:
            DebugLevel.Set(int(data["dbg_lv"]))
            LOGService.Set(int(data["dbg_lv"]))

        if "redis_dbg_lv" in data:
            RDSPGuard.SetDebugLevel(int(data["redis_dbg_lv"]))

        if "mysql_dbg_lv" in data:
            MYPGuard.SetDebugLevel(int(data["mysql_dbg_lv"]))

        if "redis_cfg_path" in data:
            if not self.InitRPGuard(data["redis_cfg_path"]):
                raise MainServiceError("初始化Redis失败！")
            RDSPGuard.ProcWith(self.ConfigAllRP)
            EventRP.load_init()
            UserRP.load_init()
        else:
            raise MainServiceError("缺少Redis配置路径！")

        if "mysql_cfg_path" in data:
            if not self.InitMYPGuard(data["mysql_cfg_path"], data["server_math_info"]):
                raise MainServiceError("初始化MySQL失败！")

            MYPGuard.ProcWith(self.ConfigAllMYP)
            self.CreateTask(ServerMYP.load_init())
        else:
            raise MainServiceError("缺少MySQL配置路径！")

        if "async" in data:
            self.mAsyncGuard = AsyncGuard(**(data["async"]))
        else:
            self.mAsyncGuard = AsyncGuard()

        self.dbLog = ioloop.PeriodicCallback(DBLogMgr.OnEventWriteDBLogs, 2 * 1000)  # 这里的时间是毫秒
        self.dbLog.start()

        self.active = ioloop.PeriodicCallback(self.OnShowActiveStatus, 300 * 1000)  # 这里的时间是毫秒
        self.active.start()

        if "port" in data:
            self.mPort = int(data["port"])
        if "xxtkey" in data:
            XXTEncrypt.SetKey(data["xxtkey"])

        # 加载服务器列表
        self.GetServerList()
        # 開啟Version.json取得目前的後端程式版本
        self.VersionJson()

    def InitRPGuard(self, path):
        if self.mRPGuard is not None:
            return False
        self.mRPGuard = RDSPGuard.LoadByFile(path)
        return self.mRPGuard is not None

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

    def ConfigAllRP(self, rp):
        pubsub = rp.PubSub
        if pubsub is not None:
            pubsub.OnPubMsgCB = subscribe.SubscribecbHandler.OnRedisSubscribeCB
            self.CreateTask(pubsub.AsyncUpdate())
        libgrd = rp.LibGrd
        if libgrd is not None:
            self.CreateTask(libgrd.AsyncUpdate())

    def ConfigAllMYP(self, myp):
        self.CreateTask(myp.AsyncUpdate())

    def CreateTask(self, co):
        IOLoop.current().asyncio_loop.create_task(co)

    def GetServerList(self):
        # data = self.settings
        # host_api_key = data["multihost"]["hostkey"]
        # multi_host = 0
        rp = RDSPGuard.RP("game")

        # inf_resp = rp.LibGrd.R.hgetall("multi@inf_" + "8482c6afb2b6f032f3ab245346077c74")
        # if inf_resp is not None:
        #     print(type(inf_resp))
        #     print(11111111111111, inf_resp)
        #     print(11111111111111, len(inf_resp))

        # channel_res = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
        # if channel_res[0] == 0:
        #     chl_data = OnRedisResultParser(channel_res[1])
        #     ctm_data = json.loads(chl_data["extra"])
            # if "multihost" in ctm_data:
            #     multi_host = ctm_data["multihost"]
        # if multi_host == 1:
        #     rp1 = self.mRPGuard.RP("gamelist_multihost")
        #     server_list_db = rp1.LibGrd.R.get("var@serverlist")
        # else:
        rp1 = self.mRPGuard.RP("gamelist")
        server_list_db = rp1.LibGrd.R.get("var@serverlist")
        if server_list_db == None or len(server_list_db) == 0:
            return
        server_list = get_game_server_list_ret()
        server_list.ParseFromString(server_list_db)

        for idx in range(len(server_list.gslist)):
            ServListMgr.AddServ(server_list.gslist[idx])

    def OnShowActiveStatus(self):
        Info("当前时间：%s" % GetServerTimeStr())

    async def OnAsyncKeepAlive(self, await_time = 5, keep_timeout = 60):
        while self.mRunning:
            # await asyncio.sleep(await_time) //移至尾端，目的讓server開機就先跑一次。2023/02/10-Jason
            nowtime = GetServerTime()
            rp = RDSPGuard.RP("game")
            results = await rp.AsyncHelper.Exec("HGETALL", "sha@keepalive")
            if results != None and isinstance(results, dict) == True:
                for kv in results.items():
                    if kv[0].isdigit() and kv[1].isdigit():
                        uuid, lasttime = int(kv[0]), int(kv[1])
                        if nowtime - lasttime > keep_timeout:
                            account_res = await rp.LibGrd.AsyncCall("common.GetInfoBySYS", *(uuid,))
                            if account_res[0] != 0 or len(account_res) < 5:
                                continue
                            if account_res[1] == None:
                                continue

                            account_base = db_data_user()
                            account_base.ParseFromString(account_res[1])

                            # 若玩家在遊戲中且尚未結算, 檢查該局是否已結算
                            checkResult = await self.checkGameEnd(account_base)
                            if checkResult == False:
                                continue

                            # 玩家已無在進行遊戲
                            DEBUG("玩家uuid:%d nickname:%s 下线", uuid, account_base.nickname)
                            # multihost_uuid = account_base.hostuuid  # 由來源uuid抓取裡面的多代理服務的玩家uuid
                            access_token = account_res[4].decode()
                            # # 取得cfg→multihost→多代理服務主機位址
                            # url = self.settings["multihost"]["service"]
                            # # 向多代理服務主機→service server→handlers→HDRIsGaming請求遊戲狀態
                            # is_gaming = RequestHelper.DoPost(url + "/isgaming", {"hostuuid": multihost_uuid})
                            # # 如果不在遊戲中，才進入OnLogout轉錢至ps
                            # if is_gaming == False:
                            # if self.CheckMultiHostSwitch(account_base):  # 多代理商模式
                            #     await self.OnLogoutFromKeepAlive(uuid, account_base.channel, access_token,
                            #                                      handlers.ask_ps_to_final_trade_is_fail)
                            # else:  # 單代理商模式

                            await self.OnLogout(uuid, account_base.sin_channel, access_token,
                                                    handlers.ask_ps_to_final_trade_is_fail, False)
                            await rp.AsyncHelper.Exec("HDEL", "sha@keepalive", str(uuid))
            await asyncio.sleep(await_time)
    # def CheckMultiHostSwitch(self, account_base):
    #     try:
    #         # 查詢多代理商開關
    #         multi_host = 0
    #         rp = RDSPGuard.RP("game")
    #         channel_res = rp.LibGrd.Call("channel.GetInfo", *(account_base.channel,))
    #         if channel_res[0] == 0:
    #             chl_data = OnRedisResultParser(channel_res[1])
    #             ctm_data = json.loads(chl_data["extra"])
    #             if "multihost" in ctm_data:
    #                 multi_host = ctm_data["multihost"]  # 多代理商開啟或關閉
    #                 if multi_host == 1:  # 若多代理商模式開啟
    #                     return True
    #                 return False
    #             return False
    #         return False
    #     except:
    #         PrintEXC()

    async def OnAsyncUpdateOnline(self, await_time = 60):
        while self.mRunning:
            await asyncio.sleep(await_time)
            try:
                rp = RDSPGuard.RP("gamelist")
                results = await rp.AsyncHelper.Exec("HGETALL", "sha@onlinenums")
                ServListMgr.OnUpdate(results)
            except:
                PrintEXC()

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

    def TradeLog(self, type, data, channel):  # 公版寫入或更新dmgamelog資料庫內容
        try:
            sqlp = MYPGuard.MYP("log")
            sql = sSqls[type]
            sqlp.Exec(sql=sql.GetSQL(params=data), callback=None)
        except:
            PrintEXC()

    async def OnLogout(self, uuid, host_api_key, access_token, ask_ps_to_final_trade_is_fail, needCheckGameEnd = True):
        try:
            DEBUG("玩家uuid:%d OnLogout", uuid)
            #auto trans
            while True:
                if ask_ps_to_final_trade_is_fail == True:  # 若向ps請求最後一筆交易沒有回應
                    Warn(f"uuid:{uuid} ask_ps_to_final_trade_is_fail!")
                    break  # 單代理商的遊戲錢包就咬死不能轉出

                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
                if chl_resp[0] != 0:
                    Warn(f"host_api_key:{host_api_key} channel get info error!")
                    break

                chl_data = OnRedisResultParser(chl_resp[1])
                ctm_data = json.loads(chl_data["extra"])
                if ctm_data["auto_trans"] != 1:
                    DEBUG("uuid:%d auto_trans: 0", uuid)
                    break

                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                if account_res[0] != 0:
                    Warn(f"uuid:{uuid} auto translate error : -1 error")
                    break

                account_base = db_data_user()
                account_base.ParseFromString(account_res[1])
                if account_base.score <= 0:
                    DEBUG("uuid:%d score: 0", uuid)
                    break

                if needCheckGameEnd:
                    checkResult = await self.checkGameEnd(account_base)
                    if checkResult == False:
                        Warn(f"uuid:{uuid} game not end!")
                        return

                if access_token == 0 or access_token != account_res[4].decode():
                    Warn(f"uuid:{uuid} auto translate error : -4 invalid token")
                    break
                #共享錢包refund開始
                wallet_type = ctm_data["wallet_type"]
                if wallet_type == 1:
                    multi_inf = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + account_base.channel, account_base.sin_channel)
                    multi_inf = json.loads(multi_inf)
                    host_url = multi_inf["host_url"]

                    dl_url = host_url["base_url"] + "/" + host_url["refundbet"]
                    response = RequestHelper.DoGet(dl_url,
                                                {"access_token": account_res[4].decode(), "txn_id": account_base.sn})
                    # txn_id = "%.3d%.13d%.3d" % 。(GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                    if response and response["status_code"] == 0:  # 若共享方反饋正常
                        # 向redis撤銷base.txn_id單號
                        refundbet_error_result = {"txn_id": account_base.sn, "host_api_key": account_base.sin_channel,
                                                "uuid": uuid}
                        self._SuccessRefundbetAndWriteBase(account_base, refundbet_error_result, response)
                        self._delete_fake_data_from_ps_db(account_base)
                    else:
                         #refund失敗 寫入錯誤LOG 有紀錄方便後面開發refundex機制
                        status = -100 if response == None else response["status_code"]
                        refundbet_data = {"txn_id": account_base.sn, "uuid": uuid,
                                        "member_id": str(account_base.sdk_uuid), "host_api_key": account_base.sin_channel,
                                        "amount": tranout, "status": status, "date": GetServerTimeStr()}
                        # 寫入game_bet_error_log資料表
                        self.TradeLog("insert_once_refundbet_error", refundbet_data, host_api_key)

                        err_msg = ", memberid: " + str(account_base.sdk_uuid) + ", bet: " + str(tranout)
                        data = {"txn": account_base.sn, "host": account_base.sin_channel, "type": 0, "action": 1,
                                "err_code": 4,
                                "err_descr": "results == None, " + err_msg,
                                "time": GetServerTimeStr()}
                        self.TradeLog("add_hosterrlog", data, host_api_key)

                        Warn("--- OnUserTranslate Game to PS Failed member_id=", account_base.sdk_uuid, " score=",
                            account_base.score, " - ", tranout, " response=None", f"sn:{account_base.sn}")
                #獨立錢包
                elif wallet_type == 0:

                    txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                    rp2 = RDSPGuard.RP("tradelist")
                    set_list_success = await rp2.AsyncHelper.Exec("SETNX", "list@trade_" + str(uuid), txn_id)  # 新增人員
                    if set_list_success == True:  # 寫入list@trade_成功，才走4分鐘流程
                        await rp2.AsyncHelper.Exec("EXPIRE", "list@trade_" + str(uuid), 240)  # 設定4分鐘
                    timeStamp = GetServerTimeStr()
                    rollin = await rp2.AsyncHelper.Exec("get", "list@trade_" + str(uuid))
                    if (str(json.loads(rollin)) != txn_id):
                        Warn(f"uuid:{uuid} get trade txn_id error")
                        return -10, "Please confirm your account balance after 4 minutes."
                    op = "in" # 游戏转到PS
                    balance = account_base.score

                    # pre-borrowed balance to redis, fixed the online problem by Leo.
                    account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                    account_base.ParseFromString(account_res[1])
                    Warn("--- OnLogout member_id=", account_base.sdk_uuid, " score=", balance, " - balance=", balance)
                    account_base.score -= balance
                    account_buffer = account_base.SerializeToString()
                    rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))
                    multi_inf = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + account_base.channel, account_base.sin_channel)
                    multi_inf = json.loads(multi_inf)

                    # check final score
                    account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                    account_base.ParseFromString(account_res[1])
                    Warn("--- OnLogout check, member_id=", account_base.sdk_uuid, " score=", account_base.score)

                    # 二轉玩家判斷
                    cantrans = 1
                    sMainSQL = '''SELECT * FROM `dmgamelog`.`game_trade_log` WHERE `member_id` = '%(memberid)s' ORDER BY dtm DESC LIMIT 1;;'''
                    hints = {}
                    sql = sMainSQL % {"memberid": account_base.sdk_uuid}
                    result = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                    if result != None:
                        if len(result) == 0 or (result[0]["amount"] == balance and result[0]["type"] == 0):
                            cantrans = 0
                            # 交易錯誤日志
                            data = {"txn": txn_id, "host": account_base.sin_channel, "type": 3,
                                    "memberid": account_base.sdk_uuid,
                                    "amount": balance, "time": timeStamp, "end": 0}
                            TradeLog("add_tradeerrlog", data)
                            await rp2.AsyncHelper.Exec("DEL", "list@trade_" + str(uuid))  # 刪除人員名單及時間戳
                    if cantrans == 1:
                        # 交易錯誤日志
                        sql = sSqls["add_tradeerrlog"]
                        MYPGuard.MYP("log").Exec(sql=sql.GetSQL(params={"txn": txn_id,
                                                                        "host": account_base.sin_channel,
                                                                        "type": 0,
                                                                        "memberid": account_base.sdk_uuid,
                                                                        "amount": balance,
                                                                        "time": timeStamp,
                                                                        "end": 0}), callback=None)
                        # request to ps server
                        # url = self.settings["ps_urls"]["rollin"]
                        # response = await self.mAsyncGuard.DoAsync(RequestHelper.ReqRollIn, url, account_base.channel,
                        #                                                       account_base.sdk_uuid, txn_id, balance)
                        # response = json.loads(response)

                        parameters = {
                            "amount": balance,
                            "host_id": multi_inf["host_id"],
                            "id": account_base.sdk_uuid
                        }
                        sqlp = MYPGuard.MYP(multi_inf["db_id"])
                        sql = sSqls["update_rollin_member"]
                        result = await sqlp.AsyncExec(sql=sql.GetSQL(params=parameters))

                        parameters = {
                            "txn_id": txn_id,
                            "type": 0,
                            "host_id": multi_inf["host_id"],
                            "member_id": account_base.sdk_uuid,
                            "amount": balance,
                            "note": "RollIn",
                            "id": account_base.sdk_uuid
                        }
                        sql = sSqls["insert_funds_log"]
                        result = await sqlp.AsyncExec(sql=sql.GetSQL(params=parameters))  # 寫入fundslog
                        response = {}
                        response["status_code"] = 0  # 成功後response = 0

                        # 刪除交易錯誤日志
                        sql = sSqls["delete_tradeerrlog"]
                        MYPGuard.MYP("log").Exec(sql=sql.GetSQL(params={"txn": txn_id,
                                                                        "host": account_base.sin_channel,
                                                                        "type": 0,
                                                                        "memberid": account_base.sdk_uuid,
                                                                        "amount": balance,
                                                                        "time": timeStamp,
                                                                        "end": 0}), callback=None)
                        # if response == None or response["status_code"] != 0:
                        #     # if fail then reback the balance
                        #     account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                        #     account_base.ParseFromString(account_res[1])
                        #     Warn("--- OnLogout Fail member_id=", account_base.sdk_uuid, " score=", balance, " + balance=", balance, " response=", response)
                        #     account_base.score += balance
                        #     account_buffer = account_base.SerializeToString()
                        #     rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))
                        #     Warn("auto translate error : -6")
                        #     break
                        await rp2.AsyncHelper.Exec("DEL", "list@trade_" + str(uuid))  # 刪除人員名單及時間戳

                        # 写日志
                        sqlp = MYPGuard.MYP("log")
                        sql = sSqls["add_tradelog"]
                        sqlp.Exec(sql=sql.GetSQL(params={"txn": txn_id,
                                                        "host": account_base.sin_channel,
                                                        "type": 0 if op == "in" else 1,
                                                        "memberid": account_base.sdk_uuid, "amount": balance,
                                                        "time": timeStamp}), callback=None)

                # 推送平台下线
                url = self.settings["ps_urls"]["logout"]
                await self.mAsyncGuard.DoAsync(RequestHelper.ReqLogout, url, host_api_key, access_token)
                # 执行游戏下线
                rp = RDSPGuard.RP("game")
                await rp.LibGrd.AsyncCall("common.OnLogoutSG", *(uuid,))
                await rp.LibGrd.AsyncCall("common.OnLogout", *(uuid,))

                # 玩家下線時，儲存玩家登出時間
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                save_logout_time = db_data_user()
                save_logout_time.ParseFromString(account_res[1])
                save_logout_time.lastlogouttime = GetServerTime()  # 抓取下線當下時間
                save_logout_time_buffer = save_logout_time.SerializeToString()
                rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, save_logout_time_buffer))

                # check final score
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                account_base.ParseFromString(account_res[1])
                Warn("*** OnLogout Finished, member_id=", account_base.sdk_uuid, " score=", account_base.score)
                return

            #推送平台下线
            url = self.settings["ps_urls"]["logout"]
            await self.mAsyncGuard.DoAsync(RequestHelper.ReqLogout, url, host_api_key, access_token)
            #执行游戏下线
            rp = RDSPGuard.RP("game")
            await rp.LibGrd.AsyncCall("common.OnLogoutSG", *(uuid,))
            await rp.LibGrd.AsyncCall("common.OnLogout", *(uuid,))

            # 玩家下線時，儲存玩家登出時間
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            save_logout_time = db_data_user()
            save_logout_time.ParseFromString(account_res[1])
            save_logout_time.lastlogouttime = GetServerTime()  # 抓取下線當下時間
            save_logout_time_buffer = save_logout_time.SerializeToString()
            rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, save_logout_time_buffer))

            # check final score
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            account_base.ParseFromString(account_res[1])
            Warn("--- OnLogout Finished, member_id=", account_base.sdk_uuid, " score=", account_base.score)
        except:
            Err("OnLogout Fail, 玩家uuid: ", uuid)
            PrintEXC()

    async def OnLogoutFromKeepAlive(self, uuid, host_api_key, access_token, ask_ps_to_final_trade_is_fail, needCheckGameEnd = True):
        try:
            DEBUG("玩家uuid:%d OnLogoutFromKeepAlive", uuid)
            # auto trans
            while True:
                if ask_ps_to_final_trade_is_fail == True:  # 若向ps請求最後一筆交易沒有回應
                    break  # 多代理商的遊戲錢包就咬死不能轉出
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
                if chl_resp[0] != 0:
                    Warn(f"host_api_key:{host_api_key} channel get info error!")
                    break

                chl_data = OnRedisResultParser(chl_resp[1])
                ctm_data = json.loads(chl_data["extra"])
                if ctm_data["auto_trans"] != 1:
                    DEBUG("uuid:%d auto_trans: 0", uuid)
                    break

                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                if account_res[0] != 0:
                    Warn(f"uuid:{uuid} auto translate error : -1 error")
                    break

                account_base = db_data_user()
                account_base.ParseFromString(account_res[1])
                if account_base.score <= 0:
                    DEBUG("uuid:%d score: 0", uuid)
                    break

                if needCheckGameEnd:
                    checkResult = await self.checkGameEnd(account_base)
                    if checkResult == False:
                        Warn(f"uuid:{uuid} game not end!")
                        return

                if access_token == 0 or access_token != account_res[4].decode():
                    Warn(f"uuid:{uuid} auto translate error : -4 invalid token")
                    break

                # 向多代理商執行轉錢
                url = self.settings["multihost"]["service"] + "/multionlogout"
                await self.mAsyncGuard.DoAsync(RequestHelper.ReqMultiOnLogout, url, account_base.hostuuid)

                # 推送平台下线
                url = self.settings["ps_urls"]["logout"]
                await self.mAsyncGuard.DoAsync(RequestHelper.ReqLogout, url, host_api_key, access_token)
                # 执行游戏下线
                rp = RDSPGuard.RP("game")
                await rp.LibGrd.AsyncCall("common.OnLogoutSG", *(uuid,))
                await rp.LibGrd.AsyncCall("common.OnLogout", *(uuid,))

                # 玩家下線時，儲存玩家登出時間
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                save_logout_time = db_data_user()
                save_logout_time.ParseFromString(account_res[1])
                save_logout_time.score = 0  # 若「向多代理商執行轉錢」有執行清空score，則單代理商也要清空
                save_logout_time.lastlogouttime = GetServerTime()  # 抓取下線當下時間
                save_logout_time_buffer = save_logout_time.SerializeToString()
                rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, save_logout_time_buffer))

                # check final score
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                account_base.ParseFromString(account_res[1])
                Warn("--- OnLogoutFromKeepAlive Finished, member_id=", account_base.sdk_uuid, " score=",
                     account_base.score)
                return

            #推送平台下线
            url = self.settings["ps_urls"]["logout"]
            await self.mAsyncGuard.DoAsync(RequestHelper.ReqLogout, url, host_api_key, access_token)
            #执行游戏下线
            rp = RDSPGuard.RP("game")
            await rp.LibGrd.AsyncCall("common.OnLogoutSG", *(uuid,))
            await rp.LibGrd.AsyncCall("common.OnLogout", *(uuid,))
            # 玩家下線時，儲存玩家登出時間
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            save_logout_time = db_data_user()
            save_logout_time.ParseFromString(account_res[1])
            save_logout_time.lastlogouttime = GetServerTime()  # 抓取下線當下時間
            save_logout_time_buffer = save_logout_time.SerializeToString()
            rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, save_logout_time_buffer))

            # check final score
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            account_base.ParseFromString(account_res[1])
            Warn("--- OnLogoutFromKeepAlive Finished, member_id=", account_base.sdk_uuid, " score=", account_base.score)
        except:
            Err("OnLogoutFromKeepAlive Fail, 玩家uuid: ", uuid)
            PrintEXC()

    async def checkGameEnd(self, account_base):
        try:
            fail_timeout = 900
            nowtime = GetServerTime()
            game_difftime = nowtime - account_base.last_game_starttime
            # 未開局 or 遊戲超時 or 已結束
            if account_base.last_game_starttime <= 0 or \
                    game_difftime > fail_timeout or \
                    account_base.current_game_uuid == account_base.last_game_uuid:
                return True

            myp = MYPGuard.MYP("log")
            sql = sSqls["query_play_count"]
            params = {
                "uuid": account_base.uuid,
                "round_id": account_base.current_game_uuid
            }

            query_result = await myp.AsyncExec(sql=sql.GetSQL(params=params))
            # 查無該局遊戲紀錄結果
            if query_result[0] == None or query_result[0]["count"] == 0:
                return False
            else:
                return True
        except:
            PrintEXC()
            return False
