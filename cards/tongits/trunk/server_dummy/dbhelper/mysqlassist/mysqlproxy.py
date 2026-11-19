from mysqlassist.asynctask import AsyncDelegate
from mysqlassist.mysqlhandler import MySQLHandlerPool
from mysqlassist.utils import *
import json
import asyncio

class MySQLProxy(object):
    def __init__(self, name = "default", mysqlhdr_pool = None):
        self.mName = name
        self.mMySQLHDRPool = mysqlhdr_pool
        Log("MySQLProxy创建：", self.mName, self.mMySQLHDRPool)

    def IsEmpty(self):
        return True

    def Exec(self, sql = "", hint = None, callback = None):
        conn = self.mMySQLHDRPool.GetConnection()
        results = None
        if conn is not None:
            results = conn.Exec(sql)
            if hint is not None and callback is not None:
                callback(hint, results)
        else:
            Warn("可用连接数不足！")
        self.mMySQLHDRPool.ReleaseConnection(conn)
        return results

    def Update(self):
        pass

    async def AsyncUpdate(self):
        pass

class AsyncMySQLProxy(MySQLProxy):
    def __init__(self, name = "default", mysqlhdr_pool = None, queue_size = 128, sleep_time = 0.02, workers = 1):
        super().__init__(name = name, mysqlhdr_pool = mysqlhdr_pool)
        self.mDgtCount = workers
        self.mCounter = 0
        self.mDelegate = [
            AsyncDelegate(
                mysqlhdr_pool = mysqlhdr_pool,
                queue_size = queue_size,
                sleep_time = sleep_time
                ) for i in range(self.mDgtCount)
        ]
        for dgt in self.mDelegate:
            dgt.start()
        Log("MySQLProxy创建：", self.mName, self.mMySQLHDRPool, self.mDelegate)

    def IsEmpty(self):
        for dgt in self.mDelegate:
            if not dgt.IsEmpty:
                return False
        return True

    def Exec(self, sql = "", hint = None, callback = None):
        self.mDelegate[self.mCounter].PushTask(sql = sql, hint = hint, callback = callback)
        self.mCounter += 1
        self.mCounter %= self.mDgtCount

    def AsyncHelper(self, hint, results):
        hint["results"] = results

    async def AsyncExec(self, sql = "", hint = None, callback = None):
        pack_hint = { }
        self.mDelegate[self.mCounter].PushTask(sql = sql, hint = pack_hint, callback = self.AsyncHelper)
        self.mCounter += 1
        self.mCounter %= self.mDgtCount
        while "results" not in pack_hint:
            await asyncio.sleep(0.02)
        results = pack_hint["results"]
        if callback is not None:
            callback(hint, results)
        return results

    def Update(self):
        for dgt in self.mDelegate:
            dgt.Update()

    async def AsyncUpdate(self):
        if len(self.mDelegate) == 1:
            await self.mDelegate[0].AsyncUpdate()
        else:
            while True:
                for dgt in self.mDelegate:
                    dgt.Update()
                await asyncio.sleep(0.02)

class ProxyCreator(object):

    @classmethod
    def LoadWithCfg(cls, name, cfg):
        #cfg 異常檢查
        if ("host" not in cfg) or (cfg["host"] is None) or (not isinstance(cfg["host"], str)) or (len(cfg["host"]) == 0) or \
            ("password" not in cfg) or (cfg["password"] is None) or (not isinstance(cfg["password"], str)) or (len(cfg["password"]) == 0) or \
            ("database" not in cfg) or (cfg["database"] is None) or (not isinstance(cfg["database"], str)) or (len(cfg["database"]) == 0) or \
            ("port" not in cfg) or (cfg["port"] is None) or (not isinstance(cfg["port"], int)) or (cfg["port"] <= 0):

            Err("<连接池>配置：")
            Err(json.dumps(cfg, indent=4))
            return None

        proxy_class = MySQLProxy
        if "async_mode" in cfg:
            try:
                b = int(cfg["async_mode"]) != 0
                if b:
                    proxy_class = AsyncMySQLProxy
            except:
                pass
            cfg.pop("async_mode")

        queue_size = 1024
        if "queue_size" in cfg:
            try:
                queue_size = int(cfg["queue_size"])
            except:
                pass
            cfg.pop("queue_size")

        sleep_time = 0.02
        if "sleep_time" in cfg:
            try:
                sleep_time = float(cfg["sleep_time"])
            except:
                pass
            cfg.pop("sleep_time")

        workers = 1
        if "workers" in cfg:
            try:
                workers = int(cfg["workers"])
                if workers < 1:
                    workers = 1
            except:
                pass
            cfg.pop("workers")

        Info("<连接池>配置预览：")
        Info(json.dumps(cfg, indent = 4))
        pool = MySQLHandlerPool(**cfg)

        if proxy_class == MySQLProxy:
            return proxy_class(name = name, mysqlhdr_pool = pool)
        else:
            return proxy_class(name = name, mysqlhdr_pool = pool, queue_size = queue_size, sleep_time = sleep_time, workers = workers)
