import asyncio
import os
import aiohttp.web
import sys
import time
import env_setting
import pg_general
from pg_asqldb import PG_ASQLDB
from pg_slotgame_asqldb import PG_SLOTGAME_ASQLDB
from enum import IntEnum
from pg_fbavatar import PG_FBAVATAR,AVATAR_SYSTEM
from pg_redis import PGRedis
from pg_general import SendMsgType, PASS_REDIS_VALIDATION_CODE
import pg_namesample
import requests

from urllib import parse
from traceback import format_exc
import hashlib
import json
import datetime
import pytz
import string
import random


HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 81))


PREFIX = 'SDAP'
PREFIX_S = 'SDAPS'





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
            clientdata['gameagreement2'] = app['gameagreement2']
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
    linecode = request.rel_url.query.get('linecode')
    linestate = request.rel_url.query.get('linestate')
    lineaccesstoken = request.rel_url.query.get('lineaccesstoken')
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
                                                        ip, platform, devicedescription,lobbyserverip,region,region_sub,city,fcmtoken,ver,rer,username,password,
                                                        newaccflag,connecttype,auserid,aauthcode,atoken,linecode,linestate,lineaccesstoken)
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
                url = env_setting.PS_API_SERVER_URL + 'host/signin/?prefix={0}&member_id={1}&password={2}'.format(PREFIX_S, memberid, logintoken)
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

async def line_login_callback_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'line_login_callback_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        code = request.rel_url.query.get('code')
        state = request.rel_url.query.get('state')
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'line_login_callback_handle code:{0}, state:{1}'.format(code, state))

        if code is not None and state is not None:
            # result, clientdata = await db.linelogincallback(code, state)
            resultdata['code'] = code
            resultdata['state'] = state
            # resultdata['apiresult'] = pg_general.Apiresult.success

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'line_login_callback_handle send:{}'.format(resultdata))
    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'line_login_callback_handle ValueError:{0}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'line_login_callback_handle Except:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def use_agreement_text_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'use_agreement_text_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        result, clientdata = await db.get_use_agreement()
        resultdata['clientdata'] = clientdata
        resultdata['apiresult'] = result

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'use_agreement_text_handle send:{}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'use_agreement_text_handle ValueError:{0}'.format(format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'use_agreement_text_handle Except:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def privacy_agreement_text_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'privacy_agreement_text_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        result, clientdata = await db.get_privacy_agreement()
        resultdata['clientdata'] = clientdata
        resultdata['apiresult'] = result

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'privacy_agreement_text_handle send:{}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'privacy_agreement_text_handle ValueError:{0}'.format(format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'privacy_agreement_text_handle Except:{0}'.format(format_exc()))

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
        result, clientdata = await db.updatememberlogout(memberid, logintoken, redis_obj)
        resultdata['clientdata'] = clientdata
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
    mode = pg_general.converttype(request.rel_url.query.get('mode', 0), int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken, mode)
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
        mode = pg_general.converttype(mode, int)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    jsoncontent = await request.json()

    if jsoncontent is None:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror
    else:
        result, clientdata = await db.shopping(redis_obj, logintoken, memberid, cardinfo, jsoncontent, mode)
        resultdata['apiresult'] = result

        if result == pg_general.Apiresult.success:
            resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.warn,
                        'shopping_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def linegameshopping_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.warn, 'linegameshopping_handle recv:{0}'.format(request.rel_url))
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

        platform = pg_general.converttype(request.rel_url.query.get('platform'), int)
        shopid = pg_general.converttype(request.rel_url.query.get('shopid'), str)
        num = request.rel_url.query.get('num')
        mode = pg_general.converttype(request.rel_url.query.get('mode'), int)
        pay_method = pg_general.converttype(request.rel_url.query.get('paymethod'), str)

        if mode is None:
            mode = 0
        else:
            mode = pg_general.converttype(mode, int)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, platform, shopid, num, mode, pay_method]:
            result, clientdata = await db.linegameshopping(redis_obj, memberid, logintoken, platform, shopid, num, mode, pay_method)
            resultdata['clientdata'] = clientdata
            resultdata['apiresult'] = result
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            'linegameshopping_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'linegameshopping_handle ValueError:{0}'.format(format_exc()))

    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'linegameshopping_handle Exception:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def getroomsharingurl_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.warn, 'getroomsharingurl_handle recv:{0}'.format(request.rel_url))
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

        room_id = pg_general.converttype(request.rel_url.query.get('room_id'), str)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, room_id]:
            result, clientdata = await db.getroomsharingurl(memberid, logintoken, room_id)
            resultdata['clientdata'] = clientdata
            resultdata['apiresult'] = result
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            'getroomsharingurl_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getroomsharingurl_handle ValueError:{0}'.format(format_exc()))

    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'getroomsharingurl_handle Exception:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def sendlinedepositanimation_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.warn, 'sendlinedepositanimation_handle recv:{0}'.format(request.rel_url))
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
            result, clientdata = await db.sendlinedepositanimation(memberid, logintoken)
            resultdata['clientdata'] = clientdata
            resultdata['apiresult'] = result
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            'sendlinedepositanimation_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'sendlinedepositanimation_handle ValueError:{0}'.format(format_exc()))

    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'sendlinedepositanimation_handle Exception:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def playingstatus_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.warn, 'playingstatus_handle recv:{0}'.format(request.rel_url))
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
            result, clientdata = await db.playingstatus(memberid, logintoken)
            resultdata['clientdata'] = clientdata
            resultdata['apiresult'] = result
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            'playingstatus_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'playingstatus_handle ValueError:{0}'.format(format_exc()))

    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'playingstatus_handle Exception:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def getinboxinfo_handle(request):
    try:
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
    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:getinboxinfo_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid,
                                                                                                    logintoken))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:getinboxinfo_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid,
                                                                                                   logintoken))

    return aiohttp.web.json_response(resultdata)


async def receiveinbox_handle(request):
    try:
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
    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:receiveinbox_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid,
                                                                                                    logintoken))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:receiveinbox_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid,
                                                                                                   logintoken))
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
    mode = pg_general.converttype(request.rel_url.query.get('mode'), int)

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
    mode = pg_general.converttype(request.rel_url.query.get('mode'), int)

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
    try:
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
        mode = pg_general.converttype(request.rel_url.query.get('mode'), int)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken, mode)
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

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:updatefriendlist_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc(),memberid,logintoken))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:updatefriendlist_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid,
                                logintoken))
    return aiohttp.web.json_response(resultdata)

async def updateblacklist_handle(request):
    try:
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
        mode = pg_general.converttype(request.rel_url.query.get('mode'), int)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken, mode)
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

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:updateblacklist_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid, logintoken))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:updateblacklist_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid, logintoken))
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
        result, clientdata = await db.webapi_serial_input(logintoken, memberid, serial)
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
        phone = phone.strip().replace('+', '')
        if phone[:2] == '09': # 09 to 8559
            phone = '886' + phone[1:]
        # if phone[:1] == '0': # 0 to 66
        #     phone = '66' + phone[1:]
        # else:
        #     phone = '66' + phone
        # if phone[:1] == '0': # 0 to 855
        #     phone = '855' + phone[1:]
        # else:
        #     phone = '855' + phone
        #phone = '886' + phone


        result, clientdata = await db.sendphonevalidate(logintoken, memberid, phone)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata



    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'sendphonevalidate_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def sendemailvalidate_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendemailvalidate_handle recv:{0}'.format(request.rel_url))
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
        email = pg_general.converttype(request.rel_url.query.get('email'), str)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, email]:
            result, clientdata = await db.sendemailvalidate(logintoken, memberid, email)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendphonevalidate_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendemailvalidate_handle ValueError:{0}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendemailvalidate_handle Except:{0}'.format(format_exc()))

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

async def feedbackemailvalidatecode_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'feedbackemailvalidatecode_handle recv:{0}'.format(request.rel_url))
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

            result, clientdata = await db.feedbackemailvalidatecode(logintoken, memberid, code)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'feedbackvalidatecode_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))



    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'feedbackemailvalidatecode_handle ValueError:{0}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'feedbackemailvalidatecode_handle Exception:{0}'.format(format_exc()))

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

async def getbanplayer_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getbanplayer_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    data = await request.json()
    memberlist = data.get('memberlist')

    result, clientdata = await db.getbanplayer(memberlist)
    resultdata['apiresult'] = result
    resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getbanplayer_handle resultdata:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def banplayer_operate_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'banplayer_operate_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        memberlist = data.get('memberlist')
        account_type = data.get('account_type')

        if None not in [memberlist, account_type]:

            if account_type == 1 or account_type == 3:

                result, clientdata = await db.banplayer_operate(memberlist, account_type)
                resultdata['apiresult'] = result
                resultdata['clientdata'] = clientdata

            else:
                resultdata['apiresult'] = pg_general.Apiresult.parametererror
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'banplayer_operate_handle resultdata:{0}'.format(resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:banplayer_operate_handle ValueError:{0},memberid:{1}'.format(format_exc(), memberid))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:banplayer_operate_handle Exception:{0},memberid:{1}'.format(format_exc(), memberid))

    return aiohttp.web.json_response(resultdata)

async def getcreditcardinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getcreditcardinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    result, clientdata = await db.getcreditcardinfo()
    resultdata['apiresult'] = result
    resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                    'getcreditcardinfo_handle get creditcardinfo:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def newcreditcardinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'newcreditcardinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    data = await request.json()

    itemcode = data.get('itemcode')
    cashamount = data.get('cashamount')
    pointamount = data.get('pointamount')
    currency = data.get('currency')
    productname = data.get('productname')

    if None not in [cashamount, pointamount, currency, productname]:
        result, clientdata = await db.newcreditcardinfo(itemcode, cashamount, pointamount, currency, productname)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'newcreditcardinfo_handle new creditcardinfo:{0}'.format(resultdata))
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    return aiohttp.web.json_response(resultdata)

async def delcreditcardinfo_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'delcreditcardinfo_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    itemcode = pg_general.converttype(request.rel_url.query.get('itemcode'), int)

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'delcreditcardinfo_handle recv:{0}'.format(itemcode))
    if None not in [itemcode]:
        result, clientdata = await db.delcreditcardinfo(itemcode)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'delcreditcardinfo_handle del creditcardinfo:{0}'.format(resultdata))
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

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

async def getclubchannellist_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getclubchannellist_handle recv:{0}'.format(request.rel_url))
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

            result, clientdata = await db.getclubchannellist(logintoken, memberid, redis_obj)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'getclubchannellist_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclubchannellist_handle ValueError:{0}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclubchannellist_handle Exception:{0}'.format(format_exc()))

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

