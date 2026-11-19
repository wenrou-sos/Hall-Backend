from mysqlassist import MYPGuard
from dbexecution import sSqls

import json

class ServerMYP():
    myp = MYPGuard.MYP("game")
    face_member_lock_lv_list = []
    upgrade_threshold_list = []

    @classmethod
    async def load_init(cls):
        """載入 init

        MYProxyGuard 物件在 ServerMYP 載入之前還沒有實例
        等實例之後再重新 init 一次，確保 myp 不會是 None
        """
        cls.myp = MYPGuard.MYP("game")
        await cls.set_face_member_lock_lv_list()
        await cls.set_upgrade_threshold_list()

    @classmethod
    async def set_face_member_lock_lv_list(cls):
        if cls.face_member_lock_lv_list:
            return cls.face_member_lock_lv_list

        sql = sSqls["get_face_member_lock_lv_list"]

        query_result = await cls.myp.AsyncExec(sql=sql.GetSQL())
        data = json.loads(query_result[0].get('data'))

        cls.face_member_lock_lv_list = data.get('face_member_lock_lv', [])
        return cls.face_member_lock_lv_list

    @classmethod
    async def set_upgrade_threshold_list(cls):
        if cls.upgrade_threshold_list:
            return cls.upgrade_threshold_list

        sql = sSqls["get_upgrade_threshold_list"]

        query_result = await cls.myp.AsyncExec(sql = sql.GetSQL())
        data = json.loads(query_result[0].get('data'))

        cls.upgrade_threshold_list = data.get('upgrade_threshold', [])

        return cls.upgrade_threshold_list