
import json
from redisassist import RDSPGuard
from mysqlassist import MYPGuard
from dbexecution import sExeHandlers
from data_struct_pb2 import *
from utils import *

class DBTask(object):
    def __init__(self, redis_mark = None, mysql_mark = None, task_type = None):
        self.mRedisMark = redis_mark
        self.mMySQLMark = mysql_mark
        self.mTaskType = task_type

    @property
    def RedisMark(self):
        return self.mRedisMark

    @property
    def MySQLMark(self):
        return self.mMySQLMark

    @property
    def TaskType(self):
        return self.mTaskType

    def Proc(self, data, hint):
        return True

    def DoTask(self, rds_proxy, task_type, data, hint):
        ret = self.MakeTaskHint(rds_proxy, task_type, hint)
        if ret == 0:
            if isinstance(data, bytes):
                data = data.decode()
            Log("执行任务：", self)
            try:
                return self.Proc(data, hint)
            except:
                PrintEXC()
                hint["exc"] = 1
                self.Finish(hint)
                return False
        else:
            hint["forbidden"] = ret
            self.Finish(hint)
            return False

    def MakeTaskHint(self, rds_proxy, task_type, hint):
        if rds_proxy.Name != self.mRedisMark:
            Err("RedisProxy错误：", rds_proxy.Name, self.mRedisMark)
            return 1

        if task_type != self.mTaskType:
            Err("任务类型错误：", task_type, self.mTaskType)
            return 2

        if self.mTaskType not in sExeHandlers:
            Err("任务处理句柄不存在：", self.mTaskType)
            return 3

        myp = MYPGuard.MYP(self.mMySQLMark)
        if myp is None:
            Err("MySQLProxy不存在：", self.mMySQLMark)
            return 4

        r = rds_proxy.R
        exe_hd = sExeHandlers[self.mTaskType]

        hint["rp"] = rds_proxy
        hint["r"] = r
        hint["myp"] = myp
        hint["exe_hd"] = exe_hd
        return 0

    def Finish(self, hint, results = None):
        hint.pop("rp", None)
        hint.pop("r", None)
        hint.pop("myp", None)
        hint.pop("exe_hd", None)
        if "callback" in hint:
            cb = hint.pop("callback")
            cb(hint)
        else:
            Warn("未设置有效的结果回调：", self.mTaskType)

