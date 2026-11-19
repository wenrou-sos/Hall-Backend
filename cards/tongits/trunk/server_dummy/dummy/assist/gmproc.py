
import asyncio
import json
import time
from redisassist import RDSPGuard
from mysqlassist import MYPGuard
from utils import *
from data_struct_pb2 import *

sRPGame = None
sRPGameList = None
sRPSubGame = None
sMYPGame = None

def ConfigRPRef():
    global sRPGame
    sRPGame = RDSPGuard.RP("game")
    #Info("初始化GM处理RPGame：", sRPGame)
    global sRPGameList
    sRPGameList = RDSPGuard.RP("gamelist")
    #Info("初始化GM处理RPGameList：", sRPGameList)
    global sRPSubGame
    sRPSubGame = RDSPGuard.RP("subgame")
    #Info("初始化GM处理RPSubGame：", sRPSubGame)
    global sMYPGame
    sMYPGame = MYPGuard.MYP("game")
    #Info("初始化GM处理MYPGame：", sMYPGame)

def GetProtoBaseData(ss_data):
    pb_base = db_data_user_account()
    pb_base.ParseFromString(ss_data)
    return pb_base

def GetProtoScoreData(ss_data):
    pb_score = db_data_user_score()
    pb_score.ParseFromString(ss_data)
    return pb_score

def GetProtoMailData(ss_data):
    return None

async def GetInfo(uid, t, need_base = 0, need_score = 0, need_mail = 0):
    result = None
    if t == 0:
        result = (await sRPGame.LibGrd.AsyncCall("common.GetInfoBySYS", *(uid, need_base, need_score, need_mail)))
    elif t == 1:
        result = (await sRPGame.LibGrd.AsyncCall("common.GetInfoByACC", *(uid, need_base, need_score)))
    elif t == 2:
        result = (await sRPGame.LibGrd.AsyncCall("common.GetInfoByPHO", *(uid, need_base, need_score)))
    elif t == 3:
        result = (await sRPGame.LibGrd.AsyncCall("common.GetInfoByGID", *(uid, need_base, need_score)))

    if result != None and result[0] == 0:
        if need_base == 1 and result[1] is None:
            Err("未找到Base数据：", uid, t)
            result[0] = -1000

        if need_score == 1 and result[2] is None:
            Err("未找到Score数据：", uid, t)
            result[0] -= 2000

    return result

