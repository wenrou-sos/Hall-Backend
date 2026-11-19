from datetime import datetime,timedelta
from enum import IntEnum
from glogger import log
import hashlib
import env_setting
import asyncio
import pg_general

TIME_DIFF = -8

PASS_REDIS_VALIDATION_CODE = 3343  # 提供後台 call API 時可以繞過 redis 驗證

if env_setting.PRODUCTION_MODE == True:
    LOG_PREFIX = 'Prod_Lucky_Angkor_'
else:
    LOG_PREFIX = 'SD555-APP-'

class SendMsgType(IntEnum):
    server_to_all_client = 0
    server_to_client = 1
    server_to_channel = 2
    server_to_clubchannel = 3

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
    accpasserror = 8   # 帳號或是密碼錯誤
    duplicationacc = 9  # 帳號重複
    hasusernameacc = 10 # 使用　fb 登入的時候有查到　此　deviceid 已經綁定 username
    hasanotherfbid = 11        # 使用 fb 登入的時候有查到此 deviceid 已經綁過 fbid
    blackme = 12                # 對方 block me
    hasanotherlinesub = 12 # 使用Line登入的時候有查到此deviceid已經綁過line帳號

class transactiontype(IntEnum):
    shopmall = 0
    promotion = 1
    goldtosilver = 2
    silvertogold = 3
    gift = 4
    serial = 5
    savetosafe = 6
    getfromsafe = 7
    pointtocredit = 8
    rejectgift = 9
    gashwallet = 10
    receivegift = 11
    overtimerejectgift = 12
    dailywheel = 13
    bindphonereward = 14
    getpiggycredit = 15
    gashpoint = 16
    receiveinbox = 17
    webcreditcard = 18
    freebox = 19
    inboxfreewheel = 20
    buyboxcost = 21
    buyboxget = 22
    tutorialwin = 23
    depositefishgame = 24
    withdrawfishgame = 25
    emailbindreward = 26

class PG_LogerLevel(IntEnum):
    trace = 0
    debug = 1
    info = 2
    warn = 3
    error = 4

class GashWalletErrorEnum(IntEnum):
    RequestError = 0
    SettleError = 1
    CheckError = 2

class seatstatus(IntEnum):
    Empty = 0
    Playing = 1
    Reserved = 2

def getutcnow_datetime():
    return datetime.utcnow()

def getutcnow():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now

def getutcnowHM():
    now = datetime.utcnow().strftime('%H:%M.%f')
    return now

def datetimetostr_nof(datetime1):
    return datetime1.strftime('%Y-%m-%d %H:%M:%S')


def get_local_datetime():
    return (datetime.utcnow() - timedelta(hours=TIME_DIFF))
def get_tw_datetime():
    return (datetime.utcnow()+timedelta(hours=8))
def get_th_datetime():
    return (datetime.utcnow()+timedelta(hours=7))
def get_cb_datetime():
    return (datetime.utcnow()+timedelta(hours=7))
def get_cb_datetime_nof():
    return (datetime.utcnow()+timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')

def get_tw_date_str():
    twdatetime = get_tw_datetime()
    return twdatetime.date().__str__()
def get_tw_date_month_str():
    twdatestr = get_tw_date_str()
    return twdatestr.split('-')[0] + '-' + twdatestr.split('-')[1]


def get_tw_2020_first_date():
    return datetime.strptime('2020-01-01','%Y-%m-%d')

def getnow():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now

def utctimestamptodatetimestring(timestamp):
    return datetime.utcfromtimestamp(timestamp).__str__()

def strtodatetime(timestr):
    result = datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')
    return result

def strtodatetime_nof(timestr):
    result = datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
    return result

def get_utc_to_local_datetime(utctime1):

    localdatetime = utctime1 - timedelta(hours=TIME_DIFF)

    return localdatetime

def datetime_to_str(parms):
    return parms.strftime('%Y-%m-%d %H:%M:%S')


def generatorsha256():
    result = hashlib.sha256(getutcnow().encode()).hexdigest()
    return result


async def a_writelog(loglevel, logmsg):
    if loglevel == PG_LogerLevel.warn:
        logger.warning(LOG_PREFIX+"apiserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    elif loglevel == PG_LogerLevel.error:
        logger.error(LOG_PREFIX+"apiserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    else:
        if env_setting.DEBUG_LOG_MODE == True:
            logger.info(LOG_PREFIX+"apiserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
        else:
            pass

def writelog(loglevel, logmsg):

    asyncio.ensure_future(a_writelog(loglevel, logmsg))

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

def check_english(str1):
    for item in str1:
        if item.isdigit() != True:
            code = ord(item)
            # writelog(pg_general.PG_LogerLevel.debug,
            #                     'pg_asqldb:updateprofile check_english code:{0}'.format(code))
            # 英文 Unicode範圍: 0041 - 005A, 0061 - 007A(若含數字與符號，則為0021 - 007E)
            # 泰文 Unicode範圍: 0E00 - 0E7F
            if code < 0x0E00 or code > 0x0E7F:
                if code < 0x0041 or code > 0x007A:
                    return False
            # if code > 0x005A and code < 0x0061:
            #     return False
            # if code < 0x0030 and code < 0x0039:
            #     return False
    return True