class DBSaveBaseTask(DBTask):
    sDataKeyPrefix = "sha@data_"
    sACCKey = "sha@acc2uuid"
    sBaseField = "base"
    def __init__(self):
        super().__init__(redis_mark = "game", mysql_mark = "game", task_type = "db_savebase")

    def Proc(self, data, hint):
        r = hint["r"]
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        if len(data) < 1:
            uuid_set = r.hvals(DBSaveBaseTask.sACCKey)
            hint["uuid_set"] = uuid_set
            hint["total_count"] = len(uuid_set)
            hint["saved"] = 0
            hint["next_batch"] = 0
            hint["ignore"] = []
            self.BatchSaveCallback(hint, None)
            return True
        else:
            int(data) # 检查参数是否为整数或者整数字符串
            ignore = []
            hint["total_count"] = 1
            hint["saved"] = 0
            hint["ignore"] = ignore
            data_key = DBSaveBaseTask.sDataKeyPrefix + data
            base_data = r.hget(data_key, DBSaveBaseTask.sBaseField)
            if base_data is None:
                ignore.append(data)
                self.Finish(hint)
            else:
                myp.Exec(sql = exe_hd.GetSQL(params = self.GetParams(base_data)), hint = hint, callback = self.SaveCallback)
            return True

    def BatchSaveCallback(self, hint, results):
        Log("批量保存基本信息回调！")
        total_count = hint["total_count"]
        next_batch = hint["next_batch"]
        saved = next_batch
        if saved == total_count:
            hint["saved"] = saved - len(hint["ignore"])
            hint.pop("uuid_set")
            hint.pop("next_batch")
            self.Finish(hint)
            return

        hint["saved"] = saved
        uuid_set = hint["uuid_set"]
        ignore = hint["ignore"]
        r = hint["r"]
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        batch_count = 128
        if saved + batch_count > total_count:
            batch_count = total_count - saved
        next_batch += batch_count
        hint["next_batch"] = next_batch
        sql_list = []
        for i in range(saved, next_batch):
            uuid = uuid_set[i]
            if isinstance(uuid, bytes):
                uuid = uuid.decode()
            data_key = DBSaveBaseTask.sDataKeyPrefix + uuid
            base_data = r.hget(data_key, DBSaveBaseTask.sBaseField)
            if base_data is None:
                ignore.append(uuid)
            else:
                sql_list.append(exe_hd.GetSQL(params = self.GetParams(base_data)))
        myp.Exec(sql = sql_list, hint = hint, callback = self.BatchSaveCallback)

    def SaveCallback(self, hint, results):
        Log("保存基本信息回调！")
        saved = hint["saved"]
        saved += 1
        hint["saved"] = saved
        if saved >= hint["total_count"]:
            self.Finish(hint)

    def GetParams(self, ss_data):
        pb_base = db_data_user()
        pb_base.ParseFromString(ss_data)

        params = {
            "uid"   : pb_base.uuid,
            "acc"   : pb_base.account,
            "chl"   : pb_base.channel,
            "cuid"  : pb_base.sdk_uuid,
            "plt"   : pb_base.source,
            "pft"   : pb_base.profit,
            "dpft"  : pb_base.dailyprofit,
            "lstst" : pb_base.lastscoretime,
            "cst"   : pb_base.control_status,
            "csc"   : pb_base.control_score,
            "rstr"  : pb_base.disable_login,
            "ex"    : pb_base.jsondata
        }
        return params

class DBLoadBaseTask(DBTask):
    sCountSQL = "SELECT COUNT(1) FROM `data_user`;;"
    sCountSQLKey = "COUNT(1)"
    sACCKey = "sha@acc2uuid"
    sDataKeyPrefix = "sha@data_"
    sBaseField = "base"
    sChlField = "channel"
    def __init__(self):
        super().__init__(redis_mark = "game", mysql_mark = "game", task_type = "db_loadbase")

    def Proc(self, data, hint):
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        if len(data) < 1:
            myp.Exec(sql = DBLoadBaseTask.sCountSQL, hint = hint, callback = self.CountCallback)
        else:
            int(data) # 检查参数是否为整数或者整数字符串
            hint["total_count"] = 1
            hint["loaded"] = 0
            params = {
                "start_index" : 0,
                "count" : 1,
                "cond" : "WHERE `ID` = " + data
            }
            myp.Exec(sql = exe_hd.GetSQL(params = params), hint = hint, callback = self.LoadCallback)

        return True

    def CountCallback(self, hint, results):
        Log("统计基本信息条目数回调！")
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        total_cnt = results[0][DBLoadBaseTask.sCountSQLKey]
        hint["loaded"] = 0
        hint["total_count"] = total_cnt

        if total_cnt < 1:
            self.Finish(hint)
        else:
            start_index = 0
            lc_per_times = 1000
            while start_index < total_cnt:
                if start_index + lc_per_times > total_cnt:
                    lc_per_times = total_cnt - start_index
                params = {
                    "start_index" : start_index,
                    "count" : lc_per_times,
                    "cond" : ""
                }
                myp.Exec(sql = exe_hd.GetSQL(params = params), hint = hint, callback = self.BatchLoadCallback)
                start_index += lc_per_times

    def BatchLoadCallback(self, hint, results):
        Log("批量读取基本信息回调！")
        r = hint["r"]
        for item in results:
            self.WriteToRedis(r, item)

        loaded = hint["loaded"]
        loaded += len(results)
        hint["loaded"] = loaded
        if loaded >= hint["total_count"]:
            self.Finish(hint)

    def LoadCallback(self, hint, results):
        Log("读取基本信息回调！")
        if len(results) > 0:
            self.WriteToRedis(hint["r"], results[0])
            loaded = hint["loaded"]
            loaded += 1
            hint["loaded"] = loaded
        else:
            Warn("未查询到有效的基本数据！")
        self.Finish(hint)

    def WriteToRedis(self, r, item):
        uid = item["id"]
        acc = item["account"]
        chl = item["channel"]
        cuid = item["chluuid"]
        plt = item["platform"]
        pft = item["profit"]
        dptf = item["dailyprofit"]
        lstst = item["lastscoretime"]
        cst = item["ctrlstatus"]
        csc = item["ctrlscore"]
        rstr = item["restriction"]
        ex = item["extra"]
        r.hset(DBLoadBaseTask.sACCKey, acc, uid)

        pb_base = db_data_user()
        pb_base.uuid = uid
        pb_base.account = acc
        pb_base.channel = chl
        pb_base.sdk_uuid = cuid
        pb_base.source = plt
        pb_base.profit = pft
        pb_base.dailyprofit = dptf
        pb_base.lastscoretime = lstst
        pb_base.control_status = cst
        pb_base.control_score = csc
        pb_base.disable_login = rstr
        pb_base.jsondata = ex
        ss_data = pb_base.SerializeToString()
        data_key = DBLoadBaseTask.sDataKeyPrefix + str(uid)
        r.hset(data_key, DBLoadBaseTask.sBaseField, ss_data)
        r.hset(data_key, DBLoadBaseTask.sChlField, chl)

