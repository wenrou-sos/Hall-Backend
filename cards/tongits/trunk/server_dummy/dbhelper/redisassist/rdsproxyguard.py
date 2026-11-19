from redisassist.redisproxy import *
from redisassist.utils import DebugLevel
import json

from data_struct_pb2 import db_data_user

class RDSProxyGuardError(Exception):
    pass

class RDSProxyGuard(object):
    sProxys = {}

    def __init__(self):
        raise RDSProxyGuardError("RDSProxyGuard无法被初始化！")

    @classmethod
    def LoadByFile(cls, path):
        cls.Clear()
        with open(path, "r") as hd:
            data = json.loads(hd.read())
            if "dbs" in data:
                dbs = data["dbs"]
                for key in dbs:
                    cfg = dbs[key]
                    rp = RedisProxy.LoadWithCfg(key, cfg)
                    if rp is not None:
                        cls.sProxys[key] = rp
                        Info("RDSProxyGuard.LoadByData sProxys Set: ", key)
                    else:
                        Warn("Not a valid redis cfg, key:", key)

        if len(cls.sProxys) < 1:
            return None

        return cls

    @classmethod
    def RP(cls, name):
        if name in cls.sProxys:
            return cls.sProxys[name]
        else:
            return None

    @classmethod
    def Dispose(cls, name):
        rp = cls.sProxys[name]
        if rp is not None:
            rp.CloseLibGuard()
            rp.ClosePubSub()
            cls.sProxys[name] = None

    @classmethod
    def Clear(cls):
        for name in cls.sProxys:
            rp = cls.sProxys[name]
            if rp is not None:
                rp.CloseLibGuard()
                rp.ClosePubSub()
        cls.sProxys = {}

    @classmethod
    def ProcWith(cls, proc_fun = print, rp_name = None, *argv, **kwargv):
        if rp_name is None:
            for name in cls.sProxys:
                proc_fun(cls.sProxys[name], *argv, **kwargv)
        else:
            if rp_name in cls.sProxys:
                proc_fun(cls.sProxys[rp_name], *argv, **kwargv)

    @classmethod
    def SetDebugLevel(cls, lv):
        DebugLevel.Set(lv)

