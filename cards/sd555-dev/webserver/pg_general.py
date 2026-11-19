from datetime import datetime,timedelta
from enum import IntEnum
from glogger import log
import hashlib
import env_setting
# import asyncio

# 儲值先判斷是否為機器人帳號(付款方式, 會員代號)
def is_robot_or_not(deposit_method, memberid):
    # 先看memberid的log，比對玩家是否不是機器人帳號，等級用error才能看到log
    writelog(PG_LogerLevel.error, 'web client call webserver for {} memberid={}'.format(deposit_method, memberid))
    # 確認memberid，機器人自動帳號則退回玩家顯示儲值失敗
    memberid = int(memberid)
    if memberid <= 2:    # 2以下都不是正常帳號
        writelog(PG_LogerLevel.error, 'web client call webserver, but memberid is failed')
        member_is_robot = {"statuscode": 3}
        return member_is_robot    # statuscode != 0 → 強制登出
    else:
        member_is_not_robot = {"statuscode": 0}
        return member_is_not_robot

TIME_DIFF = 4

if env_setting.PRODUCTION_MODE == True:
    LOG_PREFIX = 'PRODUCTION_'
else:
    LOG_PREFIX = ''

class Packagestatuscode(IntEnum):
    success = 0
    networkerror = 1
    membererror = 2
    balanceerror = 3
    commanderror = 4
    psloginerror = 5
    accountfreeze = 6 # 帳號凍結


class Apiresult(IntEnum):
    success = 0
    parametererror = 1
    connectdberror = 2
    dbnodata = 3
    othererror = 4
    balanceerror = 5
    psloginerror = 6
    accountfreeze = 7  # 帳號凍結

class PG_LogerLevel(IntEnum):
    trace = 0
    debug = 1
    info = 2
    warn = 3
    error = 4

def getutcnow_datetime():
    return datetime.utcnow()

def getutcnow():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now

def get_local_datetime():
    return (datetime.utcnow() - timedelta(hours=TIME_DIFF))

def get_tw_datetime():
    return (datetime.utcnow()+timedelta(hours=8))

def getnow():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now

def utctimestamptodatetimestring(timestamp):
    return datetime.utcfromtimestamp(timestamp).__str__()

def strtodatetime(timestr):
    result = datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')
    return result


def get_utc_to_local_datetime(utctime1):

    localdatetime = utctime1 - timedelta(hours=TIME_DIFF)

    return localdatetime

def generatorsha256():
    result = hashlib.sha256(getutcnow().encode()).hexdigest()
    return result


def a_writelog(loglevel, logmsg):
    if loglevel == PG_LogerLevel.warn:
        logger.warning(LOG_PREFIX+"webserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    elif loglevel == PG_LogerLevel.error:
        logger.error(LOG_PREFIX+"webserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    else:
        if env_setting.DEBUG_LOG_MODE == True:
            logger.info(LOG_PREFIX+"webserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
        else:
            pass

def writelog(loglevel, logmsg):

    a_writelog(loglevel, logmsg)

    # if loglevel == PG_LogerLevel.warn:
    #     logger.warning(LOG_PREFIX+"apiserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    # elif loglevel == PG_LogerLevel.error:
    #     logger.error(LOG_PREFIX+"apiserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    # else:
    #     if env_setting.DEBUG_LOG_MODE == True:
    #         logger.info(LOG_PREFIX+"apiserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    #     else:
    #         pass

def loggerinit():
    global logger
    logger = log()


def converttype(data, type):
    try:
        return type(data)
    except Exception as e:
        return None

def intWithCommas(x):
    if isinstance(x,int) != True:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)


def check_chinese(str1):

    for item in str1:
        code = ord(item)
        if code < 0x4e00 or code > 0x9fa5:
            return False

    return True