class DBSaveChlTask(DBTask):
    sChlKeyPrefix = "sha@chl_"
    def __init__(self):
        super().__init__(redis_mark = "game", mysql_mark = "game", task_type = "db_savechl")

    def Proc(self, data, hint):
        rp = hint["rp"]
        r = hint["r"]
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        if len(data) < 1:
            chl_key_set = r.keys(DBSaveChlTask.sChlKeyPrefix + "*")

            hint["chl_key_set"] = chl_key_set
            hint["total_count"] = len(chl_key_set)
            hint["saved"] = 0
            hint["next_batch"] = 0
            hint["ignore"] = []
            self.BatchSaveCallback(hint, None, begin = True)
            return True
        else:
            ignore = []
            hint["total_count"] = 1
            hint["saved"] = 0
            hint["ignore"] = ignore
            data_list = rp.LibGrd.Call("ew_common.GetChannelInfo", data)
            if data_list[0] != 0:
                ignore.append(data)
                self.Finish(hint)
            else:
                params = self.GetParams(data_list)
                params["chl"] = data
                myp.Exec(sql = exe_hd.GetSQL(params = params), hint = hint, callback = self.SaveCallback)
            return True

    def BatchSaveCallback(self, hint, results, begin = False):
        Log("批量保存基本信息回调！")
        total_count = hint["total_count"]
        saved = hint["saved"]
        next_batch = hint["next_batch"]
        if not begin:
            saved += 1
            if saved == total_count:
                hint["saved"] = saved - len(hint["ignore"])
                hint.pop("chl_key_set")
                hint.pop("next_batch")
                self.Finish(hint)
                return
            hint["saved"] = saved
        if saved == next_batch:
            chl_key_set = hint["chl_key_set"]
            ignore = hint["ignore"]
            rp = hint["rp"]
            myp = hint["myp"]
            exe_hd = hint["exe_hd"]
            batch_count = 128
            if saved + batch_count > total_count:
                batch_count = total_count - saved
            next_batch += batch_count
            hint["next_batch"] = next_batch
            for i in range(saved, next_batch):
                chl_key = chl_key_set[i]
                if isinstance(chl_key, bytes):
                    chl_key = chl_key.decode()
                chl = chl_key.replace(DBSaveChlTask.sChlKeyPrefix, "")
                data_list = rp.LibGrd.Call("ew_common.GetChannelInfo", chl)
                if data_list[0] != 0:
                    ignore.append(chl)
                    saved += 1
                    continue
                params = self.GetParams(data_list)
                params["chl"] = chl
                myp.Exec(sql = exe_hd.GetSQL(params = params), hint = hint, callback = self.BatchSaveCallback)
            if saved == total_count:
                hint["saved"] = saved - len(hint["ignore"])
                hint.pop("chl_key_set")
                hint.pop("next_batch")
                self.Finish(hint)
            else:
                hint["saved"] = saved

    def SaveCallback(self, hint, results):
        Log("保存基本信息回调！")
        saved = hint["saved"]
        saved += 1
        hint["saved"] = saved
        if saved >= hint["total_count"]:
            self.Finish(hint)

    def GetParams(self, data_list):
        tmp = data_list[1]
        d = { tmp[i * 2].decode() : tmp[i * 2 + 1] for i in range(int(len(tmp) / 2))}
        params = {
            "nam"  : d["name"].decode(),
            "ak"   : d["apikey"].decode(),
            "st"   : int(d["status"]),
            "tr"   : int(d["totalreg"]),
            "svrs" : d["servers"].decode(),
            "ex"   : d["extra"].decode()
        }
        return params

