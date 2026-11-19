
import random
import time
import datetime
import hashlib
import asyncio
from tornado.web import *
from redisassist import RDSPGuard, EventRP, UserRP
from mysqlassist import MYPGuard
from mysqlassist.myp_object import ServerMYP
from servlist import *
from utils import *
from xxt_encrypt import *
from dblogmgr import DBLogMgr
from urllib import request, parse
from md5_sign import *
import json
from main_cmd_pb2 import *
from error_pb2 import *
from c_g_game_pb2 import *
from center_game_pb2 import *
from c_l_lobby_pb2 import *
from data_struct_pb2 import *
from requesthelper import RequestHelper
from dbexecution import sSqls
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import Parse
import mainservice

allow_leverage = 1  # 設定全域變數，以小博大機制開關
ask_ps_to_final_trade_is_fail = False  # 設置全域變數，驗證向ps請求最後一筆交易是否失敗，決定斷線時遊戲錢包是否轉出

class MyResponse(object):
    def __init__(self, data = None):
        self.mData = {}
        if data is not None and isinstance(data, dict):
            self.mData.update(data)

    @classmethod
    def Create(cls, data = None):
        return cls(data = data)

    @property
    def Data(self):
        return self.mData

    def OK(self):
        self.mData["error_code"] = 0
        self.mData["msg"] = "success"

    def Except(self):
        self.mData["error_code"] = -99
        self.mData["msg"] = "system error"

    def Error(self, error_code, error_str):
        self.mData["error_code"] = error_code
        self.mData["msg"] = error_str

    def Add(self, k, v):
        if k is None or v is None:
            return False
        self.mData[k] = v

    def AddRes(self, t):
        if t is None or not isinstance(t, dict):
            return
        self.mData.update(t)

async def duplicate_transfer_check(settings, async_guard, myp_guard, host_api_key,
                                   member_id, balance, call_from=None):
    """檢查是否二轉玩家

        透過 GS API 取得玩家交易記錄判斷是否有二轉
        如果 GS API 沒記錄或執行過程中出現錯誤則從 MySQL DB 中取得記錄判斷

        Args:
            settings (dict): 伺服器的設定檔，main.json 那個檔案裡的資料
            async_guard (AsyncGuard): 主服務的 AsyncGuard 物件
            myp_guard (MYPGuard): 主服務的 AsyncGuard 物件
            host_api_key (str): 代理商 api key
            member_id (str): 玩家名稱
            balance (int): 此次操作轉出的金額
            call_from (str): 在呼叫時可以寫入文字，在發生錯誤時可以在 LOG 檔案知道是哪邊操作出問題

        Returns:
            0 代表二轉，1 代表正常
        """
    try:
        get_last_roll_ps_url = settings["ps_urls"]["get_last_roll"]

        post_data = {
            "host_api_key": host_api_key,
            "member_id": member_id
        }

        response = await async_guard.DoAsync(
            RequestHelper.DoPost, get_last_roll_ps_url, post_data)

        """
        if response:
            response = json.loads(response)
        else:
            Warn(f"{call_from} get_last_roll_ps_url no response")
            response = {}
        """

        has_record = response.get("status_code") == 0
        is_roll_out = response.get("note") == "RollIn"
        is_same_amount = response.get("amount") == balance

        if has_record and is_roll_out and is_same_amount:
            return 0

        if not has_record:
            sMainSQL = '''SELECT * FROM `dmgamelog`.`game_trade_log` WHERE `member_id` = '%(memberid)s' ORDER BY dtm DESC LIMIT 1;;'''
            sql = sMainSQL % {"memberid": member_id}

            result = await myp_guard.MYP("game").AsyncExec(sql=sql, hint={},
                                                           callback=None)

            if result and result[0]["amount"] == balance and result[0]["type"] == 0:
                return 0

    except Exception as e:
        Warn(f"duplicate_transfer_check has {e} error in {call_from}")

        sMainSQL = '''SELECT * FROM `dmgamelog`.`game_trade_log` WHERE `member_id` = '%(memberid)s' ORDER BY dtm DESC LIMIT 1;;'''
        sql = sMainSQL % {"memberid": member_id}

        result = await myp_guard.MYP("game").AsyncExec(sql=sql, hint={},
                                                       callback=None)

        if result and result[0]["amount"] == balance and result[0]["type"] == 0:
            return 0

    return 1

async def OnUserGetBalance(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid"))
        token = int(r.get_argument("token"))
        autotrans = r.get_argument("autotrans", default = None)
        subgameid = r.get_argument("subgameid", default=999)

        # Log("----------------------------------OnUserGetBalance Enter[", autotrans, "]")

        # autotrans:0 => only get balance
        # autotrans:1 => get balance and auto translate all host balance
        # autotrans:none => follow server option
        if autotrans != None:
            autotrans = int(autotrans)

        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0:
            return -1, "error"
        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])

        # 查詢多代理商開關
        # multi_host = 0
        # rp = RDSPGuard.RP("game")
        # channel_res = rp.LibGrd.Call("channel.GetInfo", *(account_base.channel,))
        # if channel_res[0] != 0:
        #     return -5, "error"
        # if channel_res[0] == 0:
        #     chl_data = OnRedisResultParser(channel_res[1])
        #     ctm_data = json.loads(chl_data["extra"])
        #     if "multihost" in ctm_data:
        #         multi_host = ctm_data["multihost"]

        # 測試人員跳過 API，直接回傳
        if account_base.user_type == 999:
            rsp = MyResponse.Create()
            rsp.OK()
            rsp.Add("data", {
                "uuid": account_base.uuid,
                "score": account_base.score,
                "balance": 1000000000
            })

            r.add_header("Access-Control-Allow-Origin", "*")
            r.write(json.dumps(rsp.Data))
            r.flush()
            r.finish()
            return 0, 'success'

        auth_token = 0 if len(account_res) < 4 else int(account_res[3].decode())
        if token == 0 or token != auth_token:
            return -4, "invalid token"
        host_api_key = account_base.channel
        # 錢包類型
        '''
        chl_resp = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
        if chl_resp[0] == 0:
            tmp = OnRedisResultParser(chl_resp[1])
            host_name = tmp["name"]
            wallet_type = json.loads(tmp["extra"])["wallet_type"]
        '''

        # print("multi_host", multi_host)
        # if multi_host:
        host_api_key = account_base.sin_channel
        multi_inf = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + account_base.channel,  account_base.sin_channel)
        multi_inf = json.loads(multi_inf)
        wallet_type = 0
        if "host_url" in multi_inf.keys():
            wallet_type = 1

        # channel_res = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
        # if channel_res[0] != 0:
        #     return -5, "error"

        if wallet_type:  # 共享錢包
            host_url = multi_inf["host_url"]
            # 確認卡錢轉出
            txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
            dl_url = host_url["base_url"] + "/" + host_url["getbalance"]
            err_msg = ", memberid: " + str(account_base.sdk_uuid)
            data = {"txn": txn_id, "host": account_base.sin_channel, "type": 6, "action": 6,
                    "err_code": 1, "err_descr": "response error" + err_msg, "time": GetServerTimeStr()}
            TradeLog("add_hosterrlog", data)
            results = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode()})
            TradeLog("delete_hosterrlog", data)
            if results == None:
                err_msg = ", memberid: " + str(account_base.sdk_uuid)
                data = {"txn": txn_id, "host": account_base.sin_channel, "type": 6, "action": 6,
                        "err_code": 4,
                        "err_descr": "results == None, " + err_msg,
                        "time": GetServerTimeStr()}
                TradeLog("add_hosterrlog", data)
                return -5, "error"
            elif results["status_code"] != 0:
                err_msg = ", memberid: " + str(account_base.sdk_uuid)
                data = {"txn": txn_id, "host": account_base.sin_channel, "type": 6, "action": 6,
                        "err_code": 4,
                        "err_descr": "response_status_code: " + str(results["status_code"]) + err_msg,
                        "time": GetServerTimeStr()}
                TradeLog("add_hosterrlog", data)
                return results["status_code"], ""

            rsp = MyResponse.Create()
            rsp.OK()
            rsp.Add("data", {
                "uuid": account_base.uuid,
                "score": account_base.score,
                "balance": 0 if "balance" not in results else results["balance"]
            })
        else:  # 獨立錢包
            url = multi_inf["ps_urls"]["getbalance"]
            response = await r.application.AsyncGuard.DoAsync(RequestHelper.ReqQueryBalance, url, account_base.sin_channel,
                                                              account_base.sdk_uuid)

            if response["status_code"] != 0:
                return response["status_code"], ""

            ask_ps_to_final_trade_is_fail = False  # 若發生斷線則正常執行與驗證轉出入流程
            if await rp.AsyncHelper.Exec("HGET", "save@myself", uuid):  # 若自救標籤存在
                await rp.AsyncHelper.Exec("HDEL", "save@myself", uuid)  # 則清除

            rsp = MyResponse.Create()
            rsp.OK()
            rsp.Add("data", {
                "uuid": account_base.uuid,
                "score": account_base.score,
                "balance": 0 if "balance" not in response else response["balance"],
                "save_myself": 1 if await rp.AsyncHelper.Exec("HGET", "save@myself", uuid) else 0
            })

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnUserGetBalanceDetails(r)->(int, str):  # 自救流程1分鐘後啟動
    try:
        uuid = int(r.get_argument("uuid"))
        if uuid == None:
            return -1, "uuid is none"

        # 取得玩家base
        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res == None:
            return 8, "member's base is none"

        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])

        # 1分鐘後，前端請求，系統判斷玩家base.score是否有錢
        if account_base.score > 0:
            status = 1  # 轉失敗

            if not await rp.AsyncHelper.Exec("HGET", "save@myself", uuid):  # 若自救標籤不存在
                await rp.AsyncHelper.Exec("HSET", "save@myself", uuid, account_base.nickname)  # 則建立標籤

            # mm示警
            mm_save_myself_url = r.application.settings.get("mm_save_myself_url", "")
            if mm_save_myself_url:
                text = "getbalance ask to ps api error: "
                text += "Member={}, ".format(account_base.nickname)
                text += "base_score={}".format(account_base.score)
                # 送出示警
                RequestHelper.DoPost(mm_save_myself_url, {"text": text})

        else:
            status = 0  # 轉成功

            if await rp.AsyncHelper.Exec("HGET", "save@myself", uuid):  # 若自救標籤存在
                await rp.AsyncHelper.Exec("HDEL", "save@myself", uuid)  # 則清除

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", {
            "status": 0 if status == 0 else 1
        })

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
    except:
        PrintEXC()
        return -1, "error"

async def OnUsrGetRoomByAuthCode(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid"))
        token = int(r.get_argument("token"))
        pwd = r.get_argument("pwd")

        rp = RDSPGuard.RP("game")
        account_res = await rp.LibGrd.AsyncCall("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0:
            return -1, "error"
        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])
        auth_token = 0 if len(account_res) < 4 else int(account_res[3].decode())
        if token == 0 or token != auth_token:
            return -4, "invalid token"

        rsp = MyResponse.Create()
        rsp.OK()

        server_res = await rp.AsyncHelper.Exec("HGET", "sha@roompwd", pwd)
        if server_res is not None:
            rsp.Add("data", json.loads(server_res.decode()))
        else:
            return 2, "room not exist"

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnUserGetScore(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid"))
        token = int(r.get_argument("token"))

        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0:
            return -1, "error"
        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])
        auth_token = 0 if len(account_res) < 4 else int(account_res[3].decode())
        if token == 0 or token != auth_token:
            return -4, "invalid token"

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", {
            "uuid" : account_base.uuid,
            "score" : account_base.score
        })

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

def _user_translate_for_tester(op, account_base, balance, uuid, rp, r):
    """處理測試人員轉錢流程

    根據 op 的值做不同的處理
    回傳 api 結果
    """
    if op == 'out':
        account_base.score += balance
        score = account_base.score

    elif op == 'in':
        account_base.score -= balance
        account_base.txn_id = "0"
        score = balance

    rsp = MyResponse.Create()
    rsp.OK()
    rsp.Add("data", {
        "uuid": uuid,
        "score": score,
        "balance": balance
    })
    account_buffer = account_base.SerializeToString()
    rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

    # check score
    account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
    account_base.ParseFromString(account_res[1])
    Warn("--- _user_translate_for_tester check, member_id=", account_base.sdk_uuid, " score=",
         account_base.score)

    r.add_header("Access-Control-Allow-Origin", "*")
    r.write(json.dumps(rsp.Data))
    r.flush()
    r.finish()

def _delete_fake_data_from_ps_db(account_base):
    """刪除 PS DB accounting 表內假的資料

    沒有走完正常的流程要刪除資料表資料 & 玩家 base
    玩家離開遊戲的話會是 call 這邊的 API，所以這邊也要做 sn 的刪除處理
    """
    rp = RDSPGuard.RP("game")
    multi_inf = rp.LibGrd.R.hget("multi@inf_" + account_base.channel, account_base.sin_channel)
    multi_inf = json.loads(multi_inf)
    sqlp = MYPGuard.MYP(multi_inf["db_id"])
    sql = sSqls["delete_ps_db_accounting"]
    result = sqlp.Exec(sql=sql.GetSQL(params={"sn": account_base.sn}))

    account_base.sn = 0
    UserRP.set_account_base(account_base)

async def OnUserTranslate(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid"))
        op = str(r.get_argument("op"))
        balance = int(r.get_argument("money"))  #单位分
        token = int(r.get_argument("token"))

        cantrans = 1
        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0:
            return -1, "error"

        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])

        # 測試人員跳過 API 直接回傳
        if account_base.user_type == 999:
            _user_translate_for_tester(op, account_base, balance, uuid, rp, r)
            return 0, "success"

        # 錢包類型
        chl_resp = rp.LibGrd.Call("channel.GetInfo", *(account_base.channel,))
        multi_inf = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + account_base.channel, account_base.sin_channel)
        multi_inf = json.loads(multi_inf)
        wallet_type = 0
        if "host_url" in multi_inf.keys():
            wallet_type = 1
        # if chl_resp[0] == 0:
        #     tmp = OnRedisResultParser(chl_resp[1])
        #     host_name = tmp["name"]
        #     multihost = json.loads(tmp["extra"])["multihost"]
        #     wallet_type = json.loads(tmp["extra"])["wallet_type"]

        # Log("---OnUserTranslate Enter score=", account_base.score, ", balance=", balance)
        if len(account_res[2].decode()) > 0:
            return -2, "is gaming"
        if token == 0 or token != int(account_res[3].decode()):
            return -4, "invalid token"
        if balance <= 0:
            return -5, "invalid money"
        timeStamp = GetServerTimeStr()
        response = {}
        if op == "in":      #游戏转到PS(人員不再lock名單中)
            if wallet_type == 1:  # 共享錢包
                sn = account_base.sn
                _delete_fake_data_from_ps_db(account_base)
                txn_id = account_base.txn_id
                host_url = multi_inf["host_url"]
                dl_url = host_url["base_url"] + "/" + host_url["refundbet"]
                err_msg = ", memberid: " + str(account_base.sdk_uuid)
                data = {"txn": txn_id, "host": account_base.sin_channel, "type": 2, "action": 3,
                        "err_code": 1, "err_descr": "response error" + err_msg, "time": GetServerTimeStr()}
                TradeLog("add_hosterrlog", data)
                response = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode(), "txn_id": sn})
                TradeLog("delete_hosterrlog", data)
                if response == None:
                    err_msg = ", memberid: " + str(account_base.sdk_uuid)
                    data = {"txn": txn_id, "host": account_base.sin_channel, "type": 2, "action": 3,
                            "err_code": 4,
                            "err_descr": "results == None, " + err_msg,
                            "time": GetServerTimeStr()}
                    TradeLog("add_hosterrlog", data)
                    Warn("--- OnUserTranslate (op=in share) Game to PS Failed member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ", balance, " response=None")

                    return -5, "error"
                elif response["status_code"] != 0:
                    data = {"txn": txn_id, "host": account_base.sin_channel, "type": 2, "action": 3,
                            "err_code": 4,
                            "err_descr": "response_status_code: " + str(response["status_code"]) + err_msg,
                            "time": GetServerTimeStr()}
                    TradeLog("add_hosterrlog", data)
                    Warn("--- OnUserTranslate (op=in share) Game to PS Failed member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ", balance, " status_code=", response["status_code"])
                    return response["status_code"], ""

                Warn("--- OnUserTranslate (op=in share) Game to PS member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ", balance)
                # if multihost == 0:
                account_base.score -= balance
                account_base.txn_id = "0"
                account_buffer = account_base.SerializeToString()
                rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

                # check score
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                account_base.ParseFromString(account_res[1])
                Warn("--- OnUserTranslate check, member_id=", account_base.sdk_uuid, " score=",
                     account_base.score)
            else:  # 獨立錢包
                _delete_fake_data_from_ps_db(account_base)
                txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                rp2 = RDSPGuard.RP("tradelist")
                SETNX_ret = await rp2.AsyncHelper.Exec("SETNX", "list@trade_" + str(uuid), txn_id)
                if SETNX_ret:
                    await rp2.AsyncHelper.Exec("EXPIRE", "list@trade_" + str(uuid), 240)  # 設定4分鐘
                if balance > account_base.score and account_base.score >= 0:
                    await rp2.AsyncHelper.Exec("DEL", "list@trade_" + str(uuid))  # 刪除人員名單及時間戳
                    return -3, "not enough money"
                rollin = await rp2.AsyncHelper.Exec("get", "list@trade_" + str(uuid))
                if rollin is not None and str(json.loads(rollin)) != txn_id:
                    return -1, "txn_id error"
                # pre-borrowed balance to redis, fixed the online problem by Leo.
                Warn("--- OnUserTranslate (op=in independent) Game to PS member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ",balance)
                # if multihost == 0:
                account_base.score -= balance
                account_base.txn_id = "0"
                account_buffer = account_base.SerializeToString()
                rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

                # check score
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                account_base.ParseFromString(account_res[1])
                Warn("--- OnUserTranslate check, member_id=", account_base.sdk_uuid, " score=",
                     account_base.score)

                # 二轉玩家判斷
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

                        has_result = len(result) != 0

                        dtm = result[0].get("dtm", "null") if has_result else ""
                        type = result[0].get("type", "null")  if has_result else ""
                        amount = result[0].get("amount", "null")  if has_result else ""

                        warning_msg = "--- OnUserTranslate (op=in independent) trade error"
                        warning_msg += f" member_id: {account_base.sdk_uuid}"
                        warning_msg += f" type: {type}"
                        warning_msg += f" amount: {amount}"
                        warning_msg += f" dtm: {dtm}"

                        Warn(warning_msg)

                if cantrans == 1:
                    # 交易錯誤日志
                    data = {"txn": txn_id, "host": account_base.sin_channel, "type": 0 if op == "in" else 1,
                            "memberid": account_base.sdk_uuid,
                            "amount": balance, "time": timeStamp, "end": 0}
                    TradeLog("add_tradeerrlog", data)
                    # request to ps server
                    # url = r.application.settings["ps_urls"]["rollin"]
                    # response = await r.application.AsyncGuard.DoAsync(RequestHelper.ReqRollIn, url, account_base.channel,
                    #                                                      account_base.sdk_uuid, txn_id, balance)
                    #
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

                    Log("===def OnUserTranslate post rollin response={} member_id={}".format(response, account_base.sdk_uuid))
                    # if response == None or response["status_code"] != 0:
                    #     # if fail then reback the balance
                    #     account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                    #     account_base.ParseFromString(account_res[1])
                    #     Warn("--- OnUserTranslate Game to PS Fail member_id=", account_base.sdk_uuid, " score=", account_base.score, " + ", balance, " response=", response)
                    #     account_base.score += balance
                    #     account_buffer = account_base.SerializeToString()
                    #     rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))
                    #     return response["status_code"], ""

                    # 刪除交易錯誤日志
                    TradeLog("delete_tradeerrlog", data)

                    await rp2.AsyncHelper.Exec("DEL", "list@trade_" + str(uuid))  #刪除人員名單及時間戳
        elif op == "out":   #PS转到游戏
            txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
            # url = r.application.settings["ps_urls"]["rollout"]
            # response = await r.application.AsyncGuard.DoAsync(RequestHelper.ReqRollOut, url, account_base.channel,
            #                                                      account_base.sdk_uuid, txn_id, balance)
            # response = json.loads(response)
            # if response["status_code"] != 0:
            #     Warn("--- OnUserTranslate (op=out) PS to Game Failed member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ", balance, " status_code=", response["status_code"])
            #     return response["status_code"], ""

            parameters = {
                "amount": balance,
                "host_id": multi_inf["host_id"],
                "id": account_base.sdk_uuid
            }
            sqlp = MYPGuard.MYP(multi_inf["db_id"])
            sql = sSqls["update_rollout_member"]
            result = await sqlp.AsyncExec(sql=sql.GetSQL(params=parameters))

            parameters = {
                "txn_id": txn_id,
                "type": 1,
                "host_id": multi_inf["host_id"],
                "member_id": account_base.sdk_uuid,
                "amount": balance,
                "note": "RollOut",
                "id": account_base.sdk_uuid
            }
            sql = sSqls["insert_funds_log"]
            result = await sqlp.AsyncExec(sql=sql.GetSQL(params=parameters))  # 寫入fundslog
            response = {}
            response["status_code"] = 0  # 成功後response = 0

            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            account_base.ParseFromString(account_res[1])
            Warn("--- OnUserTranslate (op=out) PS to Game member_id=", account_base.sdk_uuid, " score=", account_base.score, " - ", balance)
            account_base.score += balance
            account_buffer = account_base.SerializeToString()
            rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

            # check score
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            account_base.ParseFromString(account_res[1])
            Warn("--- OnUserTranslate check, member_id=", account_base.sdk_uuid, " score=",
                 account_base.score)
        if cantrans == 1:
            # 交易日志
            Log("===write sql memberid={}".format(account_base.sdk_uuid))
            data = {"txn": txn_id, "host": account_base.sin_channel, "type": 0 if op == "in" else 1,
                    "memberid": account_base.sdk_uuid, "amount": balance, "time": timeStamp}
            if wallet_type:
                TradeLog("add_sharingtradelog", data)
            else:
                TradeLog("add_tradelog", data)

            Log("===end sql memberid={}".format(account_base.sdk_uuid))
        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", {
            "uuid" : uuid,
            "score" : account_base.score,
            "balance" : 0 if "balance" not in response else response["balance"]
        })

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

