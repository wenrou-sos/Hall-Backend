import asyncio
import os
import aiohttp.web
import sys
import time
import env_setting
import pg_general
from pg_asqldb import PG_ASQLDB
from enum import IntEnum
from pg_fbavatar import PG_FBAVATAR,AVATAR_SYSTEM
from pg_redis import PGRedis
from pg_general import SendMsgType
import pg_namesample
import requests

from urllib import parse
import hashlib
import json
import datetime
import pytz
import string
import random


HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 81))


PREFIX = 'PG'
PREFIX_S = 'PGS'





async def healthycheck_handle(request):
    return aiohttp.web.Response(text='check')

async def serverinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'serverinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    logintoken = request.match_info["slogintoken"]

    ver = request.rel_url.query.get('ver')
    rer = request.rel_url.query.get('rer')
    platform = pg_general.converttype(request.rel_url.query.get('platform'),int)


    if logintoken is not None:
        result, clientdata = await db.getserverinfo(logintoken,ver,rer,platform)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            clientdata['useagreement'] = app['useagreement']
            clientdata['privacyagreement'] = app['privacyagreement']
            clientdata['gameagreement'] = app['gameagreement']
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'serverinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    return aiohttp.web.json_response(resultdata)

async def login_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'login_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    fbavatarobj = app["pg_fbavatar"]
    redis_obj = app['redis']
    defaultchannelindex = app['defaultchannelindex']
    fblink = app['fblink']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    logintoken = request.match_info["slogintoken"]
    deviceid = request.rel_url.query.get("deviceid")
    newaccflag = pg_general.converttype(request.rel_url.query.get('newaccflag'),int)
    username = request.rel_url.query.get('username')
    password = request.rel_url.query.get('password')
    fbid = request.rel_url.query.get("fbid")
    fbtoken = request.rel_url.query.get("fbtoken")
    fbavatar = request.rel_url.query.get("fbavatar")
    fbnickname = request.rel_url.query.get("fbnickname")
    ip = request.rel_url.query.get("ip")
    platform = pg_general.converttype(request.rel_url.query.get("platform"), int)
    devicedescription = request.rel_url.query.get("devicedescription")
    lobbyserverip = request.rel_url.query.get("lobbyserverip")
    region = request.rel_url.query.get('region')
    region_sub = request.rel_url.query.get('region_sub')
    city = request.rel_url.query.get('city')
    fcmtoken = request.rel_url.query.get('fcmtoken')
    ver = request.rel_url.query.get('ver')
    rer = request.rel_url.query.get('rer')
    connecttype = request.rel_url.query.get('connecttype')
    auserid = request.rel_url.query.get('auserid')
    aauthcode = request.rel_url.query.get('aauthcode')
    atoken = request.rel_url.query.get('atoken')

    if logintoken is not None and deviceid is not None and platform is not None and newaccflag is not None:
        result, clientdata, serverdata = await db.login(redis_obj,fblink,defaultchannelindex,fbavatarobj,logintoken, deviceid, fbid,fbtoken,fbavatar,fbnickname,
                                                        ip, platform, devicedescription,lobbyserverip,region,region_sub,city,fcmtoken,ver,rer,username,password,newaccflag,connecttype,auserid,aauthcode,atoken)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success and clientdata.get('result')==0:

            # 加入 dailywheelflag , dailywigninflag
            clientdata['dailywheelflag'] = app['dailywheelflag']
            clientdata['chatroomflag'] = app['chatroomflag']
            clientdata['jpenable'] = True if app['jpenable'] == 1 else False
            if app['jpenable'] ==  1:
                # get redis jppool data
                jppool = await redis_obj.get_json_value("jppool")
                clientdata['jppool'] = jppool

            # 加入 jinsongprizeenable , jinsongprize
            clientdata['jinsongprizeenable'] = True if app['jinsongprizeenable'] ==1 else False
            jinsongprize = await redis_obj.get_json_value('jinsongprizesetting')
            if jinsongprize is not None:
                clientdata['jinsongprize'] = pg_general.converttype(jinsongprize.get('totaljinsongprize'),int)


            resultdata['clientdata'] = clientdata
            resultdata['serverdata'] = serverdata

            if env_setting.SIGNINPS_FLAG ==True:
                data = ''
                # call ps game server sign in
                memberid = serverdata.get('memberid')
                pg_general.writelog(pg_general.PG_LogerLevel.debug, 'login_handle signin ps memberid:{0},logintoken:{1}'.format(memberid,logintoken))

                psgameserverresult = pg_general.Apiresult.psloginerror
                psgameserverresult_silver = pg_general.Apiresult.psloginerror
                # call ps signin for gold
                url = env_setting.PS_API_SERVER_URL + 'host/signin/?prefix={0}&member_id={1}&password={2}'.format(PREFIX, memberid,logintoken)
                errcount = 0
                pg_general.writelog(pg_general.PG_LogerLevel.debug,'login_handle gold signin url:{0}'.format(url))
                uidparam = {}
                for _err in range(3):
                    try:
                        # call ps signin api
                        if env_setting.LOCAL_SERVER == False:

                            async with aiohttp.ClientSession() as session:
                                async with session.get(url,timeout= 60) as response:
                                    if response.status == 200:
                                        data = await response.json()
                                        if int(data.get('status_code')) != 0:
                                            psgameserverresult = pg_general.Apiresult.connectdberror
                                            raise ValueError('can not sign in user gold')
                                        psgameserverresult = pg_general.Apiresult.success
                                        resultdata['clientdata']['gameserver'] = data.get("server_info").get("slot")
                                        resultdata['clientdata']['fishserver'] = data.get('server_info').get('fish')
                                        hostid = data.get('host_id')
                                        resultdata['clientdata']['logintoken'] = logintoken + '(*--)' + hostid
                                        uidparam['uid_g'] = data.get('uid')
                                        break
                                    else:
                                        data = await response.text()
                        else:
                            psgameserverresult = pg_general.Apiresult.success
                        await asyncio.sleep(0)
                    except ValueError as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'login_handle gold signin ValueError:{0}'.format(e))
                        break
                    except Exception as e:
                        errcount += 1
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'login_handle gold signin except:{0},errcount:{1},data:{2}'.format(e,errcount,data))
                        await asyncio.sleep(0)
                pg_general.writelog(pg_general.PG_LogerLevel.debug, 'login_handle gold signin result:{0}, recv:{1}'.format(psgameserverresult,data))

                # call ps signin for silver
                url = env_setting.PS_API_SERVER_URL + 'host/signin/?prefix={0}&member_id={1}&password={2}'.format(PREFIX_S, memberid,
                                                                                                      logintoken)
                errcount = 0
                pg_general.writelog(pg_general.PG_LogerLevel.debug, 'login_handle silver signin url:{0}'.format(url))
                for _err in range(3):
                    try:
                        # call ps signin api
                        if env_setting.LOCAL_SERVER == False:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(url, timeout=60) as response:
                                    if response.status == 200:
                                        data = await response.json()
                                        if int(data.get('status_code')) != 0:
                                            psgameserverresult_silver = pg_general.Apiresult.connectdberror
                                            raise ValueError('can not sign in user silver')
                                        psgameserverresult_silver = pg_general.Apiresult.success
                                        resultdata['clientdata']['gameserver_silver'] = data.get("server_info").get("slot")
                                        hostid = data.get('host_id')
                                        resultdata['clientdata']['logintoken_silver'] = logintoken + '(*--)' + hostid
                                        uidparam['uid_s'] = data.get('uid')
                                        break
                                    else:
                                        data = await response.text()
                        else:
                            psgameserverresult_silver = pg_general.Apiresult.success
                        await asyncio.sleep(0)
                    except ValueError as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'login_handle silver signin ValueError:{0}'.format(e))
                        break
                    except Exception as e:
                        errcount += 1
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'login_handle silver signin except:{0},errcount:{1},data:{2}'.format(e, errcount,
                                                                                                          data))
                        await asyncio.sleep(0)
                pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                    'login_handle silver signin result:{0}, recv:{1}'.format(psgameserverresult_silver, data))

                asyncio.ensure_future(db.saveloginuid(logintoken,memberid,uidparam))
                # resultdata['apiresult'] = pg_general.Apiresult.success if psgameserverresult == psgameserverresult_silver == pg_general.Apiresult.success else pg_general.Apiresult.psloginerror
                resultdata['apiresult'] = psgameserverresult
            else:
                resultdata['apiresult'] = pg_general.Apiresult.success
        else:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'login_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    return aiohttp.web.json_response(resultdata)


async def logout_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'logout_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if memberid is not None and logintoken is not None:
        result = await db.updatememberlogout(memberid, logintoken)
        resultdata['apiresult'] = result
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'logout_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    return aiohttp.web.json_response(resultdata)


async def getmemberinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getmemberinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }



    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]
    param_memberid = pg_general.converttype(request.rel_url.query.get('param_memberid'),int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()


    if memberid is not None and logintoken is not None:
        result, clientdata = await db.getmemberinfo(redis_obj,logintoken, memberid,param_memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            # resultdata"isfirstbuy": data.get('isfirstbuy'),
            # "registrationdatetime": registrationdatetime
            clientdata.pop('isfirstbuy',None)
            clientdata.pop('registrationdatetime',None)
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getmemberinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)




async def updatetutorialstate_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'updatetutorialstate_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    result, award, credit = await db.updatetutorialstate(logintoken, memberid)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = {
            "result": 0,
            "award": award,
            "credit": credit,
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'updatetutorialstate_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def updateprofile_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'updateprofile_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]
    nickname = request.rel_url.query.get("nickname")

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()


    if None not in [memberid,logintoken,nickname]:
        result, clientdata = await db.updateprofile(logintoken, memberid,  nickname)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'updateprofile_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)