class DBLoadChlTask(DBTask):
    sCountSQL = "SELECT COUNT(1) FROM `data_channel`;;"
    sCountSQLKey = "COUNT(1)"
    sChlKeyPrefix = "sha@chl_"
    sBaseField = "base"
    def __init__(self):
        super().__init__(redis_mark = "game", mysql_mark = "game", task_type = "db_loadchl")

    def Proc(self, data, hint):
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        if len(data) < 1:
            myp.Exec(sql = DBLoadChlTask.sCountSQL, hint = hint, callback = self.CountCallback)
        else:
            hint["total_count"] = 1
            hint["loaded"] = 0
            params = {
                "start_index" : 0,
                "count" : 1,
                "cond" : "WHERE `Channel` = '%s'" % data
            }
            myp.Exec(sql = exe_hd.GetSQL(params = params), hint = hint, callback = self.LoadCallback)

        return True

    def CountCallback(self, hint, results):
        Log("统计基本信息条目数回调！")
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        total_cnt = results[0][DBLoadChlTask.sCountSQLKey]
        hint["loaded"] = 0
        hint["total_count"] = total_cnt

        if total_cnt < 1:
            self.Finish(hint)
        else:
            start_index = 0
            lc_per_times = 1000
            while start_index < total_cnt:
                if start_index + lc_per_times > total_cnt:
                    lc_per_times = total_cnt - start_index
                params = {
                    "start_index" : start_index,
                    "count" : lc_per_times,
                    "cond" : ""
                }
                myp.Exec(sql = exe_hd.GetSQL(params = params), hint = hint, callback = self.BatchLoadCallback)
                start_index += lc_per_times

    def BatchLoadCallback(self, hint, results):
        Log("批量读取基本信息回调！")
        r = hint["r"]
        for item in results:
            self.WriteToRedis(r, item)

        loaded = hint["loaded"]
        loaded += len(results)
        hint["loaded"] = loaded
        if loaded >= hint["total_count"]:
            self.Finish(hint)

    def LoadCallback(self, hint, results):
        Log("读取基本信息回调！")
        if len(results) > 0:
            self.WriteToRedis(hint["r"], results[0])
            loaded = hint["loaded"]
            loaded += 1
            hint["loaded"] = loaded
        else:
            Warn("未查询到有效的基本数据！")
        self.Finish(hint)

    def WriteToRedis(self, r, item):
        chl = item["channel"]
        item["onlines"] = 0
        chl_key = DBLoadChlTask.sChlKeyPrefix + chl
        item.pop("channel", None)
        r.hmset(chl_key, item)

