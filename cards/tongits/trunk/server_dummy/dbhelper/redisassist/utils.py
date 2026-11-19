import time
import datetime
from traceback import print_exc

class DebugLevel(object):
    sLevel = 0
    @classmethod
    def Set(cls, lv):
        if isinstance(lv, int) or isinstance(lv, long):
            cls.sLevel = lv

def Log(*argv, **kwargv):
    if DebugLevel.sLevel <= 0:
        print("[" + GetServerTimeStr() + "]" + "[Redis][LOG]", *argv, **kwargv)

def Warn(*argv, **kwargv):
    if DebugLevel.sLevel <= 1:
        print("[" + GetServerTimeStr() + "]" + "[Redis][WARN]", *argv, **kwargv)

def Err(*argv, **kwargv):
    if DebugLevel.sLevel <= 2:
        print("[" + GetServerTimeStr() + "]" + "[Redis][ERR]", *argv, **kwargv)

def Info(*argv, **kwargv):
    if DebugLevel.sLevel <= 3:
        print("[" + GetServerTimeStr() + "]" + "[Redis][INFO]", *argv, **kwargv)

def PrintEXC():
    if DebugLevel.sLevel <= 2:
        print_exc()

def GetServerTime():
    return int(time.time())

def GetServerZeroTime(t = None):
    if t is None:
        t = time.time()
    t = int(t)
    return t - t % 86400

def GetServerTimeStr():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')