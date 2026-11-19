from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import os
import aiohttp.web
import sys
import time
import env_setting
from pg_telegram import PG_TELEBOT
import pg_general
from pg_asqldb import PG_ASQLDB
from enum import IntEnum
from pg_redis import PGRedis
import pg_fcm
from pg_rankupload import PG_RANKUPLOAD
from datetime import timedelta
import json
import pg_sms


HOST = os.getenv('HOST', '127.0.0.1')
if env_setting.LOCAL_SERVER:
    PORT = int(os.getenv('PORT', 82))
else:
    PORT = int(os.getenv('PORT',80))








async def healthycheck_handle(request):
    return aiohttp.web.Response(text='check')

async def allusers_handle(request):
    app = request.app
    redis_obj = app['redis']
    onlinekeys = await redis_obj.get_all_keys('online*')
    if onlinekeys is None:
        onlinekeys = 0

    return aiohttp.web.Response(text=str(len(onlinekeys)))

async def allmallhistory_handle(request):
    app = request.app
    db = app['DB'][0]

    result, resultdata = await db.allmallhistory()

    if resultdata is None:
        resultdata = 'Failed'



    return aiohttp.web.Response(text=resultdata)

async def getservicechat_handle(request):
    app = request.app
    db = app['DB'][0]
    data = await request.post()


    return aiohttp.web.Response(text=data)


async def createseats_handle(request):
    app = request.app
    db = app['DB'][0]

    redis_obj = app['redis']

    result,resultdata = await db.createseats(redis_obj)


    data = "ok"


    return aiohttp.web.Response(text=data)

async def delgoldseats_handle(request):
    app = request.app
    db = app['DB'][0]

    redis_obj = app['redis']
    keys = await redis_obj.get_all_keys('goldseats*')
    for item in keys:
        await redis_obj.del_key(item)

    data = 'ok'
    return aiohttp.web.Response(text=data)

