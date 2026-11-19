
# Depend on Python 3.5.x +

import redis
import os
import socket
import json
import asyncio
from redisassist.utils import *
from copy import deepcopy

class PubSubProxyError(Exception):
    pass

class LibGuardError(Exception):
    pass

class RedisProxyError(Exception):
    pass

class AsyncRDSHelper(object):
    def __init__(self, rds_proxy = None, suspend_time = 1.0):
        self.mRdsProxy = rds_proxy
        self.mOriRedis = self.mRdsProxy.R
        self.mSuspendTime = suspend_time

    @property
    def Proxy(self):
        return self.mRdsProxy

    @property
    def R(self):
        return self.mOriRedis

    @property
    def SuspendTime(self):
        return self.mSuspendTime

    @SuspendTime.setter
    def SuspendTime(self, time):
        self.mSuspendTime = time

    async def Exec(self, cmd, *argv):
        conn = None

        while True:
            try:
                conn = self.mOriRedis.connection_pool.get_connection(cmd)
                break
            except:
                await asyncio.sleep(self.mSuspendTime)

        while True:
            try:
                conn.send_command(cmd, *argv)
                break
            except:
                PrintEXC()
                await asyncio.sleep(self.mSuspendTime)

        while not conn.can_read():
            await asyncio.sleep(self.mSuspendTime)

        response = None
        try:
            response = conn.read_response()
        except redis.ResponseError:
            PrintEXC()
            return response

        self.mOriRedis.connection_pool.release(conn)

        if cmd in self.mOriRedis.response_callbacks:
            return self.mOriRedis.response_callbacks[cmd](response)
        return response

class PubSubProxy(object):
    def __init__(self, rds_proxy = None):
        self.mRdsProxy = rds_proxy
        self.mOriRedis = self.mRdsProxy.R
        self.mPubSub = self.mOriRedis.pubsub()
        self.mAsyncHelper = self.mRdsProxy.AsyncHelper
        self.mOnPubMsgCB = None # def fun(pb_proxy, msg, ptn, chl, data)
        self.mAsyncRunning = False

    def __del__(self):
        if self.mPubSub is not None:
            self.mPubSub.close()

    @property
    def Proxy(self):
        return self.mRdsProxy

    @property
    def R(self):
        return self.mOriRedis

    @property
    def PubSub(self):
        return self.mPubSub

    @property
    def AsyncHelper(self):
        return self.mAsyncHelper

    @property
    def OnPubMsgCB(self):
        return self.mOnPubMsgCB

    @OnPubMsgCB.setter
    def OnPubMsgCB(self, cb):
        self.mOnPubMsgCB = cb

    @property
    def AsyncRunning(self):
        return self.mAsyncRunning

    @AsyncRunning.setter
    def AsyncRunning(self, b):
        self.mAsyncRunning = b

    @property
    def Subscribe(self):
        return self.mPubSub.subscribe

    @property
    def PSubscribe(self):
        return self.mPubSub.psubscribe

    @property
    def ClearSubcribe(self):
        self.mPubSub.unsubscribe

    @property
    def ClearPSubcribe(self):
        self.mPubSub.punsubscribe

    def Update(self):
        resp = self.mPubSub.get_message()
        while resp is not None:
            Log("收到订阅消息：", resp)
            handler = self.mOnPubMsgCB
            if handler is not None:
                ptn = resp["pattern"]
                chl = resp["channel"]
                if isinstance(ptn, bytes):
                    ptn = ptn.decode()
                if isinstance(chl, bytes):
                    chl = chl.decode()
                handler(self, resp["type"], ptn, chl, resp["data"])
            resp = self.mPubSub.get_message()

    async def AsyncUpdate(self):
        if self.mAsyncRunning:
            return
        self.mAsyncRunning = True
        while self.mAsyncRunning:
            resp = self.mPubSub.get_message()
            if resp is None:
                await asyncio.sleep(self.mAsyncHelper.SuspendTime)
                continue
            Log("收到订阅消息：", resp)
            handler = self.mOnPubMsgCB
            if handler is not None:
                ptn = resp["pattern"]
                chl = resp["channel"]
                if isinstance(ptn, bytes):
                    ptn = ptn.decode()
                if isinstance(chl, bytes):
                    chl = chl.decode()
                handler(self, resp["type"], ptn, chl, resp["data"])