async def getdailybonusinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getdailybonusinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if memberid is not None and logintoken is not None:
        result, clientdata = await db.getdailybonusinfo(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getdailybonusinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def spindailybonus_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'spindailybonus_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if memberid is not None and logintoken is not None:
        result, clientdata = await db.spindailybonus(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getdailybonusinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)








async def getpiggyinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getpiggyinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if memberid is not None and logintoken is not None:
        result, clientdata = await db.getpiggyinfo(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getpiggyinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def getmallinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getmallinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]
    mode = request.rel_url.query.get('mode')
    if mode is None:
        mode = 0
    else:
        mode = pg_general.converttype(mode,int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid,logintoken,mode]:
        result, clientdata = await db.getmallinfo(logintoken, memberid,mode)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getmallinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def shopping_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.warn, 'shopping_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    cardinfo = app['cardinfo']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    mode = request.rel_url.query.get('mode')
    if mode is None:
        mode = 0
    else:
        mode = pg_general.converttype(mode,int)


    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    jsoncontent = await request.json()

    if jsoncontent is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
    else:
        result, clientdata = await db.shopping(redis_obj,logintoken, memberid,cardinfo,jsoncontent,mode)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.warn,
                        'shopping_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def getinboxinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getinboxinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if memberid is not None and logintoken is not None:
        result, clientdata = await db.getinboxinfo(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getinboxinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def receiveinbox_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'receiveinbox_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"], int)
    logintoken = request.match_info["slogintoken"]
    inboxid = pg_general.converttype(request.rel_url.query.get("inboxid"), int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if memberid is not None and logintoken is not None and inboxid is not None:
        result, clientdata = await db.receiveinbox(logintoken, memberid, inboxid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'receiveinbox_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def feedback_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'feedback_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    email = request.rel_url.query.get("email")
    content = request.rel_url.query.get("content")
    typeid = request.rel_url.query.get("typeid")

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if email is None or content is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
    else:
        result, clientdata = await db.feedback(logintoken, memberid, email, content,typeid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'feedback_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)




async def getgamelist_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getgamelist_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    result, clientdata = await db.getgamelist(logintoken, memberid)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getgamelist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def joingame_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'joingame_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    gameid = request.rel_url.query.get("gameid")
    gametype = pg_general.converttype(request.rel_url.query.get("gametype"), int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if gameid is None or gametype is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
    else:
        result, clientdata = await db.joingame(logintoken, memberid, gameid, gametype)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'joingame_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def getgamerank_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getgamerank_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }


    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    gameid = request.rel_url.query.get("gameid")

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if gameid is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
    else:
        result, clientdata = await db.getgamerank(logintoken, memberid, gameid,redis_obj)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getgamerank_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def getleaderrank_handle(request):      # 一次取得 陣營榜單以及富豪榜單
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getleaderrank_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.match_info["smemberid"],int)
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    result, clientdata = await db.getleaderrank(logintoken, memberid)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getleaderrank_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)




async def sendchat_public_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendchat_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    contentdata = await request.json()

    result, clientdata = await db.sendchat_public(redis_obj,logintoken, memberid,contentdata)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success and clientdata.get('black_chat_content') is None and clientdata.get('card_0') is None:
        # msg_info = {"commandid": 3000004, "data": clientdata}
        # await send_to_all_lobbyserver(app, msg_info)

        msg_info2 = {"commandid": 3000020, "data":{"talklist":[clientdata]}}
        await send_to_all_lobbyserver(app,msg_info2)

        resultdata['clientdata'] = {"result":0}
    elif result == pg_general.Apiresult.success and clientdata.get('black_chat_content') == True:
        resultdata['clientdata'] = {"result": 0}
    elif result == pg_general.Apiresult.success and clientdata.get('card_0') == True:
        resultdata['clientdata'] = {"result": 0}
    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendchat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def getsettingcontent_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getsettingcontent_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    type = pg_general.converttype(request.rel_url.query.get("type"), int)


    if None not in [memberid, logintoken, type]:
        result, clientdata = await db.getsettingcontent(logintoken, memberid, type)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getsettingcontent_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getsecretmall_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getsecretmall_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:
        result, clientdata = await db.getsecretmall(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getsecretmall_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def senddownloadsignal_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'senddownloadsignal_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    state = request.rel_url.query.get('state')
    region = request.rel_url.query.get('region')



    if None not in [logintoken,state]:
        asyncio.ensure_future(db.senddownloadsignal(logintoken, memberid,state,region))
        # result, clientdata = await db.senddownloadsignal(logintoken, memberid,state,region)
        # resultdata['apiresult'] = result
        #
        # if result == pg_general.Apiresult.success:
        #     resultdata['clientdata'] = clientdata

        resultdata['apiresult'] = pg_general.Apiresult.success
        resultdata['clientdata'] = {}

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'senddownloadsignal_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def getpiggycredit_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getpiggycredit_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid,logintoken]:
        result, clientdata = await db.getpiggycredit(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getpiggycredit_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getfriendlist_handle(request): # get friend list
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getfriendlist_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:
        result, clientdata = await db.getfriendlist(logintoken, memberid,redis_obj)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getfriendlist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getblacklist_handle(request): # get blacklist
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getblacklist_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:
        result, clientdata = await db.getblacklist(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getblacklist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def updatefriendlist_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'updatefriendlist_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    type = pg_general.converttype(request.rel_url.query.get('type'),int)
    friend_memberid = pg_general.converttype(request.rel_url.query.get('friend_memberid'),int)
    friend_nickname = pg_general.converttype(request.rel_url.query.get('friend_nickname'),str)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken,type]:
        if (type in [0,1] and friend_memberid is not None) or (type in [2,3] and friend_nickname is not None):

            result, clientdata = await db.updatefriendlist(logintoken, memberid,type,friend_memberid,friend_nickname,redis_obj)
            resultdata['apiresult'] = result

            if result == pg_general.Apiresult.success:
                resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'updatefriendlist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def updateblacklist_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'updateblacklist_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    type = pg_general.converttype(request.rel_url.query.get('type'), int)
    black_memberid = pg_general.converttype(request.rel_url.query.get('black_memberid'), int)
    black_nickname = pg_general.converttype(request.rel_url.query.get('black_nickname'),str)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, type]:
        if (type in [0,1] and black_memberid is not None) or (type in [2,3] and black_nickname is not None):
            result, clientdata = await db.updateblacklist(logintoken, memberid, type, black_memberid,black_nickname)
            resultdata['apiresult'] = result

            if result == pg_general.Apiresult.success:
                resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'updateblacklist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)



async def safetask_handle(request): # 處理保險箱
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'safetask_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    type = pg_general.converttype(request.rel_url.query.get('type'), int)
    amount = pg_general.converttype(request.rel_url.query.get('amount'), int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, type]:

        result, clientdata = await db.safetask(logintoken, memberid, type,amount)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'safetask_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def serialinput_handle(request): # input serial to get credit

    # 先不使用
    resultdata = {
        'serverdata': {},
        'clientdata': {"result":0},
        'apiresult': pg_general.Apiresult.success
    }
    return aiohttp.web.json_response(resultdata)

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'serialinput_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    serial = request.rel_url.query.get('serial')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None in [memberid, logintoken, serial]:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    else:

        result, clientdata = await db.serialinput(logintoken, memberid, serial)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata




    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'serialinput_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def makelike_handle(request):  # 按讚
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'makelike_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    likememberid = request.rel_url.query.get('likememberid')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, likememberid]:

        result, clientdata = await db.makelike(logintoken, memberid, likememberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'makelike_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def sendprivatchat_handle(request): # 傳送私人訊息
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendprivatchat_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = pg_general.converttype(request.match_info["smemberid"],int)
    logintoken = request.match_info["slogintoken"]
    chatmemberid = pg_general.converttype(request.rel_url.query.get('chatmemberid'),int)
    type = pg_general.converttype(request.rel_url.query.get('type'),int)
    content = request.rel_url.query.get('content')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, chatmemberid,type,content]:

        result, clientdata = await db.sendprivatchat(logintoken, memberid, chatmemberid,type,content)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success and clientdata.get('black_chat_content') is None and clientdata.get('card_0') is None:
            sendmsg = clientdata

            # 抓取 對象的 lobbyserverip from redis
            lobbyserverip = await redis_obj.get_value('online_{}'.format(chatmemberid))
            chatmemberidlogintoekn = await redis_obj.get_value(str(chatmemberid))

            if lobbyserverip is not None and lobbyserverip != [] and chatmemberidlogintoekn is not None and chatmemberidlogintoekn != '':
                if len(lobbyserverip) >0:
                    try:
                        if env_setting.LOCAL_SERVER == False:
                            realurl = 'http://{}/broadcasttoall'.format(lobbyserverip)
                        else:
                            realurl = 'http://127.0.0.1/broadcasttoall'
                        sendmsg = {"type": SendMsgType.server_to_client,
                                   "logintoken": chatmemberidlogintoekn,
                                   "msg":{"commandid":3000005,"data": sendmsg}
                                   }

                        async with aiohttp.ClientSession() as session:
                            async with session.get(realurl, json=sendmsg) as response:
                                if response.status == 200:
                                    data = await response.text()
                                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                        'sendprivatchat_handle response:{0},sendmsg:{1}'.format(data,sendmsg))



                    except Exception as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'sendprivatchat_handle Exception:{0}'.format(e))
                    await asyncio.sleep(0)
                resultdata['clientdata'] = {'result':0}
            else:
                resultdata['clientdata'] = {'result': 1}        # 對方不在線上
                # 存入 redis reservedchat_{}
                if sendmsg.get('activenumber') >= 50:     # 活躍度不足50，無法使用離線訊息功能
                    await redis_obj.lpush('reservedchat_{}'.format(chatmemberid),json.dumps(sendmsg))
                    await redis_obj.expire('reservedchat_{}'.format(chatmemberid),86400*7)

        elif result == pg_general.Apiresult.blackme:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = {'result': 0}
        elif result == pg_general.Apiresult.success and clientdata.get('black_chat_content') == True:
            resultdata['clientdata'] = {"result": 0}
        elif result == pg_general.Apiresult.success and clientdata.get('card_0') == True:
            resultdata['clientdata'] = {"result": 0}

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendprivatchat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def sendphonevalidate_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendphonevalidate_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    phone = request.rel_url.query.get('phone')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken,phone]:
        phone = phone.strip().replace('-','')

        result, clientdata = await db.sendphonevalidate(logintoken, memberid, phone)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata



    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendphonevalidate_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def feedbackvalidatecode_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'feedbackvalidatecode_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    code = request.rel_url.query.get('code')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, code]:

        result, clientdata = await db.feedbackvalidatecode(logintoken, memberid, code)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'feedbackvalidatecode_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getgiftdata_handle(request): # get gift frame data
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getgiftdata_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = pg_general.converttype(request.match_info["smemberid"],int)
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:

        result, clientdata = await db.getgiftdata(logintoken, memberid)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getgiftdata_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getcardinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getcardinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:

        result, clientdata = await db.getcardinfo(logintoken, memberid,redis_obj)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getcardinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getchannellist_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getchannellist_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:

        result, clientdata = await db.getchannellist(logintoken, memberid,redis_obj)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getchannellist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getchannelmember_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getchannelmember_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    channelindex = request.rel_url.query.get('channelindex')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken,channelindex]:

        result, clientdata = await db.getchannelmember(logintoken, memberid, channelindex,redis_obj)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getchannelmember_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def joinchannel_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'joinchannel_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    channelindex = request.rel_url.query.get('channelindex')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, channelindex]:

        result, clientdata = await db.joinchannel(logintoken, memberid, channelindex, redis_obj)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'joinchannel_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def receivegift_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'receivegift_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    num = request.rel_url.query.get('num')
    password = request.rel_url.query.get('password')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, num,password]:
        result, clientdata = await db.receivegift(logintoken, memberid, num,password)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'receivegift_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def rejectgift_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'rejectgift_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    num = request.rel_url.query.get('num')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, num]:
        result, clientdata = await db.rejectgift(redis_obj,logintoken, memberid, num)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'rejectgift_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def sendchannelchat_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendchannelchat_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    channelindex = request.rel_url.query.get('channelindex')
    type = request.rel_url.query.get('type')
    content = request.rel_url.query.get('content')

    bubblememberid = request.rel_url.query.get('memberid')
    bubblenickname = request.rel_url.query.get('nickname')
    bubbleavatar = request.rel_url.query.get('avatar')

    if None not in  [bubblememberid,bubblenickname,bubbleavatar]:
        bubbleinfo = {
            "memberid": bubblememberid,
            "nickname": bubblenickname,
            "avatar": bubbleavatar
        }
    else:
        bubbleinfo = {}

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, channelindex,type,content]:
        result, clientdata = await db.sendchannelchat(redis_obj,logintoken, memberid, channelindex,type,content,bubbleinfo)
        if result == pg_general.Apiresult.success and clientdata!= {} and clientdata.get('black_chat_content') is None and clientdata.get('card_0') is None:
            data = clientdata.get('data')
            await send_to_all_lobbyserver(app,{"commandid": 3000021,"data":{"talklist": [data],"channelindex":data.get('channelindex')}})


            resultdata['apiresult'] = result
            resultdata['clientdata'] = {'result':0}
        elif result == pg_general.Apiresult.success and clientdata.get('black_chat_content') == True:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = {"result": 0}
        elif result == pg_general.Apiresult.success and clientdata.get('card_0') == True:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = {"result": 0}
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendchannelchat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def sendservicechat_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendservicechat_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    type = pg_general.converttype(request.rel_url.query.get('type'),int)
    content = request.rel_url.query.get('content')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, type, content]:
        result, clientdata = await db.sendservicechat(redis_obj, logintoken, memberid, type, content)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = {'result': 0}

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendservicechat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def sendgift_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendgift_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    amount = pg_general.converttype(request.rel_url.query.get('amount'), int)
    nickname = request.rel_url.query.get('nickname')
    password = request.rel_url.query.get('password')
    addflag = pg_general.converttype(request.rel_url.query.get('addflag'),int)
    code = pg_general.converttype(request.rel_url.query.get('code'),str)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, nickname, amount, password,addflag,code]:
        result, clientdata = await db.sendgift(logintoken, memberid, nickname, amount,password,addflag,code)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendgift_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def sendgiftsms_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendgiftsms_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:
        result, clientdata = await db.sendgiftsms(logintoken, memberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendgiftsms_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def creditexchange_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'creditexchange_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]
    type =  pg_general.converttype(request.rel_url.query.get('type'),int)
    amount = pg_general.converttype(request.rel_url.query.get('amount'),int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid,logintoken,type,amount]:
        result, clientdata = await db.creditexchange(logintoken, memberid,type,amount)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'creditexchange_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def pointtocredit_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pointtocredit_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    type = pg_general.converttype(request.rel_url.query.get('type'),int)
    amount = pg_general.converttype(request.rel_url.query.get('amount'),int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()


    if None not in [memberid,logintoken,type]:
        if (type ==0 and None not in [amount]) or type ==1:
            result, clientdata = await db.pointtocredit(logintoken, memberid,type,amount)
            resultdata['apiresult'] = result

            if result == pg_general.Apiresult.success:
                resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'pointtocredit_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getfreeboxstatus_handle(request):  # 免費寶相
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getfreeboxstatus_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:

        result, clientdata = await db.getfreeboxstatus(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getfreeboxstatus_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def receivefreebox_handle(request): # 領取祝福寶箱
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'receivefreebox_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken]:

        result, clientdata = await db.receivefreebox(logintoken, memberid)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'receivefreebox_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def forgetpasssms_handle(request): # forget password send sms
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'forgetpasssms_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    logintoken = request.match_info["slogintoken"]
    username = request.rel_url.query.get('username')
    phone = request.rel_url.query.get('phone')

    result, clientdata = await db.forgetpasssms(logintoken,username,phone)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'forgetpasssms_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def changenewpassword_handle(request): # change new password
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'changenewpassword_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }


    logintoken = request.match_info["slogintoken"]
    username = request.rel_url.query.get('username')
    phone = request.rel_url.query.get('phone')
    validatecode = request.rel_url.query.get('validatecode')
    newpassword = request.rel_url.query.get('newpassword')

    result, clientdata = await db.changenewpassword(logintoken, username, phone,validatecode,newpassword)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'changenewpassword_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def bindusername_handle(request):  # bindusername
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'bindusername_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    username = request.rel_url.query.get('username')
    password = request.rel_url.query.get('password')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    result, clientdata = await db.bindusername(logintoken, memberid,username, password)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'bindusername_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def friendonlinestatus_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'friendonlinestatus_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    result, clientdata = await db.friendonlinestatus(logintoken, memberid,redis_obj)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'friendonlinestatus_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def updatemembermessage_handle(request): # 更新心情留言
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'updatemembermessage_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    jsoncontent = await request.json()
    if jsoncontent is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
        return aiohttp.web.json_response(resultdata)

    message = jsoncontent.get('message')
    if message is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
        return aiohttp.web.json_response(resultdata)


    if None not in [memberid,logintoken,message]:
        result, clientdata = await db.updatemembermessage(logintoken, memberid,message)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'updatemembermessage_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def reportmember_handle(request): # 檢舉玩家
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'reportmember_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    jsoncontent = await request.json()
    if jsoncontent is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
        return aiohttp.web.json_response(resultdata)

    tomemberid = jsoncontent.get('memberid')
    content = jsoncontent.get('content')
    if None in [memberid , logintoken , tomemberid,content]:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
        return aiohttp.web.json_response(resultdata)


    result, clientdata = await db.reportmember(logintoken, memberid, tomemberid,content)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'reportmember_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def actionframe_handle(request): # 活動與官方公告頁面
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'actionframe_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None in [memberid, logintoken]:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
        return aiohttp.web.json_response(resultdata)

    result, clientdata = await db.actionframe(logintoken, memberid)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'actionframe_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def restoreIAP_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'restoreIAP_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = request.match_info["smemberid"]
        logintoken = request.match_info["slogintoken"]

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        jsoncontent = await request.json()
        if jsoncontent is None:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'restoreIAP_handle jsoncontent:{0}'.format(jsoncontent))

        result, clientdata = await db.restoreIAP(logintoken, memberid,jsoncontent)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'restoreIAP_handle logintoken:{0}, error:{1}'.format(logintoken, e))


    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'restoreIAP_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getselfrankgamesort_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getselfrankgamesort_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"],int)
        logintoken = request.match_info["slogintoken"]

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()


        result, clientdata = await db.getselfrankgamesort(redis_obj,logintoken, memberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getselfrankgamesort_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getselfrankgamesort_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getselfrankgamesortnew_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getselfrankgamesortnew_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.getselfrankgamesortnew(redis_obj, logintoken, memberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getselfrankgamesortnew_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getselfrankgamesortnew_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getmemberinfolessdata_handle(request):

    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'getmemberinfolessdata_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        jsoncontent = await request.json()
        if jsoncontent is None:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)

        findmemberid = jsoncontent.get('findmemberid')
        if findmemberid is None:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.getmemberinfolessdata(redis_obj, logintoken, memberid,findmemberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getmemberinfolessdata_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getmemberinfolessdata_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getboxinfo_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'getboxinfo_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.getboxinfo(redis_obj, logintoken, memberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getboxinfo_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getboxinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def buybox_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'buybox_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        item = pg_general.converttype(request.rel_url.query.get('item'),int)


        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.buybox(redis_obj, logintoken, memberid,item)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'buybox_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'buybox_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def skiptutorial_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'skiptutorial_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.skiptutorial(redis_obj, logintoken, memberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'skiptutorial_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'skiptutorial_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def gettutorialguide_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'gettutorialguide_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.gettutorialguide(redis_obj, logintoken, memberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'gettutorialguide_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'gettutorialguide_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def joinfishgame_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'joinfishgame_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        hallid = pg_general.converttype(request.rel_url.query.get('hallid'),int)
        gameid = request.rel_url.query.get('gameid')


        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.joinfishgame(redis_obj, logintoken, memberid,hallid,gameid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'joinfishgame_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'joinfishgame_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)




async def getavatarlist_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getavatarlist_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.getavatarlist(logintoken, memberid)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,'getavatarlist_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getavatarlist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def setavatarfromlist_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'setavatarfromlist_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {"result": 1},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        jsoncontent = await request.json()
        if jsoncontent is None:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)

        avatarurl = jsoncontent.get('avatarurl')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.setavatarfromlist(logintoken, memberid,avatarurl)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'setavatarfromlist_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'setavatarfromlist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def getseatsinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getseatsinfo_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        gameid = request.rel_url.query.get('gameid')
        type = pg_general.converttype(request.rel_url.query.get('type'),int)

        if None in [gameid,type]:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)


        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        result, clientdata = await db.getseatsinfo(redis_obj,logintoken, memberid, gameid,type)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getseatsinfo_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getseatsinfo_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)


async def backtohall_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'backtohall_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]
        gamelogdataindex = pg_general.converttype(request.rel_url.query.get('gamelogdataindex'),int)
        seat_data = request.rel_url.query.get('seatdata')


        result , clientdata  = await db.backtohall(app,redis_obj, logintoken, memberid,gamelogdataindex,seat_data)

        resultdata['clientdata'] = clientdata

        resultdata['apiresult'] = pg_general.Apiresult.success


    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'backtohall_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'backtohall_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def joingameseat_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'joingameseat_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        gameid = request.rel_url.query.get('gameid')
        gametype = pg_general.converttype(request.rel_url.query.get('gametype'),int)
        seatnum = pg_general.converttype(request.rel_url.query.get('seatnum'),int)

        jsoncontent ={
            'gameid': gameid,
            'gametype': gametype,
            'seatnum': seatnum
        }

        if None in [gameid,gametype,seatnum]:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)

        result, clientdata = await db.joingameseat(redis_obj, logintoken, memberid,jsoncontent)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata



    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'joingameseat_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'joingameseat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getnewdragontigerrank_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getnewdragontigerrank_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        gameid = request.rel_url.query.get('gameid')

        jsoncontent = {
            'gameid': gameid
        }

        if None in [gameid]:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)

        result, clientdata = await db.getnewdragontigerrank(redis_obj, logintoken, memberid, jsoncontent)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata



    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getnewdragontigerrank_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'joingameseat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def getnewtotalrank_handle(request):      # 抓新的 榮譽榜單
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getnewtotalrank_handle recv:{0}'.format(request.rel_url))
    try:
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        memberid = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]


        result, clientdata = await db.getnewtotalrank(redis_obj, logintoken, memberid)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata



    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getnewtotalrank_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getnewtotalrank_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def servicetouser_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'servicetouser_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = pg_general.converttype(request.rel_url.query.get('memberid'), int)
    content = request.rel_url.query.get('content')


    result, clientdata = await db.servicetouser(redis_obj,memberid,content)
    resultdata['apiresult'] = result

    if result == pg_general.Apiresult.success:
        resultdata['clientdata'] = {"result": clientdata.get('result')}

        # get member's logintoken from redis
        if clientdata.get('result') == 0:
            userip = clientdata.get('userip')
            memberlogintoken = clientdata.get('logintoken')
            msg = clientdata.get('msg')
            sendmsg = {
                "type": SendMsgType.server_to_client,
                "commandid": 3000012,
                "logintoken": memberlogintoken,
                "msg": msg
            }
            asyncio.ensure_future(send_to_all_lobbyserver_future(userip, sendmsg))


    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'servicetouser_handle send:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)