async def getclubchannelmember_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getclubchannelmember_handle recv:{0}'.format(request.rel_url))
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
        clubid = request.rel_url.query.get('clubid')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, clubid]:

            result, clientdata = await db.getclubchannelmember(logintoken, memberid, clubid, redis_obj)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'getclubchannelmember_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclubchannelmember_handle ValueError:{0}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclubchannelmember_handle Exception:{0}'.format(format_exc()))

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

async def joinclubchannel_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'joinclubchannel_handle recv:{0}'.format(request.rel_url))
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
        clubid = request.rel_url.query.get('clubid')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'joinclubchannel_handle memberid:{0}, logintoken:{1}, clubid:{2}, redis_obj:{3}'.format(
                                                                                    memberid, logintoken, clubid, redis_obj))
        if None not in [memberid, logintoken, clubid]:

            result, clientdata = await db.joinclubchannel(logintoken, memberid, clubid, redis_obj)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'joinchannel_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))


    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:joinclubchannel_handle ValueError:{0}'.format(format_exc()))

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:joinclubchannel_handle Exception:{0}'.format(format_exc()))

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

async def sendclubchannelchat_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendclubchannelchat_handle recv:{0}'.format(request.rel_url))
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
        clubid = request.rel_url.query.get('clubid')
        type = request.rel_url.query.get('type')
        content = request.rel_url.query.get('content')

        bubblememberid = request.rel_url.query.get('memberid')
        bubblenickname = ''
        bubbleavatar = ''

        if None not in  [bubblememberid,bubblenickname,bubbleavatar]:
            bubbleinfo = {
                "memberid": bubblememberid,
                "nickname": bubblenickname,
                "avatar": bubbleavatar
            }
        else:
            bubbleinfo = {}

        #確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, clubid, type, content]:
            result, clientdata = await db.sendclubchannelchat(redis_obj, logintoken, memberid, clubid, type, content,
                                                          bubbleinfo)
            if result == pg_general.Apiresult.success and clientdata != {} and clientdata.get('black_chat_content') is None:
                data = clientdata.get('data')
                await send_to_all_lobbyserver(app, {"commandid": 3000028, "data": {"talklist": [data],"channelclub": data.get(
                                                                                       'channelclub')}})

                resultdata['apiresult'] = result
                resultdata['clientdata'] = {'result': 0,
                                            'data': clientdata}
            elif result == pg_general.Apiresult.success and clientdata.get('black_chat_content') == True:
                resultdata['apiresult'] = result
                resultdata['clientdata'] = {"result": 1,
                                            "errormsg": 'content is include black chat content'}
            elif result == pg_general.Apiresult.success and clientdata.get('card_0') == True:
                resultdata['apiresult'] = result
                resultdata['clientdata'] = {"result": 2,
                                            "errormsg": 'the card level is bronze'}
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendclubchannelchat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'sendclubchannelchat_handle ValueError:{0}'.format(format_exc()))

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'sendclubchannelchat_handle ValueError:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def getgameroomchat_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getgameroomchat_handle recv:{0}'.format(request.rel_url))
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
        clubid = request.rel_url.query.get('clubid')
        roomid = request.rel_url.query.get('roomid')

        #確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, roomid]:
            result, clientdata = await db.getgameroomchat(redis_obj, logintoken, memberid, clubid, roomid)
            if result == pg_general.Apiresult.success and clientdata != {}:

                resultdata['apiresult'] = result
                resultdata['clientdata'] = {'result': 0,
                                            'data': clientdata}
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'getgameroomchat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'getgameroomchat_handle ValueError:{0}'.format(format_exc()))

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'getgameroomchat_handle Exception:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def sendgameroomchat_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendgameroomchat_handle recv:{0}'.format(request.rel_url))
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
        clubid = request.rel_url.query.get('clubid')
        roomid = request.rel_url.query.get('roomid')
        content = request.rel_url.query.get('content')

        bubblememberid = request.rel_url.query.get('memberid')
        bubblenickname = ''
        bubbleavatar = ''

        if None not in  [bubblememberid,bubblenickname,bubbleavatar]:
            bubbleinfo = {
                "memberid": bubblememberid,
                "nickname": bubblenickname,
                "avatar": bubbleavatar
            }
        else:
            bubbleinfo = {}

        #確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, roomid, content]:
            result, clientdata = await db.sendgameroomchat(redis_obj, logintoken, memberid, clubid, roomid, content,
                                                          bubbleinfo)
            if result == pg_general.Apiresult.success and clientdata != {} and clientdata.get(
                    'black_chat_content') is None:

                # await send_to_all_lobbyserver(app, {"commandid": 3000031, "data": {"talklist": [data],"chatroom": data.get(
                #                                                                        'chatroom')}})

                resultdata['apiresult'] = result
                resultdata['clientdata'] = {'result': 0,
                                            'data': clientdata}
            elif result == pg_general.Apiresult.success and clientdata.get('black_chat_content') == True:
                resultdata['apiresult'] = result
                resultdata['clientdata'] = {"result": 1,
                                            "errormsg": 'content is include black chat content'}
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendgameroomchat_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'sendgameroomchat_handle ValueError:{0}'.format(format_exc()))

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'sendgameroomchat_handle ValueError:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

# async def webshopping_handle(request):
#     try:
#         pg_general.writelog(pg_general.PG_LogerLevel.debug, 'webshopping_handle recv:{0}'.format(request.rel_url))
#         app = request.app
#         db = app["DB"][0]
#         redis_obj = app['redis']
#
#         resultdata = {
#             'serverdata': {},
#             'clientdata': {},
#             'apiresult': pg_general.Apiresult.connectdberror
#         }
#
#         memberid = request.match_info["smemberid"]
#         logintoken = request.match_info["slogintoken"]
#         cash = pg_general.converttype(request.rel_url.query.get('cash'), int)
#         credit = pg_general.converttype(request.rel_url.query.get('credit'), int)
#         type = request.rel_url.query.get('type')
#
#         # 確認 token 有效 # TODO recover
#         # validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
#         # if validateresult == False:
#         #     return aiohttp.web.HTTPNotFound()
#
#         if None not in [memberid, logintoken, cash, credit, type]:
#             result, clientdata = await db.webshopping(logintoken, memberid, cash, credit, type)
#             if result == pg_general.Apiresult.success:
#
#                 resultdata['apiresult'] = result
#                 resultdata['clientdata'] = clientdata
#         else:
#             resultdata['apiresult'] = pg_general.Apiresult.parametererror
#
#         pg_general.writelog(pg_general.PG_LogerLevel.debug,
#                             'webshopping_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
#
#     except ValueError as e:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                     'webshopping_handle ValueError:{0}'.format(format_exc()))
#
#     except Exception as e:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                     'webshopping_handle Exception:{0}'.format(format_exc()))
#
#     return aiohttp.web.json_response(resultdata)
#
# async def flashpayreturn_handle(requst):
#     try:
#         pg_general.writelog(pg_general.PG_LogerLevel.debug, 'flashpayreturn_handle recv:{0}'.format(request.rel_url))
#         app = request.app
#         db = app["DB"][0]
#         redis_obj = app['redis']
#
#         resultdata = {
#             'serverdata': {},
#             'clientdata': {},
#             'apiresult': pg_general.Apiresult.connectdberror
#         }
#
#         object_id = request.rel_url.query.get('objectId')
#         status = request.rel_url.query.get('status')
#
#         if None not in [objectId, status]:
#             result, clientdata = await db.flashpayreturn(object_id, status)
#             if result == pg_general.Apiresult.success:
#
#                 resultdata['apiresult'] = result
#                 resultdata['clientdata'] = clientdata
#
#         else:
#             resultdata['apiresult'] = pg_general.Apiresult.parametererror
#
#         pg_general.writelog(pg_general.PG_LogerLevel.debug,
#                             'flashpayreturn_handle send:{1}'.format(resultdata))
#
#     except ValueError as e:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                     'flashpayreturn_handle ValueError:{0}'.format(format_exc()))
#
#     except Exception as e:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                     'flashpayreturn_handle Exception:{0}'.format(format_exc()))
#
#     return aiohttp.web.json_response(resultdata)
#
# async def flashpaynotify_handle(requst):
#     try:
#         pg_general.writelog(pg_general.PG_LogerLevel.debug, 'flashpaynotify_handle recv:{0}'.format(request.rel_url))
#         app = request.app
#         db = app["DB"][0]
#         redis_obj = app['redis']
#
#         resultdata = {
#             'serverdata': {},
#             'clientdata': {},
#             'apiresult': pg_general.Apiresult.connectdberror
#         }
#
#         out_trade_no = request.rel_url.query.get('outTradeNo')
#         trade_no = request.rel_url.query.get('tradeNo')
#         trade_status = request.rel_url.query.get('tradeStatus')
#         trade_time = request.rel_url.query.get('tradeTime')
#         payment_amount = request.rel_url.query.get('paymentAmount')
#         cur = request.rel_url.query.get('cur')
#         complete_time = request.rel_url.query.get('completeTime')
#
#         if None not in [out_trade_no, trade_no, trade_status, trade_time, payment_amount, cur]:
#             result, clientdata = await db.flashpaynotify(out_trade_no, trade_no, trade_status, trade_time,
#                                                          payment_amount, cur, complete_time)
#             if result == pg_general.Apiresult.success:
#
#                 resultdata['apiresult'] = result
#                 resultdata['clientdata'] = clientdata
#
#         else:
#             resultdata['apiresult'] = pg_general.Apiresult.parametererror
#
#         pg_general.writelog(pg_general.PG_LogerLevel.debug,
#                             'flashpaynotify_handle send:{1}'.format(resultdata))
#
#     except ValueError as e:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                     'flashpaynotify_handle ValueError:{0}'.format(format_exc()))
#
#     except Exception as e:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                     'flashpaynotify_handle Exception:{0}'.format(format_exc()))
#
#     return aiohttp.web.json_response(resultdata)


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