async def makeserialtable_handle(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']

    modeindex = pg_general.converttype(request.rel_url.query.get('modeindex'),int)
    amount = pg_general.converttype(request.rel_url.query.get('amount'),int)

    if None not in [modeindex,amount]:
          await db.makeserialtable(modeindex,amount)

    data = 'ok'
    return aiohttp.web.Response(text=data)



async def makepromotiontoinbox_handle(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    telebotobj = app['telebot']

    ip = request.remote

    admin = request.rel_url.query.get('admin')
    pd = request.rel_url.query.get('pd')
    userlist = request.rel_url.query.get('userlist')
    title = request.rel_url.query.get('title')
    content = request.rel_url.query.get('content')
    type = pg_general.converttype(request.rel_url.query.get('type'),int)
    amount = pg_general.converttype(request.rel_url.query.get('amount'),int)

    param = {
        "ip": ip,
        "admin": admin,
        "pd": pd,
        "userlist": userlist,
        "title": title,
        "content": content,
        "type": type,
        "amount": amount
    }

    # insert api log
    await db.writeapilog(admin, pd, ip, 'makepromotiontoinbox', param)
    if env_setting.PRODUCTION_MODE == True:
        telebotobj.sendfeedbackmsg(json.dumps(param), 'apiadmin')
    result = {"result": -1}


    if None not in [admin, pd,userlist,title,content,ip,type,amount]:
        result = await db.makepromotiontoinbox(telebotobj,param)

    return aiohttp.web.Response(text=json.dumps(result))
async def getredisdata_handle(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']

    cmd = request.rel_url.query.get('cmd')
    args = request.rel_url.query.get('args')

    result = "empty"
    if cmd == 'hgetall':
        redisresult = await redis_obj.hgetall(args)
        result = json.dumps(redisresult)
    elif cmd == 'hkeys':
        redisresult = await redis_obj.hkeys(args)
        result = json.dumps(redisresult)
    elif cmd == 'dbsize':
        redisresult = await redis_obj.get_db_size()
        result = str(redisresult)
    elif cmd == 'ttl':
        redisresult = await redis_obj.ttl(args)
        result = str(redisresult)
    elif cmd == 'keys':
        redisresult = await redis_obj.get_all_keys(args)
        result = json.dumps(redisresult)
    elif cmd == 'info':
        redisresult = await redis_obj.info()
        result = json.dumps(redisresult)
    elif cmd == 'lrange':
        redisresult = await redis_obj.lrange(args)
        result = json.dumps(redisresult)
    elif cmd == 'get':
        redisresult = await redis_obj.get_value(args)
        result = json.dumps(redisresult)
    elif cmd == 'llen':
        redisresult = await redis_obj.llen(args)
        result = str(redisresult)


    return aiohttp.web.Response(text=result)


async def delsilverseats_handle(request):
    app = request.app
    db = app['DB'][0]

    redis_obj = app['redis']
    keys = await redis_obj.get_all_keys('silverseats*')
    for item in keys:
        await redis_obj.del_key(item)

    data = 'ok'
    return aiohttp.web.Response(text=data)

async def delgameseat_handle(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    gameid = request.rel_url.query.get('gameid')

    for i in range(100):
        await redis_obj.hmset("silverseats_{}@{}".format(gameid,i+1), {"his1turn":0,"his2turn":0,"his3turn":0,"his1multi":0,"his2multi":0,"his3multi":0,"avgturn":0,"unopenturn":0})
        await redis_obj.hmset("goldseats_{}@{}".format(gameid,i+1),{"his1turn": 0, "his2turn": 0, "his3turn": 0, "his1multi": 0, "his2multi": 0,"his3multi": 0,"avgturn":0,"unopenturn":0})


    data = 'ok'
    return aiohttp.web.Response(text=data)

async def makejinsonggamedayranksettle_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.info, "makejinsonggamedayranksettle_handle start")
    try:
        pw = request.rel_url.query.get('pw')
        date = request.rel_url.query.get('date') # "2021-10-05"

        if pw is None:
            return aiohttp.web.Response(text="pw is none")
        if pw != 'ssstarplaygogogo123E':
            return aiohttp.web.Response(text="pw is not good")
        if date is None:
            return aiohttp.web.Response(text="date is null")
        app = request.app
        redis_obj = app['redis']
        db = app['DB'][0]
        try:
            date = pg_general.strtodate(date).date()
        except Exception as e:
            return aiohttp.web.Response(text="date error")
        # 日榜結算
        result = await db.makejinsonggamedayranksettle(redis_obj, app, date)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makejinsonggamedayranksettle_handle except:{0}".format(e))
        return aiohttp.web.Response(text="not work")

    return aiohttp.web.Response(text="is ok")

async def makejinsongmonthprizesettle_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.info, "makejinsongmonthprizesettle_handle start")
    try:
        pw = request.rel_url.query.get('pw')
        date = request.rel_url.query.get('date') # ex: "2021-10-01" or "2021-10-16" must have 1 or 16 of day

        if pw is None:
            return aiohttp.web.Response(text="pw is none")
        if pw != 'ssstarplaygogogo123E':
            return aiohttp.web.Response(text="pw is not good")
        if date is None:
            return aiohttp.web.Response(text="date is null")

        app = request.app
        redis_obj = app['redis']
        db = app['DB'][0]
        try:
            date = pg_general.strtodate(date).date()
        except Exception as e:
            return aiohttp.web.Response(text="date error")
        if date.day != 1 and date.day != 16:
            return aiohttp.web.Response(text="day is not good")
        # 周榜結算
        result = await db.makejinsongmonthprizesettle(redis_obj, app, date.day, date)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makejinsongmonthprizesettle_handle except:{0}".format(e))
        return aiohttp.web.Response(text="not work")

    return aiohttp.web.Response(text="is ok")

async def createdbpool(app):
    db = PG_ASQLDB()

    await db.createpool()
    app["DB"].append(db)
    return

async def get_all_settings(app):
    # 拿到所有的設定值
    db = app['DB'][0]


    # headline_multipilier_content & setting win_content & setting
    result , data = await db.get_all_settings()
    if result == pg_general.Apiresult.success:
        app['rankminwin'] = data.get('rankminwin')      # 最低上榜的分數
        app['rankminmultipilier'] = data.get('rankminmultipilier')  # 最低上榜的倍數
        app['rankdaybonuscountdown'] = data.get('rankdaybonuscountdown')
        app['rankdaymultipilierinboxcontent'] = data.get('rankdaymultipilierinboxcontent')
        app['rankdaywininboxcontent'] = data.get('rankdaywininboxcontent')
        app['rankdaymultipilierinboxtitle'] = data.get('rankdaymultipilierinboxtitle')
        app['rankdaywininboxtitle'] = data.get('rankdaywininboxtitle')
        app["rankmonthbonuscountdown"] = data.get('rankmonthbonuscountdown')
        app["rankmonthmultipilierinboxcontent"] = data.get('rankmonthmultipilierinboxcontent')
        app["rankmonthmultipilierinboxtitle"] = data.get('rankmonthmultipilierinboxtitle')
        app["rankmonthwininboxcontent"] = data.get('rankmonthwininboxcontent')
        app["rankmonthwininboxtitle"] = data.get('rankmonthwininboxtitle')

        app['jpenable'] = data.get('jpenable')      # JP 是否開啟
        app['gameInfo'] = data.get('gameInfo')      # 遊戲資料
        app['cardinfo'] = data.get('cardinfo')      # 會員卡資料


        app['total_games'] = data.get('total_enabled_game_amount')      # 總共有幾款遊戲


    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_all_settings result:{0},resultdata={1}'.format(result,data))

async def get_lobby_server_ips(app):    # 定時抓 lobby server ips
    db = app['DB'][0]

    while(1):
        try:
            result , data = await db.get_lobby_server_ips()
            if result == pg_general.Apiresult.success:
                app['lobbyserverips'] = data
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "get_lobby_server_ips except:{0}".format(e))
        finally:
            await asyncio.sleep(5)

async def send_to_all_lobbyserver_future(app,item,sendmsg):
    try:
        realurl = 'http://{0}/broadcasttoall'.format(item)
        async with aiohttp.ClientSession() as session:
            response = await session.get(realurl, json=sendmsg)
            if response.status == 200:
                data = await response.text()
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                    'send_to_all_lobbyserver_future response:{0}'.format(data))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'send_to_all_lobbyserver_future except:{0}'.format(e))
        tempcount = app['lobbyserverips_error_count'].get(item)
        if tempcount is None:
            app['lobbyserverips_error_count'][item] = 1
        else:
            app['lobbyserverips_error_count'][item] = app['lobbyserverips_error_count'][item] + 1
            if app['lobbyserverips_error_count'][item] >=3:
                db = app['DB'][0]
                result_del_lobbyserver = await db.dellobbyserverip(item)


