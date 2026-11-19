
import os
import random
import time
import datetime
import re
import logging
import signal
import hashlib
import platform
import uuid

from traceback import print_exc, format_exc
#import psutil

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s][%(levelname)s] %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
LOGIns = logging.getLogger()

class LOGService(object):
    @classmethod
    def Set(cls, lv):
        if isinstance(lv, int):
            if lv == 0:
                LOGIns.setLevel(logging.DEBUG)
            elif lv == 1:
                LOGIns.setLevel(logging.INFO)
            elif lv == 2:
                LOGIns.setLevel(logging.WARNING)
            elif lv == 3:
                LOGIns.setLevel(logging.ERROR)

def DEBUG(msg, *argv, **kwargv):
    LOGIns.debug(msg, *argv, **kwargv)

def INFO(msg, *argv, **kwargv):
    LOGIns.info(msg, *argv, **kwargv)

def WARNING(msg, *argv, **kwargv):
    LOGIns.warning(msg, *argv, **kwargv)

def ERROR(msg, *argv, **kwargv):
    LOGIns.error(msg, *argv, **kwargv)

"""
    ******************************************************************************
"""
class DebugLevel(object):
    sLevel = 0
    @classmethod
    def Set(cls, lv):
        if isinstance(lv, int) or isinstance(lv, long):
            cls.sLevel = lv

def Log(*argv, **kwargv):
    if DebugLevel.sLevel <= 0:
        print("[" + GetServerTimeStr() + "][LOG]", *argv, **kwargv)

def Warn(*argv, **kwargv):
    if DebugLevel.sLevel <= 1:
        print("[" + GetServerTimeStr() + "][WARN]", *argv, **kwargv)

def Err(*argv, **kwargv):
    if DebugLevel.sLevel <= 2:
        print("[" + GetServerTimeStr() + "][ERR]", *argv, **kwargv)

def Info(*argv, **kwargv):
    if DebugLevel.sLevel <= 3:
        print("[" + GetServerTimeStr() + "][INFO]", *argv, **kwargv)

def PrintEXC(fhd = None):
    if DebugLevel.sLevel <= 2:
        if fhd is None:
            print_exc()
        else:
            print_exc(file = fhd)

def GetEXC():
    return format_exc()
"""
    ******************************************************************************
"""

MAX_ACCOUNT_LEN = 64         # 账号长度限制
MAX_NICKNAME_LEN = 64        # 昵称长度限制
MAX_PWD_LEN = 32             # 密码长度限制
MAX_IP_LEN = 64              # IP长度限制

P = re.compile(r'[\s\\\(\)\[\]\{\}\,\.\'\"\:\;\#\/\`]', re.I)

def GenNetSign(socketid, servport):
    return str(servport) + "|" + str(socketid)

def GenTokenID():
    return random.randint(25452368, 96532548)

def GenNickNameBytes():
    nickname = "JJ"+str(random.randint(2356212, 96358975))
    return nickname.encode('utf-8')

def GenHostApiHashKey(host_api_key, subgame_id):
    return hashlib.md5((host_api_key + str(subgame_id)).encode()).hexdigest()

# 检测昵称是否合法
def CheckNickNameValid(nickname):
    if isinstance(nickname, bytes):
        if P.search(nickname.decode('utf-8')) is None:
            return True
    return False

def CheckAndReviseNiceName(nickname):
    if isinstance(nickname, bytes):
        try:
            name = re.sub(r'[\s\\\(\)\[\]\{\}\,\.\'\"\:\;\#\/\`]', "", nickname.decode('utf-8'))
            return name.encode('utf-8')
        except:
            return nickname
    return nickname

# 检查IP格式
def CheckIPFormat(ip):
    if ip is not None and isinstance(ip, str):
        try:
            matchobjv4 = re.match(
                r'^(((\d{1,2})|(1\d{1,2})|(2[0-4]\d)|(25[0-5]))\.){3}((\d{1,2})|(1\d{1,2})|(2[0-4]\d)|(25[0-5]))$', ip)
            if matchobjv4:
                return True
            matchobjv6 = re.match(
                r'^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$',
                ip)
            if matchobjv6:
                return True
        except:
            return False
    return False

def CheckAndReviseIPAddress(address):
    res = b'127.0.0.1'
    if address is not None:
        try:
            if isinstance(address, bytes):
                res = address.decode('utf-8').strip('\n').encode('utf-8')
            elif isinstance(address, str):
                res = address.strip('\n').encode('utf-8')
            if CheckIPFormat(res.decode('utf-8')) == False:
                res = b'127.0.0.1'
        except:
            return b'127.0.0.1'
    return res

def GenSmsCode():
    return random.randint(100000, 999999)

def GetRndInt(beg, end):
    return random.randint(beg, end)

def GetServerTime():
    return int(time.time())

def GetServerTimeMS():
    return (int(round(time.time() * 1000)))

def GetServerZeroTime(t = None):
    if t is None:
        t = time.time()
    t = int(t)
    return t - t % 86400
    #lt = time.localtime(t)
    #time1 = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00', lt), '%Y-%m-%d %H:%M:%S'))
    #return int(time1)

def GetServerTimeStr():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def GetServerTimeFromIntToStr(time_stamp):
    struct_time = time.localtime(time_stamp)  # 轉成時間元組
    timeString = time.strftime("%Y-%m-%d %H:%M:%S", struct_time)  # 轉成字串
    return timeString

# 字典排序 False 从小到大，反之
def SortDictByKey(sdict, bRev = False):
    if isinstance(sdict, dict) and len(sdict) > 0:
        keys = list(sdict.keys())
        keys.sort(reverse = bRev)
        rdict = {}
        for i in range(len(keys)):
            rdict[keys[i]] = sdict[keys[i]]
        return rdict
    return sdict

#redis结果集转换成dict
def OnRedisResultParser(v):
    mResults = {}
    if isinstance(v, list):
        for idx in range(0, len(v), 2):
            skey = v[idx]
            sval = v[idx + 1]
            if isinstance(skey, bytes): skey = skey.decode()
            if isinstance(sval, bytes): sval = sval.decode()
            mResults[skey] = sval
    return mResults

def WritePidAndSignal(signal_func): # func like def f(signum, frame)
    #捕获退出信号
    os_name = platform.system()
    if os_name != 'Windows':
        signal.signal(signal.SIGUSR2, signal_func)
    try:
        f = open(".pids", mode="a+", encoding="utf-8")
        f.write(str(os.getpid()) + "\n")
        f.flush()
        f.close()
    except:
        Err("保存进程信号失败，无法执行一件关闭进程")

def GenShortUUID():
    return str(uuid.uuid4())[:8]

'''
def GetCpuAndMemory(pid=None):
    try:
        if pid is None:
            pid = os.getpid()
        p = psutil.Process(pid)
        cpu_percent = float("%.2f" % p.cpu_percent())
        mem_percent = float("%.2f" % p.memory_percent())
        return str(cpu_percent)+"%", str(mem_percent)+"%"
    except:
        return "0.00%", "0.00%"
'''