async def gettransferdata_handle(request): # get tansfergold frame data
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'gettransferdata_handle recv:{0}'.format(request.rel_url))
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

        result, clientdata = await db.gettransferdata(logintoken, memberid)
        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'gettransferdata_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def savetransferdata_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'savetransferdata_handle recv:{0}'.format(request.rel_url))
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

    member_id = pg_general.converttype(request.rel_url.query.get('memberid'), int)
    usdamount = pg_general.converttype(request.rel_url.query.get('usdamount'), int)
    banktype = pg_general.converttype(request.rel_url.query.get('banktype'), str)
    bankacc = pg_general.converttype(request.rel_url.query.get('bankacc'), str)
    bankphone = pg_general.converttype(request.rel_url.query.get('bankphone'), str)

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, member_id, usdamount, banktype,bankacc,bankphone]:
        result, clientdata = await db.savetransferdata(logintoken, memberid, member_id, usdamount,banktype,bankacc,bankphone)
        pg_general.writelog(pg_general.PG_LogerLevel.error, '************************aaa{0}'.format(result))
        pg_general.writelog(pg_general.PG_LogerLevel.error, '************************aaa{0}'.format(pg_general.Apiresult.success))
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'savetransferdata_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def get_club_lobby_info_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_club_lobby_info_handle recv:{0}'.format(request.rel_url))
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

    club_id = request.rel_url.query.get('clubid')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, club_id]:
        result, clientdata = await db.get_club_lobby_info(redis_obj, logintoken,
                                                          memberid, club_id)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'get_club_lobby_info_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def check_club_name_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'check_club_name_handle recv:{0}'.format(request.rel_url))
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

    club_name = request.rel_url.query.get('clubname')

    # 確認 token 有效
    validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
    if validateresult == False:
        return aiohttp.web.HTTPNotFound()

    if None not in [memberid, logintoken, club_name]:
        result, clientdata = await db.check_club_name(logintoken, memberid, club_name)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'check_club_name_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def create_club_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'create_club_handle recv:{0}'.format(request.rel_url))
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

        club_name = request.rel_url.query.get('clubname')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_name]:
            result, clientdata = await db.create_club(logintoken, memberid, club_name, redis_obj)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'create_club_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, 'create_club_handle Exception:{0}'.format(format_exc()))

    return aiohttp.web.json_response(resultdata)

async def apply_club_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'apply_club_handle recv:{0}'.format(request.rel_url))
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

        club_id = request.rel_url.query.get('clubid')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_id]:
            result, clientdata = await db.apply_club(logintoken, memberid, club_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'apply_club_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def get_club_apply_list_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_club_apply_list_handle recv:{0}'.format(request.rel_url))
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

        club_id = request.rel_url.query.get('clubid')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_id]:
            result, clientdata = await db.get_club_apply_list(logintoken, club_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_club_apply_list_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_club_apply_list_handle err:{0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def get_club_member_list_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_club_member_list_handle recv:{0}'.format(request.rel_url))
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

        club_id = request.rel_url.query.get('clubid')
        mode = pg_general.converttype(request.rel_url.query.get('mode'), int)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_id]:
            result, clientdata = await db.get_club_member_list(redis_obj, logintoken, club_id, memberid, mode)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_club_member_list_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def get_club_proxy_list_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_club_proxy_list_handle recv:{0}'.format(request.rel_url))
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

        club_id = request.rel_url.query.get('clubid')
        member_id = pg_general.converttype(request.rel_url.query.get('memberid'), int)
        position = pg_general.converttype(request.rel_url.query.get('position'), int)

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_id, member_id, position]:
            result, clientdata = await db.get_club_proxy_list(redis_obj, logintoken, club_id, member_id, position)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_club_proxy_list_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def verify_club_apply_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'verify_club_apply recv:{0}'.format(request.rel_url))
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

        club_id = request.rel_url.query.get('clubid')
        applicant_id = pg_general.converttype(request.rel_url.query.get('applicantid'), int)
        action = request.rel_url.query.get('action')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        is_correct_action = action in ('accept', 'reject')

        if None not in [memberid, logintoken, club_id, applicant_id, action] and is_correct_action:
            result, clientdata = await db.verify_apply(logintoken, club_id, applicant_id, action, memberid)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'verify_club_apply logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def quit_club_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'quit_club_handle recv:{0}'.format(request.rel_url))
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

        club_id = request.rel_url.query.get('clubid')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_id]:
            result, clientdata = await db.quit_club(logintoken, club_id, memberid, 'quit')

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'quit_club_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def kick_club_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'kick_club_handle recv:{0}'.format(request.rel_url))
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

        club_id = request.rel_url.query.get('clubid')
        kick_member_id = request.rel_url.query.get('kickmemberid')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_id, kick_member_id]:
            result, clientdata = await db.quit_club(logintoken, club_id, kick_member_id, 'kick')

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'kick_club_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def mod_club_proxy_holding_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'mod_club_proxy_holding_handle recv:{0}'.format(request.rel_url))
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

        data = await request.json()

        club_id = data.get('clubid')
        proxyid = pg_general.converttype(data.get('proxyid'), int)
        position = pg_general.converttype(data.get('position'), int)
        holding = data.get('holding')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()


        if None not in [memberid, logintoken, club_id, proxyid, position]:

            result, clientdata = await db.mod_club_proxy_holding(memberid,logintoken, club_id,
                                              proxyid, position,holding)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'mod_club_proxy_holding_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def mod_club_member_win_limit_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'mod_club_member_win_limit_handle recv:{0}'.format(request.rel_url))
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

        data = await request.json()

        club_id = data.get('clubid')
        proxyid = pg_general.converttype(data.get('proxyid'), int)
        limit = data.get('limit')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [memberid, logintoken, club_id, proxyid, limit]:
            result, clientdata = await db.mod_club_member_win_limit(logintoken, club_id,
                                                                 proxyid, limit)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'mod_club_member_win_limit_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)


def _proxy_ratio_check(first_ratio, second_ratio, third_ratio, fourth_ratio,
                       fifth_ratio, sixth_ratio):
    """檢查代理比例格式是否正確

    比例設計為累計，從右往左累計，first_ratio 不可超過 90
    館主累計比例為 100

    Args:
        first_ratio (int): 一級代理累計獎勵比例
        second_ratio (int): 二級代理累計獎勵比例
        third_ratio (int): 三級代理累計獎勵比例
        fourth_ratio (int): 四級代理累計獎勵比例
        fifth_ratio (int): 五級代理累計獎勵比例
        sixth_ratio (int): 六級代理累計獎勵比例
    """
    if first_ratio > 90:
        return False

    ratio_ls = [first_ratio, second_ratio, third_ratio, fourth_ratio, fifth_ratio, sixth_ratio]

    for i in range(1, len(ratio_ls)):
        one = ratio_ls[i-1]
        two = ratio_ls[i]

        if one < two:  # 右邊的數字不可大於左邊的數字
            return False

    return True


def _get_ratio(first_ratio, second_ratio, third_ratio, fourth_ratio,
                       fifth_ratio, sixth_ratio):
    """取得要寫入資料庫的比例

    從 100 開始扣除累計的比例值，計算出每個職位的數值是多少
    館主累計比例為 100

    Returns:
        list: [30, 20, 15, 10, 10, 10, 5] 依序為 館主、一級、二級、三級、四級、五級、六級
    """
    output_ls = []
    ratio_ls = [first_ratio, second_ratio, third_ratio, fourth_ratio,
                fifth_ratio, sixth_ratio]
    total_ratio = 100

    for i in range(6):
        tmp_ratio = total_ratio - ratio_ls[i]
        output_ls.append(tmp_ratio)
        total_ratio = ratio_ls[i]

    output_ls.append(ratio_ls[-1])

    return output_ls

