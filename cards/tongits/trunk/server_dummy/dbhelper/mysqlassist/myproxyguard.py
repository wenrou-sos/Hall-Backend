from mysqlassist.mysqlproxy import *
from mysqlassist.utils import DebugLevel
import json

class MYProxyGuardError(Exception):
    pass

class MYProxyGuard(object):
    sProxys = {}

    def __init__(self):
        raise MYProxyGuardError("MYProxyGuard无法被初始化！")

    @classmethod
    def LoadByFile(cls, path):
        cls.Clear()
        with open(path, "r") as hd:
            data = json.loads(hd.read())
            if "dbs" in data:
                dbs = data["dbs"]
                for key in dbs:
                    cfg = dbs[key]
                    myp = ProxyCreator.LoadWithCfg(key, cfg)
                    if myp is not None:
                        cls.sProxys[key] = myp
                        Info("MYProxyGuard.LoadByFile sProxys Set: ", key)
                    else:
                        Warn("Not a valid mysql cfg, key:", key)

        if len(cls.sProxys) < 1:
            return None

        return cls

    @classmethod
    def LoadByData(cls, row_data):
        cls.Clear()
        data = row_data
        if "dbs" in data:
            dbs = data["dbs"]
            for key in dbs:
                try:
                    cfg = dbs[key]
                    myp = ProxyCreator.LoadWithCfg(key, cfg)
                    if myp is not None:
                        cls.sProxys[key] = myp
                        Info("MYProxyGuard.LoadByData sProxys Set: ", key)
                    else:
                        Warn("Not a valid mysql cfg, key:", key)
                except:
                    print(dbs[key], key)
                    PrintEXC()
                    continue

        if len(cls.sProxys) < 1:
            return None

        return cls

    @classmethod
    def MYP(cls, name):
        if name in cls.sProxys:
            return cls.sProxys[name]
        else:
            return None

    @classmethod
    def Clear(cls):
        cls.sProxys = {}

    @classmethod
    def ProcWith(cls, proc_fun = print, myp_name = None, *argv, **kwargv):
        if myp_name is None:
            for name in cls.sProxys:
                proc_fun(cls.sProxys[name], *argv, **kwargv)
        else:
            if myp_name in cls.sProxys:
                proc_fun(cls.sProxys[myp_name], *argv, **kwargv)

    @classmethod
    def SetDebugLevel(cls, lv):
        DebugLevel.Set(lv)