class DBSaveSGTask(DBTask):
    sSGKeyPrefix = "sha@sgjson_"
    def __init__(self):
        super().__init__(redis_mark = "subgame", mysql_mark = "game", task_type = "db_savesg")

    def Proc(self, data, hint):
        if len(data) < 1:
            self.ReadDataFromRedis(hint)
        else:
            pair = data.split("|")
            uuid = pair[0]
            svr_id = pair[1]
            if len(uuid) < 1:
                uuid = None
            else:
                int(uuid) # 检查参数是否为整数或者整数字符串
            if len(svr_id) < 1:
                svr_id = None
            else:
                int(svr_id) # 检查参数是否为整数或者整数字符串
            self.ReadDataFromRedis(hint, uuid = uuid, svr_id = svr_id)
        return True

    def ReadDataFromRedis(self, hint, uuid = None, svr_id = None):
        r = hint["r"]
        sg_key_set = None
        ignore = []
        hint["ignore"] = ignore
        if uuid is None:
            sg_key_set = r.keys(DBSaveSGTask.sSGKeyPrefix + "*")
            hint["total_count"] = len(sg_key_set)
            hint["saved"] = 0
        else:
            hint["total_count"] = 1
            hint["saved"] = 0
            sg_key = DBSaveSGTask.sSGKeyPrefix + uuid
            if r.exists(sg_key) != 0:
                sg_key_set = (sg_key, )
            else:
                ignore.append(uuid + "|" + (svr_id or ""))
                self.Finish(hint)
                return

        if svr_id is not None:
            hint["svr_id"] = svr_id

        hint["sg_key_set"] = sg_key_set
        hint["next_batch"] = 0
        self.BatchSaveCallback(hint, None, begin = True)

    def BatchSaveCallback(self, hint, results, begin = False):
        Log("批量保存游戏信息回调！")
        total_count = hint["total_count"]
        saved = hint["saved"]
        next_batch = hint["next_batch"]
        if not begin:
            saved += 1
            hint["saved"] = saved
            if saved == total_count:
                hint.pop("sg_key_set")
                hint.pop("next_batch")
                if "svr_id" in hint:
                    hint.pop("svr_id")
                self.Finish(hint)
                return
            hint["saved"] = saved
        if next_batch == saved:
            sg_key_set = hint["sg_key_set"]
            ignore = hint["ignore"]
            r = hint["r"]
            myp = hint["myp"]
            exe_hd = hint["exe_hd"]
            batch_count = 64
            if saved + batch_count > total_count:
                batch_count = total_count - saved
            next_batch += batch_count
            hint["next_batch"] = next_batch
            for i in range(saved, next_batch):
                sg_key = sg_key_set[i]
                if isinstance(sg_key, bytes):
                    sg_key = sg_key.decode()
                svr_id_2_jdata = None
                if "svr_id" in hint:
                    svr_id = hint["svr_id"]
                    jdata = r.hget(sg_key, svr_id)
                    svr_id_2_jdata = { svr_id : jdata }
                else:
                    svr_id_2_jdata = r.hgetall(sg_key)
                uuid = int(sg_key.split("_")[1])
                params = {
                    "uuid" : uuid
                }
                sql_comb = ""
                ignore = hint["ignore"]
                for svr_id in svr_id_2_jdata:
                    jdata = svr_id_2_jdata[svr_id]
                    if isinstance(svr_id, bytes):
                        svr_id = svr_id.decode()
                    if jdata is not None:
                        if isinstance(jdata, bytes):
                            jdata = jdata.decode()
                        try:
                            json.loads(jdata)
                        except:
                            Err("不是有效的Json数据：", jdata)
                            ignore.append(str(uuid) + "|" + svr_id)
                        else:
                            params["svr_id"] = int(svr_id)
                            params["json_data"] = jdata
                            sql_comb += exe_hd.GetSQL(params = params)
                    else:
                        ignore.append(str(uuid) + "|" + svr_id)
                if len(sql_comb) < 1:
                    saved += 1
                    continue
                myp.Exec(sql = sql_comb, hint = hint, callback = self.BatchSaveCallback)
            hint["saved"] = saved
            if saved == total_count:
                hint.pop("sg_key_set")
                hint.pop("next_batch")
                if "svr_id" in hint:
                    hint.pop("svr_id")
                self.Finish(hint)