async def update_club_right_setting_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'update_club_right_setting_handle recv:{0}'.format(request.rel_url))
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
        mode = pg_general.converttype(request.rel_url.query.get('mode', 0), int)

        data = await request.json()

        club_id = data.get('clubid')
        first_ratio = data.get('first')
        second_ratio = data.get('second')
        third_ratio = data.get('third')
        fourth_ratio = data.get('fourth')
        fifth_ratio = data.get('fifth')
        sixth_ratio = data.get('sixth')

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken, mode)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        is_not_none = None not in (memberid, logintoken, club_id, first_ratio, second_ratio,
                                   third_ratio, fourth_ratio, fifth_ratio, sixth_ratio)
        is_correct_format = _proxy_ratio_check(first_ratio, second_ratio, third_ratio,
                                                fourth_ratio, fifth_ratio, sixth_ratio)

        if is_not_none and is_correct_format:
            ratio_ls = _get_ratio(first_ratio, second_ratio, third_ratio,
                                                fourth_ratio, fifth_ratio, sixth_ratio)
            result, clientdata = await db.update_club_right_setting(memberid, logintoken,
                                                                    club_id, ratio_ls)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'update_club_right_setting_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def prohibitplayerclub_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'prohibitplayerclub_handle recv:{0}'.format(request.rel_url))
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

        clubid = request.rel_url.query.get('clubid')
        proxyid = pg_general.converttype(request.rel_url.query.get('proxyid'), int)
        banplayergame = pg_general.converttype(request.rel_url.query.get('banplayergame'), int)
        banchat = pg_general.converttype(request.rel_url.query.get('banchat'), int)

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [clubid, banplayergame, banchat]:
            result, clientdata = await db.prohibitplayerclub(memberid, logintoken, clubid, proxyid, banplayergame, banchat)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'prohibitplayerclub_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def transfer_club_credit_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'transfer_club_credit_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        receive_member_id = data.get('receiveid')
        amount = data.get('amount')
        action = data.get('action')

        is_correct_amount = amount > 0

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if (None not in [member_id, logintoken, club_id, receive_member_id, amount, action]
                and is_correct_amount):
            result, clientdata = await db.transfer_club_credit(member_id, logintoken,
                                                         club_id, receive_member_id, amount, action)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'transfer_club_credit_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def remove_proxy_right_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'remove_proxy_right_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        proxy_id = data.get('proxyid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id, proxy_id]:
            result, clientdata = await db.remove_proxy_right(logintoken, club_id, proxy_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'remove_proxy_right_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def retrieve_money_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'retrieve_money_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        target_member_id = data.get('targetmemberid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id, target_member_id]:
            result, clientdata = await db.retrieve_money(member_id, target_member_id,
                                                         logintoken, club_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'retrieve_money_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'retrieve_money_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'retrieve_money_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def get_money_detail_handle(request):
    '''金幣明細'''
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_money_detail_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        start_datetime = data.get('startdatetime')
        end_datetime = data.get('enddatetime')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()
        start_datetime_check = pg_general.converttype(start_datetime, str) is not None
        end_datetime_check = pg_general.converttype(end_datetime, str) is not None

        if (None not in [member_id, logintoken, club_id] and start_datetime_check
            and end_datetime_check):
            result, clientdata = await db.get_money_detail(logintoken, club_id, start_datetime, end_datetime)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_money_detail_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_money_detail_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_money_detail_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def save_club_info_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'save_club_info_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        introduction = data.get('introduction')
        post_msg = data.get('postmsg')
        apply_mode = pg_general.converttype(data.get('applymode'), int)
        line = data.get('line')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if (None not in [member_id, logintoken, club_id, introduction, post_msg, apply_mode,
                         line]):
            result, clientdata = await db.save_club_info(logintoken, club_id,
                                                     introduction, post_msg, apply_mode, line)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'save_club_info_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'save_club_info_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'save_club_info_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def close_club_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'close_club_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id]:
            result, clientdata = await db.close_club(logintoken, club_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'close_club_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'close_club_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'close_club_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def set_club_room_password_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'set_club_room_password_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        password = data.get('password')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id, password]:
            result, clientdata = await db.set_club_room_password(logintoken, club_id, password)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'set_club_room_password_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'set_club_room_password_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'set_club_room_password_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def add_club_room_setting_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'add_club_room_setting_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        game_id = data.get('gameid')
        setting_name = data.get('settingname')
        bet = pg_general.converttype(data.get('bet'), int)
        outtax = pg_general.converttype(data.get('outtax'), int)
        same_ip = pg_general.converttype(data.get('sameip'), int)
        similar = pg_general.converttype(data.get('similar'), int)
        player = pg_general.converttype(data.get('player'), int)
        thinktime = pg_general.converttype(data.get('thinktime'), int)
        rounds = pg_general.converttype(data.get('rounds'), int)
        walletrange = data.get('walletrange')
        setting = data.get('setting')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        is_not_none = None not in (member_id, logintoken, club_id, game_id, setting_name,
                           bet, outtax, same_ip, similar, player, thinktime, rounds,
                           walletrange, setting)
        if is_not_none:
            result, clientdata = await db.add_club_room_setting(logintoken, club_id,
                                game_id, setting_name, bet, outtax, same_ip, similar,
                                player, thinktime, rounds, walletrange, setting)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'add_club_room_setting_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'add_club_room_setting_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'add_club_room_setting_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def mod_club_room_setting_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'mod_club_room_setting_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        setting_id = data.get('id')
        bet = pg_general.converttype(data.get('bet'), int)
        outtax = pg_general.converttype(data.get('outtax'), int)
        same_ip = pg_general.converttype(data.get('sameip'), int)
        similar = pg_general.converttype(data.get('similar'), int)
        player = pg_general.converttype(data.get('player'), int)
        thinktime = pg_general.converttype(data.get('thinktime'), int)
        rounds = pg_general.converttype(data.get('rounds'), int)
        walletrange = data.get('walletrange')
        setting = data.get('setting')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        is_not_none = None not in (member_id, logintoken, club_id, setting_id,
                           bet, outtax, same_ip, similar, player, thinktime, rounds,
                           walletrange, setting)
        if is_not_none:
            result, clientdata = await db.mod_club_room_setting(logintoken, club_id,
                                setting_id, bet, outtax, same_ip, similar,
                                player, thinktime, rounds, walletrange, setting)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'mod_club_room_setting_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'mod_club_room_setting_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'mod_club_room_setting_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def delete_club_room_setting_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'delete_club_room_setting_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        setting_id = data.get('id')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in (member_id, logintoken, club_id, setting_id):
            result, clientdata = await db.delete_club_room_setting(logintoken, club_id,
                                                                    setting_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'delete_club_room_setting_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'mod_club_room_setting_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'mod_club_room_setting_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def get_game_record_handle(request):
    '''遊戲紀錄'''
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_game_record_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        game_id = data.get('gameid')
        start_datetime = data.get('startdatetime')
        end_datetime = data.get('enddatetime')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()
        start_datetime_check = pg_general.converttype(start_datetime, str) is not None
        end_datetime_check = pg_general.converttype(end_datetime, str) is not None

        if (None not in [member_id, logintoken, club_id] and start_datetime_check
            and end_datetime_check):
            result, clientdata = await db.get_game_record(logintoken, club_id, game_id,
                                                         start_datetime, end_datetime)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_game_record_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_game_record_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_game_record_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def get_self_record_handle(request):
    '''我的戰績'''
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_self_record_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        room_id = data.get('roomid')
        game_id = data.get('gameid')
        start_datetime = data.get('startdatetime')
        end_datetime = data.get('enddatetime')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()
        start_datetime_check = pg_general.converttype(start_datetime, str) is not None
        end_datetime_check = pg_general.converttype(end_datetime, str) is not None

        if (None not in [member_id, logintoken, club_id] and start_datetime_check
            and end_datetime_check):
            result, clientdata = await db.get_self_record(logintoken, member_id, club_id, game_id, start_datetime, end_datetime, room_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_self_record_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_self_record_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_self_record_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def get_member_record_handle(request):
    '''會員戰績'''
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_member_record_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        room_id = data.get('roomid')
        game_id = data.get('gameid')
        search = data.get('search')
        start_datetime = data.get('startdatetime')
        end_datetime = data.get('enddatetime')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()
        start_datetime_check = pg_general.converttype(start_datetime, str) is not None
        end_datetime_check = pg_general.converttype(end_datetime, str) is not None

        if (None not in [member_id, logintoken, club_id] and start_datetime_check
            and end_datetime_check):
            result, clientdata = await db.get_member_record(logintoken, club_id, game_id, start_datetime, end_datetime, room_id, search)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_member_record_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_member_record_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_member_record_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def get_performance_handle(request):
    '''績效'''
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_performance_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        search = data.get('search')
        start_datetime = data.get('startdatetime')
        end_datetime = data.get('enddatetime')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()
        start_datetime_check = pg_general.converttype(start_datetime, str) is not None
        end_datetime_check = pg_general.converttype(end_datetime, str) is not None
        
        if (None not in [member_id, logintoken, club_id] and start_datetime_check
            and end_datetime_check):
            result, clientdata = await db.get_performance(logintoken, club_id, start_datetime, end_datetime, search)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_performance_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_performance_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_performance_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def get_member_money_detail_handle(request):
    '''個人金幣明細'''
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_member_money_detail_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        start_datetime = data.get('startdatetime')
        end_datetime = data.get('enddatetime')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()
        start_datetime_check = pg_general.converttype(start_datetime, str) is not None
        end_datetime_check = pg_general.converttype(end_datetime, str) is not None

        if (None not in [member_id, logintoken, club_id] and start_datetime_check
            and end_datetime_check):
            result, clientdata = await db.get_member_money_detail(logintoken, member_id, club_id, start_datetime, end_datetime)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_member_money_detail_handle resultdata:{0}'.format(resultdata))
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_member_money_detail_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_member_money_detail_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def create_room_handle(request):
    """建立一般房間 or 俱樂部房間"""
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'create_room_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        game_id = data.get('gameid')
        club_id = data.get('clubid')
        amount = data.get('amount')
        rounds = data.get('rounds')
        game_setting = data.get('setting')
        password_room = data.get('passwordroom')
        club_room_setting_id = data.get('clubroomsettingid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, game_setting, amount, rounds]:
            result, clientdata = await db.create_room(member_id, logintoken, redis_obj, club_id,
                                                      game_id, game_setting, amount, rounds,
                                                      password_room, club_room_setting_id)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'create_room_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def find_join_room_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'find_join_room_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        club_id = request.rel_url.query.get('clubid')
        club_room_setting_id = request.rel_url.query.get('clubroomsettingid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken]:
            result, clientdata = await db.find_join_room(logintoken, member_id, club_id,
                                                         redis_obj, club_room_setting_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'find_join_room_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def join_room_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'join_room_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        room_id = data.get('roomid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, room_id]:
            result, clientdata = await db.join_room(member_id, logintoken, redis_obj,
                                                         club_id, room_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'join_room_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'join_room_handle ValueError: {0}'.format(
                                format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'join_room_handle Exception: {0}'.format(
                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def room_ready_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'room_ready_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        room_id = data.get('roomid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id, room_id]:
            result, clientdata = await db.room_ready(member_id, logintoken, redis_obj,
                                                         club_id, room_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'room_ready_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def leave_room_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'leave_room_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        room_id = data.get('roomid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id, room_id]:
            result, clientdata = await db.leave_room(member_id, logintoken, redis_obj,
                                                         club_id, room_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'leave_room_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def kick_room_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'kick_room_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        room_id = data.get('roomid')
        target_member_id = data.get('targetmemberid')
        target_logintoken = data.get('targetlogintoken')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id, room_id, target_member_id, target_logintoken]:
            result, clientdata = await db.leave_room(target_member_id, target_logintoken, redis_obj,
                                                         club_id, room_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'kick_room_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def dismiss_room_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'dismiss_room_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()

        room_key = data.get('room_key')
        already_play_round = data.get('already_play_round')

        result, clientdata = await db.dismiss_room(redis_obj, room_key, already_play_round)

        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'dismiss_room_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def room_start_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'room_start_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        data = await request.json()

        club_id = data.get('clubid')
        room_id = data.get('roomid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken, club_id, room_id]:
            result, clientdata = await db.room_start(member_id, logintoken, redis_obj,
                                                         club_id, room_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'room_start_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def get_game_room_setting_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_game_room_setting_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken]:
            result, clientdata = await db.get_game_room_setting(logintoken)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_game_room_setting_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e

    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def get_room_card_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_room_card_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        club_id = request.rel_url.query.get('clubid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken]:
            result, clientdata = await db.get_room_card(logintoken, member_id, club_id)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_room_card_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def get_room_info_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_room_info_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = pg_general.converttype(request.match_info["smemberid"], int)
        logintoken = request.match_info["slogintoken"]

        club_id = request.rel_url.query.get('clubid')

        # 確認token有效
        validateresult = await redis_obj.validatelogintoken(member_id, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None not in [member_id, logintoken]:
            result, clientdata = await db.get_room_info(logintoken, member_id, club_id, redis_obj)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'get_room_info_handle resultdata:{0}'.format(resultdata))
    except ValueError as e:
        resultdata['error'] = e
    except Exception as e:
        resultdata['error'] = e

    return aiohttp.web.json_response(resultdata)

async def prohibitplayerall_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'prohibitplayerall_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']
        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()

        banplayerall = pg_general.converttype(data.get('banplayerall'),int)
        memberlist = data.get('memberlist')

        if None not in [banplayerall]:
            result, clientdata = await db.prohibitplayerall(banplayerall, memberlist)

            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'prohibitplayerall_handle resultdata:{0}'.format(resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:prohibitplayerall_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid, logintoken))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:prohibitplayerall_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc(), memberid, logintoken))

    return aiohttp.web.json_response(resultdata)

async def getprohibitplayer_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getprohibitplayer_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        memberlist = data.get('memberlist')
        clubid = data.get('clubid')

        if memberlist is not None:
            result, clientdata = await db.getprohibitplayer(memberlist, clubid)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'getprohibitplayer_handle resultdata:{0}'.format(resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getprohibitplayer_handle ValueError:{0}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getprohibitplayer_handle Exception:{0}'.format(format_exc()))

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

async def sendgiftemailsms_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'sendgiftemailsms_handle recv:{0}'.format(request.rel_url))
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
            result, clientdata = await db.sendgiftemailsms(logintoken, memberid)
            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = result
                resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendgiftemailsms_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendgiftemailsms_handle ValueError except:{0}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'sendgiftemailsms_handle Except except:{0}'.format(format_exc()))

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

async def silvertogoldswitch_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'silvertogoldswitch_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    redis_obj = app['redis']
    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    silvertogoldenable = pg_general.converttype(request.rel_url.query.get('silvertogoldenable'), int)

    if None not in [silvertogoldenable]:
        result, clientdata = await db.silvertogoldswitch(silvertogoldenable)
        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result
    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'silvertogoldswitch_handle send:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def modexchangerateandswitch_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'modexchangerateandswitch_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        rate = pg_general.converttype(data.get('rate'), int)
        silvertogoldenable = pg_general.converttype(data.get('silvertogoldenable'), int)

        if None not in [rate, silvertogoldenable] and rate > 0:
            result, clientdata = await db.modexchangerateandswitch(rate, silvertogoldenable)
            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = result
                resultdata['clientdata'] = clientdata
            else:
                resultdata['apiresult'] = result
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modexchangerateandswitch_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modexchangerateandswitch_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'modexchangerate_handle send:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def getexchangerate_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getexchangerate_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]
        redis_obj = app['redis']

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        result, clientdata = await db.getexchangerate()

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modexchangerate_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modexchangerate_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getexchangerate_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def membersearch_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'membersearch_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        club_type = pg_general.converttype(request.rel_url.query.get('clubtype'), int)
        club = request.rel_url.query.get('club') # 根據 clubtype 可能為 id or name
        member_id = request.rel_url.query.get('memberid')
        username = request.rel_url.query.get('account')
        nickname = request.rel_url.query.get('nickname')
        position = request.rel_url.query.get('position')
        uuid = request.rel_url.query.get('uuid')

        result, clientdata = await db.membersearch(club_type, club, member_id,
                                                   username, nickname, position, uuid)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:membersearch_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:membersearch_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    if club_type != 0: # = 0 撈的資料可能會太多，就不顯示 LOG 了
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'membersearch_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def modmember_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'modmember_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()

        member_id = data.get('memberid')
        phone = data.get('phone')
        email = data.get('email')
        card = data.get('card')
        level = data.get('level')
        club_id = pg_general.converttype(data.get('clubid'), str)
        position = pg_general.converttype(data.get('position'), int)
        proxy = pg_general.converttype(data.get('proxy'), int)
        mode = data.get('mode', 0)

        # 在 mode = 1 時檢查是否有帶欄位值
        mode_check = mode == 0 or (mode == 1 and None not in (club_id, position, proxy))

        if None not in (member_id, phone, email, card, level) and mode_check:
            result, clientdata = await db.modmember(member_id, phone, email, card, level,
                                                    club_id, position, proxy, mode)
        else:
            result = pg_general.Apiresult.parametererror

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modmember_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modmember_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'modmember_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def modclubmemberholding_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'modclubmemberholding_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()

        member_id = data.get('memberid')
        club_id = data.get('clubid')
        holding = data.get('holding')

        result, clientdata = await db.update_club_member_holding(member_id, club_id, holding)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modclubmemberholding_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:modclubmemberholding_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'modclubmemberholding_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def getclublist_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getclublist_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        result, clientdata = await db.get_club_list()

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclublist_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclublist_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getclublist_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def getclubpositionproxylist_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'getclubpositionproxylist_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }
        result = pg_general.Apiresult.parametererror

        club_id = request.rel_url.query.get('clubid')
        position = pg_general.converttype(request.rel_url.query.get('position'), int)

        if None not in (club_id, position):
            result, clientdata = await db.get_club_position_proxy_list(club_id, position)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclubpositionproxylist_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:getclubpositionproxylist_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'getclubpositionproxylist_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def setcreateclubverify_handle(request):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'setcreateclubverify_handle recv:{0}'.format(request.rel_url))
        app = request.app
        db = app["DB"][0]

        resultdata = {
            'serverdata': {},
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }
        result = pg_general.Apiresult.parametererror

        data = await request.json()
        member_id = data.get('memberid')
        right = pg_general.converttype(data.get('right'), int)

        if None not in (member_id, right):
            result, clientdata = await db.set_create_club_verify(member_id, right)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = result

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:setcreateclubverify_handle ValueError:{0},memberid:{1},logintoken:{2}'.format(format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                    'pg_asqldb:setcreateclubverify_handle Exception:{0},memberid:{1},logintoken:{2}'.format(format_exc()))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'setcreateclubverify_handle send:{0}'.format(resultdata))

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
        gametype = pg_general.converttype(request.rel_url.query.get('gametype'), int)
        seatnum = pg_general.converttype(request.rel_url.query.get('seatnum'), int)

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

async def joincardgame_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'joincardgame_handle recv:{0}'.format(request.rel_url))
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
        hallid = pg_general.converttype(request.rel_url.query.get('hallid'), int)

        jsoncontent ={
            'gameid': gameid,
            'hallid': hallid
        }

        # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if None in [gameid, hallid]:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            return aiohttp.web.json_response(resultdata)

        result, clientdata = await db.joincardgame(logintoken, memberid,
                                                   jsoncontent)

        if result == pg_general.Apiresult.success:
            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'joincardgame_handle logintoken:{0}, error:{1}'.format(logintoken, e))

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'joincardgame_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))
    return aiohttp.web.json_response(resultdata)

async def modfirstlogin_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'modfirstlogin_handle recv:{0}'.format(request.rel_url))
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

        # # 確認 token 有效
        validateresult = await redis_obj.validatelogintoken(memberid, logintoken)
        if validateresult == False:
            return aiohttp.web.HTTPNotFound()

        if memberid is not None and logintoken is not None:
            result, clientdata = await db.modfirstlogin(logintoken, memberid)
            resultdata['apiresult'] = result
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'modfirstlogin_handle logintoken:{0}, send:{1}'.format(logintoken, resultdata))

    except ValueError as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:modfirstlogin_handle ValueError:{0}'.format(format_exc()))

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:modfirstlogin_handle Exception:{0}'.format(format_exc()))
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

async def member_item_operate_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'member_item_operate_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    data = await request.json()

    operate = data.get('operate')
    item = data.get('item')
    amount = data.get('amount')
    member_ls = data.get('member_list')
    club_id = data.get('club_id')

    can_operate = operate in ('send', 'withdraw')
    # 在有俱樂部 ID 的情況下，只能操作金幣
    is_correct_item = item == 'gold' if club_id else item in ('silver', 'roomcard')
    is_club_id = club_id != None
    is_correct_amount = isinstance(amount, int) and amount > 0
    is_correct_list = isinstance(member_ls, list)

    if can_operate and is_correct_item and is_correct_amount and is_correct_list and is_club_id:
        if item == 'gold':
            item_column_in_table = 'credit'
        elif item == 'silver':
            item_column_in_table = 'silvercredit'
        else:
            item_column_in_table = item

        result, clientdata = await db.member_item_operate(operate, item_column_in_table,
                                                          amount, member_ls, club_id)

        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'member_item_operate_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def add_action_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'add_action_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    data = await request.json()

    action_number = data.get('actionnumber')
    list_type = data.get('listtype')
    list_pos = data.get('listpos')
    list_name = data.get('listname')
    button_url = data.get('buttonurl', '')
    content_pos = data.get('contentpos')
    content_type = data.get('contenttype')
    content = data.get('content', '')
    click_url = data.get('clickurl', '')
    size = data.get('size')
    start_time = data.get('starttime')
    end_time = data.get('endtime')

    is_correct_action_number = isinstance(action_number, int)
    is_correct_list_type = isinstance(list_type, int)
    is_correct_list_pos = isinstance(list_pos, int)
    is_correct_list_name = isinstance(list_name, str) and list_name != ''
    is_correct_content_pos = isinstance(content_pos, int)
    is_correct_content_type = isinstance(content_type, int)
    is_correct_size = isinstance(size, str)
    is_correct_start_time = isinstance(start_time, str)
    is_correct_end_time = isinstance(end_time, str)

    if (is_correct_action_number and is_correct_list_type and is_correct_list_pos and
        is_correct_list_name and is_correct_content_pos and is_correct_content_type
        and is_correct_size and is_correct_start_time and is_correct_end_time):
        start_time = pg_general.strtodatetime_nof(start_time)
        end_time = pg_general.strtodatetime_nof(end_time)

        result, clientdata = await db.add_action(action_number, list_type, list_pos,
                                                     list_name, button_url, content_pos,
                                                     content_type, content, click_url, size,
                                                     start_time, end_time)

        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'add_action_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def get_action_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'get_action_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    result, clientdata = await db.get_action()

    resultdata['apiresult'] = result
    resultdata['clientdata'] = clientdata

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'get_action_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def delete_action_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'delete_action_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    data = await request.json()
    action_index = data.get('actionindex')

    if isinstance(action_index, int):
        result, clientdata = await db.delete_action(action_index)

        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'delete_action_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def send_inbox_to_member_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'send_inbox_to_member_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    data = await request.json()

    title = data.get('title')
    content = data.get('content')
    uri = data.get('uri')
    promotion_id = data.get('promotionid')
    amount = data.get('amount')
    dateline = data.get('dateline')
    mode = data.get('mode')
    sending_ls = data.get('list')

    is_not_none_value = None not in (title, content, uri, promotion_id, amount, dateline, sending_ls, mode)
    # 分別代表（銀幣、房卡、一般郵件）
    is_correct_promotion_id = promotion_id in ('67', '71', '6')
    is_correct_amount = isinstance(amount, int) and amount >= 0
    is_correct_dateline = isinstance(dateline, str)
    is_correct_sending_ls = isinstance(sending_ls, list)

    if (is_not_none_value and is_correct_promotion_id and is_correct_amount and
            is_correct_dateline and is_correct_sending_ls):

        main_type = '6' if promotion_id == '6' else '0'
        amount = 0 if main_type == '6' else amount # 避免一般信件有獎勵
        dateline = pg_general.strtodatetime_nof(dateline)

        result, clientdata = await db.send_inbox_to_member(title, content, uri, promotion_id,
                                                           amount, main_type, dateline, sending_ls, mode)

        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'send_inbox_to_member_handle send:{0}'.format(resultdata))

    return aiohttp.web.json_response(resultdata)

async def search_inbox_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'search_inbox_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    resultdata = {
        'serverdata': {},
        'clientdata': {},
        'apiresult': pg_general.Apiresult.connectdberror
    }

    data = await request.json()

    start_datetime = data.get('start_datetime')
    end_datetime = data.get('end_datetime')
    club_type = pg_general.converttype(data.get('clubtype'), int)
    club = data.get('club')
    member_id = pg_general.converttype(data.get('memberid'), int)

    is_not_none_value = None not in (start_datetime, end_datetime, club_type, club)
    is_correct_dateline = isinstance(start_datetime, str) and isinstance(end_datetime, str)

    if is_not_none_value and is_correct_dateline:
        result, clientdata = await db.search_inbox(start_datetime, end_datetime,
                                                   club_type, club, member_id)

        resultdata['apiresult'] = result
        resultdata['clientdata'] = clientdata

    else:
        resultdata['apiresult'] = pg_general.Apiresult.parametererror

    if club_type != 0:  # = 0 撈的資料可能會太多，就不顯示 LOG 了
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                        'search_inbox_handle send:{0}'.format(resultdata))

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
            'access_token': seatlogintoken,  # use password to pass logintoken,
            'status_code': status_code,
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
        'access_token': ''  # use password to pass access_token,
    }

    try:
        member_id = request.rel_url.query.get("member_id")
        access_token = request.rel_url.query.get("password")  # password is access_token

        # 就有的程式碼，應該用不到了 2022.07.14 seatlogintoken = access_token
        # 確認 memberid and logintoken 是否正確
        # if member_id[:4] == 'ssea':  # new mode
        #     # find real memberid
        #     templist = member_id.split('_')
        #     gameid = templist[1]
        #     seatnum = pg_general.converttype(templist[2], int)
        #
        #
        #     # get real memberid
        #     member_id = await redis_obj.hget('silverseats_{}@{}'.format(gameid, seatnum), 'memberid')
        #     # get real logintoken
        #     logintoken = seatlogintoken.split('*****')[1]

        member_id = pg_general.converttype(member_id, int)

        result = await db.psapis_signin(access_token, member_id)
        status_code = 0 if result == pg_general.Apiresult.success else -1

        resultdata = {
            'status_code': status_code,
            'access_token': access_token
        }

    except Exception:
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
    # 舊的程式碼，應該用不到了 2022.07.14
    # if access_token[:4] == 'ssea' and '*****' in access_token: # new mode
    #     logintoken = access_token.split('*****')[1]
    # elif access_token[:4] == 'fish' and '*****' in access_token:
    #     logintoken = access_token.split('*****')[1]
    if '(*--)' in access_token:
        access_token = access_token.split('(*--)')[0]
    else:
        access_token = access_token

    step = request.rel_url.query.get("step")

    resultdata = {
        'status_code': 1,
        'member_id': "0",
        'balance': 0
    }

    result , clientdata = await db.psapis_authenticate(access_token)
    if result == pg_general.Apiresult.success:
        resultdata = {
            "status_code": 0,
            "balance": pg_general.converttype(clientdata.get("silvercredit"),int),
            "account_type": pg_general.converttype(clientdata.get('account_type'), int)
        }
        # 舊的程式碼，應該用不到了 2022.07.14
        # if access_token[:4] == 'ssea' and '*****' in access_token:  # new mode
        #     resultdata["member_id"] =  access_token.split('*****')[0]
        # elif access_token[:4] == 'fish' and '*****' in access_token:
        #     resultdata["member_id"] = 'fish_{}'.format(clientdata.get('memberid'))
        #     resultdata["member_name"] = clientdata.get('nickname')

        resultdata["member_id"] = pg_general.converttype(clientdata.get("memberid"), str)
        resultdata["nickname"] = pg_general.converttype(clientdata.get("nickname"), str)

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

    access_token = request.rel_url.query.get("access_token")
    game_id = request.rel_url.query.get("game_id")

    # 舊有的程式碼，應該不會用到了 2022.07.13
    # if logintoken[:4] == 'ssea' and '*****' in logintoken: # new mode
    #     logintoken = logintoken.split('*****')[1]
    #     seatinfo = logintoken.split('*****')[0]

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
    access_token = pg_general.converttype(request.rel_url.query.get("access_token"), str)
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

    # 舊有的程式碼，應該是用不到了 2022.07.13
    # if logintoken[:4] == 'ssea' and '*****' in logintoken:  # new mode
    #     logintoken = logintoken.split('*****')[1]


    # 先抓 判斷是否可以 bet , 如果可以的話  resut = success , clientdata 會有它的 memberid , after credit
    # 如果找不到此玩家, result = dbnodata , 如果credit 不夠 , 回 othererror
    result, clientdata = await db.psapis_bet(redis_obj, access_token, betdata)

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

    access_token = pg_general.converttype(request.rel_url.query.get("access_token"),str)
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
    # 舊有的程式碼，應該不會用到了 2022.07.13
    # if logintoken[:4] ==  'ssea' and '*****' in logintoken: # new mode
    #     seat_data = logintoken.split('*****')[0]
    #     logintoken = logintoken.split('*****')[1]


    result , clientdata = await db.psapis_result(redis_obj, access_token, apiresultdata)
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
            "token": access_token,
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

    access_token = pg_general.converttype(request.rel_url.query.get("access_token"), str)

    # 舊有的程式碼，應該用不到了 2022.07.13
    # if logintoken[:4] == 'ssea' and '*****' in logintoken: # new mode
    #     logintoken = logintoken.split('*****')[1]

    result, clientdata = await db.psapis_getbalance(access_token)
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

async def psapis_refund_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_refund_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    access_token = pg_general.converttype(request.rel_url.query.get("access_token"), str)
    txn_id = pg_general.converttype(request.rel_url.query.get("txn_id"), int)
    # 舊的程式碼，應該用不到了 2022.07.13
    # if logintoken[:4] == 'ssea' and '*****' in logintoken: # new mode
    #     logintoken = logintoken.split('*****')[1]

    result, clientdata = await db.psapis_refund(access_token, txn_id)
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

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'psapis_refund_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def dummy_login_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'dummy_login_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    result = pg_general.Apiresult.parametererror

    data = await request.json()

    host_api_key = data.get("host_api_key")
    access_token = data.get("access_token")

    if None not in (host_api_key, access_token):
        result, clientdata = await db.dummy_login(access_token)

    if result == pg_general.Apiresult.success:
        resultdata = {
            'status_code': clientdata.get('status_code'),
            'member_id': clientdata.get('member_id'),
            'member_name': clientdata.get('member_name'),
            'balance': clientdata.get('balance'),
        }
    else:
        resultdata = {
            'status_code': 1,
            'member_id': "",
            'member_name': "",
            'balance': 0,
        }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'dummy_login_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def dummy_logout_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'dummy_logout_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]
    status_code = 1

    data = await request.json()

    host_api_key = data.get("host_api_key")
    access_token = data.get("access_token")

    if None not in (host_api_key, access_token):
        status_code = 0

    resultdata = {
        'status_code': status_code
    }

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'dummy_logout_handle response:{0}'.format(resultdata))
    return aiohttp.web.json_response(resultdata)

async def set_game_status_handle(request):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'set_game_status_handle recv:{0}'.format(request.rel_url))
    app = request.app
    db = app["DB"][0]

    data = await request.json()

    member_id = data.get('member_id')
    game_id = data.get('game_id')

    if None not in (member_id, game_id):
        result, clientdata = await db.set_game_status(member_id, game_id)

    resultdata = {}

    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'set_game_status_handle response:{0}'.format(resultdata))
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
    slot_game_db = PG_SLOTGAME_ASQLDB()

    await db.createpool()
    await slot_game_db.createpool()

    db.set_slot_game_db(slot_game_db)
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
        app['gameagreement2'] = data.get('gameagreement2')
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
        elif commandid == 3000028:
            if env_setting.LOCAL_SERVER == False:
                realurl = 'http://' + item + "/broadcasttoall"
            else:
                realurl = 'http://127.0.0.1/broadcasttoall'
            sendmsg = {"type": SendMsgType.server_to_clubchannel,
                       "msg": sendmsg
                       }

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