def TradeLog(type, data):
    try:
        sqlp = MYPGuard.MYP("log")
        sql = sSqls[type]
        sqlp.Exec(sql=sql.GetSQL(params=data), callback=None)
    except:
        PrintEXC()

# def SecondaryRecharge(data):
#     try:
#         # sqlp = MYPGuard.MYP("log")
#         # sql = sSqls["secondary_recharge"]
#         # hint = {}
#         # result = sqlp.Exec(sql=sql.GetSQL(params=data), hint = hint, callback=None)
#         sMainSQL = '''SELECT * FROM `dmgamelog`.`game_trade_log` WHERE `member_id` = '%(memberid)s' ORDER BY dtm DESC LIMIT 1;;'''
#         sql = sMainSQL % data
#         print("111111111111111111", sql)
#         result = MYPGuard.MYP("log").Exec(sql=sql, callback=None)
#         print("111111111111111111", result)
#         # sMainSQL = '''SELECT `json_options` FROM `dmgame`.`cfg_gameroominfo` WHERE `host_api_key`= '%(host_api_key)s' AND `subgame_id`= '%(subgameid)s';;'''
#         # hints = {}
#         # sql = sMainSQL % {"host_api_key": host_api_key, "subgameid": serv_data.subgame_id}
#         # resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
#         if result == None:
#             return 0
#         else:
#             return result
#     except:
#         PrintEXC()

async def OnUserGetFaceID(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid"))
        token = int(r.get_argument("token"))
        faceid = None

        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0:
            return -1, "error account"
        if len(account_res[2].decode()) > 0:
            return -2, "gaming"
        if token != int(account_res[3].decode()):
            return -4, "failed token"

        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])
        if account_base.faceid != faceid:
            # idrange = r.application.settings["faceid"]
            # if faceid < idrange[0] or faceid > idrange[1]:
            #     return -3, "faceid invalid"
            account_base.faceid = account_base.faceid
            account_buffer = account_base.SerializeToString()
            rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", {
            "faceid": account_base.faceid,
            "curheadframe": account_base.frame,
            "curtitle": account_base.designation,
            "pokertype": account_base.card_style
        })
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnUserGetInfo(r)->(int, str):
    """取得玩家目前頭像與稱號"""
    try:
        uuid = int(r.get_argument("uuid",  default=None))

        if uuid == None:
            return 13, "uuid is none"

        account_base = UserRP.get_account_base(uuid)

        if not account_base:
            return -1, "error account"

        data = {
                "CurHeadFrame": account_base.frame,
                "CurTitle": account_base.designation,
                "pokerType": account_base.card_style,
                "MemberLv": account_base.lv,
                "FaceMemberLockLv": ServerMYP.face_member_lock_lv_list
        }

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", data)

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnUserGetNewItemFlag(r)->(int, str):
    """取得玩家是否有新道具的 Flag"""
    try:
        uuid = int(r.get_argument("uuid",  default=None))

        if uuid == None:
            return 13, "uuid is none"

        data = {
            "newitem": UserRP.get_new_item_flag(uuid)
        }

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", data)

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnUserGetUserReward(r)->(int, str):
    """取得玩家抽獎中獎資訊"""
    try:
        uuid = int(r.get_argument("uuid",  default=None))

        if uuid == None:
            return 13, "uuid is none"

        evnet_dc = EventRP.get_event_data(uuid)
        bonus = evnet_dc.get("bonus", 0)
        has_show_bonus = evnet_dc.get("has_show_bonus", 0)

        if bonus != 0 and not has_show_bonus:
            EventRP.set_shown_bonus(uuid)

        data = {
            "score": 0 if has_show_bonus else bonus
        }

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", data)

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnSetFaceID(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid"))
        token = int(r.get_argument("token"))
        faceid = int(r.get_argument("faceid"))
        curheadframe = r.get_argument("curheadframe", None)
        curtitle = r.get_argument("curtitle", None)
        pokertype = r.get_argument("pokertype", None)

        curheadframe = int(curheadframe) if curheadframe else curheadframe
        curtitle = int(curtitle) if curtitle else curtitle
        pokertype = int(pokertype) if pokertype else pokertype

        save_flag = 0

        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0:
            return -1, "error account"
        if len(account_res[2].decode()) > 0:
            return -2, "gaming"
        if token != int(account_res[3].decode()):
            return -4, "failed token"

        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])
        if account_base.faceid != faceid:
            idrange = r.application.settings["faceid"]
            if faceid < idrange[0] or (faceid > idrange[1] and faceid < 100):
                return -3, "faceid invalid"

            save_flag = 1
            account_base.faceid = faceid

        if account_base.frame != curheadframe and curheadframe is not None:
            idrange = r.application.settings["frame_id"]
            if curheadframe < idrange[0] or curheadframe > idrange[1]:
                return -3, "frame invalid"
            save_flag = 1
            account_base.frame = curheadframe

        if account_base.designation != curtitle and curtitle is not None:
            idrange = r.application.settings["designation_id"]
            if curtitle < idrange[0] or curtitle > idrange[1]:
                return -3, "designation invalid"
            save_flag = 1
            account_base.designation = curtitle

        if account_base.card_style != pokertype  and pokertype is not None:
            idrange = r.application.settings["card_style_id"]
            if pokertype < idrange[0] or pokertype > idrange[1]:
                return -3, "card_style invalid"
            save_flag = 1
            account_base.card_style = pokertype

        if save_flag:
            account_buffer = account_base.SerializeToString()
            rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

        # # 查詢多代理商開關
        # multi_host = 0
        # rp = RDSPGuard.RP("game")
        # channel_res = rp.LibGrd.Call("channel.GetInfo", *(account_base.channel,))
        # if channel_res[0] == 0:
        #     chl_data = OnRedisResultParser(channel_res[1])
        #     ctm_data = json.loads(chl_data["extra"])
        #     if "multihost" in ctm_data:
        #         multi_host = ctm_data["multihost"]

        # if multi_host == 1:
        #     # 多代理商路徑
        #     sync_url = r.application.settings["multihost"]["service"] + "/syncbase"
        #     # 同步至多代理商
        #     await r.application.AsyncGuard.DoAsync(RequestHelper.ReqSyncBase, sync_url,
        #                                            account_base.hostuuid, account_base.faceid, account_base.frame,
        #                                            account_base.designation, account_base.card_style, False)

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", {
            "uuid" : uuid,
            "faceid" : faceid,
            "curheadframe": account_base.frame,
            "curtitle": account_base.designation,
            "pokertype": account_base.card_style
        })

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnPing(r)->(int, str):
    try:
        try:
            uuid = int(r.get_argument("uuid", 0))

            # 是否維護
            rp = RDSPGuard.RP("game")
            is_maintain = False
            results = await rp.LibGrd.AsyncCall("common.GetInfoBySYS", *(uuid,))
            # 試玩桌因為access token網址拿掉，進入，沒有redis資訊，所以無資訊必須避開維護
            if results != None and results[0] == 0 and results[1] != None:
                account_base = db_data_user()
                account_base.ParseFromString(results[1])
                rp2 = RDSPGuard.RP("gamelist")
                # 單代理商向var@maintain_取得本代理商在多代理商的狀態
                host_maintain = rp2.LibGrd.R.get("var@maintain_" + account_base.channel)
                if host_maintain:  # 如果狀態是維護
                    is_maintain = True
                if account_base.banned == 1:  # banned
                    is_maintain = True
                channel_res = await rp.LibGrd.AsyncCall("channel.GetInfo", *(account_base.channel,))
                if channel_res[0] == 0:
                    chl_data = OnRedisResultParser(channel_res[1])
                    ctm_data = json.loads(chl_data["extra"])
                    if "status" in ctm_data:
                        status = ctm_data["status"]
                        if status == 1:  # 維護
                            is_maintain = True

            if uuid > 0 and is_maintain == False:
                RDSPGuard.RP("game").LibGrd.Call("common.OnKeepAlive", *(uuid, GetServerTime(), 0))
        except:
            pass

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", {})

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        return -1, "ok"

def tidy_all_the_prize(prize, conv):
    for i in prize:
        lottery = {
            "tid": 999,
            "nid": 9999,
            "type": 3,
            "args": [
                "9999",
                "99",
                "99999",
                "99"
            ],
            "lottery": {"member_id": i["member_id"], "bonus": i["bonus"]}
        }
        conv.append(lottery)
    return conv

async def OnUserGetNotices(r)->(int, str):
    try:
        uuid = r.get_argument("uuid", default=0)
        if isinstance(uuid, int) == False:
            return -1, "ok"

        uuid = int(uuid)
        if uuid == 0:
            return -1, "ok"

        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0 or account_res[1] is None:
            return -1, "error"
        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])

        host_api_key = account_base.channel
        channel_res = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
        if channel_res[0] != 0:
            return -1, "error"

        # 取得各個活動檔期的日期時間點
        date_dict = await rp.AsyncHelper.Exec("HGET", "sha@chl_" + host_api_key, "date")
        conv = []  # 最後要給前端的跑馬燈
        if date_dict != None:
            date_list = json.loads(date_dict)  # 反序列化

        # 如果潑水節活動下架或者活動還沒開始
        if date_dict == None or int(time.time()) >= date_list["discontinued"] or int(time.time()) < date_list["songkran_start"]:
            rp2 = RDSPGuard.RP("gamelist")
            notices = await rp2.AsyncHelper.Exec("LRANGE", "list@notice_" + host_api_key, 0, -1)

            for n in notices:
                try:
                    noti_data = json.loads(n.decode())
                    conv.append(noti_data)
                except:
                    PrintEXC()

        # 如果第三週跑馬燈活動已經開始，且活動結束但活動還沒下架
        elif int(time.time()) >= date_list["songkran_end"] and int(time.time()) <= date_list["discontinued"]:
            rp = RDSPGuard.RP("game")
            # 取得獎項名單
            first_prize = await rp.AsyncHelper.Exec("HGET", "first@notice_" + host_api_key, "ledmul")
            second_prize = await rp.AsyncHelper.Exec("HGET", "second@notice_" + host_api_key, "ledmul")
            special_prize = await rp.AsyncHelper.Exec("HGET", "special@notice_" + host_api_key, "ledmul")

            first_prize = json.loads(first_prize.decode())
            second_prize = json.loads(second_prize.decode())
            special_prize = json.loads(special_prize.decode())

            conv = tidy_all_the_prize(first_prize, conv)  # 一獎取全部

            second_prize = random.sample(second_prize, 5)  # 二獎隨機取5個
            conv = tidy_all_the_prize(second_prize, conv)

            special_prize = random.sample(special_prize, 20)  # 加碼獎隨機取20個
            conv = tidy_all_the_prize(special_prize, conv)

        # 如果第一週或第二週中獎活動已經開始，且未達第三週中獎活動
        elif int(time.time()) >= date_list["first_week_start"] and int(time.time()) <= date_list["songkran_end"]:
            rp = RDSPGuard.RP("game")
            # 取得獎項名單
            first_prize = await rp.AsyncHelper.Exec("HGET", "first@notice_" + host_api_key, "ledmul")
            second_prize = await rp.AsyncHelper.Exec("HGET", "second@notice_" + host_api_key, "ledmul")

            first_prize = json.loads(first_prize.decode())
            second_prize = json.loads(second_prize.decode())

            conv = tidy_all_the_prize(first_prize, conv)  # 一獎取全部

            second_prize = random.sample(second_prize, 25)  # 二獎隨機取25個
            conv = tidy_all_the_prize(second_prize, conv)

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("notice", conv)
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "ok"

def OnGetUserGameRecord(hint, results):
    hint["results"] = results

async def OnUserGetGameRecord(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid"))
        token = int(r.get_argument("token"))
        query_page = int(r.get_argument("page"))  # 第N頁
        query_count = int(r.get_argument("count"))  # 每頁顯示數量
        query_time = str(r.get_argument("time"))  # 玩家所在時區的小日曆日期
        gmt = int(r.get_argument("gmt", default=0))  # 玩家所在國家的時區，預設為倫敦時間+0

        if query_page < 0 or query_count <= 0 \
                or ((query_page+1) * query_count) > 500:
            return -1, "(query_page * query_count) out of range"

        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0 or account_res[1] is None:
            return -1, "error"
        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])
        if int(account_res[3].decode()) != token:
            return -4, "failed token"

        #sMainSQL = '''SELECT `JsonData` AS `jd` FROM `data_gamerecord` WHERE `UUID` = %(uuid)d;;
        #hints = {}
        #sql = sMainSQL % {"uuid":uuid}
        #MYPGuard.MYP("game").Exec(sql=sql, hint=hints, callback=OnGetUserGameRecord)
        #runtime = GetServerTime()
        #while "results" not in hints:
        #    if GetServerTime() - runtime >= 5:  # 3秒超时时间
        #        return -5
        #    await asyncio.sleep(0.02)
        # data = "[]" if len(results) == 0 else results[0]["jd"]

        medium_time = int(time.mktime(time.strptime(query_time, "%Y-%m-%d")))  # 指定日期的午夜0點0分0秒
        start_time = medium_time - gmt * 3600  # 搜尋起始時間，當地時間00:00:00 - 時區
        end_time = medium_time + 86399 - gmt * 3600  # 搜尋結束時間，當地時間23:59:59 - 時區

        result_count = 0
        if query_page == 0:
            sMainSQL = '''SELECT COUNT(*) AS count FROM (SELECT gp.vSubGameID FROM `game_play_log` AS gp 
            INNER JOIN `game_table_log` AS gt ON gp.vRoundID=gt.vRoundID AND gp.vUUID=%(uuid)d 
            AND UNIX_TIMESTAMP(gp.vTime) BETWEEN %(start_time)d AND %(end_time)d LIMIT 500) AS a;;'''
            hints = {}
            sql = sMainSQL % {"uuid": uuid, "start_time": start_time,"end_time": end_time}
            MYPGuard.MYP("log").Exec(sql=sql, hint=hints, callback=OnGetUserGameRecord)
            runtime = GetServerTime()
            while "results" not in hints:
                if GetServerTime() - runtime >= 5:  # 3秒超时时间
                    return -5, "time out 11"
                await asyncio.sleep(0.02)
            query_result = hints["results"]
            result_count = int(query_result[0]["count"])

        #查询记录
        sMainSQL = '''SELECT gp.vSubGameID, gp.vRoundID, gp.vChairID, gp.vTime, gt.Log FROM `game_play_log` AS gp 
                      INNER JOIN `game_table_log` AS gt ON gp.vRoundID=gt.vRoundID AND gp.vUUID=%(uuid)d 
                      AND UNIX_TIMESTAMP(gp.vTime) BETWEEN %(start_time)d AND %(end_time)d ORDER BY gp.vTime DESC 
                      LIMIT %(start_index)d, %(count)d;;'''
        hints = {}
        sql = sMainSQL % {"uuid": uuid,
                          "start_time" : start_time,
                          "end_time" : end_time,
                          "start_index" : query_page * query_count,
                          "count" : query_count}
        MYPGuard.MYP("log").Exec(sql=sql, hint=hints, callback=OnGetUserGameRecord)
        runtime = GetServerTime()
        while "results" not in hints:
            if GetServerTime() - runtime >= 5:  # 3秒超时时间
                return -5, "time out"
            await asyncio.sleep(0.02)

        rsp = MyResponse.Create()
        rsp.OK()

        data = []
        query_result = hints["results"]
        for result in query_result:
            json_data = json.loads(result["Log"])
            res_data = json_data["detail"]
            res_data["rs"] = json_data["roundid"]
            # 從utc+0轉換成所在國家的時區日期時間，回傳至放大鏡紀錄
            res_data["t"] = (result["vTime"] + datetime.timedelta(hours=gmt)).strftime('%Y-%m-%d %H:%M:%S')
            res_data["sidx"] = result["vChairID"]
            data.append(res_data)

        query_data = { "data" : data, "page" : query_page}
        if query_page == 0:
            query_data["total"] = result_count
        rsp.Add("data", query_data)

        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "error"

async def OnMoniGetSrvList(r)->(int, str):
    try:
        verification = r.get_argument("verification")
        if verification != "A265781E11C782D84E5D0FC9EBB4941C":
            return -1, "failed"

        rsp = MyResponse.Create()
        rsp.OK()

        servers = []
        mSvrLists = ServListMgr.mSvrLists
        for serveruid, serverdata in mSvrLists.items():
            servers.append({
                "svruid" : serveruid.decode(),
                "host_api_key" : serverdata.host_api_key.decode(),
                "subgame_id" : serverdata.subgame_id,
                "server_addr" : serverdata.server_addr.decode(),
                "server_port" : serverdata.server_port,
                "server_type" : serverdata.server_type,
                "cell_score" : serverdata.cell_score,
                "admission_score" : serverdata.admission_score,
            })
        rsp.Add("data", servers)
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        return -1, "failed"

async def OnUsrGetLaunchInfo(r)->(int, str):
    try:
        uuid = r.get_argument("id")

        if uuid is None:
            return -1, "id failed"

        svr_id = -1
        rp = RDSPGuard.RP("game")
        svr_uuid = await rp.AsyncHelper.Exec("HGET", "sha@data_" + uuid, "svr_id")

        '''
        # multi_host = 0
        rp = RDSPGuard.RP("game")
        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
        if account_res[0] != 0 or account_res[1] is None:
            return -1, "error"
        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])

        host_api_key = account_base.channel
        channel_res = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
        if channel_res[0] == 0:
            chl_data = OnRedisResultParser(channel_res[1])
            ctm_data = json.loads(chl_data["extra"])
            if "multihost" in ctm_data:
                multi_host = ctm_data["multihost"]
        '''

        if svr_uuid is not None:
            # if multi_host == 1:
            #     url = r.application.settings["multihost"]["service"] + "/serverlist"
            #     resp = await r.application.AsyncGuard.DoAsync(RequestHelper.ReqMultiServerList, url, account_base.hostuuid)
            #     svr_id = eval(resp)["svr_id"]
            # else:
            rplst = RDSPGuard.RP("gamelist")
            server_list_db = rplst.LibGrd.R.get("var@serverlist")
            server_list = get_game_server_list_ret()
            if server_list_db is not None and len(server_list_db) > 0:
                server_list.ParseFromString(server_list_db)
                for idx in range(len(server_list.gslist)):
                    # 走訪取得遊戲內的uuid，若與被踢除的玩家吻合
                    if server_list.gslist[idx].server_uuid == svr_uuid:
                        # svr_id = -1，不在遊戲中；svr_id = 0~5，正在遊戲桌
                        svr_id = server_list.gslist[idx].subgame_id

        rsp = MyResponse.Create()
        rsp.OK()

        data = {
            "svr_id": svr_id
        }
        rsp.Add("data", data)
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "failed"