class DBLoadSGTask(DBTask):
    sCountSQL = "SELECT COUNT(1) FROM `data_SubGameInfo` %(cond)s;;"
    sCountSQLKey = "COUNT(1)"
    sSGKeyPrefix = "sha@sgjson_"
    def __init__(self):
        super().__init__(redis_mark = "subgame", mysql_mark = "game", task_type = "db_loadsg")

    def Proc(self, data, hint):
        myp = hint["myp"]
        uuid = None
        svr_id = None
        if len(data) > 0:
            pair = data.split("|")
            uuid = pair[0]
            svr_id = pair[1]
            if len(uuid) < 1:
                uuid = None
            else:
                int(uuid) # 检查参数是否为整数或者整数字符串
            if len(svr_id) < 1:
                svr_id = None
            else:
                int(svr_id) # 检查参数是否为整数或者整数字符串

        hint["uuid"] = uuid
        hint["svr_id"] = svr_id

        params = {
            "cond" : self.GetCondStr(uuid = uuid, svr_id = svr_id)
        }

        myp.Exec(sql = DBLoadSGTask.sCountSQL % params, hint = hint, callback = self.CountCallback)

        return True

    def CountCallback(self, hint, results):
        Log("统计游戏信息条目数回调！")
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        total_cnt = results[0][DBLoadSGTask.sCountSQLKey]
        hint["loaded"] = 0
        hint["total_count"] = total_cnt

        if total_cnt == 0:
            hint.pop("uuid")
            hint.pop("svr_id")
            self.Finish(hint)
            return

        uuid = hint["uuid"]
        svr_id = hint["svr_id"]
        start_index = 0
        lc_per_times = 1000
        while start_index < total_cnt:
            if start_index + lc_per_times > total_cnt:
                lc_per_times = total_cnt - start_index
            params = {
                "start_index" : start_index,
                "count" : lc_per_times,
                "cond" : self.GetCondStr(uuid = uuid, svr_id = svr_id)
            }
            myp.Exec(sql = exe_hd.GetSQL(params = params), hint = hint, callback = self.BatchLoadCallback)
            start_index += lc_per_times

    def BatchLoadCallback(self, hint, results):
        Log("批量读取游戏信息回调！")
        r = hint["r"]
        for item in results:
            self.WriteToRedis(r, item)

        loaded = hint["loaded"]
        loaded += len(results)
        hint["loaded"] = loaded
        if loaded >= hint["total_count"]:
            hint.pop("uuid")
            hint.pop("svr_id")
            self.Finish(hint)

    def WriteToRedis(self, r, item):
        uuid = item["UUID"]
        svr_id = item["ServerID"]
        jdata = item["JsonData"]
        r.hset(DBLoadSGTask.sSGKeyPrefix + str(uuid), svr_id, jdata)

    def GetCondStr(self, uuid = None, svr_id = None):
        cond_group = []
        if uuid is not None:
            cond_group.append("`UUID` = " + uuid)
        if svr_id is not None:
            cond_group.append("`ServerID` = " + svr_id)

        if len(cond_group) > 0:
            return "WHERE " + " AND ".join(cond_group)
        else:
            return ""

class DBSaveOnlStatus(DBTask):
    sChlField = "channel"
    sSTField = "status"
    sTRField = "totalreg"
    sOnlField = "onlines"
    def __init__(self):
        super().__init__(redis_mark = "game", mysql_mark = "log", task_type = "db_save_onlstatus")

    def Proc(self, data, hint):
        data = int(data) # 检查参数是否为整数或者整数字符串
        r = hint["r"]
        myp = hint["myp"]
        exe_hd = hint["exe_hd"]
        chl_data_set = r.keys("sha@chl_*")
        valid_chls = []
        for chl_data in chl_data_set:
            status = int(r.hget(chl_data, DBSaveOnlStatus.sSTField))
            if status != 1:
                chl = chl_data.decode().split("_")[1]
                tr = int(r.hget(chl_data, DBSaveOnlStatus.sTRField))
                onl = int(r.hget(chl_data, DBSaveOnlStatus.sOnlField))
                valid_chls.append({ "tc" : tr, "gc" : onl, "chl" : chl, "t" : data })

        sql_list = []
        for chl_param in valid_chls:
            sql_list.append(exe_hd.GetSQL(params = chl_param))
        myp.Exec(sql = sql_list, hint = hint, callback = self.Finish)
        return True

