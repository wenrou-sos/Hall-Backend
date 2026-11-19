import asyncio
import aiohttp.web
import pg_general
import json
import serverconf
from urllib import parse
from pg_redis import PGRedis
apiserver = serverconf.apiserver
from pg_ga import PG_GA
########################################  getapiresult ###############################
async def getapiresult(logintoken, realurl,jsoncontent=None):
    pg_general.writelog(pg_general.PG_LogerLevel.debug, "getapiresult logintoken:{0}, realurl:{1}".format(logintoken, realurl))
    commandresult = pg_general.Packagestatuscode.commanderror
    serverdata = {}
    clientdata = {}

    try:
        #async with aiohttp.request('GET', realurl) as response:
        async with aiohttp.ClientSession() as session:
            async with session.get(realurl,json=jsoncontent,timeout=60) as response:
                # response = await session.get(realurl,json=jsoncontent,timeout=60)
                if response.status == 200:
                    data = await response.json()
                    #data = json.loads(data)
                    apiresult = data.get("apiresult")
                    serverdata = data.get("serverdata", {})
                    clientdata = data.get("clientdata", {})

                    # apiresult轉換statuscode
                    if apiresult == pg_general.Apiresult.success:
                        commandresult = pg_general.Packagestatuscode.success
                    elif apiresult == pg_general.Apiresult.parametererror or apiresult == pg_general.Apiresult.dbnodata or apiresult == pg_general.Apiresult.othererror:
                        commandresult = pg_general.Packagestatuscode.commanderror
                    elif apiresult == pg_general.Apiresult.connectdberror:
                        commandresult = pg_general.Packagestatuscode.networkerror
                    elif apiresult == pg_general.Apiresult.balanceerror:
                        commandresult = pg_general.Packagestatuscode.balanceerror
                    elif apiresult == pg_general.Apiresult.accountfreeze:
                        commandresult = pg_general.Packagestatuscode.accountfreeze

                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        "getapiresult response, logintoken:{0}, realurl:{1}, apiresult:{2}, serverdata:{3}, clientdata:{4}, commandresult:{5}".format(
                                            logintoken, realurl, apiresult, serverdata, clientdata, commandresult))
                else:
                    commandresult = pg_general.Packagestatuscode.networkerror
                    pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                        "getapiresult response.status:{0}, url:{1}, logintoken:{2}".format(
                                            response.status, realurl, logintoken))
    except Exception as e:
        commandresult = pg_general.Packagestatuscode.networkerror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getapiresult error:{0}, url:{1}, logintoken:{2}".format(
                                e, realurl, logintoken))

    return serverdata, clientdata, commandresult

################################### api route #############################################
async def serverinfo_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000000
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/serverinfo', 'serverinfo')


    rer = recvdata.get('rer')
    ver = recvdata.get('ver')
    platform = recvdata.get('platform')
    if rer is None:
        rer = ''
    if ver is None:
        ver = ''

    param = '?ver={0}&rer={1}'.format(ver,rer)

    if platform is not None:
        param = param + '&platform={0}'.format(platform)



    # 發送request到apiserver
    realurl = apiserver + '/serverinfo/{0}/{1}/{2}'.format(memberid, logintoken,param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def sendofficialnoticepromotion(app,logintoken,memberid):
    try:
        await asyncio.sleep(3)
        ws = app["client_dict"][logintoken].client_ws
        redis = app['redis']

        # get redis chatroom_public and chatroom_channel_3
        memberchannel = await redis.get_all_keys('channel_*_{}'.format(memberid))
        if memberchannel is not None:
            memberchannelindex = int(memberchannel[0].split('_')[1])
        else:
            memberchannelindex = 3


        chatroom_public_list = await redis.lrange('chatroom_public',0,19)
        if chatroom_public_list is not None:
            chatroom_public_list.reverse()
            chatroom_public_list = [json.loads(item.decode('utf-8')) for item in chatroom_public_list]
            await ws.send_json({
                "commandid": 3000020,
                "data": {
                    "talklist": chatroom_public_list
                }
            })

        chatroom_channel_list = await redis.lrange('chatroom_channel_{}'.format(memberchannelindex),0,19)
        if chatroom_channel_list is not None:
            chatroom_channel_list.reverse()
            chatroom_channel_list = [json.loads(item.decode('utf-8')) for item in chatroom_channel_list]
            await ws.send_json({
                "commandid": 3000021,
                "data": {
                    "talklist": chatroom_channel_list,
                    "channelindex": memberchannelindex
                }
            })

        # 抓取保留的 私人訊息
        llen = await redis.llen('reservedchat_{}'.format(memberid))
        if llen > 0:
            contentlist = []
            for i in range(llen):
                content = await redis.rpop('reservedchat_{0}'.format(memberid))
                if content is not None:
                    contentlist.append(json.loads(content.decode('utf-8')))
            for item in contentlist:
                await ws.send_json({
                    "commandid": 3000005,
                    "data": item
                })
                await asyncio.sleep(0.3)



        await asyncio.sleep(12)

        chatroom_promotion = await redis.get_json_value('chatroom_promotion')
        chatroom_notice = await redis.get_json_value('chatroom_notice')



        nowtwtime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')

        if len(chatroom_notice) > 0:
            await ws.send_json({
                "commandid": 3000010,
                "data": {
                    "contentlist": chatroom_notice,
                    "time": nowtwtime
                }
            })
        if len(chatroom_promotion) > 0:
            await ws.send_json({
                "commandid": 3000011,
                "data": {
                    "contentlist": chatroom_promotion,
                    "time": nowtwtime
                }
            })
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            'sendofficialnoticepromotion except:{2} , logintoken:{0} set memberid:{1}'.format(logintoken, memberid,e))