async def ProcKick(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def ForbiddenLogin(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        s = int(data["s"])
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_base = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_base = GetProtoBaseData(query_results[1])
                pb_base.disable_login = s
                uuid = pb_base.uuid
                await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, pb_base.SerializeToString(), "0", "0"))
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def ModLoginPWD(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        pwd = data["pwd"]
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_base = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_base = GetProtoBaseData(query_results[1])
                pb_base.pwd = pwd.encode()
                uuid = pb_base.uuid
                await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, pb_base.SerializeToString(), "0", "0"))
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def ModBankPWD(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        pwd = data["pwd"]
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_score = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_score = GetProtoScoreData(query_results[2])
                pb_score.bank_pwd = pwd.encode()
                uuid = pb_score.uuid
                await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, "0", pb_score.SerializeToString(), "0"))
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def CancelDeviceBind(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_base = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_base = GetProtoBaseData(query_results[1])
                pb_base.device_id = "".encode()
                pb_base.device_pwd = "".encode()
                uuid = pb_base.uuid
                await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, pb_base.SerializeToString(), "0", "0"))
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def SetUserType(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        uk = int(data["uk"])
        ut = int(data["ut"])
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_base = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_base = GetProtoBaseData(query_results[1])
                pb_base.user_kind = uk
                pb_base.user_type = ut
                uuid = pb_base.uuid
                await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, pb_base.SerializeToString(), "0", "0"))
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def ModBankScore(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        score = data["sc"]
        direct = "drt" in data
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_score = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_score = GetProtoScoreData(query_results[2])
                if direct:
                    pb_score.score += score
                else:
                    pb_score.bank_score += score
                uuid = pb_score.uuid
                await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, "0", pb_score.SerializeToString(), "0"))
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def ModUserGID(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        gid = int(data["gid"])
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_base = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_base = GetProtoBaseData(query_results[1])
                old_gid = pb_base.game_id
                pb_base.game_id = gid
                uuid = pb_base.uuid
                ret = await sRPGame.LibGrd.AsyncCall("common.ModGIDBySYS", *(uuid, pb_base.SerializeToString(), old_gid, gid))
                if ret != 0:
                    msg = "modify failed!(%d)" % ret
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def SendNotice(data):
    try:
        notice = data["nt"]
        await sRPGame.AsyncHelper.Exec("PUBLISH", "sg_event", "2:" + json.dumps(notice))
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def GetOnlineUsers(data):
    try:
        uuid2sid = await sRPGame.AsyncHelper.Exec("HGETALL", "sha@uuid2sid")
        ret_data = {}
        if uuid2sid is not None:
            for uuid in uuid2sid:
                sid = uuid2sid[uuid].decode()
                uuid = uuid.decode()
                if uuid.isdigit():
                    ret_data[uuid] = int(sid)
        return json.dumps(ret_data)
    except:
        PrintEXC()
        return "exc"

def RollbackTradeAsyncHelper(hint, results):
    if len(results) < 1:
        hint["ret"] = None
    else:
        hint["ret"] = results[0]

def RollbackTradeAsyncHelper2(hint, results):
    if len(results) < 1:
        hint["ret"] = None
    else:
        cnt = results[0]["ROW_COUNT()"]
        if cnt != 0:
            hint["ret"] = cnt
        else:
            hint["ret"] = None

async def RollbackTrade(data):
    try:
        tn = data["tn"]
        tid = int(data["tid"])
        sql = "SELECT `Score`, `Tax`, `SelfUUID`, `TargetUUID` FROM `%s` WHERE `ID` = %d AND `Status` = 1" % (tn, tid)
        hint = {}
        sMYPGame.Exec(sql = sql, hint = hint, callback = RollbackTradeAsyncHelper)
        begin_time = time.time()
        while "ret" not in hint:
            if time.time() - begin_time > 5:
                return "internal timeout"
            await asyncio.sleep(0.02)
        query_results = hint["ret"]
        if query_results is None:
            return "can not find trade data"
        score = int(query_results["Score"])
        tax = int(query_results["Tax"])
        suuid = query_results["SelfUUID"]
        duuid = query_results["TargetUUID"]

        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(suuid, 0))
            if ret != 0:
                msg = "lock user1 failed!"
                break
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(duuid, 0))
            if ret != 0:
                msg = "lock user2 failed!"
                break

            await asyncio.sleep(1.5)

            query_results = await GetInfo(suuid, 0, need_score = 1)
            s_pb_score = None
            s_swap_bank = None
            if query_results[0] != 0:
                msg = "invalid uid1 or type1!"
                break
            else:
                s_pb_score = GetProtoScoreData(query_results[2])
                s_swap_bank = query_results[4]
                if s_swap_bank is None:
                    s_swap_bank = 0
                else:
                    s_swap_bank = int(s_swap_bank.decode())

            query_results = await GetInfo(duuid, 0, need_score = 1)
            d_pb_score = None
            d_swap_bank = None
            if query_results[0] != 0:
                msg = "invalid uid1 or type1!"
                break
            else:
                d_pb_score = GetProtoScoreData(query_results[2])
                d_swap_bank = query_results[4]
                if d_swap_bank is None:
                    d_swap_bank = 0
                else:
                    d_swap_bank = int(d_swap_bank.decode())

            '''
            s_swap_bank += score
            s_pb_score.bank_score += s_swap_bank
            s_swap_bank = 0
            '''

            d_cost = score - tax
            rec = {}
            if d_cost > d_swap_bank:
                rec["sb"] = d_swap_bank
                d_cost -= d_swap_bank
                d_swap_bank = 0
            else:
                rec["sb"] = d_cost
                d_swap_bank -= d_cost
                d_cost = 0

            if d_cost > d_pb_score.bank_score:
                rec["b"] = d_pb_score.bank_score
                d_cost -= d_pb_score.bank_score
                d_pb_score.bank_score = 0
            else:
                rec["b"] = d_cost
                d_pb_score.bank_score -= d_cost
                d_cost = 0

            if d_cost > d_pb_score.score:
                rec["s"] = d_pb_score.score
                d_cost -= d_pb_score.score
                d_pb_score.score = 0
            else:
                rec["s"] = d_cost
                d_pb_score.score -= d_cost
                d_cost = 0

            s_swap_bank += score - tax - d_cost
            s_pb_score.bank_score += s_swap_bank
            s_swap_bank = 0

            rec["r"] = d_cost

            sql = "UPDATE `%s` SET `Status` = -%d WHERE `ID` = %d AND `Status` = 1;;SELECT ROW_COUNT()" % (tn, d_cost, tid)
            new_hint = {}
            sMYPGame.Exec(sql = sql, hint = new_hint, callback = RollbackTradeAsyncHelper2)

            timeout = False
            begin_time = time.time()
            while "ret" not in new_hint:
                if time.time() - begin_time > 5:
                    timeout = True
                    break
                await asyncio.sleep(0.02)

            if timeout:
                msg = "internal timeout2"
                break

            if new_hint["ret"] is None:
                msg = "status conflict"
                break

            uuid = s_pb_score.uuid
            await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, "0", s_pb_score.SerializeToString(), "0"))
            await sRPGame.AsyncHelper.Exec("HSET", "sha@data_" + str(uuid), "bank", s_swap_bank)
            uuid = d_pb_score.uuid
            await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, "0", d_pb_score.SerializeToString(), "0"))
            await sRPGame.AsyncHelper.Exec("HSET", "sha@data_" + str(uuid), "bank", d_swap_bank)
            msg = rec

            break

        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(suuid, 0))
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(duuid, 0))
        return msg
    except:
        PrintEXC()
        return "exc"