def _get_day_interval_and_nowtime(login_time):
    """取得玩家登入天數差距

    Args:
        login_time (int): 時間戳

    Returns:
        int: 天數差距
        int: 現在時間戳
    """

    tz = datetime.timezone(datetime.timedelta(hours=+7))

    nowtime = datetime.datetime.now(tz)
    lastlogintime = datetime.datetime.fromtimestamp(login_time).astimezone(tz)  # int to datetime

    # 去掉時間，用日期做天數計算
    nowtime_date = datetime.datetime(nowtime.year, nowtime.month, nowtime.day)
    lastlogintime_date = datetime.datetime(lastlogintime.year, lastlogintime.month, lastlogintime.day)

    return (nowtime_date - lastlogintime_date).days, nowtime

def _get_multi_host_info(uuid):
    multi_host = 0  # 預設為單代理商
    hostuuid = None  # 預設單代理商沒有hostuuid
    # 查詢redis account base
    rp = RDSPGuard.RP("game")
    account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
    if account_res[0] == 0:
        account_base = db_data_user()
        account_base.ParseFromString(account_res[1])
        hostuuid = account_base.hostuuid  # 取得多代理商uuid
        host_api_key = account_base.channel  # 取得商戶代號

        # 查詢多代理商開關
        channel_res = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
        if channel_res[0] == 0:
            chl_data = OnRedisResultParser(channel_res[1])
            ctm_data = json.loads(chl_data["extra"])
            if "multihost" in ctm_data:
                multi_host = ctm_data["multihost"]  # 多代理商開啟或關閉

    return multi_host, hostuuid

async def OnEventLoginReward(r)->(int, str):
    """每日登入獎勵計算

    確認玩家是否連續登入，並將值回傳給前端
    若有修正，要檢查 HDRDoCompensate
    """
    try:
        uuid = int(r.get_argument("uuid", default=None))  # 玩家uuid

        if uuid == None:
            return 13, "uuid is none"

        login_data = EventRP.get_login_data(uuid)  # 獲取玩家登入活動所需資料

        if login_data == None:
            return 14, "login_data is none"

        # 取得玩家redis base
        account_base = UserRP.get_account_base(uuid)

        if account_base == None:
            return 15, "account_base is none"

        # 取得商戶redis date活動時程
        rp = RDSPGuard.RP("game")
        date_redis = rp.LibGrd.R.hget("sha@chl_" + str(account_base.channel), "date")
        if date_redis == None:
            return 16, "date_redis is none"

        multi_host, hostuuid = _get_multi_host_info(uuid)
        day_interval, nowtime = _get_day_interval_and_nowtime(login_data["login_time"])

        if day_interval != 0 and login_data["reset_point_in_game"] != 1:  # 重置每日獲得點數
            EventRP.set_login_during_event(uuid)
            EventRP.reset_daily_point(uuid)

            # if multi_host == 1:  # 同步重製水球到多代理
            #     # 多代理商路徑
            #     sync_url = r.application.settings["multihost"]["service"] + "/syncevent"
            #     post_data = {"daily_point": 0}

            #     await r.application.AsyncGuard.DoAsync(
            #         RequestHelper.ReqSyncEvent, sync_url,
            #         hostuuid, post_data)

        login_day = login_data["continue_login_day"]  # 預設要回傳的連續登入天數

        # 確認活動結束時，不再計算連續登入
        date_redis = json.loads(date_redis.decode())
        songkran_start = date_redis["songkran_start"]
        songkran_end = date_redis["songkran_end"]
        if songkran_start <= int(time.time()) and songkran_end >= int(time.time()):
            login_timestamp = int(datetime.datetime.timestamp(nowtime))

            # 若未收到過活動禮、不是當日重複登入
            if login_data["has_award"] != 1 and day_interval >= 1:
                is_continue = day_interval == 1

                # 連續登入就累加，不是的話就從第一天開始
                login_day = login_day + 1 if is_continue else 1
                has_award = 1 if login_day >= 5 else 0

                EventRP.update_login_data(uuid, login_timestamp, login_day, has_award)

                if has_award:
                    EventRP.add_event_item(uuid, 'photo', 200)
                    UserRP.set_new_item_flag(uuid, 1)

                # # 驗證是否需要同步
                # if multi_host == 1:
                #     # 多代理商路徑
                #     sync_url = r.application.settings["multihost"]["service"] + "/syncevent"
                #     post_data = {
                #             "login_time":login_timestamp,
                #             "login_day":login_day,
                #             "has_award":has_award
                #         }

                #     # 同步至多代理商
                #     await r.application.AsyncGuard.DoAsync(
                #         RequestHelper.ReqSyncEvent, sync_url,
                #         hostuuid, post_data)

            elif day_interval >= 1: # 領過禮物、不是重複登入，要刷新登入時間
                EventRP.update_login_data(uuid, login_timestamp, login_day, 1)

                # # 驗證是否需要同步
                # if multi_host == 1:
                #     # 多代理商路徑
                #     sync_url = r.application.settings["multihost"][
                #                    "service"] + "/syncevent"
                #     post_data = {
                #         "login_time": login_timestamp,
                #         "login_day": login_day,
                #         "has_award": 1
                #     }

                #     # 同步至多代理商
                #     await r.application.AsyncGuard.DoAsync(
                #         RequestHelper.ReqSyncEvent, sync_url,
                #         hostuuid, post_data)

        data = {
            # login_day 只會 + 到 5，若已領獎前端需要的值是 6
            "sign_days": 6 if login_data['has_award'] else login_day,
            "remain_point": EventRP.get_remain_point(uuid)
        }

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", data)
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "failed"

async def OnGetEventItem(r)->(int, str):  # 取得玩家目前擁有的活動道具
    try:
        uuid = int(r.get_argument("uuid", default=None))  # 玩家uuid

        if uuid == None:
            return 13, "uuid is none"

        # 取得玩家目前擁有的活動道具：頭像、頭框、稱號、撲克牌樣式
        event_item = EventRP.get_event_item(uuid)
        UserRP.set_new_item_flag(uuid, 0)

        if event_item == None:
            return 14, "event_item is none"

        data = event_item

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", data)
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "failed"

async def OnEventTaskInfo(r)->(int, str):
    try:
        uuid = int(r.get_argument("uuid", default=None))

        if uuid is None:
            return 13, "uuid is none"

        task_info = EventRP.get_task_info(uuid)

        if task_info == None:
            return 15, "no task info"

        rsp = MyResponse.Create()
        rsp.OK()

        data = task_info

        rsp.Add("data", data)
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "failed"

async def OnMemberGrade(r)->(int, str):  # 查詢玩家等級、遊玩次數、勝場數
    try:
        uuid = r.get_argument("uuid")  # 玩家uuid

        if uuid is None:  # 沒輸入報錯誤
            return 13, "uuid failed"

        upgrade_list = ServerMYP.upgrade_threshold_list

        account_base = UserRP.get_account_base(uuid)

        if account_base is None:
            return 15, "base is none"

        data = {
            "lv": account_base.lv,  # 等級
            "play_times": account_base.play_times,  # 生涯遊玩次數
            "all_win_times": account_base.all_win_times,  # 生涯勝場數
            "upgrade_needs_win": upgrade_list  # 所有等級所需勝場數門檻陣列
        }

        rsp = MyResponse.Create()
        rsp.OK()
        rsp.Add("data", data)
        r.add_header("Access-Control-Allow-Origin", "*")
        r.write(json.dumps(rsp.Data))
        r.flush()
        r.finish()
        return 0, "success"
    except:
        PrintEXC()
        return -1, "failed"

sExtrAction = {
    "faceid": OnSetFaceID,  # 網頁開啟前端送進頭像、頭框、稱號、卡牌樣式
    "ping": OnPing,
    "getnotices": OnUserGetNotices,
    "getbalance": OnUserGetBalance,
    "getbalancedetails": OnUserGetBalanceDetails,
    "trans": OnUserTranslate,
    "gamerecord": OnUserGetGameRecord,
    "getscore": OnUserGetScore,
    "queryroom": OnUsrGetRoomByAuthCode,
    "serverlist": OnMoniGetSrvList,
    "getlaunch": OnUsrGetLaunchInfo,
    "getface": OnUserGetFaceID,  # F5操作後端取得後台頭像
    "getuserinfo": OnUserGetInfo,  # 取得玩家目前頭像、頭框、稱號
    "getnewitem": OnUserGetNewItemFlag,  # 確認玩家是否有新道具
    "getuserreward": OnUserGetUserReward,  # 取得玩家抽獎中獎資訊與是否彈跳視窗過

    "getusereventdata": OnEventLoginReward,  # 潑水節每日登入獎勵
    "geteventitem": OnGetEventItem,  # 潑水節玩家目前擁有的活動道具
    "gettasklist": OnEventTaskInfo,  # 取得遊戲內任務紀錄

    "getmember": OnMemberGrade  # 玩家點擊頭像，看到會員等級制度
}

class HDRInputValueError(Exception):
    """如果 API 輸入的值錯誤了 用來跳出 try except 回傳 status_code"""
    pass

#提供给内部调用
class OnHandler(tornado.web.RequestHandler):
    async def get(self):
        rsp = None
        try:
            act = self.get_argument("action", default = None)
            if act in sExtrAction:
                error_code, error_str = await sExtrAction[act](self)
                if error_code is not 0:
                    rsp = MyResponse.Create()
                    rsp.Error(error_code, error_str)
            else:
                Warn("[OnHandler] action not match")
                rsp = MyResponse.Create()
                rsp.Except()
        except:
            PrintEXC()
            rsp = MyResponse.Create()
            rsp.Except()

        if rsp is not None:
            self.add_header("Access-Control-Allow-Origin", "*")
            self.write(json.dumps(rsp.Data))
            self.flush()
            self.finish()

####################
# 提供给外部的接口 #
####################

def token_credits_cash(user_type, serv_data):
    # 0~5廳：正常現金玩家；6~11廳：潛在信用玩家
    # 如果是正常現金玩家且走訪至6~11廳
    if user_type == 0 and serv_data.subgame_id >= 6 and serv_data.subgame_id <= 11:
        return False  # 則不存取此廳
    # 如果是潛在信用玩家且走訪至0~5廳
    if user_type == 1 and serv_data.subgame_id >= 0 and serv_data.subgame_id <= 5:
        return False  # 則不存取此廳
    return True  # 存取此廳

class MissingArgError(Exception):
    pass

class ReqHandlerWrapper(tornado.web.RequestHandler):
    def GetBodyArgument(self, key, **kwargs):
        if "req_data" not in self.__dict__:
            self.req_data = json.loads(self.request.body)
        if key not in self.req_data:
            if "default" in kwargs:
                return kwargs["default"]
            else:
                raise MissingArgError()
        else:
            return self.req_data[key]