async def send_to_all_lobbyserver(app,sendmsg):
    try:
        if env_setting.LOCAL_SERVER == True:
            return
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
        lobbyserverips = app['lobbyserverips'].copy()
        if lobbyserverips != []:
            for item in lobbyserverips:
                asyncio.ensure_future(send_to_all_lobbyserver_future(app,item,sendmsg))


    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'send_to_all_lobbyserver , except:{0}'.format(e))
    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'send_to_all_lobbyserver , done')
async def getannouncement(app):
    while(1):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'getannouncement start')
            db = app['DB'][0]

            result, clientdata = await db.getannouncement()

            announcedata = {
                "commandid": 3000001,
                "announcement": clientdata
            }

            if result == pg_general.Apiresult.success:
                senddata = {
                    "type": 0,
                    "msg": announcedata
                }
                await send_to_all_lobbyserver(app,senddata)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,'getannouncement , except:{0}'.format(e))
        finally:
            await asyncio.sleep(30)

async def makerealtimerank(app):  # 做所有的及時榜單
    '''

    rich rank

    '''
    db = app['DB'][0]
    rankminwin = app['rankminwin']
    rankminmultipilier = app['rankminmultipilier']
    redis_obj = app['redis']
    upload_obj = app['uploadobj']
    while(1):
        try:
            # 計算每日龍虎榜單
            # 抓取上次的 taskinfo

            result = await db.makelivegamelist(app)

            # get 每日的前一分鐘不做 及時榜單 以及富豪榜單
            templocalstartdatetime = pg_general.get_local_start_datetime()
            templocaldatetimenow = pg_general.get_tw_datetime()
            if (templocaldatetimenow - templocalstartdatetime).total_seconds() <60:
                await asyncio.sleep(5)
                continue

            rankmode = await db.get_rank_mode()
            if rankmode == -1:
                raise Exception('get rankmode error')

            todayrankstarttime = pg_general.get_local_starttime_utc_str()
            todayrankendtime = pg_general.datetime_to_str(pg_general.getutcnow_datetime()-timedelta(seconds=30))
            todayrankindex = 0

            result , resultdata = await db.get_bethistory(todayrankstarttime,todayrankendtime,todayrankindex,rankminwin,rankminmultipilier,redis_obj,upload_obj,rankmode)

            # 找出 每一個 game 的 top win and top multipilier
            if result == pg_general.Apiresult.success and rankmode ==1:
                gamelist = {}
                for item in resultdata:
                    gameid = item.get('gameid')
                    rankwinlist = item.get('rankwin')
                    rankmultipilierlist = item.get('rankmultipilier')
                    if len(rankmultipilierlist)> 0:
                        topmultiplieravatar = "" if rankmultipilierlist[0].get('avatar') is None else rankmultipilierlist[0].get('avatar')
                        topmultiplier = rankmultipilierlist[0].get('amount')
                        topmultipliernickname = rankmultipilierlist[0].get('nickname')
                        topmultipliermemberid = rankmultipilierlist[0].get('memberid')

                    else:
                        topmultiplieravatar = ""
                        topmultiplier = -1
                        topmultipliernickname = ''
                        topmultipliermemberid = 0

                    if len(rankwinlist) > 0:
                        topwinavatar = "" if rankwinlist[0].get('avatar') is None else rankwinlist[0].get('avatar')
                        topwin = rankwinlist[0].get('amount')
                        topwinnickname = rankwinlist[0].get('nickname')
                        topwinmemberid = rankwinlist[0].get('memberid')

                    else:
                        topwinavatar = ""
                        topwin = -1
                        topwinnickname = ''
                        topwinmemberid = 0

                    gamelist[gameid] = {
                        "topmultiplieravatar":topmultiplieravatar,
                        "topmultiplier": topmultiplier,
                        "topmultipliernickname": topmultipliernickname,
                        "topmultipliermemberid": topmultipliermemberid,
                        "topwinavatar":topwinavatar,
                        "topwin": topwin,
                        "topwinnickname": topwinnickname,
                        "topwinmemberid": topwinmemberid
                    }


                # send_to_lobby_data = {
                #     "type":0,
                #     "msg":{
                #         "commandid": 3000003,
                #         "gamelist": gamelist
                #     }
                # }
                # await send_to_all_lobbyserver(app,send_to_lobby_data)
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'makeallrank get_bethistory ValueError, except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'makeallrank get_bethistory , except:{0}'.format(e))

        finally:
            await asyncio.sleep(15)



        try:
            # 計算富豪榜單
            result = await db.makerichrank(redis_obj,upload_obj)



        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'makeallrank ValueError, except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'makeallrank , except:{0}'.format(e))

        finally:
            await asyncio.sleep(30)

# 做日結算 以及 產生月的即時資料
async def makedayranksettle(app):
    db = app["DB"][0]

    while(1):
        try:
            # 先抓 setting.gamedayranksettledate 來確認是否有哪一天沒有結算
            nowtime = pg_general.get_local_nowdatetime()
            if nowtime.hour == 0 and nowtime.minute == 0 and nowtime.second < 30:
                continue

            # 做 day rank live data
            result = await db.makedayranksettle(app)

            # 結算 monthly rank live data
            result = await db.makemonthlivedata(app)

            # 結算 history monthly data
            result = await db.makerankhistorydata(app)





        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'makedayranksettle , except:{0}'.format(e))
        finally:
            await asyncio.sleep(60)