class UserRP():
    """此物件主要處理玩家的資料"""
    rp = RDSProxyGuard.RP("game")  # service 伺服器的
    rplog = RDSProxyGuard.RP("gamelog")  # game 伺服器的

    @classmethod
    def load_init(cls):
        """載入 init

        RDSProxyGuard 物件在 UserRP 載入之前還沒有實例
        等實例之後再重新 init 一次，確保 rp 不會是 None
        """
        cls.rp = RDSProxyGuard.RP("game")
        cls.rplog = RDSProxyGuard.RP("gamelog")

    @classmethod
    def set_new_item_flag(cls, uuid, value):
        cls.rp.LibGrd.R.hset(f"sha@data_{uuid}", "new_item", value)

    @classmethod
    def get_new_item_flag(cls, uuid):
        res = cls.rp.LibGrd.R.hget(f"sha@data_{uuid}", "new_item")

        return int(res) if res else 0

    @classmethod
    def update_account_buffer(cls, uuid, account_buffer):
        """更新 account_base

        Args:
            uuid:
            account_base:
        """
        cls.rp.LibGrd.R.hset("sha@data_" + str(uuid), "base", account_buffer)

    @classmethod
    def get_host_name(cls, host_api_key):
        """取得 account_base 的 protobuf

        Args:
            host_api_key:

        Returns:
            None (沒有資料) 或 account_base 的 protobuf 物件
        """

        results = cls.rp.LibGrd.R.hget("sha@chl_" + str(host_api_key), "name")
        host_name = results.decode("UTF-8")

        return host_name

    @classmethod
    def get_account_base(cls, uuid):
        """取得 account_base 的 protobuf

        Args:
            uuid:

        Returns:
            None (沒有資料) 或 account_base 的 protobuf 物件
        """
        results = cls.rp.LibGrd.Call("common.GetInfoBySYS", *(uuid,))

        if not results or not results[1]:
            return None

        account_base = db_data_user()
        account_base.ParseFromString(results[1])

        return account_base

    @classmethod
    def get_uuid_by_acc(cls, host_api_key, member_id):
        acc = host_api_key + "_" + member_id
        acc_resp = cls.rp.LibGrd.Call("common.GenAcc", *(acc,))

        if acc_resp[0] != 0:
            return None  # 沒有這個玩家，是假帳號

        if acc_resp[1] != 1:
            return None  # 沒有這個玩家，是假帳號

        account_base = db_data_user()
        account_base.ParseFromString(acc_resp[2])
        return account_base.uuid  # 有這個玩家

    @classmethod
    def set_account_android(cls, subgameID, tableID, chairID, android_data, host_name):
        """設定機器人等級

        Arg:
            tableID (int):
            chairID (int):
            android_data (dict):

        """

        cls.rp.LibGrd.R.set("android@" + str(subgameID) + "_" + str(tableID) + "_" + str(chairID) + "_" + str(host_name),
                            json.dumps(android_data))

    @classmethod
    def get_account_android(cls, subgameID, tableID, chairID, host_name):
        """取得機器人等級

        Arg:
            tableID (int):
            chairID (int):

        """

        android_data = cls.rp.LibGrd.R.get("android@" + str(subgameID) + "_" + str(tableID) + "_" + str(chairID) + "_" + str(host_name))
        if android_data != None:
            return json.loads(android_data.decode())
        else:
            return None

    @classmethod
    def delete_account_android(cls, subgameID, tableID, chairID, host_name):
        """刪除機器人等級

        Arg:
            tableID (int):
            chairID (int):

        """

        cls.rp.LibGrd.R.delete("android@" + str(subgameID) + "_" + str(tableID) + "_" + str(chairID) + "_" + str(host_name))

    @classmethod
    def set_account_base(cls,account_base):
        account_buffer = account_base.SerializeToString()
        cls.rp.LibGrd.R.hset("sha@data_" + str(account_base.uuid), "base", account_buffer)