async def getreddot_countdown_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getreddot_countdown_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    memberid = request.match_info["smemberid"]
    logintoken = request.match_info["slogintoken"]

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    # reddot info
    reddot_result , reddot_clientdata = await db.getreddotinfo(logintoken,memberid)


    if reddot_result == pg_general.Apiresult.success:
        resultdata['apiresult'] = pg_general.Apiresult.success
    else:
        resultdata['apiresult'] = pg_general.Apiresult.connectdberror


    if resultdata['apiresult'] == pg_general.Apiresult.success:
        resultdata['clientdata'] = {
            "reddot": reddot_clientdata
        }
    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getreddot_countdown_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)



async def setlobbyip_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'setlobbyip_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    clientdata = {}
    ip = request.match_info["sIP"]

    if env_setting.LOCAL_SERVER == False:
        result = await db.setlobbyip(ip)
    else:
        result = pg_general.Apiresult.success

    resultdata['apiresult'] = result

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'setlobbyip_handle IP:{0}, send:{1}'.format(ip, resultdata))
    return aiohttp.web.json_response(resultdata)

async def psapi_signin_handle(request):
    '''  ps game api server will call back this function when api server login procedure call ps api server
    check memberid  and logintoken if they are promit in db
    '''
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_signin_handle recv:{0}'.format(request.rel_url))

    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'status_code': -1,
        'access_token': ''  # use password to pass logintoken,
    }


    try:
        member_id = request.rel_url.query.get("member_id")
        seatlogintoken = request.rel_url.query.get("password")  # password is logintoken


        # 確認 memberid and logintoken 是否正確
        if member_id[:4] == 'gsea': # new mode
            # find real memberid
            templist = member_id.split('_')
            gameid = templist[1]
            seatnum = pg_general.converttype(templist[2],int)


            # get real memberid
            member_id = await redis_obj.hget('goldseats_{}@{}'.format(gameid,seatnum),'memberid')

            # get real logintoken
            logintoken = seatlogintoken.split('*****')[1]
        else:
            logintoken = seatlogintoken


        member_id = pg_general.converttype(member_id,int)



        result = await db.psapi_signin(logintoken,member_id)
        status_code = 0 if result == pg_general.Apiresult.success else -1

        resultdata = {
            'status_code': status_code,
            'access_token': seatlogintoken  # use password to pass logintoken,
        }

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, 'psapi_signin_handle url:{0}'.format(request.rel_url))

    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_signin_handle response:{0}'.format(resultdata))
        return aiohttp.web.json_response(resultdata)

async def psapis_signin_handle(request):
    '''  ps game api server will call back this function when api server login procedure call ps api server
    check memberid  and logintoken if they are promit in db
    '''
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_signin_handle recv:{0}'.format(request.rel_url))

    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'status_code': -1,
        'access_token': ''  # use password to pass logintoken,
    }

    try:
        member_id = request.rel_url.query.get("member_id")
        seatlogintoken = request.rel_url.query.get("password")  # password is logintoken

        # 確認 memberid and logintoken 是否正確
        if member_id[:4] == 'ssea':  # new mode
            # find real memberid
            templist = member_id.split('_')
            gameid = templist[1]
            seatnum = pg_general.converttype(templist[2], int)


            # get real memberid
            member_id = await redis_obj.hget('silverseats_{}@{}'.format(gameid, seatnum), 'memberid')
            # get real logintoken
            logintoken = seatlogintoken.split('*****')[1]
        else:
            logintoken = seatlogintoken
        member_id = pg_general.converttype(member_id, int)

        result = await db.psapis_signin(logintoken, member_id)
        status_code = 0 if result == pg_general.Apiresult.success else -1

        resultdata = {
            'status_code': status_code,
            'access_token': seatlogintoken  # use password to pass logintoken,
        }

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, 'psapis_signin_handle url:{0}'.format(request.rel_url))

    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_signin_handle response:{0}'.format(resultdata))
        return aiohttp.web.json_response(resultdata)

async def psapi_authenticate_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_authenticate_handle recv:{0}'.format(request.rel_url))

    app = request.app
    db = app["DB"][0]


    access_token = request.rel_url.query.get("access_token")
    if access_token[:4] == 'gsea' and '*****' in access_token: # new mode
        logintoken = access_token.split('*****')[1]
    elif access_token[:4] == 'fish' and '*****' in access_token:
        logintoken = access_token.split('*****')[1]
    else:
        logintoken = access_token

    step = request.rel_url.query.get("step")

    resultdata = {
        'status_code': 1,
        'member_id': "0",
        'balance': 0
    }

    result , clientdata = await db.psapi_authenticate(logintoken)
    if result == pg_general.Apiresult.success:

        resultdata = {
            "status_code": 0,
            "balance": pg_general.converttype(clientdata.get("credit"),int),
            "account_type": pg_general.converttype(clientdata.get('account_type'),int)
        }
        if access_token[:4] == 'gsea' and '*****' in access_token:
            resultdata["member_id"] = access_token.split('*****')[0]
        elif access_token[:4] == 'fish' and '*****' in access_token:
            resultdata["member_id"] = 'fish_{}'.format(clientdata.get('memberid'))
            resultdata["member_name"] = clientdata.get('nickname')
        else:
            resultdata["member_id"] = pg_general.converttype(clientdata.get("memberid"), str)


    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_authenticate_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)


async def psapis_authenticate_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_authenticate_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    access_token = request.rel_url.query.get("access_token")
    if access_token[:4] == 'ssea' and '*****' in access_token: # new mode
        logintoken = access_token.split('*****')[1]
    elif access_token[:4] == 'fish' and '*****' in access_token:
        logintoken = access_token.split('*****')[1]
    else:
        logintoken = access_token

    step = request.rel_url.query.get("step")

    resultdata = {
        'status_code': 1,
        'member_id': "0",
        'balance': 0
    }

    result , clientdata = await db.psapis_authenticate(logintoken)
    if result == pg_general.Apiresult.success:
        resultdata = {
            "status_code": 0,
            "balance": pg_general.converttype(clientdata.get("silvercredit"),int),
            "account_type": pg_general.converttype(clientdata.get('account_type'), int)
        }
        if access_token[:4] == 'ssea' and '*****' in access_token:  # new mode
            resultdata["member_id"] =  access_token.split('*****')[0]
        elif access_token[:4] == 'fish' and '*****' in access_token:
            resultdata["member_id"] = 'fish_{}'.format(clientdata.get('memberid'))
            resultdata["member_name"] = clientdata.get('nickname')
        else:
            resultdata["member_id"] = pg_general.converttype(clientdata.get("memberid"), str)



    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_authenticate_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)


async def psapit_authenticate_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_authenticate_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    access_token = request.rel_url.query.get("access_token")
    if access_token[:4] == 'tsea' and '*****' in access_token: # new mode
        logintoken = access_token.split('*****')[1]
    else:
        logintoken = access_token

    step = request.rel_url.query.get("step")

    resultdata = {
        'status_code': 1,
        'member_id': "0",
        'balance': 0
    }

    result , clientdata = await db.psapit_authenticate(logintoken)
    if result == pg_general.Apiresult.success:
        resultdata = {
            "status_code": 0,
            "balance": pg_general.converttype(clientdata.get("silvercredit"),int)
        }
        if access_token[:4] == 'tsea' and '*****' in access_token:  # new mode
            resultdata["member_id"] =  access_token.split('*****')[0]
        else:
            resultdata["member_id"] = pg_general.converttype(clientdata.get("memberid"), str)



    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_authenticate_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)


async def psapi_logout_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_logout_handle recv:{0}'.format(request.rel_url))

    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    logintoken = request.rel_url.query.get("access_token")
    game_id = request.rel_url.query.get("game_id")

    if logintoken[:4] == 'gsea' and '*****' in logintoken: # new mode
        logintoken = logintoken.split('*****')[1]
        seatinfo = logintoken.split('*****')[0]
        # make game logout
        result, clientdata = await db.psapi_logout(redis_obj,logintoken,seatinfo)


    resultdata = {
        'status_code': 0
    }
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_logout_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def psapis_logout_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_logout_handle recv:{0}'.format(request.rel_url))

    logintoken = request.rel_url.query.get("access_token")
    game_id = request.rel_url.query.get("game_id")

    if logintoken[:4] == 'ssea' and '*****' in logintoken: # new mode
        logintoken = logintoken.split('*****')[1]
        seatinfo = logintoken.split('*****')[0]


    resultdata = {
        'status_code': 0
    }
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_logout_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def psapit_logout_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_logout_handle recv:{0}'.format(request.rel_url))

    logintoken = request.rel_url.query.get("access_token")
    game_id = request.rel_url.query.get("game_id")

    if logintoken[:4] == 'tsea' and '*****' in logintoken: # new mode
        logintoken = logintoken.split('*****')[1]
        seatinfo = logintoken.split('*****')[0]


    resultdata = {
        'status_code': 0
    }
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_logout_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def psapi_bet_handle(request):  # 金幣廳 bet
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_bet_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    cardinfo = app['cardinfo']

    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"),str)
    txn_id = pg_general.converttype(request.rel_url.query.get("txn_id"),int)
    total_bet = pg_general.converttype(request.rel_url.query.get("total_bet"), int)
    game_id = pg_general.converttype(request.rel_url.query.get("game_id"),str)
    subgame_id = pg_general.converttype(request.rel_url.query.get("subgame_id"),int)
    ts = pg_general.converttype(request.rel_url.query.get("ts"),int)
    bettime = pg_general.utctimestamptodatetimestring(ts)  # sting datetime

    betdata = {
        "txn_id": txn_id,
        "total_bet": total_bet,
        "game_id": game_id,
        "subgame_id": subgame_id,
        "bettime": bettime
    }


    if logintoken[:4] == 'gsea' and '*****' in logintoken:    # new mode
        logintoken = logintoken.split('*****')[1]



    # 先抓 判斷是否可以 bet , 如果可以的話  resut = success , clientdata 會有它的 memberid , after credit
    # 如果找步道此玩家, result = dbnodata , 如果credit 不夠 , 回 othererror
    result , clientdata = await db.psapi_bet(redis_obj,logintoken,betdata)

    if result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get("aftercredit")
        }

        # 將bet 資料丟入 queue
        memberid = clientdata.get("memberid")
        lobbyserverip = clientdata.get("lobbyserverip")

        card = clientdata.get('card')
        betdata = {
            "cmd": "bet",
            "token": logintoken,
            "game_id": game_id,
            "total_bet": total_bet,
            "memberid": memberid,
            "lobbyserverip": lobbyserverip

        }

        asyncio.ensure_future(bet_queue_future(app,betdata))



        if memberid is not None and card in [2,3,4,5]:
            # add job to redis bethistory_twdate_(memberid)
            twdatestr = pg_general.get_tw_datetime().date().__str__()
            twnowdate = pg_general.get_tw_datetime().date()
            firstdate = pg_general.get_tw_2020_first_date().date()
            datekey = str((twnowdate - firstdate).days % 60)


            # result = await redis_obj.sadd('betjob_{}'.format(twdatestr),pg_general.converttype(memberid,str))

            # add total_bet to bethistory_gold_(memberid)
            result = await redis_obj.hincrby('bethistory_gold_{}'.format(memberid), datekey, total_bet)

            # 做 bet gold 升級制度
            if card in [2,3,4]:
                asyncio.ensure_future(db.betcardlevelup_future(logintoken,memberid,card,redis_obj,cardinfo))

    else:
        resultdata = {
            'status_code': clientdata.get("status_code"),
            'balance': 0
        }


    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_bet_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def psapis_bet_handle(request):  # 銀幣廳
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_bet_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"), str)
    txn_id = pg_general.converttype(request.rel_url.query.get("txn_id"), int)
    total_bet = pg_general.converttype(request.rel_url.query.get("total_bet"), int)
    game_id = pg_general.converttype(request.rel_url.query.get("game_id"), str)
    subgame_id = pg_general.converttype(request.rel_url.query.get("subgame_id"), int)
    ts = pg_general.converttype(request.rel_url.query.get("ts"), int)
    bettime = pg_general.utctimestamptodatetimestring(ts)  # sting datetime

    betdata = {
        "txn_id": txn_id,
        "total_bet": total_bet,
        "game_id": game_id,
        "subgame_id": subgame_id,
        "bettime": bettime
    }

    if logintoken[:4] == 'ssea' and '*****' in logintoken:  # new mode
        logintoken = logintoken.split('*****')[1]


    # 先抓 判斷是否可以 bet , 如果可以的話  resut = success , clientdata 會有它的 memberid , after credit
    # 如果找步道此玩家, result = dbnodata , 如果credit 不夠 , 回 othererror
    result, clientdata = await db.psapis_bet(redis_obj,logintoken, betdata)

    if result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get("aftercredit")
        }
        memberid = clientdata.get('memberid')
        if memberid is not None:
            # add job to redis bethistory_twdate_(memberid)
            twdatestr = pg_general.get_tw_datetime().date().__str__()
            twnowdate = pg_general.get_tw_datetime().date()
            firstdate = pg_general.get_tw_2020_first_date().date()
            datekey = str((twnowdate - firstdate).days % 60)


            # result = await redis_obj.sadd('betjob_{}'.format(twdatestr),pg_general.converttype(memberid,str))

            # add total_bet to bethistory_gold_(memberid)
            result = await redis_obj.hincrby('bethistory_silver_{}'.format(memberid), datekey, total_bet)

    else:
        resultdata = {
            'status_code': clientdata.get("status_code"),
            'balance': 0
        }



    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_bet_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)