async def login_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000001
    memberid = app["client_dict"][logintoken].memberid
    selflobbyserverip = app['selfip']+':{}'.format(app['port'])
    redis_obj = app['redis']


    if memberid is not None:         # 此 logintoken 已經跟 memberid 綁定, 不能再跑登入流程, return membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "login_msghandler error logintoken:{0}, recvdata:{1}".format(logintoken, recvdata))
        commandresult = pg_general.Packagestatuscode.membererror
        return clientdata, returncommandid, commandresult


    # client ip 改由 一開始的 load balancer 提供的為準
    ip = app["client_dict"][logintoken].ip


    deviceid = recvdata.get("deviceid")
    newaccflag = recvdata.get('newaccflag')
    username = recvdata.get('username')
    password = recvdata.get('password')
    fbid = recvdata.get("fbid")
    fbtoken = recvdata.get("fbtoken")
    fbavatar = recvdata.get('fbavatar')
    fcmtoken = recvdata.get('fcmtoken')
    connecttype = recvdata.get('connecttype')
    if connecttype is None:
        connecttype = 0

    if fbavatar is not None:
        if len(fbavatar) > 0 :
            fbavatar = parse.quote(fbavatar)
    fbnickname = recvdata.get('fbnickname')
    if fbnickname is not None:
        if len(fbnickname) > 0:
            fbnickname = parse.quote(fbnickname)
    platform = recvdata.get("platform")

    devicedescription = recvdata.get("devicedescription")
    if devicedescription is not None:
        if len(devicedescription) > 0:
            devicedescription = parse.quote(devicedescription)

    auserid = recvdata.get('auserid')
    aauthcode = recvdata.get('aauthcode')
    atoken = recvdata.get('atoken')

    region = app["client_dict"][logintoken].region
    region_sub = app['client_dict'][logintoken].region_sub
    city = app["client_dict"][logintoken].city
    parameters = None


    if (None not in [newaccflag, deviceid, platform]) or (None not in [username,password,deviceid]):
        parameters = "?deviceid={0}&platform={1}".format(deviceid, platform)

        if None not in [username,password]:
            parameters = parameters + '&username={0}&password={1}'.format(username,password)

        if newaccflag is not None:
            parameters = parameters + '&newaccflag={0}'.format(newaccflag)

        if fbid is not None:
            parameters = parameters + '&fbid={0}'.format(fbid)
        if fbtoken is not None:
            parameters = parameters + '&fbtoken={0}'.format(fbtoken)
        if fbavatar is not None:
            parameters = parameters + '&fbavatar={0}'.format(fbavatar)
        if fbnickname is not None:
            parameters = parameters + '&fbnickname={0}'.format(fbnickname)
        if auserid is not None:
            parameters = parameters + '&auserid={0}'.format(auserid)
        if aauthcode is not None:
            parameters = parameters + '&aauthcode={0}'.format(aauthcode)
        if atoken is not None:
            parameters = parameters + '&atoken={0}'.format(atoken)

        if ip is not None:
            parameters = parameters + '&ip={0}'.format(ip)
        if devicedescription is not None:
            parameters = parameters + '&devicedescription={0}'.format(devicedescription)
        if fcmtoken is not None:
            parameters = parameters + '&fcmtoken={0}'.format(fcmtoken)

        parameters = parameters + '&lobbyserverip={0}'.format(app['selfip']+':{}'.format(app['port']))

        if region is not None:
            parameters = parameters + '&region={0}'.format(region)
        if region is not None:
            parameters = parameters + '&region_sub={0}'.format(region_sub)
        if city is not None:
            parameters = parameters + '&city={0}'.format(city)


        ver = None
        rer = None
        ver = recvdata.get('ver')
        rer = recvdata.get('rer')
        if ver is not None:
            parameters = parameters + '&ver={0}'.format(ver)
        if rer is not None:
            parameters = parameters + '&rer={0}'.format(rer)

        if connecttype is not None:
            parameters = parameters + '&connecttype={0}'.format(connecttype)

    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "login_msghandler parameters error:{0}, logintoken:{1}, recvdata:{2}".format(
                                parameters, logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/login/{0}/{1}/{2}'.format(memberid, logintoken, parameters)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:   # 登入失敗
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
        else:  # 登入成功
            # 設定memberid
            memberid = serverdata.get("memberid")
            if memberid is not None:

                nowtwtime = pg_general.get_tw_datetime()
                app["client_dict"][logintoken].setmemberid(memberid)
                app["client_dict"][logintoken].setlogintime(nowtwtime)
                ga_obj = app["client_dict"][logintoken].ga_obj
                #ga_obj.set_memberid(memberid)
                #ga_obj.set_ip(ip)
                ga_obj.send_page_view('/login', 'login')
                pg_general.writelog(pg_general.PG_LogerLevel.info, 'login_msghandler logintoken:{0} set memberid:{1}'.format(logintoken, memberid))

                # 先寫入 redis logintoken and lobbyserverip

                result_set_redis = await redis_obj.set_value(memberid,logintoken,180)
                result_set_redis = await redis_obj.set_value('online_{}'.format(memberid),selflobbyserverip,15)
                asyncio.ensure_future(sendofficialnoticepromotion(app,logintoken,memberid))

            elif clientdata.get('result') is not None:  # 有 result 值表示  直接回傳 result 給 client

                pass
            else:
                commandresult = pg_general.Packagestatuscode.commanderror
                clientdata = {}
    return clientdata, returncommandid, commandresult


async def getmemberinfo_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000002
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getmemberinfo', 'getmemberinfo')

    param_memberid = recvdata.get('memberid')

    if param_memberid is None:
        param_memberid = ''
    else:
        param_memberid = '?param_memberid=' + str(param_memberid)
    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getmemberinfo_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getmemberinfo/{0}/{1}/{2}'.format(memberid, logintoken,param_memberid)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult






async def updateprofile_msghandler(app, logintoken, recvdata):

    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000006
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/updateprofile', 'updateprofile')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "updateprofile_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # avatar = recvdata.get("avatar")
    nickname = recvdata.get("nickname")

    parameters = ""
    if nickname != None:
        parameters = "?nickname={0}".format(nickname)

    if parameters is None:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "updateprofile_msghandler parameters error:{0}, logintoken:{1}, recvdata:{2}".format(
                                parameters, logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/updateprofile/{0}/{1}/{2}'.format(memberid, logintoken, parameters)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult






async def getdailybonusinfo_msghandler(app, logintoken, recvdata):      # 每日登入可以轉一次的大轉輪
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000009
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getdailybonusinfo', 'getdailybonusinfo')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getdailybonusinfo_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getdailybonusinfo/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def spindailybonus_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000010
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/spindailybonus', 'spindailybonus')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "spindailybonus_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult


    # 發送request到apiserver
    realurl = apiserver + '/spindailybonus/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult



async def getpiggyinfo_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000018
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getpiggyinfo', 'getpiggyinfo')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getpiggyinfo_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getpiggyinfo/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getmallinfo_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000019
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getmallinfo', 'getmallinfo')

    mode = recvdata.get('mode')
    if mode is None:
        mode = 0
    else:
        mode = pg_general.converttype(mode,int)

    if memberid is None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getmallinfo_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getmallinfo/{0}/{1}/?mode={2}'.format(memberid, logintoken,mode)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def shopping_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000020
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/shopping', 'shopping')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "shopping_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 先看memberid的log，比對玩家是否不是機器人帳號，等級用error才能看到log
    pg_general.writelog(pg_general.PG_LogerLevel.error, 'shopping_msghandler memberid={}'.format(memberid))
    # 確認memberid，機器人自動帳號則退回到玩家
    memberid = int(memberid)
    if memberid <= 2:  # 2以下都不是正常帳號
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.error, "shopping_msghandler memberid={} is failed".format(memberid))
        return clientdata, returncommandid, commandresult

    platform = recvdata.get("platform")
    jsoncontent = recvdata.get('content')
    shopid = recvdata.get('shopid')
    num = recvdata.get('num')           # new add parameter
    mode = recvdata.get('mode') # 0: 3 items. 1: 6 items

    if mode is None:
        mode=0
    else:
        mode = pg_general.converttype(mode,int)

    pg_general.writelog(pg_general.PG_LogerLevel.warn,
                        "shopping_msghandler platform:{0},content:{1},shopid:{2},mode:{3}".format(platform,jsoncontent,shopid,mode))
    parameters = None
    if None not in [platform,jsoncontent,mode]:   # shopid拿掉，另外在裡面處理

        # 先記錄shopid的log
        pg_general.writelog(pg_general.PG_LogerLevel.error, "shopping_msghandler shopid={}".format(shopid))
        # 如果沒有shopid，則在jsoncontent內找到shopid，填進去
        if shopid == None:
            shopid = jsoncontent["id"]
            # 如果連content["id"]都是None，則回傳失敗
            if shopid == None:
                commandresult = pg_general.Packagestatuscode.commanderror
                pg_general.writelog(pg_general.PG_LogerLevel.error, "shopping_msghandler shopid is null")
                return clientdata, returncommandid, commandresult

        parameters = {
            "data":{
                "platform":platform,
                "jsoncontent":jsoncontent,
                "shopid": shopid,
                "mode": mode
            }
        }

        # new add parameter for 新舊相容, 要保留舊的
        # 要先判斷是否有此值, 如果有的話以此值為準

        if num is not None:
            parameters['data']['num'] = num


    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "shopping_msghandler parameters error:{0}, logintoken:{1}, recvdata:{2}".format(
                                parameters, logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/shopping/{0}/{1}/?mode={2}'.format(memberid, logintoken,mode)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl,parameters)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getinboxinfo_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000021
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getinboxinfo', 'getinboxinfo')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getinboxinfo_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getinboxinfo/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def receiveinbox_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000022
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/receiveinbox', 'receiveinbox')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "receiveinbox_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    inboxid = recvdata.get("inboxid")
    parameters = None
    if isinstance(inboxid, int) == True:
        parameters = "?inboxid={0}".format(inboxid)
    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "receiveinbox_msghandler parameters error:{0}, logintoken:{1}, recvdata:{2}".format(
                                parameters, logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/receiveinbox/{0}/{1}/{2}'.format(memberid, logintoken, parameters)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def feedback_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000023
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/feedback', 'feedback')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "feedback_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    email = recvdata.get("email")
    content = recvdata.get("content")
    typeid = recvdata.get("typeid")
    parameters = None
    if None not in [email,content,typeid]:
        parameters = "?email={0}&content={1}&typeid={2}".format(email, content,typeid)
    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "feedback_msghandler parameters error:{0}, logintoken:{1}, recvdata:{2}".format(
                                parameters, logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/feedback/{0}/{1}/{2}'.format(memberid, logintoken, parameters)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getgamelist_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000025
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getgamelist', 'getgamelist')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getgamelist_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult



    # 發送request到apiserver
    realurl = apiserver + '/getgamelist/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def joingame_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000026
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    #ga_obj.send_page_view('/joingame', 'joingame')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "joingame_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    gameid = recvdata.get("gameid")
    gametype = recvdata.get("gametype")

    ga_obj.send_page_view('/joingame_{0}'.format(gameid),'gameid')


    parameters = None
    if gameid != None and isinstance(gametype, int) == True:
        parameters = "?gameid={0}&gametype={1}".format(gameid, gametype)
    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "joingame_msghandler parameters error:{0}, logintoken:{1}, recvdata:{2}".format(
                                parameters, logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/joingame/{0}/{1}/{2}'.format(memberid, logintoken, parameters)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getgamerank_msghandler(app, logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000027
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getgamerank', 'getgamerank')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getgamerank_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    gameid = recvdata.get("gameid")

    parameters = None

    if gameid != None:
        parameters = "?gameid={0}".format(gameid)
    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getgamerank_msghandler parameters error:{0}, logintoken:{1}, recvdata:{2}".format(
                                parameters, logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getgamerank/{0}/{1}/{2}'.format(memberid, logintoken, parameters)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getleaderrank_msghandler(app, logintoken, recvdata):   # 一次取得兩個陣營以及富豪榜單
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000028
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getleaderrank', 'getleaderrank')

    if memberid == None:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getleaderrank memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult


    # 發送request到apiserver
    realurl = apiserver + '/getleaderrank/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0 or clientdata.get('result') == 1:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult







async def logout_msghandler(memberid,logintoken):
    # 發送request到apiserver
    realurl = apiserver + '/logout/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)
    pg_general.writelog(pg_general.PG_LogerLevel.info, 'logout logintoken:{0}, commandresult:{1}'.format(logintoken, commandresult))


async def setmyselfip_msghandler(app):
    # 送給 api server 寫入 table
    pg_general.writelog(pg_general.PG_LogerLevel.info,
                        'setmyselfip_msghandler ip:{0}'.format(app['selfip']+':{}'.format(app['port'])))
    realurl = apiserver + '/setlobbyip/{0}/'.format(app['selfip']+ ':{}'.format(app['port']))
    logintoken = 'lobbyserversetmyselfip'
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)
    pg_general.writelog(pg_general.PG_LogerLevel.info,
                        'setmyselfip_msghandler logintoken:{0}, commandresult:{1}'.format(logintoken, commandresult))
    return commandresult

async def sendchat_msghandler(app, logintoken, recvdata):

    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000031
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/sendchat', 'sendchat')

    content_type = recvdata.get('type')
    content = recvdata.get('content')
    if None in [memberid,content_type,content]:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "sendchat_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    senddata ={
        "type": content_type,
        "content": content
    }
    # 發送request到apiserver
    realurl = apiserver + '/sendchat_public/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl,senddata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getsecretmall_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000035
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getsecretmall', 'getsecretmall')

    if None in [memberid]:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getsecretmall_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getsecretmall/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def senddownloadsignal_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000036
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    region = app["client_dict"][logintoken].region

    if region is None:
        region = '0'

    region = region.lower()

    state = recvdata.get('state')


    ga_obj.send_page_view('/downloadsignal{0}'.format(str(state)), str(state))

    # 發送request到apiserver
    realurl = apiserver + '/senddownloadsignal/{0}/{1}/?state={2}&region={3}'.format(memberid, logintoken,state,region)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    # if commandresult == pg_general.Packagestatuscode.success:
    #     if len(clientdata) == 0:
    #         commandresult = pg_general.Packagestatuscode.commanderror
    #         clientdata = {}

    return clientdata, returncommandid, commandresult


async def getpiggycredit_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000038
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getpiggycredit', 'getpiggycredit')

    # 發送request到apiserver
    realurl = apiserver + '/getpiggycredit/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getfriendlist_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000039
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getfriendlist', 'getfriendlist')

    # 發送request到apiserver
    realurl = apiserver + '/getfriendlist/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getblacklist_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000040
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getblacklist', 'getblacklist')

    # 發送request到apiserver
    realurl = apiserver + '/getblacklist/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def updatefriendlist_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000041
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/updatefriendlist', 'updatefriendlist')

    type = recvdata.get('type')
    friend_memberid = recvdata.get('friend_memberid')
    friend_nickname = recvdata.get('friend_nickname')

    if None in [type]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    if type in [0,1]:
        if friend_memberid is None:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
            return clientdata,returncommandid, commandresult
        param = '?type={0}&friend_memberid={1}'.format(type,friend_memberid)
    elif type in [2,3]:
        if friend_nickname is None:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
            return clientdata,returncommandid, commandresult
        param = '?type={0}&friend_nickname={1}'.format(type,friend_nickname)
    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult


    # 發送request到apiserver
    realurl = apiserver + '/updatefriendlist/{0}/{1}/{2}'.format(memberid, logintoken,param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def updateblacklist_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000042
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/updateblacklist', 'updateblacklist')

    type = recvdata.get('type')
    black_memberid = recvdata.get('black_memberid')
    black_nickname = recvdata.get('black_nickname')

    if None in [type]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult
    if type in [0,1]:
        if black_memberid is None:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
            return clientdata, returncommandid, commandresult
        param = '?type={0}&black_memberid={1}'.format(type, black_memberid)
    elif type in [2,3]:
        if black_nickname is None:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
            return clientdata, returncommandid, commandresult
        param = '?type={0}&black_nickname={1}'.format(type,black_nickname)
    else:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/updateblacklist/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def openprivatechatroom_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000043
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/openprivatechatroom', 'openprivatechatroom')

    chat_memberid = recvdata.get('memberid')


    if None in [chat_memberid]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    param = '?chat_memberid={0}'.format(chat_memberid)

    # 發送request到apiserver
    realurl = apiserver + '/openprivatechatroom/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def safetask_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000044
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/safetask', 'safetask')

    type = recvdata.get('type')
    amount = recvdata.get('amount')

    if None in [type] or (type in [0,1] and amount is None):
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    param = '?type={0}'.format(type)
    if type in [0,1]:
        param = param + '&amount={0}'.format(amount)

    # 發送request到apiserver
    realurl = apiserver + '/safetask/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def serialinput_msghandler(app,logintoken,recvdata): # 輸入序號拿金幣
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000045
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/serialinput', 'serialinput')

    serial = recvdata.get('serial')


    if serial is None:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    if len(serial.strip()) == 0:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult


    param = '?serial={0}'.format(serial)

    # 發送request到apiserver
    realurl = apiserver + '/serialinput/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def makelike_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000046
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/makelike', 'makelike')

    likememberid = recvdata.get('memberid')

    if likememberid is None:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    param = '?likememberid={0}'.format(likememberid)

    # 發送request到apiserver
    realurl = apiserver + '/makelike/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def sendprivatchat_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000047
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/sendprivatchat', 'sendprivatchat')

    chatmemberid = recvdata.get('memberid')
    type = recvdata.get('type')
    content = recvdata.get('content')

    if None in [chatmemberid,type,content]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    param = '?chatmemberid={0}&type={1}&content={2}'.format(chatmemberid,type,content)

    # 發送request到apiserver
    realurl = apiserver + '/sendprivatchat/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult != pg_general.Packagestatuscode.success:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}

    return clientdata, returncommandid, commandresult

async def sendphonevalidate_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000048
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/sendphonevalidate', 'sendphonevalidate')

    phone = recvdata.get('phone')

    if None in [phone]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    param = '?phone={0}'.format(phone)

    # 發送request到apiserver
    realurl = apiserver + '/sendphonevalidate/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def feedbackvalidatecode_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000049
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/feedbackvalidatecode', 'feedbackvalidatecode')

    code = recvdata.get('code')

    if None in [code]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    param = '?code={0}'.format(code)

    # 發送request到apiserver
    realurl = apiserver + '/feedbackvalidatecode/{0}/{1}/{2}'.format(memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getgiftdata_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000050
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getgiftdata', 'getgiftdata')


    # 發送request到apiserver
    realurl = apiserver + '/getgiftdata/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getcardinfo_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000051
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getcardinfo', 'getcardinfo')

    # 發送request到apiserver
    realurl = apiserver + '/getcardinfo/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getchannellist_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000052
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getchannellist', 'getchannellist')

    # 發送request到apiserver
    realurl = apiserver + '/getchannellist/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getchannelmember_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000053
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getchannelmember', 'getchannelmember')

    channelindex = recvdata.get('channelindex')

    if None in [channelindex]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult


    # 發送request到apiserver
    realurl = apiserver + '/getchannelmember/{0}/{1}/?channelindex={2}'.format(memberid, logintoken,channelindex)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def joinchannel_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000054
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/joinchannel', 'joinchannel')

    channelindex = recvdata.get('channelindex')

    if None in [channelindex]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/joinchannel/{0}/{1}/?channelindex={2}'.format(memberid, logintoken, channelindex)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def receivegift_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000055
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/receivegift', 'receivegift')

    num = recvdata.get('num')
    password = recvdata.get('password')

    if None in [num,password]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/receivegift/{0}/{1}/?num={2}&password={3}'.format(memberid, logintoken, num,password)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def rejectgift_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000056
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/rejectgift', 'rejectgift')

    num = recvdata.get('num')

    if None in [num]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/rejectgift/{0}/{1}/?num={2}'.format(memberid, logintoken, num)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)


    return clientdata, returncommandid, commandresult

async def sendchannelchat_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000057
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/sendchannelchat', 'sendchannelchat')

    channelindex = recvdata.get('channelindex')
    type = recvdata.get('type')
    content = recvdata.get('content')

    if None in [channelindex,type,content]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/sendchannelchat/{0}/{1}/?type={2}&content={3}&channelindex={4}'.format(memberid, logintoken,type,content,channelindex )
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)
    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
    return clientdata, returncommandid, commandresult

async def sendservicechat_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000058
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/sendservicechat', 'sendservicechat')

    type = recvdata.get('type')
    content = recvdata.get('content')

    if None in [type, content]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/sendservicechat/{0}/{1}/?type={2}&content={3}'.format(memberid, logintoken,type, content)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)
    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
    return clientdata, returncommandid, commandresult

async def sendgift_msghandler(app,logintoken, recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000059
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/sendgift', 'sendgift')

    nickname = recvdata.get('nickname')
    amount = recvdata.get('amount')
    password = recvdata.get('password')
    addflag = recvdata.get('addflag')
    code = recvdata.get('code')

    if None in [nickname, amount, password,addflag,code]:
        commandresult = pg_general.Packagestatuscode.commanderror
        clientdata = {}
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/sendgift/{0}/{1}/?nickname={2}&amount={3}&password={4}&addflag={5}&code={6}'.format(memberid, logintoken, nickname, amount,password,addflag,code)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)
    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def sendgiftsms_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000060
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/sendgiftsms', 'sendgiftsms')


    # 發送request到apiserver
    realurl = apiserver + '/sendgiftsms/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)
    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def creditexchange_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000061
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/creditexchange', 'creditexchange')

    type = recvdata.get('type')
    amount = recvdata.get('amount')

    if None in [amount, type]:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "creditexchange_msghandler command error logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/creditexchange/{0}/{1}/?type={2}&amount={3}'.format(memberid, logintoken, type,amount)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def pointtocredit_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000062
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/pointtocredit', 'pointtocredit')

    type = recvdata.get('type')
    amount = recvdata.get('amount')

    if None in [type]:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "pointtocredit_msghandler command error logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    if type==0 and None in [amount]:
        commandresult = pg_general.Packagestatuscode.commanderror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "pointtocredit_msghandler command error logintoken:{0}, recvdata:{1}".format(
                                logintoken, recvdata))
        return clientdata, returncommandid, commandresult
    # 發送request到apiserver
    realurl = apiserver + '/pointtocredit/{0}/{1}/?type={2}&amount={3}'.format(memberid, logintoken, type, amount)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getfreeboxstatus_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000063
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getfreeboxstatus', 'getfreeboxstatus')

    # 發送request到apiserver
    realurl = apiserver + '/getfreeboxstatus/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def receivefreebox_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000064
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/receivefreebox', 'receivefreebox')

    # 發送request到apiserver
    realurl = apiserver + '/receivefreebox/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def forgetpasssms_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000065

    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/forgetpasssms', 'forgetpasssms')

    username = recvdata.get('username')
    phone = recvdata.get('phone')

    # 發送request到apiserver
    realurl = apiserver + '/forgetpasssms/xxx/{0}/?username={1}&phone={2}'.format(logintoken,username,phone)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def changenewpassword_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000066

    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/changenewpassword', 'changenewpassword')

    username = recvdata.get('username')
    phone = recvdata.get('phone')
    validatecode = recvdata.get('validatecode')
    newpassword = recvdata.get('newpassword')

    # 發送request到apiserver
    realurl = apiserver + '/changenewpassword/xxx/{0}/?username={1}&phone={2}&validatecode={3}&newpassword={4}'.format(logintoken, username, phone,validatecode,newpassword)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def bindusername_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000067

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/bindusername', 'bindusername')

    username = recvdata.get('username')
    password = recvdata.get('password')

    # 發送request到apiserver
    realurl = apiserver + '/bindusername/{0}/{1}/?username={2}&password={3}'.format(
        memberid,logintoken,username, password)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def updatemembermessage_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000068

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/updatemembermessage', 'updatemembermessage')

    message = recvdata.get('message')
    jsondata = {"message":message}
    if message is not None:
        # 發送request到apiserver
        realurl = apiserver + '/updatemembermessage/{0}/{1}/'.format(
            memberid, logintoken)
        serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl,jsoncontent=jsondata)

        # 檢查結果
        if commandresult == pg_general.Packagestatuscode.success:
            if len(clientdata) == 0:
                commandresult = pg_general.Packagestatuscode.commanderror
                clientdata = {}
    else:
        commandresult = pg_general.Packagestatuscode.commanderror


    return clientdata, returncommandid, commandresult

async def reportmember_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000069

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/reportmember', 'reportmember')

    tomemberid = recvdata.get('memberid')
    content = recvdata.get('content')

    if None not in [tomemberid,content]:

        jsondata = {"memberid": tomemberid,"content": content}

        # 發送request到apiserver
        realurl = apiserver + '/reportmember/{0}/{1}/'.format(
            memberid, logintoken)
        serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

        # 檢查結果
        if commandresult == pg_general.Packagestatuscode.success:
            if len(clientdata) == 0:
                commandresult = pg_general.Packagestatuscode.commanderror
                clientdata = {}
    else:
        commandresult = pg_general.Packagestatuscode.commanderror

    return clientdata, returncommandid, commandresult

async def actionframe_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000070

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/actionframe', 'actionframe')

    jsondata = {}

    # 發送request到apiserver
    realurl = apiserver + '/actionframe/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}


    return clientdata, returncommandid, commandresult

async def getselfrankgamesort_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000073

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getselfrankgamesort', 'getselfrankgamesort')

    jsondata = {}

    # 發送request到apiserver
    realurl = apiserver + '/getselfrankgamesort/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getselfrankgamesortnew_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000081

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getselfrankgamesortnew', 'getselfrankgamesortnew')

    jsondata = {}

    # 發送request到apiserver
    realurl = apiserver + '/getselfrankgamesortnew/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getmemberinfolessdata_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000082

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getmemberinfolessdata', 'getmemberinfolessdata')

    findmemberid = recvdata.get('findmemberid')

    jsondata = {
        "findmemberid": findmemberid
    }

    # 發送request到apiserver
    realurl = apiserver + '/getmemberinfolessdata/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getboxinfo_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000083

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getboxinfo', 'getboxinfo')

    jsondata = {}

    # 發送request到apiserver
    realurl = apiserver + '/getboxinfo/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def buybox_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000084

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/buybox', 'buybox')

    item = recvdata.get('item')
    if None not in [item]:

        # 發送request到apiserver
        realurl = apiserver + '/buybox/{0}/{1}/?item={2}'.format(memberid, logintoken,item)
        serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

        # 檢查結果
        if commandresult == pg_general.Packagestatuscode.success:
            if len(clientdata) == 0:
                commandresult = pg_general.Packagestatuscode.commanderror
                clientdata = {}
    else:
        commandresult = pg_general.Packagestatuscode.commanderror

    return clientdata, returncommandid, commandresult


async def skiptutorial_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000085

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/skiptutorial', 'skiptutorial')


    # 發送request到apiserver
    realurl = apiserver + '/skiptutorial/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def gettutorialguide_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000086

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/gettutorialguide', 'gettutorialguide')

    # 發送request到apiserver
    realurl = apiserver + '/gettutorialguide/{0}/{1}/'.format(memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def joinfishgame_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {"result": 1}
    returncommandid = 2000087

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/joinfishgame', 'joinfishgame')

    hallid = recvdata.get('hallid')
    gameid = recvdata.get('gameid')


    if None not in [hallid,gameid]:
        # 發送request到apiserver
        realurl = apiserver + '/joinfishgame/{0}/{1}/?hallid={2}&gameid={3}'.format(memberid, logintoken,hallid,gameid)
        serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

        # 檢查結果
        if commandresult == pg_general.Packagestatuscode.success:
            if len(clientdata) == 0:
                commandresult = pg_general.Packagestatuscode.commanderror
                clientdata = {"result": 1}
            else:
                logdataindex = clientdata.get('logdataindex')

                if logdataindex is not None:
                    clientdata.pop('logdataindex')
                    app["client_dict"][logintoken].gamelogdataindex = logdataindex
                app["client_dict"][logintoken].joinedgameid = gameid
                app["client_dict"][logintoken].joinedhall = hallid + 3
                app["client_dict"][logintoken].seatnum = 0
                app["client_dict"][logintoken].joinedgametime = pg_general.getutcnowdatetime()
    else:
        commandresult = pg_general.Packagestatuscode.commanderror

    return clientdata, returncommandid, commandresult


async def getavatarlist_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000074

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getavatarlist', 'getavatarlist')

    jsondata = {}

    # 發送request到apiserver
    realurl = apiserver + '/getavatarlist/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def setavatarfromlist_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000075

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/setavatarfromlist', 'setavatarfromlist')

    avatarurl = recvdata.get('avatarurl')
    jsondata = {}
    if None not in [avatarurl]:
        jsondata = {"avatarurl": avatarurl}

        # 發送request到apiserver
        realurl = apiserver + '/setavatarfromlist/{0}/{1}/'.format(
            memberid, logintoken)
        serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

        # 檢查結果
        if commandresult == pg_general.Packagestatuscode.success:
            if len(clientdata) == 0:
                commandresult = pg_general.Packagestatuscode.commanderror
                clientdata = {}
    else:
        commandresult = pg_general.Packagestatuscode.commanderror

    return clientdata, returncommandid, commandresult


async def getseatsinfo_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000076

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getseatsinfo', 'getseatsinfo')

    gameid = recvdata.get('gameid')
    type = recvdata.get('type')

    jsondata = {}
    if None not in [gameid,type]:
        param = '?gameid={}&type={}'.format(gameid,type)

        # 發送request到apiserver
        realurl = apiserver + '/getseatsinfo/{0}/{1}/{2}'.format(
            memberid, logintoken,param)
        serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

        # 檢查結果
        if commandresult == pg_general.Packagestatuscode.success:
            if len(clientdata) == 0:
                commandresult = pg_general.Packagestatuscode.commanderror
                clientdata = {}
    else:
        commandresult = pg_general.Packagestatuscode.commanderror

    return clientdata, returncommandid, commandresult

async def joingameseat_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000077

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/joingameseat', 'joingameseat')

    gameid = recvdata.get('gameid')
    gametype = recvdata.get('gametype')
    seatnum = recvdata.get('seatnum')

    if None in [gameid,gametype,seatnum]:
        commandresult = pg_general.Packagestatuscode.commanderror
        return clientdata, returncommandid, commandresult

    param = '?gameid={}&gametype={}&seatnum={}'.format(gameid,gametype,seatnum)

    # 發送request到apiserver
    realurl = apiserver + '/joingameseat/{0}/{1}/{2}'.format(
        memberid, logintoken,param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}
        else:
            logdataindex = clientdata.get('logdataindex')
            tempseatnum = clientdata.get('seatnum')
            if logdataindex is not None:
                app["client_dict"][logintoken].gamelogdataindex = logdataindex
            app["client_dict"][logintoken].joinedgameid = gameid
            app["client_dict"][logintoken].joinedhall = gametype
            app["client_dict"][logintoken].seatnum = tempseatnum


    return clientdata, returncommandid, commandresult

async def backtohall_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000078
    redis = app['redis']

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/backtohall', 'backtohall')

    gameid = app["client_dict"][logintoken].joinedgameid
    hallid = app["client_dict"][logintoken].joinedhall
    seatnum = app["client_dict"][logintoken].seatnum
    gamelogdataindex = app["client_dict"][logintoken].gamelogdataindex



    if gameid != '':  # 刪除佔位資料, 因為要判斷卡別資料,所以要丟給 apiserver 處理
        app["client_dict"][logintoken].joinedgameid = ''
        app["client_dict"][logintoken].joinedhall = 0
        app["client_dict"][logintoken].seatnum = 0
        app["client_dict"][logintoken].gamelogdataindex = 0
        # remove redis this game data
        if hallid == 0:
            seatkey = 'gold'
        elif hallid ==1:
            seatkey = 'silver'
        elif hallid ==2:
            seatkey = 'tutorial'
        elif hallid ==3:
            seatkey = 'fishg'
        elif hallid ==4:
            seatkey = 'fishs'

        seat_data = 'seats{}_{}@{}_{}'.format(seatkey, gameid, seatnum, memberid)

        pg_general.writelog(pg_general.PG_LogerLevel.info, seat_data)
        await redis.del_key(seat_data)

        # 發送request到apiserver
        realurl = apiserver + '/backtohall/{0}/{1}/?gamelogdataindex={2}&seatdata={3}'.format(memberid, logintoken,gamelogdataindex,seat_data)
        serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)


        commandresult = pg_general.Packagestatuscode.success
        clientdata = {"result": 0}
    return clientdata, returncommandid, commandresult

async def getnewdragontigerrank_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000079

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getnewdragontigerrank', 'getnewdragontigerrank')

    gameid = recvdata.get('gameid')

    if None in [gameid]:
        commandresult = pg_general.Packagestatuscode.commanderror
        return clientdata, returncommandid, commandresult

    param = '?gameid={}'.format(gameid)

    # 發送request到apiserver
    realurl = apiserver + '/getnewdragontigerrank/{0}/{1}/{2}'.format(
        memberid, logintoken, param)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def getnewtotalrank_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000080

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getnewtotalrank', 'getnewtotalrank')



    # 發送request到apiserver
    realurl = apiserver + '/getnewtotalrank/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def restoreIAP_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000072

    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/restoreIAP', 'restoreIAP')


    platform = recvdata.get('platform')
    content = recvdata.get('content')
    jsondata = {
        "platform": platform,
        "content": content
    }
    # 發送request到apiserver
    realurl = apiserver + '/restoreIAP/{0}/{1}/'.format(
        memberid, logintoken)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl, jsoncontent=jsondata)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult


async def getsettingcontent_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000033
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/getsetttingcontent', 'getsettingcontent')

    type = recvdata.get('type')

    if None in [memberid,type]:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.warn,
                            "getsettingcontent_msghandler memberid error, logintoken:{0}, recvdata:{1}".format(logintoken, recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    realurl = apiserver + '/getsettingcontent/{0}/{1}/?type={2}'.format(memberid, logintoken,type)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def testshopping_msghandler(app,logintoken,recvdata):
    commandresult = pg_general.Packagestatuscode.networkerror
    serverdata = {}
    clientdata = {}
    returncommandid = 2000034
    memberid = app["client_dict"][logintoken].memberid
    ga_obj = app["client_dict"][logintoken].ga_obj
    ga_obj.send_page_view('/testshopping', 'testshopping')

    platform = recvdata.get('platform')
    content = recvdata.get('content')
    shopid = recvdata.get('shopid')

    if None in [memberid, platform,shopid]:
        commandresult = pg_general.Packagestatuscode.membererror
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            "testshopping_msghandler memberid,platform,shopid error, logintoken:{0}, recvdata:{1}".format(logintoken,
                                                                                                    recvdata))
        return clientdata, returncommandid, commandresult

    # 發送request到apiserver
    # serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)
    commandresult = pg_general.Packagestatuscode.success


    if platform ==0 or platform == 1:
        if shopid[:4] == 'shop':
            clientdata ={
                "result": 0,
                "buycredit": 1000000,
                "credit": 1900000,
                "content": {}
            }
        else:       # secret offer
            clientdata = {
                "result": 0,
                "buycredit": 1000000,
                "credit": 1900000,
                "content": {}
            }
    elif platform == 2:
        clientdata = {
            "result":1,
            "credit":0
        }



    # 檢查結果
    if commandresult == pg_general.Packagestatuscode.success:
        if len(clientdata) == 0:
            commandresult = pg_general.Packagestatuscode.commanderror
            clientdata = {}

    return clientdata, returncommandid, commandresult

async def backtohall_future(app,redis,memberid,logintoken,gamelogdataindex,seat_data):
    # 發送request到apiserver
    realurl = apiserver + '/backtohall/{0}/{1}/?gamelogdataindex={2}&seatdata={3}'.format(memberid, logintoken,gamelogdataindex,seat_data)
    serverdata, clientdata, commandresult = await getapiresult(logintoken, realurl)

    return




commandlist = {1000000: serverinfo_msghandler,
               1000001: login_msghandler,
               1000002: getmemberinfo_msghandler,
               1000006: updateprofile_msghandler,
               1000009: getdailybonusinfo_msghandler,
               1000010: spindailybonus_msghandler,
               1000018: getpiggyinfo_msghandler,
               1000019: getmallinfo_msghandler,
               1000020: shopping_msghandler,
               1000021: getinboxinfo_msghandler,
               1000022: receiveinbox_msghandler,
               1000023: feedback_msghandler,
               1000025: getgamelist_msghandler,
               # 1000026: joingame_msghandler,  棄用
               1000027: getgamerank_msghandler,
               1000028: getleaderrank_msghandler,
               1000031: sendchat_msghandler,
               1000033: getsettingcontent_msghandler,
               1000034: testshopping_msghandler,
               1000035: getsecretmall_msghandler,
               1000036: senddownloadsignal_msghandler,
               1000038: getpiggycredit_msghandler,
               1000039: getfriendlist_msghandler,
               1000040: getblacklist_msghandler,
               1000041: updatefriendlist_msghandler,
               1000042: updateblacklist_msghandler,
               1000043: openprivatechatroom_msghandler,
               1000044: safetask_msghandler,
               1000045: serialinput_msghandler,
               1000046: makelike_msghandler,
               1000047: sendprivatchat_msghandler,
               1000048: sendphonevalidate_msghandler,
               1000049: feedbackvalidatecode_msghandler,
               1000050: getgiftdata_msghandler,
               1000051: getcardinfo_msghandler,
               1000052: getchannellist_msghandler,
               1000053: getchannelmember_msghandler,
               1000054: joinchannel_msghandler,
               1000055: receivegift_msghandler,
               1000056: rejectgift_msghandler,
               1000057: sendchannelchat_msghandler,
               1000058: sendservicechat_msghandler,
               1000059: sendgift_msghandler,
               1000060: sendgiftsms_msghandler,
               1000061: creditexchange_msghandler,
               1000062: pointtocredit_msghandler,
               1000063: getfreeboxstatus_msghandler,
               1000064: receivefreebox_msghandler,
               1000065: forgetpasssms_msghandler,
               1000066: changenewpassword_msghandler,
               1000067: bindusername_msghandler,
               1000068: updatemembermessage_msghandler,
               1000069: reportmember_msghandler,
               1000070: actionframe_msghandler,
               1000072: restoreIAP_msghandler,
               1000073: getselfrankgamesort_msghandler,
               1000074: getavatarlist_msghandler,
               1000075: setavatarfromlist_msghandler,
               1000076: getseatsinfo_msghandler,
               1000077: joingameseat_msghandler,
               1000078: backtohall_msghandler,
               1000079: getnewdragontigerrank_msghandler,
               1000080: getnewtotalrank_msghandler,
               1000081: getselfrankgamesortnew_msghandler,
               1000082: getmemberinfolessdata_msghandler,
               1000083: getboxinfo_msghandler,
               1000084: buybox_msghandler,
               1000085: skiptutorial_msghandler,
               1000086: gettutorialguide_msghandler,
               1000087: joinfishgame_msghandler


               }