class EventRP():
    """此物件主要處理活動相關的資料"""
    rp = RDSProxyGuard.RP("game") # service 伺服器的
    rplog = RDSProxyGuard.RP("gamelog") # game 伺服器的
    event_name = "songkran"
    point_limit = 2000
    total_point_limit = 42000

    room_lottery_ticket_dc = {
        "0": 1,
        "1": 5,
        "2": 15,
        "3": 20,
        "4": 20,
        "5": 20,
        "6": 1,
        "7": 5,
        "8": 15,
        "9": 20,
        "10": 20,
        "11": 20,
    }

    @classmethod
    def load_init(cls):
        """載入 init

        RDSProxyGuard 物件在 EventRP 載入之前還沒有實例
        等實例之後再重新 init 一次，確保 rp 不會是 None
        """
        cls.rp = RDSProxyGuard.RP("game")
        cls.rplog = RDSProxyGuard.RP("gamelog")
        cls.event_name = "songkran"
        cls.point_limit = 2000

    @classmethod
    def get_event_data(cls, uuid, key=""):
        """取得玩家活動相關資料

        回傳全部資料或者某個 key 的資料

        Args:
            uuid (int): 玩家 uuid
            key (str): key 的值

        Returns:
            dict: 玩家活動資料，若沒有資料則回傳 {}
            : 根據 key 回傳資料
        """
        event_data = cls.rp.LibGrd.R.hget(f"sha@data_{uuid}", "event")

        if not event_data:
            return {}

        result = json.loads(event_data.decode())

        if key:
            return result.get(key, "")

        return result

    @classmethod
    def get_login_data(cls, uuid):
        """取得登入活動所需資料

        Args:
            uuid (int): 玩家 uuid

        Returns:
            dict:
                Examples:
                    {
                        "login_time": 1643074625, # 上次更新的登入時間點
                        "continue_login_day": 3,
                        "has_award": 0,
                        "reset_point_in_game": 0 # 是否在遊戲中重製點數過
                    }
        """
        event_dc = cls.get_event_data(uuid)

        if len(event_dc) == 0:
            return None

        return {
            "login_time": event_dc.get("login_time", 0),
            "continue_login_day": event_dc.get("continue_login_day", 0),
            "has_award": event_dc.get("has_award", 0),
            "reset_point_in_game": event_dc.get("reset_point_in_game", 0),
        }

    @classmethod
    def get_event_item(cls, uuid):
        """取得玩家擁有的活動道具

        Args:
            uuid:

        Returns:
            dict:
                Examples:
                    {
                        "photo": [...], # 頭像
                        "frame": [...], # 頭框
                        "designation": [...], # 稱號
                        "card_style": [...] # 撲克牌樣式
                    }
        """
        """
        photo_item = {
            "活動名稱": [道具...],
            "活動名稱": [道具...],
        }
        """
        photo_data = cls.rp.LibGrd.R.hget(f"sha@data_{uuid}", "photo_item")
        frame_data = cls.rp.LibGrd.R.hget(f"sha@data_{uuid}", "frame_item")
        designation_data = cls.rp.LibGrd.R.hget(f"sha@data_{uuid}", "designation_item")
        card_style_data = cls.rp.LibGrd.R.hget(f"sha@data_{uuid}", "card_style_item")

        # 如果 redis 回傳 None 給 []，不然就解析成 dict，給 key=songkran 的串列
        photo_ls = json.loads(photo_data.decode()).get(cls.event_name) if photo_data else []
        frame_ls = json.loads(frame_data.decode()).get(cls.event_name) if frame_data else []
        designation_ls = json.loads(designation_data.decode()).get(cls.event_name) if designation_data else []
        card_style_ls = json.loads(card_style_data.decode()).get(cls.event_name) if card_style_data else []

        return {
            "photo": photo_ls,
            "frame": frame_ls,
            "designation": designation_ls,
            "card_style": card_style_ls
        }

    @classmethod
    def get_task_info(cls, uuid):
        """取得任務列表要顯示的資料

        Args:
            uuid:

        Returns:
            dict:
                Examples:
                    {
                       "daily_point":  60,
                       "task":  {
                            "dummy":  0,
                            "one_turn_dummy":  3,
                            "lay_off":  6,
                            "play_game":  4,
                            "win_gold_card":  0
                      },
                       "remain_point":  60,
                       "total_point":  60
                    }
        """
        event_dc = cls.get_event_data(uuid)
        task_dc = event_dc.get("task", {})

        output_task_dc = {
            "dummy": task_dc.get("dummy", 0),
            "one_turn_dummy": task_dc.get("one_turn_dummy", 0),
            "lay_off": task_dc.get("lay_off", 0),
            "play_game": task_dc.get("play_game", 0),
            "win_gold_card": task_dc.get("win_gold_card", 0)
        }

        return {
            "task": output_task_dc,
            "total_point": event_dc.get("total_point", 0),
            "remain_point": event_dc.get("remain_point", 0),
            "daily_point": event_dc.get("daily_point", 0)
        }

    @classmethod
    def get_remain_point(cls, uuid):
        """取得玩家剩餘點數

        Args:
            uuid:

        Returns:
            int: 剩餘的錢，沒錢或沒欄位就回傳 0
        """
        remain_point = cls.get_event_data(uuid, "remain_point")

        return remain_point if remain_point else 0 # 可能沒有這個值

    @classmethod
    def get_login_list(cls):
        """取得活動期間登入玩家列表

        Returns:
            list: [10039, 10040, ...]
        """
        results = cls.rp.LibGrd.R.hgetall(f"sha@login_during_event")

        output_ls = []

        # redis 中的資料格式是 byte 將其轉為 int
        for res in results.items():
            if res[0].isdigit() and res[1].isdigit():
                output_ls.append(int(res[0])) # res[0], res[1] 會是一樣的

        return output_ls

    @classmethod
    def update_event_data(cls, uuid, data, hostuuid=None, host_api_key=None, sub_game_id=None):
        """更新 event 資料

        Args:
            uuid:
            data (dict): 活動事件的資料
            hostuuid (int): 玩家在多代理商的 uuid
            host_api_key (str): 多代理商的 api_key
            sub_game_id (str): 要同步到單代理的遊戲
        """
        cls.rp.LibGrd.R.hmset(f"sha@data_{uuid}",
                               {"event": json.dumps(data)})

        if hostuuid != None:  # 若遊戲為多代理商模式
            publish_data = {"fnc": "AccountEvent", "type": "AccountEvent",
                            "data": {"uuid": hostuuid, "event": data}}
            # 將redis event同步至單代理商
            cls.rplog.LibGrd.R.publish(
                host_api_key + "_" + str(sub_game_id),
                json.dumps(publish_data))

    @classmethod
    def update_login_data(cls, uuid, login_time, login_day, has_award):
        """更新登入時間 & 連續登入天數 & 是否獲得獎勵 & 在遊戲中是否重製點數

        Args:
            uuid:
            login_time (int): 獲得登入獎勵的時間戳
            login_day (int): 連續登入天數
            has_award (int): 1 代表已經獲得獎勵了
        """
        event_dc = cls.get_event_data(uuid)
        event_dc["login_time"] = login_time
        event_dc["continue_login_day"] = login_day
        event_dc["has_award"] = has_award
        event_dc["reset_point_in_game"] = 0

        cls.update_event_data(uuid, event_dc)

    @classmethod
    async def update_two_times_date(cls, host_api_key, json_data):
        """更新兩倍水球起始時間、修正中獎活動的起始與結束日期

        Args:
            host_api_key (str): 商戶 key
            json_data (dict): 要修改的資料，日期格式為 YYYY-MM-dd
        """

        # 執行寫入sha@chl_
        await cls.rp.AsyncHelper.Exec("HSET", "sha@chl_" + host_api_key, "json_data",
                            json_data)

    @classmethod
    def add_task_times(cls, uuid, data):
        """增加玩家達成任務的次數

        Args:
            uuid:
            data (dict): 任務次數記錄
                Examples:
                    {
                        "dummy":  0,
                        "one_turn_dummy":  0,
                        "lay_off":  3,
                        "play_game":  3,
                        "win_gold_card":  0
                    }
        """
        event_dc = cls.get_event_data(uuid)
        task_dc = event_dc.get("task")

        if not task_dc:
            event_dc["task"] = data

        else: # 相加
            for key in task_dc:
                task_dc[key] += data.get(key, 0)

            event_dc["task"] = task_dc

        cls.update_event_data(uuid, event_dc)

    @classmethod
    def add_event_item(cls, uuid, _type, item):
        """新增活動道具到指定類別

        若原本沒資料會新建

        Args:
            uuid:
            _type (str): photo、frame、designation、card_style 四種道具類別
            item (str): 道具代號
        """
        item_data = cls.rp.LibGrd.R.hget(f"sha@data_{uuid}", f"{_type}_item")

        if not item_data:
            result = {cls.event_name: [item]}

        else:
            result = json.loads(item_data.decode())
            item_ls = result.get(cls.event_name, [])
            item_ls.append(item)

            result[cls.event_name] = item_ls

        cls.rp.LibGrd.R.hmset(f"sha@data_{uuid}",
                               {f"{_type}_item": json.dumps(result)})

    @classmethod
    def reset_daily_point(cls, uuid):
        """重置每日獲得點數"""
        event_dc = cls.get_event_data(uuid)
        event_dc["daily_point"] = 0

        cls.update_event_data(uuid, event_dc)

    @classmethod
    def add_point(cls, uuid, point):
        """增加每日獲得點數、總共獲得點數、剩餘點數

        檢查是否超過每日上線

        Args:
            uuid:
            point (int): 增加的點數
        """
        event_dc = cls.get_event_data(uuid)

        is_over_daily_limit = event_dc.get("daily_point", 0) >= cls.point_limit
        # 因小工具暴力加水球可能會導致超過上限
        is_over_total_limit = event_dc.get("total_point", 0) >= cls.total_point_limit

        if is_over_daily_limit or is_over_total_limit:
            return

        is_exceeded_limit = event_dc.get("daily_point", 0) + point > cls.point_limit

        if is_exceeded_limit:
            tmp_point = cls.point_limit - event_dc.get("daily_point", 0)

            daily_point = cls.point_limit
            total_point = event_dc.get("total_point", 0) + tmp_point
            remain_point = event_dc.get("remain_point", 0) + tmp_point

        else:
            daily_point = event_dc.get("daily_point", 0) + point
            total_point = event_dc.get("total_point", 0) + point
            remain_point = event_dc.get("remain_point", 0) + point

        event_dc["daily_point"] = daily_point
        event_dc["total_point"] = total_point
        event_dc["remain_point"] = remain_point

        cls.update_event_data(uuid, event_dc)

    @classmethod
    def minus_point(cls, uuid, point):
        """扣掉剩餘的點數

        Args:
            uuid:
            point (int): 要扣掉的點數
        """
        event_dc = cls.get_event_data(uuid)
        remain_point = event_dc.get("remain_point", 0) - point

        # 避免有負值
        event_dc["remain_point"] = remain_point if remain_point > 0 else 0

        cls.update_event_data(uuid, event_dc)

    @classmethod
    def set_bonus(cls, uuid, bonus):
        """設定中獎者得到獎金

        Args:
            uuid:
            bonus (int): 獲得的獎金
        """
        event_dc = cls.get_event_data(uuid)
        event_dc["bonus"] = bonus
        event_dc["bonus_timestamp"] = int(time.time())

        cls.update_event_data(uuid, event_dc)

    @classmethod
    def set_shown_bonus(cls, uuid):
        """設定顯示過領取獎勵狀態"""
        event_dc = cls.get_event_data(uuid)
        event_dc["has_show_bonus"] = 1

        cls.update_event_data(uuid, event_dc)

    @classmethod
    def set_login_during_event(cls, uuid):
        """將玩家 uuid 存到活動期間登入資料表中"""
        cls.rp.LibGrd.R.hset(f"sha@login_during_event", uuid, uuid)

    @classmethod
    def update_date(cls, multi_host_api_key, host_api_key, json_data, sub_game_id):
        """更新 event 資料

        Args:
            uuid:
            data (dict): 活動事件的日期時間
        """

        if multi_host_api_key == None:  # 單代理商
            cls.rp.LibGrd.R.hmset(f"sha@chl_{host_api_key}",
                                   {"date": json.dumps(json_data)})
        else:  # 多代理商
            cls.rp.LibGrd.R.hmset(f"sha@chl_{multi_host_api_key}",
                                   {"date": json.dumps(json_data)})
            # 整理需要監聽的內容
            publish_data = {"fnc": "ChlDate", "type": "ChlDate",
                            "data": {"host_api_key": host_api_key, "date": json_data}}
            # 將redis event同步至單代理商
            cls.rplog.LibGrd.R.publish(
                host_api_key + "_" + str(sub_game_id),
                json.dumps(publish_data))

    @classmethod
    def set_chl_bonus(cls, host_api_key, first_prize=None, second_prize=None, special_prize=None):
        """寫入中獎名單與獎金至跑馬燈

        Args:
            uuid:
            bonus (int): 獲得的獎金
        """
        if first_prize != None:
            cls.rp.LibGrd.R.hmset(f"first@notice_{host_api_key}",
                                  {"ledmul": json.dumps(first_prize)})
        if second_prize != None:
            cls.rp.LibGrd.R.hmset(f"second@notice_{host_api_key}",
                                  {"ledmul": json.dumps(second_prize)})
        if special_prize != None:
            cls.rp.LibGrd.R.hmset(f"special@notice_{host_api_key}",
                                  {"ledmul": json.dumps(special_prize)})