async def psapit_bet_handle(request):  # 銀幣廳
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_bet_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"), str)
    txn_id = pg_general.converttype(request.rel_url.query.get("txn_id"), int)
    total_bet = pg_general.converttype(request.rel_url.query.get("total_bet"), int)
    game_id = pg_general.converttype(request.rel_url.query.get("game_id"), str)
    subgame_id = pg_general.converttype(request.rel_url.query.get("subgame_id"), int)
    ts = pg_general.converttype(request.rel_url.query.get("ts"), int)
    bettime = pg_general.utctimestamptodatetimestring(ts)  # sting datetime

    betdata = {
        "txn_id": txn_id,
        "total_bet": total_bet,
        "game_id": game_id,
        "subgame_id": subgame_id,
        "bettime": bettime
    }

    if logintoken[:4] == 'tsea' and '*****' in logintoken:  # new mode
        logintoken = logintoken.split('*****')[1]


    # 先抓 判斷是否可以 bet , 如果可以的話  resut = success , clientdata 會有它的 memberid , after credit
    # 如果找步道此玩家, result = dbnodata , 如果credit 不夠 , 回 othererror
    result, clientdata = await db.psapit_bet(redis_obj,logintoken, betdata)

    if result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get("aftercredit")
        }
        memberid = clientdata.get('memberid')
        if memberid is not None:
            # add job to redis bethistory_twdate_(memberid)
            twdatestr = pg_general.get_tw_datetime().date().__str__()
            twnowdate = pg_general.get_tw_datetime().date()
            firstdate = pg_general.get_tw_2020_first_date().date()
            datekey = str((twnowdate - firstdate).days % 60)


            # result = await redis_obj.sadd('betjob_{}'.format(twdatestr),pg_general.converttype(memberid,str))

            # add total_bet to bethistory_gold_(memberid)
            result = await redis_obj.hincrby('bethistory_silver_{}'.format(memberid), datekey, total_bet)

    else:
        resultdata = {
            'status_code': clientdata.get("status_code"),
            'balance': 0
        }



    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_bet_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)




async def psapi_result_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_result_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    rankminwin = app['rankminwin']
    rankminmultipilier = app['rankminmultipilier']


    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"),str)
    txn_id = pg_general.converttype(request.rel_url.query.get("txn_id"),int)
    total_win = pg_general.converttype(request.rel_url.query.get("total_win"), int)
    bonus_win = pg_general.converttype(request.rel_url.query.get("bonus_win"),int)
    game_id = pg_general.converttype(request.rel_url.query.get("game_id"),str)
    subgame_id = pg_general.converttype(request.rel_url.query.get("subgame_id"),int)
    ts = pg_general.converttype(request.rel_url.query.get("ts"),int)
    resulttime = pg_general.utctimestamptodatetimestring(ts)  # sting datetime
    has_bonus = pg_general.converttype(request.rel_url.query.get('has_bonus'),int)

    apiresultdata = {
        "txn_id": txn_id,
        "total_win": total_win,
        "bonus_win": bonus_win,
        "game_id": game_id,
        "subgame_id": subgame_id,
        "resulttime": resulttime,
        "has_bonus": has_bonus
    }

    seat_data = None
    if logintoken[:4] ==  'gsea' and '*****' in logintoken: # new mode
        seat_data = logintoken.split('*****')[0]
        logintoken = logintoken.split('*****')[1]


    result , clientdata = await db.psapi_result(redis_obj,logintoken,apiresultdata,rankminwin,rankminmultipilier)
    if result == pg_general.Apiresult.success and clientdata.get('status_code') == 99:
        resultdata = {
            'status_code': 0,
            'balance': 0
        }
    elif result == pg_general.Apiresult.success and clientdata.get('status_code') == 98:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get('balance')
        }
    elif result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get("aftercredit")
        }
        # 將 result 資料丟入傳入 future 來執行 quests
        memberid = clientdata.get("memberid")
        lobbyserverip = clientdata.get("lobbyserverip")
        total_bet = clientdata.get('total_bet')
        avatar = clientdata.get('avatar')
        nickname = clientdata.get('nickname')
        gamename = clientdata.get('gamename')
        card = pg_general.converttype(clientdata.get('card'),int)

        quest_task_data = {
            "cmd": "result",
            "token": logintoken,
            "game_id": game_id,
            "total_win": total_win,
            "bonus_win": bonus_win,
            "base_win": total_win-bonus_win,
            "memberid": memberid,
            "lobbyserverip": lobbyserverip,
            "total_bet": total_bet,
            "multipilier": pg_general.converttype(total_win/total_bet,int),
            "txn_id": txn_id,
            "has_bonus": has_bonus,
            "avatar": avatar,
            "nickname": nickname,
            "gamename": gamename,
            "card": card,
            "seat_data": seat_data

        }

        # 開一個 future 處理 bigprize
        asyncio.ensure_future(quest_task_future(app,quest_task_data))
        # 開一個 future 處理 畫面左邊的大獎彈窗 以及 公開頻道大獎公告
        asyncio.ensure_future(bigprize_task_future(app,quest_task_data,1))




    else:
        resultdata = {
            'status_code': clientdata.get('status_code'),
            'balance': 0
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_result_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)


async def psapis_result_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_result_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"),str)
    txn_id = pg_general.converttype(request.rel_url.query.get("txn_id"),int)
    total_win = pg_general.converttype(request.rel_url.query.get("total_win"), int)
    bonus_win = pg_general.converttype(request.rel_url.query.get("bonus_win"),int)
    game_id = pg_general.converttype(request.rel_url.query.get("game_id"),str)
    subgame_id = pg_general.converttype(request.rel_url.query.get("subgame_id"),int)
    ts = pg_general.converttype(request.rel_url.query.get("ts"),int)
    resulttime = pg_general.utctimestamptodatetimestring(ts)  # sting datetime
    has_bonus = pg_general.converttype(request.rel_url.query.get('has_bonus'),int)

    apiresultdata = {
        "txn_id": txn_id,
        "total_win": total_win,
        "bonus_win": bonus_win,
        "game_id": game_id,
        "subgame_id": subgame_id,
        "resulttime": resulttime,
        "has_bonus": has_bonus
    }

    seat_data = None
    if logintoken[:4] ==  'ssea' and '*****' in logintoken: # new mode
        seat_data = logintoken.split('*****')[0]
        logintoken = logintoken.split('*****')[1]


    result , clientdata = await db.psapis_result(redis_obj,logintoken,apiresultdata)
    if result == pg_general.Apiresult.success and clientdata.get('status_code') == 99:
        resultdata = {
            'status_code': 0,
            'balance': 0
        }
    elif result == pg_general.Apiresult.success and clientdata.get('status_code') == 98:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get('balance')
        }
    elif result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get("aftercredit")
        }

        # 將 result 資料丟入傳入 future 來執行 quests
        memberid = clientdata.get("memberid")
        lobbyserverip = clientdata.get("lobbyserverip")
        total_bet = clientdata.get('total_bet')
        avatar = clientdata.get('avatar')
        nickname = clientdata.get('nickname')
        card = pg_general.converttype(clientdata.get('card'), int)
        gamename = clientdata.get('gamename')
        quest_task_data = {
            "cmd": "result",
            "token": logintoken,
            "game_id": game_id,
            "total_win": total_win,
            "bonus_win": bonus_win,
            "base_win": total_win - bonus_win,
            "memberid": memberid,
            "lobbyserverip": lobbyserverip,
            "total_bet": total_bet,
            "multipilier": pg_general.converttype(total_win / total_bet, int),
            "txn_id": txn_id,
            "has_bonus": has_bonus,
            "avatar": avatar,
            "nickname": nickname,
            "card": card,
            "seat_data": seat_data,
            "gamename": gamename

        }

        # 開一個 future 處理 bigprize
        asyncio.ensure_future(quest_task_future_silver(app, quest_task_data))

        asyncio.ensure_future(bigprize_task_future(app, quest_task_data,2))

    else:
        resultdata = {
            'status_code': clientdata.get('status_code'),
            'balance': 0
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_result_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def psapit_result_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_result_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"),str)
    txn_id = pg_general.converttype(request.rel_url.query.get("txn_id"),int)
    total_win = pg_general.converttype(request.rel_url.query.get("total_win"), int)
    bonus_win = pg_general.converttype(request.rel_url.query.get("bonus_win"),int)
    game_id = pg_general.converttype(request.rel_url.query.get("game_id"),str)
    subgame_id = pg_general.converttype(request.rel_url.query.get("subgame_id"),int)
    ts = pg_general.converttype(request.rel_url.query.get("ts"),int)
    resulttime = pg_general.utctimestamptodatetimestring(ts)  # sting datetime
    has_bonus = pg_general.converttype(request.rel_url.query.get('has_bonus'),int)

    apiresultdata = {
        "txn_id": txn_id,
        "total_win": total_win,
        "bonus_win": bonus_win,
        "game_id": game_id,
        "subgame_id": subgame_id,
        "resulttime": resulttime,
        "has_bonus": has_bonus
    }

    seat_data = None
    if logintoken[:4] ==  'tsea' and '*****' in logintoken: # new mode
        seat_data = logintoken.split('*****')[0]
        logintoken = logintoken.split('*****')[1]


    result , clientdata = await db.psapit_result(redis_obj,logintoken,apiresultdata)
    if result == pg_general.Apiresult.success and clientdata.get('status_code') == 99:
        resultdata = {
            'status_code': 0,
            'balance': 0
        }
    elif result == pg_general.Apiresult.success and clientdata.get('status_code') == 98:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get('balance')
        }
    elif result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': 0,
            'balance': clientdata.get("aftercredit")
        }

        # 將 result 資料丟入傳入 future 來執行 quests
        # memberid = clientdata.get("memberid")
        # lobbyserverip = clientdata.get("lobbyserverip")
        # total_bet = clientdata.get('total_bet')
        # avatar = clientdata.get('avatar')
        # nickname = clientdata.get('nickname')
        # card = pg_general.converttype(clientdata.get('card'), int)
        # gamename = clientdata.get('gamename')
        # quest_task_data = {
        #     "cmd": "result",
        #     "token": logintoken,
        #     "game_id": game_id,
        #     "total_win": total_win,
        #     "bonus_win": bonus_win,
        #     "base_win": total_win - bonus_win,
        #     "memberid": memberid,
        #     "lobbyserverip": lobbyserverip,
        #     "total_bet": total_bet,
        #     "multipilier": pg_general.converttype(total_win / total_bet, int),
        #     "txn_id": txn_id,
        #     "has_bonus": has_bonus,
        #     "avatar": avatar,
        #     "nickname": nickname,
        #     "card": card,
        #     "seat_data": seat_data,
        #     "gamename": gamename
        #
        # }
        #
        # # 開一個 future 處理 bigprize
        # asyncio.ensure_future(quest_task_future_silver(app, quest_task_data))
        #
        # asyncio.ensure_future(bigprize_task_future(app, quest_task_data,2))

    else:
        resultdata = {
            'status_code': clientdata.get('status_code'),
            'balance': 0
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_result_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)



async def psapi_getbalance_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_getbalance_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"), str)

    if logintoken[:4] == 'gsea' and '*****' in logintoken: # new mode
        logintoken = logintoken.split('*****')[1]


    result, clientdata = await db.psapi_getbalance(logintoken)
    if result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': clientdata.get('status_code'),
            'balance': clientdata.get("balance")
        }
    else:
        resultdata = {
            'status_code': 1,
            'balance': 0
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapi_getbalance_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def psapis_getbalance_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_getbalance_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"), str)

    if logintoken[:4] == 'ssea' and '*****' in logintoken: # new mode
        logintoken = logintoken.split('*****')[1]

    result, clientdata = await db.psapis_getbalance(logintoken)
    if result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': clientdata.get('status_code'),
            'balance': clientdata.get("balance")
        }
    else:
        resultdata = {
            'status_code': 1,
            'balance': 0
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_getbalance_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)


async def psapit_getbalance_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_getbalance_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    logintoken = pg_general.converttype(request.rel_url.query.get("access_token"), str)

    if logintoken[:4] == 'tsea' and '*****' in logintoken: # new mode
        logintoken = logintoken.split('*****')[1]

    result, clientdata = await db.psapit_getbalance(logintoken)
    if result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': clientdata.get('status_code'),
            'balance': clientdata.get("balance")
        }
    else:
        resultdata = {
            'status_code': 1,
            'balance': 0
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_getbalance_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)


async def psapit_signin_handle(request):
    '''  ps game api server will call back this function when api server login procedure call ps api server
    check memberid  and logintoken if they are promit in db
    '''
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_signin_handle recv:{0}'.format(request.rel_url))

    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'status_code': -1,
        'access_token': ''  # use password to pass logintoken,
    }

    try:
        member_id = request.rel_url.query.get("member_id")
        seatlogintoken = request.rel_url.query.get("password")  # password is logintoken

        # 確認 memberid and logintoken 是否正確
        if member_id[:4] == 'tsea':  # new mode
            # find real memberid
            templist = member_id.split('_')
            gameid = templist[1]
            seatnum = pg_general.converttype(templist[2], int)


            # get real memberid
            member_id = await redis_obj.hget('tutorialseats_{}@{}'.format(gameid, seatnum), 'memberid')
            # get real logintoken
            logintoken = seatlogintoken.split('*****')[1]
        else:
            logintoken = seatlogintoken
        member_id = pg_general.converttype(member_id, int)

        result = await db.psapit_signin(logintoken, member_id)
        status_code = 0 if result == pg_general.Apiresult.success else -1

        resultdata = {
            'status_code': status_code,
            'access_token': seatlogintoken  # use password to pass logintoken,
        }

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, 'psapit_signin_handle url:{0}'.format(request.rel_url))

    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapit_signin_handle response:{0}'.format(resultdata))
        return aiohttp.web.json_response(resultdata)



async def getlobbyserverips_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getlobbyserverips_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    resultdata = {}

    result, clientdata = await db.getlobbyserverip()
    if result == pg_general.Apiresult.success:
        resultdata = clientdata

    return aiohttp.web.json_response(resultdata)


async def callpsgamelist_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'callpsgamelist_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    psgamelistresult = pg_general.Apiresult.othererror

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.othererror
    }
    clientdata = {}

    # call ps server to get game list
    url = env_setting.PS_API_SERVER_URL + 'feed/gamelist?host_id={0}'.format(env_setting.PS_HOST_ID)
    # call ps signin api
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                psgamelistresult = pg_general.Apiresult.success

    await asyncio.sleep(0)

    if psgamelistresult == pg_general.Apiresult.success:
        psgamelistresult = await db.callpsgamelist(data)

    resultdata['apiresult'] = psgamelistresult
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'callpsgamelist_handle response:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

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
        app['headline_multipilier_content'] = data.get('headline_multipilier_content')
        app['headline_multipilier_setting'] = data.get('headline_multipilier_setting')
        app['headline_win_setting'] = data.get('headline_win_setting')
        app['headline_win_content'] = data.get('headline_win_content')
        app['dailywheelflag'] = data.get('dailywheelflag')
        app['dailysigninflag'] = data.get('dailysigninflag')
        app['chatroomflag'] = data.get('chatroomflag')
        app['completeallcontinuoussigninaward'] = data.get('completeallcontinuoussigninaward')
        app['bigprizehitamount'] = data.get('bigprizehitamount')
        app['bigprizewinamount'] = data.get('bigprizewinamount')
        app['defaultchannelindex'] = data.get('defaultchannelindex')
        app['cardinfo'] = data.get('cardinfo')
        app['useagreement'] = data.get('useagreement')
        app['privacyagreement'] = data.get('privacyagreement')
        app['gameagreement'] = data.get('gameagreement')

        app['bigwincontent_publicchat'] = data.get('bigwincontent_publicchat')
        app['bigmultipliercontent_publicchat'] = data.get('bigmultipliercontent_publicchat')
        app['jpenable'] = data.get('jpenable')
        app['fblink'] = data.get('fblink')
        app['jinsongprizeenable'] = data.get('jinsongprizeenable')
        app['rankminwin'] = data.get('rankminwin')
        app['rankminmultipilier'] = data.get('rankminmultipilier')
    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_all_settings result:{0},resultdata={1}'.format(result,data))