async def checkfeedback(app):
    telebot = app["telebot"]
    db = app['DB'][0]
    while(1):
        try:
            result, msg = await db.getfeedback()
            if len(msg)>0:
                telebot.sendfeedbackmsg(msg,'feedback')



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'checkfeedback , except:{0}'.format(e))
        finally:
            await asyncio.sleep(10)

async def checkconcurrentuser(app):
    db = app['DB'][0]
    redis_obj = app['redis']
    while (1):
        try:
            lobbyips = []
            lobbyips = app['lobbyserverips'].copy()

            if env_setting.LOCAL_SERVER == True:
                lobbyips =['127.0.0.1']

            amount = 0
            if len(lobbyips) > 0 :
                for item in lobbyips:
                    realurl = 'http://' + item + '/concurrent_user?checkflag=1'
                    try:
                        async with aiohttp.ClientSession() as session:
                            response = await session.get(realurl)
                            if response.status == 200:
                                tempamount = await response.text()
                                amount = amount + pg_general.converttype(tempamount,int)
                    except Exception as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'checkconcurrentuser , except:{0}'.format(e))



            result = await db.writeconcurrentuser(amount)
            redis_result = await redis_obj.set_value("concurrent_user",amount)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'checkconcurrentuser , except:{0}'.format(e))
        finally:
            await asyncio.sleep(60)



async def initialredis(app):
    pg_general.writelog(pg_general.PG_LogerLevel.info, "initial redis server connection start")
    redis = PGRedis()
    app['redis'] = redis
    if redis.initialflag:
        pg_general.writelog(pg_general.PG_LogerLevel.info, "initial redis server connection end")
    else:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "initial redis server connection error")


async def bonus_dateline_inbox(app):
    try:
        db = app['DB'][0]
        pg_general.writelog(pg_general.PG_LogerLevel.info, "bonus_dateline_inbox start")

        result , token = await db.get_bonus_index_exceed_date_line()

        # token = [
        #     "dFDmvx_6XWM:APA91bFVPweU1WlIHGbd6RXKlQn_AHYfyMhDpYvKmMqxPqy5OkmyVHCRbSxF-JCu9CBEdT4SrTU9pKwGRbSkTTrc39mZuoSdpPFU_B05VPu3x8n6rFrmhYwI7puEjwQWjFRKmICv6c97"]
        pass

        # await pg_fcm.send_notification_multiple_device(token)

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "bonus_dateline_inbox error : {}".format(e))

        pg_general.writelog(pg_general.PG_LogerLevel.info, "bonus_dateline_inbox end")


async def del_announcement_task(app):
    db = app['DB'][0]
    pg_general.writelog(pg_general.PG_LogerLevel.info, "del_announcement_task start")
    result = await db.del_announcement_task()


    pg_general.writelog(pg_general.PG_LogerLevel.info, "del_announcement_task end")

async def getchannellist(app):
    db = app['DB'][0]
    redis_obj = app['redis']
    while(1):
        try:
            result, channellist = await db.getchannellist(redis_obj)
            if result ==True:
                senddata = {
                    "type": 0,
                    "msg": channellist
                }
                await send_to_all_lobbyserver(app, senddata)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "getchannellist error:{}".format(e))
        finally:
            if env_setting.PRODUCTION_MODE == False:
                await asyncio.sleep(10)
            else:
                await asyncio.sleep(60)

async def updateofficialactiontoredis(app):
    db = app['DB'][0]
    redis_obj = app['redis']

    while (1):
        try:
            await db.updateofficialactiontoredis(redis_obj)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "getchannellist error:{}".format(e))
        finally:
                await asyncio.sleep(60)

async def make_bethistory_summary(app):
    db = app['DB'][0]
    redis_obj = app['redis']
    try:
        await db.make_bethistory_summary(redis_obj)



    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "make_bethistory_summary error:{}".format(e))
    finally:
           pass

async def clear_bethistory_daily_data(app):
    db = app['DB'][0]
    redis_obj = app['redis']
    cardinfo = app['cardinfo']
    try:
        await db.clear_bethistory_daily_data(redis_obj,cardinfo)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "clear_bethistory_daily_data error:{}".format(e))
    finally:
        pass