class LibGuard(PubSubProxy):
    def __init__(self, rds_proxy = None, preload = False, libs = None, dynamic_update = False, update_hint = None):
        super().__init__(rds_proxy = rds_proxy)
        self.mScripts = {} # 库名：{ 脚本名 : 脚本哈希值 }
        self.mLibs = []
        self.mDynamicUpdate = False
        self.mUpdateHint = None

        if preload:
            if not self.Preload(libs):
                raise LibGuardError("预加载库失败：", libs)
            else:
                self.mLibs = [lib for lib in libs]

        if dynamic_update and isinstance(update_hint, str):
            if self.mPubSub is None:
                raise LibGuardError("库更新监控启动失败：", self.mPubSub)

            self.OnPubMsgCB = self.OnLibUpdate
            self.Subscribe(*(update_hint,))
            self.mDynamicUpdate = dynamic_update
            self.mUpdateHint = update_hint

    @property
    def Libs(self):
        return self.mLibs

    @property
    def DynamicUpdate(self):
        return self.mDynamicUpdate

    @property
    def UpdateHint(self):
        return self.mUpdateHint

    def Preload(self, libs):
        if self.mPubSub is None:
            return False
        if self.mOriRedis is None:
            return False
        try:
            for lib in libs:
                Log("lib@" + lib)
                val = self.mOriRedis.get("lib@" + lib)
                if val is None:
                    continue
                if isinstance(val, bytes):
                    val = val.decode()
                if len(val) > 0:
                    pairs = val.split("|")
                    scs = {}
                    for pair in pairs:
                        val_pair = pair.split(":")
                        scs[val_pair[0]] = val_pair[1]
                    self.mScripts[lib] = scs
                else:
                    self.mScripts[lib] = {}
            Info("库预览：")
            Info(json.dumps(self.mScripts, indent = 4))
            return True
        except:
            PrintEXC()
            return False

    def OnLibUpdate(self, caller, msg, ptn, chl, data):
        if caller != self:
            Log("Caller <=> Self", caller, self)
            return
        if chl == self.mUpdateHint and msg == "message":
            Log("收到库更新通知！")
            try:
                if isinstance(data, bytes):
                    data = data.decode()
                if data.startswith("lib@"):
                    data = data[4:]
                    pair = data.split("/")
                    lib_name = pair[0]
                    if lib_name in self.mScripts:
                        if len(pair[1]) > 0:
                            vals = pair[1].split("|")
                            scs = {}
                            for val in vals:
                                val_pair = val.split(":")
                                scs[val_pair[0]] = val_pair[1]
                            self.mScripts[lib_name] = scs
                            Info("库预览：")
                            Info(json.dumps(self.mScripts, indent = 4))
                            Info("库更新完成：", lib_name)
            except:
                PrintEXC()
                Log("库更新失败：", msg, ptn, chl, data)

    # sc_name参数为字符串，形式为<lib_name>.<script_name>
    def Call(self, sc_name, *args):
        try:
            pair = sc_name.split(".")
            lib = pair[0]
            sc = pair[1]
            if lib in self.mScripts:
                scs = self.mScripts[lib]
                if sc in scs:
                    sha = scs[sc]
                    Log("Call", sc_name, sha)
                    return self.mOriRedis.evalsha(sha, 0, *args)
            return None
        except:
            PrintEXC()
            return None

    async def AsyncCall(self, sc_name, *args):
        try:
            pair = sc_name.split(".")
            lib = pair[0]
            sc = pair[1]
            if lib in self.mScripts:
                scs = self.mScripts[lib]
                if sc in scs:
                    sha = scs[sc]
                    Log("AsyncCall", sc_name, sha)
                    return (await self.mAsyncHelper.Exec("EVALSHA", sha, 0, *args))
            return None
        except:
            PrintEXC()
            return None