async def line_deposit_log_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        # memberid = pg_general.converttype(request.match_info["smemberid"], int)
        # logintoken = request.match_info["slogintoken"]

        data = await request.json()
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'line_deposit_log_handle data:{0}'.format(data))

        order_num = data.get('order_id')
        product_name = data.get('product_name')
        line_sub = data.get('line_uid')
        trade_time = data.get('trade_time')
        cash = pg_general.converttype(data.get('amount'), int)
        amount = pg_general.converttype(data.get('product_number'), int)
        mode = pg_general.converttype(data.get('product_mode'), int)
        status = pg_general.converttype(data.get('status'), int)
        method = data.get('method')

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'line_deposit_log_handle order_num:{0}, product_name:{1}, line_sub:{2}, trade_time:{3}, cash:{4}, amount:{5}, mode:{6}, status:{7}, method:{8} '.format(
                                order_num, product_name, line_sub, trade_time, cash, amount, mode, status, method))

        if None not in [order_num, product_name, line_sub, trade_time, cash, amount, mode, status, method]:
            result, clientdata = await db.line_deposit_log(order_num, product_name, line_sub, trade_time, cash, amount,
                                                                  mode, status, method)

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'line_deposit_log_handle clientdata:{0}'.format(clientdata))

            resultdata['apiresult'] = pg_general.Apiresult.success
            resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'line_deposit_log_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'line_deposit_log_handle Exception: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def bindlineprofile_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        # memberid = pg_general.converttype(request.match_info["smemberid"], int)
        # logintoken = request.match_info["slogintoken"]
        # access_token = request.rel_url.query.get('access_token')

        data = await request.json()
        sub = data.get('sub')
        name = data.get('name')
        picture = data.get('picture')
        email = data.get('email')

        if None not in [sub, name]:
            result, clientdata = await db.bind_line_proflie(sub, name, picture, email)

            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = pg_general.Apiresult.success
                resultdata['clientdata'] = clientdata

            elif result ==pg_general.Apiresult.connectdberror:
                resultdata['apiresult'] = pg_general.Apiresult.connectdberror
                resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            resultdata['clientdata'] = clientdata

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'bindlineprofile_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'bindlineprofile_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def updatepopulargame_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        game_name = data.get('game_name')

        if None not in [game_name]:
            result, clientdata = await db.updatepopulargame(game_name)

            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = pg_general.Apiresult.success
                resultdata['clientdata'] = clientdata

            else:
                resultdata['apiresult'] = pg_general.Apiresult.connectdberror
                resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            resultdata['clientdata'] = clientdata

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'updatepopulargame_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'updatepopulargame_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def populargame_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        redis_obj = app['redis']
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        ip = data.get("ip")
        sub = data.get('sub')
        name = data.get('name')
        picture = data.get('picture')
        email = data.get('email')

        if None not in [ip, sub, name]:
            result, clientdata = await db.populargame(redis_obj, sub, name, picture, email, ip)

            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = pg_general.Apiresult.success
                resultdata['clientdata'] = clientdata

            else:
                resultdata['apiresult'] = pg_general.Apiresult.connectdberror
                resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            resultdata['clientdata'] = clientdata

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'populargame_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'populargame_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def depositpackage_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        sub = data.get('sub')
        name = data.get('name')
        picture = data.get('picture')
        email = data.get('email')

        if None not in [sub, name]:
            result, clientdata = await db.depositpackage(sub, name, picture, email)

            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = pg_general.Apiresult.success
                resultdata['clientdata'] = clientdata

            else:
                resultdata['apiresult'] = pg_general.Apiresult.connectdberror
                resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            resultdata['clientdata'] = clientdata

        log_msg = """pg_asqldb:depositpackage return resultdata:{0}""".format(resultdata)
        pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'depositpackage_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'depositpackage_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def gamelobby_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        sub = data.get('sub')
        name = data.get('name')
        picture = data.get('picture')
        email = data.get('email')

        if None not in [sub, name]:
            result, clientdata = await db.gamelobby(sub, name, picture, email)

            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = pg_general.Apiresult.success
                resultdata['clientdata'] = clientdata

            elif result ==pg_general.Apiresult.connectdberror:
                resultdata['apiresult'] = pg_general.Apiresult.connectdberror
                resultdata['clientdata'] = clientdata

        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            resultdata['clientdata'] = clientdata

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'gamelobby_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'gamelobby_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def referralfriend_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        redis_obj = app['redis']
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        referralsub = data.get('referral_sub')
        sub = data.get('sub')
        sub_nickname = data.get('sub_nickname')
        referraltime = pg_general.converttype(data.get('referral_time'), str)

        if None not in [referralsub, sub, referraltime, sub_nickname]:
            result, clientdata = await db.referralfriend(redis_obj, referralsub, sub, referraltime, sub_nickname)


            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = pg_general.Apiresult.success
                resultdata['clientdata'] = clientdata

            elif result ==pg_general.Apiresult.connectdberror:
                resultdata['apiresult'] = pg_general.Apiresult.connectdberror
                resultdata['clientdata'] = clientdata
            elif result == pg_general.Apiresult.dbnodata:
                resultdata['apiresult'] = pg_general.Apiresult.dbnodata
                resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            resultdata['clientdata'] = clientdata

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'referralfriend_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'referralfriend_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def gameroomsharing_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        redis_obj = app['redis']
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        data = await request.json()
        line_uid = data.get('line_uid')
        room_id = data.get('room_id')
        nickname = data.get('nickname')

        if None not in [line_uid, room_id]:
            result, clientdata = await db.gameroomsharing(redis_obj, line_uid, room_id, nickname)


            if result == pg_general.Apiresult.success:
                resultdata['apiresult'] = pg_general.Apiresult.success
                resultdata['clientdata'] = clientdata
            elif result ==pg_general.Apiresult.parametererror:
                resultdata['apiresult'] = pg_general.Apiresult.parametererror
                resultdata['clientdata'] = clientdata
            elif result ==pg_general.Apiresult.connectdberror:
                resultdata['apiresult'] = pg_general.Apiresult.connectdberror
                resultdata['clientdata'] = clientdata
            elif result == pg_general.Apiresult.dbnodata:
                resultdata['apiresult'] = pg_general.Apiresult.dbnodata
                resultdata['clientdata'] = clientdata
            elif result == 4:
                resultdata['apiresult'] = 4
                resultdata['clientdata'] = clientdata
        else:
            resultdata['apiresult'] = pg_general.Apiresult.parametererror
            resultdata['clientdata'] = clientdata

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'gameroomsharing_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'gameroomsharing_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