class HDRRequestGame(ReqHandlerWrapper):
    def _get_cli_url(self, ctm_data, game_id):
        cli_url = ctm_data["dl_url"]
        if cli_url[-1] != '/':
            cli_url += '/'
        cli_url += game_id

        return cli_url

    def _get_gs_url(self, ctm_data):
        gs_url = ctm_data["gs_url"]
        if isinstance(gs_url, dict):
            if "CARD" in gs_url:
                gs_url = gs_url["CARD"]
        return gs_url

    # def _get_multi_host(self, channel_res):
    #     """取得是否啟動多代理服務

    #     Args:
    #         channel_res (list): 伺服器的資料

    #     Returns:
    #         int: 1 多代理，0 單代理
    #     """
    #     multi_host = 0

    #     if channel_res[0] == 0:
    #         chl_data = OnRedisResultParser(channel_res[1])
    #         ctm_data = json.loads(chl_data["extra"])
    #         if "multihost" in ctm_data:
    #             multi_host = ctm_data["multihost"]

    #     return multi_host

    def _get_svrid_and_serv_data(self, login_resp, host_api_key):
        """取得這兩筆資料

        Args:
            login_resp: 不清楚內容是什麼
            host_api_key: 不清楚內容是什麼

        Returns:
            last_svrid:

            last_serv_data:
        """
        last_svrid = -1
        last_serv_data = None
        svr_uuid = login_resp[1].decode()
        if len(svr_uuid) > 0:
            last_serv_data = ServListMgr.GetSvrByHostApiKey(host_api_key,
                                                            svr_uuid)
            if last_serv_data is not None:
                last_svrid = last_serv_data.subgame_id

        return last_svrid, last_serv_data

    def _get_encr_data(self, encode, data):
        """加密傳給前端的資料"""
        if encode > 0:
            encr_data = json.dumps(data).encode()  # XXTEncrypt.Encrypt(json.dumps(data))
        else:
            encr_data = XXTEncrypt.Encrypt(json.dumps(data))

        return encr_data

    async def _login_with_tester(self, host_api_key, game_id, rp):
        """以測試員身分登入，並回傳資料

        跟一般登入差別在於少了一些檢查的步驟
        名稱寫死 play_star_tester (在某些 game 邏輯判斷會使用到，若有修正要檢查，直接搜尋名稱)
        錢的部份寫入固定金額到 redis 中

        Args:
            host_api_key (str): 代理商的 api key
            game_id (str): 遊戲的 ID
            rp: 讀取 game redis 的物件

        Returns:
            dict: 玩家資料
        """
        uid = nam = 'play_star_tester'
        acc = host_api_key + "_" + uid # 為了區別在多代理商 redis 的名稱，多加了 api key

        Log("tester_acc={}".format(acc))
        acc_resp = await rp.LibGrd.AsyncCall("common.GenAcc", *(acc,))

        account_base = db_data_user()

        if acc_resp[1] == 1:  # 已有账号、登录
            account_base.ParseFromString(acc_resp[2])

            account_base.score = 0 # 預設金額
            account_base.lastlogintime = GetServerTime()
            account_base.game_id = game_id  # 將遊戲代號存取至redis base
            account_base.user_type = 999  # 設定身分為測試人員
            if not account_base.lv:  # 改版後第一次玩
                account_base.lv = 1  # 初始等級1
            account_buffer = account_base.SerializeToString()

            if len(EventRP.get_event_data(account_base.uuid)) == 0:
                self._set_default_event_data(account_base.uuid)

        elif acc_resp[1] == 2:  # 新建账号、登录
            account_base.uuid = int(acc_resp[2])
            account_base.game_id = game_id  # 將遊戲代號存取至redis base
            account_base.user_type = 999  # 設定身分為測試人員
            account_base.account = acc
            account_base.channel = host_api_key
            account_base.sdk_uuid = uid
            account_base.score = 0 # 預設金額
            account_base.banned = 0
            account_base.VIP = 0  # 新建帳號不會是vip，預設給0
            idrange = self.application.settings["faceid"]
            account_base.faceid = GetRndInt(idrange[0], idrange[1])
            account_base.bankscore = 0
            account_base.nickname = nam
            account_base.source = "PC"
            account_base.lv = 1  # 初始等級1
            account_base.jsondata = b"{}"
            account_base.lastlogintime = GetServerTime()
            account_base.regtime = account_base.lastlogintime
            account_buffer = account_base.SerializeToString()
            ret = await rp.LibGrd.AsyncCall("common.OnRegAcc", *(account_base.uuid, acc, account_buffer, host_api_key))

            self._set_default_event_data(account_base.uuid)

        new_token = GetRndInt(1000000, 9999999)
        login_resp = await rp.LibGrd.AsyncCall("common.OnLogin", *(account_base.uuid, account_buffer, new_token, acc, host_api_key))

        # # 同步token至多代理商redis的sha@data_
        # if multi_host == 1:  # 如果跨代理商開關啟動
        #     sync_url = self.application.settings["multihost"][
        #                    "service"] + "/synctoken"
        #     sync_token = await self.application.AsyncGuard.DoAsync(
        #         RequestHelper.ReqSyncToken,
        #         sync_url,
        #         account_base.hostuuid, new_token)

        # 添加ping
        await rp.LibGrd.AsyncCall("common.OnKeepAlive",
                                  *(account_base.uuid, GetServerTime(), 1))

        last_svrid, last_serv_data = self._get_svrid_and_serv_data(
            login_resp, host_api_key)

        return {
            "uuid": account_base.uuid,
            "game_id": account_base.game_id,
            "account": account_base.account,
            "nickname": account_base.nickname,
            "score": account_base.score,
            "banned": account_base.banned,
            "VIP": account_base.VIP,
            "token": new_token,
            "svrid": last_svrid,
            "faceid": account_base.faceid,
            "bankscore": account_base.bankscore,
            "sdk_uuid": account_base.sdk_uuid,
            "channel": account_base.channel,
            "source": account_base.source,
            "access_token": acc,
            "profit": account_base.profit,
            "dailyprofit": account_base.dailyprofit,
            "lastscoretime": account_base.lastscoretime,
            "regtime": account_base.regtime,
            "lastlogintime": account_base.lastlogintime,
            "jsondata": account_base.jsondata
        }

    async def _get_server_data_with_tester(self, host_api_key):
        """取得測試人員使用的 game server 資料

        跟一般登入差別在於一些檢查以及只會顯示現金桌子

        Args:
            host_api_key (str): 單代理商的 api key

        Returns:
            list: 桌子的設定資料
        """
        # if multi_host == 1:  # 跨代理商開關啟動：導入跨server
        #     url = self.application.settings["multihost"][
        #               "service"] + "/gameserverlist"
        #     multihost_host_api_key = self.application.settings["multihost"][
        #         "hostkey"]
        #     # 新增user_type導入HDRGameServerList，取得此類型玩家可進入的廳種
        #     response = await self.application.AsyncGuard.DoAsync(
        #         RequestHelper.ReqGetGameList, url,
        #         multihost_host_api_key, 0) # 取得一般現金廳

        #     rp2 = RDSPGuard.RP("gamelist")
        #     multi_cfg = await rp2.AsyncHelper.Exec("get",
        #                                            "multi@cfg_" + host_api_key)
        #     multi_cfg = int(multi_cfg) if multi_cfg else 0

        #     if multi_cfg == 1:
        #         servers = json.loads(response)["data"]
        #         Log(f"(multi) tester_room_result_a={servers}")

        #     else:
        #         same_count = 0  # 用來記錄房間參數相同的數量
        #         for subgame_id in range(len(json.loads(response)["data"])):
        #             url = self.application.settings["multihost"][
        #                       "service"] + "/getsvropt"
        #             multihost_game_id = self.application.settings["multihost"][
        #                 "game_id"]
        #             game_cfg = await self.application.AsyncGuard.DoAsync(
        #                 RequestHelper.ReqMultiHostSvropt,
        #                 url, multihost_host_api_key, multihost_game_id,
        #                 subgame_id)
        #             if 'data' not in json.loads(game_cfg):  # 防呆避免開桌目的是跳房號設定時，產生錯誤
        #                 continue  # 沒有此房就換下一房
        #             game_cfg = json.loads(game_cfg)['data']

        #             hash_key = GenHostApiHashKey(host_api_key, subgame_id)
        #             myp = MYPGuard.MYP("game")
        #             sql = sSqls["query_room"]
        #             query_results = await myp.AsyncExec(
        #                 sql.GetSQL({"hash_key": hash_key}))

        #             result = query_results[0]
        #             room_cfg = json.loads(result["json_options"])

        #             if game_cfg == room_cfg:
        #                 same_count += 1
        #                 await rp2.AsyncHelper.Exec("set",
        #                                            "multi@cfg_" + host_api_key,
        #                                            1)
        #             else:
        #                 await rp2.AsyncHelper.Exec("set",
        #                                            "multi@cfg_" + host_api_key,
        #                                            0)
        #                 break
        #         # 房間參數全都一樣，才給參數
        #         if same_count == len(json.loads(response)["data"]):
        #             servers = json.loads(response)["data"]
        #             Log(f"(multi) tester_room_result_b={servers}")
        #         else:
        #             servers = []
        #             Log(f"(multi) tester_room_result_c={servers}")

        # else:
        servers = []
        svr_list = ServListMgr.GetOptimalSvrByHostApiKey(host_api_key)
        Log("(single) tester_room_list={}".format(svr_list))
        for serv_data in svr_list:
            sMainSQL = '''SELECT `json_options` FROM `dmgame`.`cfg_gameroominfo` WHERE `host_api_key`= '%(host_api_key)s' AND `subgame_id`= '%(subgameid)s';;'''
            hints = {}
            sql = sMainSQL % {"host_api_key": host_api_key,
                                "subgameid": serv_data.subgame_id}
            resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql,
                                                            hint=hints,
                                                            callback=None)
            servinfo = {}
            servinfo["subgame_id"] = serv_data.subgame_id
            servinfo["server_type"] = serv_data.server_type
            servinfo["addr"] = serv_data.server_addr.decode()
            servinfo["port"] = serv_data.server_port
            servinfo["cell"] = serv_data.cell_score
            servinfo["adm_score"] = serv_data.admission_score
            servinfo["max_player"] = serv_data.max_player
            servinfo["cur_player"] = serv_data.cur_player
            servinfo["max_score"] = eval(resualt[0]['json_options'])['max_score']
            servers.append(servinfo)

            Log("(single) tester_room_result={}".format(servers))
        return servers

    async def _get_event_loading_data(self, host_api_key, game_id, lang):
        """Call GS DB API 拿loading圖相關資料"""
        get_host_game_info_url = self.application.settings["ps_urls"]["get_host_game_info"]

        host_game_info_dc = {
            "host_id": host_api_key,
            "game_id": game_id,
            "subgame_id": "0",  # 只需要請求一次，預設 0
            "lang": lang,
        }

        response = await self.application.AsyncGuard.DoAsync(
            RequestHelper.DoGet, get_host_game_info_url, host_game_info_dc
        )

        if response is None:
            return {}, []

        return response["host_image"], response["eventInfo"]

    def _set_default_event_data(self, uuid):
        """設定玩家預設活動資料"""
        event_dc = {
            "task": {
                "one_turn_dummy": 0,
                "dummy": 0,
                "lay_off": 0,
                "play_game": 0,
                "win_gold_card": 0
            },
            "total_point": 0,
            "daily_point": 0,
            "remain_point": 0,
            "continue_login_day": 0,
            "login_time": 0,
            "has_award": 0,
            "bonus": 0,
            "has_show_bonus": 0,
            "lottery_ticket": 0,
            "reset_point_in_game": 0,
            "bonus_timestamp": 0,
        }

        EventRP.update_event_data(uuid, event_dc)

    async def post(self):
        resp = {
            "status_code" : -1,
            "download_url" : ""
        }
        try:
            single_host_api_key = self.GetBodyArgument("single_host_api_key", default = "")
            host_api_key = self.GetBodyArgument("multi_host_api_key", default = "")
            game_id = self.GetBodyArgument("game_id", default = "")
            if len(single_host_api_key) == 0 or len(host_api_key) == 0 or len(game_id) == 0:
                Warn("launch by MissingArgError")
                return

            room_id = int(self.GetBodyArgument("room_id", default = 0))
            lang = self.GetBodyArgument("lang", default = "")
            access_token = self.GetBodyArgument("access_token", default = "")
            return_url = self.GetBodyArgument("return_url", default = "")
            return_target = self.GetBodyArgument("return_target", default = "")
            encode = int(self.GetBodyArgument("encode", default = 0))
            user_type = int(self.GetBodyArgument("user_type", default=0))  # 0正常現金玩家；1潛在信用玩家

            if access_token == "test mode":
                user_type = 999

            rp = RDSPGuard.RP("game")
            channel_res = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))

            # multi_host = self._get_multi_host(channel_res)

            multi_inf = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + host_api_key, single_host_api_key)
            if multi_inf is None:
                Warn("launch host_api_key=", host_api_key, ", single_host_api_key=", single_host_api_key)
                return

            multi_inf = json.loads(multi_inf)

            while True:
                if channel_res[0] != 0:
                    resp["status_code"] = 1
                    break

                cfg_resp = await rp.AsyncHelper.Exec("HGET", "sha@cfg_" + game_id, "data")
                if cfg_resp is None:
                    resp["status_code"] = 2
                    break

                cfg = json.loads(cfg_resp)
                if not cfg["enable"]:
                    Err("Game not enable!", game_id)
                    break

                chl_data = OnRedisResultParser(channel_res[1])
                ctm_data = json.loads(chl_data["extra"])

                status = ctm_data.get("status", 0)
                if status == 1:  # 維護
                    resp["status_code"] = 4
                    break

                cli_url = self._get_cli_url(ctm_data, game_id)
                gs_url = self._get_gs_url(ctm_data)

                wallet_type = 0
                if "host_url" in multi_inf.keys():
                    wallet_type = 1

                auto_trans = ctm_data["auto_trans"]
                # 新增組房功能：1開啟、0關閉，預設為關閉
                create_room_switch = ctm_data.get("create_room_switch", 0)
                # 新增語言切換功能：1開啟、0關閉，預設為開啟
                language_switch = ctm_data.get("language_switch", 1)
                # 抓取目前以小博大機制開關：結算是否計算以小博大，預設為1開啟
                global allow_leverage
                allow_leverage = ctm_data.get("allow_leverage", 1)
                data = {
                        "lang" : lang,
                        "r_url" : return_url,
                        "r_tar" : return_target,
                        "gs_url" : gs_url,
                        "trans" : auto_trans,
                        "create_room_switch" : create_room_switch,  # 新增組房功能：1開啟、0關閉
                        "language_switch": language_switch,  # 新增語言切換功能：1開啟、0關閉
                        "allow_leverage": allow_leverage,  # 抓取目前以小博大機制開關
                        "wallet_type": wallet_type,  # 錢包類型
                    }

                if user_type == 999: # 測試人員登入
                    data['pdata'] = await self._login_with_tester(host_api_key, game_id, rp)
                    data["servers"] = await self._get_server_data_with_tester(host_api_key)

                elif len(access_token) != 0:
                    url = multi_inf["ps_urls"]["login"]
                    response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqLoginVerify, url,
                                                                            single_host_api_key, access_token)
                    Log("RequestGameLoginVerify={}".format(response))

                    if response['status_code'] != 0:
                        resp["status_code"] = 3
                        break

                    uid = response["member_id"]
                    nam = response["member_name"]
                    acc = host_api_key + "_" + uid
                    Log("acc={}".format(acc))
                    acc_resp = await rp.LibGrd.AsyncCall("common.GenAcc", *(acc,))
                    if acc_resp[0] != 0:
                        Err("common.GenAcc:", acc_resp[0])
                        break

                    account_base = db_data_user()
                    account_buffer = None
                    if acc_resp[1] == 1:  # 已有账号、登录
                        account_base.ParseFromString(acc_resp[2])
                        if account_base.sin_channel != single_host_api_key:
                            resp["status_code"] = 10
                            break
                        rp2 = RDSPGuard.RP("gamelist")
                        # 單代理商向var@maintain_取得本代理商在多代理商的狀態
                        host_maintain = rp2.LibGrd.R.get("var@maintain_" + account_base.channel)
                        if host_maintain:  # 如果狀態是維護
                            break  # 不可進入大廳
                        if account_base.banned == 1:  # banned
                            break
                        if account_base.disable_login > 0:
                            Err("Forbidden login account:", acc)
                            break
                        if account_base.VIP == None:  # 如果玩家個人資訊沒有vip欄位
                            account_base.VIP = 0  # 從始至今還沒有成為過vip的人，預設給0
                        account_base.lastlogintime = GetServerTime()
                        account_base.game_id = game_id  # 將遊戲代號存取至redis base
                        account_base.user_type = user_type  # 將玩家付款種類存取至redis base

                        if not account_base.lv:  # 改版後第一次玩
                            account_base.lv = 1  # 初始等級1

                        account_buffer = account_base.SerializeToString()

                        if len(EventRP.get_event_data(account_base.uuid)) == 0:
                            self._set_default_event_data(account_base.uuid)

                        Log("玩家{}的付款方式={}".format(nam, user_type))
                    elif acc_resp[1] == 2:  # 新建账号、登录
                        account_base.uuid = int(acc_resp[2])
                        account_base.game_id = game_id  # 將遊戲代號存取至redis base
                        account_base.user_type = user_type  # 將玩家付款種類存取至redis base
                        account_base.account = acc
                        account_base.channel = host_api_key
                        account_base.sin_channel = single_host_api_key
                        account_base.sdk_uuid = uid
                        account_base.score = 0
                        account_base.banned = 0
                        account_base.VIP = 0  # 新建帳號不會是vip，預設給0
                        idrange = self.application.settings["faceid"]
                        account_base.faceid = GetRndInt(idrange[0], idrange[1])
                        account_base.bankscore = 0
                        account_base.nickname = nam
                        account_base.source = "PC"
                        account_base.lv = 1  # 初始等級1
                        account_base.jsondata = b"{}"
                        account_base.lastlogintime = GetServerTime()
                        account_base.regtime = account_base.lastlogintime
                        account_buffer = account_base.SerializeToString()
                        Log("玩家{}的付款方式={}".format(nam, user_type))
                        ret = await rp.LibGrd.AsyncCall("common.OnRegAcc",
                                                        *(account_base.uuid, acc, account_buffer, host_api_key))
                        if ret != 0:
                            Err("common.OnRegAcc:", ret)
                            break
                        self._set_default_event_data(account_base.uuid)

                    else:
                        Err("Unknown account result type:", acc_resp[1])
                        break

                    new_token = GetRndInt(1000000, 9999999)
                    login_resp = await rp.LibGrd.AsyncCall("common.OnLogin", *(
                    account_base.uuid, account_buffer, new_token, access_token, host_api_key))
                    if login_resp[0] != 0:
                        Err("common.OnLogin:", login_resp[0])
                        break

                    # # 同步token至多代理商redis的sha@data_
                    # if multi_host == 1:  # 如果跨代理商開關啟動
                    #     sync_url = self.application.settings["multihost"]["service"] + "/synctoken"
                    #     sync_token = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqSyncToken,
                    #                                                            sync_url,
                    #                                                            account_base.hostuuid, new_token)

                    # 添加ping
                    await rp.LibGrd.AsyncCall("common.OnKeepAlive", *(account_base.uuid, GetServerTime(), 1))

                    last_svrid, last_serv_data = self._get_svrid_and_serv_data(login_resp, host_api_key)

                    pdata = {
                        "uuid": account_base.uuid,
                        "game_id": account_base.game_id,  # 將遊戲代號存取至redis base
                        "account": account_base.account,
                        "nickname": account_base.nickname,
                        "score": account_base.score,
                        "banned": account_base.banned,
                        "VIP": account_base.VIP,
                        "token": new_token,
                        "svrid": last_svrid,
                        "faceid": account_base.faceid,
                        "bankscore": account_base.bankscore,
                        "sdk_uuid": account_base.sdk_uuid,
                        "channel": account_base.channel,
                        "source": account_base.source,
                        "access_token": access_token,
                        "profit": account_base.profit,
                        "dailyprofit": account_base.dailyprofit,
                        "lastscoretime": account_base.lastscoretime,
                        "regtime": account_base.regtime,
                        "lastlogintime": account_base.lastlogintime,
                        "jsondata": account_base.jsondata
                    }
                    data["pdata"] = pdata
                    servers = []
                    same_cfg = 0

                    # if multi_host == 1:  # 跨代理商開關啟動：導入跨server
                    #     url = self.application.settings["multihost"]["service"] + "/gameserverlist"
                    #     multihost_host_api_key = self.application.settings["multihost"]["hostkey"]
                    #     # 新增user_type導入HDRGameServerList，取得此類型玩家可進入的廳種
                    #     response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqGetGameList, url,
                    #                                                          multihost_host_api_key, user_type)
                    #     if json.loads(response)['error_code'] != 0:
                    #         resp["status_code"] = 3
                    #         break

                    #     rp2 = RDSPGuard.RP("gamelist")
                    #     multi_cfg = await rp2.AsyncHelper.Exec("get", "multi@cfg_" + host_api_key)
                    #     multi_cfg = int(multi_cfg) if multi_cfg else 0

                    #     if multi_cfg == 1:
                    #         servers = json.loads(response)["data"]

                    #     else:
                    #         same_count = 0  # 用來記錄房間參數相同的數量
                    #         for subgame_id in range(len(json.loads(response)["data"])):
                    #             url = self.application.settings["multihost"]["service"] + "/getsvropt"
                    #             multihost_game_id = self.application.settings["multihost"]["game_id"]
                    #             game_cfg = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqMultiHostSvropt,
                    #                                                                  url, multihost_host_api_key,
                    #                                                                  multihost_game_id,
                    #                                                                  subgame_id)
                    #             if 'data' not in json.loads(game_cfg):  # 防呆避免開桌目的是跳房號設定時，產生錯誤
                    #                 continue  # 沒有此房就換下一房
                    #             game_cfg = json.loads(game_cfg)['data']

                    #             hash_key = GenHostApiHashKey(host_api_key, subgame_id)
                    #             myp = MYPGuard.MYP("game")
                    #             sql = sSqls["query_room"]
                    #             query_results = await myp.AsyncExec(sql.GetSQL({"hash_key": hash_key}))

                    #             if len(query_results) < 1:
                    #                 resp["status_code"] = 2
                    #                 break
                    #             else:
                    #                 result = query_results[0]
                    #                 room_cfg = json.loads(result["json_options"])
                    #                 if game_cfg == room_cfg:
                    #                     same_count += 1
                    #                     await rp2.AsyncHelper.Exec("set", "multi@cfg_" + host_api_key, 1)
                    #                 else:
                    #                     await rp2.AsyncHelper.Exec("set", "multi@cfg_" + host_api_key, 0)
                    #                     break
                    #         # 房間參數全都一樣，才給參數
                    #         if same_count == len(json.loads(response)["data"]):
                    #             servers = json.loads(response)["data"]
                    #         else:
                    #             servers = []

                    # else:
                    svr_list = ServListMgr.GetOptimalSvrByHostApiKey(host_api_key)
                    Log("svr_list={}".format(svr_list))
                    for serv_data in svr_list:
                        # 如果不是與付款種類相符的廳
                        if token_credits_cash(user_type, serv_data) == False:
                            continue
                        if last_svrid >= 0 and last_serv_data is not None \
                                and serv_data.subgame_id == last_serv_data.subgame_id:
                            serv_data = last_serv_data

                        if serv_data.server_type == 1:  # 試玩桌
                            continue
                            
                        sMainSQL = '''SELECT `json_options` FROM `dmgame`.`cfg_gameroominfo` WHERE `host_api_key`= '%(host_api_key)s' AND `subgame_id`= '%(subgameid)s';;'''
                        hints = {}
                        sql = sMainSQL % {"host_api_key": host_api_key, "subgameid": serv_data.subgame_id}
                        resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                        if resualt == None or resualt == ():
                            resp["status_code"] = 3
                            break
                        else:
                            maxscore = eval(resualt[0]['json_options'])['max_score']
                        servinfo = {}
                        servinfo["subgame_id"] = serv_data.subgame_id
                        servinfo["server_type"] = serv_data.server_type
                        servinfo["addr"] = serv_data.server_addr.decode()
                        servinfo["port"] = serv_data.server_port
                        servinfo["cell"] = serv_data.cell_score
                        servinfo["adm_score"] = serv_data.admission_score
                        servinfo["max_player"] = serv_data.max_player
                        servinfo["cur_player"] = serv_data.cur_player
                        servinfo["max_score"] = maxscore
                        servers.append(servinfo)
                    data["servers"] = servers

                else:
                    data["pdata"] = "N/A"
                    svr_id = 9999
                    svr_list = ServListMgr.GetOptimalSvrByHostApiKey(host_api_key)
                    Log("svr_list={}".format(svr_list))
                    servers = []
                    # if multi_host == 1:  # 跨代理商開關啟動：導入跨server
                    #     url = self.application.settings["multihost"]["service"] + "/gameserverlist"
                    #     multihost_host_api_key = self.application.settings["multihost"]["hostkey"]
                    #     response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqGetGameList, url,
                    #                                                          multihost_host_api_key)
                    #     if json.loads(response)['error_code'] != 0:
                    #         resp["status_code"] = 3
                    #         break
                    #     servers = json.loads(response)["data"]
                    # else:
                    for serv_data in svr_list:
                        sMainSQL = '''SELECT `json_options` FROM `dmgame`.`cfg_gameroominfo` WHERE `host_api_key`= '%(host_api_key)s' AND `subgame_id`= '%(subgameid)s';;'''
                        hints = {}
                        sql = sMainSQL % {"host_api_key": host_api_key, "subgameid": serv_data.subgame_id}
                        resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                        if resualt == None or resualt == ():
                            resp["status_code"] = 3
                            break
                        else:
                            maxscore = eval(resualt[0]['json_options'])['max_score']
                        if serv_data.server_type == 1:  # 試玩桌
                            servinfo = {}
                            servinfo["subgame_id"] = svr_id
                            servinfo["server_type"] = serv_data.server_type
                            servinfo["addr"] = serv_data.server_addr.decode()
                            servinfo["port"] = serv_data.server_port
                            servinfo["cell"] = serv_data.cell_score
                            servinfo["adm_score"] = serv_data.admission_score
                            servinfo["max_player"] = serv_data.max_player
                            servinfo["cur_player"] = serv_data.cur_player
                            servinfo["max_score"] = maxscore
                            servers.append(servinfo)
                    data["servers"] = servers

                host_image, event_info = await self._get_event_loading_data(
                    host_api_key, game_id, lang)

                data["host_image"] = host_image
                data["eventInfo"] = event_info

                Log(data)

                encr_data = self._get_encr_data(encode, data)
                cli_url += "?data=" + encr_data.decode()
                resp["download_url"] = cli_url
                resp["status_code"] = 0
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRQueryTradeLog(ReqHandlerWrapper):
    async def post(self):
        resp = { "status_code" : -1 }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            member_id = self.GetBodyArgument("member_id", default = None)
            t = self.GetBodyArgument("type", default = None)
            txn_id = self.GetBodyArgument("txn_id", default = None)
            start_dtm = self.GetBodyArgument("start_dtm", default = None)
            end_dtm = self.GetBodyArgument("end_dtm", default = None)

            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                myp = MYPGuard.MYP("log")
                sql = sSqls["query_trade"]
                params = {
                    "start_index" : 0,
                    "count" : 100
                }

                conditions = []
                conditions.append("`host_key` = '%s'" % host_api_key)
                if member_id is not None and member_id != "":
                    conditions.append("`member_id` = '%s'" % member_id)
                if txn_id is not None:
                    conditions.append("`txn_id` = '%s'" % txn_id)
                else:
                    if t is not None:
                        conditions.append("`type` = %d" % int(t))
                    if start_dtm is not None:
                        conditions.append("`dtm` >= '%s'" % start_dtm)
                    if end_dtm is not None:
                        conditions.append("`dtm` < '%s'" % end_dtm)

                params["cond"] = "WHERE " + " AND ".join(conditions)
                query_result = await myp.AsyncExec(sql = sql.GetSQL(params = params))
                for res in query_result:
                    res["dtm"] = res["dtm"].strftime('%Y-%m-%d %H:%M:%S')

                resp["status_code"] = 0
                resp["records"] = query_result
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDROnlineInfo(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            multi_host_api_key = self.GetBodyArgument("multi_host_api_key", default = "")  # 指向的多代理商服務商戶代號
            host_api_key = self.GetBodyArgument("host_api_key", default = "")  # 目標單代理商商戶代號

            while True:
                if multi_host_api_key is None or len(multi_host_api_key) == 0 or\
                    host_api_key is None or len(host_api_key) == 0:
                    resp["status_code"] = -1  # 無必要參數
                    break

                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(multi_host_api_key,))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1  # sha@chl_帶入的host_api_key不是多代理商的商戶代號
                    break
                uuid_set = await rp.AsyncHelper.Exec("HGETALL", "sha@uuid2sid")
                if uuid_set is None:
                    Err("Online list is None!")
                    resp["status_code"] = 2  # 沒有任何玩家在遊戲房內，且沒有預設_holder在redis資料表內
                    break
                # 向多代理商主機請求目標單代理商的玩家清單
                redis_response = await rp.AsyncHelper.Exec("HGETALL", "var@host_" + str(host_api_key))
                if redis_response != None:  # 找得到時
                    resp["status_code"] = 0
                    resp["num_of_persons"] = len(redis_response)  # 回傳多代理商服務中，本單代理商的玩家總人數
                else:  # 找不到時，表示所有房間都沒人
                    resp["status_code"] = 0
                    resp["num_of_persons"] = 0  # 回傳多代理商服務中，本單代理商的玩家0人
                break
        except:
            PrintEXC()
        # try:
        #     host_api_key = self.GetBodyArgument("host_api_key")  # 單一代理商商戶代號
        #     detail = self.GetBodyArgument("detail", default=0)  # 是否取得玩家詳細資料0不用1要
        #     # 取得本單一代理商的多代理商服務商戶代號
        #     multi_host_api_key = self.application.settings["multihost"]["hostkey"]
        #     # 向多代理商取得這個單代理商的玩家總人數
        #     url = self.application.settings["multihost"]["service"] + "/numofsingleinmulti"
        #     response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqNumOfSingleInMulti, url,
        #                                                             multi_host_api_key, host_api_key)
        #     response = json.loads(response)  # 反序列化
        #     if response['status_code'] != 0:
        #         resp["status_code"] = 2  # 取得本單代理商在多代理商遊戲人數失敗
        #     else:
        #         resp["status_code"] = 0
        #         resp["total"] = int(response["num_of_persons"])  # 多代理商服務中，本單代理商的玩家總人數
        # except:
        #     PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