async def send_to_all_lobbyserver_future(item, sendmsg):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'send_to_all_lobbyserver_future sendmsg:{0}'.format(sendmsg))
        commandid = sendmsg.get('commandid')
        delay = sendmsg.get('delay')
        if commandid is None:
            raise Exception('send_to_all_lobbyserver_future commandid is None')

        if delay is not None:
            await asyncio.sleep(delay)

        realurl = ''
        if commandid == 3000001:
            realurl = 'http://' + item + "/headline/{0}".format(SendMsgType.server_to_all_client)
        elif commandid in [3000004,3000006,3000020,3000022]:
            if env_setting.LOCAL_SERVER == False:
                realurl = 'http://' + item + "/broadcasttoall"
            else:
                realurl = 'http://127.0.0.1/broadcasttoall'
            sendmsg = {"type":SendMsgType.server_to_all_client,
                       "msg":sendmsg
                       }
        elif commandid in [3000021]:
            if env_setting.LOCAL_SERVER == False:
                realurl = 'http://' + item + "/broadcasttoall"
            else:
                realurl = 'http://127.0.0.1/broadcasttoall'
            sendmsg = {"type": SendMsgType.server_to_channel,
                       "msg": sendmsg
                       }
        elif commandid == 3000012:
            if env_setting.LOCAL_SERVER == False:
                realurl = 'http://' + item + "/broadcasttoall"
            else:
                realurl = 'http://127.0.0.1/broadcasttoall'

            sendmsg = sendmsg

        async with aiohttp.ClientSession() as session:
            async with session.get(realurl, json=sendmsg) as response:
                if response.status == 200:
                    data = await response.text()
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'send_to_all_lobbyserver_future response:{0}'.format(data))

        await asyncio.sleep(0)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'send_to_all_lobbyserver_future except:{0}'.format(e))

    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'send_to_all_lobbyserver_future end:{0}'.format(sendmsg))

async def send_to_all_lobbyserver(app,sendmsg):

    try:
        db = app['DB'][0]
        result, clientdata = await db.getlobbyserverip()
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'send_to_all_lobbyserver ips:{0}'.format(clientdata))
        if result == pg_general.Apiresult.success:
            ips = clientdata.get('ip')
            if ips is not None:
                for item in ips:
                    asyncio.ensure_future(send_to_all_lobbyserver_future(item,sendmsg))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'send_to_all_lobbyserver except:{0}'.format(e))

async def bigprize_task_future(app,clientdata,type):    # type =0 金廳 , 1:銀廳
    db = app['DB'][0]

    bigwincontent_publicchat = app['bigwincontent_publicchat']
    bigmultipliercontent_publicchat = app['bigmultipliercontent_publicchat']

    pg_general.writelog(pg_general.PG_LogerLevel.info,
                        'bigprize_task_future create memberid:{0}'.format(clientdata.get('memberid')))
    total_result = pg_general.Apiresult.connectdberror
    bigprizehitamount = app['bigprizehitamount']
    bigprizewinamount = app['bigprizewinamount']

    try:

        gameid = clientdata.get('game_id')
        total_win = clientdata.get('total_win')
        memberid = clientdata.get('memberid')
        total_bet = clientdata.get('total_bet')

        avatar = clientdata.get('avatar')
        nickname = clientdata.get('nickname')

        multiplier = int(total_win/total_bet)

        gamename = clientdata.get('gamename')

        seat_data = clientdata.get('seat_data').split('_')[2]

        bigprize = []
        bigprize_chatpublic = {}
        bigmultiplier_chatpublic = {}
        # 判斷是否 倍數 通知
        if multiplier >= bigprizehitamount:
            bigprize.append({
                "gameid": gameid,
                "type": 0,
                "amount": multiplier,
                "memberid": memberid,
                "nickname": nickname,
                "avatar": avatar
            })
            # 聊天室 大獎公告
            chattime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')
            publicchat_bigprize_content = bigmultipliercontent_publicchat.format(nickname, gamename, format(multiplier, ',d'),seat_data)
            bigmultiplier_chatpublic = {
                "time": chattime,
                "avatar": AVATAR_SYSTEM,
                "nickname": "系統公告",
                "type": 0,
                "content": publicchat_bigprize_content,
                "bubbleinfo": {
                    "memberid": memberid,
                    "nickname": nickname,
                    "avatar": avatar
                }
            }


        # 判斷是否分數通知
        if total_win >= bigprizewinamount:
            bigprize.append({
                "gameid": gameid,
                "type": 1,
                "amount": total_win,
                "memberid": memberid,
                "nickname": nickname,
                "avatar": avatar
            })
            # 聊天室 大獎公告
            chattime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')
            publicchat_bigprize_content = bigwincontent_publicchat.format(nickname,gamename,format(total_win,',d'),seat_data)
            bigprize_chatpublic = {
                "time": chattime,
                "avatar": AVATAR_SYSTEM,
                "nickname": "系統公告",
                "type": 0,
                "content": publicchat_bigprize_content,
                "bubbleinfo":{
                    "memberid": memberid,
                    "nickname": nickname,
                    "avatar": avatar
                }

            }


        if len(bigprize) >0 :
            msg_info = {"commandid": 3000006, "bigprize": bigprize, "delay": 30}
            await send_to_all_lobbyserver(app, msg_info)

        if bigprize_chatpublic != {}:
            msg_info = {"commandid": 3000022, "data": bigprize_chatpublic, "delay": 30}
            await send_to_all_lobbyserver(app, msg_info)

        if bigmultiplier_chatpublic != {}:
            msg_info = {"commandid": 3000022, "data": bigmultiplier_chatpublic, "delay": 30}
            await send_to_all_lobbyserver(app, msg_info)


        total_result = pg_general.Apiresult.success
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, 'bigprize_task_future except:{0}'.format(e))
    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.info, 'bigprize_task_future exit result:{0}'.format(total_result))

async def quest_task_future_silver(app,clientdata):     #  銀幣 任務 future , 每一次 result 都會開一個 future 來做
    db = app['DB'][0]
    redis_obj = app['redis']
    pg_general.writelog(pg_general.PG_LogerLevel.info,
                        'quest_task_future_silver create memberid:{0}'.format(clientdata.get('memberid')))
    total_result = pg_general.Apiresult.connectdberror

    try:
        # call ps get free game information 判斷此單是否有進去 free game
        txn_id = clientdata.get('txn_id')
        clientdata['freegameflag'] = clientdata.get('has_bonus')


        if clientdata.get('seat_data') is not None: # seat mode
            seatnum = clientdata.get('seat_data').split('_')[2]

            result, updatedata = await db.make_seats_data_update(redis_obj,clientdata,'silver')
            senddata = {}
            senddata['cmd'] = "result"
            senddata['token'] = clientdata.get('token')
            senddata['lobbyserverip'] = clientdata.get('lobbyserverip')
            senddata['hallid'] = 1    # 銀幣廳
            senddata['gameid'] = clientdata.get('game_id')
            senddata['seatnum'] = seatnum
            senddata['unopenturn'] = updatedata.get('unopenturn')
            senddata['avgturn'] = updatedata.get('avgturn')
            senddata['his1turn'] = updatedata.get('his1turn')
            senddata['his2turn'] = updatedata.get('his2turn')
            senddata['his3turn'] = updatedata.get('his3turn')
            senddata['his1multi'] = updatedata.get('his1multi')
            senddata['his2multi'] = updatedata.get('his2multi')
            senddata['his3multi'] = updatedata.get('his3multi')
            senddata['memberid'] = clientdata.get('memberid')

            lobbyserverip = clientdata.get("lobbyserverip")
            if lobbyserverip is None:
                raise ValueError

            realurl = 'http://' + lobbyserverip + "/result/"

            async with aiohttp.ClientSession() as session:
                async with session.get(realurl,json=senddata) as response:
                    if response.status == 200:
                        data = await response.text()
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            'quest_task_future_silver call lobbyserver result:{0}'.format(data))
                    else:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'quest_task_future_silver call lobbyserver fail txn_id:{0}'.format(txn_id))
            await asyncio.sleep(0)


        total_result = pg_general.Apiresult.success
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, 'quest_task_future_silver except:{0}'.format(e))
    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.info, 'quest_task_future_silver exit result:{0}'.format(total_result))


async def quest_task_future(app,clientdata):     # 金幣 任務 future , 每一次 result 都會開一個 future 來做
    db = app['DB'][0]
    redis_obj = app['redis']
    pg_general.writelog(pg_general.PG_LogerLevel.info, 'quest_task_future create memberid:{0}'.format(clientdata.get('memberid')))
    total_result = pg_general.Apiresult.connectdberror

    try:
        # call ps get free game information 判斷此單是否有進去 free game
        txn_id = clientdata.get('txn_id')
        clientdata['freegameflag'] = clientdata.get('has_bonus')


        # 做會員 mmeber.biggestmultiplier, member.biggestwins
        result = await db.do_biggest_multiplier_wins(clientdata)

        # make 50倍送轉輪活動
        result = await db.make_free_wheel_action(redis_obj,clientdata)

        if clientdata.get('seat_data') is not None: # seat mode
            seatnum = clientdata.get('seat_data').split('_')[2]

            result, updatedata = await db.make_seats_data_update(redis_obj,clientdata,'gold')
            senddata = {}
            senddata['cmd'] = "result"
            senddata['token'] = clientdata.get('token')
            senddata['lobbyserverip'] = clientdata.get('lobbyserverip')
            senddata['hallid'] = 0    # 金幣廳
            senddata['gameid'] = clientdata.get('game_id')
            senddata['seatnum'] = seatnum
            senddata['unopenturn'] = updatedata.get('unopenturn')
            senddata['avgturn'] = updatedata.get('avgturn')
            senddata['his1turn'] = updatedata.get('his1turn')
            senddata['his2turn'] = updatedata.get('his2turn')
            senddata['his3turn'] = updatedata.get('his3turn')
            senddata['his1multi'] = updatedata.get('his1multi')
            senddata['his2multi'] = updatedata.get('his2multi')
            senddata['his3multi'] = updatedata.get('his3multi')
            senddata['memberid'] = clientdata.get('memberid')

            lobbyserverip = clientdata.get("lobbyserverip")
            if lobbyserverip is None:
                raise ValueError

            realurl = 'http://' + lobbyserverip + "/result/"

            async with aiohttp.ClientSession() as session:
                async with session.get(realurl,json=senddata) as response:
                    if response.status == 200:
                        data = await response.text()
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            'quest_task_future call lobbyserver result:{0}'.format(data))
                    else:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'quest_task_future call lobbyserver fail txn_id:{0}'.format(txn_id))
            await asyncio.sleep(0)


        total_result = pg_general.Apiresult.success
    except Exception as e :
        pg_general.writelog(pg_general.PG_LogerLevel.error, 'quest_task_future except:{0}'.format(e))
    finally:
        pg_general.writelog(pg_general.PG_LogerLevel.info, 'quest_task_future exit result:{0}'.format(total_result))



async def bet_queue_future(app,betdata):
    db = app["DB"][0]

    error = ''
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'bet_queue_future betdata:{0}'.format(betdata))

        if betdata is None or betdata == {}:  # 如果是空的 跳到 finally
            raise ValueError('betdata is None or == {}')

        result , clientdata = await db.bet_process(betdata)

        lobbyserverip = clientdata.get("lobbyserverip")
        if lobbyserverip is None:
            raise ValueError('lobbyserverip is None')

        realurl = 'http://' + lobbyserverip + "/bet/"


        async with aiohttp.ClientSession() as session:
            async with session.get(realurl,json=clientdata) as response:
                if response.status == 200:
                    data = await response.text()
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'bet_queue_future response result:{0}'.format(data))

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'bet_queue_future response except:{0}'.format(e))
    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'bet_queue_future response Value except:{0}'.format(e))


async def webapi_getserverstatus_handle(request):
    app = request.app
    db = app["DB"][0]

    serverstatus = await db.web_getserverstatus()

    return aiohttp.web.json_response(serverstatus)

async def webapi_getrichestrank_handle(request):

    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    rank_richsest = await redis_obj.get_json_value('rank_richest')

    return aiohttp.web.json_response(rank_richsest)

async def webapi_add_comment_handle(request):
    app = request.app
    db = app['DB'][0]

    resultdata = {"status_code": 1}

    content = request.rel_url.query.get('content')
    typeid = request.rel_url.query.get('typeid')
    memberid = request.rel_url.query.get('memberid')


    if None not in [content,typeid,memberid]:
        result = await db.webapi_add_comment(memberid,typeid,content)



        resultdata = {"status_code": 0}


    return aiohttp.web.json_response(resultdata)

async def webapi_ecpay_credit_start_purchase_handle(request):

    ecpaydata ={
        "ProductName": request.rel_url.query.get("ProductName"),
        'Amount': request.rel_url.query.get('Amount'),
        "ProductNum": request.rel_url.query.get('ProductNum'), # 產包代號
        "token": request.rel_url.query.get('token'),
        "paymentStr": request.rel_url.query.get('paymentStr'),
        "paymentType": request.rel_url.query.get('paymentType'),
        "CarruerType": request.rel_url.query.get('CarruerType'), # 發票載具種類0: 電子發票, 1: 自然人頻正
        "Donation": request.rel_url.query.get('Donation'),
        "LoveCode": request.rel_url.query.get('LoveCode'),
        "CarruerNum": request.rel_url.query.get('CarruerNum'),
        "CustomerAddr": request.rel_url.query.get('CustomerAddr'),
        "CustomerPhone": request.rel_url.query.get('CustomerPhone'),
        "CustomerEmail": request.rel_url.query.get('CustomerEmail'),
        "CustomerName": request.rel_url.query.get('CustomerName'),
        "invoiceAgent": request.rel_url.query.get('invoiceAgent'),
        "CustomerIdentifier": request.rel_url.query.get('CustomerIdentifier'),
        "memberid": request.rel_url.query.get('memberid')
    }

    app = request.app
    db = app['DB'][0]
    result , clientdata = await db.webapi_ecpay_credit_start_purchase(ecpaydata)

    return aiohttp.web.json_response(clientdata)

async def webapi_ecpay_credit_order_result_handle(request):
    orderresultdata = dict(request.rel_url.query)
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    cardinfo = app['cardinfo']
    clientdata = {"status_code": 1}

    if orderresultdata is not None:
        result, clientdata = await db.webapi_ecpay_credit_order_result(redis_obj,cardinfo,orderresultdata)

    return aiohttp.web.json_response(clientdata)