class RedisProxy(object):
    @classmethod
    def LoadWithCfg(cls, name, cfg):
        # cfg 異常檢查
        if ("host" not in cfg) or (cfg["host"] is None) or (not isinstance(cfg["host"], str)) or (len(cfg["host"]) == 0) or \
            ("db" not in cfg) or (cfg["db"] is None) or (not isinstance(cfg["db"], int)) or (cfg["db"] <= 0) or \
            ("port" not in cfg) or (cfg["port"] is None) or (not isinstance(cfg["port"], int)) or (cfg["port"] <= 0):
            Err("<连接池>配置：")
            Err(json.dumps(cfg, indent=4))
            return None

        if "password" in cfg:
            v = cfg["password"]
            if isinstance(v, str) and len(v) > 0:
                pass
            else:
                cfg.pop("password")

        if "encoding" in cfg:
            v = cfg["encoding"]
            if isinstance(v, str) and len(v) > 0:
                pass
            else:
                cfg["encoding"] = "utf-8"
        else:
            cfg["encoding"] = "utf-8"

        unix_mode = False
        if "path" in cfg:
            v = cfg["path"]
            if isinstance(v, str) and len(v) > 0:
                unix_mode = True
            else:
                cfg.pop("path")

        compat = False
        if "compatible" in cfg:
            try:
                compat = int(cfg["compatible"]) != 0
            except:
                PrintEXC()
            cfg.pop("compatible")

        conn_cls = redis.Connection

        if unix_mode:
            sock_path = cfg["path"]
            if os.path.exists(sock_path):
                conn_cls = redis.UnixDomainSocketConnection
                cfg.pop("host")
                cfg.pop("port")
            elif compat:
                cfg.pop("path")
                unix_mode = False
            else:
                raise RedisProxyError("无效的<Socket>文件描述符：", sock_path)

        if "decode_responses" in cfg:
            try:
                b = int(cfg["decode_responses"]) != 0
                cfg["decode_responses"] = b
            except:
                PrintEXC()
                cfg["decode_responses"] = False
        else:
            cfg["decode_responses"] = False

        if "socket_timeout" in cfg:
            try:
                v = float(cfg["socket_timeout"])
                if v > 0:
                    cfg["socket_timeout"] = v
                else:
                    cfg.pop("socket_timeout")
            except:
                PrintEXC()
                cfg.pop("socket_timeout")

        if "retry_on_timeout" in cfg:
            try:
                b = int(cfg["retry_on_timeout"]) != 0
                cfg["retry_on_timeout"] = b
            except:
                PrintEXC()
                cfg["retry_on_timeout"] = False
        else:
            cfg["retry_on_timeout"] = False

        if "socket_read_size" in cfg:
            try:
                v = int(cfg["socket_read_size"])
                if v > 0:
                    cfg["socket_read_size"] = v
                else:
                    cfg["socket_read_size"] = 65536
            except:
                PrintEXC()
                cfg["socket_read_size"] = 65536
        else:
            cfg["socket_read_size"] = 65536

        if "socket_connect_timeout" in cfg:
            if unix_mode:
                cfg.pop("socket_connect_timeout")
            else:
                try:
                    v = float(cfg["socket_connect_timeout"])
                    if v > 0:
                        cfg["socket_connect_timeout"] = v
                    else:
                        cfg.pop("socket_connect_timeout")
                except:
                    PrintEXC()
                    cfg.pop("socket_connect_timeout")

        if "max_connections" in cfg:
            try:
                v = int(cfg["max_connections"])
                if v > 0:
                    cfg["max_connections"] = v
                else:
                    cfg["max_connections"] = 1024
            except:
                PrintEXC()
                cfg["max_connections"] = 1024
        else:
            cfg["max_connections"] = 1024

        lua_lib_cfg = None
        if "lua_lib_cfg" in cfg:
            lua_lib_cfg = cfg["lua_lib_cfg"]
            if isinstance(lua_lib_cfg, dict):
                pass
            else:
                lua_lib_cfg = None
            cfg.pop("lua_lib_cfg")

        cfg["connection_class"] = repr(conn_cls)

        sub_chls = None
        if "subscribe" in cfg:
            sub_chls = cfg["subscribe"]
            if not isinstance(sub_chls, list):
                sub_chls = None
            elif len(sub_chls) < 1:
                sub_chls = None
            cfg.pop("subscribe")

        psub_chls = None
        if "psubscribe" in cfg:
            psub_chls = cfg["psubscribe"]
            if not isinstance(psub_chls, list):
                psub_chls = None
            elif len(psub_chls) < 1:
                psub_chls = None
            cfg.pop("psubscribe")

        Info("<连接池>配置预览：")
        Info(json.dumps(cfg, indent = 4))
        rds_cfg = deepcopy(cfg)

        cfg["connection_class"] = conn_cls

        # 此处暂时采用普通连接池，需要多线程时再升级
        conn_pool = redis.ConnectionPool(**cfg)

        rp = cls(name = name, connection_pool = conn_pool)

        try:
            if lua_lib_cfg is not None:
                RedisProxy.SetLibGuard(rp, lua_lib_cfg)

            if sub_chls is not None or psub_chls is not None:
                rp.OpenPubSub()
                if sub_chls is not None:
                    rp.PubSub.Subscribe(sub_chls)
                if psub_chls is not None:
                    rp.PubSub.PSubscribe(psub_chls)
        except:
            Err("<连接池>配置：")
            Err(json.dumps(rds_cfg, indent=4))
            PrintEXC()
            return None

        return rp

    @classmethod
    def SetLibGuard(cls, rp, lib_cfg):
        if rp is None or lib_cfg is None:
            raise RedisProxyError("无法完成LibGuard的初始化：", rp, lib_cfg)
            return

        if rp.IsEmpty:
            raise RedisProxyError("无法完成LibGuard的初始化：", rp.IsEmpty)
            return

        rp.OpenLibGuard(lib_cfg)

    def __init__(self, name = "default", connection_pool = None, suspend_time = 0.02):
        self.mName = name
        self.mOriRedis = None
        self.mConnectionPool = None
        self.mLibGuard = None
        self.mPubSub = None
        self.mAsyncHelper = None
        if connection_pool is None:
            Info("初始化<Redis>代理为空代理！")
        else:
            self.mOriRedis = redis.StrictRedis(connection_pool = connection_pool)
            self.mConnectionPool = connection_pool
            self.mAsyncHelper = AsyncRDSHelper(rds_proxy = self, suspend_time = suspend_time)

    def __del__(self):
        self.CloseLibGuard()
        self.ClosePubSub()

    @property
    def Name(self):
        return self.mName

    @property
    def R(self):
        return self.mOriRedis

    @property
    def Pool(self):
        return self.mConnectionPool
    
    @property
    def LibGrd(self):
        return self.mLibGuard

    @property
    def PubSub(self):
        return self.mPubSub

    @property
    def AsyncHelper(self):
        return self.mAsyncHelper

    @property
    def IsEmpty(self):
        return self.mOriRedis is None or self.mConnectionPool is None
        
    def OpenLibGuard(self, lib_cfg):
        self.CloseLibGuard()
        self.mLibGuard = LibGuard(rds_proxy = self, **lib_cfg)

    def CloseLibGuard(self):
        if self.mLibGuard is not None:
            del self.mLibGuard
            self.mLibGuard = None

    def OpenPubSub(self):
        self.ClosePubSub()
        self.mPubSub = PubSubProxy(rds_proxy = self)

    def ClosePubSub(self):
        if self.mPubSub is not None:
            del self.mPubSub
            self.mPubSub = None

    def Update(self):
        if self.mPubSub is not None:
            self.mPubSub.Update()

        if self.mLibGuard is not None:
            self.mLibGuard.Update()