# class HDRNumOfSingleInMulti(ReqHandlerWrapper):  # (內部自動摳，外部不准打)取得多代理商服務中，本單代理商的玩家總人數
#     async def post(self):
#         resp = {
#             "status_code": -1
#         }
#         try:
#             multi_host_api_key = self.GetBodyArgument("multi_host_api_key")  # 指向的多代理商服務商戶代號
#             host_api_key = self.GetBodyArgument("host_api_key")  # 目標單代理商商戶代號
#             while True:
#                 rp = RDSPGuard.RP("game")
#                 chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(multi_host_api_key,))
#                 if chl_resp[0] != 0:
#                     resp["status_code"] = 1  # sha@chl_帶入的host_api_key不是多代理商的商戶代號
#                     break
#                 uuid_set = await rp.AsyncHelper.Exec("HGETALL", "sha@uuid2sid")
#                 if uuid_set is None:
#                     Err("Online list is None!")
#                     resp["status_code"] = 2  # 沒有任何玩家在遊戲房內，且沒有預設_holder在redis資料表內
#                     break
#                 # 向多代理商主機請求目標單代理商的玩家清單
#                 redis_response = await rp.AsyncHelper.Exec("HGETALL", "var@host_" + str(host_api_key))
#                 if redis_response != None:  # 找得到時
#                     resp["status_code"] = 0
#                     resp["num_of_persons"] = len(redis_response)  # 回傳多代理商服務中，本單代理商的玩家總人數
#                 else:  # 找不到時，表示所有房間都沒人
#                     resp["status_code"] = 0
#                     resp["num_of_persons"] = 0  # 回傳多代理商服務中，本單代理商的玩家0人
#                 break
#         except:
#             PrintEXC()
#         self.set_header('Content-Type', 'application/json; charset=UTF-8')
#         self.write(json.dumps(resp))
#         self.flush()
#         self.finish()

class HDRLoginRecords(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            member_id = self.GetBodyArgument("member_id", default = None)
            game_id = self.GetBodyArgument("game_id", default = None)
            subgame_id = self.GetBodyArgument("subgame_id", default = None)
            start_dtm = self.GetBodyArgument("start_dtm")
            end_dtm = self.GetBodyArgument("end_dtm")
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                myp = MYPGuard.MYP("log")
                sql = sSqls["query_login"]
                params = {
                    "start_index" : 0,
                    "count" : 100
                }

                conditions = []
                conditions.append("`vTime` >= '%s'" % start_dtm)
                conditions.append("`vTime` < '%s'" % end_dtm)
                conditions.append("`vType` = 3")

                if member_id is not None:
                    conditions.append("`vMemberId` = '%s'" % member_id)
                if game_id is None:
                    cfg_keys = await rp.AsyncHelper.Exec("KEYS", "sha@cfg_*")
                    game_id = "N/A"
                    if cfg_keys is not None and isinstance(cfg_keys, list):
                        game_id = cfg_keys[0].decode().split("_")[1]
                if subgame_id is not None:
                    conditions.append("`vSubGameId` = %d" % int(subgame_id))
                params["cond"] = "WHERE " + " AND ".join(conditions)
                query_result = await myp.AsyncExec(sql = sql.GetSQL(params = params))

                records = []
                for rec in query_result:
                    d = {
                        "member_id" : rec["vMemberId"],
                        "game_id" : game_id,
                        "subgame_id" : int(rec["vSubGameId"]),
                        "dtm" : rec["vTime"].strftime('%Y-%m-%d %H:%M:%S')
                    }
                    records.append(d)
                resp["status_code"] = 0
                resp["records"] = records
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRForceLogout(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            session_id = self.GetBodyArgument("session_id", default = None)
            member_id = self.GetBodyArgument("member_id", default = None)
            game_id = self.GetBodyArgument("game_id", default = None)
            subgame_id = self.GetBodyArgument("subgame_id", default = None)

            async_request = []
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                if member_id is not None:
                    acc = host_api_key + "_" + member_id
                    uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", acc)
                    if uuid is None:
                        resp["status_code"] = 2
                        break
                    uuid = int(uuid.decode())
                    await rp.AsyncHelper.Exec("PUBLISH", "sg_event", "5:" + str(uuid))
                    async_request.append(uuid)
                elif subgame_id is not None:
                    results = await rp.AsyncHelper.Exec("HGETALL", "sha@uuid2sid")
                    if results != None and isinstance(results, dict) == True:
                        for uuid, svrid in results.items():
                            if uuid.isdigit():
                                uuid = int(uuid)
                                host_key = await rp.AsyncHelper.Exec("HGET", "sha@data_" + str(uuid), "channel")
                                if host_key is not None and host_key.decode() == host_api_key:
                                    server_data = ServListMgr.GetSvrData(svrid)
                                    if server_data is None \
                                            or server_data.subgame_id != subgame_id:
                                        continue
                                    async_request.append(uuid)
                    await rp.AsyncHelper.Exec("PUBLISH", "sg_event", "6:" + host_api_key + "|" + str(subgame_id))
                else:
                    results = await rp.AsyncHelper.Exec("HVALS", "sha@acc2uuid")
                    for uuid in results:
                        if uuid.isdigit():
                            uuid = uuid.decode()
                            channel = await rp.AsyncHelper.Exec("HGET", "sha@data_"+uuid, "channel")
                            if channel is not None and channel.decode() == host_api_key:
                                async_request.append(int(uuid))
                    await rp.AsyncHelper.Exec("PUBLISH", "sg_event", "7:" + host_api_key)
                resp["status_code"] = 0
                break

            Log("踢人", async_request)
            #执行下线
            rp = RDSPGuard.RP("game")
            for uuid in async_request:
                ares = await rp.LibGrd.AsyncCall("common.GetInfoBySYS", *(uuid,))
                if ares[0] == 0 and len(ares) >= 5:
                    auth_token = int(ares[3].decode())
                    access_token = ares[4].decode()
                    if auth_token > 0:
                        account_base = db_data_user()
                        account_base.ParseFromString(ares[1])

                        await self.application.OnLogout(uuid, account_base.sin_channel, access_token)
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRDisMissGame(ReqHandlerWrapper):  # 強制解散卡在遊戲內的桌子或廳別
    async def post(self):
        resp = {
            "status_code": -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key", default=None)  # 多代理商戶或主服務商戶金鑰
            single_host_api_key = self.GetBodyArgument("single_host_api_key", default=None)  # 目標玩家來源商戶金鑰
            subgame_id = self.GetBodyArgument("subgame_id", default=None)  # 遊戲房號
            nick_name = self.GetBodyArgument("nick_name", default=None)  # 玩家名稱
            type = self.GetBodyArgument("type", default=0)  # 0解散整桌1解散整廳

            if type == 0:
                # 如果4個參數都有
                if host_api_key != None and single_host_api_key != None and subgame_id != None and nick_name != None:
                    rp = RDSPGuard.RP("game")
                    chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
                    if chl_resp[0] != 0:
                        resp["status_code"] = 1  # 回傳錯誤：商戶不存在
                    else:
                        # 進入center→OnRedisSubscribeCB
                        await rp.AsyncHelper.Exec("PUBLISH", "sg_event", "8:" \
                            + str(host_api_key) + "|" + str(single_host_api_key) + "|" + str(subgame_id) + "|" + str(nick_name))
                        resp["status_code"] = 0  # 回傳正確：正常解散
            elif type == 1:
                # 如果只有2個參數
                if host_api_key != None and subgame_id != None:
                    rp = RDSPGuard.RP("game")
                    chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
                    if chl_resp[0] != 0:
                        resp["status_code"] = 1  # 回傳錯誤：商戶不存在
                    else:
                        # 進入center→OnRedisSubscribeCB
                        await rp.AsyncHelper.Exec("PUBLISH", "sg_event", "9:" \
                                                  + str(host_api_key) + "|" + str(subgame_id))
                        resp["status_code"] = 0  # 回傳正確：正常解散
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRGetScore(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1,
            "data": []
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            member_id = self.GetBodyArgument("member_id", default = None)

            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break
                if member_id is not None: # to do: get score from member
                    uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", host_api_key + "_" + member_id)
                    if uuid is None:
                        resp["status_code"] = 2
                        break
                    uuid = int(uuid.decode())
                    account_base_ss = await rp.AsyncHelper.Exec("HGET", "sha@data_" + str(uuid), "base")
                    if account_base_ss is None:
                        resp["status_code"] = 3
                    account_base = db_data_user()
                    account_base.ParseFromString(account_base_ss)

                    svr_uuid = await rp.AsyncHelper.Exec("HGET", "sha@data_" + str(uuid), "svr_id")
                    svr_id = '999'
                    if svr_uuid is not None:
                        rplst = RDSPGuard.RP("gamelist")
                        server_list_db = rplst.LibGrd.R.get("var@serverlist")
                        server_list = get_game_server_list_ret()
                        if server_list_db is not None and len(server_list_db) > 0:
                            server_list.ParseFromString(server_list_db)
                            for idx in range(len(server_list.gslist)):
                                if server_list.gslist[idx].server_uuid == svr_uuid:
                                    svr_id = server_list.gslist[idx].subgame_id
                        svr_uuid = svr_uuid.decode()
                    else:
                        svr_uuid = '999'

                    resp["status_code"] = 0
                    resp["data"].append({
                        "member_id": member_id,
                        "score": account_base.score,
                        "svr_uuid": svr_uuid,
                        "game_id": svr_id #房間ID
                    })
                    break
                else: # to do: get all member's score from host
                    all_keys = await rp.AsyncHelper.Exec("HKEYS", "sha@acc2uuid")
                    for i in range(len(all_keys)):
                        hostid = all_keys[i].decode().split("_")[0]
                        memberid = all_keys[i].decode().split("_")[1]
                        if hostid == host_api_key:
                            uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", all_keys[i])
                            if uuid is None:
                                resp["status_code"] = 4
                                break
                            uuid = int(uuid.decode())
                            account_base_ss = await rp.AsyncHelper.Exec("HGET", "sha@data_" + str(uuid), "base")
                            if account_base_ss is None:
                                resp["status_code"] = 5
                                break
                            account_base = db_data_user()
                            account_base.ParseFromString(account_base_ss)
                            resp["data"].append({
                                "member_id": memberid,
                                "score": account_base.score
                            })
                    resp["status_code"] = 0
                    break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRRollOut(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code": -1
        }
        try:
            # Warn("----------------------------------HDRRollOut Enter")
            host_api_key = self.GetBodyArgument("host_api_key")
            member_id = self.GetBodyArgument("member_id")
            balance = self.GetBodyArgument("money") #单位分

            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key,))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break
                uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", host_api_key + "_" + member_id)
                if uuid is None:
                    resp["status_code"] = 2
                    break
                uuid = int(uuid.decode())
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                if account_res[0] != 0:
                    resp["status_code"] = 3
                    break
                account_base = db_data_user()
                account_base.ParseFromString(account_res[1])
                if account_base.channel != host_api_key:
                    resp["status_code"] = 4
                    break
                if len(account_res[2].decode()) > 0:
                    resp["status_code"] = 5 # "is gaming"
                    break
                if balance > account_base.score:
                    resp["status_code"] = 6  # "not enough money"
                    break
                txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
                rp2 = RDSPGuard.RP("tradelist")
                set_list_success = await rp2.AsyncHelper.Exec("SETNX", "list@trade_" + str(uuid), txn_id)  # 新增人員
                if set_list_success == True:
                    await rp2.AsyncHelper.Exec("EXPIRE", "list@trade_" + str(uuid), 240)  # 設定4分鐘
                timeStamp = GetServerTimeStr()
                # 游戏转到PS
                rollin = await rp2.AsyncHelper.Exec("get", "list@trade_" + str(uuid))
                if rollin is not None and str(json.loads(rollin)) != txn_id:
                    return -10, "Please confirm your account balance after 4 minutes."
                # pre-borrowed balance to redis, fixed the online problem by Leo.
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                account_base.ParseFromString(account_res[1])
                Warn("---HDRRollOut member_id=", member_id, " score=",
                        account_base.score, " - ", balance)
                account_base.score -= balance
                account_buffer = account_base.SerializeToString()
                rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

                # check score
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                account_base.ParseFromString(account_res[1])
                Warn("--- HDRRollOut check, member_id=", account_base.sdk_uuid, " score=",
                     account_base.score)


                chl_resp = rp.LibGrd.Call("channel.GetInfo", *(account_base.channel,))
                if chl_resp[0] == 0:
                    tmp = OnRedisResultParser(chl_resp[1])
                    host_name = tmp["name"]

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
                    # url = self.application.settings["ps_urls"]["rollin"]
                    # response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqRollIn, url,
                    #                                                         account_base.channel,
                    #                                                         account_base.sdk_uuid, txn_id, balance)
                    # response = json.loads(response)
                    multi_inf = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + account_base.channel, account_base.sin_channel)
                    multi_inf = json.loads(multi_inf)
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
                    #     Warn("---HDRRollOut Fail member_id=", member_id, " score=", account_base.score, " + ", balance)
                    #     account_base.score += balance
                    #     account_buffer = account_base.SerializeToString()
                    #     rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))
                    #     resp["status_code"] = 7 + response["status_code"]
                    #     break
                    await rp2.AsyncHelper.Exec("DEL", "list@trade_" + str(uuid))  #刪除人員名單及時間戳

                    # 写日志
                    sqlp = MYPGuard.MYP("log")
                    sql = sSqls["add_tradelog"]
                    sqlp.Exec(sql=sql.GetSQL(params={"txn": txn_id,
                                                     "host": account_base.sin_channel,
                                                     "type": 0,
                                                     "memberid": account_base.sdk_uuid, "amount": balance,
                                                     "time": timeStamp}), callback=None)
                resp["status_code"] = 0
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRQueryTableLog(ReqHandlerWrapper):
    async def post(self):
        response = { "status_code" : -1 }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            round_id = self.GetBodyArgument("round_id", default = None)
            game_id = self.GetBodyArgument("game_id", default = None)
            subgame_id = self.GetBodyArgument("subgame_id", default = None)
            start_dtm = self.GetBodyArgument("start_dtm")
            end_dtm = self.GetBodyArgument("end_dtm")
            member_id = self.GetBodyArgument("member_id", default=None)
            count = self.GetBodyArgument("count", default=None)

            while True:
                rp = RDSPGuard.RP("game")
                host_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if host_resp[0] != 0:
                    response["status_code"] = 1
                    break

                myp = MYPGuard.MYP("log")
                sql = sSqls["query_table"]
                params = {
                    "start_index" : 0,
                    "count" : count if count is not None else 100
                }

                if game_id is None:
                    cfg_keys = await rp.AsyncHelper.Exec("KEYS", "sha@cfg_*")
                    game_id = "N/A"
                    if cfg_keys is not None and isinstance(cfg_keys, list):
                        game_id = cfg_keys[0].decode().split("_")[1]

                cond_list = []
                cond_list.append("`vHostApiKey` = '%s'" % host_api_key)
                if round_id is not None:
                    cond_list.append("`vRoundID` = '%s'" % round_id)
                else:
                    cond_list.append("`vTime` >= '%s'" % start_dtm)
                    cond_list.append("`vTime` < '%s'" % end_dtm)
                    if subgame_id is not None:
                        chl_data = OnRedisResultParser(host_resp[1])
                        hash_key = GenHostApiHashKey(host_api_key, subgame_id)
                        cond_list.append("`vHashKey` = '%s'" % (hash_key))
                if member_id is not None:
                    cond_list.append("`Log` LIKE '%{}%'".format("\"" + "nam" + "\"" + ": " + "\"" + member_id + "\""))
                params["cond"] = "WHERE " + " AND ".join(cond_list)
                Log(sql.GetSQL(params = params))
                query_result = await myp.AsyncExec(sql = sql.GetSQL(params = params))

                rec_list = []
                for result in query_result:
                    log_data = json.loads(result["Log"])
                    game_data = log_data["detail"]
                    rec = {
                        "round_id" : log_data["roundid"],
                        "game_id" : game_id,
                        "subgame_id" : log_data["subgameid"],
                        "players" : game_data["p"],
                        "start_dtm" : game_data["bt"],
                        "end_dtm" : log_data["time"],
                        "gc": game_data["gc"],
                        "cell": game_data["cell"]
                    }
                    rec_list.append(rec)
                response["status_code"] = 0
                response["records"] = rec_list
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(response))
        self.flush()
        self.finish()