async def webapi_serial_input_handle(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    resultdata = {
        "status_code": 1,
        "msg": "序號輸入錯誤, 請重新輸入 !!"
    }

    serial = request.rel_url.query.get('serial')
    logintoken = request.rel_url.query.get('logintoken')
    memberid = request.rel_url.query.get('memberid')

    if None not in [memberid,logintoken,serial]:
        result , clientdata = await db.webapi_serial_input(logintoken,memberid,serial)

        if result == pg_general.Apiresult.success:
            resultdata['status_code'] = clientdata.get('errcode')
            resultdata['msg'] = clientdata.get('errdescription')

    return aiohttp.web.json_response(resultdata)

async def webapi_loginfb_handle(request):
    app = request.app
    db = app['DB'][0]
    fbavatarobj = app["pg_fbavatar"]

    resultdata = {
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    fbid = request.rel_url.query.get('fbid')
    fbtoken = request.rel_url.query.get('fbtoken')
    user_region = request.rel_url.query.get('user_region')
    user_region_sub = request.rel_url.query.get('user_region_sub')
    user_city = request.rel_url.query.get('user_city')
    user_ip = request.rel_url.query.get('user_ip')



    if None not in [fbid]:
        result, clientdata = await db.webapi_loginfb(fbavatarobj,fbid,fbtoken,user_region,user_region_sub,user_city,user_ip)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'webapi_loginfb_handle fbid:{0}, send:{1}'.format(fbid, resultdata))
    return aiohttp.web.json_response(resultdata)

async def webapi_loginbytoken_handle(request):      # renew token
    app = request.app
    db = app['DB'][0]

    resultdata = {
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    fbid = request.rel_url.query.get('fbid')
    if fbid == 'None':
        fbid = None
    username = request.rel_url.query.get('username')
    if username == 'None':
        username = None
    weblogintoken = request.rel_url.query.get('weblogintoken')
    if weblogintoken == 'None':
        weblogintoken = None

    if None not in [weblogintoken,fbid] or None not in [weblogintoken,username] :
        result, clientdata = await db.webapi_loginbytoken(fbid,weblogintoken,username)
        resultdata['apiresult'] = result

        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'webapi_loginfb_handle fbid:{0}, send:{1}'.format(fbid, resultdata))
    return aiohttp.web.json_response(resultdata)



async def webapi_loginusername_handle(request):
    app = request.app
    db = app['DB'][0]

    resultdata = {
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    username = request.rel_url.query.get('username')
    password = request.rel_url.query.get('password')
    user_region = request.rel_url.query.get('user_region')
    user_region_sub = request.rel_url.query.get('user_region_sub')
    user_city = request.rel_url.query.get('user_city')
    user_ip = request.rel_url.query.get('user_ip')

    if None not in [username,password]:
        result, clientdata = await db.webapi_loginusername(username,password, user_region, user_region_sub, user_city, user_ip)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'webapi_loginusername_handle username:{0}, send:{1}'.format(username, resultdata))
    return aiohttp.web.json_response(resultdata)



async def webapi_getgashwalletitem_handle(request):
    app = request.app
    db = app['DB'][0]
    clientdata = {}

    result , clientdata = await db.webapi_getgashwalletitem()
    resultdata = clientdata

    return aiohttp.web.json_response(resultdata)

async def webapi_getgashpointitem_handle(request):
    app = request.app
    db = app['DB'][0]
    clientdata = {}

    result, clientdata = await db.webapi_getgashpointitem()
    resultdata = clientdata

    return aiohttp.web.json_response(resultdata)

# 3-1 智冠驗證廠商通行證
async def mycard_gashpoints_handle(request):
    # 取得info資料庫的預設值
    app = request.app
    db = app['DB'][0]
    getinfo = await db.get_mycardinfo()

    # 如果無法取得資料
    if getinfo == None:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "It did not get db data in 3-1")
        # 錯誤回傳給前端
        return_message = {"return_msg": "3-1沒有取得預設資料", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    # 處理參數
    # 資料庫取得的變數是小寫
    # 前端給我們的變數是大寫
    # 傳送給智冠的變數也是大寫
    FacServiceId = pg_general.converttype(getinfo["facserviceid"], str)  # 廠商服務代碼

    # 產生隨機
    characters = string.ascii_letters.lower()
    pwd_e = "".join(random.choice(characters) for i in range(random.randint(6, 6)))  # 取得6碼小寫英文字
    pwd_d = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')  # 取得現在時間的數字
    FacTradeSeq = pwd_e + pwd_d  # 廠商交易序號(每筆都不一樣)

    TradeType = pg_general.converttype(getinfo["tradetype"], str)  # 交易模式
    ServerId = ""  # 伺服器代號
    CustomerId = pg_general.converttype(request.rel_url.query.get("CustomerId", ""), str)  # 會員代號
    PaymentType = pg_general.converttype(getinfo["paymenttype"], str)  # 付費方式
    ItemCode = ""  # 品項代碼
    ProductName = pg_general.converttype(getinfo["productname"], str)  # 產品名稱
    Amount = pg_general.converttype(request.rel_url.query.get("Amount", ""), str)  # 交易金額
    Currency = pg_general.converttype(getinfo["currency"], str)  # 幣別
    SandBoxMode = pg_general.converttype(request.rel_url.query.get("SandBoxMode", "false"), str)  # 是否為測試環境：不是布林值，是小寫字串
    FacReturnURL = pg_general.converttype(request.rel_url.query.get("FacReturnURL", ""), str)  # 交易結果回傳網址
    Key = pg_general.converttype(getinfo["key"], str)  # 智冠給的廠商用Key

    # 如果必填欄位沒東西
    if CustomerId == "" or SandBoxMode == "" or FacReturnURL == "" or Amount == "":
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "You did not write parameters in 3-1.")
        # 錯誤回傳給前端
        return_message = {"return_msg": "3-1必填欄位沒寫", "status_code": -1}
        return aiohttp.web.json_response(return_message)

    # 建立ParaValue，參數依文件的順序組成字串
    ParaValue = "?FacServiceId=" + FacServiceId + "&FacTradeSeq=" + FacTradeSeq + "&TradeType=" + TradeType + "&ServerId=" + ServerId + "&CustomerId=" + CustomerId + "&PaymentType=" + PaymentType + "&ItemCode=" + ItemCode + "&ProductName=" + ProductName + "&Amount=" + Amount + "&Currency=" + Currency + "&SandBoxMode=" + SandBoxMode + "&FacReturnURL=" + FacReturnURL

    # 產生一個Hash驗證碼
    preHashValue = FacServiceId + FacTradeSeq + TradeType + ServerId + CustomerId + PaymentType + ItemCode + ProductName + Amount + Currency + SandBoxMode + FacReturnURL + Key
    ###WriteLog(FacTradeSeq, "preHashValue|" + preHashValue)
    # 編碼
    EncodeHashValue = parse.quote_plus(preHashValue)
    # 將url內的「冒號」%3A轉為小寫
    EncodeHashValue = EncodeHashValue.replace("%3A", "%3a")
    # 將url內的「正斜線」%2F轉為小寫
    EncodeHashValue = EncodeHashValue.replace("%2F", "%2f")
    # 編成雜湊碼
    Hash = hashlib.sha256(EncodeHashValue.encode("utf-8"))
    # 組成16進制字串
    Hash = Hash.hexdigest()

    # Hash有東西後，把它加進去ParaValue內
    ParaValue += "&Hash=" + Hash
    ###WriteLog(FacTradeSeq, "preHashValue|" + Hash)

    # 是否為測試環境
    official_url = "https://b2b.mycard520.com.tw/MyBillingPay/v1.1/AuthGlobal"    # 正式環境
    test_url = "https://testb2b.mycard520.com.tw/MyBillingPay/v1.1/AuthGlobal"    # 測試環境
    if SandBoxMode == "false":    # 不是布林值，是字串
        b2b_api_url = official_url + ParaValue
    else:
        b2b_api_url = test_url + ParaValue

    # 向智冠提交請求驗證Auth
    SendStatus, returnMsg = await Send_MyCard_b2b(b2b_api_url, "3-1")

    # 將輸入參數整理成小寫dict，準備新增至資料庫
    inter_3_1 = {"FacServiceId": FacServiceId,
                 "FacTradeSeq": FacTradeSeq,
                 "TradeType": TradeType,
                 "ServerId": ServerId,
                 "CustomerId": CustomerId,
                 "PaymentType": PaymentType,
                 "ItemCode": ItemCode,
                 "ProductName": ProductName,
                 "Amount": Amount,
                 "Currency": Currency,
                 "SandBoxMode": SandBoxMode,
                 "FacReturnURL": FacReturnURL,
                 "Hash": Hash}

    # 取得Send_MyCard_b2b智冠MyCard回傳結果後，將結果新增資料表
    app = request.app
    db = app['DB'][0]
    message = await db.mycard_gashpoints(inter_3_1, returnMsg)

    # 判斷回傳結果資料有沒有新增至資料表
    if message == False:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Insert DB fail in 3-1.")
        # 錯誤回傳給前端
        return_message = {"return_msg": "3-1新增資料失敗", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    if SendStatus == True:
        # ReturnCode是1，請求成功
        if returnMsg["ReturnCode"] == "1":
            # 準備回傳給前端「跳轉MyCard儲值頁面」的網址，是正式環境還是測試環境
            official_url_3_2 = "https://www.mycard520.com.tw/MyCardPay/"
            test_url_3_2 = "https://test.mycard520.com.tw/MyCardPay/"
            if SandBoxMode == "false":    # 不是布林值，是字串
                mycard_url = official_url_3_2 + "?AuthCode=" + returnMsg["AuthCode"]
            else:
                mycard_url = test_url_3_2 + "?AuthCode=" + returnMsg["AuthCode"]

            # log
            pg_general.writelog(pg_general.PG_LogerLevel.info, "{} in 3-1".format(returnMsg["ReturnMsg"]))
            # 正確回傳給前端
            return_message = {"return_msg": returnMsg["ReturnMsg"], "status_code": 200, "mycard_url": mycard_url}
            return aiohttp.web.json_response(return_message)

        else:
            # log
            pg_general.writelog(pg_general.PG_LogerLevel.error, "{} in 3-1".format(returnMsg["ReturnMsg"]))
            # 錯誤回傳給前端
            return_message = {"return_msg": returnMsg["ReturnMsg"], "status_code": 406}
            return aiohttp.web.json_response(return_message)

    else:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Call api fail in 3-1.")
        # 錯誤回傳給前端
        return_message = {"return_msg": "Call api fail in 3-1.", "status_code": 401}
        return aiohttp.web.json_response(return_message)

# 3-2-4 確認交易並回傳交易結果給廠商 → 接收回傳交易結果
async def mycard_mcresult_handle(request):
    Json3_4_2 = {
        "ReturnCode": request.rel_url.query.get("ReturnCode", "") ,   # 回傳結果代碼
        "ReturnMsg": request.rel_url.query.get("ReturnMsg", ""),    # 訊息描述
        "PayResult": request.rel_url.query.get("PayResult", ""),    # 交易結果代碼
        "FacTradeSeq": request.rel_url.query.get("FacTradeSeq", ""),    # 廠商交易序號
        "PaymentType": request.rel_url.query.get("PaymentType", ""),    # 付費方式
        "Amount": request.rel_url.query.get("Amount", ""),    # 金額
        "Currency": request.rel_url.query.get("Currency", ""),    # 幣別
        "MyCardTradeNo": request.rel_url.query.get("MyCardTradeNo", ""),
        "MyCardType": request.rel_url.query.get("MyCardType", ""),    # 通路代碼，PaymentType = INGAME時才有值
        "PromoCode": request.rel_url.query.get("PromoCode", ""),    # 活動代碼
        "Hash": request.rel_url.query.get("Hash", "")    # 驗證碼
    }

    # 準備放入資料表
    app = request.app
    db = app['DB'][0]
    message = await db.mycard_mcresult(Json3_4_2)

    if message == True:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.info, "Insert db success in 3-2-4.")
        # 正確回傳
        return_message = {"return_msg": "3-2-4新增資料成功", "status_code": 200}
        return aiohttp.web.json_response(return_message)
    else:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Insert db fail in 3-2-4.")
        # 錯誤回傳
        return_message = {"return_msg": "3-2-4新增資料失敗", "status_code": -10}
        return aiohttp.web.json_response(return_message)