def LoadGVerAsyncHelper(hint, results):
    ver = 1
    if len(results) > 0:
        ver = int(results[0]["Value1"])
    hint["ver"] = ver

async def LoadGVer(data):
    try:
        sql = "SELECT `Value1` FROM `cfg_data` WHERE `ID` = 99999"
        hint = {}
        sMYPGame.Exec(sql = sql, hint = hint, callback = LoadGVerAsyncHelper)
        begin_time = time.time()
        while "ver" not in hint:
            if time.time() - begin_time > 5:
                return "internal timeout"
            await asyncio.sleep(0.02)
        ver = hint["ver"]
        await sRPGameList.AsyncHelper.Exec("SET", "var@gver", ver)
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def ReloadConfig(data):
    try:
        await sRPGame.AsyncHelper.Exec("PUBLISH", "reloadcfg", "1")
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def QueryTotalScore(data):
    try:
        uuid_set = await sRPGame.AsyncHelper.Exec("HVALS", "sha@gid2uuid")
        total_score = 0
        total_trans = 0
        ignore = []
        for uuid in uuid_set:
            uuid = uuid.decode()
            data_key = "sha@data_" + uuid
            pair = await sRPGame.AsyncHelper.Exec("HMGET", data_key, "score", "bank")
            score = pair[0]
            bank = pair[1]
            if score is None or bank is None:
                ignore.append(uuid)
            else:
                bank = int(bank.decode())
                score_data = GetProtoScoreData(score)
                total_score = total_score + bank + score_data.score + score_data.bank_score
                total_trans += bank
        return { "total" : total_score, "trans" : total_trans, "ignore" : ignore }
    except:
        PrintEXC()
        return "exc"

async def UnBindAllDevice(data):
    try:
        dev_type = int(data["dt"])
        uuid_set = await sRPGame.AsyncHelper.Exec("HVALS", "sha@gid2uuid")
        total = 0
        exclude = 0
        ignore = []
        for uuid in uuid_set:
            uuid = uuid.decode()
            data_key = "sha@data_" + uuid
            base = await sRPGame.AsyncHelper.Exec("HGET", data_key, "base")
            if base is None:
                ignore.append(uuid)
            else:
                base_data = GetProtoBaseData(base)
                if dev_type == 0 or dev_type == base_data.device_type:
                    base_data.device_id = b''
                    base_data.device_pwd = b''
                    total += 1
                    await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, base_data.SerializeToString(), "0", "0"))
                else:
                    exclude += 1
        return { "total" : total, "exclude" : exclude, "ignore" : ignore }
    except:
        PrintEXC()
        return "exc"