class HDRQueryPlayLog(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            round_id = self.GetBodyArgument("round_id", default = None)
            member_id = self.GetBodyArgument("member_id", default = None)
            game_id = self.GetBodyArgument("game_id", default = None)
            subgame_id = self.GetBodyArgument("subgame_id", default = None)
            start_dtm = self.GetBodyArgument("start_dtm")
            end_dtm = self.GetBodyArgument("end_dtm")
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                if game_id is None:
                    cfg_keys = await rp.AsyncHelper.Exec("KEYS", "sha@cfg_*")
                    game_id = "N/A"
                    if cfg_keys is not None and isinstance(cfg_keys, list):
                        game_id = cfg_keys[0].decode().split("_")[1]

                myp = MYPGuard.MYP("log")
                sql = sSqls["query_play"]
                params = {
                    "start_index" : 0,
                    "count" : 20
                }
                cond_list = []
                if round_id is not None:
                    cond_list.append("gp.vRoundID = '%s'" % round_id)
                else:
                    cond_list.append("gp.vTime >= '%s'" % start_dtm)
                    cond_list.append("gp.vTime < '%s'" % end_dtm)
                    if member_id is not None:
                        cond_list.append("gp.vMemberID = '%s'" % member_id)
                    if subgame_id is not None:
                        chl_data = OnRedisResultParser(chl_resp[1])
                        cond_list.append("gp.vSubGameID = %d" % subgame_id)
                params["cond"] = " " + " AND ".join(cond_list)
                query_result = await myp.AsyncExec(sql = sql.GetSQL(params = params))

                rec_list = []
                for result in query_result:
                    log_data = json.loads(result["da"])
                    game_data = log_data["detail"]
                    rec = {
                        "sn": result["ID"],
                        "round_id": result["vRoundID"],
                        "member_id": result["vMemberID"],
                        "game_id": game_id,
                        "subgame_id": int(result["vSubGameID"]),
                        "result": game_data["p"],
                        "start_dtm": game_data["bt"],
                        "end_dtm": log_data["time"]
                    }
                    cal_score = int(result["vCalScore"])
                    if cal_score > 0:
                        rec["win"] = cal_score
                        rec["bet"] = 0
                    elif cal_score < 0:
                        rec["win"] = 0
                        rec["bet"] = -cal_score
                    else:
                        rec["win"] = 0
                        rec["bet"] = 0
                    rec_list.append(rec)

                resp["status_code"] = 0
                resp["records"] = rec_list
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRQueryPlayerHourLog(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            member_id = self.GetBodyArgument("member_id", default = None)
            game_id = self.GetBodyArgument("game_id", default = None)
            subgame_id = self.GetBodyArgument("subgame_id", default = None)
            start_dtm = self.GetBodyArgument("start_dtm")
            end_dtm = self.GetBodyArgument("end_dtm")
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                if game_id is None:
                    cfg_keys = await rp.AsyncHelper.Exec("KEYS", "sha@cfg_*")
                    game_id = "N/A"
                    if cfg_keys is not None and isinstance(cfg_keys, list):
                        game_id = cfg_keys[0].decode().split("_")[1]

                myp = MYPGuard.MYP("log")
                sql = sSqls["query_hourlog"]
                params = {
                    "start_index" : 0,
                    "count" : 1000
                }
                cond_list = []
                cond_list.append("`time` > '%s'" % start_dtm)
                cond_list.append("`time` <= '%s'" % end_dtm)
                cond_list.append("`host_api_key` = '%s'" % host_api_key)
                if member_id is not None:
                    cond_list.append("`member_id` = '%s'" % member_id)
                #chl_data = OnRedisResultParser(chl_resp[1])
                #ctm_data = json.loads(chl_data["extra"])
                if subgame_id is not None:
                    cond_list.append("`subgame_id` = %d" % subgame_id)
                params["cond"] = "WHERE " + " AND ".join(cond_list)
                Log(sql.GetSQL(params = params))
                query_result = await myp.AsyncExec(sql = sql.GetSQL(params = params))
                rec_list = []
                for result in query_result:
                    rec = {
                        "member_id" : result["member_id"],
                        "game_id" : game_id,
                        "subgame_id" : int(result["subgame_id"]),
                        "count" : int(result["count"]),
                        "dtm" : result["time"].strftime('%Y-%m-%d %H:%M:%S')
                    }
                    profit = int(result["profit"])
                    if profit > 0:
                        rec["win"] = profit
                        rec["bet"] = 0
                    elif profit < 0:
                        rec["win"] = 0
                        rec["bet"] = -profit
                    else:
                        rec["win"] = 0
                        rec["bet"] = 0
                    rec_list.append(rec)

                resp["records"] = rec_list
                resp["status_code"] = 0
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRQueryPlayerDayLog(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            member_id = self.GetBodyArgument("member_id", default = None)
            game_id = self.GetBodyArgument("game_id", default = None)
            subgame_id = self.GetBodyArgument("subgame_id", default = None)
            start_dt = self.GetBodyArgument("start_dt")
            end_dt = self.GetBodyArgument("end_dt")
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                if game_id is None:
                    cfg_keys = await rp.AsyncHelper.Exec("KEYS", "sha@cfg_*")
                    game_id = "N/A"
                    if cfg_keys is not None and isinstance(cfg_keys, list):
                        game_id = cfg_keys[0].decode().split("_")[1]

                myp = MYPGuard.MYP("log")
                sql = sSqls["query_hourlog"]
                params = {
                    "start_index" : 0,
                    "count" : 10000
                }
                cond_list = []
                cond_list.append("`time` > '%s'" % start_dt)
                cond_list.append("`time` <= '%s'" % end_dt)
                cond_list.append("`host_api_key` = '%s'" % host_api_key)
                if member_id is not None:
                    cond_list.append("`member_id` = '%s'" % member_id)
                if subgame_id is not None:
                    cond_list.append("`subgame_id` = %d" % int(subgame_id))
                params["cond"] = "WHERE " + " AND ".join(cond_list)
                query_result = await myp.AsyncExec(sql = sql.GetSQL(params = params))
                log_statistic = {}
                for result in query_result:
                    mid = result["member_id"]
                    sgid = int(result["subgame_id"])
                    count = int(result["count"])
                    profit = int(result["profit"])
                    time = result["time"].strftime('%Y-%m-%d')
                    if mid in log_statistic:
                        tmp = log_statistic[mid]
                        if time in tmp:
                            time_tmp = tmp[time]
                            if sgid in time_tmp:
                                tmp2 = time_tmp[sgid]
                                tmp2[0] += profit
                                tmp2[1] += count
                            else:
                                time_tmp[sgid] = [profit, count]
                        else:
                            time_tmp = {}
                            time_tmp[sgid] = [profit, count]
                            tmp[time] = time_tmp
                    else:
                        tmp = {}
                        tmp[time] = {}
                        tmp[time][sgid] = [profit, count]
                        log_statistic[mid] = tmp

                rec_list = []
                for mid, stdata in log_statistic.items():
                    for tm, tmdata in stdata.items():
                        for sgid, st in tmdata.items():
                            rec = {
                                "member_id" : mid,
                                "game_id" : game_id,
                                "subgame_id" : sgid,
                                "count" : st[1],
                                "dt" : tm
                            }
                            tot_profit = st[0]
                            if tot_profit > 0:
                                rec["win"] = tot_profit
                                rec["bet"] = 0
                            elif tot_profit < 0:
                                rec["win"] = 0
                                rec["bet"] = -tot_profit
                            else:
                                rec["win"] = 0
                                rec["bet"] = 0
                            rec_list.append(rec)

                resp["records"] = rec_list
                resp["status_code"] = 0
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()


# 游戏设定
class HDRCreateServerConfig(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            game_id = self.GetBodyArgument("game_id")
            data = self.GetBodyArgument("data")

            rp = RDSPGuard.RP("game")
            key = "sha@cfg_" + game_id
            ret = await rp.AsyncHelper.Exec("HGET", key, "data")
            if ret is not None:
                resp["status_code"] = 1
            else:
                await rp.AsyncHelper.Exec("HSET", key, "data", json.dumps(data))
                if data["enable"]:
                    await rp.AsyncHelper.Exec("PUBLISH", "sg_event", "3:1")
                resp["status_code"] = 0
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRGetServerConfig(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            game_id = self.GetBodyArgument("game_id")
            rp = RDSPGuard.RP("game")
            key = "sha@cfg_" + game_id
            ret = await rp.AsyncHelper.Exec("HGET", key, "data")
            if ret is None:
                resp["status_code"] = 1
            else:
                resp["data"] = json.loads(ret)
                resp["status_code"] = 0
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRUpdateServerConfig(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            game_id = self.GetBodyArgument("game_id")
            data = self.GetBodyArgument("data")

            rp = RDSPGuard.RP("game")
            key = "sha@cfg_" + game_id
            ret = await rp.AsyncHelper.Exec("HGET", key, "data")
            if ret is None:
                resp["status_code"] = 1
            else:
                old_data = json.loads(ret)
                old_sw = old_data["enable"]
                old_data.update(data)
                await rp.AsyncHelper.Exec("HSET", key, "data", json.dumps(old_data))
                new_sw = old_data["enable"]
                if new_sw != old_sw:
                    await rp.AsyncHelper.Exec("PUBLISH", "sg_event", "3:" + str(int(new_sw)))
                resp["status_code"] = 0
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRDeleteServerConfig(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            game_id = self.GetBodyArgument("game_id")
            rp = RDSPGuard.RP("game")
            key = "sha@cfg_" + game_id
            await rp.AsyncHelper.Exec("HDEL", key, "data")
            resp["status_code"] = 0
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

# 渠道相关
class HDRCreateChannel(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_id = self.GetBodyArgument("host_id")
            host_api_key = self.GetBodyArgument("host_api_key")
            data = self.GetBodyArgument("data")
            rp = RDSPGuard.RP("game")
            ret = await rp.LibGrd.AsyncCall("channel.CreateNew", *(host_api_key, host_id, "", json.dumps(data), ))
            if ret == 0:
                resp["status_code"] = 0
            else:
                resp["status_code"] = 1
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRGetChannelInfo(ReqHandlerWrapper):
    async def post(self):
        resp = { "status_code" : -1 }

        try:
            while True:
                host_api_key = self.GetBodyArgument("host_api_key", default = "")
                if len(host_api_key) == 0:
                    break

                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] == 0:
                    tmp = OnRedisResultParser(chl_resp[1])
                    resp["data"] = json.loads(tmp["extra"])
                    resp["status_code"] = 0
                else:
                    resp["status_code"] = 1

                break
        except:
            PrintEXC()

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRModChannelInfo(ReqHandlerWrapper):
    async def post(self):
        resp = { "status_code" : -1 }
        try:
            while True:
                host_api_key = self.GetBodyArgument("host_api_key", default = "")
                if len(host_api_key) == 0:
                    break

                data = self.GetBodyArgument("data", default = "")
                if len(data) == 0:
                    break

                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] == 0:
                    tmp = OnRedisResultParser(chl_resp[1])
                    old_data = json.loads(tmp["extra"])
                    old_data.update(data)
                    # multi_host = old_data["multihost"]
                    # if multi_host == 1:  # 多代理商時
                    #     url = self.application.settings["multihost"]["service"] + "/hostmaintain"
                    #     # 像多代理商請求並通知
                    #     multi_host_api_key = self.application.settings["multihost"]["hostkey"]  # 取得多代理商api key
                    #     await self.application.AsyncGuard.DoAsync(RequestHelper.ReqHostMaintain, url, host_api_key,
                    #                                               data["status"], multi_host_api_key)
                    await rp.AsyncHelper.Exec("HSET", "sha@chl_" + host_api_key, "extra", json.dumps(old_data))
                    resp["status_code"] = 0
                else:
                    resp["status_code"] = 1

                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRDeleteChannel(ReqHandlerWrapper):
    async def post(self):
        resp = { "status_code" : -1 }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")

            rp = RDSPGuard.RP("game")
            ret = await rp.LibGrd.AsyncCall("channel.Remove", *(host_api_key, ))
            if ret == 0:
                resp["status_code"] = 0
            else:
                resp["status_code"] = 1
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

# 游戏配置
class HDRCreateServerOption(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            game_id = self.GetBodyArgument("game_id")
            subgame_id = int(self.GetBodyArgument("subgame_id"))
            data = self.GetBodyArgument("data")
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                Log(chl_resp)
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                cfg_resp = await rp.AsyncHelper.Exec("HGET", "sha@cfg_" + game_id, "data")
                if cfg_resp is None:
                    resp["status_code"] = 2
                    break

                fix_keys = [
                    "srvtype",  # 服务类型(1：体验场 2：正式场 3:亲友场)
                    "tablecount",  # 桌子数
                    "cellscore",  # 底注(cent)
                    "accessscore",  # 准入(cent)
                    "thinktime",  # 思考时间(s)
                    "ledmul",  # 跑马灯倍数
                    "allowrobot",  # 是否允许匹配机器人(0:不允许)
                    "ipfilter",  # 匹配时是否过滤桶IP段玩家(0:不过滤)
                    "random_robot_rate",  # 機器人強制排隊(防套利0~100)
                    "MultiHost",  # 多代理商配對開關
                    "max_score",  # 最大攜帶金額
                    "pre_arbitrage",  # 防止玩家套利機制0關閉1啟動
                    "max_connected",  # 房間最大容留連線人數
                    "win_times",  # 贏分底注倍率上限，超過則下一場開始vip
                    "robot_draw_rate",  # 機器人摸到好牌的機率
                    "robot_draw_rate_vip",  # vip房內，機器人摸到好牌的機率
                    "bad_draw_rate",  # 真人玩家啟用壞牌抽牌機制的機率
                    "bad_draw_rate_vip",  # vip房內，真人玩家啟用壞牌抽牌機制的機率
                    # "challengetime",  # 接受比牌的思考時間
                    # "robot_fight_rate",  # 機器人目前比牌點數最小，發起比牌的機率
                ]

                key_chk = True
                for key in fix_keys:
                    if key not in data:
                        key_chk = False
                        break
                    else:
                        data[key] = int(data[key])

                if not key_chk:
                    Err("Option format error!", data)
                    break

                # 是否允許啟用以小博大機制結算分數(0不允許1允許)
                data["allow_leverage"] = allow_leverage  # 全域變數

                hash_key = GenHostApiHashKey(host_api_key, subgame_id)
                Log("host_api_key hash(md5)", hash_key)
                params = {
                    "hash_key" : hash_key,
                    "host_api_key" : host_api_key,
                    "subgame_id" : subgame_id,
                    "json_options" : json.dumps(data),
                    "create_time" : GetServerTimeStr()
                }
                myp = MYPGuard.MYP("game")
                sql = sSqls["db_createroom"]
                await myp.AsyncExec(sql.GetSQL(params))
                resp["status_code"] = 0
                rp2 = RDSPGuard.RP("gamelist")
                await rp2.AsyncHelper.Exec("del", "multi@cfg_" + host_api_key)
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRGetServerOption(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            game_id = self.GetBodyArgument("game_id")
            subgame_id = int(self.GetBodyArgument("subgame_id"))
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                cfg_resp = await rp.AsyncHelper.Exec("HGET", "sha@cfg_" + game_id, "data")
                if cfg_resp is None:
                    resp["status_code"] = 2
                    break

                hash_key = GenHostApiHashKey(host_api_key, subgame_id)
                myp = MYPGuard.MYP("game")
                sql = sSqls["query_room"]
                query_results = await myp.AsyncExec(sql.GetSQL({"hash_key" : hash_key}))
                if len(query_results) < 1:
                    resp["status_code"] = 2
                else:
                    result = query_results[0]
                    resp["data"] = json.loads(result["json_options"])
                    resp["status_code"] = 0
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRUpdateServerOption(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            game_id = self.GetBodyArgument("game_id")
            subgame_id = int(self.GetBodyArgument("subgame_id"))
            data = self.GetBodyArgument("data")
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                cfg_resp = await rp.AsyncHelper.Exec("HGET", "sha@cfg_" + game_id, "data")
                # Log(cfg_resp)
                if cfg_resp is None:
                    resp["status_code"] = 2
                    break

                fix_keys = [
                    #"srvtype",  # 服务类型(1：体验场 2：正式场)
                    #"tablecount",  # 桌子数
                    "cellscore",  # 底注(cent)
                    "accessscore",  # 准入(cent)
                    "thinktime",  # 思考时间(s)
                    "ledmul",  # 跑马灯倍数
                    "allowrobot",  # 是否允许匹配机器人(0:不允许)
                    "ipfilter",     # 匹配时是否过滤桶IP段玩家(0:不过滤)
                    "random_robot_rate",  # 機器人強制排隊(防套利0~100)
                    "MultiHost",  # 多代理商配對開關
                    "max_score",  # 最大攜帶金額
                    "pre_arbitrage",  # 防止玩家套利機制0關閉1啟動
                    "max_connected",  # 房間最大容留連線人數
                    "win_times",  # 贏分底注倍率上限，超過則下一場開始vip
                    "robot_draw_rate",  # 機器人摸到好牌的機率
                    "robot_draw_rate_vip",  # vip房內，機器人摸到好牌的機率
                    "bad_draw_rate",  # 真人玩家啟用壞牌抽牌機制的機率
                    "bad_draw_rate_vip",  # vip房內，真人玩家啟用壞牌抽牌機制的機率
                    # "challengetime",  # 接受比牌的思考時間
                    # "robot_fight_rate",  # 機器人目前比牌點數最小，發起比牌的機率
                ]

                key_chk = True
                for key in data:
                    if key not in fix_keys:
                        key_chk = False
                        # Log(key)
                        break
                    else:
                        data[key] = int(data[key])

                if not key_chk:
                    Err("Option format error!", data)
                    break

                # 是否允許啟用以小博大機制結算分數(0不允許1允許)
                data["allow_leverage"] = allow_leverage  # 全域變數

                hash_key = GenHostApiHashKey(host_api_key, subgame_id)
                myp = MYPGuard.MYP("game")
                sql = sSqls["query_room"]
                query_results = await myp.AsyncExec(sql.GetSQL({"hash_key" : hash_key}))
                if len(query_results) < 1:
                    resp["status_code"] = 2
                    break

                result = query_results[0]
                src_data = json.loads(result["json_options"])
                src_data.update(data)
                params = {
                    "hash_key" : hash_key,
                    "json_options" : json.dumps(src_data)
                }
                sql = sSqls["update_room"]
                await myp.AsyncExec(sql.GetSQL(params))
                resp["status_code"] = 0
                rp2 = RDSPGuard.RP("gamelist")
                await rp2.AsyncHelper.Exec("del", "multi@cfg_" + host_api_key)
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRDeleteServerOption(ReqHandlerWrapper):
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            game_id = self.GetBodyArgument("game_id")
            subgame_id = int(self.GetBodyArgument("subgame_id"))
            while True:
                rp = RDSPGuard.RP("game")
                chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
                if chl_resp[0] != 0:
                    resp["status_code"] = 1
                    break

                cfg_resp = await rp.AsyncHelper.Exec("HGET", "sha@cfg_" + game_id, "data")
                if cfg_resp is None:
                    resp["status_code"] = 2
                    break

                hash_key = GenHostApiHashKey(host_api_key, subgame_id)
                myp = MYPGuard.MYP("game")
                sql = sSqls["delete_room"]
                await myp.AsyncExec(sql.GetSQL({"hash_key" : hash_key}))
                resp["status_code"] = 0
                rp2 = RDSPGuard.RP("gamelist")
                await rp2.AsyncHelper.Exec("del", "multi@cfg_" + host_api_key)
                break
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRInsertMultiHostInformation(ReqHandlerWrapper):
    """
        新增單代理商戶資訊至多代理
        共享錢包需新增URL
        獨立前包為空
    """
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            single_host_api_key = self.GetBodyArgument("single_host_api_key")
            data = self.GetBodyArgument("data")
            
            rp = RDSPGuard.RP("game")
            chl_resp = await rp.LibGrd.AsyncCall("channel.GetInfo", *(host_api_key, ))
            if chl_resp[0] != 0:
                resp["status_code"] = 1
            else:
                inf_resp = await rp.AsyncHelper.Exec("HSET", "multi@inf_" + host_api_key, single_host_api_key, json.dumps(data))  # 先存空dict
                if inf_resp == 1:
                    resp["msg"] = "Inster success"
                    resp["status_code"] = 0
                elif inf_resp == 0:
                    resp["msg"] = "Update success"
                    resp["status_code"] = 0
                else:
                    resp["msg"] = "error"
                    resp["status_code"] = 1

        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRGetMultiHostInformation(ReqHandlerWrapper):
    """
        查詢多代理底下的單代理商戶是否存在
        共享錢包為共享錢包URL
        獨立前包為空
    """
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            single_host_api_key = self.GetBodyArgument("single_host_api_key")
            
            rp = RDSPGuard.RP("game")
            inf_resp = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + host_api_key, single_host_api_key)
            if inf_resp is None:
                resp["status_code"] = 1
            else:
                resp["status_code"] = 0
                resp["data"] = json.loads(inf_resp)

        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRDeleteMultiHostInformation(ReqHandlerWrapper):
    """
        刪除多代理底下的單代理商戶資料
    """
    async def post(self):
        resp = {
            "status_code" : -1
        }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            single_host_api_key = self.GetBodyArgument("single_host_api_key")
            
            rp = RDSPGuard.RP("game")
            inf_resp = await rp.AsyncHelper.Exec("HDEL", "multi@inf_" + host_api_key, single_host_api_key)  # 先存空dict
            if inf_resp == 1:
                resp["status_code"] = 0
                resp["msg"] = "success"
            else:
                resp["status_code"] = 1
                resp["msg"] = "error"

        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRSetAndroidOption(ReqHandlerWrapper):
    async def post(self):
        resp = { "status_code" : -1 }
        try:
            data = self.GetBodyArgument("data")
            if data != None:
                sqlcommand = 'TRUNCATE cfg_android;'
                await MYPGuard.MYP("game").AsyncExec(sqlcommand, None)
                sql = 'INSERT INTO `cfg_android` (`NickName`) VALUES("' + data[0] + '")'
                del data[0]
                for name in data:
                    sql = sql + ',("' + name + '")'
                await MYPGuard.MYP("game").AsyncExec(sql)
                resp["status_code"] = 0
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRSetAndroidVip(ReqHandlerWrapper):
    async def post(self):
        resp = { "status_code" : -1 }
        try:
            data = self.GetBodyArgument("data")
            if data != None:
                sqlcommand = 'TRUNCATE cfg_android_vip;'
                await MYPGuard.MYP("game").AsyncExec(sqlcommand, None)
                sql = 'INSERT INTO `cfg_android_vip` (`NickName`) VALUES("' + data[0] + '")'
                del data[0]
                for name in data:
                    sql = sql + ',("' + name + '")'
                await MYPGuard.MYP("game").AsyncExec(sql)
                resp["status_code"] = 0
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRExcepplayer(ReqHandlerWrapper):
    async def post(self):
        resp = {"status_code": -1}
        try:
            host_api_key = self.GetBodyArgument("host_api_key", default = None)
            type = self.GetBodyArgument("type", default = 0)

            if host_api_key != None and host_api_key != '':
                rp = RDSPGuard.RP("game")
                # get playsr list
                index = 0
                scanfinish = False
                playlst = []
                while scanfinish == False:
                    rdres = await rp.AsyncHelper.Exec("HSCAN", "sha@acc2uuid", index, "match", host_api_key + "*", "count", 1000)
                    if rdres is None:
                        resp["status_code"] = 1
                        break
                    if rdres[0] is None:
                        resp["status_code"] = 2
                        break
                    index = rdres[0]
                    if index == 0: # end
                        scanfinish = True
                    if rdres[1] == None:
                        resp["status_code"] = 3
                        break
                    for key in rdres[1]:
                        data = key.decode().split("_")
                        playlst.append({
                            "uuid": rdres[1][key].decode(),
                            "host_id": data[0],
                            "memberid": data[1]
                        })
                # check player list
                userinfo = []
                if playlst != []:
                    for item in playlst:
                        rdres = await rp.AsyncHelper.Exec("HGET", "sha@data_" + item["uuid"], "base")
                        if rdres is None:
                            continue
                        account_base = db_data_user()
                        account_base.ParseFromString(rdres)
                        if account_base is None:
                            continue
                        data = {
                                    "memberid": account_base.sdk_uuid,
                                    "uuid": account_base.uuid,
                                    "score": account_base.score
                                }
                        # type 0: check player's score < 0
                        if type == 0:
                            if account_base.score < 0:
                                userinfo.append(data)
                        # type 1: check player's score > 0
                        if type == 1:
                            if account_base.score > 0:
                                userinfo.append(data)
                        # type 2: check player's score < 0 and clear
                        if type == 2:
                            if account_base.score < 0:
                                token = await rp.AsyncHelper.Exec("HGET", "sha@data_" + item["uuid"], "acs_token")
                                if token is None:
                                    account_base.score = 0
                                    account_buffer = account_base.SerializeToString()
                                    rp.LibGrd.Call("common.SetInfoBySYS", *(account_base.uuid, account_buffer))
                                    userinfo.append(data)

                                    # check final score
                                    account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(account_base.uuid,))
                                    account_base.ParseFromString(account_res[1])
                                    Warn("--- HDRExcepplayer Finished, member_id=", account_base.sdk_uuid, " score=",
                                         account_base.score)
                # end
                resp["data"] = userinfo
                if resp["status_code"] == -1:
                    resp["status_code"] = 0
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRHealthcheck(ReqHandlerWrapper):    # Healthcheck
    async def get(self):
        resp = {"status_code" : 0}
        self.add_header("Access-Control-Allow-Origin", "*")
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRVersionJson(ReqHandlerWrapper):    # 確認目前後端程式版本
    async def get(self):
        # 開啟Version.json取得目前的後端程式版本
        call_program_version_data_back = mainservice.program_version_data
        # 如果Version.json存在，回傳版本號
        if call_program_version_data_back != {}:
            resp = call_program_version_data_back
        # 不存在檔案時，統一給404 not found
        else:
            raise tornado.web.HTTPError(
                status_code = 404,
                reason = "Not Found"
            )
        self.add_header("Access-Control-Allow-Origin", "*")
        self.write(json.dumps(resp))
        self.flush()
        self.finish()
        
class HDRGetLoginHistory(ReqHandlerWrapper): #查詢最後一筆進入遊戲的時間
    async def post(self):
        resp = { "error_code" : -1,"msg": "error" }
        try:
            host_id = str(self.GetBodyArgument("host_api_key", default = None))
            game_id = int(self.GetBodyArgument("game_id", default = 999))  # 其實是subgame_id桌號
            member_id = str(self.GetBodyArgument("member_id", default = None))
            rp = RDSPGuard.RP("game")
            if member_id is None or member_id is "" or game_id is 999 or game_id is "" or host_id is None or host_id is "":
                resp = {
                    "error_code": -1,
                    "msg": "error"
                }
            else:
                acc = host_id + "_" + member_id
                uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", acc)
                if not uuid:
                    resp = {
                        "error_code": -2,
                        "msg": "uuid not found"
                    }
                else:
                    uuid = int(uuid.decode())
                    sMainSQL = '''SELECT * FROM `dmgamelog`.`game_login_log` WHERE `vHostApiKey`= '%(host_id)s' AND `vType`= 3 AND `vUUID`=%(uuid)d ORDER BY ID DESC LIMIT 0 , 1;;'''
                    hints = {}
                    sql = sMainSQL % {"host_id": host_id, "uuid": uuid}
                    resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                    if resualt[0] is "":
                        resp = {
                            "error_code": -3,
                            "msg": "SQL information not found"
                        }
                    else:
                        resp = {
                            "error_code": 0,
                            "msg": "success",
                            "member_id": resualt[0]["vMemberId"],
                            "game_id": int(resualt[0]["vSubGameId"]),
                            "dtm": resualt[0]["vTime"].strftime('%Y-%m-%d %H:%M:%S')
                        }
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRGetTradeErrLog(ReqHandlerWrapper): #查詢交易失敗的名單
    async def post(self):
        resp = { "error_code" : -1,"msg": "error"  }
        try:
            searchtime = (datetime.datetime.now() - datetime.timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            sMainSQL = '''SELECT * FROM `dmgamelog`.`game_trade_err_log` WHERE `dtm` < '%(searchtime)s' 
                            AND `txn_id` NOT IN(SELECT `txn_id` FROM `dmgamelog`.`game_trade_log`);;'''
            hints = {}
            sql = sMainSQL % {"searchtime": searchtime}
            resualt = await MYPGuard.MYP("log").AsyncExec(sql=sql, hint=hints, callback=None)
            if not resualt:
                resp = {
                    "error_code": 0,
                    "msg": "list is empty"
                }
            else:
                error_log = []
                txn_id_list = []
                for i in range(len(resualt)):
                    d = {
                        "txn_id": resualt[i]["txn_id"],
                        "host_key": resualt[i]["host_key"],
                        "type": resualt[i]["type"],
                        "member_id": resualt[i]["member_id"],
                        "amount": resualt[i]["amount"],
                        "dtm": resualt[i]["dtm"].strftime('%Y-%m-%d %H:%M:%S'),
                        "end": resualt[i]["end"]
                    }
                    txn_id_list.append(resualt[i]["txn_id"])
                    error_log.append(d)
                resp["error_code"] = 0
                resp["msg"] = "success"
                resp["search_dtm"] = searchtime
                resp["count"] = len(txn_id_list)
                resp["txn_id_list"] = txn_id_list
                resp["detail"] = error_log

        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRRecoveryTradeLog(ReqHandlerWrapper): #補回交易紀錄及清除名單
    async def post(self):
        resp = {"error_code": -1, "msg": "error"}
        try:
            txn_id_list = self.GetBodyArgument("txn_id_list")
            txn_id_len = len(txn_id_list)
            txn_id_list = "(" + ','.join(txn_id_list) + ")"
            sMainSQL = 'SELECT * FROM `dmgamelog`.`game_trade_err_log` WHERE `txn_id` IN ' + txn_id_list + ' AND `txn_id` NOT IN(SELECT `txn_id` FROM `dmgamelog`.`game_trade_log`);;'
            hints = {}
            resualt = await MYPGuard.MYP("log").AsyncExec(sql=sMainSQL, hint=hints, callback=None)
            if not resualt:
                resp = {
                    "error_code": -2,
                    "msg": "check list error"
                }
            elif txn_id_len != len(resualt):
                resp = {
                    "error_code": -3,
                    "msg": "check count error"
                }
            else:
                sMainSQL = 'INSERT INTO `game_trade_log`(SELECT `txn_id`, `host_key`, `type`, `member_id`, `amount`, `dtm` FROM `dmgamelog`.`game_trade_err_log` WHERE `txn_id` IN ' + txn_id_list + 'AND `txn_id` NOT IN(SELECT `txn_id` FROM `dmgamelog`.`game_trade_log`))'
                hints = {}
                await MYPGuard.MYP("log").AsyncExec(sql=sMainSQL, hint=hints, callback=None)
                delete_list = []
                sMainSQL = '''DELETE FROM `dmgamelog`.`game_trade_err_log` WHERE '''
                hints = {}
                for i in range(len(resualt)):
                    delete_list.append(resualt[i]["txn_id"])
                    sMainSQL = sMainSQL + "`txn_id`='" + resualt[i]["txn_id"] + "'"
                    if i != len(resualt)-1:
                        sMainSQL = sMainSQL + " OR "
                sMainSQL = sMainSQL + ";;"
                await MYPGuard.MYP("log").AsyncExec(sql=sMainSQL, hint=hints, callback=None)

                resp["error_code"] = 0
                resp["msg"] = "success"
                resp["count"] = len(resualt)
                resp["txn_id_list"] = delete_list

        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRBanPlayer(ReqHandlerWrapper):  # ban玩家
    async def post(self):
        resp = {"error_code": -1, "msg": "error"}
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            type_id = self.GetBodyArgument("type")
            game_id = self.GetBodyArgument("game_id")
            player_list = self.GetBodyArgument("player_list", default = None)
            member_list = []
            rp = RDSPGuard.RP("game")
            # # 查詢多代理商開關
            # multi_host = 0
            # channel_res = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
            # if channel_res[0] == 0:
            #     chl_data = OnRedisResultParser(channel_res[1])
            #     ctm_data = json.loads(chl_data["extra"])
            #     if "multihost" in ctm_data:
            #         multi_host = ctm_data["multihost"]

            if int(type_id) == 0:  #查詢名單
                sMainSQL = '''SELECT `member_id` FROM `dmgame`.`ban_player` WHERE `apikey`= '%(host_api_key)s' AND `game_id`='%(game_id)s';;'''
                hints = {}
                sql = sMainSQL % {"host_api_key": host_api_key, "game_id": game_id}
                resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                resp["player_list"] = []
                if resualt:
                    for player in resualt:
                        member_list.append(player["member_id"])
                        resp["player_list"] = member_list
            elif int(type_id) == 1:  #新增名單
                sMainSQL = '''REPLACE INTO `dmgame`.`ban_player` (`apikey`, `game_id`, `member_id`) VALUES '''
                hints = {}
                for i in range(len(player_list)):
                    sMainSQL = sMainSQL + "(" + "'" + host_api_key + "'" + ',' + "'" + game_id + "'" + ',' + "'" + player_list[i] + "'" + ')'
                    acc = host_api_key + "_" + player_list[i]
                    uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", acc)
                    if uuid != None:
                        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                        if account_res[0] == 0:
                            account_base = db_data_user()
                            account_base.ParseFromString(account_res[1])
                            account_base.banned = 1
                            account_buffer = account_base.SerializeToString()
                            uuid = str(uuid.decode())
                            await rp.AsyncHelper.Exec("HSET", "sha@data_" + uuid, "base", account_buffer)
                    if i+1 != len(player_list):
                        sMainSQL = sMainSQL + " ,"
                sql = sMainSQL + ";;"
                await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)

                # if multi_host == 1:
                #     url = self.application.settings["multihost"]["service"] + "/banplayer"
                #     response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqMultiHostBanned, url,
                #                                                          host_api_key, type_id, game_id, player_list)

                resp["player_list"] = player_list
            elif int(type_id) == 2:  #刪除名單
                for player in player_list:
                    sMainSQL = '''DELETE FROM `dmgame`.`ban_player` WHERE member_id='%(member_id)s';'''
                    acc = host_api_key + "_" + player
                    uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", acc)
                    if uuid != None:
                        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                        if account_res[0] == 0:
                            account_base = db_data_user()
                            account_base.ParseFromString(account_res[1])
                            account_base.banned = 0
                            account_buffer = account_base.SerializeToString()
                            uuid = str(uuid.decode())
                            await rp.AsyncHelper.Exec("HSET", "sha@data_" + uuid, "base", account_buffer)
                    hints = {}
                    sql = sMainSQL % {"member_id": player}
                    await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                    # if multi_host == 1:
                    #     url = self.application.settings["multihost"]["service"] + "/banplayer"
                    #     response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqMultiHostBanned, url,
                    #                                                          host_api_key, type_id, game_id, player_list)

                resp["player_list"] = player_list
            resp["error_code"] = 0
            resp["msg"] = "success"

        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRVIPPlayer(ReqHandlerWrapper):  # VIP玩家
    async def post(self):
        resp = {"error_code": -1, "msg": "error"}
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            type_id = self.GetBodyArgument("type")
            game_id = self.GetBodyArgument("game_id")
            player_list = self.GetBodyArgument("player_list", default = None)

            rp = RDSPGuard.RP("game")
            # # 查詢多代理商開關
            # multi_host = 0
            # channel_res = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
            # if channel_res[0] == 0:
            #     chl_data = OnRedisResultParser(channel_res[1])
            #     ctm_data = json.loads(chl_data["extra"])
            #     if "multihost" in ctm_data:
            #         multi_host = ctm_data["multihost"]  # 多代理商開啟或關閉

            if int(type_id) == 0:  #查詢名單
                resp["player_list"] = []  # 準備傳送資料格式
                for i in player_list:
                    sMainSQL = '''SELECT `member_id` FROM `dmgame`.`VIP_player` WHERE `member_id`= '%(i)s' AND `apikey`= '%(host_api_key)s' AND `game_id`='%(game_id)s';;'''
                    hints = {}
                    sql = sMainSQL % {"i": i, "host_api_key": host_api_key, "game_id": game_id}
                    resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)

                    if resualt:  # 若有取得vip玩家
                        member_dict = {}
                        acc = host_api_key + "_" + resualt[0]["member_id"]  # 整理成rjitgkflnlk_owen99999
                        # 取得玩家uuid
                        uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", acc)

                        if uuid != None:
                            # 藉由uuid取得玩家account_base
                            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))

                            if account_res[0] == 0:
                                account_base = db_data_user()
                                account_base.ParseFromString(account_res[1])
                                loginTime = GetServerTimeFromIntToStr(account_base.lastlogintime)  # 轉換時間
                                logOutTime = GetServerTimeFromIntToStr(account_base.lastlogouttime)  # 轉換時間
                                member_dict.update({"memberID": resualt[0]["member_id"]})  # 玩家名稱
                                member_dict.update({"loginTime": loginTime})  # 登入時間
                                member_dict.update({"logoutTime": logOutTime})  # 登出時間
                                member_dict.update({"ipAddress": account_base.ip_address})  # 玩家位址
                                resp["player_list"].append(member_dict)  # 加入回傳給後臺

            elif int(type_id) == 1:  #新增名單
                sMainSQL = '''REPLACE INTO `dmgame`.`VIP_player` (`apikey`, `game_id`, `member_id`) VALUES '''
                hints = {}
                for i in range(len(player_list)):
                    sMainSQL = sMainSQL + "(" + "'" + host_api_key + "'" + ',' + "'" + game_id + "'" + ',' + "'" + player_list[i] + "'" + ')'
                    acc = host_api_key + "_" + player_list[i]
                    uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", acc)
                    if uuid != None:
                        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                        if account_res[0] == 0:
                            account_base = db_data_user()
                            account_base.ParseFromString(account_res[1])
                            account_base.VIP = 1
                            account_buffer = account_base.SerializeToString()
                            uuid = str(uuid.decode())
                            await rp.AsyncHelper.Exec("HSET", "sha@data_" + uuid, "base", account_buffer)
                    if i+1 != len(player_list):
                        sMainSQL = sMainSQL + " ,"
                sql = sMainSQL + ";;"
                await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                resp["player_list"] = player_list
                # 新增VIP_player資料表的同時，新增vip_log資料表至dmgamelog資料庫
                sMainSQL2 = '''INSERT INTO `dmgamelog`.`vip_log` (`apikey`, `game_id`, `member_id`, `add_time`) VALUES '''
                hints = {}
                for i in range(len(player_list)):
                    sMainSQL2 = sMainSQL2 + "(" + "'" + host_api_key + "'" + ',' + "'" + game_id + "'" + ',' + "'" + \
                                player_list[i] + "'" + ',' + "'" + GetServerTimeStr() + "'" + ')'
                    if i + 1 != len(player_list):
                        sMainSQL2 = sMainSQL2 + " ,"
                sql2 = sMainSQL2 + ";;"
                await MYPGuard.MYP("log").AsyncExec(sql=sql2, hint=hints, callback=None)
                # if multi_host == 1:
                #     url = self.application.settings["multihost"]["service"] + "/vipplayer"
                #     response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqMultiHostVip, url,
                #                                                          host_api_key, type_id, game_id, player_list)
            elif int(type_id) == 2:  #刪除名單
                for player in player_list:
                    sMainSQL = '''DELETE FROM `dmgame`.`VIP_player` WHERE member_id='%(member_id)s';'''
                    acc = host_api_key + "_" + player
                    uuid = await rp.AsyncHelper.Exec("HGET", "sha@acc2uuid", acc)
                    if uuid != None:
                        account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
                        if account_res[0] == 0:
                            account_base = db_data_user()
                            account_base.ParseFromString(account_res[1])
                            account_base.VIP = 0
                            account_buffer = account_base.SerializeToString()
                            uuid = str(uuid.decode())
                            await rp.AsyncHelper.Exec("HSET", "sha@data_" + uuid, "base", account_buffer)
                    hints = {}
                    sql = sMainSQL % {"member_id": player}
                    await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                # if multi_host == 1:
                #     url = self.application.settings["multihost"]["service"] + "/vipplayer"
                #     response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqMultiHostVip, url,
                #                                                          host_api_key, type_id, game_id, player_list)
                resp["player_list"] = player_list
            resp["error_code"] = 0
            resp["msg"] = "success"

        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

# class HDRMultiHostScore(ReqHandlerWrapper): #多代理商分數同步redis
#     async def post(self):
#         resp = { "error_code" : -1,"msg": "error"  }
#         try:
#             uuid = str(self.GetBodyArgument("uuid"))
#             lastscoretime = self.GetBodyArgument("lastscoretime")
#             dailyprofit = self.GetBodyArgument("dailyprofit")
#             profit = self.GetBodyArgument("profit")
#             score = self.GetBodyArgument("score")
#             control_status = self.GetBodyArgument("control_status")
#             control_score = self.GetBodyArgument("control_score")
#             if not uuid:
#                 resp = {
#                     "error_code": 1,
#                     "msg": "uuid is empty"
#                 }
#             else:
#                 rp = RDSPGuard.RP("game")
#                 results = await rp.AsyncHelper.Exec("HGET", "sha@data_" + uuid, "base")
#                 # results = await rp.LibGrd.AsyncCall("common.GetInfoBySYS", *(uuid))
#                 if results is None:
#                     resp = {
#                         "error_code": 3,
#                         "msg": "account_base is empty"
#                     }
#                 else:
#                     account_base = db_data_user()
#                     account_base.ParseFromString(results)
#                     account_base.lastscoretime = lastscoretime
#                     account_base.dailyprofit = dailyprofit
#                     account_base.profit = profit
#                     account_base.score = score
#                     account_base.control_status = control_status
#                     account_base.control_score = control_score
#                     account_base_ss = account_base.SerializeToString()
#                     rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_base_ss))
#                     resp["error_code"] = 0
#                     resp["msg"] = "success"
#         except:
#             PrintEXC()
#         self.set_header('Content-Type', 'application/json; charset=UTF-8')
#         self.write(json.dumps(resp))
#         self.flush()
#         self.finish()

class HDRGameServerList(ReqHandlerWrapper): #gameserver 設定值與路徑
    async def post(self):
        resp = { "error_code" : -1,"msg": "error"  }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")  # 多代理商服務器代號
            user_type = self.GetBodyArgument("user_type", default=0)  # 0正常現金玩家；1潛在信用玩家
            svr_list = ServListMgr.GetOptimalSvrByHostApiKey(host_api_key)
            servers = []
            for serv_data in svr_list:
                # 如果不是與付款種類相符的廳
                if token_credits_cash(user_type, serv_data) == False:
                    continue
                sMainSQL = '''SELECT `json_options` FROM `dmgame`.`cfg_gameroominfo` WHERE `host_api_key`= '%(host_api_key)s' AND `subgame_id`= '%(subgameid)s';;'''
                hints = {}
                sql = sMainSQL % {"host_api_key": host_api_key, "subgameid": serv_data.subgame_id}
                resualt = await MYPGuard.MYP("game").AsyncExec(sql=sql, hint=hints, callback=None)
                if resualt == None or resualt == ():
                    resp["status_code"] = 3
                    break
                else:
                    maxscore = eval(resualt[0]['json_options'])['max_score']
                servinfo = {}
                servinfo["subgame_id"] = serv_data.subgame_id
                servinfo["server_type"] = serv_data.server_type
                servinfo["addr"] = serv_data.server_addr.decode()
                servinfo["port"] = serv_data.server_port
                servinfo["cell"] = serv_data.cell_score
                servinfo["adm_score"] = serv_data.admission_score
                servinfo["max_player"] = serv_data.max_player
                servinfo["cur_player"] = serv_data.cur_player
                servinfo["max_score"] = maxscore
                servers.append(servinfo)
            if svr_list:
                resp["data"] = servers
                resp["error_code"] = 0
                resp["msg"] = "success"
            else:
                resp["error_code"] = -1
                resp["msg"] = "error"
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRHosturl(ReqHandlerWrapper): #Hosturl 設定值與路徑
    async def post(self):
        resp = { "error_code" : -1,"msg": "error"  }
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            rp = RDSPGuard.RP("game")
            # 錢包類型
            chl_resp = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
            if chl_resp[0] == 0:
                tmp = OnRedisResultParser(chl_resp[1])
                wallet_type = json.loads(tmp["extra"])["wallet_type"]
                if wallet_type == 0:
                    host_url = {
                        "rollout": self.application.settings["ps_urls"]["rollout"],
                        "getbalance": self.application.settings["ps_urls"]["getbalance"]
                    }
                    resp["data"] = host_url
                    resp["error_code"] = 0
                    resp["msg"] = "success"
                else:
                    host_url = rp.LibGrd.R.hget("sha@chl_" + host_api_key, "host_url")
                    host_url = json.loads(host_url.decode())
                    if host_url:
                        resp["data"] = host_url
                        resp["error_code"] = 0
                        resp["msg"] = "success"
                    else:
                        resp["error_code"] = -1
                        resp["msg"] = "error"
            else:
                resp["error_code"] = -1
                resp["msg"] = "error"
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRWalletType(ReqHandlerWrapper): #WalletType 設定值與路徑
    async def post(self):
        resp = { "error_code" : -1,"msg": "error"}
        try:
            host_api_key = self.GetBodyArgument("host_api_key")
            rp = RDSPGuard.RP("game")
            # 錢包類型
            chl_resp = rp.LibGrd.Call("channel.GetInfo", *(host_api_key,))
            if chl_resp[0] == 0:
                tmp = OnRedisResultParser(chl_resp[1])
                wallet_type = json.loads(tmp["extra"])["wallet_type"]
                resp["data"] = wallet_type
                resp["error_code"] = 0
                resp["msg"] = "success"
            else:
                resp["error_code"] = -1
                resp["msg"] = "error"
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

# class HDRGetIsGaming(ReqHandlerWrapper):  # 查詢多代理商服務的玩家是否遊戲中
#     async def post(self):
#         try:
#             multihost_uuid = self.GetBodyArgument("hostuuid")  # 接收多代理商服務的玩家uuid
#             if multihost_uuid is None:
#                 return False  # 沒有傳多代理服務的玩家uuid
#             rp = RDSPGuard.RP("game")
#             svr_id = await rp.AsyncHelper.Exec("HGET", "sha@data_" + str(multihost_uuid), "svr_id")
#             if svr_id != None or svr_id != -1 or svr_id != 999:
#                 return False  # 多代理服務的玩家已離開遊戲
#             else:
#                 return True  # 多代理服務的玩家遊戲中
#         except:
#             PrintEXC()

class HDRSingleChlHostUUID(ReqHandlerWrapper):  # 向自己的sha@data_取得ban與vip狀態回傳給多代理商服務
    async def post(self):
        resp = {"ban": None, "vip": None}
        try:
            hostuuid = self.GetBodyArgument("hostuuid")  # 接收到多代理商戶的玩家uuid
            rp = RDSPGuard.RP("game")
            # 向自己的redis取得base資料
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(hostuuid,))
            if account_res[0] == 0:
                account_base = db_data_user()
                account_base.ParseFromString(account_res[1])
                resp["ban"] = account_base.banned  # 回傳ban狀態
                resp["vip"] = account_base.VIP  # 回傳vip狀態
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRServerlist(ReqHandlerWrapper):  # 取得玩家遊戲狀態
    async def post(self):
        resp = {"svr_id": None}
        try:
            uuid = self.GetBodyArgument("uuid")  # 接收到來源商戶的玩家uuid
            rp = RDSPGuard.RP("game")
            svr_uuid = await rp.AsyncHelper.Exec("HGET", "sha@data_" + str(uuid), "svr_id")
            rplst = RDSPGuard.RP("gamelist")
            server_list_db = rplst.LibGrd.R.get("var@serverlist")
            server_list = get_game_server_list_ret()
            if server_list_db is not None and len(server_list_db) > 0:
                server_list.ParseFromString(server_list_db)
                for idx in range(len(server_list.gslist)):
                    # 走訪取得遊戲內的uuid，若與被踢除的玩家吻合
                    if server_list.gslist[idx].server_uuid == svr_uuid:
                        # svr_id = -1，不在遊戲中；svr_id = 0~5，正在遊戲桌
                        svr_id = server_list.gslist[idx].subgame_id
                        resp["svr_id"] = svr_id
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRMultiOnLogout(ReqHandlerWrapper):  # 多代理商與異常關閉時的OnLogout處理
    async def post(self):
        resp = {"status_code": -1, "msg": "error"}
        try:
            uuid = self.GetBodyArgument("hostuuid")  # 接收到多代理商戶的玩家uuid
            txn_id = "%.3d%.13d%.3d" % (GetRndInt(100, 999), GetServerTimeMS(), GetRndInt(100, 999))
            rp2 = RDSPGuard.RP("tradelist")
            set_list_success = await rp2.AsyncHelper.Exec("SETNX", "list@trade_" + str(uuid), txn_id)  # 新增人員
            if set_list_success == True:  # 寫入list@trade_成功，才走4分鐘流程
                await rp2.AsyncHelper.Exec("EXPIRE", "list@trade_" + str(uuid), 240)  # 設定4分鐘
            timeStamp = GetServerTimeStr()
            rollin = await rp2.AsyncHelper.Exec("get", "list@trade_" + str(uuid))
            if rollin is not None and str(json.loads(rollin)) != txn_id:
                resp["status_code"] = -10
                resp["msg"] = "Please confirm your account balance after 4 minutes."
            op = "in"  # 游戏转到PS
            # pre-borrowed balance to redis, fixed the online problem by Leo.
            rp = RDSPGuard.RP("game")
            account_base = db_data_user()
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            account_base.ParseFromString(account_res[1])
            balance = account_base.score
            Warn("--- HDRMultiOnLogout member_id=", account_base.sdk_uuid, " score=", balance,
                 " - balance=", balance)
            account_base.score -= balance
            account_buffer = account_base.SerializeToString()
            rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))

            # check score
            account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))
            account_base.ParseFromString(account_res[1])
            Warn("--- HDRMultiOnLogout check, member_id=", account_base.sdk_uuid, " score=",
                 account_base.score)

            # 錢包類型
            chl_resp = rp.LibGrd.Call("channel.GetInfo", *(account_base.channel,))
            if chl_resp[0] == 0:
                tmp = OnRedisResultParser(chl_resp[1])
                host_name = tmp["name"]
            multi_inf = await rp.AsyncHelper.Exec("HGET", "multi@inf_" + account_base.channel, account_base.sin_channel)
            multi_inf = json.loads(multi_inf)
            wallet_type = 0
            if "host_url" in multi_inf.keys():
                wallet_type = 1

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
                # response = await self.application.AsyncGuard.DoAsync(RequestHelper.ReqRollIn, url, account_base.channel,
                #                                                     account_base.sdk_uuid, txn_id, balance)
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
                #     Warn("--- HDRMultiOnLogout Fail member_id=", account_base.sdk_uuid, " score=", balance, " + balance=", balance, " response=", response)
                #     account_base.score += balance
                #     account_buffer = account_base.SerializeToString()
                #     rp.LibGrd.Call("common.SetInfoBySYS", *(uuid, account_buffer))
                #     Warn("auto translate error : -6")

                await rp2.AsyncHelper.Exec("DEL", "list@trade_" + str(uuid))  # 刪除人員名單及時間戳

                # 写日志
                sqlp = MYPGuard.MYP("log")
                sql = sSqls["add_tradelog"]
                sqlp.Exec(sql=sql.GetSQL(params={"txn": txn_id,
                                                 "host": account_base.sin_channel,
                                                 "type": 0 if op == "in" else 1,
                                                 "memberid": account_base.sdk_uuid, "amount": balance,
                                                 "time": timeStamp}), callback=None)
            resp["status_code"] = 0
            resp["msg"] = "success"
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRSyncToken(ReqHandlerWrapper):  # 同步token至多代理商redis的sha@data_
    async def post(self):
        resp = {"status_code": -1, "msg": "error"}
        try:
            hostuuid = self.GetBodyArgument("hostuuid")  # 接收到多代理商戶的玩家uuid
            new_token = self.GetBodyArgument("new_token")  # 要同步至多代理商的token
            # 開始同步
            rp = RDSPGuard.RP("game")
            await rp.AsyncHelper.Exec("HSET", "sha@data_" + str(hostuuid), "token", new_token)
            resp["status_code"] = 0
            resp["msg"] = "success"
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRHostMainTain(ReqHandlerWrapper):  # 單代理商掛維護通知多代理商
    async def post(self):
        resp = {"error_code": -1, "msg": "error"}
        try:
            host_api_key = self.GetBodyArgument("host_api_key")  # 單代理商商戶
            multi_host_api_key = self.GetBodyArgument("multi_host_api_key")  # 多代理商商戶
            is_maintain = self.GetBodyArgument("is_maintain")  # 是否要0維護1不要維護
            # 查詢多代理商開關---
            multi_host = 0
            rp = RDSPGuard.RP("game")
            # 向sha@chl取得extra資訊
            channel_res = rp.LibGrd.Call("channel.GetInfo", *(multi_host_api_key,))
            if channel_res[0] == 0:
                chl_data = OnRedisResultParser(channel_res[1])
                ctm_data = json.loads(chl_data["extra"])
                if "multihost" in ctm_data:
                    multi_host = ctm_data["multihost"]
            if multi_host:  # 如果是多代理商
                if is_maintain == 1:  # 如果維護狀態啟動
                    rp = RDSPGuard.RP("gamelist")
                    # 將多代理商內需要維護的單代理商狀態，告知多代理商
                    await rp.AsyncHelper.Exec("set", "var@maintain_" + host_api_key, is_maintain)
                else:  # 如果沒有要維護
                    rp = RDSPGuard.RP("gamelist")
                    # 將多代理商內需要維護的單代理商狀態，告知多代理商
                    await rp.AsyncHelper.Exec("del", "var@maintain_" + host_api_key)

            resp["error_code"] = 0
            resp["msg"] = "success"
        except:
            PrintEXC()
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRWriteSlotGameAccounting(ReqHandlerWrapper):
    """寫轉錢記錄到 slot-game.accounting 表內

    因為在 game/attemper.py 無法用 async 所以透過 API 寫入假的資料
    確保可以順利寫入資料後拿到 sn 值
    """
    async def post(self):
        resp = {"status_code": -1, "msg": "error"}

        multi_inf = self.GetBodyArgument("multi_inf")
        host_id = self.GetBodyArgument("host_id")
        game_id = self.GetBodyArgument("game_id")
        subgame_id = self.GetBodyArgument("subgame_id")
        member_id = self.GetBodyArgument("member_id")

        try:
            sql = sSqls["insert_ps_db_accounting"]
            sqlp = MYPGuard.MYP(multi_inf["db_id"])

            data = {
                "machine_id": -1,
                "host_id": host_id,
                "host_level": 0,
                "begin_time": GetServerTimeStr(),
                "game_time": GetServerTimeStr(),
                "game_id": game_id,
                "subgame_id": subgame_id,
                "member_id": member_id,
                "init_cent": 0,
                "bet": 0,
                "denom": 1,
                "total_win": 0,
                "bonus_win": 0,
                "gamble_win": 0,
                "jackpot_win": 0,
                "game_data": "{}",
                "game_result": "{}",
                "end_cent": 0,
                "bonus": 0,
                "gamble": 0,
                "game_module": "0",
                "game_end": 0,
                "test_account": 0
            }

            result = await sqlp.AsyncExec(sql=sql.GetSQL(params=data))
            resp["status_code"] = 0
            resp["msg"] = "success"
            resp["result"] = result
        except:
            PrintEXC()

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRGetSlotGameAccountingSN(ReqHandlerWrapper):
    """取得 slot-game.accounting 表內尚未結束的 SN 值"""
    async def post(self):
        resp = {"status_code": -1, "msg": "error"}
        multi_inf = self.GetBodyArgument("multi_inf")
        host_id = self.GetBodyArgument("host_id")
        game_id = self.GetBodyArgument("game_id")
        subgame_id = self.GetBodyArgument("subgame_id")
        member_id = self.GetBodyArgument("member_id")

        try:
            sql = sSqls["get_ps_db_accounting_sn"]
            sqlp = MYPGuard.MYP(multi_inf["db_id"])

            data = {
                "host_id": host_id,
                "game_id": game_id,
                "subgame_id": subgame_id,
                "member_id": member_id,
            }

            result = await sqlp.AsyncExec(sql=sql.GetSQL(params=data))
            if len(result) != 0:  # 回傳會是 list
                resp["status_code"] = 0
                resp["msg"] = "success"
                resp["sn"] = result[0]["sn"]

        except:
            PrintEXC()

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRPsAskResultEx(ReqHandlerWrapper):  # PS向GS請求錯誤帳務處理，GS向共享第三方請求resultex
    async def post(self):
        resp = {"status_code": -1, "msg": "gs enter the except error"}  # gs例外錯誤
        try:
            member_id = self.GetBodyArgument("member_id")  # 玩家名稱
            txn_id = int(self.GetBodyArgument("txn_id"))  # 單號是accounting sn不是bet result txn_id
            total_win = int(self.GetBodyArgument("total_win"))  # 不是總贏分，而是結算完畢後，剩餘帶入內的金額，使用gold
            bonus_win = int(self.GetBodyArgument("bonus_win"))  # 免費遊戲贏分
            game_id = self.GetBodyArgument("game_id")  # 遊戲代號
            subgame_id = int(self.GetBodyArgument("subgame_id"))  # 廳房號碼
            ts = int(self.GetBodyArgument("ts"))  # 結帳時間(時間戳)
            betamt = int(self.GetBodyArgument("betamt"))  # 沒有抽水的tot的絕對值
            winamt = int(self.GetBodyArgument("winamt"))  # 獲勝且沒有抽水的tot + 獲勝且抽過水的tot，如果輸了，則統一為0

            gs_db_params = {
                "member_id": member_id,
                "gold": total_win,  # 不是總贏分，而是結算完畢後，剩餘帶入內的金額，使用gold
                "game_id": game_id,
                "subgame_id": subgame_id
            }
            # 先驗證ps請求gs的這筆，是否為遊戲錢包轉入共享錢包result失敗
            myp = MYPGuard.MYP("log")
            sql = sSqls["get_game_share_result_err_log"]
            query_results = await myp.AsyncExec(sql=sql.GetSQL(gs_db_params))

            if len(query_results) < 1:  # 沒資料，表示會員錢包正常
                resp["status_code"] = 10
                resp["msg"] = "do not need to ask to resultex"  # 會員交易正常，不需要向共享方請求resultex
            else:  # 有資料，表示會員錢包異常
                rp = RDSPGuard.RP("game")
                host_api_key = query_results[0]["host_api_key"]

                # 向redis讀取共享方請求之路徑
                host_url = rp.LibGrd.R.hget("sha@chl_" + host_api_key, "host_url")
                host_url = json.loads(host_url.decode())
                dl_url = host_url["base_url"] + "/" + host_url["resultex"]

                resultex_params = {
                    "member_id": member_id,
                    "txn_id": txn_id,
                    "total_win": total_win,
                    "bonus_win": bonus_win,
                    "game_id": game_id,
                    "subgame_id": subgame_id,
                    "ts": ts,
                    "betamt": betamt,
                    "winamt": winamt
                }
                # 正式向共享方請求resultex
                response_resultex = RequestHelper.DoGet(dl_url, resultex_params)

                if response_resultex:  # 廠商有回應
                    resp["status_code"] = response_resultex["status_code"]
                    if resp["status_code"] == 0:
                        resp["msg"] = "success"  # resultex成功

                        # 成功的話，把在game_share_result_err_log的資料刪了
                        myp = MYPGuard.MYP("log")
                        sql = sSqls["delete_game_share_result_err_log"]
                        await myp.AsyncExec(sql=sql.GetSQL(gs_db_params))

                    elif resp["status_code"] == 1:
                        resp["msg"] = "member_id is not exist"  # 會員名稱不存在
                    elif resp["status_code"] == 2:
                        resp["msg"] = "txn_id is failed"  # 單號不存在
                    else:
                        resp["msg"] = "vendors error is unknown"  # 廠商回應未知錯誤
                else:
                    resp["status_code"] = -2
                    resp["msg"] = "vendor do not respose any message"  # 廠商無回應
        except:
            PrintEXC()

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(resp))
        self.flush()
        self.finish()