async def makesuspenselist_job(app):        # 製作停權名單 給 web
    db = app['DB'][0]
    upload_obj = app['uploadobj']
    try:
        await db.makesuspenselist(upload_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makesuspenselist_job error:{}".format(e))
    finally:
        pass

async def makenewslist_job(app):            # 製作 news list for web
    db = app['DB'][0]
    upload_obj = app['uploadobj']
    try:
        await db.makenewslist(upload_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makenewslist_job error:{}".format(e))
    finally:
        pass

async def returngift_job(app):              # 每日將過期的 gif 退回
    db = app['DB'][0]
    redis_obj = app['redis']
    try:
        await db.returngift(redis_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "returngift_job error:{}".format(e))
    finally:
        pass

async def makedailysummaryreportrequest(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    telebotobj = app['telebot']
    try:
        await db.makedailysummaryreport(redis_obj, telebotobj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makedailysummaryreportrequest error:{}".format(e))
    finally:
        return aiohttp.web.Response(text='done')
async def makedailysummaryreport(app):      # 製作前一日的 daily summary report
    db = app['DB'][0]
    redis_obj = app['redis']
    telebotobj = app['telebot']
    try:
        await db.makedailysummaryreport(redis_obj,telebotobj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makedailysummaryreport error:{}".format(e))
    finally:
        pass

async def get_makeproreporttouser(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    try:
        asyncio.ensure_future(db.makeproreporttouser(redis_obj))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "get_makeproreporttouser error:{}".format(e))
    finally:
        return aiohttp.web.Response(text='done')


async def service_to_user_handle(request):
    app = request.app
    db = app['DB'][0]
    try:
        response_data = 'error 1'

        memberid = request.rel_url.query.get('memberid')
        content = request.rel_url.query.get('content')
        if None in [memberid,content]:
            response_data = 'memberid or content is empty !!'
        else:
            response_data = await db.service_to_user(memberid,content)

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "service_to_user error:{}".format(e))
    finally:
        return aiohttp.web.Response(text=response_data)





async def makelikerank(app):                # 製作即時人氣榜單
    db = app['DB'][0]
    redis_obj = app['redis']

    while(1):
        try:
            await db.makelikerank(redis_obj)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "makelikerank error:{}".format(e))

        await asyncio.sleep(60)

async def jppool_broadcast(app):            # 廣播 jp pool
    db = app['DB'][0]
    redis_obj = app['redis']
    try:
        await db.jppool_broadcast(redis_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "jppool_broadcast error:{}".format(e))

async def makepayconfig(app):               # make payment config for web server
    db = app['DB'][0]
    upload_obj = app['uploadobj']
    try:
        await db.makepayconfig(upload_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makepayconfig error:{}".format(e))

async def makewebad(app):                   # make web AD
    db = app['DB'][0]
    upload_obj = app['uploadobj']
    try:
        await db.makewebad(upload_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makewebad error:{}".format(e))

async def makesignal_redis(app):        # make signal action redis data
    redis_obj = app['redis']
    db = app['DB'][0]
    try:
        result = await db.make_signal_action_redis(redis_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makesignal_redis error:{}".format(e))

async def makeproreporttouser(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    try:
        result = await db.makeproreporttouser(redis_obj)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makeproreporttouser error:{}".format(e))

async def makeclearjobflagandcarddata(app):
    redis_obj = app['redis']
    db = app['DB'][0]

    while(1):
        try:
            result = await db.makeclearjobflagandcarddata(app)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "makeclearjobflagandcarddata error:{}".format(e))
        await asyncio.sleep(15)

async def clearseats_job(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    while(1):
        try:
            result = await db.clearseats_job(redis_obj,app)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "clearseats_job error:{}".format(e))
        await asyncio.sleep(2)

async def broadcast_jinsongprize(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    while (1):
        try:
            result = await db.broadcast_jinsongprize(redis_obj, app)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "broadcast_jinsongprize error:{}".format(e))
        await asyncio.sleep(30)

async def make_jinsongprize_live(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    while (1):
        try:
            result = await db.make_jinsongprize_live(redis_obj, app)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "make_jinsongprize_live error:{}".format(e))
        await asyncio.sleep(60)

async def make_new_dragon_tiger_rank_live(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    upload_obj = app['uploadobj']
    while(1):
        try:
            result = await db.make_new_dragon_tiger_rank_live(redis_obj,app,upload_obj)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"make_new_dragon_tiger_rank_live:{}".format(e))
        await asyncio.sleep(60)

async def clear_fish_game_credit_account(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    while(1):
        try:
            result = await db.clear_fish_game_credit_account(redis_obj,app)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "clear_fish_game_credit_account:{}".format(e))

        await asyncio.sleep(10)

async def sendtelebot(msg):
    try:
        result = False
        CS_BOT_API_TOKEN = '1443273366:AAH24wGmJIDYJEQharElwMtQNPOPMGPuFf8'
        CS_CHATROOM_ID = -373321094

        SERVICE_CHATROOM_URL = 'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}'.format(CS_BOT_API_TOKEN,CS_CHATROOM_ID,msg)
        async with aiohttp.ClientSession() as session:
            async with session.get(SERVICE_CHATROOM_URL, timeout=60) as response:
                if response.status == 200:
                    result = True

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:sendtelebot except: {0}'.format(e))
    return result






async def check_telegram_CS_bot(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    last_chatroom_updateid = await redis_obj.get_value('telegram_bot_cs_last_chatroom_update_id')
    if last_chatroom_updateid is None:
        last_chatroom_updateid = 0
    else:
        last_chatroom_updateid = pg_general.converttype(last_chatroom_updateid,int)

    CS_BOT_API_TOKEN = '1443273366:AAH24wGmJIDYJEQharElwMtQNPOPMGPuFf8'
    url = 'https://api.telegram.org/bot{}/getUpdates?offset={}'.format(CS_BOT_API_TOKEN,last_chatroom_updateid)
    CS_CHATROOM_ID = -373321094
    while(1):
        try:
            respdict = {}
            async with aiohttp.ClientSession() as session:
                response = await session.get(url)
                if response.status == 200:
                    respdict = await response.json()

            if respdict == {} or respdict is None:
                raise Exception('no data')

            okflag = respdict.get('ok')
            if okflag != True:
                raise Exception('error')
            result = respdict.get('result')
            if result is None:
                raise Exception('error')
            if len(result) < 1:
                raise Exception('no data')
            for item in result:
                tempupdateid = item.get("update_id")
                if last_chatroom_updateid >= tempupdateid:
                    continue
                last_chatroom_updateid = tempupdateid
                await redis_obj.set_value('telegram_bot_cs_last_chatroom_update_id',last_chatroom_updateid,86400*100)
                message = item.get('message')

                chatroomid = message['chat']['id']
                if CS_CHATROOM_ID != chatroomid:
                    continue
                chattext = message['text']
                if '@JinsongCSBot' not in chattext:
                    continue
                chattextlist = chattext.split(' ')
                if len(chattextlist) < 2:
                    await sendtelebot('格式錯誤1 : {}'.format(chattext))
                    continue

                if '@JinsongCSBot help' == chattext.strip():

                    sendstr = 'help 說明\n'
                    sendstr += '{memberid} = 會員編號\n{content} = 要傳送的內容\n{phone} = 手機號碼\n\n'
                    sendstr += '{memberid}***{content} 傳送 app 內客服訊息\n\n'
                    sendstr += '{memberid}**2**{content} 傳送簡訊到此會員手機號碼\n\n'
                    sendstr += '{memberid}**3** 查詢會員相關資料\n\n'
                    sendstr += '{phone}**4** 使用手機查詢會員編號\n\n'

                    await sendtelebot(sendstr)
                    continue
                if '***' in chattext:   # service
                    tempchattextlist = ' '.join(chattextlist[1:]).split('***')
                    if len(tempchattextlist) != 2:
                        await sendtelebot('格式錯誤2 : {}'.format(' '.join(chattextlist[1:])))
                        continue

                    memberid = pg_general.converttype(tempchattextlist[0],int)
                    content = tempchattextlist[1]

                    if memberid is None or content is None:
                        await sendtelebot('格式錯誤3 : {}'.format(' '.join(chattextlist[1:])))
                        continue

                    response_data = await db.service_to_user(memberid, content)
                    await sendtelebot('傳送成功 : {},{}'.format(memberid,content))
                elif '**1**' in chattext:   # 傳送  username 到綁定手機
                    memberid = pg_general.converttype(chattextlist[1].split('**1**')[0],int)
                    if memberid is None:
                        await sendtelebot('格式錯誤4 : {}'.format(' '.join(chattextlist[1:])))
                        continue
                    result,clientdata = await db.getmemberinfo(memberid)
                    if result == False:
                        await sendtelebot('找不到此會員')


                elif '**2**' in chattext:   # 傳送 自訂義訊息到綁定手機
                    memberid = pg_general.converttype(chattextlist[1].split('**2**')[0], int)
                    if memberid is None:
                        await sendtelebot('格式錯誤6 : {}'.format(' '.join(chattextlist[1:])))
                        continue

                    tempcontent = chattext.split('**2**')[1].strip()
                    if len(tempcontent) <=0:
                        await sendtelebot('格式錯誤')
                        continue

                    result,clientdata = await db.getmemberinfo(memberid)
                    if result == False:
                        await sendtelebot('找不到此會員')
                        continue
                    tempphone = clientdata.get('phone')
                    if tempphone[:2] != '09':
                        await sendtelebot('此會員手機號碼有誤,或是沒有綁定')
                        continue

                    result = await pg_sms.sendsms(tempphone,tempcontent)

                    await sendtelebot('傳送簡訊成功, phone: {}, content: {}'.format(tempphone,tempcontent))

                elif '**3**' in chattext:   # 查詢 user 相關資料

                    memberid = pg_general.converttype(chattextlist[1].split('**3**')[0], int)

                    if memberid is None:
                        await sendtelebot('格式錯誤5 : {}'.format(' '.join(chattextlist[1:])))
                        continue
                    result, clientdata = await db.getmemberinfo(memberid)
                    if result == False:
                        await sendtelebot('找不到此會員')
                    # clientdata = {
                    #     "nickname": data.get('nickname'),
                    #     "username": data.get('username'),
                    #     "phone": data.get('phone'),
                    #     "card": data.get('card'),
                    #     "level": data.get('level'),
                    #     "credit": data.get('credit'),
                    #     "silvercredit": data.get('silvercredit'),
                    #     "point": data.get('point'),
                    #     "safe": data.get('safe')
                    # }
                    sendstr = 'memberid: {}\n'.format(memberid)
                    sendstr += 'nickname: {}\n'.format(clientdata.get('nickname'))
                    sendstr += 'username: {}\n'.format(clientdata.get('username'))
                    sendstr += 'fbid: {}\n'.format(clientdata.get('fbid'))
                    sendstr += 'appleid: {}\n'.format(clientdata.get('auserid'))
                    sendstr += 'phone: {}\n'.format(clientdata.get('phone'))
                    sendstr += 'card: {}\n'.format(clientdata.get('card'))
                    sendstr += 'level: {}\n'.format(clientdata.get('level'))
                    sendstr += 'credit: {:,}\n'.format(clientdata.get('credit'))
                    sendstr += 'silvercredit: {:,}\n'.format(clientdata.get('silvercredit'))
                    sendstr += 'point: {:,}\n'.format(clientdata.get('point'))
                    sendstr += 'safe: {:,}\n'.format(clientdata.get('safe'))
                    await sendtelebot(sendstr)
                elif '**4**' in chattext: # 用手機號查memberid
                    phone = chattextlist[1].split('**4**')[0]
                    if phone [:2] != '09':
                        await sendtelebot('手機號碼錯誤 : {}'.format(' '.join(chattextlist[1:])))
                        continue
                    result, clientdata = await db.getmemberfromphone(phone)
                    if result == False:
                        await sendtelebot('查詢手機號碼錯誤 : {}'.format(' '.join(chattextlist[1:])))
                        continue
                    phonelist = clientdata.get('phonelist')
                    phonelist = list(map(str,phonelist))
                    await sendtelebot('查詢到的memberid list : {}\n'.format(','.join(phonelist)))

        except Exception as e:
            pass
        await asyncio.sleep(15)




async def makejinsonggamedayranksettle(app):
    redis_obj = app['redis']
    db = app['DB'][0]
    try:
        # 日榜結算
        result = await db.makejinsonggamedayranksettle(redis_obj, app)

        localdate = pg_general.get_local_date()

        # 周榜結算
        # 判斷現在是否是星期天
        if localdate.weekday() == 6:
            result = await db.makejinsonggameweekranksettle(redis_obj,app)


        #金爽月榜結算
        # 判斷是否有 日 每月一日
        if localdate.day ==1 or localdate.day == 16:
            result = await db.makejinsongmonthprizesettle(redis_obj,app,localdate.day)



    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makejinsonggamedayranksettle:{}".format(e))

async def makeactivenumbersettle(app):          # 作每日活躍指數調整
    try:
        redis_obj = app['redis']
        db = app['DB'][0]

        result = await db.makeactivenumbersettle(redis_obj,app)


    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "makeactivenumbersettle:{}".format(e))

async def get_fish_game_bethistory(app):    # 撈魚機 bethistory
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.info, "get_fish_game_bethistory start")
        db = app['DB'][0]
        redis_obj = app['redis']


        result = await db.get_fish_game_bethistory(app,redis_obj)



    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "get_fish_game_bethistory:{}".format(e))



async def openfreewheelaction(app):
    db = app['DB'][0]
    redis_obj = app['redis']

    result = await db.openfreewheelaction(redis_obj)

async def senddailybonus_notification(app):
    db = app['DB'][0]
    redis_obj = app['redis']

    await db.senddailybonus_notification(redis_obj)

async def noticeuserinboxdateline(app):
    db = app['DB'][0]
    redis_obj = app['redis']

    await db.noticeuserinboxdateline(redis_obj)
#
async def testurl(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']

    try:
        asyncio.ensure_future(db.makejinsonggamedayranksettle(redis_obj, app))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "testurl error:{}".format(e))
    finally:
        return aiohttp.web.Response(text='done')


def main():
    try:
        if not env_setting.LOCAL_SERVER:
            time.sleep(10)
        pg_general.writelog(pg_general.PG_LogerLevel.debug, "control server start...")

        loop = asyncio.get_event_loop()
        app = aiohttp.web.Application()
        app["DB"] = []
        app['gamedayranksettletasktime'] = pg_general.strtodatetime('1970-01-01 00:00:00')
        app["lobbyserverips"] = []
        app["lobbyserverips_error_count"] = {}
        app["telebot"] = PG_TELEBOT()
        app["uploadobj"] = PG_RANKUPLOAD()



        # initial Redis object
        loop.run_until_complete(initialredis(app))

        # create db connection
        loop.run_until_complete(createdbpool(app))
        loop.run_until_complete(get_all_settings(app))
        # 定時抓 lobby server ips
        asyncio.ensure_future(get_lobby_server_ips(app))


        # 抓公告傳給 所有 lobby server 傳送給所有玩家
        asyncio.ensure_future(getannouncement(app))

        # 做及時的榜單
        asyncio.ensure_future(makerealtimerank(app))

        # 做日榜結算
        asyncio.ensure_future(makedayranksettle(app))


        # 定時 check feedback and send to telegram
        asyncio.ensure_future(checkfeedback(app))

        # 每一分鐘 check concurrent user log
        asyncio.ensure_future(checkconcurrentuser(app))

        # 每五分鐘做一次 廣播 channellist
        asyncio.ensure_future(getchannellist(app))

        # 每一分中更新一次 官方通知與官方活動到 redis
        asyncio.ensure_future(updateofficialactiontoredis(app))

        # 每一分鐘做一次人氣榜單
        asyncio.ensure_future(makelikerank(app))

        loop.run_until_complete(app['DB'][0].makeclearjobflagandcarddata(app))

        asyncio.ensure_future(makeclearjobflagandcarddata(app))

        # 清除座位
        asyncio.ensure_future(clearseats_job(app))

        # 廣播金爽及時榜單
        asyncio.ensure_future(broadcast_jinsongprize(app))

        # 座金爽榜及時榜單
        asyncio.ensure_future(make_jinsongprize_live(app))

        # 做新的龍虎榜 live
        asyncio.ensure_future(make_new_dragon_tiger_rank_live(app))

        # clear fish game credit account
        asyncio.ensure_future(clear_fish_game_credit_account(app))



        #app.router.add_route('GET', '/getannouncement/',getannouncement_handle)

        if env_setting.PRODUCTION_MODE == True:
            asyncio.ensure_future(check_telegram_CS_bot(app))



        # for system debug using
        app.router.add_route('GET', '/healthycheck', healthycheck_handle)  # return 'check' for healthy check
        app.router.add_route('GET', '/allusers', allusers_handle)
        app.router.add_route('GET', '/allmallhistory', allmallhistory_handle) # return mallhistory, gashwalletdeposite 5 records
        app.router.add_route('POST', '/getservicechat', getservicechat_handle)
        app.router.add_route('GET', '/createseats', createseats_handle)
        app.router.add_route('GET', '/delgoldseats', delgoldseats_handle)
        app.router.add_route('GET', '/delsilverseats', delsilverseats_handle)
        app.router.add_route('GET', '/getredis',getredisdata_handle)
        app.router.add_route('GET', '/makeserialtable', makeserialtable_handle)
        app.router.add_route('GET', '/makepromotiontoinbox', makepromotiontoinbox_handle)
        app.router.add_route('GET', '/makedailysummaryreportrequest', makedailysummaryreportrequest)
        app.router.add_route('GET', '/get_makeproreporttouser', get_makeproreporttouser)
        app.router.add_route('GET', '/service_to_user', service_to_user_handle)
        app.router.add_route('GET', '/delgameseat', delgameseat_handle)
        app.router.add_route('GET', '/testurl/', testurl)
        app.router.add_route('GET', '/makegamedayranksettle', makejinsonggamedayranksettle_handle)  # 手動製作日榜榜單(補異常榜單用)
        app.router.add_route('GET', '/makegmonthprizesettle', makejinsongmonthprizesettle_handle)  # 手動製作周榜單(補異常榜單用)



        # scheduler 抓明天過期 bonus mail token
        scheduler = AsyncIOScheduler()
        # 做 信件 快到期 推播通知
         # scheduler.add_job(bonus_dateline_inbox, 'cron', second='0,10,20,30,40,50',args=[app])

        scheduler.add_job(del_announcement_task,'cron',second='0',args=[app]) # 每一分中做一次 檢查刪除 公告
        scheduler.add_job(make_bethistory_summary,'interval', days=1,start_date='2020-01-01 00:00:20',timezone='Asia/Taipei',args=[app])
        scheduler.add_job(clear_bethistory_daily_data,'interval', days=1,start_date='2020-01-01 00:00:00',timezone='Asia/Taipei',args=[app])
        scheduler.add_job(makesuspenselist_job,'interval',minutes=10,start_date='2020-01-01 00:05:05',timezone='Asia/Taipei',args=[app])
        scheduler.add_job(makenewslist_job,'interval',minutes=5,start_date='2020-01-01 00:00:45',timezone='Asia/Taipei',args=[app])
        scheduler.add_job(returngift_job,'interval',minutes=15,start_date='2020-01-01 00:01:30',timezone='Asia/Taipei',args=[app])
        if app['jpenable'] == 1:
            scheduler.add_job(jppool_broadcast, 'interval',seconds=10,start_date='2020-01-01 00:00:03', timezone='Asia/Taipei',args=[app])        # 廣播 jp pool

        if env_setting.PRODUCTION_MODE == True:     # 正是機才做報表
            scheduler.add_job(makedailysummaryreport, 'interval', days=1,start_date='2020-01-01 00:15:00', timezone='Asia/Taipei',args=[app])      # make daily summary report
        scheduler.add_job(makepayconfig, 'interval', seconds=10, start_date='2020-01-01 00:00:00', timezone='Asia/Taipei', args=[app])           # make payment config for web server
        scheduler.add_job(makewebad,'interval', seconds=60, start_date='2020-01-01 00:00:00', timezone='Asia/Taipei', args=[app])               # make webad
        scheduler.add_job(makesignal_redis,'interval', days=1,start_date='2020-01-01 20:00:00',timezone='Asia/Taipei',args=[app])           # make signal action redis data
        scheduler.add_job(makeproreporttouser,'interval',days=1,start_date='2020-01-01 00:10:00',timezone='Asia/Taipei',args=[app])         # make 活動 report to user
        scheduler.add_job(openfreewheelaction,'interval',days=1,start_date='2020-01-01 20:00:00', timezone='Asia/Taipei', args=[app])
        scheduler.add_job(senddailybonus_notification,'interval',days=1,start_date='2020-01-01 12:03:00', timezone='Asia/Taipei', args=[app])
        scheduler.add_job(senddailybonus_notification,'interval', days=1, start_date='2020-01-01 20:32:00', timezone='Asia/Taipei', args=[app])
        scheduler.add_job(noticeuserinboxdateline,'interval',days=1,start_date = '2020-01-01 12:00:00', timezone='Asia/Taipei', args=[app])
        scheduler.add_job(makejinsonggamedayranksettle, 'interval', days=1,start_date='2020-01-01 00:01:00', timezone='Asia/Taipei', args=[app])    # 新的日榜 周榜 月榜結算
        scheduler.add_job(makeactivenumbersettle, 'interval', days=1,start_date='2020-01-01 00:20:00', timezone='Asia/Taipei', args=[app])          # 每日做活躍指數調整
        scheduler.add_job(get_fish_game_bethistory, 'interval', minutes=1, start_date='2020-01-01 00:00:00', timezone='Asia/Taipei', args=[app])       # 撈魚機 bethistory
        scheduler.start()





        aiohttp.web.run_app(app, host="0.0.0.0", port=PORT)
    except:
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            'main all except:{0}'.format(sys.exc_info()[0]))


if __name__ == '__main__':
    pg_general.loggerinit()
    main()