async def ModPhone(data):
    try:
        uid = data["uid"]
        mod_acc = int(data["ma"])
        pho = int(data["pho"])
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, 0))
            if ret != 0:
                msg = "lock user failed!"
                break

            await asyncio.sleep(1.5)

            data_key = "sha@data_" + str(uid)
            base = await sRPGame.AsyncHelper.Exec("HGET", data_key, "base")
            if base is None:
                msg = "uuid is invalid!"
                break
            else:
                base_data = GetProtoBaseData(base)
                if base_data.phone == 0:
                    msg = "phone not bind!"
                    break
                old_pho = base_data.phone
                old_acc = base_data.account
                base_data.phone = pho
                ret = 0
                if mod_acc == 1:
                    base_data.account = str(pho).encode()
                    ret = await sRPGame.LibGrd.AsyncCall("common.ModPhoneBySYS", *(uid, base_data.SerializeToString(), old_pho, pho, old_acc))
                else:
                    ret = await sRPGame.LibGrd.AsyncCall("common.ModPhoneBySYS", *(uid, base_data.SerializeToString(), old_pho, pho, "0"))
                if ret != 0:
                    msg = "modify failed!(%d)" % ret
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, 0))
        return msg
    except:
        PrintEXC()
        return "exc"

async def KickAllToolUsers(data):
    try:
        await sRPGame.AsyncHelper.Exec("PUBLISH", "gm_proxy", "1")
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def SetUserAddr(data):
    try:
        uid = data["uid"]
        t = int(data["t"])
        addr = data["addr"]
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, t))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)
            query_results = await GetInfo(uid, t, need_base = 1)
            if query_results[0] != 0:
                msg = "invalid uid or type!"
            else:
                pb_base = GetProtoBaseData(query_results[1])
                pb_base.reg_addr = addr.encode()
                uuid = pb_base.uuid
                await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, pb_base.SerializeToString(), "0", "0"))
            break
        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, t))
        return msg
    except:
        PrintEXC()
        return "exc"

async def StateConfig(data):
    try:
        send = {
            "uuid" : data["uid"],
            "control_status" : data["st"],
            "control_score" : data["sc"]
        }
        await sRPGame.AsyncHelper.Exec("PUBLISH", "sg_event", "3:" + json.dumps(send))
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def ReloadSGCfg(data):
    try:
        await sRPGame.AsyncHelper.Exec("PUBLISH", "sg_event", "4:")
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def SetRank(data):
    try:
        send = {
            "uid_list" : data["us"]
        }
        await sRPGame.AsyncHelper.Exec("PUBLISH", "sg_event", "5:" + json.dumps(send))
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def ShutdownSG(data):
    try:
        send = {
            "sid_list" : data["ss"]
        }
        await sRPGame.AsyncHelper.Exec("PUBLISH", "sg_event", "6:" + json.dumps(send))
        return "ok"
    except:
        PrintEXC()
        return "exc"