class HDRPsAskResultEx(ReqHandlerWrapper):  # PS向GS請求錯誤帳務處理，GS向共享第三方請求resultex
    async def post(self):
        resp = {"status_code": -1, "msg": "gs enter the except error"}  # gs例外錯誤
        try:
            member_id = self.GetBodyArgument("member_id")  # 玩家名稱
            txn_id = int(self.GetBodyArgument("txn_id"))  # 單號是accounting sn不是bet result txn_id
            total_win = int(self.GetBodyArgument("total_win"))  # 不是總贏分，而是結算完畢後，剩餘帶入內的金額，使用gold
            bonus_win = int(self.GetBodyArgument("bonus_win"))  # 免費遊戲贏分
            game_id = self.GetBodyArgument("game_id")  # 遊戲代號
            subgame_id = int(self.GetBodyArgument("subgame_id"))  # 廳房號碼
            ts = int(self.GetBodyArgument("ts"))  # 結帳時間(時間戳)
            betamt = int(self.GetBodyArgument("betamt"))  # 沒有抽水的tot的絕對值
            winamt = int(self.GetBodyArgument("winamt"))  # 獲勝且沒有抽水的tot + 獲勝且抽過水的tot，如果輸了，則統一為0

            gs_db_params = {
                "member_id": member_id,
                "gold": total_win,  # 不是總贏分，而是結算完畢後，剩餘帶入內的金額，使用gold
                "game_id": game_id,
                "subgame_id": subgame_id
            }
            # 先驗證ps請求gs的這筆，是否為遊戲錢包轉入共享錢包result失敗
            myp = MYPGuard.MYP("log")
            sql = sSqls["get_game_share_result_err_log"]
            query_results = await myp.AsyncExec(sql=sql.GetSQL(gs_db_params))

            if len(query_results) < 1:  # 沒資料，表示會員錢包正常
                resp["status_code"] = 10
                resp["msg"] = "do not need to ask to resultex"  # 會員交易正常，不需要向共享方請求resultex
            else:  # 有資料，表示會員錢包異常
                rp = RDSPGuard.RP("game")
                host_api_key = query_results[0]["host_api_key"]

                # 向redis讀取共享方請求之路徑
                host_url = rp.LibGrd.R.hget("sha@chl_" + host_api_key, "host_url")
                host_url = json.loads(host_url.decode())
                dl_url = host_url["base_url"] + "/" + host_url["resultex"]

                resultex_params = {
                    "member_id": member_id,
                    "txn_id": txn_id,
                    "total_win": total_win,
                    "bonus_win": bonus_win,
                    "game_id": game_id,
                    "subgame_id": subgame_id,
                    "ts": ts,
                    "betamt": betamt,
                    "winamt": winamt
                }
                # 正式向共享方請求resultex
                response_resultex = RequestHelper.DoGet(dl_url, resultex_params)

                if response_resultex:  # 廠商有回應
                    resp["status_code"] = response_resultex["status_code"]
                    if resp["status_code"] == 0:
                        resp["msg"] = "success"  # resultex成功

                        # 成功的話，把在game_share_result_err_log的資料刪了
                        myp = MYPGuard.MYP("log")
                        sql = sSqls["delete_game_share_result_err_log"]
                        await myp.AsyncExec(sql=sql.GetSQL(gs_db_params))

                    elif resp["status_code"] == 1:
                        resp["msg"] = "member_id is not exist"  # 會員名稱不存在
                    elif resp["status_code"] == 2:
                        resp["msg"] = "txn_id is failed"  # 單號不存在
                    else:
                        resp["msg"] = "vendors error is unknown"  # 廠商回應未知錯誤
                else:
                    resp["status_code"] = -2
                    resp["msg"] = "vendor do not respose any message"  # 廠商無回應
        except:
            PrintEXC()

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(resp))
        self.flush()
        self.finish()