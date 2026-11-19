from datetime import datetime,timedelta,date
from enum import IntEnum
from glogger import log
import hashlib
from calendar import monthrange
import env_setting

TIME_DIFF = -8


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
    accountfreeze = 6  # 帳號凍結

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

class seatstatus(IntEnum):
    Empty = 0
    Playing = 1
    Reserved = 2


def getutcnow_datetime():
    now = datetime.utcnow()
    return now
def getutcnow():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now
def getutcnow_nof():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    return now
def getutcnowdate():
    nowdate = datetime.utcnow().strftime('%Y-%m-%d')
    return nowdate
def get_tw_datetime():
    return (datetime.utcnow()+timedelta(hours=8))


def get_tw_2020_first_date():
    return datetime.strptime('2020-01-01','%Y-%m-%d')

def getnow():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now
###################################################
def datetime_to_str(parms):
    return parms.strftime('%Y-%m-%d %H:%M:%S')

class SendMsgType(IntEnum):
    server_to_all_client = 0
    server_to_client = 1
    server_to_channel = 2

def get_local_nowdatetime():
    utcnow = datetime.utcnow()
    localnow = utcnow - timedelta(hours=TIME_DIFF)
    return localnow

def get_local_nowdatetimestr():
    utcnow = datetime.utcnow()
    localnow = utcnow - timedelta(hours=TIME_DIFF)
    localnow_str = localnow.strftime('%Y-%m-%d %H:%M:%S.%f')
    return localnow_str

def get_local_nowdatetimestr_nof():
    utcnow = datetime.utcnow()
    localnow = utcnow - timedelta(hours=TIME_DIFF)
    localnow_str_nof = localnow.strftime('%Y-%m-%d %H:%M:%S')
    return localnow_str_nof

# 找 local 今天起始時間, 換算 utc 時間
def get_local_starttime_utc_str():
    nowtime = get_local_nowdatetimestr_nof()
    list1 = nowtime.split(' ')
    starttime_str = list1[0] + ' 00:00:00'
    strattime_datetime = datetime.strptime(starttime_str, '%Y-%m-%d %H:%M:%S')
    utctime_datetime = strattime_datetime + timedelta(hours=TIME_DIFF)
    return utctime_datetime.__str__()

# 找今天一開始的時間
def get_local_start_datetime():
    nowtime = get_local_nowdatetimestr_nof()
    list1 = nowtime.split(' ')
    starttime_str = list1[0] + ' 00:00:00'
    strattime_datetime = datetime.strptime(starttime_str, '%Y-%m-%d %H:%M:%S')
    return strattime_datetime

# 找台灣昨天起始與結束時間換算成 utctime
def get_tw_yesterday_startend_datetime_str():
    yesterdaydate = (get_local_nowdatetime() - timedelta(days=1)).date()
    yesterdaystartdatetime_str,yesterdayenddatetime_str = get_date_to_utc_start_end_time(yesterdaydate)


    return yesterdaystartdatetime_str,yesterdayenddatetime_str,yesterdaydate.__str__()

def get_local_nowtime_utc_str():
    nowtime = get_local_nowdatetime()
    nowtime_utc = nowtime + timedelta(hours=TIME_DIFF)
    return nowtime_utc.strftime('%Y-%m-%d %H:%M:%S')

def get_localdate_utc_date_str():
    return (datetime.utcnow() - timedelta(hours=TIME_DIFF)).strftime('%Y-%m-%d')

def utcstr_to_local_datetime_str(str):
    utcdatetime = datetime.strptime(str, '%Y-%m-%d %H:%M:%S')
    localdatetime = utcdatetime - timedelta(hours=TIME_DIFF)
    return localdatetime.strftime('%Y-%m-%d %H:%M:%S')

def get_date_to_utc_start_end_time(date1):
    starttime = date1.__str__() + ' 00:00:00'
    endtime = date1.__str__() + ' 23:59:59'

    starttime_datetime = datetime.strptime(starttime,'%Y-%m-%d %H:%M:%S')
    endtime_datetime = datetime.strptime(endtime,'%Y-%m-%d %H:%M:%S')

    utc_starttime_str = (starttime_datetime + timedelta(hours=TIME_DIFF)).strftime('%Y-%m-%d %H:%M:%S')
    utc_endtime_str = (endtime_datetime + timedelta(hours=TIME_DIFF)).strftime('%Y-%m-%d %H:%M:%S')

    return utc_starttime_str,utc_endtime_str
def local_datetime_to_utc_datetime(date1):
    utcdatetime = date1 + timedelta(hours=TIME_DIFF)
    return utcdatetime

def get_tw_date_str():
    twdatetime = get_tw_datetime()
    return twdatetime.date().__str__()

def get_local_date():
    utcdatetime = datetime.utcnow()
    localdatetime = utcdatetime - timedelta(hours=TIME_DIFF)
    return localdatetime.date()

def get_tw_date_month_str():
    twdatestr = get_tw_date_str()
    return twdatestr.split('-')[0] + '-' + twdatestr.split('-')[1]

def get_local_datetime():
    return (datetime.utcnow() - timedelta(hours=TIME_DIFF))

#########################################################
def utctimestamptodatetimestring(timestamp):
    return datetime.utcfromtimestamp(timestamp).__str__()

def strtodatetime(timestr):
    result = datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
    return result

def strtodate(datestr):
    result = datetime.strptime(datestr, '%Y-%m-%d')
    return result

def strtomonth(monthstr):
    result = datetime.strptime(monthstr,'%Y-%m')
    return result

def generatorsha256():
    result = hashlib.sha256(getutcnow().encode()).hexdigest()
    return result

def monthlastday(date1):
    return monthrange(date1.year,date1.month)[1]




def writelog(loglevel, logmsg):
    if loglevel == PG_LogerLevel.warn:
        logger.warning(LOG_PREFIX+"controlserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    elif loglevel == PG_LogerLevel.error:
        logger.error(LOG_PREFIX+"controlserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    else:
        if env_setting.DEBUG_LOG_MODE == True:
            logger.info(LOG_PREFIX+"controlserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
        else:
            pass

def loggerinit():
    global logger
    logger = log()


def converttype(data, type):
    try:
        return type(data)
    except Exception as e:
        return None