async def CostUserScore(data):
    try:
        uid = data["uid"]
        sc = int(data["sc"])
        if sc < 1:
            return "invalid score " + str(sc)
        msg = "ok"
        while True:
            ret = await sRPGame.LibGrd.AsyncCall("common.LockUser", *(uid, 0))
            if ret != 0:
                msg = "lock user failed!"
                break
            await asyncio.sleep(1.5)

            query_results = await GetInfo(uid, 0, need_score = 1)
            pb_score = None
            swap_bank = None
            if query_results[0] != 0:
                msg = "invalid uid or type!"
                break
            else:
                pb_score = GetProtoScoreData(query_results[2])
                swap_bank = query_results[4]
                if swap_bank is None:
                    swap_bank = 0
                else:
                    swap_bank = int(swap_bank.decode())

            cost = sc
            rec = {}
            if cost > swap_bank:
                rec["sb"] = swap_bank
                cost -= swap_bank
                swap_bank = 0
            else:
                rec["sb"] = cost
                swap_bank -= cost
                cost = 0

            if cost > pb_score.bank_score:
                rec["b"] = pb_score.bank_score
                cost -= pb_score.bank_score
                pb_score.bank_score = 0
            else:
                rec["b"] = cost
                pb_score.bank_score -= cost
                cost = 0

            if cost > pb_score.score:
                rec["s"] = pb_score.score
                cost -= pb_score.score
                pb_score.score = 0
            else:
                rec["s"] = cost
                pb_score.score -= cost
                cost = 0

            rec["r"] = cost
            uuid = pb_score.uuid
            await sRPGame.LibGrd.AsyncCall("common.SetInfoBySYS", *(uuid, "0", pb_score.SerializeToString(), "0"))
            await sRPGame.AsyncHelper.Exec("HSET", "sha@data_" + str(uuid), "bank", swap_bank)
            msg = rec
            Info("消耗用户积分操作：", uuid, msg)
            break

        await sRPGame.LibGrd.AsyncCall("common.UnLockUser", *(uid, 0))
        return msg
    except:
        PrintEXC()
        return "exc"

async def SGExtendsOp(data):
    try:
        uuid = data["uid"]
        svr_id = int(data["sid"])
        jdata = data["d"]
        force = int(data.pop("foc", 0))
        svr_id = svr_id - svr_id % 10
        ret = await sRPSubGame.LibGrd.AsyncCall("ew_subgame.SaveExt", *(uuid, svr_id, jdata, force))
        if ret == -1:
            return "last command not be processed!"
        return "ok"
    except:
        PrintEXC()
        return "exc"

sGMOpKick         = 0
sGMOpFbdLogin     = 1
sGMOpModLoginPWD  = 2
sGMOpModBankPWD   = 3
sGMOpCanclDevBind = 4
sGMOpSetUserType  = 5
sGMOpModBankScore = 6
sGMOpModUserGID   = 7
sGMOpSendNotice   = 8
sGMOpOnlineUsers  = 9
sGMOpRollbackTrade = 10
sGMOpLoadGVer     = 11
sGMOpReloadConfig = 12
sGMOpQueryTotalSc = 13
sGMOpUnBindAllDev   = 14
sGMOpModPhone       = 15
sGMOpKickAllToolUsers = 16
sGMOpSetUserAddr  = 17
sGMStateConfig    = 18
sGMReloadSGCfg    = 19
sGMSetRank        = 20
sGMShutdownSG     = 21
sGMCostUserScore   = 22
sGMSGExtendsOp    = 23

sProc = {
    # sGMOpKick : ProcKick,
    # sGMOpFbdLogin : ForbiddenLogin,
    # sGMOpModLoginPWD : ModLoginPWD,
    # sGMOpModBankPWD : ModBankPWD,
    # sGMOpCanclDevBind : CancelDeviceBind,
    # sGMOpSetUserType : SetUserType,
    # sGMOpModBankScore : ModBankScore,
    # sGMOpModUserGID : ModUserGID,
    # sGMOpSendNotice : SendNotice,
    sGMOpOnlineUsers : GetOnlineUsers,
    # sGMOpRollbackTrade : RollbackTrade,
    # sGMOpLoadGVer : LoadGVer,
    # sGMOpReloadConfig : ReloadConfig,
    # sGMOpQueryTotalSc : QueryTotalScore,
    # sGMOpUnBindAllDev : UnBindAllDevice,
    # sGMOpModPhone : ModPhone,
    # sGMOpKickAllToolUsers : KickAllToolUsers,
    # sGMOpSetUserAddr : SetUserAddr,
    sGMStateConfig : StateConfig,
    sGMReloadSGCfg : ReloadSGCfg,
    sGMSetRank : SetRank,
    sGMShutdownSG : ShutdownSG,
    # sGMCostUserScore : CostUserScore,
    sGMSGExtendsOp : SGExtendsOp
}