sTaskInsList = [
    DBSaveBaseTask(),
    DBLoadBaseTask(),
    DBSaveChlTask(),
    DBLoadChlTask(),
    DBSaveSGTask(),
    DBLoadSGTask(),
    DBSaveOnlStatus()
]

sTaskProcs = {
    ins.TaskType : ins for ins in sTaskInsList
}

class TaskQueue(object):
    sTaskCache = {} # proxy_name : { "task_type1+':'+data1" : hint1, "task_type2+':'+data2" : hint2 }
    sQueue = []
    sTotalTask = 0
    sValidTask = 0

    @classmethod
    def Push(cls, rds_proxy_name, task_type, data, hint_data = None, immed = False): 
        # 默认值hint_data = dict()写法采用的引用机制，hint_data默认值永远引用的是同一个dict()
        # 可以理解为函数在解释过程中参数列表被隐式构造为一个函数辅助的list 和 dict，
        # list dict只会构造一次，如[rds_proxy_name, task_type, data] { "hint_data" : dict() }
        # 这样在不传入hint_data时，hint_data默认都是引用的同一个dict
        ''' 测试代码
        def Add(val, data = dict()):
            if "val" not in data:
                data["val"] = val
            else:
                tmp = data["val"]
                tmp += val
                data["val"] = tmp
            return data

        d1 = Add(10)
        d2 = Add(20)

        d1 = Add(1, data = d1)
        d2 = Add(1, data = d2)
        print(d1["val"])
        print(d2["val"])
        '''

        rp = RDSPGuard.RP(rds_proxy_name)
        if rp is None:
            Info("不存在对应的RedisProxy：", rds_proxy_name)
            return 1

        if task_type not in sTaskProcs:
            Info("不存在对应的TaskProc：", rds_proxy_name)
            return 2

        cls.sTotalTask += 1

        task_proc = sTaskProcs[task_type]
        hint_data = hint_data or {}
 
        if isinstance(data, bytes):
            data = data.decode()
        
        if immed:
            if not task_proc.DoTask(rp, task_type, data, hint_data):
                Info("任务处理失败：", rp, task_proc, task_type, data, hint_data)
                return 4
            else:
                cls.sValidTask += 1
                return 0
        else:
            tasks = None
            if rds_proxy_name not in cls.sTaskCache:
                tasks = set()
                cls.sTaskCache[rds_proxy_name] = tasks
            else:
                tasks = cls.sTaskCache[rds_proxy_name]

            key = task_type + ":" + data
            if key in tasks:
                Warn("已存在相同任务！", key)
                return 3
            else:
                exe_time = int(time.time()) + 1
                d = [key, rp, task_proc, hint_data, exe_time, tasks]
                cls.sQueue.append(d)
                tasks.add(key)
                return 0

    @classmethod
    def DoAllTask(cls, proc_cnt = 128):
        cnt = 0
        cur_time = GetServerTime()
        for d in cls.sQueue:
            exe_time = d[4]
            if exe_time < cur_time:
                key = d[0]
                rp = d[1]
                task_proc = d[2]
                hint = d[3]
                tasks = d[5]
                pair = key.split(":")
                task_type = pair[0]
                task_data = pair[1]
                if not task_proc.DoTask(rp, task_type, task_data, hint):
                    Info("任务处理失败：", rp, task_proc, task_type, task_data, hint)
                else:
                    cls.sValidTask += 1
                tasks.remove(key)

                cnt += 1
                if cnt >= proc_cnt:
                    break
            else:
                break
        if cnt > 0:
            cls.sQueue = cls.sQueue[cnt:]
        return cnt
