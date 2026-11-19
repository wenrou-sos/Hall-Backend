import datetime
from utils import *
from mysqlassist import MYPGuard
import json

class DBLogMgrInitError(Exception):
    pass

class DBLogMgr(object):
    sCacheLogs = {}        # <表名, []>

    def __init__(self):
        raise DBLogMgr("DBLogMgr无法被初始化")

    @classmethod
    def WriteLog(cls, col_name: str, jsonstr: str):
        try:
            if cls.sCacheLogs.get(col_name) == None:
                cls.sCacheLogs[col_name] = []
            sLogQueue = cls.sCacheLogs[col_name]
            sLogQueue.append(jsonstr)
        except:
            PrintEXC()

    @classmethod
    def OnEventWriteDBLogs(cls):
        try:
            log = MYPGuard.MYP("log")
            for col_name, sLogQueue in cls.sCacheLogs.items():
                if len(sLogQueue) > 0:
                    if "game_login_log" == col_name:
                        col_name += "_" + datetime.datetime.now().strftime('%Y%m%d')
                    sql = "INSERT INTO " + col_name + "(Log) VALUES"
                    for idx in range(len(sLogQueue)):
                        if idx == len(sLogQueue) - 1:
                            sql += ("('" + sLogQueue[idx] + "')")
                        else:
                            sql += ("('" + sLogQueue[idx] + "'),")
                    log.Exec(sql)
            cls.sCacheLogs.clear()
        except:
            PrintEXC()