async def setlinedepositanimation_handle(request):
    try:
        app = request.app
        db = app['DB'][0]
        clientdata = {}
        resultdata = {
            'clientdata': {},
            'apiresult': pg_general.Apiresult.connectdberror
        }

        member_id = request.match_info["smemberid"]

        result, clientdata = await db.sendlinedepositanimation(member_id, 'setlinedepositanimation')

        resultdata['apiresult'] = pg_general.Apiresult.success
        resultdata['clientdata'] = clientdata

    except ValueError:
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'setlinedepositanimation_handle ValueError: {0}'.format(
                                                                                                format_exc()))
    except Exception:
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'setlinedepositanimation_handle ValueError: {0}'.format(
                                                                                                format_exc()))

    return aiohttp.web.json_response(resultdata)

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
    try:
        app = request.app
        db = app['DB'][0]
        redis_obj = app['redis']

        command = request.rel_url.query.get('command')
        res = ''

        if command == 'clear room':
            res = await db._clear_room_data(redis_obj)

        resultdata = {
            'serverdata': 852,
            'clientdata': 852,
            'apiresult': 567,
            'res': res,
        }

    except:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            "testsettle_handle {}".format(format_exc()))

    return aiohttp.web.json_response(resultdata)

def main(port=PORT):
    try:
        if not env_setting.LOCAL_SERVER:
            time.sleep(10)
        pg_general.writelog(pg_general.PG_LogerLevel.debug, "api server start...")

        loop = asyncio.get_event_loop()
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
        app.router.add_route('GET', '/sendemailvalidate/{smemberid}/{slogintoken}/', sendemailvalidate_handle)
        app.router.add_route('GET', '/feedbackvalidatecode/{smemberid}/{slogintoken}/', feedbackvalidatecode_handle)
        app.router.add_route('GET', '/feedbackemailvalidatecode/{smemberid}/{slogintoken}/', feedbackemailvalidatecode_handle)
        app.router.add_route('GET', '/getgiftdata/{smemberid}/{slogintoken}/', getgiftdata_handle)
        app.router.add_route('GET', '/getcardinfo/{smemberid}/{slogintoken}/', getcardinfo_handle)
        app.router.add_route('GET', '/getchannellist/{smemberid}/{slogintoken}/', getchannellist_handle)
        app.router.add_route('GET', '/getclubchannellist/{smemberid}/{slogintoken}/', getclubchannellist_handle)
        app.router.add_route('GET', '/getchannelmember/{smemberid}/{slogintoken}/', getchannelmember_handle)
        app.router.add_route('GET', '/getclubchannelmember/{smemberid}/{slogintoken}/', getclubchannelmember_handle)
        app.router.add_route('GET', '/joinchannel/{smemberid}/{slogintoken}/', joinchannel_handle)
        app.router.add_route('GET', '/joinclubchannel/{smemberid}/{slogintoken}/', joinclubchannel_handle)
        app.router.add_route('GET', '/receivegift/{smemberid}/{slogintoken}/', receivegift_handle)
        app.router.add_route('GET', '/rejectgift/{smemberid}/{slogintoken}/', rejectgift_handle)
        app.router.add_route('GET', '/sendchannelchat/{smemberid}/{slogintoken}/', sendchannelchat_handle)
        app.router.add_route('GET', '/sendclubchannelchat/{smemberid}/{slogintoken}/', sendclubchannelchat_handle)
        app.router.add_route('GET', '/sendservicechat/{smemberid}/{slogintoken}/', sendservicechat_handle)
        app.router.add_route('GET', '/sendgift/{smemberid}/{slogintoken}/', sendgift_handle)
        app.router.add_route('GET', '/sendgiftsms/{smemberid}/{slogintoken}/', sendgiftsms_handle)
        app.router.add_route('GET', '/sendgiftemailsms/{smemberid}/{slogintoken}/', sendgiftemailsms_handle)
        app.router.add_route('POST', '/creditexchange/{smemberid}/{slogintoken}/', creditexchange_handle)
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
        app.router.add_route('GET', '/joincardgame/{smemberid}/{slogintoken}/', joincardgame_handle)
        app.router.add_route('GET', '/getnewdragontigerrank/{smemberid}/{slogintoken}/', getnewdragontigerrank_handle)
        app.router.add_route('GET', '/getnewtotalrank/{smemberid}/{slogintoken}/', getnewtotalrank_handle)
        app.router.add_route('GET', '/getselfrankgamesortnew/{smemberid}/{slogintoken}/', getselfrankgamesortnew_handle)
        app.router.add_route('GET', '/getmemberinfolessdata/{smemberid}/{slogintoken}/', getmemberinfolessdata_handle)
        app.router.add_route('GET', '/getboxinfo/{smemberid}/{slogintoken}/', getboxinfo_handle)
        app.router.add_route('GET', '/buybox/{smemberid}/{slogintoken}/', buybox_handle)
        app.router.add_route('GET', '/skiptutorial/{smemberid}/{slogintoken}/', skiptutorial_handle)
        app.router.add_route('GET', '/gettutorialguide/{smemberid}/{slogintoken}/', gettutorialguide_handle)
        app.router.add_route('GET', '/joinfishgame/{smemberid}/{slogintoken}/', joinfishgame_handle)
        app.router.add_route('GET', '/gettransferdata/{smemberid}/{slogintoken}/', gettransferdata_handle)
        app.router.add_route('GET', '/savetransferdata/{smemberid}/{slogintoken}/', savetransferdata_handle)
        app.router.add_route('POST', '/firstlogin/{smemberid}/{slogintoken}/', modfirstlogin_handle)
        app.router.add_route('GET', '/sendgameroomchat/{smemberid}/{slogintoken}/', sendgameroomchat_handle)
        app.router.add_route('GET', '/getgameroomchat/{smemberid}/{slogintoken}/', getgameroomchat_handle)
        # app.router.add_route('GET', '/webshopping/{smemberid}/}{slogintoken}/', webshopping_handle)
        app.router.add_route('GET', '/linegameshopping/{smemberid}/{slogintoken}/', linegameshopping_handle)
        app.router.add_route('GET', '/playingstatus/{smemberid}/{slogintoken}/', playingstatus_handle)
        app.router.add_route('GET', '/getroomsharingurl/{smemberid}/{slogintoken}/', getroomsharingurl_handle)
        app.router.add_route('GET', '/sendlinedepositanimation/{smemberid}/{slogintoken}/', sendlinedepositanimation_handle)

        # for club
        app.router.add_route('GET', '/getclublobbyinfo/{smemberid}/{slogintoken}/', get_club_lobby_info_handle)
        app.router.add_route('GET', '/checkclubname/{smemberid}/{slogintoken}/', check_club_name_handle)
        app.router.add_route('GET', '/createclub/{smemberid}/{slogintoken}/', create_club_handle)
        app.router.add_route('GET', '/applyclub/{smemberid}/{slogintoken}/', apply_club_handle)
        app.router.add_route('GET', '/getclubapplylist/{smemberid}/{slogintoken}/', get_club_apply_list_handle)
        app.router.add_route('GET', '/getclubmemberlist/{smemberid}/{slogintoken}/', get_club_member_list_handle)
        app.router.add_route('GET', '/getclubproxylist/{smemberid}/{slogintoken}/', get_club_proxy_list_handle)
        app.router.add_route('GET', '/verifyclubapply/{smemberid}/{slogintoken}/', verify_club_apply_handle)
        app.router.add_route('GET', '/quitclub/{smemberid}/{slogintoken}/', quit_club_handle)
        app.router.add_route('GET', '/kickclub/{smemberid}/{slogintoken}/', kick_club_handle)
        app.router.add_route('POST', '/modclubproxyholding/{smemberid}/{slogintoken}/', mod_club_proxy_holding_handle)
        app.router.add_route('POST', '/modclubmemberwinlimit/{smemberid}/{slogintoken}/', mod_club_member_win_limit_handle)
        app.router.add_route('POST', '/updateclubrightsetting/{smemberid}/{slogintoken}/', update_club_right_setting_handle)
        app.router.add_route('POST', '/prohibitplayerclub/{smemberid}/{slogintoken}/', prohibitplayerclub_handle)
        app.router.add_route('POST', '/transferclubcredit/{smemberid}/{slogintoken}/', transfer_club_credit_handle)
        app.router.add_route('POST', '/removeproxyright/{smemberid}/{slogintoken}/', remove_proxy_right_handle)
        app.router.add_route('POST', '/retrievemoney/{smemberid}/{slogintoken}/', retrieve_money_handle)
        app.router.add_route('POST', '/getmoneydetail/{smemberid}/{slogintoken}/', get_money_detail_handle)#金幣明細
        app.router.add_route('POST', '/saveclubinfo/{smemberid}/{slogintoken}/', save_club_info_handle)
        app.router.add_route('POST', '/closeclub/{smemberid}/{slogintoken}/', close_club_handle)
        app.router.add_route('POST', '/setclubroompassword/{smemberid}/{slogintoken}/', set_club_room_password_handle)
        app.router.add_route('POST', '/addclubroomsetting/{smemberid}/{slogintoken}/', add_club_room_setting_handle)
        app.router.add_route('POST', '/modclubroomsetting/{smemberid}/{slogintoken}/', mod_club_room_setting_handle)
        app.router.add_route('POST', '/deleteclubroomsetting/{smemberid}/{slogintoken}/', delete_club_room_setting_handle)
                
        app.router.add_route('POST', '/getgamerecord/{smemberid}/{slogintoken}/', get_game_record_handle)#遊戲紀錄
        app.router.add_route('POST', '/getselfrecord/{smemberid}/{slogintoken}/', get_self_record_handle)#我的戰績
        app.router.add_route('POST', '/getmemberrecord/{smemberid}/{slogintoken}/', get_member_record_handle)#會員戰績
        app.router.add_route('POST', '/getperformance/{smemberid}/{slogintoken}/', get_performance_handle)#績效
        app.router.add_route('POST', '/getmembermoneydetail/{smemberid}/{slogintoken}/', get_member_money_detail_handle)#個人金幣明細

        # for room
        app.router.add_route('POST', '/createroom/{smemberid}/{slogintoken}/', create_room_handle)
        app.router.add_route('GET', '/findjoinroom/{smemberid}/{slogintoken}/', find_join_room_handle)
        app.router.add_route('GET', '/joinroom/{smemberid}/{slogintoken}/', join_room_handle)
        app.router.add_route('GET', '/roomready/{smemberid}/{slogintoken}/', room_ready_handle)
        app.router.add_route('GET', '/leaveroom/{smemberid}/{slogintoken}/', leave_room_handle)
        app.router.add_route('GET', '/kickroom/{smemberid}/{slogintoken}/', kick_room_handle)
        app.router.add_route('POST', '/dismissroom/', dismiss_room_handle)
        app.router.add_route('GET', '/roomstart/{smemberid}/{slogintoken}/', room_start_handle)
        app.router.add_route('GET', '/getgameroomsetting/{smemberid}/{slogintoken}/', get_game_room_setting_handle)
        app.router.add_route('GET', '/getroomcard/{smemberid}/{slogintoken}/', get_room_card_handle)
        app.router.add_route('GET', '/getroominfo/{smemberid}/{slogintoken}/', get_room_info_handle)

        # 官方使用 api
        app.router.add_route('GET', '/jinsong/servicetouser/', servicetouser_handle)
        app.router.add_route('POST', '/getbanplayer/', getbanplayer_handle)
        app.router.add_route('POST', '/banplayeroperate/', banplayer_operate_handle)
        # ==================後台不使用此功能，目前暫停使用==================
        #app.router.add_route('GET', '/getcreditcardinfo/', getcreditcardinfo_handle)
        #app.router.add_route('POST', '/newcreditcardinfo/', newcreditcardinfo_handle)
        #app.router.add_route('POST', '/delcreditcardinfo/', delcreditcardinfo_handle)
        # ==================後台不使用此功能，目前暫停使用==================
        # ==================與修改貨幣匯率合併============================
        #app.router.add_route('POST', '/silvertogoldswitch/', silvertogoldswitch_handle)
        # ==================與修改貨幣匯率合併============================
        app.router.add_route('POST', '/memberitemoperate/', member_item_operate_handle)
        app.router.add_route('POST', '/addaction/', add_action_handle)
        app.router.add_route('GET', '/getaction/', get_action_handle)
        app.router.add_route('POST', '/deleteaction/', delete_action_handle)
        app.router.add_route('POST', '/sendinboxtomember/', send_inbox_to_member_handle)
        app.router.add_route('POST', '/searchinbox/', search_inbox_handle)
        app.router.add_route('POST', '/prohibitplayerall/', prohibitplayerall_handle)
        app.router.add_route('POST', '/getprohibitplayer/', getprohibitplayer_handle)
        app.router.add_route('POST', '/modexchangerateandswitch/', modexchangerateandswitch_handle)
        app.router.add_route('GET', '/getexchangerate/', getexchangerate_handle)
        app.router.add_route('GET', '/membersearch/', membersearch_handle)
        app.router.add_route('POST', '/modmember/', modmember_handle)
        app.router.add_route('POST', '/modclubmemberholding/', modclubmemberholding_handle)
        app.router.add_route('GET', '/getclublist/', getclublist_handle)
        app.router.add_route('GET', '/getclubpositionproxylist/', getclubpositionproxylist_handle)
        app.router.add_route('POST', '/setcreateclubverify/', setcreateclubverify_handle)

        # for ps call back gold host
        app.router.add_route('GET', '/api/signin', psapi_signin_handle)
        app.router.add_route('GET', '/api/authenticate', psapi_authenticate_handle)
        app.router.add_route('GET', '/api/logout', psapi_logout_handle)
        app.router.add_route('GET', '/api/bet', psapi_bet_handle)
        app.router.add_route('GET', '/api/result', psapi_result_handle)
        app.router.add_route('GET', '/api/getbalance', psapi_getbalance_handle)

        # for ps call back silver host
        app.router.add_route('GET', '/apis/authenticate', psapis_authenticate_handle)
        app.router.add_route('GET', '/apis/signin', psapis_signin_handle)
        app.router.add_route('GET', '/apis/logout', psapis_logout_handle)
        app.router.add_route('GET', '/apis/bet', psapis_bet_handle)
        app.router.add_route('GET', '/apis/result', psapis_result_handle)
        app.router.add_route('GET', '/apis/getbalance', psapis_getbalance_handle)
        app.router.add_route('GET', '/apis/game/refund', psapis_refund_handle)

        # for dummy 共享使用
        app.router.add_route('POST', '/api/dummy/login', dummy_login_handle)
        app.router.add_route('POST', '/api/dummy/logout', dummy_logout_handle)

        app.router.add_route('POST', '/setgamestatus/', set_game_status_handle)

        # for ps call back
        app.router.add_route('GET', '/apit/signin', psapit_signin_handle)
        app.router.add_route('GET', '/apit/authenticate', psapit_authenticate_handle)
        app.router.add_route('GET', '/apit/logout', psapit_logout_handle)
        app.router.add_route('GET', '/apit/bet', psapit_bet_handle)
        app.router.add_route('GET', '/apit/result', psapit_result_handle)
        app.router.add_route('GET', '/apit/getbalance', psapit_getbalance_handle)


        # for line use api
        app.router.add_route('POST', '/linedepositlog/', line_deposit_log_handle)
        app.router.add_route('POST', '/bindlineprofile/', bindlineprofile_handle)
        app.router.add_route('POST', '/updatepopulargame/', updatepopulargame_handle)
        app.router.add_route('POST', '/populargame/', populargame_handle)
        app.router.add_route('POST', '/depositpackage/', depositpackage_handle)
        # app.router.add_route('POST', '/gamelobby/', gamelobby_handle)
        app.router.add_route('POST', '/referralfriend/', referralfriend_handle)
        app.router.add_route('POST', '/gameroomsharing/', gameroomsharing_handle)

        app.router.add_route('GET', '/setlinedepositanimation/{smemberid}/', setlinedepositanimation_handle)

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
        app.router.add_route('GET', '/linelogincallback', line_login_callback_handle)
        app.router.add_route('GET', '/useagreementtext', use_agreement_text_handle)
        app.router.add_route('GET', '/privacyagreementtext', privacy_agreement_text_handle)
        # app.router.add_route('POST', '/flashpayreturn', flashpayreturn_handle)
        # app.router.add_route('POST', '/flashpaynotify', flashpaynotify_handle)

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


