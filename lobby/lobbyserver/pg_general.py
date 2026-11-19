from datetime import datetime,timedelta
from enum import IntEnum
from glogger import log
import hashlib
import env_setting
import asyncio



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
class seatstatus(IntEnum):
    Empty = 0
    Playing = 1
    Reserved = 2

def converttype(data, type):
    try:
        return type(data)
    except Exception as e:
        return None
def getutcnow():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now

def get_tw_datetime():
    return (datetime.utcnow()+timedelta(hours=8))

def getnow():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    return now

def utctimestamptodatetimestring(timestamp):
    return datetime.utcfromtimestamp(timestamp.__str__())

def strtodatetime(timestr):
    result = datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')
    return result

def getutcnowdatetime():
    return datetime.utcnow()

def generatorsha256():
    result = hashlib.sha256(getutcnow().encode()).hexdigest()
    return result


def a_writelog(loglevel,logmsg):
    if loglevel == PG_LogerLevel.warn:
        # logger.warning(LOG_PREFIX+"lobbyserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
        logger.warning(logmsg[0],logmsg[1])
    elif loglevel == PG_LogerLevel.error:
        # logger.error(LOG_PREFIX+"lobbyserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
        logger.error(logmsg[0],logmsg[1])
    else:
        if env_setting.DEBUG_LOG_MODE ==True:
            # logger.info(LOG_PREFIX+"lobbyserver",
            #             "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
            logger.info(logmsg[0],logmsg[1])
        else:
            pass

async def log_put_queue(data):
    templevel = data[0]
    templog1 = data[1]
    templog2 = LOG_PREFIX+"lobbyserver", "{0} {1} {2}".format(str(templevel).replace('PG_LogerLevel.', ''), getutcnow(), templog1)

    await log_queue.put((templevel,templog2))

def writelog(loglevel, logmsg):
    # asyncio.ensure_future(a_writelog(loglevel,logmsg))
    asyncio.ensure_future(log_put_queue((loglevel,logmsg)))
    # if loglevel == PG_LogerLevel.warn:
    #     logger.warning(LOG_PREFIX+"lobbyserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    # elif loglevel == PG_LogerLevel.error:
    #     logger.error(LOG_PREFIX+"lobbyserver", "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    # else:
    #     if env_setting.DEBUG_LOG_MODE ==True:
    #         logger.info(LOG_PREFIX+"lobbyserver",
    #                     "{0} {1} {2}".format(str(loglevel).replace('PG_LogerLevel.', ''), getutcnow(), logmsg))
    #     else:
    #         pass

async def Logfuture(log_queue):
    while(1):

        try:
            msg_info = await log_queue.get()
            a_writelog(msg_info[0],msg_info[1])
        except Exception as e:
            pass

        # await asyncio.sleep(0)


def loggerinit():
    global logger
    global log_queue

    logger = log()
    log_queue = asyncio.Queue(maxsize=-1)
    asyncio.ensure_future(Logfuture(log_queue))

