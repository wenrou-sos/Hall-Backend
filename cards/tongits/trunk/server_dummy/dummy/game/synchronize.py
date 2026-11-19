import redis
import threading
import json
from dbexecution import sSqls
from mysqlassist import MYPGuard
from data_struct_pb2 import *
from google.protobuf.json_format import Parse
from redisassist import RDSPGuard

def synchronize_data(host, port, db, password, hostkey, subgame_id):
    rc = redis.StrictRedis(host=host, port=port, db=db, password=password)
    ps = rc.pubsub()
    ps.subscribe(hostkey + "_" + str(subgame_id))
    print("redis 監聽中", hostkey + "_" + str(subgame_id))
    for item in ps.listen():  # 监听状态：有消息发布了就拿过来
        if item['type'] == 'message':
            data = json.loads(item['data'].decode("UTF-8"))
            if data["fnc"] == "WriteTableLog":
                WriteTableLog(data)
            elif data["fnc"] == "TradeLog":
                TradeLog(data)
            elif data["fnc"] == "AccountBase":
                AccountBase(data)
            elif data["fnc"] == "AccountNewSvrID":
                AccountNewSvrID(data)
            elif data["fnc"] == "AccountDelSvrID":
                AccountDelSvrID(data)
            elif data["fnc"] == "AccountEvent":
                AccountEvent(data)
            elif data["fnc"] == "VipLog":
                VipLog(data)
            elif data["fnc"] == "VipPlayer":
                VipPlayer(data)
            elif data["fnc"] == "ChlDate":
                ChlDate(data)

def TradeLog(data):
    sqlp = MYPGuard.MYP("log")
    sql = sSqls[data["type"]]
    sqlp.Exec(sql=sql.GetSQL(params=data["data"]), callback=None)

def WriteTableLog(data):  # 写日志
    sqlp = MYPGuard.MYP("log")
    sql = sSqls["save_logs"]
    col = data["type"]
    sqlp.Exec(sql=sql.GetSQL(params={"col": col, "json_data":  json.dumps(data["data"])}))

def AccountBase(data):
    account_base = db_data_user()
    account_base = Parse(data["data"]["base"], account_base)
    account_base.hostuuid, account_base.uuid = account_base.uuid, account_base.hostuuid
    account_buffer = account_base.SerializeToString()
    rp = RDSPGuard.RP("game")
    rp.LibGrd.Call("common.SetInfoBySYS", *(data["data"]["uuid"], account_buffer))

def AccountNewSvrID(data):
    rp = RDSPGuard.RP("game")
    rp.LibGrd.R.hset("sha@data_" + str(data["data"]["uuid"]), "svr_id", str(data["data"]["svr_id"]))

def AccountDelSvrID(data):
    rp = RDSPGuard.RP("game")
    rp.LibGrd.R.hdel("sha@data_" + str(data["data"]["uuid"]), "svr_id")

def AccountEvent(data):
    rp = RDSPGuard.RP("game")
    rp.LibGrd.R.hmset("sha@data_" + str(data["data"]["uuid"]),
                      {"event": json.dumps(data["data"]["event"])})

def VipLog(data):
    sqlp = MYPGuard.MYP("log")
    sql = sSqls["save_vip_log"]
    col = data["type"]
    sqlp.Exec(sql=sql.GetSQL(params={"col": col, "apikey": data["data"]["apikey"], "game_id": data["data"]["game_id"], "member_id": data["data"]["member_id"], "add_time": data["data"]["add_time"]}))

def VipPlayer(data):
    sqlp = MYPGuard.MYP("game")
    sql = sSqls["save_vip_player"]
    col = data["type"]
    sqlp.Exec(sql=sql.GetSQL(params={"col": col, "apikey": data["data"]["apikey"], "game_id": data["data"]["game_id"], "member_id": data["data"]["member_id"]}))

def ChlDate(data):
    rp = RDSPGuard.RP("game")
    rp.LibGrd.R.hset("sha@chl_" + str(data["data"]["host_api_key"]), "date", json.dumps(data["data"]["date"]))