# 3-3 驗證MyCard交易結果
async def mycard_checkMyCardTradeResult_handle(request):
    FacTradeSeq = pg_general.converttype(request.rel_url.query.get("FacTradeSeq", ""), str)    # 廠商交易序號

    # 如果沒有廠商交易序號
    if FacTradeSeq == "":
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "FacTradeSeq is none in 3-3")
        # 錯誤回傳
        return_message = {"return_msg": "3-3沒有廠商交易序號", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    # 從資料表內取得AuthCode與SandBoxMode與Amount與CustomerId
    app = request.app
    db = app['DB'][0]
    gethistory = await db.get_mycardhistory_AuthCode_SandBoxMode(FacTradeSeq)

    # 是否取得資料
    if gethistory == None:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "It did not get db data in 3-3")
        # 錯誤回傳
        return_message = {"return_msg": "3-3未取得交易授權碼或環境參數", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    # 拆解Json Load
    AuthCode = gethistory["authcode"]
    SandBoxMode = gethistory["sandboxmode"]
    Amount = gethistory["amount"]
    CustomerId = gethistory["customerid"]
    TradeSeq = gethistory["tradeseq"]
    # MyCardTradeNo = gethistory["mycardtradeno"]
    FacTradeSeq = gethistory["factradeseq"]
    Currency = gethistory["currency"]
    PaymentType = gethistory["paymenttype"]

    # 如果沒有交易授權碼或沒有給環境
    if AuthCode == "" or SandBoxMode == "" or Amount == "" or CustomerId == "":
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "AuthCode or SandBoxMode or Amount or CustomerId is none in 3-3")
        # 錯誤回傳
        return_message = {"return_msg": "3-3交易授權碼或環境參數是空的", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    # 組合ParaValue
    ParaValue = "?AuthCode=" + AuthCode

    # 是否為測試環境
    official_url = "https://b2b.mycard520.com.tw/MyBillingPay/v1.1/TradeQuery"    # 正式環境
    test_url = "https://testb2b.mycard520.com.tw/MyBillingPay/v1.1/TradeQuery"    # 測試環境
    if SandBoxMode == "false":    # 不是布林值，是字串
        b2b_api_url = official_url + ParaValue
    else:
        b2b_api_url = test_url + ParaValue

    # 向智冠提交請求驗證Auth
    SendStatus, returnMsg = await Send_MyCard_b2b(b2b_api_url, "3-3")

    # 取得Send_MyCard_b2b智冠MyCard回傳結果後，將結果新增至DB
    app = request.app
    db = app['DB'][0]
    # 如果沒有經過3-2-4改3-6補儲，則MyCardTradeNo會出現在這裡
    message, MyCardTradeNo = await db.mycard_checkMyCardTradeResult(AuthCode, returnMsg)

    # 判斷回傳結果資料有沒有新增至資料表
    if message == False:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Insert mycardhistory failed in 3-3.")
        # 錯誤回傳
        return_message = {"return_msg": "3-3新增資料失敗", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    if SendStatus == True:
        # ReturnCode是1，查有資料，交易存在
        if returnMsg["ReturnCode"] == "1":
            # PayResult是3，交易成功
            if returnMsg["PayResult"] == "3":
                # log
                pg_general.writelog(pg_general.PG_LogerLevel.info, "{} in 3-3".format(returnMsg["ReturnMsg"]))
                # 正確回傳
                return_message = {"return_msg": returnMsg["ReturnMsg"], "status_code": 200, "AuthCode": AuthCode, "SandBoxMode": SandBoxMode, "Amount": Amount, "CustomerId": CustomerId, "TradeSeq": TradeSeq, "MyCardTradeNo": MyCardTradeNo, "FacTradeSeq": FacTradeSeq, "Currency": Currency, "PaymentType": PaymentType}
                return aiohttp.web.json_response(return_message)

            else:
                # log
                pg_general.writelog(pg_general.PG_LogerLevel.error, "{} in 3-3".format(returnMsg["ReturnMsg"]))
                # 錯誤回傳
                return_message = {"return_msg": returnMsg["ReturnMsg"], "status_code": 402}
                return aiohttp.web.json_response(return_message)

        else:
            # log
            pg_general.writelog(pg_general.PG_LogerLevel.error, "{} in 3-3".format(returnMsg["ReturnMsg"]))
            # 錯誤回傳
            return_message = {"return_msg": returnMsg["ReturnMsg"], "status_code": 406}
            return aiohttp.web.json_response(return_message)

    else:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Call api fail in 3-3.")
        # 錯誤回傳
        return_message = {"return_msg": "Call api fail in 3-3.", "status_code": 401}
        return aiohttp.web.json_response(return_message)

# 3-4 確認MyCard交易，並進行請款
async def mycard_mycardReturnInvoiceResult_handle(request):
    AuthCode = pg_general.converttype(request.rel_url.query.get("AuthCode", ""), str)  # 交易授權碼
    SandBoxMode = pg_general.converttype(request.rel_url.query.get("SandBoxMode", ""), str)  # 是否為測試環境
    Amount = pg_general.converttype(request.rel_url.query.get("Amount", ""), str)  # 交易金額
    CustomerId = pg_general.converttype(request.rel_url.query.get("CustomerId", ""), str)  # 會員代號
    TradeSeq = pg_general.converttype(request.rel_url.query.get("TradeSeq", ""), str)  # MyCard 交易序號
    MyCardTradeNo = pg_general.converttype(request.rel_url.query.get("MyCardTradeNo", ""), str)
    FacTradeSeq = pg_general.converttype(request.rel_url.query.get("FacTradeSeq", ""), str)  # 廠商交易序號
    Currency = pg_general.converttype(request.rel_url.query.get("Currency", ""), str)  # 幣別
    PaymentType = pg_general.converttype(request.rel_url.query.get("PaymentType", ""), str)  # 付費方式

    # 如果沒有交易授權碼，沒有給環境，沒有金額
    if AuthCode == "" or SandBoxMode == "" or Amount == "" or CustomerId == "" or TradeSeq == "" or MyCardTradeNo == "" or FacTradeSeq == "" or Currency == "" or PaymentType == "":
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "AuthCode or SandBoxMode or Amount or CustomerId is none in 3-4")
        # 錯誤回傳
        return_message = {"return_msg": "3-4沒有交易授權碼、環境、金額", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    # 組合ParaValue
    ParaValue = "?AuthCode=" + AuthCode

    # 是否為測試環境
    official_url = "https://b2b.mycard520.com.tw/MyBillingPay/v1.1/PaymentConfirm"  # 正式環境
    test_url = "https://testb2b.mycard520.com.tw/MyBillingPay/v1.1/PaymentConfirm"  # 測試環境
    if SandBoxMode == "false":    # 不是布林值，是字串
        b2b_api_url = official_url + ParaValue
    else:
        b2b_api_url = test_url + ParaValue

    # 向智冠提交請求驗證Auth
    SendStatus, returnMsg = await Send_MyCard_b2b(b2b_api_url, "3-4")

    # 取得Send_MyCard_b2b智冠MyCard回傳結果後，將結果新增至DB
    app = request.app
    db = app['DB'][0]
    message = await db.mycard_mycardReturnInvoiceResult(AuthCode, returnMsg)

    # 判斷回傳結果資料有沒有新增至資料表
    if message == False:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Insert mycardhistory failed in 3-4.")
        # 錯誤回傳
        return_message = {"return_msg": "3-4新增資料失敗", "status_code": -10}
        return aiohttp.web.json_response(return_message)

    if SendStatus == True:
        # ReturnCode是1，請求成功
        if returnMsg["ReturnCode"] == "1":
            # update member acc 發送點數給玩家 = 更新點數至member資料庫
            app = request.app
            db = app['DB'][0]
            redis_obj = app['redis']
            cardinfo = app['cardinfo']
            update_db = await db.mycard_update_member_point(Amount, CustomerId, TradeSeq, MyCardTradeNo, FacTradeSeq, Currency, PaymentType, redis_obj, cardinfo)

            # 如果會員點數沒有入帳
            if update_db == False:
                # log
                pg_general.writelog(pg_general.PG_LogerLevel.error, "Update member points failed in 3-4.")
                # 錯誤回傳
                return_message = {"return_msg": "3-4會員點數沒入帳", "status_code": 507}
                return aiohttp.web.json_response(return_message)
            else:
                # log
                pg_general.writelog(pg_general.PG_LogerLevel.info, "{} in 3-4".format(returnMsg["ReturnMsg"]))
                # 正確回傳
                return_message = {"return_msg": returnMsg, "status_code": 200}
                return aiohttp.web.json_response(return_message)

        else:
            # log
            pg_general.writelog(pg_general.PG_LogerLevel.error, "{} in 3-4".format(returnMsg["ReturnMsg"]))
            # 錯誤回傳
            return_message = {"return_msg": returnMsg, "status_code": 406}
            return aiohttp.web.json_response(return_message)

    else:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Call api fail in 3-4.")
        # 錯誤回傳
        return_message = {"return_msg": "Call api fail in 3-4.", "status_code": 401}
        return aiohttp.web.json_response(return_message)

# 3-6 補儲值 → 新增智冠補儲值輸入值至資料庫
async def mycard_mcredeposit_handle(request):
    Json3_6 = {
        "ReturnCode": request.rel_url.query.get("ReturnCode", ""),  # 回傳結果代碼
        "ReturnMsg": request.rel_url.query.get("ReturnMsg", ""),  # 訊息描述
        "FacServiceId": request.rel_url.query.get("FacServiceId", ""),  # 廠商服務代碼
        "FacTradeSeq": request.rel_url.query.get("FacTradeSeq", "")  # 廠商交易序號
    }

    app = request.app
    db = app['DB'][0]
    message = await db.mycard_mcredeposit(Json3_6)

    # 判斷回傳結果資料有沒有新增至資料表
    if message == True:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.info, "Insert db success in 3-6.")
        # 正確回傳
        return_message = {"return_msg": "3-6新增資料成功", "status_code": 200}
        return aiohttp.web.json_response(return_message)
    else:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "Insert db fail in 3-6.")
        # 錯誤回傳
        return_message = {"return_msg": "3-6新增資料失敗", "status_code": -10}
        return aiohttp.web.json_response(return_message)

# 3-7-single 交易成功資料的差異比對，供智冠MyCard查詢：「單筆查詢」
async def mycard_mcresultcheck_single_handle(request):
    trade_number = {
        "MyCardTradeNo": request.rel_url.query.get("MyCardTradeNo", "")   # 卡片號碼，或會員扣點交易序號，端看PaymentType而定
    }
    # PaymentType = INGAME時，傳MyCard卡片號碼
    # PaymentType = COSTPOINT時，傳會員扣點交易序號，格式為MMS開頭+數字
    # 其餘PaymentType為Billing小額付款交易，傳Billing交易序號

    # 抓取資料庫內容
    app = request.app
    db = app['DB'][0]
    Difference_data = await db.mycard_mcresultcheck_single_get(trade_number)

    # 抓取失敗
    if Difference_data == None:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "get single data failed in 3-7.")
        # 錯誤回傳
        return_to_software = "3-7無匹配資料或參數沒有值<BR>"
        return aiohttp.web.json_response(return_to_software)

    # regular英國時間 → iso8601台北時間 → 這是智冠要的！
    # regular_utc_time = datetime.datetime.strptime(Difference_data["utcnowdate"], '%Y-%m-%d %H:%M:%S')
    regular_utc_time = Difference_data["insertutcnowdate"]
    regular_taipei_time = regular_utc_time + datetime.timedelta(hours=8)
    iso_taipei_time = regular_taipei_time.isoformat()
    no_microsecond = datetime.datetime.strptime(iso_taipei_time, '%Y-%m-%dT%H:%M:%S.%f').replace(microsecond=0)
    iso_taipei_no_microsecond = no_microsecond.isoformat()

    # 處理後的時間新增至Difference_data
    Difference_data["tradedatetime"] = iso_taipei_no_microsecond

    # 原本取得的utc時間刪除
    del Difference_data["insertutcnowdate"]

    # 成功回傳給智冠
    str3_7 = "{},{},{},{},{},{},{},{}<BR>".format(Difference_data["paymenttype"], Difference_data["tradeseq"], Difference_data["mycardtradeno"], Difference_data["factradeseq"], Difference_data["customerid"], Difference_data["amount"], Difference_data["currency"], Difference_data["tradedatetime"])
    return_to_software = str3_7
    return aiohttp.web.json_response(return_to_software)

# 3-7-multi 交易成功資料的差異比對，供智冠MyCard查詢：「多筆查詢」
async def mycard_mcresultcheck_multi_handle(request):
    datetime_range = {
        "StartDateTime": request.rel_url.query.get("StartDateTime", ""),
        "EndDateTime": request.rel_url.query.get("EndDateTime", "")
    }

    # iso8601台北時間 → regular英國時間 → 比對金爽資料庫
    # _S起始時間；_E結束時間
    regular_taipei_time_S = datetime.datetime.strptime(datetime_range["StartDateTime"], '%Y-%m-%dT%H:%M:%S')
    regular_utc_time_S = regular_taipei_time_S - datetime.timedelta(hours=8)
    # iso_utc_time_S = regular_taipei_time_S.astimezone(pytz.utc)
    # regular_utc_time_S = iso_utc_time_S.strftime('%Y-%m-%d %H:%M:%S')

    regular_taipei_time_E = datetime.datetime.strptime(datetime_range["EndDateTime"], '%Y-%m-%dT%H:%M:%S')
    regular_utc_time_E = regular_taipei_time_E - datetime.timedelta(hours=8)
    # iso_utc_time_E = regular_taipei_time_E.astimezone(pytz.utc)
    # regular_utc_time_E = iso_utc_time_E.strftime('%Y-%m-%d %H:%M:%S')

    # 處理後的時間丟回去datetime_range
    datetime_range["StartDateTime"] = regular_utc_time_S
    datetime_range["EndDateTime"] = regular_utc_time_E

    # 抓取資料庫內容
    app = request.app
    db = app['DB'][0]
    Difference_data = await db.mycard_mcresultcheck_multi_get(datetime_range)

    # 抓取失敗
    if Difference_data == None:
        # log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "get multi data failed in 3-7.")
        # 錯誤回傳
        return_to_software = "3-7無匹配資料或參數沒有值<BR>"
        return aiohttp.web.json_response(return_to_software)

    # 走訪多筆Difference_data
    for i in Difference_data:
        # regular英國時間 → iso8601台北時間 → 這是智冠要的！
        # regular_utc_time = datetime.datetime.strptime(i["utcnowdate"], '%Y-%m-%d %H:%M:%S')
        regular_utc_time = i["insertutcnowdate"]
        regular_taipei_time = regular_utc_time + datetime.timedelta(hours=8)
        iso_taipei_time = regular_taipei_time.isoformat()
        no_microsecond = datetime.datetime.strptime(iso_taipei_time, '%Y-%m-%dT%H:%M:%S.%f').replace(microsecond=0)
        iso_taipei_no_microsecond = no_microsecond.isoformat()

        # 處理後的時間新增至Difference_data
        i["tradedatetime"] = iso_taipei_no_microsecond

        # 原本取得的utc時間刪除
        del i['insertutcnowdate']

    # 將多筆整理成字串
    str_fetch_all = ""
    for i in Difference_data:
        str_fetch_one = "{},{},{},{},{},{},{},{}<BR>".format(i["paymenttype"], i["tradeseq"], i["mycardtradeno"], i["factradeseq"], i["customerid"], i["amount"], i["currency"], i["tradedatetime"])
        str_fetch_all = str_fetch_all + str_fetch_one

    # 成功回傳給智冠
    return_to_software = str_fetch_all
    return aiohttp.web.json_response(return_to_software)

# 向智冠提交請求驗證Auth
async def Send_MyCard_b2b(b2b_api_url, status_api):
    try:
        responce = requests.get(b2b_api_url)
        # 如果有回應資料
        if responce != None:
            result_data = json.loads(responce.text)
            # 如果智冠的responce是200
            if responce.status_code == 200:
                # 如果result_data沒東西
                if result_data == None:
                    pg_general.writelog((pg_general.PG_LogerLevel.error, "HttpStatusCode.OK但result_data = none in {}".format(status_api)))
                    return False, None
                elif result_data == "":
                    pg_general.writelog((pg_general.PG_LogerLevel.error, "HttpStatusCode.OK但result_data = 空值 in {}".format(status_api)))
                    return False, None
                else:
                    returnMsg = result_data
                    return True, returnMsg    # 正確回傳
            else:
                pg_general.writelog((pg_general.PG_LogerLevel.error, "BadRequest in {}".format(status_api)))
                return False, None
        else:
            pg_general.writelog((pg_general.PG_LogerLevel.error, "response = none in {}".format(status_api)))
            return False, None
    except Exception as e:
        pg_general.writelog((pg_general.PG_LogerLevel.error, 'pg_general: except:{0} in {1}'.format(e.args[0], status_api)))
        return False, None

async def webapi_get_gash_wallet_base64_handle(request):
    app = request.app
    db = app['DB'][0]
    clientdata = {}

    memberid = pg_general.converttype(request.rel_url.query.get('memberid'),int)
    itemid = pg_general.converttype(request.rel_url.query.get('itemid'),int)
    amount = pg_general.converttype(request.rel_url.query.get('amount'),int)

    result, clientdata = await db.webapi_get_gash_wallet_base64(memberid,itemid,amount)
    resultdata = clientdata

    return aiohttp.web.json_response(resultdata)

async def webapi_get_gash_point_base64_handle(request):
    app = request.app
    db = app['DB'][0]
    clientdata = {}

    memberid = pg_general.converttype(request.rel_url.query.get('memberid'), int)
    itemid = pg_general.converttype(request.rel_url.query.get('itemid'), int)
    amount = pg_general.converttype(request.rel_url.query.get('amount'), int)

    result, clientdata = await db.webapi_get_gash_point_base64(memberid, itemid, amount)
    resultdata = clientdata

    return aiohttp.web.json_response(resultdata)

async def webapi_ret_gash_wallet_base64_handle(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    cardinfo = app['cardinfo']
    clientdata = {}

    base64 = request.rel_url.query.get('data')

    result, clientdata = await db.webapi_ret_gash_wallet_base64(base64,redis_obj,cardinfo)
    resultdata = clientdata

    return aiohttp.web.json_response(resultdata)


async def webapi_ret_gash_point_base64_handle(request):
    app = request.app
    db = app['DB'][0]
    redis_obj = app['redis']
    cardinfo = app['cardinfo']
    clientdata = {}

    base64 = request.rel_url.query.get('data')

    result, clientdata = await db.webapi_ret_gash_point_base64(base64, redis_obj, cardinfo)
    resultdata = clientdata

    return aiohttp.web.json_response(resultdata)

async def webapi_logout_handle(request):
    app = request.app
    db = app['DB'][0]

    resultdata = {
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }
    fbid = request.rel_url.query.get('fbid')
    weblogintoken = request.rel_url.query.get('weblogintoken')
    username = request.rel_url.query.get('username')

    if None not in [fbid,weblogintoken] or None not in[username,weblogintoken]:
        result, clientdata = await db.webapi_logout(fbid, weblogintoken,username)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'webapi_logout_handle fbid:{0}, send:{1}'.format(fbid, resultdata))
    return aiohttp.web.json_response(resultdata)



async def testfbavatartobucket(app):
    pg_fb= app['pg_fbavatar']
    result,avatar_url = await pg_fb.upload_avatar("66",
                              "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=2183264558418225&height=50&width=50&ext=1565318424&hash=AeRN_Vq6DYd-FFng")

async def initialredis(app):
    pg_general.writelog(pg_general.PG_LogerLevel.info, "initial redis server connection start")
    redis = PGRedis()
    app['redis'] = redis
    if redis.initialflag:
        pg_general.writelog(pg_general.PG_LogerLevel.info, "initial redis server connection end")
    else:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "initial redis server connection error")




async def reloadallconfig_handle(request):
    app = request.app

    id = request.rel_url.query.get('id')

    if id != 'UUIIx123kjsdfkxKJKJKJ123KJKJHbHY*Y*':
        return aiohttp.web.HTTPNotFound()

    await get_all_settings(app)

    return aiohttp.web.Response(text='done')

async def setdebugmode_handle(request):
    app = request.app

    id = request.rel_url.query.get('id')
    mode = pg_general.converttype(request.rel_url.query.get('mode'),int)
    if id != 'UUIIx123kjsdfkxKJKdaddafasdfasdadfJKJ123adf3w423KJKJHbHY*Y*':
        return aiohttp.web.HTTPNotFound()


    if mode == 0:
        env_setting.DEBUG_LOG_MODE = False
    elif mode ==1:
        env_setting.DEBUG_LOG_MODE = True

    return aiohttp.web.Response(text='done')

async def testsettle_handle(request):
    app = request.app
    db = app['DB'][0]
    # await pg_namesample.changenamemtest(db)
    # content = request.rel_url.query.get('content')
    # content = db.
    print(content)
    return aiohttp.web.json_response('0')
def main(port=PORT):
    try:
        if not env_setting.LOCAL_SERVER:
            time.sleep(10)
        pg_general.writelog(pg_general.PG_LogerLevel.debug, "api server start...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = aiohttp.web.Application()
        app["DB"] = []
        app["client_dict"] = {}
        app["pg_fbavatar"] = PG_FBAVATAR()



        # initial Redis object
        loop.run_until_complete(initialredis(app))




        # create db connection
        loop.run_until_complete(createdbpool(app))
        # get all setting from db
        loop.run_until_complete(get_all_settings(app))

        # test
        # loop.run_until_complete(app['DB'][0].testgoogleiapconfirm())




        # for lobby server using
        app.router.add_route('GET', '/serverinfo/{smemberid}/{slogintoken}/', serverinfo_handle)
        app.router.add_route('GET', '/login/{smemberid}/{slogintoken}/', login_handle)
        app.router.add_route('GET', '/getmemberinfo/{smemberid}/{slogintoken}/', getmemberinfo_handle)
        app.router.add_route('GET', '/updateprofile/{smemberid}/{slogintoken}/', updateprofile_handle)
        app.router.add_route('GET', '/getdailybonusinfo/{smemberid}/{slogintoken}/', getdailybonusinfo_handle)
        app.router.add_route('GET', '/spindailybonus/{smemberid}/{slogintoken}/', spindailybonus_handle)
        app.router.add_route('GET', '/getpiggyinfo/{smemberid}/{slogintoken}/', getpiggyinfo_handle)
        app.router.add_route('GET', '/getmallinfo/{smemberid}/{slogintoken}/', getmallinfo_handle)
        app.router.add_route('GET', '/shopping/{smemberid}/{slogintoken}/', shopping_handle)
        app.router.add_route('GET', '/getinboxinfo/{smemberid}/{slogintoken}/', getinboxinfo_handle)
        app.router.add_route('GET', '/receiveinbox/{smemberid}/{slogintoken}/', receiveinbox_handle)
        app.router.add_route('GET', '/feedback/{smemberid}/{slogintoken}/', feedback_handle)
        app.router.add_route('GET', '/getgamelist/{smemberid}/{slogintoken}/', getgamelist_handle)
        # app.router.add_route('GET', '/joingame/{smemberid}/{slogintoken}/', joingame_handle)  # 棄用
        app.router.add_route('GET', '/getgamerank/{smemberid}/{slogintoken}/', getgamerank_handle)
        app.router.add_route('GET', '/getleaderrank/{smemberid}/{slogintoken}/', getleaderrank_handle)
        app.router.add_route('GET', '/logout/{smemberid}/{slogintoken}/', logout_handle)
        app.router.add_route('GET', '/getreddot_countdown/{smemberid}/{slogintoken}/', getreddot_countdown_handle)
        app.router.add_route('GET', '/sendchat_public/{smemberid}/{slogintoken}/', sendchat_public_handle)
        app.router.add_route('GET', '/getsettingcontent/{smemberid}/{slogintoken}/', getsettingcontent_handle)
        app.router.add_route('GET', '/getsecretmall/{smemberid}/{slogintoken}/',getsecretmall_handle)
        app.router.add_route('GET', '/senddownloadsignal/{smemberid}/{slogintoken}/', senddownloadsignal_handle)
        app.router.add_route('GET', '/getpiggycredit/{smemberid}/{slogintoken}/', getpiggycredit_handle)
        app.router.add_route('GET', '/getfriendlist/{smemberid}/{slogintoken}/', getfriendlist_handle)
        app.router.add_route('GET', '/getblacklist/{smemberid}/{slogintoken}/', getblacklist_handle)
        app.router.add_route('GET', '/updatefriendlist/{smemberid}/{slogintoken}/', updatefriendlist_handle)
        app.router.add_route('GET', '/updateblacklist/{smemberid}/{slogintoken}/', updateblacklist_handle)
        app.router.add_route('GET', '/safetask/{smemberid}/{slogintoken}/', safetask_handle)
        app.router.add_route('GET', '/serialinput/{smemberid}/{slogintoken}/', serialinput_handle)
        app.router.add_route('GET', '/makelike/{smemberid}/{slogintoken}/', makelike_handle)
        app.router.add_route('GET', '/sendprivatchat/{smemberid}/{slogintoken}/', sendprivatchat_handle)
        app.router.add_route('GET', '/sendphonevalidate/{smemberid}/{slogintoken}/', sendphonevalidate_handle)
        app.router.add_route('GET', '/feedbackvalidatecode/{smemberid}/{slogintoken}/', feedbackvalidatecode_handle)
        app.router.add_route('GET', '/getgiftdata/{smemberid}/{slogintoken}/', getgiftdata_handle)
        app.router.add_route('GET', '/getcardinfo/{smemberid}/{slogintoken}/', getcardinfo_handle)
        app.router.add_route('GET', '/getchannellist/{smemberid}/{slogintoken}/', getchannellist_handle)
        app.router.add_route('GET', '/getchannelmember/{smemberid}/{slogintoken}/', getchannelmember_handle)
        app.router.add_route('GET', '/joinchannel/{smemberid}/{slogintoken}/', joinchannel_handle)
        app.router.add_route('GET', '/receivegift/{smemberid}/{slogintoken}/', receivegift_handle)
        app.router.add_route('GET', '/rejectgift/{smemberid}/{slogintoken}/', rejectgift_handle)
        app.router.add_route('GET', '/sendchannelchat/{smemberid}/{slogintoken}/', sendchannelchat_handle)
        app.router.add_route('GET', '/sendservicechat/{smemberid}/{slogintoken}/', sendservicechat_handle)
        app.router.add_route('GET', '/sendgift/{smemberid}/{slogintoken}/', sendgift_handle)
        app.router.add_route('GET', '/sendgiftsms/{smemberid}/{slogintoken}/', sendgiftsms_handle)
        app.router.add_route('GET', '/creditexchange/{smemberid}/{slogintoken}/', creditexchange_handle)
        app.router.add_route('GET', '/pointtocredit/{smemberid}/{slogintoken}/', pointtocredit_handle)
        app.router.add_route('GET', '/getfreeboxstatus/{smemberid}/{slogintoken}/', getfreeboxstatus_handle)
        app.router.add_route('GET', '/receivefreebox/{smemberid}/{slogintoken}/', receivefreebox_handle)
        app.router.add_route('GET', '/forgetpasssms/{smemberid}/{slogintoken}/', forgetpasssms_handle)
        app.router.add_route('GET', '/changenewpassword/{smemberid}/{slogintoken}/', changenewpassword_handle)
        app.router.add_route('GET', '/bindusername/{smemberid}/{slogintoken}/', bindusername_handle)
        app.router.add_route('GET', '/friendonlinestatus/{smemberid}/{slogintoken}/', friendonlinestatus_handle)
        app.router.add_route('GET', '/updatemembermessage/{smemberid}/{slogintoken}/', updatemembermessage_handle)
        app.router.add_route('GET', '/reportmember/{smemberid}/{slogintoken}/', reportmember_handle)
        app.router.add_route('GET', '/actionframe/{smemberid}/{slogintoken}/', actionframe_handle)
        app.router.add_route('GET', '/restoreIAP/{smemberid}/{slogintoken}/', restoreIAP_handle)
        # app.router.add_route('GET', '/getselfrankgamesort/{smemberid}/{slogintoken}/', getselfrankgamesort_handle)   # 棄用
        app.router.add_route('GET', '/getavatarlist/{smemberid}/{slogintoken}/', getavatarlist_handle)
        app.router.add_route('GET', '/setavatarfromlist/{smemberid}/{slogintoken}/', setavatarfromlist_handle)
        app.router.add_route('GET', '/getseatsinfo/{smemberid}/{slogintoken}/', getseatsinfo_handle)
        app.router.add_route('GET', '/backtohall/{smemberid}/{slogintoken}/', backtohall_handle)
        app.router.add_route('GET', '/joingameseat/{smemberid}/{slogintoken}/', joingameseat_handle)
        app.router.add_route('GET', '/getnewdragontigerrank/{smemberid}/{slogintoken}/', getnewdragontigerrank_handle)
        app.router.add_route('GET', '/getnewtotalrank/{smemberid}/{slogintoken}/', getnewtotalrank_handle)
        app.router.add_route('GET', '/getselfrankgamesortnew/{smemberid}/{slogintoken}/', getselfrankgamesortnew_handle)
        app.router.add_route('GET', '/getmemberinfolessdata/{smemberid}/{slogintoken}/', getmemberinfolessdata_handle)
        app.router.add_route('GET', '/getboxinfo/{smemberid}/{slogintoken}/', getboxinfo_handle)
        app.router.add_route('GET', '/buybox/{smemberid}/{slogintoken}/', buybox_handle)
        app.router.add_route('GET', '/skiptutorial/{smemberid}/{slogintoken}/', skiptutorial_handle)
        app.router.add_route('GET', '/gettutorialguide/{smemberid}/{slogintoken}/', gettutorialguide_handle)
        app.router.add_route('GET', '/joinfishgame/{smemberid}/{slogintoken}/', joinfishgame_handle)

        # 官方使用 api
        app.router.add_route('GET', '/jinsong/servicetouser/', servicetouser_handle)



        # for ps call back gold host
        app.router.add_route('GET', '/api/signin', psapi_signin_handle)
        app.router.add_route('GET', '/api/authenticate', psapi_authenticate_handle)
        app.router.add_route('GET', '/api/logout', psapi_logout_handle)
        app.router.add_route('GET', '/api/bet', psapi_bet_handle)
        app.router.add_route('GET', '/api/result', psapi_result_handle)
        app.router.add_route('GET', '/api/getbalance', psapi_getbalance_handle)

        # for ps call back silver host
        app.router.add_route('GET', '/apis/signin', psapis_signin_handle)
        app.router.add_route('GET', '/apis/authenticate', psapis_authenticate_handle)
        app.router.add_route('GET', '/apis/logout', psapis_logout_handle)
        app.router.add_route('GET', '/apis/bet', psapis_bet_handle)
        app.router.add_route('GET', '/apis/result', psapis_result_handle)
        app.router.add_route('GET', '/apis/getbalance', psapis_getbalance_handle)

        # for ps call back
        app.router.add_route('GET', '/apit/signin', psapit_signin_handle)
        app.router.add_route('GET', '/apit/authenticate', psapit_authenticate_handle)
        app.router.add_route('GET', '/apit/logout', psapit_logout_handle)
        app.router.add_route('GET', '/apit/bet', psapit_bet_handle)
        app.router.add_route('GET', '/apit/result', psapit_result_handle)
        app.router.add_route('GET', '/apit/getbalance', psapit_getbalance_handle)


        # web using api
        app.router.add_route('GET', '/web/api/getserverstatus/', webapi_getserverstatus_handle)
        app.router.add_route('GET', '/web/api/getrichestrank/', webapi_getrichestrank_handle)
        app.router.add_route('GET', '/web/api/loginfb/', webapi_loginfb_handle)
        app.router.add_route('GET', '/web/api/loginbytoken/', webapi_loginbytoken_handle)
        app.router.add_route('GET', '/web/api/logout/', webapi_logout_handle)
        app.router.add_route('GET', '/web/api/loginusername/', webapi_loginusername_handle)
        app.router.add_route('GET', '/web/api/getgashwalletitem/', webapi_getgashwalletitem_handle)
        app.router.add_route('GET', '/web/api/getgashpointitem/', webapi_getgashpointitem_handle)
        app.router.add_route('GET', '/web/api/get_gash_wallet_base64/',webapi_get_gash_wallet_base64_handle)
        app.router.add_route('GET', '/web/api/ret_gash_wallet_base64/', webapi_ret_gash_wallet_base64_handle)
        app.router.add_route('GET', '/web/api/get_gash_point_base64/', webapi_get_gash_point_base64_handle)
        app.router.add_route('GET', '/web/api/ret_gash_point_base64/', webapi_ret_gash_point_base64_handle)
        app.router.add_route('GET', '/web/api/add_comment/', webapi_add_comment_handle)
        app.router.add_route('GET', '/web/api/ecpay_credit_start_purchase/', webapi_ecpay_credit_start_purchase_handle)
        app.router.add_route('GET', '/web/api/ecpay_credit_order_result/', webapi_ecpay_credit_order_result_handle)
        app.router.add_route('GET', '/web/api/serialinput/', webapi_serial_input_handle)

        # 增加MyCard儲值方式
        # 3-1
        app.router.add_route('GET', '/mycard/gashpoints/', mycard_gashpoints_handle)
        # 3-2-4
        app.router.add_route('GET', '/mycard/mcresult/', mycard_mcresult_handle)
        # 3-3
        app.router.add_route('GET', '/mycard/checkMyCardTradeResult/', mycard_checkMyCardTradeResult_handle)
        # 3-4
        app.router.add_route('GET', '/mycard/mycardReturnInvoiceResult/', mycard_mycardReturnInvoiceResult_handle)
        # 3-6
        app.router.add_route('GET', '/mycard/mcredeposit/', mycard_mcredeposit_handle)
        # 3-7
        app.router.add_route('GET', '/mycard/mcresultcheck/single/', mycard_mcresultcheck_single_handle)
        # 3-7
        app.router.add_route('GET', '/mycard/mcresultcheck/multi/', mycard_mcresultcheck_multi_handle)

        # for system debug using
        app.router.add_route('GET', '/healthycheck/', healthycheck_handle)  # return 'check' for healthy check
        app.router.add_route('GET', '/getlobbyserverips/',  getlobbyserverips_handle)  # 拿到 lobby server ip info
        app.router.add_route('GET', '/callpsgamelist/',callpsgamelist_handle) # 拿到 ps game list and write to DB
        app.router.add_route('GET', '/setlobbyip/{sIP}/', setlobbyip_handle)  # 設定 lobby server ip

        # for reload all config
        app.router.add_route('GET', '/reloadallconfig/',reloadallconfig_handle)
        app.router.add_route('GET', '/setdebugmode/', setdebugmode_handle)


        # for test
        app.router.add_route('GET','/testsettle/',testsettle_handle)

        aiohttp.web.run_app(app, host="0.0.0.0", port=port)
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'main all except:{0},e:{1}'.format(sys.exc_info()[0],e))

if __name__ == '__main__':

    port = None
    if len(sys.argv) ==2:
        port = pg_general.converttype(sys.argv[1],int)

    pg_general.loggerinit()
    if port is not None:
        main(port)
    else:
        main()


