import asyncio
import aiomysql
import os
import env_setting
import pg_general
import random
import json
from datetime import timedelta, datetime
# from pg_fbavatar import PG_FBAVATAR
import pg_fbavatar
import aiohttp.web
import pg_namesample
from hanziconv import HanziConv
from random import seed
from random import randint
import pg_sms
import re
from pg_general import SendMsgType
import Gash
import suds.client as sudscl
import ECPay
import urllib.parse
import importlib.util
import applesignin
import calendar

if env_setting.LOCAL_SERVER == True:
    ECPAY_SDK_PATH = "ecpay_payment_sdk.py"
else:
    ECPAY_SDK_PATH = os.path.dirname(os.path.abspath(__file__)) + "//ecpay_payment_sdk.py"

spec = importlib.util.spec_from_file_location(
    "ecpay_payment_sdk",
    ECPAY_SDK_PATH
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ecpay_payment_sdk = module.ECPayPaymentSdk(
    MerchantID = ECPay.MerchantID,
    HashKey = ECPay.HashKey,
    HashIV = ECPay.HashIV
)


from pg_redis import PGRedis , DEFAULT_EXPIRE_SECONDS

if env_setting.LOCAL_SERVER == True:
    DB_HOST = '35.234.43.196'
    DB_HOST_READ = '35.234.43.196'
else:
    if env_setting.PRODUCTION_MODE == False:
        DB_HOST = '10.46.192.16'
        DB_HOST_READ = '10.46.192.16'
    else:
        DB_HOST = '10.46.192.18'
        DB_HOST_READ = '10.46.192.20'

DB_USER = 'root'
DB_NAME = 'slotwarapp'
if env_setting.PRODUCTION_MODE == False:
    DB_PASSWORD = 'Ck31uNv6gjflma5p'
else:
    DB_PASSWORD = '1EHhbNow3yxKcEmD'

# if env_setting.PRODUCTION_MODE == True:
#     CLOUDSQL_CONNECTION_NAME = 'playgemsforfunbackend:us-east1:production-slotwar'
#     CLOUDSQL_CONNECTION_NAME_READ = 'playgemsforfunbackend:us-east1:production-slotwar-replica'
# else:
#     CLOUDSQL_CONNECTION_NAME = 'playgemsforfunbackend:asia-east1:slotbackend'
#     CLOUDSQL_CONNECTION_NAME_READ = 'playgemsforfunbackend:asia-east1:slotbackend-replica'



IOS_IAP_VALIDATE_URL_SANDBOX = 'https://sandbox.itunes.apple.com/verifyReceipt'
IOS_IAP_VALIDATE_URL = 'https://buy.itunes.apple.com/verifyReceipt'


BUNDLE_ID_IOS = 'com.slots.casino.jinsong'
BUNDLE_ID_ANDROID = 'com.slots.casino.jinsong'




if env_setting.LOCAL_SERVER:
    AUTH_GOOGLE_IAP_FILE = "api-5948518497852894469-486172-a6232afe0253.json"
else:
    AUTH_GOOGLE_IAP_FILE = os.path.dirname(os.path.abspath(__file__)) + "//api-5948518497852894469-486172-a6232afe0253.json"



import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
GOOGLE_IAP_CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(AUTH_GOOGLE_IAP_FILE,scopes='https://www.googleapis.com/auth/androidpublisher')
GOOGLE_IAP_SERVICE = googleapiclient.discovery.build("androidpublisher", "v3",  credentials=GOOGLE_IAP_CREDENTIALS)
GOOGLE_IAP_BUNDLE_ID = "com.slots.casino.jinsong"
# result = GOOGLE_IAP_SERVICE.purchases().products().get(packageName=GOOGLE_IAP_BUNDLE_ID, productId="shop_lv_04", token="fnbdbnppcfppkfhembnoncdp.AO-J1OzLi2HbKFUKK95ZUhI5CmYvdXXjTNrnBtjh0CilcAh2DbaJPixeTdN_bbDfFoi9qye4IDTKHTdO4Vj5BBAKoj8s9uhZdHaXcG8aUEEofBGwqMWAkx6q6jDD3cRsOOaoTb2gN3TX").execute()
#



class PG_ASQLDB:

    async def createpool(self):
        try:

            if not env_setting.LOCAL_SERVER:
                # cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)
                # cloudsql_unix_socket_read = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME_READ)

                # self.pool = await aiomysql.create_pool(unix_socket=cloudsql_unix_socket, port=3306, user=DB_USER,
                #                                        password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
                self.pool = await aiomysql.create_pool(host=DB_HOST, port=3306, user=DB_USER,
                                                       password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

                pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                    "pg_asqldb:createpool: main db create pool done")

                # self.pool_read = await aiomysql.create_pool(unix_socket=cloudsql_unix_socket_read, port=3306, user=DB_USER,
                #                                        password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

                self.pool_read = await aiomysql.create_pool(host=DB_HOST_READ, port=3306, user=DB_USER,
                                                            password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
                pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                    "pg_asqldb:createpool: repplication db create pool done")
            else:
                self.pool = await aiomysql.create_pool(host=DB_HOST, port=3306, user=DB_USER,
                                                       password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

                self.pool_read = await aiomysql.create_pool(host=DB_HOST_READ, port=3306, user=DB_USER,
                                                       password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                "pg_asqldb:createpool except: {0}".format(e))
    async def closepool(self):
        await self.pool.close()
        await self.pool.wait_closed()

        await self.pool_read.close()
        await self.pool_read.wait_closed()

    async def getdbdata(self, logintoken, command=None, fetchall=False,fromwritedb=False):
        datalen = -1
        data = None
        if command is None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:getdbdata:command=None logintoken:{0}".format(logintoken))
            return datalen, data

        connectionpool = None
        if fromwritedb == True:
            connectionpool = self.pool
        else:
            connectionpool = self.pool_read

        errcount = 0
        for _errcount in range(3):
            try:
                async with connectionpool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cur:
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            "pg_asqldb:getdbdata:execute command:{0}, logintoken:{1}".format(command,
                                                                                                             logintoken))
                        datarows = await cur.execute(command)
                        if datarows == 0:
                            datalen = 0
                        else:
                            if fetchall == True:
                                data = await cur.fetchall()
                                datalen = len(data)

                            else:
                                data = await cur.fetchone()
                                datalen = 1
                        await cur.close()
                #connectionpool.release(conn)
                break
            except Exception as e:
                errcount += 1
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:getdbdata exception:{0}, command:{1}, logintoken:{2},errcount:{3}'.format(e, command,
                                                                                                            logintoken,errcount))
                await asyncio.sleep(0)

        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            "pg_asqldb:getdbdata:finally datalen:{0}, data:{1}, logintoken:{2}".format(datalen,
                                                                                                       data,
                                                                                                       logintoken))
        return datalen, data

    async def insertdbdata(self, logintoken, command=None,many=False,manydata=[]):
        result = False
        index = 0
        if command is None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:insertdbdata:command=None logintoken:{0}".format(logintoken))
            return result, index
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        "pg_asqldb:insertdbdata:execute command:{0}, logintoken:{1}".format(command,
                                                                                                            logintoken))
                    if many==False:
                        datarows = await cur.execute(command)
                    elif many==True:
                        datarows = await cur.executemany(command,manydata)
                    await conn.commit()
                    index = cur.lastrowid
                    result = True
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:insertdbdata exception:{0}, command:{1}, logintoken:{2}'.format(e, command,
                                                                                                           logintoken))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_asqldb:insertdbdata:finally result:{0}, index:{1}, logintoken:{2}".format(result,
                                                                                                              index,
                                                                                                              logintoken))
            return result, index

    async def updatedbdata(self, logintoken, command=None):
        result = False
        if command is None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:updatedbdata:command=None logintoken:{0}".format(logintoken))
            return result
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        "pg_asqldb:updatedbdata:execute command:{0}, logintoken:{1}".format(command,
                                                                                                            logintoken))
                    datarows = await cur.execute(command)
                    await conn.commit()
                    result = True
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatedbdata exception:{0}, command:{1}, logintoken:{2}'.format(e, command,
                                                                                                           logintoken))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_asqldb:updatedbdata:finally result:{0}, logintoken:{1}".format(result, logintoken))
            return result


    async def updatedbdata_affectrows(self,logintoken,command = None):
        affectrows = 0
        if command is None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:updatedbdata_affectrows:command=None logintoken:{0}".format(logintoken))
            return affectrows
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        "pg_asqldb:updatedbdata_affectrows:execute command:{0}, logintoken:{1}".format(command,
                                                                                                            logintoken))
                    datarows = await cur.execute(command)
                    await conn.commit()
                    affectrows = datarows
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatedbdata_affectrows exception:{0}, command:{1}, logintoken:{2}'.format(e, command,
                                                                                                           logintoken))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_asqldb:updatedbdata_affectrows:finally datarows:{0}, logintoken:{1}".format(affectrows, logintoken))
            return affectrows


    async def getserverinfo(self, logintoken,ver=None,rer=None,platform=None):
        """
        取得伺服器狀態
        從DB serverinfo 撈取serverstate和resourceuri
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:getserverinfo logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror

        clientdata = {}


        command = 'select * from serverinfo'
        datalen, data = await self.getdbdata(logintoken, command)
        if datalen > 0:
            serverstate = pg_general.converttype(data.get('serverstate'), int)
            resourceserveruri = pg_general.converttype(data.get('resourceuri'), str)
            command = 'select updatestoremessage_title,updatestoremessage_detail, androidver, iosver,androidurl,iosurl,rerobject,rerobjectnew from setting2'
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen > 0:
                update_message_title = data.get('updatestoremessage_title')
                update_message_detail = data.get('updatestoremessage_detail')
                androidver = data.get('androidver')
                iosver = data.get('iosver')
                androidurl = data.get('androidurl')
                iosurl = data.get('iosurl')
                rerobject = json.loads(data.get('rerobject'))
                rerobjectnew = json.loads(data.get('rerobjectnew'))

                isnewversion = False
                needask = True

                if ver is not None and rer is not None:
                    if platform is None: # old version
                        if len(ver.split('.')) == 3 and len(rer.split('.')) == 3:
                            tempver = rerobjectnew.get(ver)
                            if tempver is not None:
                                temprer= tempver.get(rer)
                                if temprer is not None:
                                    if temprer.get('rer') is not None and temprer.get('size') is not None:
                                        isnewversion = True
                                        tempneedask = temprer.get('needask')
                                        if tempneedask is None:
                                            needask = True
                                        else:
                                            needask = tempneedask

                                        rerdata = {
                                            ver: {  "rer": temprer.get('rer'),
                                                    "rersize": temprer.get('size')
                                                }
                                        }
                    else:   # new version with  ios and android seperate
                        if platform == 0: # ios
                            rerobjectnew = rerobjectnew.get('ios')
                        else:               # android
                            rerobjectnew = rerobjectnew.get('android')

                        if rerobjectnew is not None:
                            if len(ver.split('.')) == 3 and len(rer.split('.')) == 3:
                                tempver = rerobjectnew.get(ver)
                                if tempver is not None:
                                    temprer= tempver.get(rer)
                                    if temprer is not None:
                                        if temprer.get('rer') is not None and temprer.get('size') is not None:
                                            isnewversion = True
                                            tempneedask = temprer.get('needask')
                                            if tempneedask is None:
                                                needask = True
                                            else:
                                                needask = tempneedask

                                            rerdata = {
                                                ver: {  "rer": temprer.get('rer'),
                                                        "rersize": temprer.get('size')
                                                    }
                                            }

                # tips
                tips = []
                command = 'select * from loadingtips'
                datalen , data = await self.getdbdata(logintoken,command,True)
                if datalen > 0:
                    for item in data:
                        tips.append(item.get('tips'))


                clientdata = {
                    'serverstate': serverstate,
                    'resourceserveruri': resourceserveruri,
                    'message_title': update_message_title,
                    'message_detail': update_message_detail,
                    'androidver': androidver,
                    'iosver': iosver,
                    'androidurl': androidurl,
                    'iosurl': iosurl,
                    'rerobject': rerobject if isnewversion == False else rerdata,
                    'needask': needask,
                    'tips': tips
                }
                result = pg_general.Apiresult.success

        else:
            result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getserverinfo result:{0}, clientdata:{1}, logintoken:{2}'.format(result, clientdata, logintoken))
        return result, clientdata

    async def write_redis_member_join_channel_future(self,redis_obj, memberid, channel,expiretime=180):
        try:
            # 先抓取 member channel info
            oldchannel = await redis_obj.get_all_keys('channel_*_{}'.format(memberid))
            if len(oldchannel) > 0:  # 如果有存在加入的 channel 則刪除舊有的 data
                for item in oldchannel:
                    await redis_obj.del_key(item)

            await redis_obj.set_value('channel_{}_{}'.format(channel, memberid), str(1),expiretime)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'write_redis_member_join_channel_future memberid:{0},channel:{1}'.format(memberid,
                                                                                                         channel))

    async def login(self, redis_obj,fblink,defaultchannelindex,fbavatarobj,logintoken, deviceid, fbid,fbtoken,fbavatar,fbnickname, ip, platform, devicedescription,lobbyserverip,region,region_sub,city,fcmtoken,ver=None,rer=None,username=None,password=None,newaccflag=None,connecttype=None,auserid=None,aauthcode=None,atoken=None):
        """
        登入
        先找出memberid (參照 function findmemberidandlasttoken) 找不到memberid則建立新會員 (參照 function createmember)
        有memberid後更新DB登入資料 (參照 function updatememberlogin)
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:login logintoken:{0}, deviceid:{1}, fbid:{2},'
                                                            'fbtoken:{3},ip:{4}, platform:{5}, devicedescription:{6},lobbyserverip:{7},'
                                                            'fbavatar:{8},fbnickname:{9},fcmtoken:{10},username:{11},password:{12},newaccflag:{13}'.format(logintoken, deviceid,
                                                            fbid,fbtoken, ip, platform, devicedescription,lobbyserverip,fbavatar,fbnickname,fcmtoken,username,password,newaccflag))

        totalresult = pg_general.Apiresult.connectdberror # test
        try:
            clientdata = {}
            serverdata = {}

            memberresult = pg_general.Apiresult.connectdberror
            memberid = None
            createresult = None

            registerflag = 0

            # 檢查 data
            if newaccflag == 1:
                confirmresult = await self.confirmregisterdata(logintoken,username,password)
                if confirmresult == False:
                    totalresult = pg_general.Apiresult.success
                    clientdata= {
                        "result": 5
                    }
                    return totalresult, clientdata, serverdata
                # use username create member
                createresult, creatememberid = await self.createmember_by_username(deviceid, platform, logintoken,username,password)
                if createresult == pg_general.Apiresult.success:
                    memberid = creatememberid
                    registerflag = 1        # 註冊成功
                elif createresult == pg_general.Apiresult.duplicationacc:
                    totalresult = pg_general.Apiresult.success
                    clientdata = {
                        "result": 4
                    }
                    return totalresult, clientdata, serverdata


            # 找memberid
            memberidresult, getmemberid, lasttoken,otherdata,loginmethod = await self.findmemberidandlasttoken(deviceid, fbid, logintoken,username,password,auserid,aauthcode,atoken)
            if memberidresult == pg_general.Apiresult.success:
                memberid = getmemberid
            elif memberidresult == pg_general.Apiresult.dbnodata:
                # 找不到memberid 新增會員
                createresult, creatememberid = await self.createmember(deviceid, platform, logintoken)      # create member by deviceid
                if createresult == pg_general.Apiresult.success:
                    memberid = creatememberid
                    registerflag = 1    # 註冊成功
            elif memberidresult == pg_general.Apiresult.accountfreeze:      # 帳號凍結
                totalresult = pg_general.Apiresult.success
                serverdata = {
                    "memberid": getmemberid
                }
                clientdata = {
                    "result": 3
                }
                return totalresult,clientdata,serverdata
            elif memberidresult == pg_general.Apiresult.accpasserror:  # 帳號或是密碼錯誤
                totalresult = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return totalresult, clientdata, serverdata
            elif memberidresult ==  pg_general.Apiresult.hasusernameacc:    # 使用　fb 登入的時候有查到　此　deviceid 已經綁定 username
                totalresult = pg_general.Apiresult.success
                clientdata = {
                    "result": 6
                }
                return totalresult, clientdata, serverdata
            elif memberidresult == pg_general.Apiresult.hasanotherfbid:        # 使用 fb 登入的時候有查到此 deviceid 已經綁過 fbid
                totalresult = pg_general.Apiresult.success
                clientdata = {
                    "result": 7
                }
                return totalresult, clientdata, serverdata
            elif loginmethod is None:
                totalresult = pg_general.Apiresult.connectdberror
                raise ValueError('loginmethod is None')


            # 到這邊應該要有 memberid 如果沒有的話, 就讓玩家斷線
            if memberid is None:
                totalresult = pg_general.Apiresult.connectdberror
                clientdata = {}
                serverdata = {}
                return totalresult, clientdata, serverdata


            # 判斷此帳號之前沒有斷線做斷線處理
            if lasttoken is not None:
                updatememberlogoutresult = await self.updatememberlogout(memberid, lasttoken)


            # 抓是否有改過 avatar
            command = 'select isavatarchanged from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command,False,True)
            isavatarchanged = 0
            if datalen ==1:
                isavatarchanged = data.get('isavatarchanged')


            # 判斷 fbtoken 是否正確　跟 graph api 確認
            fbemail = ''

            # 如果有 fbid data and 有創帳號 當作是 fblogin method
            if fbtoken is not None and createresult == pg_general.Apiresult.success:
                loginmethod = 2
            # 如果有 auserid and 有創帳號 當作是 apple sign in method
            if auserid is not None and createresult == pg_general.Apiresult.success:
                loginmethod = 4

            # 抓取 fbuser email
            if fbtoken is not None and loginmethod ==2:
                if fbtoken != '':
                    fbuserresult, fbuserdata = await fbavatarobj.getfbdata(logintoken,memberid,fbtoken)
                    if fbuserresult != pg_general.Apiresult.success:
                        raise ValueError('fblogin error')
                    fbemail = fbuserdata.get('email')
                    if fbemail is None:
                        fbemail = ''

                # 更換 fbavatar
            if fbid is not None and fbid != "" and fbavatar is not None and fbavatar != "" and loginmethod == 2:
                fbavatar_result, avatarurl = await fbavatarobj.upload_avatar(memberid, fbavatar)
                if fbavatar_result == True and avatarurl != "":
                    fbavatar = avatarurl
                else:
                    fbavatar = pg_fbavatar.AVATAR_FB_DEFAULT

            # 更新member 登入資料更新資料
            updateloginresult , otherdict = await self.updatememberlogin(memberid, deviceid, fbid,fbtoken,fbavatar,fbnickname,fbemail,
                                                             ip, platform, devicedescription, logintoken,lobbyserverip,region,region_sub,city,fcmtoken,otherdata,ver,rer,loginmethod,username,connecttype,isavatarchanged,auserid,aauthcode,atoken)





            if updateloginresult == pg_general.Apiresult.success:
                memberresult = pg_general.Apiresult.success

            if memberresult != pg_general.Apiresult.success: # member 處理完後 先判斷一次 如果 memberresult 出錯則跳Except返回
                raise ValueError('1')




            getmemberinforesult , data = await self.getmemberinfo(redis_obj,logintoken,memberid)
            if getmemberinforesult != pg_general.Apiresult.success: # getmemberinfo 如果出錯 except 返回
                raise ValueError('getmemberinfo error memberid:{0},logintoken:{1}'.format(memberid,logintoken))

            activenumber = data.get('activenumber')
            avatar = data.get('avatar')
            exppercent = data.get('exppercent')
            exppercent = 100 if exppercent > 100 else exppercent
            credit = data.get('credit')
            silvercredit = data.get('silvercredit')
            level = data.get('level')
            exptonextlevel = data.get('exptonextlevel')
            maxbet = data.get('maxbet')
            channel = data.get('channel')
            card = data.get('card')
            nickname = data.get('nickname')
            isbindfb = data.get('isbindfb')
            isbindphone = data.get('isbindphone')
            isbindacc = data.get('isbindacc')
            isfirstbuy = data.get('isfirstbuy')
            registrationdatetime = data.get('registrationdatetime')
            needtutorialflag = data.get('needtutorialflag')
            if None in [avatar,exppercent,credit,level,exptonextlevel,maxbet,isfirstbuy]:        # 都要有資料
                raise ValueError('4')

            firstbuymalldata= {}
            firstbuymalldata = await self.getfirstbuymallinfo(logintoken,memberid)

            firstbuymallinfo = firstbuymalldata.get('firstbuymallinfo')
            firstbuycountdownsec = firstbuymalldata.get('firstbuycountdownsec')
            firstbuytotalpercent = firstbuymalldata.get('firstbuytotalpercent')

            now = pg_general.getutcnow_datetime()
            firstbuydifftime = pg_general.converttype(firstbuycountdownsec - (now - registrationdatetime).total_seconds(),int)
            if firstbuydifftime <0:
                firstbuydifftime = 0

            getdailybonusinforesult , data = await self.getdailybonusinfo(logintoken,memberid)
            if getdailybonusinforesult != pg_general.Apiresult.success:
                raise ValueError('11')

            isspin = data.get('isspin')
            if isspin is None:
                raise ValueError('12')


            # reddot 通知
            reddot = []
            getreddotresult , data = await self.getreddotinfo(logintoken,memberid)
            reddot = data


            # feedbacktype
            feedbacktyperesult , data = await self.getfeedbacktype(logintoken,memberid)
            if feedbacktyperesult != pg_general.Apiresult.success:
                raise ValueError('16')

            feedbacktype = data.get('feedbacktype')

            # get announcement
            getannoucementresult , data = await self.getannouncement()
            if getannoucementresult != pg_general.Apiresult.success:
                raise ValueError('17')

            announcementdict = data

            getspecialactionimageresult , data = await self.getspecialaction(logintoken,memberid)

            specialactionurlnew = []
            tempspecialactionurlnew = data.get('specialactionurlnew')
            if tempspecialactionurlnew is not None:
                tempspecialactionurlnew = tempspecialactionurlnew.strip()
                if len(tempspecialactionurlnew)>0:
                    specialactionurlnew = tempspecialactionurlnew.split(',')



            totalresult = pg_general.Apiresult.success

            if channel ==0:
                channel = defaultchannelindex
                command = 'update member set channel="{0}" where memberid = "{1}"'.format(channel,memberid)
                await self.updatedbdata(logintoken,command)

            # 抓 setting.bindphonereward and weburl and firstbuyflag
            command = 'select mallserialcount,bindphonereward,weburl,firstbuyflag from setting2'
            datalen , data = await self.getdbdata(logintoken,command)

            bindphonereward = 0
            weburl = ''
            firstbuyflag = 0
            mallserialcount = 0
            if datalen ==1:
                bindphonereward = data.get('bindphonereward')
                weburl = data.get('weburl')
                firstbuyflag = data.get('firstbuyflag')
                mallserialcount = data.get('mallserialcount')

            lobbyaction = []
            # 抓 lobbyaction
            command = 'select * from lobbyaction'
            datalen, data = await self.getdbdata(logintoken,command,True)
            if datalen > 0:
                for item in data:
                    posid = item.get('posid')
                    picurl = item.get('picurl')
                    tempcontent = json.loads(item.get('content'))
                    actiontype = tempcontent.get('actiontype')
                    pageid = None
                    posindex = None
                    openurl = None
                    if actiontype == 0: # internal page
                        pageid = tempcontent.get('pageid')
                        if pageid == 3:
                            posindex = tempcontent.get('posindex')
                    elif actiontype ==1:    # open url
                        openurl = tempcontent.get('openurl')

                    tempdict = {}
                    tempdict['posid'] = posid
                    tempdict['picurl'] = picurl
                    tempdict['actiontype'] = actiontype
                    if pageid is not None:
                        tempdict['pageid'] = pageid
                    if posindex is not None:
                        tempdict['posindex'] = posindex
                    if openurl is not None:
                        tempdict['openurl'] = openurl
                    lobbyaction.append(tempdict)

            # 重新對 lobbyaction 排序
            if len(lobbyaction) > 0:
                lobbyaction = sorted(lobbyaction, key=lambda k: (k['posid']), reverse=False)

            # 強制關閉首購
            if firstbuyflag ==0:
                isfirstbuy = 0

            # 不需要首購, 強制時間設定 = 0
            if isfirstbuy == 0:
                firstbuydifftime = 0

            # 抓 actionnumbers  from action table
            nowutcdattime = pg_general.getutcnow_datetime()
            command = 'select distinct(actionnumber) as actionnumber from action where starttime <= "{0}" and (endtime>="{0}" or endtime is null) and listtype = "0" order by listtype,listpos,contentpos'.format(nowutcdattime)
            datalen, data = await self.getdbdata(logintoken,command,True)

            if datalen > 0:
                actionnumbers = [item.get('actionnumber') for item in data]

            clientdata = {
                "result": 0,
                "registerflag": registerflag,
                "activenumber": activenumber,
                "avatar": avatar,
                "credit": credit,
                "silvercredit": silvercredit,
                "level": level,
                "card": card,
                "nickname": nickname,
                "exppercent": exppercent,
                "isspin": isspin,
                "reddot": reddot,
                "feedbacktype": feedbacktype,
                "logintoken": logintoken,
                "memberid": pg_general.converttype(memberid,str),
                "maxbet": maxbet,
                "exptonextlevel": exptonextlevel,
                "fblink": fblink,
                "announcement": announcementdict,
                "isbindfb": isbindfb,
                "isbindacc": isbindacc,
                "isbindphone": isbindphone,
                "specialactionurlnew": specialactionurlnew,
                "channel": channel,
                "bindphonereward": bindphonereward,
                "weburl": weburl,
                "lobbyaction": lobbyaction,
                "isfirstbuy": isfirstbuy,
                "firstbuycountdownsec": firstbuydifftime,
                "firstbuytotalpercent": firstbuytotalpercent,
                "firstbuymallinfo": firstbuymallinfo,
                "actionnumbers": actionnumbers,
                "mallserialcount": mallserialcount,
                "needtutorialflag": needtutorialflag
            }

            await self.write_redis_member_join_channel_future(redis_obj,memberid,channel)

            serverdata = {
                "memberid": memberid
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:login ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:login exception:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:login totalresult:{0}, clientdata:{1}, serverdata:{2}, logintoken:{3}'.format(totalresult, clientdata, serverdata, logintoken))

            return totalresult, clientdata, serverdata



    async def getfeedbacktype(self,logintoken,memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getfeedbacktype logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        # initial vars
        feedbacktype = []

        clientdata = {}
        command = 'select * from feedbacktype order by id'

        datalen, data = await self.getdbdata(logintoken, command, True)

        if datalen > 0:
            for item in data:
                feedbacktype.append(item)

        clientdata = {
            "result": 0,
            "feedbacktype" : feedbacktype
        }
        result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:gettipsinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                      logintoken,
                                                                                                      clientdata))
        return result, clientdata

    async def findmemberidandlasttoken(self, deviceid, fbid, logintoken,username,password,auserid,aauthcode,atoken):
        """
        找memberid和最後登入的token
        從DB member 撈取memberid和logintoken
        membeid的規則 fbid優先度大於deviceid
        因此先利用fbid反查memberid
        找不到時再用deviceid反查memberid
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:findmemberid logintoken:{0}, deviceid:{1}, fbid:{2},username:{3},password:{4},auserid:{5},aauthcode:{6},atoken:{7}'.format(logintoken, deviceid, fbid,username,password,auserid,aauthcode,atoken))
            result = pg_general.Apiresult.connectdberror
            memberid = None
            lasttoken = None
            otherdata={}
            isbindfb = None

            loginmethod = None   # 1: username , 2: fb , 3: deviceid , 4: app sign in

            if username is not None:
                username = username.strip()
            if password is not None:
                password = password.strip()


            # 找memberid(username>fbid>deviceid)
            if None not in [username,password]:
                # user username & password to find memberid
                command = 'select * from member where username ="{0}"'.format(username)
                datalen , data = await self.getdbdata(logintoken, command,False,True)
                if datalen != 1:
                    result = pg_general.Apiresult.accpasserror
                    return result, memberid, lasttoken, otherdata
                elif datalen <0:
                    result = pg_general.Apiresult.connectdberror
                    raise ValueError('get data error')
                else:
                    userpassword = data.get('password')
                    enable = data.get('enable')
                    getmemberid = pg_general.converttype(data.get('memberid'), int)
                    lasttoken = data.get('logintoken')
                    isbindfb = data.get('isbindfb')


                    if enable != 1:         # 帳戶凍結
                        result = pg_general.Apiresult.accountfreeze
                        memberid = getmemberid
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if userpassword != password: # 密碼錯誤
                        result = pg_general.Apiresult.accpasserror
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if getmemberid is not None:
                        memberid = getmemberid
                        result = pg_general.Apiresult.success
                        loginmethod = 1
            elif fbid is not None:
                # 用fbid找memberid
                command = 'select * from member where fbid = "{0}"'.format(fbid)
                datalen, data = await self.getdbdata(logintoken, command)

                if datalen == 1:
                    enable = data.get('enable')
                    getmemberid = pg_general.converttype(data.get('memberid'), int)
                    lasttoken = data.get('logintoken')
                    isbindfb = data.get('isbindfb')


                    if enable != 1:         # 帳戶凍結
                        result = pg_general.Apiresult.accountfreeze
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if getmemberid is not None:
                        memberid = getmemberid
                        result = pg_general.Apiresult.success
                        loginmethod =2
            elif None not in [auserid,aauthcode,atoken]:        # apple sign in
                # 確認 data 正確性
                confirmresult,confirmdata = await applesignin.apple_sign_in_check(logintoken,auserid,atoken,aauthcode)

                if confirmresult == False:
                    result = pg_general.Apiresult.othererror
                    return result, memberid, lasttoken, otherdata, loginmethod

                command = 'select * from member where auserid="{0}"'.format(auserid)
                datalen , data = await self.getdbdata(logintoken,command)
                if datalen ==1:
                    enable = data.get('enable')
                    getmemberid = pg_general.converttype(data.get('memberid'),int)
                    lasttoken = data.get('logintoken')
                    isbindfb = data.get('isbindfb')

                    if enable != 1:         # 帳戶凍結
                        result = pg_general.Apiresult.accountfreeze
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if getmemberid is not None:
                        memberid = getmemberid
                        result = pg_general.Apiresult.success
                        loginmethod = 4

            # 用deviceid找memberid
            if memberid is None:
                command = 'select * from member where lastdeviceid = "{0}"'.format(deviceid)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen == 1:
                    enable = data.get('enable')
                    confirmusername = data.get('username')
                    getmemberid = pg_general.converttype(data.get('memberid'), int)
                    lasttoken = data.get('logintoken')
                    isbindfb = data.get('isbindfb')

                    confirmfbid = data.get('fbid')
                    if enable != 1: # 凍結
                        result = pg_general.Apiresult.accountfreeze
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if confirmusername is not None and confirmusername != '' and fbid is not None: # 找不到 fbid 但是有找到 deviceid and username 表示之前有使用 username 綁過此帳號
                        result = pg_general.Apiresult.hasusernameacc
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if confirmfbid is not None and fbid is not None:
                        if len(confirmfbid) > 1:
                            result = pg_general.Apiresult.hasanotherfbid
                            return result, memberid, lasttoken, otherdata, loginmethod


                    if getmemberid is not None:
                        memberid = getmemberid
                        result = pg_general.Apiresult.success
                        loginmethod = 3
                elif datalen == 0:
                    result = pg_general.Apiresult.dbnodata
            if None not in [memberid]:          # 有找到加入otherdata
                otherdata ={
                    "isbindfb" : isbindfb

                }
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:findmemberid ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:findmemberid exception:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:findmemberid result:{0}, memberid:{1}, logintoken:{2},otherdata:{3}'.format(result, memberid, logintoken,otherdata))
            return result, memberid, lasttoken,otherdata,loginmethod

    async def createmember_by_username(self, deviceid, platform, logintoken,username,password):
        """
        建立新會員
        DB member insert 一筆會員資料
        有memberid後再建立其他與會員相關的table (參照 function createothermembertable)
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:createmember logintoken:{0}, deviceid:{1}, platform:{2},username:{3},password:{4}'.format(logintoken, deviceid, platform,username,password))

        result = pg_general.Apiresult.connectdberror
        memberid = None



        now = pg_general.getutcnow()
        nowdatetime = pg_general.strtodatetime(now)
        yesterday = nowdatetime - timedelta(days=1)

        insertkey = 'registrationdatetime, lastlogintime, adcountdown, lastdeviceid, platform, logintoken, lastchoosecamp'
        insertvalue = ' "{0}", "{0}", "{0}", "{1}", "{2}", "{3}", "{4}"'.format(now, deviceid, platform, logintoken, yesterday)

        insertkey = insertkey + ',username,password'
        insertvalue = insertvalue + ',"{0}","{1}"'.format(username,password)

        command = 'insert into member({0}) values({1})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            memberid = index

            # 改一個預設的暱稱
            await pg_namesample.makeanewname(self,memberid)

            createresult = await self.createothermembertable(memberid, logintoken, nowdatetime)
            if createresult == pg_general.Apiresult.success:
                result = pg_general.Apiresult.success
        elif insertresult == False and username is not None:
            result = pg_general.Apiresult.duplicationacc



        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:createmember result:{0}, memberid:{1}, logintoken{2}'.format(
                                result, memberid, logintoken))
        return result, memberid


    async def createmember(self, deviceid, platform, logintoken):
        """
        建立新會員
        DB member insert 一筆會員資料
        有memberid後再建立其他與會員相關的table (參照 function createothermembertable)
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:createmember logintoken:{0}, deviceid:{1}, platform:{2}'.format(logintoken, deviceid, platform))

        result = pg_general.Apiresult.connectdberror
        memberid = None

        now = pg_general.getutcnow()
        nowdatetime = pg_general.strtodatetime(now)
        yesterday = nowdatetime - timedelta(days=1)

        insertkey = 'registrationdatetime, lastlogintime, adcountdown, lastdeviceid, platform, logintoken, lastchoosecamp'
        insertvalue = ' "{0}", "{0}", "{0}", "{1}", "{2}", "{3}", "{4}"'.format(now, deviceid, platform, logintoken, yesterday)

        command = 'insert into member({0}) values({1})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            memberid = index

            # 改一個預設的暱稱
            await pg_namesample.makeanewname(self,memberid)

            createresult = await self.createothermembertable(memberid, logintoken, nowdatetime)
            if createresult == pg_general.Apiresult.success:
                result = pg_general.Apiresult.success
        elif insertresult == False:
            result = pg_general.Apiresult.connectdberror



        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:createmember result:{0}, memberid:{1}, logintoken{2}'.format(
                                result, memberid, logintoken))
        return result, memberid


    async def createothermembertable(self, memberid, logintoken, nowdatetime):
        """
        建立其他與會員相關的table
        建立 DB memberdailybonus 會員每日登入
        建立 DB memberpiggyinfo 會員小豬
        建立DB memberfreecoins 會員資料
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:createothermembertable logintoken:{0}, memberid:{1}, nowdatetime:{2}'.format(logintoken, memberid, nowdatetime))

        result = pg_general.Apiresult.connectdberror
        insertcount = 0
        yesterday = nowdatetime - timedelta(days=1)

        # memberdailybonus
        insertkey = 'memberid, lastspintime'
        insertvalue = '"{0}", "{1}"'.format(memberid, yesterday)
        command = 'insert into memberdailybonus({0}) values({1})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            insertcount += 1

        # memberpiggyinfo
        insertkey = 'memberid, dateline'
        insertvalue = '"{0}", "{1}"'.format(memberid, yesterday)
        command = 'insert into memberpiggyinfo({0}) values({1})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            insertcount += 1


        # insertresult, index = await self.creatememberemptyquests(memberid,logintoken)
        # if insertresult == True:
        #     insertcount += 1

        # memberfreecoin
        command = 'insert into memberfreecoins (memberid,lastgettime) values ( {0},"{1}")'.format(memberid,yesterday)
        insertresult , index = await self.insertdbdata(logintoken , command)
        if insertresult == True:
            insertcount += 1



        if insertcount == 3:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:createothermembertable result:{0}, logintoken{1}'.format(result, logintoken))
        return result


    async def updatememberlogin(self, memberid, deviceid, fbid,fbtoken,fbavatar,fbnickname,fbemail, ip, platform, devicedescription, logintoken,lobbyserverip,region,region_sub,city,fcmtoken,otherdata,ver,rer,loginmethod,username,connecttype,isavatarchanged,auserid,aauthcode,atoken):
        """
        更新member登入資料
        DB member 更新member的logintoken 登入時間 登入裝置....
        存入 fbavatar , fbnickname into member(avatar,nickname)
        DB memberloginlog 新增一筆會員登入的時間
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:updatememberlogin logintoken:{0}, memberid:{1}, deviceid:{2}, fbid:{3}, ip:{4},' \
                            ' platform:{5}, devicedescription:{6},lobbyserverip:{7},region:{8},region_sub:{9},city:{10},fbtoken:{11},fbavatar:{12},fbnickname:{13},fcmtoken:{14}'.
                                    format(logintoken, memberid, deviceid, fbid, ip, platform, devicedescription,lobbyserverip,region,region_sub,city,fbtoken,fbavatar,fbnickname,fcmtoken))
        result = pg_general.Apiresult.connectdberror
        await asyncio.sleep(0)
        otherdict = {}

        isbindfb = 0

        if otherdata != {}:
            isbindfb = otherdata.get('isbindfb')



        now = pg_general.getutcnow()
        updatestr = 'lastlogintime="{0}", platform="{1}", logintoken="{2}",lobbyserverip="{3}"'.format(now, platform, logintoken,lobbyserverip)
        insertkey = 'memberid, logintime, platform, deviceid, logintoken,lobbyserverip'
        insertvalue = '{0}, "{1}", {2}, "{3}", "{4}","{5}"'.format(memberid, now, platform, deviceid, logintoken,lobbyserverip)

        if loginmethod != 2:
            updatestr = updatestr + ',lastdeviceid="{0}"'.format(deviceid)

        if auserid is not None:
            updatestr = updatestr + ',auserid="{0}"'.format(auserid)
            insertkey = insertkey + ', auserid'
            insertvalue = insertvalue + ', "{0}"'.format(auserid)

        if aauthcode is not None:
            updatestr = updatestr + ',aauthcode="{0}"'.format(aauthcode)
            insertkey = insertkey + ', aauthcode'
            insertvalue = insertvalue + ', "{0}"'.format(aauthcode)

        if atoken is not None:
            updatestr = updatestr + ',atoken="{0}"'.format(atoken)
            insertkey = insertkey + ', atoken'
            insertvalue = insertvalue + ', "{0}"'.format(atoken)

        if fbid is not None:
            updatestr = updatestr + ', fbid="{0}"'.format(fbid)
            updatestr = updatestr + ',isbindfb="1"'

        if fbtoken is not None:
            updatestr = updatestr + ',fbtoken="{0}"'.format(fbtoken)

        if isavatarchanged ==0: # 有改過不更換 avatar
            if fbavatar is not None:
                updatestr = updatestr + ',avatar="{0}"'.format(fbavatar)
            else:   # 如果沒有 fbavatar 表示沒有綁定 fb , avatar 設定 default avatar
                if isbindfb ==0:
                    updatestr = updatestr + ',avatar="{0}"'.format(pg_fbavatar.AVATAR_DEFAULT)

        if fbemail is not None and fbemail != '':
            updatestr = updatestr + ',email="{0}"'.format(fbemail)

        if fcmtoken is not None:
            updatestr = updatestr + ',fcmtoken="{0}"'.format(fcmtoken)

        if ip is not None:
            updatestr = updatestr + ', lastip="{0}"'.format(ip)
            insertkey = insertkey + ', ip'
            insertvalue = insertvalue + ', "{0}"'.format(ip)

        if region is not None:
            updatestr = updatestr + ',region="{0}"'.format(pg_general.converttype(region,str).lower())

        if devicedescription is not None:
            updatestr = updatestr + ', devicedescription="{0}"'.format(devicedescription)

        if region is not None:
            insertkey = insertkey + ',region'
            insertvalue = insertvalue + ',"{0}"'.format(region)

        if region_sub is not None:
            insertkey = insertkey + ',region_sub'
            insertvalue = insertvalue + ',"{0}"'.format(region_sub)

        if city is not None:
            insertkey = insertkey + ',city'
            insertvalue = insertvalue + ',"{0}"'.format(city)

        if ver is not None:
            updatestr = updatestr + ',ver="{0}"'.format(ver)
            insertkey = insertkey + ',ver'
            insertvalue = insertvalue + ',"{0}"'.format(ver)

        if rer is not None:
            updatestr = updatestr + ',rer="{0}"'.format(rer)
            insertkey = insertkey + ',rer'
            insertvalue = insertvalue + ',"{0}"'.format(rer)

        if loginmethod is not None:
            insertkey = insertkey + ',loginmethod,username'
            insertvalue = insertvalue + ',"{0}","{1}"'.format(loginmethod,username)

        if fbtoken is not None and fbid is not None:
            insertkey = insertkey + ',fbtoken,fbid'
            insertvalue = insertvalue + ',"{0}","{1}"'.format(fbtoken,fbid)

        if connecttype is not None:
            insertkey = insertkey + ',connecttype'
            insertvalue = insertvalue + ',"{0}"'.format(connecttype)


        # 更新member 資料表
        command = 'update member set {0} where memberid = "{1}"'.format(updatestr, memberid)
        updateresult = await self.updatedbdata(logintoken, command)

        # 新增memberloginlog 記錄
        command = 'insert into memberloginlog({0}) values({1})'.format(insertkey, insertvalue)
        insertresult, index = await self.insertdbdata(logintoken, command)

        if updateresult == True and insertresult == True:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:updatememberlogin result:{0}, logintoken:{1}'.format(result, logintoken))
        return result, otherdict

    async def updatememberlogout(self, memberid, logintoken):
        """
        更新member登出資料
        DB member 更新member的最後登出時間  及清空logintoken
        DB memberloginlog 更新登出時間
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:updatememberlogout logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
            result = pg_general.Apiresult.connectdberror

            now = pg_general.getutcnow()

            # 更新member 資料表
            command = 'update member set lastlogouttime="{0}",logintoken=null where memberid = "{1}"'.format(now, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            # 更新memberloginlog 記錄
            command = 'select * from memberloginlog where memberid = "{0}" and logintoken = "{1}"'.format(memberid, logintoken)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                index = pg_general.converttype(data.get('index'), int)
                command = 'update memberloginlog set logouttime="{0}" where memberloginlog.index = "{1}"'.format(now, index)
                updateresult = await self.updatedbdata(logintoken, command)
                if updateresult == True:
                    result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatememberlogout Except:{0}'.format(e))
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:updatememberlogout result:{0}, logintoken:{1}'.format(result, logintoken))
        return result

    async def getmemberinfo(self, redis_obj,logintoken, memberid, param_memberid=None):
        """
        取得玩家資料結果
        DB member 撈取會員基本資料 根據member.level 關聯DB levelinfo 該會員等級的資料
        玩家經驗值百分比需根據DB member 的exp 和levelinfo的newlevelexp 進行運算
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:getmemberinfo logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
            result = pg_general.Apiresult.connectdberror

            clientdata = {}

            isself = True
            if param_memberid is not None:
                if param_memberid != memberid:
                    isself = False
                selfmemberid = memberid
                memberid = param_memberid

            # if is not self add member.viewed
            if isself == False:
                command = 'update member set viewed=viewed+1 where memberid="{0}"'.format(param_memberid)
                update_result = await self.updatedbdata(logintoken,command)


            # 抓取 setting2.errordescription for changenickname error description
            command = 'select errordescription from setting2'
            datalen , data = await self.getdbdata(logintoken , command)
            if datalen ==1:
                errordescription = data.get('errordescription')
                if errordescription is not None:
                    errordescription = json.loads(errordescription)
                else:
                    errordescription = {}

            command = 'select member.*, levelinfo.newlevelexp, levelinfo.maxbet from member, levelinfo where member.memberid = "{0}" and member.level = levelinfo.level'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command,False,True)

            if datalen == 1:
                exp = pg_general.converttype(data.get('exp'), int)
                newlevelexp = pg_general.converttype(data.get('newlevelexp'), int)
                exppercent = int((exp / newlevelexp) * 100)
                exppercent = 100 if exppercent > 100 else exppercent
                now = pg_general.strtodatetime(pg_general.getutcnow())

                maxbet = pg_general.converttype(data.get("maxbet"),int)
                exptonextlevel = newlevelexp-exp

                canchangenickname = data.get('canchangenickname')
                if canchangenickname == 0:
                    canchangenickname == False
                else:
                    canchangenickname = True


                if isself == True:
                    feedbackmemberid = memberid
                else:
                    feedbackmemberid = param_memberid

                viewed = data.get('viewed')
                likeamount = data.get('likeamount')

                channel = data.get('channel')
                phonebindstatus = data.get('phonebindstatus')
                if phonebindstatus == 2:
                    isbindphone = True
                else:
                    isbindphone = False

                registerdatetimeutc = data.get('registrationdatetime')
                if registerdatetimeutc is not None:
                    registerdate = (registerdatetimeutc + timedelta(hours=8)).strftime('%Y/%m/%d')

                message = data.get('message')

                activenumber = data.get('activenumber')
                if activenumber is None:
                    activenumber = 0

                username = data.get('username')
                isbindacc = False
                if username is not None and username != '0' and username !='':
                    isbindacc = True

                registrationdatetime = data.get('registrationdatetime')

                tutorialbetfinish = data.get('tutorialbetfinish')
                if tutorialbetfinish == 0 :
                    needtutorialflag = 1
                else:
                    needtutorialflag = 0


                    # 抓取今日總押分 金幣與銀幣
                twtodaydatestr = pg_general.get_tw_date_str()

                daybet = await redis_obj.hget('daybet_{}'.format(twtodaydatestr),'{}'.format(memberid))
                if daybet is None:
                    daybet = 0
                daybets = await redis_obj.hget('daybets_{}'.format(twtodaydatestr),'{}'.format(memberid))
                if daybets is None:
                    daybets = 0



                clientdata = {
                    "nickname": pg_general.converttype(data.get('nickname'), str),
                    "avatar": pg_general.converttype(data.get('avatar'), str),
                    "level": pg_general.converttype(data.get('level'), int),
                    "card": data.get('card'),
                    "exppercent": exppercent,
                    "credit": pg_general.converttype(data.get('credit'), int),
                    "silvercredit": pg_general.converttype(data.get('silvercredit'),int),
                    "biggestmultiplier": pg_general.converttype(data.get('biggestmultiplier'), int),
                    "biggestwins": pg_general.converttype(data.get('biggestwins'), int),
                    "totaltopmultiplier": pg_general.converttype(data.get('totaltopmultiplier'), int),
                    "totaltopwin": pg_general.converttype(data.get('totaltopwin'), int),
                    "isbindfb": pg_general.converttype(data.get('isbindfb'), bool),
                    "isbindacc": isbindacc,
                    "isbindphone": isbindphone,
                    "maxbet": maxbet,
                    "exptonextlevel": exptonextlevel,
                    "isself": isself,
                    "memberid": feedbackmemberid,
                    "viewed": viewed,
                    "likeamount": likeamount,
                    "channel": channel,
                    "registerdate": registerdate,
                    "message": message,
                    "activenumber": activenumber,
                    "isfirstbuy": data.get('isfirstbuy'),
                    "registrationdatetime": registrationdatetime,
                    "daybet": daybet,
                    "daybets": daybets

                }

                # 如果是自己的話才放應該放的東西
                if isself == True:
                    clientdata['errordescription'] = errordescription
                    clientdata['canchangenickname'] = canchangenickname
                    clientdata['needtutorialflag'] = needtutorialflag


                if None not in clientdata.values():
                    result = pg_general.Apiresult.success
                else:
                    result = pg_general.Apiresult.othererror
            else:
                result = pg_general.Apiresult.dbnodata

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getmemberinfo result:{0}, clientdata:{1}, logintoken:{2}'.format(result, clientdata, logintoken))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getmemberinfo except:{0}'.format(e))
        return result, clientdata


    async def updateprofile(self, logintoken, memberid, nickname):
        '''
        更新個人資料
                更新DB member裡的會員資料(avatar nickname)
        '''

                
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:updateprofile logintoken:{0}, memberid:{1}, nickname:{2}'.format(logintoken, memberid, nickname))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            transformed_nickname = HanziConv.toTraditional(nickname)

            # 檢查格式 檢查是否有符號與英文數字 以及是否有簡體字
            if pg_general.check_chinese(nickname) == False or len(nickname)>8: # or nickname != transformed_nickname:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": "2"
                }
                raise ValueError('has simplied chinese or number')


            # 先找是否可以 change nickname
            command = 'select canchangenickname from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen <1:
                raise ValueError('1')

            canchangenickname = True if data.get('canchangenickname') > 0 else False
            if canchangenickname == False:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": "3"
                }
                raise ValueError('cant change nickname')

            updatestr = ''
            if nickname is None:
                raise ValueError('nickname is None')

            nickname = nickname.strip()
            if len(nickname) > 0:
                updatestr = 'nickname = "{0}",canchangenickname="0"'.format(nickname)

            if updatestr != '':
                # 檢查是否重複
                command = 'select nickname from member where nickname = "{0}" and memberid != "{1}"'.format(nickname,memberid)
                datalen , data = await self.getdbdata(logintoken,command)
                if datalen > 0:
                    clientdata = {
                        "result": "1"  # 資料重複
                    }
                    result = pg_general.Apiresult.success

                else:
                    # 更新member 資料表
                    command = 'update member set {0} where memberid = "{1}"'.format(updatestr, memberid)
                    updateresult = await self.updatedbdata(logintoken, command)

                    if updateresult == True:
                        clientdata = {
                            "result": "0"
                        }
                        result = pg_general.Apiresult.success
                    else:
                        result = pg_general.Apiresult.othererror
            else:
                result = pg_general.Apiresult.parametererror

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:updateprofile result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateprofile ValueError : {0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateprofile Exception : {0}'.format(e))
        return result, clientdata



    async def getdailybonusinfo(self, logintoken, memberid):
        """
        取得每日登入獎勵資料
        從DB memberdailybonus的 dailybonusgroup關聯 DB dailybonusInfo的dailybonusgroup 找出全部獎項
        實際獎項內容 從DB dailybonusInfo.promotionid = promotion.promotionindex 取得
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getdailybonusinfo logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
            result = pg_general.Apiresult.connectdberror
            isspin = None
            dailybonusinfo = []
            clientdata = {}

            # 抓免費轉輪資料
            command = 'select memberdailybonus.*,dailybonusInfo.*,promotion.*,member.card from member, memberdailybonus, dailybonusInfo, promotion where memberdailybonus.memberid = "{0}" ' \
                      ' and member.memberid = memberdailybonus.memberid and dailybonusInfo.dailybonusgroup = member.card and dailybonusInfo.promotionid = promotion.promotionindex'.format(memberid)


            datalen, data = await self.getdbdata(logintoken, command, True,True)
            if datalen == 12:
                lastspintime_utctime = data[0].get("lastspintime")
                if lastspintime_utctime is not None:
                    nowdatetime_localtime = pg_general.get_local_datetime() # tw time
                    if pg_general.get_utc_to_local_datetime(lastspintime_utctime).date() != nowdatetime_localtime.date():
                        isspin = False
                    else:
                        isspin = True



                for item in data:
                    promotiontype = pg_general.converttype(item.get("promotiontype"), int)
                    awardcontent = pg_general.converttype(item.get("content"), int)
                    posid = pg_general.converttype(item.get('posid'),int)
                    type = item.get('type')
                    if promotiontype == 0 and awardcontent is not None:
                        tempdailybonusinfo = {
                            "id": posid,
                            "type": type,
                            "pay": awardcontent
                        }

                        # 檢查是否有值為空
                        if None not in tempdailybonusinfo.values():
                            dailybonusinfo.append(tempdailybonusinfo)

                command = 'select dailybonusflag from setting2'
                datalen , data = await self.getdbdata(logintoken,command)

                if datalen ==1:
                    dailybonusflag = data.get('dailybonusflag')
                    if dailybonusflag == 0:
                        isspin = True



            else:
                result = pg_general.Apiresult.dbnodata

            # 檢查結果是否正確
            if isspin is not None and len(dailybonusinfo) == 12:
                clientdata = {
                    "isspin": isspin,
                    "dailybonusinfo": dailybonusinfo
                }
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.othererror

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getdailybonusinfo result:{0}, clientdata:{1}, logintoken:{2}'.format(result, clientdata, logintoken))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getdailybonusinfo except:{0}, clientdata:{1}, logintoken:{2}, result:{3}'.format(e,
                                                                                                                clientdata,
                                                                                                                logintoken,result))
        return result, clientdata

    async def spindailybonus(self, logintoken, memberid):
        """
        領取每日登入獎勵
        每日登入獎勵資料(參照 function getdailybonusinfo)
        如果可以spin 隨機產生spin結果
        更新 spin結果 及member 最新credit到DB
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:spindailybonus logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        isspin = None
        dailybonusinfo = []

        clientdata = {}
        award = None
        credit = None

        # 先確認是否有關閉此功能
        command=  'select dailybonusflag from setting2'
        datalen ,data = await self.getdbdata(logintoken,command)
        if datalen ==1:
            dailybonusflag = data.get('dailybonusflag')
            if dailybonusflag == 0:
                return result,clientdata

        command = 'select memberdailybonus.*, member.credit,member.silvercredit,member.card, promotion.*, dailybonusInfo.* from memberdailybonus, member, promotion, dailybonusInfo where memberdailybonus.memberid = "{0}" ' \
                  ' and member.memberid = memberdailybonus.memberid and promotion.promotionindex = dailybonusInfo.promotionid and dailybonusInfo.dailybonusgroup = member.card '.format(memberid)
        datalen, data = await self.getdbdata(logintoken, command, True)
        if datalen == 12:
            lastspintime_utctime = data[0].get("lastspintime")
            credit = pg_general.converttype(data[0].get("credit"), int)
            silvercredit = data[0].get('silvercredit')

            # 檢查是否已spin
            if lastspintime_utctime is not None and credit is not None:
                lastspintime_localtime = pg_general.get_utc_to_local_datetime(lastspintime_utctime)
                now_utctime = pg_general.getutcnow_datetime()
                now_localtime = pg_general.get_utc_to_local_datetime(now_utctime)
                if lastspintime_localtime.date() != now_localtime.date():
                    isspin = False
                else:
                    isspin = True

            if isspin == False:
                for item in data:
                    id = pg_general.converttype(item.get("dailybonusInfo.index"), int)
                    promotiontype = pg_general.converttype(item.get("promotiontype"), int)
                    awardcontent = pg_general.converttype(item.get("content"), int)
                    type = item.get('type')
                    weight = item.get('weight')
                    if promotiontype == 0 and awardcontent is not None:
                        tempdailybonusinfo = {
                            "id": id,
                            "pay": awardcontent,
                            "type": type,
                            "weight": weight
                        }

                        # 檢查是否有值為空
                        if None not in tempdailybonusinfo.values():
                            dailybonusinfo.append(tempdailybonusinfo)

                # 隨機產生spin結果
                if isspin is not None and len(dailybonusinfo) == 12:
                    temprnglist = []
                    i = 0
                    for item in dailybonusinfo:
                        tempweight = item.get('weight')
                        for _ in range(tempweight):
                            temprnglist.append(i)
                        i += 1


                    random.random()
                    rngindex = random.choice(temprnglist)



                    award = pg_general.converttype(dailybonusinfo[rngindex].get("pay"), int)
                    id = pg_general.converttype(dailybonusinfo[rngindex].get("id"), int)
                    type = dailybonusinfo[rngindex].get('type')

                    aftercredit = credit
                    aftersilvercredit = silvercredit
                    if type==0: # 金幣
                        aftercredit = credit + award
                    elif type ==1: # 銀幣
                        aftersilvercredit = silvercredit + award

                    now = pg_general.getutcnow()
                    # 測試使用 lastspin 改為 2000-01-01 00:00:00
                    if env_setting.PRODUCTION_MODE == False:
                        now = pg_general.strtodatetime('2000-01-01 00:00:00.00')

                    command = 'update member, memberdailybonus set member.credit= "{0}",member.silvercredit="{3}", memberdailybonus.lastspintime = "{1}" where member.memberid = "{2}" and memberdailybonus.memberid = "{2}"'.format(
                        aftercredit, now_utctime, memberid,aftersilvercredit)
                    updateresult = await self.updatedbdata(logintoken, command)

                    if updateresult == True and None not in [award,aftercredit,aftersilvercredit,rngindex]:
                        clientdata = {
                            "result": 0,
                            "award": award,
                            "type": type,
                            "credit": aftercredit,
                            "silvercredit": aftersilvercredit,
                            "id": rngindex
                        }
                        result = pg_general.Apiresult.success
                        param = {
                            "frommemberid": memberid,
                            "tomemberid": memberid,
                            "type": pg_general.transactiontype.dailywheel,
                            "amount": award if type==0 else 0,
                            "amount_silver": award if type==1 else 0,
                            "otherdata": 'spindailybonus'
                        }
                        asyncio.ensure_future(self.writetransactionlog(logintoken, param))


                    else:
                        result = pg_general.Apiresult.othererror
        else:
            result = pg_general.Apiresult.dbnodata



        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:spindailybonus result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata






    async def getpiggyinfo(self, logintoken, memberid):
        """
        取得小豬資訊
        從DB memberpiggyinfo的 piggylevel關聯 DB piggyinfo的level 找出此member的小豬資訊
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getpiggyinfo logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        clientdata = {}

        command = 'select memberpiggyinfo.piggycredit,setting2.minipiggytake,setting2.piggyshowamount from memberpiggyinfo,setting2 where memberpiggyinfo.memberid = "{0}"'.format(memberid)


        datalen, data = await self.getdbdata(logintoken, command)
        if datalen == 1:
            piggycredit = pg_general.converttype(data.get('piggycredit'), int)
            piggyshowamount = data.get('piggyshowamount')
            minipiggytake = data.get('minipiggytake')
            cantake = True if piggycredit >= minipiggytake else False
            clientdata = {
                "piggycredit": piggycredit,
                "amount": piggyshowamount,
                'cantake': cantake
            }

            result = pg_general.Apiresult.success

        else:
            result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                           'pg_asqldb:getpiggyinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata

    async def getmallinfo(self, logintoken, memberid,mode):
        """
        取得商城資訊
        從DB member 找isfirstbuy 判斷此玩家是否為首購
        再決定找的商城種類(一般或首購)
        從DB mall的 malltype關聯 DB mallinfo的malltype 取得商城資訊
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getmallinfo logintoken:{0}, memberid:{1}:mode:{2}'.format(logintoken, memberid,mode))
        result = pg_general.Apiresult.connectdberror

        mallcontent = []
        clientdata = {}
        mallserialcount = None
        command = 'select mallinfo.* from mallinfo where mode = {} order by showindex '.format(mode)
        datalen, data = await self.getdbdata(logintoken, command, True)
        if datalen > 0:

            for tempdata in data:

                tempmallcontent = {
                    "index": pg_general.converttype(tempdata.get("showindex"), int),
                    "credit": pg_general.converttype(tempdata.get("point"), int),
                    "cash": pg_general.converttype(tempdata.get("cash"), int),
                    "shopid": pg_general.converttype(tempdata.get("shopid"),str),
                    "flag": pg_general.converttype(tempdata.get('tag'),int)

                }

                # 檢查是否有值為空
                if None not in tempmallcontent.values():
                    mallcontent.append(tempmallcontent)

            # get mallserialcount from seting2
            command = 'select mallserialcount from setting2'
            datalen,data = await self.getdbdata('get mallserialcount',command)
            if datalen == 1:
                mallserialcount = data.get('mallserialcount')


            if len(mallcontent) > 0 :
                clientdata = {
                    "mallcontent": mallcontent,
                    "mallserialcount": mallserialcount
                }

                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.othererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                           'pg_asqldb:getmallinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata

    async def shopping(self, redis_obj, logintoken, memberid, cardinfo, jsoncontent,mode):
        """
        所有商城功能集中在這邊處理
        """
        # shopid =  'secretoffer_lv_01'
        # result_shop, ret_data = await self.secretoffermall(logintoken, memberid, shopid)

        try:
            MALL_SHOP_ID = ['shopmall_lv_01','shopmall_lv_02','shopmall_lv_03','shopmall_lv_04','shopmall_lv_05','shopmall_lv_06']
            PIGGY_SHOP_ID = ['piggy_lv_01','piggy_lv_02','piggy_lv_03','piggy_lv_04','piggy_lv_05','piggy_lv_06','piggy_lv_07','piggy_lv_08','piggy_lv_09','piggy_lv_10']
            SECRETOFFER_SHOP_ID = ['secretoffer_lv_01','secretoffer_lv_02','secretoffer_lv_03','secretoffer_lv_04','secretoffer_lv_05']


            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                'pg_asqldb:shopping logintoken:{0}, memberid:{1}, jsoncontent:{2},mode:{3}'.format(logintoken, memberid, jsoncontent,mode))
            result = pg_general.Apiresult.connectdberror
            clientdata = {
                "result":1,
                "buycredit":0,
                "credit":0,
                "content":{}
            }

            # 確認資料正確性
            jsondata = jsoncontent.get('data')
            if jsondata is None:
                raise ValueError('jsondata is None')

            platform = jsondata.get('platform')  # 0: ios , 1: android
            shopid = jsondata.get('shopid')
            if None in [platform,shopid] or platform not in [0,1]:
                raise ValueError('platform or shopid id None or platform is wrong')

            num = jsondata.get('num')
            version = 'old'
            if num is not None:
                version = 'new'
                num = int(num)

            if version == 'old':
                # check shopid 是否正確
                malltype = -1
                if shopid in MALL_SHOP_ID:
                    malltype = 0
                elif shopid in PIGGY_SHOP_ID:
                    malltype = 1
                elif shopid in SECRETOFFER_SHOP_ID:
                    malltype = 3

                if malltype == -1: # shopid 不正確
                    pg_general.writelog(pg_general.PG_LogerLevel.error, "shopid:{} is not in any SHOP_ID".format(shopid))
                    raise ValueError('shopid is wrong')

            elif version == 'new':
                # integer
                # 商城
                # number
                # 0: 一般商城, 1: luckybuy, 2: piggy, 3: 神秘商人, 4: Super Wheel
                if num == 0: # normal mall
                    malltype = 0
                elif num == 3: # secret offer
                    malltype = 3
                elif num ==5:  # 首購商城
                    malltype = 5
                else:
                    raise ValueError('shop num is wrong')


            jsoncontent_2 = jsondata.get('jsoncontent')
            if jsoncontent_2 is None:
                raise ValueError('jsoncontent_2 is None')

            internal_shopid = jsoncontent_2.get('id')
            if shopid != internal_shopid:
                pg_general.writelog(pg_general.PG_LogerLevel.error, "shopid:{} is not as same as content's shopid:{}".format(shopid, internal_shopid))
                raise ValueError('internal shopid error')

            if platform == 0: # ios

                receipt_data = jsoncontent_2.get('receiptCipheredPayload')
                currency_code = jsoncontent_2.get('currencyCode')
                transaction_id = pg_general.converttype(jsoncontent_2.get('transactionID'),str)
                price = jsoncontent_2.get('price')


            else:               # android
                receipt_data = jsoncontent_2.get('receiptCipheredPayload')
                currency_code = jsoncontent_2.get('currencyCode')
                transaction_id = pg_general.converttype(jsoncontent_2.get('transactionID'),str)
                price = jsoncontent_2.get('price')
                receipt = jsoncontent_2.get('receipt')
                receipt = json.loads(receipt)

            if None in [receipt_data,currency_code,transaction_id,price]:    #  receipt data is 為空
                raise ValueError('receiptCipheredPayload data is None')

            if platform == 1:
                if receipt is None:
                    raise ValueError('android receipt data is None')
                purchaseToken = receipt.get('purchaseToken')
                if purchaseToken is None:
                    raise ValueError('android purchaseToken data is None')

            statuscode = -1
            # server 驗證流程
            if platform ==0:    # ios
                url = IOS_IAP_VALIDATE_URL
                production_verify_flag = False
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json={"receipt-data":receipt_data}) as response:
                    # response = await session.post(url, json={"receipt-data":receipt_data})
                        if response.status != 200:
                            result = pg_general.Apiresult.othererror
                            raise ValueError('iap validate error')
                        response_data = await response.text()
                        response_data = json.loads(response_data)
                        statuscode = response_data.get('status')
                        if statuscode ==0:
                            verifyreceipt = response_data.get('receipt')
                            if verifyreceipt is None:
                                result = pg_general.Apiresult.othererror
                                raise ValueError('iap validate error 1')

                            verifybundle_id = verifyreceipt.get('bundle_id')
                            if verifybundle_id != 'com.slots.casino.jinsong':
                                result = pg_general.Apiresult.othererror
                                raise ValueError('iap validate error 2')
                            verifyin_app = verifyreceipt.get('in_app')

                            if verifyin_app is None:
                                result = pg_general.Apiresult.othererror
                                raise ValueError('iap validate error 3')

                            for inappitem in verifyin_app:
                                if inappitem.get('transaction_id') == transaction_id:
                                    production_verify_flag = True
                                    break

                            if production_verify_flag == False:
                                result = pg_general.Apiresult.othererror
                                raise ValueError('iap validate error 4')

                    if statuscode != 0 and production_verify_flag ==False:     # change to verify sandbox
                        url = IOS_IAP_VALIDATE_URL_SANDBOX
                        async with session.post(url, json={"receipt-data": receipt_data}) as response:
                        # response = await session.post(url, json={"receipt-data": receipt_data})
                            if response.status != 200:
                                result = pg_general.Apiresult.othererror
                                raise ValueError('iap sandbox validate error 1')

                            response_data = await response.text()
                            response_data = json.loads(response_data)
                            statuscode = response_data.get('status')
                            if statuscode == 0:
                                verifyreceipt = response_data.get('receipt')
                                if verifyreceipt is None:
                                    result = pg_general.Apiresult.othererror
                                    raise ValueError('iap sandbox validate error 2')

                                verifybundle_id = verifyreceipt.get('bundle_id')
                                if verifybundle_id != 'com.slots.casino.jinsong':
                                    result = pg_general.Apiresult.othererror
                                    raise ValueError('iap sandbox validate error 3')
                                verifyin_app = verifyreceipt.get('in_app')

                                if verifyin_app is None:
                                    result = pg_general.Apiresult.othererror
                                    raise ValueError('iap sandbox validate error 4')

                                for inappitem in verifyin_app:
                                    if inappitem.get('transaction_id') == transaction_id:
                                        production_verify_flag = True
                                        break

                                if production_verify_flag == False:
                                    result = pg_general.Apiresult.othererror
                                    raise ValueError('iap validate error 6')



                            else:
                                result = pg_general.Apiresult.othererror
                                raise ValueError('iap sandbox validate error 5')

            else:               # android
                response_data = GOOGLE_IAP_SERVICE.purchases().products().get(packageName=GOOGLE_IAP_BUNDLE_ID,
                        productId=shopid,token=purchaseToken).execute()
                if response_data is None:
                        raise ValueError('result_google_iap_validate data is None')
                if len(response_data) == 0:
                    raise ValueError('result_google_iap_validate data is NULL')

                statuscode = response_data.get('purchaseState')

            # 確認此單是否已經重複
            command = 'select transactionid from mallhistory where transactionid = "{0}"'.format(transaction_id)
            datalen , data = await self.getdbdata(logintoken,command,True,True)
            if datalen >0:
                clientdata = {
                    "result": 2
                }
                result = pg_general.Apiresult.success
                return result, clientdata

            if statuscode !=0:
                await self.write_mall_history(logintoken,memberid,shopid,price,transaction_id,malltype,platform,statuscode,receipt_data,currency_code,None)
                raise ValueError('receipt status != 0')

            await self.write_mall_history(logintoken,memberid,shopid,price,transaction_id,malltype,platform,statuscode,receipt_data,currency_code,response_data)
            if malltype ==0:    # normal mall
                result_shop, ret_data = await self.normalmall(logintoken,memberid,shopid,mode)
            elif malltype==3:               # secret offer mall
                result_shop, ret_data = await self.secretoffermall(logintoken,memberid,shopid)
            elif malltype==5:
                result_shop, ret_data = await self.firstbuymall(logintoken,memberid,shopid)
            else:
                raise ValueError('mall type is else')


            # write transaction log
            param = {
                "frommemberid": memberid,
                "tomemberid": memberid,
                "type": pg_general.transactiontype.shopmall,
                "amount": ret_data.get('buycredit'),
                "amount_silver": 0,
                "otherdata": 'shopmall'
            }
            asyncio.ensure_future(self.writetransactionlog(logintoken, param))

            # write giftfreezedata
            param = {
                "memberid": memberid,
                "type": 0 if platform==0 else 1,
                "amount": pg_general.converttype(ret_data.get('buycredit'),int) * 100   # 轉成金幣
            }
            asyncio.ensure_future(self.writegiftfreeze(logintoken,param))

            # update redis cardbuy_{}
            twnowdate = pg_general.get_tw_datetime().date()
            firstdate = pg_general.get_tw_2020_first_date().date()
            datekey = str((twnowdate - firstdate).days % 60)
            cash = ret_data.get('cash')
            card = ret_data.get('card')

            await redis_obj.hincrby('cardbuy_{}'.format(memberid), datekey, cash)

            # make level up future
            if card in [0, 1, 2, 3, 4]:
                logintoken = await redis_obj.get_value('{}'.format(memberid))
                apporweb = 0  # 0: app, 1: web
                asyncio.ensure_future(self.buycardlevelup_future(apporweb, logintoken, memberid, card, redis_obj, cardinfo))

            if result_shop ==pg_general.Apiresult.success:
                clientdata = {
                    "result": 0,
                    "buycredit": ret_data.get('buycredit'),
                    "credit": ret_data.get('credit'),
                    "content": ret_data.get('content')
                }
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.othererror


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:shopping ValueError:{0},memberid:{1},jsoncontent:{2}'.format(e,memberid,jsoncontent))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:shopping Exception:{0},memberid:{1},jsoncontent:{2}'.format(e, memberid,
                                                                                                        jsoncontent))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                               'pg_asqldb:shopping result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
            return result, clientdata

    async def getinboxinfo(self, logintoken, memberid):
        """
        取得郵件資料
        從DB memberinbox 找出此member的inbox資料
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getinboxinfo logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        inboxinfo = []
        clientdata = {}

        command = 'select * from memberinbox, promotion where memberinbox.memberid = "{0}" and memberinbox.promotionid = promotion.promotionindex order by memberinbox.index desc;'.format(memberid)
        datalen, data = await self.getdbdata(logintoken, command, True)
        if datalen > 0:
            now = pg_general.strtodatetime(pg_general.getutcnow())
            history_mail_count = 0
            for tempdata in data:
                promotiontype = pg_general.converttype(tempdata.get("promotiontype"), int)
                dateline = tempdata.get("dateline") # utc time


                countdownseconds = pg_general.converttype((dateline - now).total_seconds(), int)
                receivestate = pg_general.converttype(tempdata.get("receivestate"), int)
                inboxtype = None
                award = 0
                awardtype = 1
                gameid = ""
                if None not in [promotiontype,dateline,countdownseconds,receivestate]:
                    if promotiontype == 0:      # 金幣 參照 promotion content
                        inboxtype = 0
                        awardtype = 0
                        award = pg_general.converttype(tempdata.get("content"), int)

                    elif promotiontype == 1:        # free game 還沒完成
                        inboxtype = 1
                        content = json.loads(tempdata.get("content"))
                        award = content.get("freespin")
                        gameid = content.get("gameid")
                    elif promotiontype == 4:            # 金幣直接抓 memberinbox credit_award
                        award = tempdata.get('credit_award')
                        awardtype = 0
                        inboxtype = 0
                    elif promotiontype == 5:            # 銀幣 參照 promotion content
                        inboxtype = 0
                        award = pg_general.converttype(tempdata.get("content"), int)
                        awardtype = 1
                    elif promotiontype ==6:               # 免費轉輪
                        inboxtype = 3
                        award = 0
                        awardtype = 0
                    elif promotiontype ==7:             # 銀幣 直接抓 memberinbox credit_award
                        inboxtype = 0
                        award = tempdata.get('credit_award')
                        awardtype = 1

                    if receivestate == 1 and countdownseconds <=0:
                        receivestate = -1

                    # 將 dateline 轉為 localtime datetime
                    dateline = pg_general.get_utc_to_local_datetime(dateline)
                    tempinboxinfo = {
                        "inboxid": pg_general.converttype(tempdata.get("index"), int),
                        "inboxtype": inboxtype,
                        "inboxuri": pg_general.converttype(tempdata.get("inboxuri"), str),
                        "mailtype": pg_general.converttype(tempdata.get('mailtype'),int),
                        "inboxtitle": pg_general.converttype(tempdata.get("inboxtitle"), str),
                        "inboxcontent": pg_general.converttype(tempdata.get("inboxcontent"), str),
                        "receivestate": receivestate,
                        "expiredday": dateline.date().__str__().replace('-','/'),
                        "award": award,
                        "awardtype": awardtype,
                        "gameid": gameid
                    }

                    if receivestate == 0 or receivestate == -1:
                        history_mail_count += 1

                    # 檢查是否有值為空
                    if None not in tempinboxinfo.values():
                        if history_mail_count <= 30 or receivestate ==1:
                            inboxinfo.append(tempinboxinfo)

            if len(inboxinfo) > 0:
                clientdata = {
                    "inboxinfo": inboxinfo
                }

                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.othererror
        else:
            result = result = pg_general.Apiresult.success
            clientdata = {
                "inboxinfo": []
            }


        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                           'pg_asqldb:getinboxinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata

    async def receiveinbox(self, logintoken, memberid, inboxid):
        """
        領取郵件
        inboxid = -1 為一鍵領取獎勵類型為金幣的全部郵件
        inboxid = -1時 從DB memberinbox找出該玩家 獎勵類型為金幣的(promotion.promotiontype = 0) 全部inbox資訊
        inboxid 不為-1 時找出該筆的 inbox資訊
        檢查inbox資訊 可以領取的話記錄inboxid 和累加獎勵金額
        更新可領取的inbox狀態 及領取獎勵後的credit到DB
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:receiveinbox logintoken:{0}, memberid:{1}, inboxid:{2}'.format(logintoken, memberid, inboxid))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        credit = None
        totalaward = 0
        totalaward_silver = 0
        finishinboxid = []
        now = pg_general.strtodatetime(pg_general.getutcnow())
        if inboxid != -1:
            command = 'select memberinbox.*, member.credit,member.silvercredit,promotion.* from memberinbox, member, promotion where member.memberid = "{0}" and memberinbox.index = "{1}" and promotion.promotionindex = memberinbox.promotionid and memberinbox.memberid = member.memberid and memberinbox.receivestate="1"'.format(memberid, inboxid)
            datalen, data = await self.getdbdata(logintoken, command, True)
        else:
            command = 'select memberinbox.*, member.credit, member.silvercredit,promotion.* from memberinbox, member, promotion where member.memberid = "{0}" and promotion.promotionindex = memberinbox.promotionid and memberinbox.memberid = member.memberid and promotion.promotiontype in (0,3,4,5,7) and memberinbox.receivestate="1"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command, True)

        if datalen > 0:
            result = pg_general.Apiresult.othererror
            credit = pg_general.converttype(data[0].get('credit'), int)
            silvercredit = pg_general.converttype(data[0].get('silvercredit'),int)
            for item in data:
                inboxindex = pg_general.converttype(item.get('index'), int)
                receivestate = pg_general.converttype(item.get('receivestate'), int)
                promotiontype = pg_general.converttype(item.get("promotiontype"), int)
                dateline = item.get("dateline") # utc time
                countdownseconds = pg_general.converttype((dateline - now).total_seconds(), int)
                award = 0
                award_s = 0
                wheeldata = []



                inboxcontent = {}
                if receivestate is not None and promotiontype is not None and credit is not None and countdownseconds is not None:
                    if promotiontype == 0:
                        award = pg_general.converttype(item.get("content"), int)
                    elif promotiontype == 1:
                        award = 0
                    elif promotiontype == 4:    # 金幣可變
                        award = item.get('credit_award')
                    elif promotiontype == 7:    # 銀幣可變
                        award_s = item.get('credit_award')
                    elif promotiontype == 5: # 銀幣
                        award_s = pg_general.converttype(item.get('content'),int)
                    elif promotiontype == 6: # 免費轉輪
                        # 抓轉輪倍數
                        dailywheelinboxtimes = 1
                        command = 'select dailywheelinboxtimes from setting2'
                        datalen, data = await self.getdbdata(logintoken,command)
                        if datalen ==1:
                            dailywheelinboxtimes = data.get('dailywheelinboxtimes')

                        # 抓 轉輪資料
                        command = 'select dailybonusInfo_inbox.*,promotion.* from dailybonusInfo_inbox,member,promotion where ' \
                                    ' dailybonusInfo_inbox.dailybonusgroup = member.card and member.memberid = "{0}" and promotionindex = ' \
                                    'dailybonusInfo_inbox.promotionid order by posid'.format(memberid)
                        datalen , data = await self.getdbdata(logintoken,command,True)
                        if datalen !=12 :
                            result = pg_general.Apiresult.connectdberror
                            clientdta = {}
                            return result , clientdata
                        temprnglist = []
                        i = 0
                        for item in data:
                            type = item.get('promotiontype')
                            content = item.get('content')
                            weight = item.get('weight')
                            wheeldata.append({
                                "id": i,
                                "type": type,
                                "pay": content
                            })
                            for _ in range(weight):
                                temprnglist.append(i)
                            i += 1

                        random.random()
                        rngindex = random.choice(temprnglist)
                        inboxcontent = {
                            "id": rngindex,
                            "dailybonusinfo": wheeldata,
                            "awardtimes": dailywheelinboxtimes
                        }
                        windata = wheeldata[rngindex]
                        awardori = 0
                        awardori_s = 0
                        awardextra = 0
                        awardextra_s = 0
                        if windata.get('type') == 0: # 金幣
                            awardori = pg_general.converttype(windata.get('pay'),int)
                            award = awardori * dailywheelinboxtimes
                            awardextra = award -  awardori
                        elif windata.get('type') == 5: # 銀幣
                            awardori_s = pg_general.converttype(windata.get('pay'),int)
                            award_s = awardori_s * dailywheelinboxtimes
                            awardextra_s = award_s - awardori_s
                        inboxcontent['awardori'] = awardori
                        inboxcontent['awardori_s'] = awardori_s
                        inboxcontent['awardextra'] = awardextra
                        inboxcontent['awardextra_s'] = awardextra_s

                    if countdownseconds > 0 and receivestate == 1:
                        totalaward += award
                        totalaward_silver += award_s
                        finishinboxid.append(inboxindex)

            if credit is not None and len(finishinboxid) > 0:
                aftercredit = credit + totalaward

                command = 'update memberinbox, member set memberinbox.receivestate = 0, member.credit =member.credit+ "{0}",' \
                          'member.silvercredit=member.silvercredit+"{3}" where memberinbox.memberid = "{1}" and memberinbox.index in ({2}) and member.memberid = "{1}"'.format(
                    totalaward, memberid, str(finishinboxid).replace('[','').replace(']',''),totalaward_silver)
                updateresult = await self.updatedbdata(logintoken, command)
                if updateresult == True:
                    command = 'select credit,silvercredit from member where memberid="{0}"'.format(memberid)
                    datalen , data = await self.getdbdata(logintoken,command,False,True)
                    if datalen ==1:
                        aftercredit = data.get('credit')
                        aftersilvercredit = data.get('silvercredit')

                    clientdata = {
                        "result": 0,
                        "award": totalaward,
                        "award_s": totalaward_silver,
                        "credit": aftercredit,
                        "credit_s": aftersilvercredit,
                        "content": inboxcontent
                    }

                    param = {
                        "frommemberid": memberid,
                        "tomemberid": memberid,
                        "type": pg_general.transactiontype.inboxfreewheel if promotiontype ==6 else pg_general.transactiontype.receiveinbox,
                        "amount": totalaward,
                        "amount_silver": totalaward_silver,
                        "otherdata": 'receiveinbox' + ('' if promotiontype !=6 else ' :free wheel')
                    }
                    asyncio.ensure_future(self.writetransactionlog(logintoken, param))

                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 0,
                    "award": 0,
                    "award_s": 0,
                    "credit": credit,
                    "credit_s": silvercredit
                }
        else:
            result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                           'pg_asqldb:receiveinbox result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata

    async def feedback(self, logintoken, memberid, email, content,typeid):
        """
        意見及Bug回報
        將相關資料(email、content) insert到DB feedback
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:feedback logintoken:{0}, memberid:{1}, email:{2}, content:{3},typeid:{4}'.format(logintoken, memberid, email, content,typeid))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        now = pg_general.getutcnow()
        command = 'insert into feedback(memberid, logintoken, time, email, content,typeid) values({0}, "{1}", "{2}", "{3}", "{4}","{5}")'.format(memberid, logintoken, now, email, content,typeid)
        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            clientdata = {
                "result": 0,
            }

            result = pg_general.Apiresult.success
        else:
            result = pg_general.Apiresult.othererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                           'pg_asqldb:feedback result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata


    async def getgamelist(self, logintoken, memberid):
        """
        取得遊戲列表
        從DB chapterInfo 找出該章節包含的遊戲(gameidlist)
        再關聯DB game的gameindex 找出遊戲相關資訊
        chapter id : 1 ~ 5 代表該章節, 0 代表所有章節
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getgamelist logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror
        try:

            clientdata = {}
            gamelist = []


            tempclientdatagamelist = {}
            normalsort = []
            mastersort = []
            hotsort = []
            newsort  = []
            # get member's ver and rer
            command = 'select ver,rer,level from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('rerobjectnew datalen != 1')
            member_ver = data.get('ver')
            member_rer = data.get('rer')
            member_level = data.get('level')

            if None in [member_ver, member_rer]:
                raise ValueError('member ver rer is None')

            command = 'SELECT * FROM (SELECT * FROM	(SELECT * FROM chapterInfo, game WHERE chapterInfo.chapterid = "1" AND FIND_IN_SET (game.gameindex, chapterInfo.gameidlist)' \
                        ') AS t1 LEFT JOIN (SELECT gameid AS gameid_t2,avatar AS avatar_0,amount AS amount_0,memberid as memberid_0,nickname as nickname_0 FROM jinsonggameranklive WHERE rank =1 AND type=0' \
                        ') AS t2 ON t1.gameid = t2.gameid_t2) AS t3 LEFT JOIN (SELECT gameid AS gameid_t4, avatar AS avatar_1, amount AS amount_1,memberid as memberid_1,nickname as nickname_1 FROM ' \
                        'jinsonggameranklive WHERE rank =1 AND type=1) AS t4 ON t3.gameid = t4.gameid_t4'
            datalen, data = await self.getdbdata(logintoken, command, True)
            if datalen > 0:

                for item in data:
                    gameindex = item.get("gameindex")
                    gametype = item.get('gametype')
                    gameidlist = item.get("gameidlist")
                    newbiesort = item.get('newbiesort')

                    if gametype == 0: # slot
                        rankprize = json.loads(item.get('rankprize'))
                        rankweekprize = json.loads(item.get('rankweekprize'))
                        totalrankreward = 0
                        tmptopwinlist = rankprize.get('topwin')
                        for tempitem in tmptopwinlist:
                            totalrankreward += pg_general.converttype(tempitem,int)
                        tmptopmultipilierlist = rankprize.get('topmultipilier')
                        for tempitem in tmptopmultipilierlist:
                            totalrankreward += pg_general.converttype(tempitem,int)
                        tmptopwinlist = rankweekprize.get('topwin')
                        for tempitem in tmptopwinlist:
                            totalrankreward += pg_general.converttype(tempitem,int)
                        tmptopmultipilierlist = rankweekprize.get('topmultipilier')
                        for tempitem in tmptopmultipilierlist:
                            totalrankreward += pg_general.converttype(tempitem,int)
                    else:
                        totalrankreward = 0

                    if member_level >= 5:
                        gamepos = gameidlist.split(',')
                    else:
                        gamepos = newbiesort.split(',')
                    posindex = gamepos.index(str(gameindex)) +1

                    gameidlist_hotsort = item.get('hotsort')
                    gamepos_hotsort = gameidlist_hotsort.split(',')
                    if str(gameindex) in gamepos_hotsort:
                        posindex_hotsort = gamepos_hotsort.index(str(gameindex)) +1
                    else:
                        posindex_hotsort = -1

                    gameidlist_mastersort = item.get('mastersort')
                    gamepos_mastersort = gameidlist_mastersort.split(',')
                    if str(gameindex) in gamepos_mastersort:
                        posindex_mastersort = gamepos_mastersort.index(str(gameindex)) + 1
                    else:
                        posindex_mastersort = -1

                    gameidlist_newsort = item.get('newsort')
                    gamepos_newsort = gameidlist_newsort.split(',')

                    if str(gameindex) in gamepos_newsort:
                        posindex_newsort = gamepos_newsort.index(str(gameindex)) + 1
                    else:
                        posindex_newsort = -1


                    gameidlist_newgamesort = item.get('newgamesort')
                    gamepos_newgamesort = gameidlist_newgamesort.split(',')
                    if str(gameindex) in gamepos_newgamesort:
                        posindex_newgamesort = gamepos_newgamesort.index(str(gameindex)) + 1
                    else:
                        posindex_newgamesort = -1

                    gameidlist_goodranksort = item.get('goodranklist')
                    gamepos_goodranksort = gameidlist_goodranksort.split(',')
                    if str(gameindex) in gamepos_goodranksort:
                        posindex_goodranksort = gamepos_goodranksort.index(str(gameindex)) + 1
                    else:
                        posindex_goodranksort = -1

                    gameid = item.get("gameid")
                    enable = item.get("enable")
                    unlocklevel = item.get("unlocklevel")
                    # historyrankstart = item.get("historyrankstart")
                    # historyrankend = item.get("historyrankend")
                    desctitle = item.get('gamename')
                    descarea1 = item.get('descarea1')
                    descarea2 = item.get('descarea2')
                    rankminibet = item.get('rankminibet')

                    topmultiplieravatar = item.get("avatar_0")
                    topmultiplier = item.get("amount_0")
                    topmultipliernickname = item.get('nickname_0')
                    topmultipliermemberid = item.get("memberid_0")

                    topwinavatar = item.get("avatar_1")
                    topwin = item.get("amount_1")
                    topwinnickname = item.get('nickname_1')
                    topwinmemberid = item.get("memberid_1")

                    ranktype = item.get('ranktype')

                    size = item.get('size')

                    rerobject = item.get("rerobject")
                    if rerobject is not None:
                        rerobject = json.loads(rerobject)
                    else:
                        rerobject = {}

                    rerobjectnew = item.get('rerobjectnew')
                    if rerobjectnew is not None:
                        rerobjectnew = json.loads(rerobjectnew)
                    else:
                        rerobjectnew = {}



                    if rerobjectnew != {}:
                        rerobjectnew_version_data = rerobjectnew.get('v'+ member_ver)
                        if rerobjectnew_version_data is not None:
                            rerobject = rerobjectnew_version_data



                    if None not in [posindex,gameid,enable,posindex_hotsort,posindex_newsort,posindex_mastersort,posindex_newgamesort,posindex_goodranksort]:
                        tempgamelist = {
                            "posindex": posindex,
                            "posindex_hotsort": posindex_hotsort,
                            "posindex_mastersort": posindex_mastersort,
                            "posindex_newsort": posindex_newsort,
                            "posindex_newgamesort": posindex_newgamesort,
                            "posindex_goodranksort": posindex_goodranksort,
                            "gameid": gameid,
                            "enable": bool(enable),
                            "rerobject": rerobject,
                            "size": size,
                            "gametype": gametype,
                            "ranktype": ranktype,
                            "totalrankreward": totalrankreward

                        }
                        tempgamelist["unlocklevel"] = -1 if unlocklevel is None else unlocklevel

                        if topmultiplier is None:
                            tempgamelist["topmultiplieravatar"] = ""
                            tempgamelist["topmultiplier"] = -1
                            tempgamelist["topmultipliermemberid"] = -1
                            tempgamelist["topmultipliernickname"] = ''

                        else:
                            tempgamelist["topmultiplieravatar"] = "" if topmultiplieravatar is None else topmultiplieravatar
                            tempgamelist["topmultiplier"] = topmultiplier
                            tempgamelist["topmultipliermemberid"] = topmultipliermemberid
                            tempgamelist["topmultipliernickname"] = topmultipliernickname


                        if topwin is None:
                            tempgamelist["topwinavatar"] = ""
                            tempgamelist["topwin"] = -1
                            tempgamelist["topwinmemberid"] = -1
                            tempgamelist["topwinnickname"] = ''

                        else:
                            tempgamelist["topwinavatar"] = "" if topwinavatar is None else topwinavatar
                            tempgamelist["topwin"] = topwin
                            tempgamelist["topwinmemberid"] = topwinmemberid
                            tempgamelist["topwinnickname"] = topwinnickname


                        # if historyrankstart is None or historyrankend is None:
                        #     tempgamelist["historyrankstart"] = -1
                        #     tempgamelist["historyrankend"] = -1
                        # else:
                        #     tempgamelist["historyrankstart"] = historyrankstart
                        #     tempgamelist["historyrankend"] = historyrankend

                        if desctitle is None:
                            desctitle = ''
                        if descarea1 is None:
                            descarea1 = ''
                        if descarea2 is None:
                            descarea2 = ''
                        if rankminibet is None:
                            rankminibet = 0
                        tempgamelist['desctitle'] = desctitle
                        tempgamelist['descarea1'] = descarea1
                        tempgamelist['descarea2'] = descarea2
                        tempgamelist['rankminibet'] = rankminibet
                        # 檢查是否有值為空
                        if None not in tempgamelist.values():
                            gamelist.append(tempgamelist.copy())

                            del tempgamelist['posindex']
                            del tempgamelist['posindex_hotsort']
                            del tempgamelist['posindex_mastersort']
                            del tempgamelist['posindex_newsort']
                            del tempgamelist['posindex_newgamesort']
                            del tempgamelist['posindex_goodranksort']

                            del tempgamelist['gameid']
                            tempclientdatagamelist[gameid] = tempgamelist


                    else:
                        result = pg_general.Apiresult.dbnodata


                # 抓 fish 資料
                fishsort = []

                command = 'select * from gamefish'
                datalen, data = await self.getdbdata(logintoken,command,True)
                if datalen >0 :
                    for item in data:
                        gameid = item.get('gameid')
                        gametype = item.get('gametype')
                        desctitle = item.get('gamename')
                        unlocklevel = item.get('unlocklevel')
                        descarea1 = item.get('descarea1')
                        descarea2 = item.get('descarea2')
                        enable = item.get('enable')
                        sortpos = json.loads(item.get('sortpos'))


                        tempclientdatagamelist[gameid] = {
                            "gametype": gametype,
                            "desctitle": desctitle,
                            "unlocklevel": unlocklevel,
                            "descarea1": descarea1,
                            "descarea2": descarea2,
                            "enable":enable
                        }

                        for item in sortpos.keys():
                            fishsort.append((
                                gameid,
                                item,           # sort type
                                sortpos[item]   # sort pos
                            ))


                if len(gamelist) > 0:

                    clientdata['gamelist'] = tempclientdatagamelist

                    gamelist = sorted(gamelist, key=lambda k:(k['posindex']),reverse=False)
                    clientdata['normalsort'] = [item.get('gameid') for item in gamelist ]

                    gamelist = sorted(gamelist, key=lambda k:(k['posindex_goodranksort']),reverse= False)
                    clientdata['goodranksort'] = [item.get('gameid') for item in gamelist if item.get('posindex_goodranksort') !=-1]

                    gamelist = sorted(gamelist,key=lambda  k:(k['posindex_hotsort']),reverse=False)
                    clientdata['hotsort'] = [item.get('gameid') for item in gamelist if item.get('posindex_hotsort')!=-1]

                    gamelist = sorted(gamelist, key=lambda k: (k['posindex_mastersort']), reverse=False)
                    clientdata['mastersort'] = [item.get('gameid') for item in gamelist if item.get('posindex_mastersort')!=-1]

                    gamelist = sorted(gamelist, key=lambda k: (k['posindex_newsort']), reverse=False)
                    clientdata['newsort'] = [item.get('gameid') for item in gamelist if item.get('posindex_newsort')!=-1]

                    gamelist = sorted(gamelist,key=lambda k:(k['posindex_newgamesort']), reverse=False)
                    clientdata['newgamesort'] = [item.get('gameid') for item in gamelist if item.get('posindex_newgamesort') !=-1]

                    for item in fishsort:
                        gameid = item[0]
                        sorttype = item[1]
                        sortpos = item[2]

                        if clientdata.get(sorttype) is not None:
                            clientdata[sorttype].insert(sortpos,gameid)




                    result = pg_general.Apiresult.success
                # else:
                #     result = pg_general.Apiresult.othererror
            else:
                result = pg_general.Apiresult.dbnodata
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgamelist ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgamelist except:{0}'.format(e))

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                           'pg_asqldb:getgamelist result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata

    async def joingame(self, logintoken, memberid, gameid, gametype):
        """
        加入遊戲
        新增遊戲記錄到DB membergamelog
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:joingame logintoken:{0}, memberid:{1}, gameid:{2}, gametype:{3}'.format(logintoken, memberid, gameid, gametype))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        now = pg_general.getutcnow()

        command = 'insert into membergamelog(memberid, gameid, joingametime, logintoken,gametype) values("{0}", "{1}", "{2}", "{3}","{4}")'.format(memberid, gameid, now, logintoken,gametype)
        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            clientdata = {
                "result": 0,
            }
            result = pg_general.Apiresult.success
        else:
            result = pg_general.Apiresult.othererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                           'pg_asqldb:joingame result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
        return result, clientdata

    async def getgamerank(self, logintoken, memberid, gameid,redis_obj):
        """
        取得遊戲龍虎榜單
        DB Tables : gametodayrank , gamethismonthrank, gamehistoryrank
        """

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getgamerank logintoken:{0}, memberid:{1}, gameid:{2}'.format(logintoken, memberid, gameid))
        result = pg_general.Apiresult.connectdberror

        memberid = pg_general.converttype(memberid,int)

        # get rank award setting
        rankawardtodaytopmultipilier = []
        rankawardtodaytopwin = []
        rankawardthismonthtopmultipilier = []
        rankawardthismonthtopwin = []

        # get self avatar
        command = 'select avatar from member where memberid = "{0}"'.format(memberid)
        datalen , data = await self.getdbdata(logintoken, command)
        if datalen <1:
            result = pg_general.Apiresult.connectdberror
            raise ValueError('get member avatar error')

        selfavatar = data.get('avatar')

        # get gamerankaward
        command = 'select * from gamerankaward'
        datalen , data = await self.getdbdata(logintoken, command, True)

        if datalen ==-1:
            result = pg_general.Apiresult.connectdberror
            raise ValueError('get gamerankaward error')

        for item in data:
            ranktype = item.get('ranktype')
            ranktime = item.get('ranktime')

            if ranktype ==0 and ranktime ==0:
                rankawardtodaytopmultipilier = item.get('award').split(',')
                rankawardtodaytopmultipilier = [int(i) for i in rankawardtodaytopmultipilier]
            elif ranktype == 0 and ranktime ==1:
                rankawardthismonthtopmultipilier = item.get('award').split(',')
                rankawardthismonthtopmultipilier = [int(i) for i in rankawardthismonthtopmultipilier]
            elif ranktype == 1 and ranktime == 0:
                rankawardtodaytopwin = item.get('award').split(',')
                rankawardtodaytopwin = [int(i) for i in rankawardtodaytopwin]
            else:
                rankawardthismonthtopwin = item.get('award').split(',')
                rankawardthismonthtopwin = [int(i) for i in rankawardthismonthtopwin]

        # initial data area
        clientdata = {}
        gametodaytopmultipilierrankinfo = []
        gametodaytopwinrankinfo = []
        gamethismonthtopmultipilierrankinfo = []
        gamethismonthtopwinrankinfo = []
        gamehistorytopmultipilierrankinfo = []
        gamehistorytopwinrankinfo = []

        topmultipilierhistoryrankstart = None
        topmultipilierhistoryrankend = None
        topwinhistoryrankstart = None
        topwinhistoryrankend = None

        try:

            selftodaytopmultipilierrankinfo = {
                'rank': -1,
                'amount': 0
            }
            selftodaytopwinrankinfo = {
                'rank': -1,
                'amount': 0
            }

            # 抓每日排名
            # command = 'select * from gametodayrank where gameid="{0}" order by rank'.format(gameid)
            # datalen, data = await self.getdbdata(logintoken, command, True)
            # 改由 redis 抓每日排名
            data = await redis_obj.get_json_value('rank_'+ gameid)
            if data is None:
                datalen = 0
            else:
                datalen = len(data)

            if datalen > 0:
                for item in data:
                    rank = pg_general.converttype(item.get("rank"), int)
                    avatar = pg_general.converttype(item.get("avatar"), str)
                    nickname = pg_general.converttype(item.get("nickname"), str)
                    level = pg_general.converttype(item.get("level"), int)
                    amount = pg_general.converttype(item.get("amount"), int)
                    ranktype = pg_general.converttype(item.get("ranktype"),int)
                    tempmemberid = pg_general.converttype(item.get('memberid'),int)
                    card = pg_general.converttype(item.get('card'),int)

                    if None not in [rank,avatar,nickname,level,amount,ranktype,memberid,card]:
                        extraaward = 0
                        if ranktype ==0 and rank <= len(rankawardtodaytopmultipilier):
                            extraaward = rankawardtodaytopmultipilier[rank-1]
                        else:
                            if rank <= len(rankawardtodaytopwin):
                                extraaward = rankawardtodaytopwin[rank-1]


                        if ranktype == 0: # make selftodaytopmultipilierrankinfo
                            if selftodaytopmultipilierrankinfo.get('rank') == -1 and memberid == tempmemberid:
                                selftodaytopmultipilierrankinfo['rank'] = rank
                                selftodaytopmultipilierrankinfo['amount'] = amount
                        else:               # make selftodaytopwinrankinfo
                            if selftodaytopwinrankinfo.get('rank') == -1 and memberid == tempmemberid:
                                selftodaytopwinrankinfo['rank'] = rank
                                selftodaytopwinrankinfo['amount'] = amount
                        tempgamerankinfo = {
                            "rank": rank,
                            "avatar": avatar,
                            "nickname": nickname,
                            "level": level,
                            "amount": amount,
                            "extraaward": extraaward,
                            "isself": True if memberid == tempmemberid else False,
                            "memberid": tempmemberid,
                            "card": card
                        }
                        if ranktype ==0:
                            gametodaytopmultipilierrankinfo.append(tempgamerankinfo)
                        elif ranktype ==1:
                            gametodaytopwinrankinfo.append(tempgamerankinfo)

            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                raise ValueError('get daily rank error')

            # 抓每月的排名
            command = 'select * from gamethismonthrank where gameid="{0}" order by rank'.format(gameid)
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen > 0:
                for item in data:
                    rank = pg_general.converttype(item.get("rank"), int)
                    avatar = pg_general.converttype(item.get("avatar"), str)
                    nickname = pg_general.converttype(item.get("nickname"), str)
                    level = pg_general.converttype(item.get("level"), int)
                    amount = pg_general.converttype(item.get("amount"), int)
                    ranktype = pg_general.converttype(item.get("ranktype"), int)
                    tempmemberid = pg_general.converttype(item.get('memberid'),int)
                    card = pg_general.converttype(item.get('card'),int)

                    if None not in [rank, avatar, nickname, level, amount, ranktype,card]:
                        if ranktype ==0 and len(rankawardthismonthtopmultipilier)>=rank:
                            extraaward = rankawardthismonthtopmultipilier[rank-1]
                        elif ranktype ==1 and len(rankawardthismonthtopwin) >= rank:
                            extraaward = rankawardthismonthtopwin[rank-1]
                        else:
                            extraaward = 0
                        tempgamerankinfo = {
                            "rank": rank,
                            "avatar": avatar,
                            "nickname": nickname,
                            "level": level,
                            "amount": amount,
                            "extraaward": extraaward,
                            "isself": True if memberid == tempmemberid else False,
                            "memberid": tempmemberid,
                            "card": card
                        }

                        # 檢查是否有值為空
                        if ranktype == 0:
                            gamethismonthtopmultipilierrankinfo.append(tempgamerankinfo)
                        elif ranktype == 1:
                            gamethismonthtopwinrankinfo.append(tempgamerankinfo)
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                raise ValueError('get monthly rank error')

            # 抓取 history rank 最高與最低範圍 ranktype =0
            command = 'select max(monthdata) as maxmonth, min(monthdata) as minmonth from gamehistoryrank where ranktype ="0" and gameid ="{0}"'.format(gameid)
            datalen , data = await self.getdbdata(logintoken, command)

            if datalen > 0:
                topmultipilierhistoryrankstart = data.get('minmonth')
                topmultipilierhistoryrankend = data.get('maxmonth')

            # 抓取 history rank 最高與最低範圍 ranktype =1
            command = 'select max(monthdata) as maxmonth, min(monthdata) as minmonth from gamehistoryrank where ranktype ="1" and gameid="{}"'.format(gameid)
            datalen , data = await self.getdbdata(logintoken , command)

            if datalen > 0:
                topwinhistoryrankstart = data.get('minmonth')
                topwinhistoryrankend = data.get('maxmonth')

            # 抓取歷史排名, 先抓全部的 history rank by gameid
            command = 'select * from gamehistoryrank where gameid ="{0}" order by rank'.format(gameid)
            datalen , data = await self.getdbdata(logintoken, command, True)

            if datalen > 0:
                if None not in [topmultipilierhistoryrankstart,topmultipilierhistoryrankend]:
                    for monthdata in range(topmultipilierhistoryrankstart,topmultipilierhistoryrankend+1):
                        tempmonth = monthdata %100
                        if tempmonth >12 or tempmonth ==0:
                            continue
                        tempdata = [item for item in data if item.get('monthdata')==monthdata and item.get('ranktype')==0]
                        for tempdataitem in tempdata:
                            if tempdataitem.get('memberid') == memberid:
                                tempdataitem['isself'] = True
                            else:
                                tempdataitem['isself'] = False
                            # pop memberid
                            # if tempdataitem.get('memberid') is not None:
                            #     tempdataitem.pop('memberid')

                        tempdict = {
                            "month": monthdata,
                            "data": tempdata
                        }
                        gamehistorytopmultipilierrankinfo.append(tempdict)
                if None not in [topwinhistoryrankstart,topwinhistoryrankend]:
                    for monthdata in range(topwinhistoryrankstart,topwinhistoryrankend+1):
                        tempmonth = monthdata % 100
                        if tempmonth > 12 or tempmonth == 0:
                            continue
                        tempdata = [item for item in data if item.get('monthdata')==monthdata and item.get('ranktype')==1]
                        for tempdataitem in tempdata:
                            if tempdataitem.get('memberid') == memberid:
                                tempdataitem['isself'] = True
                            else:
                                tempdataitem['isself'] = False
                            # pop memberid
                            # if tempdataitem.get('memberid') is not None:
                            #     tempdataitem.pop('memberid')

                        tempdict = {
                            "month": monthdata,
                            "data": tempdata
                        }
                        gamehistorytopwinrankinfo.append(tempdict)

            # 抓重製時間倒數秒數
            localdatetime = pg_general.get_local_datetime()
            localdate = localdatetime.date()

            endtime = pg_general.strtodatetime(str(localdate) + ' 23:59:59.00')
            resetcountdown = pg_general.converttype((endtime - localdatetime).total_seconds() + 1, int)


            clientdata = {
                "topmultipilierhistoryrankstart": 0 if topmultipilierhistoryrankstart is None else topmultipilierhistoryrankstart,
                "topmultipilierhistoryrankend": 0 if topmultipilierhistoryrankend is None else topmultipilierhistoryrankend,
                "topwinhistoryrankstart": 0 if topwinhistoryrankstart is None else topwinhistoryrankstart,
                "topwinhistoryrankend": 0 if topwinhistoryrankend is None else topwinhistoryrankend,
                "selfavatar": selfavatar,
                "resetcountdown":resetcountdown,
                "selftodaytopmultipilierrankinfo": selftodaytopmultipilierrankinfo,
                "selftodaytopwinrankinfo": selftodaytopwinrankinfo,
                "gametodaytopmultipilierrankinfo":gametodaytopmultipilierrankinfo,
                "gametodaytopwinrankinfo":gametodaytopwinrankinfo,
                "gamethismonthtopmultipilierrankinfo":gamethismonthtopmultipilierrankinfo,
                "gamethismonthtopwinrankinfo":gamethismonthtopwinrankinfo,
                "gamehistorytopmultipilierrankinfo":gamehistorytopmultipilierrankinfo,
                "gamehistorytopwinrankinfo":gamehistorytopwinrankinfo

            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgamerank ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgamerank except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                               'pg_asqldb:getgamerank result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
            return result, clientdata

    async def getleaderrank(self, logintoken, memberid):
        """
        取得陣營排行榜
        從DB  camprankdetail 取得要找的陣營排行榜
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getleaderrank logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        # initial variables area
        clientdata = {}

        richestrankinfo = []
        gametotalrank = []
        likerank = []
        selfrankdata = {}
        selfrichrank = -1
        selfgametotalrank = -1
        selflikerank = -1

        try:
            command = 'select member.avatar,member.nickname,member.level,member.credit,member.activenumber,card from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken, command)

            if datalen < 0:
                result = pg_general.Apiresult.connectdberror
                raise ValueError
            elif datalen == 0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError


            selfavatar = pg_general.converttype(data.get('avatar'),str)
            selfnickname = pg_general.converttype(data.get('nickname'),str)
            selflevel = pg_general.converttype(data.get('level'),int)
            selfcredit = pg_general.converttype(data.get('credit'),int)
            selfactivenumber = data.get('activenumber')
            selfcard = data.get('card')
            selfsumwin = 0
            selflikeamount = 0
            # 富豪榜資料
            command = 'select * from richrank order by rank'
            datalen , data = await self.getdbdata(logintoken,command,True)

            if datalen == -1:
                result = pg_general.Apiresult.connectdberror
                raise ValueError

            if datalen > 0 :
                for item in data:
                    rankmemberid = pg_general.converttype(item.get("memberid"), int)
                    rank = pg_general.converttype(item.get("rank"), int)
                    avatar = pg_general.converttype(item.get("avatar"), str)
                    nickname = pg_general.converttype(item.get("nickname"), str)
                    level = pg_general.converttype(item.get("level"), int)
                    credit = pg_general.converttype(item.get("credit"), int)
                    activenumber = item.get('activenumber')
                    card = item.get('card')

                    if None not in [rankmemberid,rank,avatar,nickname,level,credit,activenumber,card]:
                        # 找出自己的 rank
                        if int(memberid) == rankmemberid:
                            selfrichrank = rank

                        temprichrankinfo = {
                            "rank": rank,
                            "avatar": avatar,
                            "nickname": nickname,
                            "level": level,
                            "credit": credit,
                            "memberid": rankmemberid,
                            "activenumber": activenumber,
                            "card": card
                        }
                        richestrankinfo.append(temprichrankinfo)

            # 積分榜資料
            command = 'select * from gametotalrank'
            datalen , data = await self.getdbdata(logintoken,command,True)
            if datalen > 0:

                gametotalrank = sorted(data, key=lambda k: (k['rank']),reverse=False)
                # find self totalgame rank
                for item in gametotalrank:
                    if item.get('memberid') ==  memberid:
                        selfgametotalrank = item.get('rank')
                        selfsumwin = item.get('sumwin')

            # 人氣榜資料
            command = 'select * from likerank'
            datalen , data = await self.getdbdata(logintoken,command,True)
            if datalen > 0:
                likerank = sorted(data,key=lambda  k:(k['rank']),reverse=False)
                # find self like rank
                for item in likerank:
                    if item.get('memberid') == memberid:
                        selflikerank = item.get('rank')
                        selflikeamount = item.get('likeamount')

            # 抓 settting2.leaderboardactionsetting
            actionrankurl = ''

            command = 'select leaderboardactionsetting from setting2'
            datalen, data = await self.getdbdata(logintoken,command)

            if datalen ==1:
                tmpdict = json.loads(data.get('leaderboardactionsetting'))

                actionrankurl = '' if tmpdict.get('actionhtmlurl') is None else tmpdict.get('actionhtmlurl')

            # 準備 selfrank

            selfrankdata['avatar'] = selfavatar
            selfrankdata['nickname'] = selfnickname
            selfrankdata['level'] = selflevel
            selfrankdata['richrank'] = selfrichrank
            selfrankdata['credit'] = selfcredit
            selfrankdata['memberid'] = memberid
            selfrankdata['activenumber'] = selfactivenumber
            selfrankdata['gametotalrank'] = selfgametotalrank
            selfrankdata['likerank'] = selflikerank
            selfrankdata['card'] = selfcard
            selfrankdata['sumwin'] = selfsumwin
            selfrankdata['likeamount'] = selflikeamount

            clientdata = {
                "selfrankdata":selfrankdata,
                "richestrankinfo": richestrankinfo,
                "gametotalrankinfo": gametotalrank,
                "likerankinfo": likerank,
                "rankactionurl": actionrankurl
            }
            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getleaderrank except : {0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                               'pg_asqldb:getleaderrank result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken, clientdata))
            return result, clientdata


    async def setlobbyip(self,ip):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'pg_asqldb:setlobbyip IP:{0}'.format(ip))
        result = pg_general.Apiresult.connectdberror

        command = 'select * from lobbyserversetting where ip = "{0}"'.format(ip)
        datalen, data = await self.getdbdata('setlobbyserverip', command, True)

        if datalen == 0:
            command = 'insert into lobbyserversetting (ip) values ("{0}")'.format(ip)
            resultdata = await self.updatedbdata('setlobbyserverip',command)
            if resultdata == True:
                result = pg_general.Apiresult.success
        elif datalen > 0:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,'pg_asqldb:setlobbyip IP:{0},result:{1}'.format(ip,result))

        return result

    async def callpsgamelist(self,gamelist):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:callpsgamelist gamelist:{0}'.format(gamelist))
        result = pg_general.Apiresult.connectdberror

        command = 'delete from gamelist'
        dbresult = await self.updatedbdata("delete all gamelist",command)

        # find all values

        parametertext = ''

        for item in gamelist:
            gameid = item.get('game_id')
            gamename = item.get('game_name').get('zh-TW')
            gamedescription = item.get('feature')
            enable = 1
            unlocklevel =0
            minbet = item.get('min_bet')
            maxbet = item.get('max_bet')

            if parametertext == '' :
                parametertext = '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(gameid,gamename,gamedescription,enable,unlocklevel,minbet,maxbet)
            else:
                parametertext = parametertext + ',("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(gameid,gamename,gamedescription,enable,unlocklevel,minbet,maxbet)

        if dbresult == True:
            command = 'insert into gamelist (gameid,gamename,gamedescription,enable,unlocklevel,minbet,maxbet) values {0}'.format(parametertext)
            dbresult = await self.updatedbdata("insert new game list",command)

            if dbresult == True:
                result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:callpsgamelist gamelist:{0},result:{1}'.format(gamelist, result))
        return result

    async def psapi_signin(self,logintoken , memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:psapi_signin logintoken:{0},memberid:{1}'.format(logintoken,memberid))
        result = pg_general.Apiresult.connectdberror

        command = 'select memberid from member where memberid ="{0}" and logintoken="{1}"'.format(memberid,logintoken)
        datalen , data = await self.getdbdata(logintoken,command,fromwritedb=True)

        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            result = pg_general.Apiresult.success


        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_signin logintoken:{0},memberid:{1},result:{2}'.format(logintoken,memberid, result))
        return result

    async def psapis_signin(self,logintoken , memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:psapis_signin logintoken:{0},memberid:{1}'.format(logintoken,memberid))
        result = pg_general.Apiresult.connectdberror

        command = 'select memberid from member where memberid ="{0}" and logintoken="{1}"'.format(memberid,logintoken)
        datalen , data = await self.getdbdata(logintoken,command,fromwritedb=True)

        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_signin logintoken:{0},memberid:{1},result:{2}'.format(logintoken,memberid, result))
        return result

    async def psapit_signin(self,logintoken , memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:psapit_signin logintoken:{0},memberid:{1}'.format(logintoken,memberid))
        result = pg_general.Apiresult.connectdberror

        command = 'select memberid from member where memberid ="{0}" and logintoken="{1}"'.format(memberid,logintoken)
        datalen , data = await self.getdbdata(logintoken,command,fromwritedb=True)

        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_signin logintoken:{0},memberid:{1},result:{2}'.format(logintoken,memberid, result))
        return result


    async def psapi_authenticate(self,logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_authenticate logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        command = 'select memberid,credit,account_type,nickname from member where logintoken ="{0}"'.format(logintoken)
        datalen , data = await self.getdbdata(logintoken,command)
        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            memberid = pg_general.converttype(data.get("memberid"),str)
            credit = pg_general.converttype(data.get("credit"),int)
            account_type = pg_general.converttype(data.get('account_type'),int)
            nickname = data.get('nickname')
            if None not in [memberid,credit]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "memberid": memberid,
                    "credit": credit,
                    "account_type": account_type,
                    "nickname": nickname
                }

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_authenticate logintoken:{0},result:{1},clientdata:{2}'.format(logintoken, result, clientdata))
        return result, clientdata

    async def psapis_authenticate(self,logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_authenticate logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        command = 'select memberid, silvercredit,account_type,nickname from member where logintoken ="{0}"'.format(logintoken)
        datalen , data = await self.getdbdata(logintoken,command)
        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            memberid = pg_general.converttype(data.get("memberid"),str)
            credit = pg_general.converttype(data.get("silvercredit"),int)
            account_type = pg_general.converttype(data.get('account_type'), int)
            nickname = data.get('nickname')
            if None not in [memberid,credit]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "memberid": memberid,
                    "silvercredit": credit,
                    "account_type": account_type,
                    "nickname": nickname
                }

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_authenticate logintoken:{0},result:{1},clientdata:{2}'.format(logintoken, result, clientdata))
        return result, clientdata

    async def psapit_authenticate(self,logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_authenticate logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        command = 'select memberid, silvercredit from member where logintoken ="{0}"'.format(logintoken)
        datalen , data = await self.getdbdata(logintoken,command)
        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            memberid = pg_general.converttype(data.get("memberid"),str)
            credit = pg_general.converttype(data.get("silvercredit"),int)
            if None not in [memberid,credit]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "memberid": memberid,
                    "silvercredit": credit
                }

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_authenticate logintoken:{0},result:{1},clientdata:{2}'.format(logintoken, result, clientdata))
        return result, clientdata


    async def writecardchangelog(self, param):
        try:

            command = 'insert into cardlevelchangelog (memberid,logtime,oldcard,newcard,memo) values(%s,%s,%s,%s,%s)'
            insertresult ,index = await self.insertdbdata('write card level change log', command, True, param)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:writecardchangelog Exception : {}'.format(e))

    async def buycardlevelup_future(self,apporweb,logintoken, memberid, card, redis_obj, cardinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:buycardlevelup_future logintoken:{0},memberid:{1},apporweb:{2}'.format(logintoken, memberid,apporweb))

            # get all sum bet from redis
            valuelist = await redis_obj.hvals('cardbuy_{}'.format(memberid))
            if len(valuelist)> 0:
                if card in [0, 1, 2, 3, 4]:  # 如果會員等級是5，那也不用升級了
                    valuelist = list(map(int, valuelist))
                    cardbuy = sum(valuelist)

                    for i in [1, 2, 3, 4, 5]:  # 從n等升i等
                        card_level = card + i  # 取得門檻的等級
                        nextlevelneedbuy = cardinfo[card_level].get('twomonthaccbuy')  # 取得下一等所需花費的金額
                        if cardbuy < nextlevelneedbuy:  # 如果2個月花費未達門檻
                            card_level = card_level - 1  # 則回到上一個等級
                            break
                        if card_level >= 5:  # 原等級 + 升n等 >= 5
                            break

                    upgrade_level = card_level - card  # 升n等 = 欲達n等 - 原等級

                    if upgrade_level > 0:  # 如果有升等才要做，沒升等就不用進去了
                        # 清空所有 bethistory from redis
                        nowutctime = pg_general.getutcnow_datetime()

                        await redis_obj.del_key('bethistory_gold_{}'.format(memberid))
                        await redis_obj.del_key('bethistory_silver_{}'.format(memberid))
                        await redis_obj.del_key('cardbuy_{}'.format(memberid))
                        await redis_obj.del_key('cardlevelupdays_{}'.format(memberid))

                        # write 升級卡別 log
                        asyncio.ensure_future(self.writecardchangelog([[memberid,nowutctime,card,card+upgrade_level,'buy']]))

                        # update member card
                        command = 'update member set card = card+{},cardlevelchangetime="{}" where memberid="{}"'.format(upgrade_level,nowutctime,memberid)
                        updateresult = await self.updatedbdata(logintoken,command)

                        # 通知該玩家升級卡別
                        # 抓取 對象的 lobbyserverip from redis
                        lobbyserverip = await redis_obj.get_value('online_{}'.format(memberid))

                        if lobbyserverip is not None and lobbyserverip != [] and logintoken is not None:
                            if len(lobbyserverip) > 0:
                                try:
                                    if env_setting.LOCAL_SERVER == False:
                                        realurl = 'http://{}/broadcasttoall'.format(lobbyserverip)
                                    else:
                                        realurl = 'http://127.0.0.1/broadcasttoall'
                                    sendmsg = {
                                        "type": SendMsgType.server_to_client,
                                        "logintoken": logintoken,
                                        "msg": {"commandid": 3000013, "data": {"card": card+upgrade_level}}
                                    }

                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(realurl, json=sendmsg) as response:
                                            if response.status == 200:
                                                data = await response.text()
                                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                    'sendcardlevelup response:{0},sendmsg:{1}'.format(data,sendmsg))



                                except Exception as e:
                                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                        'sendcardlevelup exception:{0}'.format(e))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:buycardlevelup_future ValueError:{0} ,memberid:{1}'.format(e, memberid))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:buycardlevelup_future except:{0} ,memberid:{1}'.format(e, memberid))
        finally:
            pass


    async def betcardlevelup_future(self,logintoken,memberid,card,redis_obj,cardinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:betcardlevelup_future logintoken:{0},memberid:{1}'.format(logintoken, memberid))

            # get all sum bet from redis
            valuelist = await redis_obj.hvals('bethistory_gold_{}'.format(memberid))
            if len(valuelist)> 0:
                valuelist = list(map(int, valuelist))
                cardbet = sum(valuelist)
                nextlevelneedbet = cardinfo[card+1].get('twomonthaccbet')
                if nextlevelneedbet > 0:
                    if cardbet >= nextlevelneedbet: # 生卡等級
                        # 清空所有 bethistory from redis
                        nowutctime = pg_general.getutcnow_datetime()

                        await redis_obj.del_key('bethistory_gold_{}'.format(memberid))
                        await redis_obj.del_key('bethistory_silver_{}'.format(memberid))
                        await redis_obj.del_key('cardbuy_{}'.format(memberid))
                        await redis_obj.del_key('cardlevelupdays_{}'.format(memberid))

                        # write 升級卡別 log
                        asyncio.ensure_future(self.writecardchangelog([[memberid,nowutctime,card,card+1,'bet']]))

                        # update member card
                        command = 'update member set card = card+1,cardlevelchangetime="{1}" where memberid="{0}"'.format(memberid,nowutctime)
                        updateresult = await self.updatedbdata(logintoken,command)

                        # 通知該玩家升級卡別
                        # 抓取 對象的 lobbyserverip from redis
                        lobbyserverip = await redis_obj.get_value('online_{}'.format(memberid))

                        if lobbyserverip is not None and lobbyserverip != []:
                            if len(lobbyserverip) > 0:
                                try:
                                    if env_setting.LOCAL_SERVER == False:
                                        realurl = 'http://{}/broadcasttoall'.format(lobbyserverip)
                                    else:
                                        realurl = 'http://127.0.0.1/broadcasttoall'
                                    sendmsg = {
                                        "type": SendMsgType.server_to_client,
                                        "logintoken": logintoken,
                                        "msg": {"commandid": 3000013, "data": {"card": card+1}}
                                    }

                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(realurl, json=sendmsg) as response:
                                            if response.status == 200:
                                                data = await response.text()
                                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                    'sendcardlevelup response:{0},sendmsg:{1}'.format(data,sendmsg))



                                except Exception as e:
                                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                        'sendcardlevelup exception:{0}'.format(e))



        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:betcardlevelup_future ValueError:{0} ,logintoken:{1}'.format(e, logintoken))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:betcardlevelup_future except:{0} ,logintoken:{1}'.format(e, logintoken))
        finally:
            pass


    async def make_seats_data_update(self,redis_obj,clientdata,gametype):
        try:
            result = False
            resultdata = {}

            logintoken = clientdata.get('token')
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:make_seats_data_update start, clientdata:{0} ,logintoken:{1}'.format(clientdata, logintoken))

            has_bonus = clientdata.get('has_bonus')
            seat_data = clientdata.get('seat_data')
            multipilier = clientdata.get('multipilier')

            tempgameid = seat_data.split('_')[1]
            tempseatnum = seat_data.split('_')[2]

            if gametype == 'gold':
                seatkey = 'goldseats_{}@{}'.format(tempgameid,tempseatnum)
            else:
                seatkey = 'silverseats_{}@{}'.format(tempgameid,tempseatnum)

            # get goldseats_{}@{} information
            valuelist = await redis_obj.hmget(seatkey,["unopenturn","avgturn","his1turn","his2turn","his3turn","his1multi","his2multi","his3multi"])
            if valuelist is None or valuelist == []:
                raise Exception('get seat data error')

            unopenturn = pg_general.converttype(valuelist[0],int)
            avgturn = pg_general.converttype(valuelist[1],int)
            his1turn = pg_general.converttype(valuelist[2],int)
            his2turn = pg_general.converttype(valuelist[3],int)
            his3turn = pg_general.converttype(valuelist[4],int)
            his1multi = pg_general.converttype(valuelist[5],int)
            if his1multi is None:
                his1multi = 0
            his2multi = pg_general.converttype(valuelist[6],int)
            if his2multi is None:
                his2multi = 0
            his3multi = pg_general.converttype(valuelist[7],int)
            if his3multi is None:
                his3multi = 0




            unopenturn +=1
            if has_bonus ==0: # 沒開
               pass
            else:       # 有開

                his3turn = his2turn
                his3multi = his2multi

                his2turn = his1turn
                his2multi = his1multi

                his1turn = unopenturn
                his1multi = multipilier
                unopenturn = 0
                avgturn = pg_general.converttype((his1turn+his2turn+his3turn)/3,int)

            resultdata = {
                "unopenturn": unopenturn,
                "avgturn": avgturn,
                "his1turn": his1turn,
                "his2turn": his2turn,
                "his3turn": his3turn,
                "his1multi": his1multi,
                "his2multi": his2multi,
                "his3multi": his3multi,
                "gameid": tempgameid,
                "seatnum": tempseatnum
            }

            updatedata = {
                "unopenturn": unopenturn,
                "avgturn": avgturn,
                "his1turn": his1turn,
                "his2turn": his2turn,
                "his3turn": his3turn,
                "his1multi": his1multi,
                "his2multi": his2multi,
                "his3multi": his3multi
            }

            await redis_obj.hmset(seatkey,updatedata)

            result = True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_seats_data_update except:{0} ,logintoken:{1}'.format(e, logintoken))

        return result , resultdata

    async def psapi_bet(self,redis_obj,logintoken, betdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_bet logintoken:{0},betdata:{1}'.format(logintoken,betdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        txn_id = betdata.get("txn_id")
        total_bet = betdata.get("total_bet")
        game_id = betdata.get("game_id")
        subgame_id = betdata.get("subgame_id")
        bettime = betdata.get("bettime")

        try:
            # 先確認 logintoken
            command = 'select credit,lobbyserverip,memberid,card from member where logintoken="{0}"'.format(logintoken)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata ={'status_code':1}
                raise ValueError('status_code 1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')

            beforecredit = pg_general.converttype(data.get('credit'),int)
            memberid = pg_general.converttype(data.get("memberid"),int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"),str)

            card = data.get('card')

            # update member
            command = 'update member set credit=credit-"{0}" where memberid ="{1}" and credit >="{0}"'.format(total_bet, memberid)
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            if updaterows < 1:
                result = pg_general.Apiresult.balanceerror
                clientdata = {'status_code': 3}
                raise ValueError('status_code 3')

            aftercredit = beforecredit - total_bet

            # 確認是否可以寫入 bethistory , 等於檢查 txn_id 是否重複
            command = 'insert into bethistory (txn_id,memberid,beforecredit,aftercredit,gameid,total_bet,logintoken,bettime,subgameid)' \
                      'values ("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}")'.format(txn_id,memberid,beforecredit,aftercredit,game_id,total_bet,logintoken,bettime,subgame_id)
            insertresult , index = await self.insertdbdata(logintoken,command)
            if insertresult == False:
                result = pg_general.Apiresult.othererror
                clientdata = {'status_code': 2}
                raise ValueError('status_code 2')


            result = pg_general.Apiresult.success
            clientdata = {
                "memberid": memberid,
                "lobbyserverip": lobbyserverip,
                "aftercredit": aftercredit,
                "card": card
            }
            # 寫入 redis hincyby daybet_date 設定  ttl = 10 天 864000 秒
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()
            await redis_obj.hincrby('daybet_{}'.format(twdatetimestr),'{}'.format(memberid),total_bet)
            await redis_obj.incrby('totaldaybet_{}'.format(twdatetimestr),total_bet)

            # 做金爽榜及時榜單 total bet 累積
            twtodaydate = pg_general.get_tw_datetime().date()
            if twtodaydate.day >=1 and twtodaydate.day<=15:
                await redis_obj.incrby('totalmonthbet_{}'.format(twdatetimemonthstr),total_bet)
            else:
                await redis_obj.incrby('totalmonthbet2_{}'.format(twdatetimemonthstr),total_bet)

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_bet ValueError:{0} ,logintoken:{1}'.format(e, logintoken))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_bet except:{0} ,logintoken:{1}'.format(e,logintoken))
        finally:
            pass


        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_bet logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                           result,
                                                                                                           clientdata))
        return result, clientdata

    async def psapis_bet(self,redis_obj,logintoken, betdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_bet logintoken:{0},betdata:{1}'.format(logintoken, betdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        txn_id = betdata.get("txn_id")
        total_bet = betdata.get("total_bet")
        game_id = betdata.get("game_id")
        subgame_id = betdata.get("subgame_id")
        bettime = betdata.get("bettime")

        try:
            # 先確認 logintoken , silvercredit 是否足夠
            command = 'select silvercredit , lobbyserverip,memberid from member where logintoken="{0}"'.format(
                logintoken)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')

            beforecredit = pg_general.converttype(data.get("silvercredit"), int)
            memberid = pg_general.converttype(data.get("memberid"), int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"), str)

             # update member
            command = 'update member set silvercredit=silvercredit - "{0}" where memberid ="{1}" and silvercredit >= "{0}"'.format(total_bet, memberid)
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            if updaterows < 1: # 確認 credit 是否足夠 bet
                result = pg_general.Apiresult.balanceerror
                clientdata = {'status_code': 3}
                raise ValueError('status_code 3')


            aftercredit = beforecredit - total_bet

            # 確認是否可以寫入 bethistory , 等於檢查 txn_id 是否重複
            command = 'insert into bethistory_s (txn_id,memberid,beforecredit,aftercredit,gameid,total_bet,logintoken,bettime,subgameid)' \
                      'values ("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}")'.format(txn_id, memberid,
                                                                                              beforecredit, aftercredit,
                                                                                              game_id, total_bet,
                                                                                              logintoken, bettime,
                                                                                              subgame_id)
            insertresult, index = await self.insertdbdata(logintoken, command)
            if insertresult == False:
                result = pg_general.Apiresult.othererror
                clientdata = {'status_code': 2}
                raise ValueError('status_code 2')

            result = pg_general.Apiresult.success
            clientdata = {
                "memberid": memberid,
                "lobbyserverip": lobbyserverip,
                "aftercredit": aftercredit

            }
            # 寫入 redis hincyby daybet_date 設定  ttl = 10 天 864000 秒
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()
            await redis_obj.hincrby('daybets_{}'.format(twdatetimestr), '{}'.format(memberid), total_bet)
            await redis_obj.incrby('totaldaybets_{}'.format(twdatetimestr), total_bet)
            await redis_obj.incrby('totalmonthbets_{}'.format(twdatetimemonthstr), total_bet)
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_bet ValueError:{0} ,logintoken:{1}'.format(e, logintoken))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_bet except:{0} ,logintoken:{1}'.format(e, logintoken))
        finally:
            pass

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_bet logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                  result,
                                                                                                  clientdata))

        return result, clientdata

    async def psapit_bet(self,redis_obj,logintoken, betdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_bet logintoken:{0},betdata:{1}'.format(logintoken, betdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        txn_id = betdata.get("txn_id")
        total_bet = betdata.get("total_bet")
        game_id = betdata.get("game_id")
        subgame_id = betdata.get("subgame_id")
        bettime = betdata.get("bettime")

        try:
            # 先確認 logintoken , silvercredit 是否足夠
            command = 'select silvercredit , lobbyserverip,memberid,tutorialbetfinish from member where logintoken="{0}"'.format(
                logintoken)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')

            beforecredit = pg_general.converttype(data.get("silvercredit"), int)
            memberid = pg_general.converttype(data.get("memberid"), int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"), str)
            tutorialbetfinish = data.get('tutorialbetfinish')
            if tutorialbetfinish != 0:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')


             # update member
            command = 'update member set silvercredit=silvercredit - "{0}",tutorialbetfinish = "1" where memberid ="{1}" and silvercredit >= "{0}"'.format(total_bet, memberid)
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            if updaterows < 1: # 確認 credit 是否足夠 bet
                result = pg_general.Apiresult.balanceerror
                clientdata = {'status_code': 3}
                raise ValueError('status_code 3')


            aftercredit = beforecredit - total_bet

            # 確認是否可以寫入 bethistory , 等於檢查 txn_id 是否重複
            command = 'insert into bethistory_s (txn_id,memberid,beforecredit,aftercredit,gameid,total_bet,logintoken,bettime,subgameid)' \
                      'values ("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}")'.format(txn_id, memberid,
                                                                                              beforecredit, aftercredit,
                                                                                              game_id, total_bet,
                                                                                              logintoken, bettime,
                                                                                              126)
            insertresult, index = await self.insertdbdata(logintoken, command)
            if insertresult == False:
                result = pg_general.Apiresult.othererror
                clientdata = {'status_code': 2}
                raise ValueError('status_code 2')

            result = pg_general.Apiresult.success
            clientdata = {
                "memberid": memberid,
                "lobbyserverip": lobbyserverip,
                "aftercredit": aftercredit

            }
            # 寫入 redis hincyby daybet_date 設定  ttl = 10 天 864000 秒
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()
            await redis_obj.hincrby('daybets_{}'.format(twdatetimestr), '{}'.format(memberid), total_bet)
            await redis_obj.incrby('totaldaybets_{}'.format(twdatetimestr), total_bet)
            await redis_obj.incrby('totalmonthbets_{}'.format(twdatetimemonthstr), total_bet)
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapit_bet ValueError:{0} ,logintoken:{1}'.format(e, logintoken))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapit_bet except:{0} ,logintoken:{1}'.format(e, logintoken))
        finally:
            pass

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_bet logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                  result,
                                                                                                  clientdata))

        return result, clientdata


    async def psapi_result(self,redis_obj,logintoken, apiresultdata,rankminwin,rankminmultipilier):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_result logintoken:{0},apiresultdata:{1}'.format(logintoken, apiresultdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        txn_id = apiresultdata.get("txn_id")
        total_win = apiresultdata.get("total_win")
        bonus_win = apiresultdata.get("bonus_win")
        base_win = total_win - bonus_win
        game_id = apiresultdata.get("game_id")
        subgame_id = apiresultdata.get("subgame_id")
        resulttime = apiresultdata.get("resulttime")
        has_bonus = apiresultdata.get("has_bonus")

        try:
            # 確認 logintoken 是否有效
            command = 'select lobbyserverip, memberid, credit,nickname,avatar,card,level from member where logintoken="{0}"'.format(logintoken)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code':1,"balance":0}
                raise ValueError('1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance":0}
                raise ValueError('2')


            memberid = pg_general.converttype(data.get("memberid"),int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"),str)
            beforecredit = pg_general.converttype(data.get("credit"),int)
            aftercredit = beforecredit + total_win
            nickname = data.get('nickname')
            avatar = data.get('avatar')
            card = data.get('card')
            level = data.get('level')

            # 確認 txn_id 是否已經寫過 resutltime
            command = 'select bethistory.resulttime,game.gamename,memberid from bethistory,game where bethistory.txn_id ="{0}" and bethistory.gameid = game.gameid'.format(txn_id)
            datalen, data = await self.getdbdata(logintoken, command,fromwritedb=True)
            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2, "balance": 0}
                raise ValueError('3')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('4')

            if data.get("resulttime") is not None:
                result = pg_general.Apiresult.success
                clientdata = {'status_code': 99, "balance":0}
                raise ValueError('5')

            gamename = data.get('gamename')
            betmemberid = pg_general.converttype(data.get('memberid'),int)


            # 確認 txn_id in bethistory
            command = 'update bethistory set total_win="{0}",base_win="{1}",bonus_win="{2}",resulttime="{3}",has_bonus="{5}" where txn_id="{4}"'.format(total_win,base_win,bonus_win,resulttime,txn_id,has_bonus)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2,"balance":0}
                raise ValueError('6')


            if betmemberid != memberid:  # 此筆單不是這位的
                result = pg_general.Apiresult.success
                clientdata = {'status_code':98,"balance": beforecredit}
                raise ValueError('98,betmemberid:{},memberid:{}'.format(betmemberid,memberid))

            # 抓 bethistroy 該筆單的 total_bet
            command = 'select total_bet from bethistory where txn_id ="{0}"'.format(txn_id)
            datalen , data = await self.getdbdata(logintoken,command,fromwritedb=True)


            if datalen > 0:
                total_bet = data.get('total_bet')

            # update member credit
            command = 'update member set credit=credit+"{0}" where memberid ="{1}"'.format(total_win,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code':1,"balance":0}
                raise ValueError('7')

            result = pg_general.Apiresult.success
            clientdata = {
                "lobbyserverip": lobbyserverip,
                "memberid": memberid,
                "aftercredit": aftercredit,
                "total_bet": total_bet,
                "nickname": nickname,
                "avatar": avatar,
                "gamename": gamename,
                "card": card
            }

            tmpmultipilier = pg_general.converttype(total_win/total_bet,int)

            # 寫入 redis totaldaywin
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()

            # # set memberinfo
            # memberinfojson = {
            #     "nickname": nickname,
            #     "avatar": avatar,
            #     "card": card,
            #     "level": level
            # }
            # await redis_obj.hset('memberinfo_{}'.format(twdatetimemonthstr),'{}'.format(memberid),json.dumps(memberinfojson)) # ttl two month
            # if total_win >= rankminwin:
            #     await redis_obj.hincrby('daywin_{}'.format(twdatetimestr), '{}'.format(memberid), total_win)
            #if tmpmultipilier >= rankminmultipilier:
            #    await redis_obj.hincrby('daymultipilier_{}'.format(twdatetimestr), '{}'.format(memberid), tmpmultipilier)
            # await redis_obj.hincrby('monthwin_{}'.format(twdatetimemonthstr),'{}'.format(memberid), total_win)
            await redis_obj.incrby('totaldaywin_{}'.format(twdatetimestr), total_win)
            await redis_obj.incrby('totalmonthwin_{}'.format(twdatetimemonthstr),total_win)

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_result logintoken:{0},ValueError:{1}'.format(logintoken, e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_result logintoken:{0},except:{1}'.format(logintoken, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapi_result logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                      result,
                                                                                                      clientdata))
            return result, clientdata


    async def psapis_result(self,redis_obj,logintoken, apiresultdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_result logintoken:{0},apiresultdata:{1}'.format(logintoken, apiresultdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        txn_id = apiresultdata.get("txn_id")
        total_win = apiresultdata.get("total_win")
        bonus_win = apiresultdata.get("bonus_win")
        base_win = total_win - bonus_win
        game_id = apiresultdata.get("game_id")
        subgame_id = apiresultdata.get("subgame_id")
        resulttime = apiresultdata.get("resulttime")
        has_bonus = apiresultdata.get("has_bonus")

        try:
            # 確認 logintoken 是否有效
            command = 'select lobbyserverip, memberid, silvercredit,nickname,avatar,card from member where logintoken="{0}"'.format(logintoken)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code':1,"balance":0}
                raise ValueError('1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance":0}
                raise ValueError('2')


            memberid = pg_general.converttype(data.get("memberid"),int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"),str)
            beforecredit = pg_general.converttype(data.get("silvercredit"),int)
            aftercredit = beforecredit + total_win
            nickname = data.get('nickname')
            avatar = data.get('avatar')
            card = data.get('card')

            # 確認 txn_id 是否已經寫過 resutltime
            command = 'select total_bet,game.gamename,resulttime,memberid from bethistory_s,game where game.gameid = bethistory_s.gameid and txn_id ="{0}"'.format(txn_id)
            datalen, data = await self.getdbdata(logintoken, command,fromwritedb=True)
            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2, "balance": 0}
                raise ValueError('3')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('4')

            if data.get("resulttime") is not None:
                result = pg_general.Apiresult.success
                clientdata = {'status_code': 99, "balance":0}
                raise ValueError('5')

            betmemberid = pg_general.converttype(data.get('memberid'),int)
            total_bet = data.get('total_bet')
            gamename = data.get('gamename')

            # 確認 txn_id in bethistory
            command = 'update bethistory_s set total_win="{0}",base_win="{1}",bonus_win="{2}",resulttime="{3}",has_bonus="{5}" where txn_id="{4}"'.format(total_win,base_win,bonus_win,resulttime,txn_id,has_bonus)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2,"balance":0}
                raise ValueError('6')

            if betmemberid != memberid:  # 此筆單不是這位的
                result = pg_general.Apiresult.success
                clientdata = {'status_code': 98, "balance": beforecredit}
                raise ValueError('98')

            # # 抓 bethistroy 該筆單的 total_bet
            # command = 'select total_bet from bethistory_s where txn_id ="{0}"'.format(txn_id)
            # datalen , data = await self.getdbdata(logintoken,command,fromwritedb=True)
            #
            #
            # if datalen > 0:
            #     total_bet = data.get('total_bet')

            # update member credit
            command = 'update member set silvercredit=silvercredit+"{0}" where memberid ="{1}"'.format(total_win,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code':1,"balance":0}
                raise ValueError('7')

            result = pg_general.Apiresult.success
            clientdata = {
                "lobbyserverip": lobbyserverip,
                "memberid": memberid,
                "aftercredit": aftercredit,
                "total_bet": total_bet,
                "nickname": nickname,
                "avatar": avatar,
                "card": card,
                "gamename": gamename

            }
            # 寫入 redis totaldaywin
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()
            # await redis_obj.hincrby('daywins_{}'.format(twdatetimestr), '{}'.format(memberid), total_win)
            # await redis_obj.hincrby('monthwins_{}'.format(twdatetimemonthstr), '{}'.format(memberid), total_win)
            await redis_obj.incrby('totaldaywins_{}'.format(twdatetimestr), total_win)
            await redis_obj.incrby('totalmonthwins_{}'.format(twdatetimemonthstr), total_win)

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_result logintoken:{0},ValueError:{1}'.format(logintoken, e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_result logintoken:{0},except:{1}'.format(logintoken, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapis_result logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                      result,
                                                                                                      clientdata))
            return result, clientdata
    
    async def psapit_result(self,redis_obj,logintoken, apiresultdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_result logintoken:{0},apiresultdata:{1}'.format(logintoken, apiresultdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        txn_id = apiresultdata.get("txn_id")
        total_win = apiresultdata.get("total_win")
        bonus_win = apiresultdata.get("bonus_win")
        base_win = total_win - bonus_win
        game_id = apiresultdata.get("game_id")
        subgame_id = apiresultdata.get("subgame_id")
        resulttime = apiresultdata.get("resulttime")
        has_bonus = apiresultdata.get("has_bonus")

        try:
            # 確認 logintoken 是否有效
            command = 'select lobbyserverip, memberid, silvercredit,nickname,avatar,card from member where logintoken="{0}"'.format(logintoken)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code':1,"balance":0}
                raise ValueError('1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance":0}
                raise ValueError('2')


            memberid = pg_general.converttype(data.get("memberid"),int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"),str)
            beforecredit = pg_general.converttype(data.get("silvercredit"),int)
            aftercredit = beforecredit + total_win
            nickname = data.get('nickname')
            avatar = data.get('avatar')
            card = data.get('card')



            # 確認 txn_id 是否已經寫過 resutltime
            command = 'select total_bet,game.gamename,resulttime,memberid from bethistory_s,game where game.gameid = bethistory_s.gameid and txn_id ="{0}"'.format(txn_id)
            datalen, data = await self.getdbdata(logintoken, command,fromwritedb=True)
            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2, "balance": 0}
                raise ValueError('3')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('4')

            if data.get("resulttime") is not None:
                result = pg_general.Apiresult.success
                clientdata = {'status_code': 99, "balance":0}
                raise ValueError('5')

            betmemberid = pg_general.converttype(data.get('memberid'),int)
            total_bet = data.get('total_bet')
            gamename = data.get('gamename')

            # 確認 txn_id in bethistory
            command = 'update bethistory_s set total_win="{0}",base_win="{1}",bonus_win="{2}",resulttime="{3}",has_bonus="{5}" where txn_id="{4}"'.format(total_win,base_win,bonus_win,resulttime,txn_id,has_bonus)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2,"balance":0}
                raise ValueError('6')

            if betmemberid != memberid:  # 此筆單不是這位的
                result = pg_general.Apiresult.success
                clientdata = {'status_code': 98, "balance": beforecredit}
                raise ValueError('98')

            # # 抓 bethistroy 該筆單的 total_bet
            # command = 'select total_bet from bethistory_s where txn_id ="{0}"'.format(txn_id)
            # datalen , data = await self.getdbdata(logintoken,command,fromwritedb=True)
            #
            #
            # if datalen > 0:
            #     total_bet = data.get('total_bet')




            # update member credit
            command = 'update member set silvercredit=silvercredit+"{0}",tutorialbetfinish= "2" where memberid ="{1}"'.format(total_win,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code':1,"balance":0}
                raise ValueError('7')

            result = pg_general.Apiresult.success
            clientdata = {
                "lobbyserverip": lobbyserverip,
                "memberid": memberid,
                "aftercredit": aftercredit,
                "total_bet": total_bet,
                "nickname": nickname,
                "avatar": avatar,
                "card": card,
                "gamename": gamename

            }

            #寫入 tranaction log
            param = {
                "frommemberid": memberid,
                "tomemberid": memberid,
                "type": pg_general.transactiontype.tutorialwin,
                "amount": 0,
                "amount_silver": total_win,
                "otherdata": 'tutorialwin'
            }
            asyncio.ensure_future(self.writetransactionlog(logintoken, param))

            # 寫入 redis totaldaywin
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()
            # await redis_obj.hincrby('daywins_{}'.format(twdatetimestr), '{}'.format(memberid), total_win)
            # await redis_obj.hincrby('monthwins_{}'.format(twdatetimemonthstr), '{}'.format(memberid), total_win)
            # await redis_obj.incrby('totaldaywins_{}'.format(twdatetimestr), total_win)
            # await redis_obj.incrby('totalmonthwins_{}'.format(twdatetimemonthstr), total_win)

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapit_result logintoken:{0},ValueError:{1}'.format(logintoken, e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapit_result logintoken:{0},except:{1}'.format(logintoken, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapit_result logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                      result,
                                                                                                      clientdata))
            return result, clientdata
        
    async def psapi_getbalance(self,logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_getbalance logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        try:
            # 確認 logintoken 是否有效
            command = 'select memberid, credit from member where logintoken="{0}"'.format(logintoken)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError

            memberid = pg_general.converttype(data.get("memberid"), int)
            balance = pg_general.converttype(data.get("credit"), int)


            result = pg_general.Apiresult.success
            clientdata = {
                "status_code": 0,
                "balance" : balance
            }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_getbalance logintoken:{0},except:{1}'.format(logintoken, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapi_getbalance logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                         result,
                                                                                                         clientdata))
            return result, clientdata

    async def psapis_getbalance(self,logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_getbalance logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        try:
            # 確認 logintoken 是否有效
            command = 'select memberid, silvercredit from member where logintoken="{0}"'.format(logintoken)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError

            memberid = pg_general.converttype(data.get("memberid"), int)
            balance = pg_general.converttype(data.get("silvercredit"), int)


            result = pg_general.Apiresult.success
            clientdata = {
                "status_code": 0,
                "balance" : balance
            }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_getbalance logintoken:{0},except:{1}'.format(logintoken, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapis_getbalance logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                         result,
                                                                                                         clientdata))
            return result, clientdata


    async def psapit_getbalance(self,logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_getbalance logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        try:
            # 確認 logintoken 是否有效
            command = 'select memberid, silvercredit from member where logintoken="{0}"'.format(logintoken)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError

            memberid = pg_general.converttype(data.get("memberid"), int)
            balance = pg_general.converttype(data.get("silvercredit"), int)


            result = pg_general.Apiresult.success
            clientdata = {
                "status_code": 0,
                "balance" : balance
            }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapit_getbalance logintoken:{0},except:{1}'.format(logintoken, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapit_getbalance logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                         result,
                                                                                                         clientdata))
            return result, clientdata

    async def getlobbyserverip(self):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getlobbyserverip')
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        if env_setting.LOCAL_SERVER == True:
            result = pg_general.Apiresult.success
            clientdata = {
                "ip":[ '127.0.0.1']
            }

        else:
            command = 'select ip from lobbyserversetting'
            datalen , data = await self.getdbdata('getlobbyserverip',command,True)

            if datalen > 0:
                result = pg_general.Apiresult.success
                clientdata = {
                    "ip" : [item.get("ip") for item in data]
                }

            elif datalen ==0 :
                result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getlobbyserverip result:{0},clientdata:{1}'.format(result,clientdata))
        return result, clientdata

    async def bet_process(self,betdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:bet_process , betdata:{0}'.format(betdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        # prepare data
        cmd = betdata.get('cmd')
        token = betdata.get('token')
        game_id = betdata.get('game_id')
        total_bet = pg_general.converttype(betdata.get('total_bet'),int)
        memberid = pg_general.converttype(betdata.get('memberid'),int)
        lobbyserverip = betdata.get('lobbyserverip')


        # 計算 exp, and piggy 累積
        command ='select member.credit as credit ,member.exp as exp,member.level as level, ' \
                    'levelinfo.newlevelexp as newlevelexp,' \
                    'levelinfo.rebate as rebate,memberpiggyinfo.index as memberpiggyinfoindex, ' \
                    'memberpiggyinfo.piggycredit as piggycredit ' \
                    'from  member,levelinfo,memberpiggyinfo ' \
                    'where member.memberid="{0}" and levelinfo.level=member.level and memberpiggyinfo.memberid = member.memberid'.format(memberid)

        datalen , data = await self.getdbdata(token,command)

        if datalen > 0:
            level = pg_general.converttype(data.get("level"),int)
            exp = pg_general.converttype(data.get("exp"),int)
            newlevelexp = pg_general.converttype(data.get("newlevelexp"),int)

            memberpiggyinfoindex = data.get('memberpiggyinfoindex')

            rebate = data.get('rebate')

            # 處理 piggy
            pluspiggycredit = (total_bet*rebate)
            command = 'update memberpiggyinfo set piggycredit=piggycredit+ "{0}" where memberpiggyinfo.index="{1}"'.format(pluspiggycredit,memberpiggyinfoindex)
            result = await self.updatedbdata(token,command)

            spinexp = total_bet

            exp = exp + spinexp
            levelup = 0
            if exp >= newlevelexp:
                level = level + 1
                exp = exp - newlevelexp
                levelup = 1

            unlockgame= []
            if levelup == 1 :
                # update exp and credit
                command = 'update member set exp="{0}",level="{1}" where memberid = "{2}"'.format(exp,level,memberid)
                result = await self.updatedbdata(token, command)

                # get unlockgame gameid
                command = 'select gameid from game where unlocklevel = "{0}"'.format(level)
                datalen , data = await self.getdbdata(token,command,True)
                if datalen >0:
                    for item in data:
                        unlockgame.append(item.get('gameid'))


                # write to leveluplog
                nowdatetime = pg_general.getutcnow_datetime()
                command = 'insert into leveluplog ( memberid,leveluptime,fromlevel,tolevel) values( "{0}","{1}","{2}","{3}")'.format(memberid,nowdatetime,level-1,level)
                result = await self.updatedbdata(token,command)

            else:
                command = 'update member set exp="{0}" where memberid = "{1}"'.format(exp,memberid)
                result = await self.updatedbdata(token,command)

            command = 'select maxbet,newlevelexp from levelinfo where level = "{0}"'.format(level)
            datalen , data = await self.getdbdata(token,command)

            newlevelexp = pg_general.converttype(data.get('newlevelexp'),int)
            maxbet = pg_general.converttype(data.get("maxbet"), int)

            exppercent = int((exp / newlevelexp) * 100)
            exppercent = 100 if exppercent > 100 else exppercent


            exptonextlevel = newlevelexp - exp

            clientdata = {
                "cmd":cmd,
                "token": token,
                "game_id": game_id,
                "total_bet": total_bet,
                "memberid": memberid,
                "lobbyserverip": lobbyserverip,
                "exp": exp,
                "levelup": levelup,
                "level": level,
                "unlockgame": unlockgame,
                "exppercent": exppercent,
                "maxbet": maxbet,
                "exptonextlevel": exptonextlevel
                }


            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:bet_process , result:{0},clientdata:{1}'.format(result,clientdata))
        return result , clientdata



    async def getreddotinfo(self,logintoken,memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getreddotinfo , logintoken:{0},memberid:{1}'.format(logintoken, memberid))

        result = pg_general.Apiresult.connectdberror
        clientdata = []

        now = pg_general.strtodatetime(pg_general.getutcnow())

        try:
            # inbox reddot
            command = 'select dateline,receivestate from memberinbox where memberid ="{0}" and receivestate = "1"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command,True)

            if data is not None:
                for item in data:
                    dateline = item.get("dateline")
                    countdownseconds = pg_general.converttype((dateline - now).total_seconds(), int)
                    if countdownseconds > 0:
                        clientdata.append("inbox")
                        break



            # piggy reddot
            command = 'select memberpiggyinfo.piggycredit,setting2.minipiggytake from memberpiggyinfo,setting2 ' \
                      'where memberpiggyinfo.memberid = "{0}"'.format(memberid)

            datalen , data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                piggycredit = data.get('piggycredit')
                minipiggytake = data.get('minipiggytake')
                if piggycredit >= minipiggytake:
                    clientdata.append("piggy")

            # gift redot
            command = 'select * from gift where tomemberid = "{0}" and status="0"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken, command)
            if datalen >0:
                clientdata.append('gift')


            # freebox reddot
            freeboxresult, freeboxclientdata = await self.getfreeboxstatus(logintoken,memberid)
            if freeboxresult == pg_general.Apiresult.success:
                if freeboxclientdata.get('enable') == 1:

                    timeleft = freeboxclientdata.get('timeleft')
                    gettimes = freeboxclientdata.get('gettimes')
                    totalamount = freeboxclientdata.get('totalamount')

                    if timeleft <=0 and totalamount > gettimes:
                        clientdata.append('freebox')
            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getreddotinfo , except: {0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getreddotinfo , result:{0},clientdata:{1}'.format(result, clientdata))
            return result , clientdata

    async def getannouncement(self):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getannouncement')

        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        announcementarray = []
        try:
            command = 'select groupid,comment from announcement'
            datalen , data = await self.getdbdata("getannouncement",command,True)

            if datalen > 0 and data is not None:
                groupid = pg_general.converttype(data[0].get('groupid'),int)
                announcementarray = [item.get('comment') for item in data]
                clientdata = {
                    "groupid": groupid,
                    "data": announcementarray
                }

            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getannouncement , except: {0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getannouncement , result:{0},clientdata:{1}'.format(result, clientdata))
            return result , clientdata



    async def do_biggest_multiplier_wins(self,msg_info):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:do_biggest_multiplier_wins , memberid:{0},msg_info:{1}'.format(msg_info.get('memberid'), msg_info))
        result = pg_general.Apiresult.connectdberror

        try:
            total_win = msg_info.get('total_win')
            multipilier = msg_info.get('multipilier')
            memberid = msg_info.get('memberid')
            logintoken = msg_info.get('token')

            command = 'update member set biggestmultiplier="{0}" where memberid="{1}" and biggestmultiplier<"{0}"'.format(multipilier,memberid)
            resultbiggestmultiplier = await self.updatedbdata(logintoken,command)

            command = 'update member set biggestwins="{0}" where memberid="{1}" and biggestwins<"{0}"'.format(total_win,memberid)
            resultbiggestwins = await self.updatedbdata(logintoken,command)

            result = pg_general.Apiresult.success


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                'pg_asqldb:do_biggest_multiplier_wins ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:do_biggest_multiplier_wins except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:do_biggest_multiplier_wins return, result:{0}'.format(result))
            return result

    async def make_free_wheel_action(self,redis_obj,clientdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:make_free_wheel_action, clientdata:{}'.format(clientdata))
        result = pg_general.Apiresult.connectdberror

        try:
            result = pg_general.Apiresult.success
            card = clientdata.get('card')

            if card <2:
                return result
            multipilier = clientdata.get('multipilier')
            if multipilier<50:
                return result
            logintoken = clientdata.get('token')
            memberid = clientdata.get('memberid')
            tomorrowdateline = (pg_general.get_tw_datetime() + timedelta(days=1)).date().__str__() + ' 15:59:59'
            # 判斷今天是否已經三次
            nowdatestr = pg_general.get_tw_datetime().date().__str__()
            timevalue = await redis_obj.get_value('freewheelaction_{}_{}'.format(memberid,nowdatestr))
            totalfreewheeltimes = await redis_obj.get_value('freewheelaction_acttimes')
            if timevalue is not None:
                if totalfreewheeltimes is None:
                    if pg_general.converttype(timevalue,int) >= 3:
                        return result
                else:
                    if pg_general.converttype(timevalue,int) >= pg_general.converttype(totalfreewheeltimes,int):
                        return result
            # 判斷是否活動期間

            getvalue = await redis_obj.get_value('freewheelaction')
            if getvalue is not None:
                if pg_general.converttype(getvalue,int) ==1:
                    command = 'insert into memberinbox(memberid,inboxuri,mailtype,inboxtitle,inboxcontent,receivestate,dateline,promotionid)values' \
                              '("{0}","uri","7","超級轉輪活動","恭喜您獲得 {1}\n免費超級轉輪一次","1","{2}","29")'.format(memberid,nowdatestr,tomorrowdateline)
                    updateresult = await self.updatedbdata(logintoken,command)
                    await redis_obj.incr('freewheelaction_{}_{}'.format(memberid,nowdatestr))
                    # write action_freewheel_log
                    command = 'insert into action_freewheel_log(memberid,freedate) values("{0}","{1}")'.format(memberid,nowdatestr)
                    updateresult = await self.updatedbdata(logintoken,command)




        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_free_wheel_action except:{0}'.format(e))

        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'pg_asqldb:make_free_wheel_action return, result:{0}'.format(result))
        return result

    async def get_all_settings(self):
        # 拿到 server 所有的設定
        result = pg_general.Apiresult.connectdberror
        resultdata = {}

        command = 'select * from setting'

        datalen , data = await self.getdbdata('get_all_setting',command)

        if datalen > 0:
            resultdata ={
                "headline_multipilier_content" : data.get('headline_multipilier_content'),
                "headline_multipilier_setting": data.get('headline_multipilier_setting'),
                "headline_win_setting": data.get('headline_win_setting'),
                "headline_win_content": data.get('headline_win_content'),
                "fblink": data.get('fblink'),
                "rankminwin": data.get('rankminwin'),
                "rankminmultipilier": data.get('rankminmultipilier')

            }

        command = 'select * from setting2'
        datalen , data = await self.getdbdata('get_all_setting2',command)
        if datalen >0 :

            resultdata['dailywheelflag'] = data.get('dailywheelflag')
            resultdata['dailysigninflag'] = data.get('dailysigninflag')
            resultdata['chatroomflag'] = data.get('chatroomflag')
            resultdata['completeallcontinuoussigninaward'] = data.get('completeallcontinuoussigninaward')
            resultdata['bigprizehitamount'] = data.get('bigprizehitamount')
            resultdata['bigprizewinamount'] = data.get('bigprizewinamount')
            resultdata['defaultchannelindex'] = data.get('defaultchannelindex')
            resultdata['useagreement'] = data.get('useagreement').split('**********')
            resultdata['privacyagreement'] = data.get('privacyagreement').split('**********')
            resultdata['gameagreement'] = data.get('gameagreement').split('**********')

            resultdata['bigwincontent_publicchat'] = data.get('bigwincontent_publicchat')
            resultdata['bigmultipliercontent_publicchat'] = data.get('bigmultipliercontent_publicchat')
            resultdata['jpenable'] = data.get('jpenable')
            resultdata['jinsongprizeenable'] = data.get('jinsongprizeenable')
        # get cardinfo all data
        command = 'select * from cardinfo order by card'
        datalen , data = await self.getdbdata('get all card info data on initial apiserver', command,True)
        if datalen > 0:
            resultdata['cardinfo'] = data



        result = pg_general.Apiresult.success
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:get_all_settings return, result:{0},resultdata:{1}'.format(result,resultdata))
        return result , resultdata

    # async def getmembernicknameandgamename(self,memberid,logintoken,gameid):
    #     pg_general.writelog(pg_general.PG_LogerLevel.debug,
    #                         'pg_asqldb:getmembernickname memberid{0}, logintoken:{1},gameid:{2}'.format(memberid, logintoken,gameid))
    #     result = pg_general.Apiresult.connectdberror
    #     resultdata = {}
    #
    #     command = 'select member.nickname,game.gamename from member,game where memberid ="{0}" and gameid="{1}"'.format(memberid,gameid)
    #
    #     datalen , data = await self.getdbdata(logintoken,command)
    #     if datalen > 0:
    #         resultdata = {
    #             "nickname": data.get('nickname'),
    #             "gamename": data.get('gamename')
    #         }
    #         result = pg_general.Apiresult.success
    #
    #     pg_general.writelog(pg_general.PG_LogerLevel.debug,
    #                         'pg_asqldb:getmembernickname return, result:{0},resultdata:{1}'.format(result, resultdata))
    #     return result, resultdata

    async def savechatlog(self,logintoken,memberid,tomemberid,roomid,roomtype,type,content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:savechatlog logintoken:{5},memberid:{0},tomemberid:{6},rommid:{1},roomtype:{2},type:{3},content:{4}'.format(memberid,roomid,roomtype,type,content,logintoken,tomemberid))

            logtime = pg_general.getutcnow_datetime()
            command = 'insert into chatlog (logtime,memberid,tomemberid,roomid,roomtype,type,content) values' \
                      ' ("{0}","{1}","{2}","{3}","{4}","{5}","{6}") '.format(logtime,memberid,tomemberid,roomid,roomtype,type,content)
            insert_result = await self.insertdbdata(logintoken,command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:savechatlog except: {0}'.format(e))


    async def sendtelebot(self,msg):
        try:

            SERVICE_CHATROOM_URL = 'https://api.telegram.org/bot' + '1413875566:AAFmKonsnUjVyuue7_F76-nN3sY633hL-oM' + '/sendMessage?chat_id=' + str(-373321094) + '&text={}'.format(msg)
            async with aiohttp.ClientSession() as session:
                async with session.get(SERVICE_CHATROOM_URL, timeout=60) as response:
                    pass
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendtelebot except: {0}'.format(e))




    async def check_black_chat_content(self,logintoken,contentdata):
        try:
            result = False
            command = 'select content from blackchatcontent'
            datalen ,data = await self.getdbdata(logintoken,command,True)

            if datalen > 0:
                for item in data:
                    if item.get('content') in contentdata:
                        result = True
                        break



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:check_black_chat_content except:{} ,contentdata:{}'.format( e,contentdata))
        return result



    async def sendchat_public(self,redis_obj,logintoken,memberid,contentdata):
        try:

            
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchat_public memberid{0}, logintoken:{1},contentdata:{2}'.format(memberid,
                                                                         logintoken, contentdata))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            
            # check black content
            result_blackcontent = await self.check_black_chat_content(logintoken,contentdata.get('content'))
            if result_blackcontent == True:
                result = pg_general.Apiresult.success
                resultdata = {"black_chat_content": True}
                return result, resultdata


            
            content_type = contentdata.get('type')
            content = contentdata.get('content')
            content = content[0:99]
            isuserflag = True
            if memberid == 0:  # 系統訊息
                nickname = '系統公告'
                avatar = ''
                level = 0
                activenumber = 0
                card = 0
                isuserflag = False
            else:

                command = 'select level,activenumber,card, nickname, avatar from member where memberid ="{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken,command)
                if datalen <= 0:
                    raise ValueError('db error or no member data')

                nickname = data.get('nickname')
                avatar = data.get('avatar')
                level = data.get('level')
                card = data.get('card')
                activenumber = data.get('activenumber')

                if card == 0:
                    result = pg_general.Apiresult.success
                    resultdata = {"card_0": True}
                    return result, resultdata

            nowtime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
            command = 'insert into chatroom_public (chattime,memberid,content_type,content) values ("{0}","{1}","{2}","{3}")'\
                .format(nowtime,memberid,content_type,content)
            result_insert , index_insert = await self.insertdbdata(logintoken,command)

            chattime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')

            if result_insert == True:
                result = pg_general.Apiresult.success
                resultdata = {
                    "time": chattime,
                    "avatar": avatar,
                    "nickname": nickname,
                    "content_type": content_type,
                    "content":content,
                    "memberid": memberid,
                    "card": card,
                    "level": level,
                    "activenumber": activenumber,
                    "isuserflag": isuserflag
                }
                if isuserflag == True:          # user 才紀錄 chatlog
                    asyncio.ensure_future(self.savechatlog(logintoken,memberid,"0","0","0",content_type,content)) # 寫道 chatlog

                # save to redis chatroom_public
                await redis_obj.lpush('chatroom_public',json.dumps(resultdata))
                await redis_obj.ltrim('chatroom_public',0,100)

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchat_public ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchat_public Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchat_public return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata


    async def getsettingcontent(self,logintoken,memberid,type):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getsettingcontent memberid{0}, logintoken:{1},type:{2}'.format(memberid,logintoken,type))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}


            # 抓取 content
            command = 'select content from guide where type="{0}"'.format(type)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen >0 :
                content = data.get('content')
                resultdata = {
                    "content": content
                }

                result = pg_general.Apiresult.success


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getsettingcontent Exception except:{0}'.format(e))


        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getsettingcontent return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getsecretmall(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getsecretmall memberid{0}, logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select secretoffermall.* from secretoffermall,member where member.memberid="{0}" and member.secretmallid = secretoffermall.id'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen == 1:
                resultdata = {
                    "shopid": data.get('shopid'),
                    "cost": data.get('cost'),
                    "buycredit": data.get('buypoint')
                }
                result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getsecretmall Exception except:{0}'.format(e))


        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getsecretmall return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def senddownloadsignal(self,logintoken,memberid,state,region):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:senddownloadsignal memberid:{0},logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            logtime = pg_general.getutcnow_datetime()
            command = 'insert into downloadsignal (logintoken,state,logtime,region) values ("{0}","{1}","{2}","{3}")'.format(logintoken,state,logtime,region)

            result_insert , index = await self.insertdbdata(logintoken,command)


            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:senddownloadsignal Exception except:{0}'.format(e))


        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:senddownloadsignal return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata


    async def getpiggycredit(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getpiggycredit memberid:{0},logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select member.credit,memberpiggyinfo.piggycredit,setting2.minipiggytake from member,memberpiggyinfo,setting2 where memberpiggyinfo.memberid = "{0}" ' \
                        'and member.memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen > 0 :
                minipiggytake = data.get('minipiggytake')
                piggycredit = int(data.get('piggycredit'))
                membercredit = data.get('credit')
                if piggycredit < minipiggytake:
                    raise ValueError('memberid :{0},piggycredit < minipiggytake'.format(memberid))

                command = 'update member , memberpiggyinfo  set member.credit = member.credit + "{1}" , memberpiggyinfo.piggycredit = 0 ' \
                        'where member.memberid = "{0}" and memberpiggyinfo.memberid = "{0}";'.format(memberid,piggycredit)

                update_result = await self.updatedbdata(logintoken,command)
                if update_result == True:
                    resultdata = {
                        "takecredit": piggycredit,
                        "aftercredit": membercredit + piggycredit
                    }

                    result = pg_general.Apiresult.success

                    param = {
                        "frommemberid": memberid,
                        "tomemberid": memberid,
                        "type": pg_general.transactiontype.getpiggycredit,
                        "amount": piggycredit,
                        "amount_silver":0,
                        "otherdata": 'piggycredit'
                    }
                    asyncio.ensure_future(self.writetransactionlog(logintoken, param))
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getpiggycredit ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getpiggycredit Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getpiggycredit return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getfriendlist(self,logintoken,memberid,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getfriendlist memberid:{0},logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {"friendlist": []}

            command = 'select friendlist from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen != 1:
                raise ValueError('getfriendlist error 1')

            friendlist = data.get('friendlist')

            if friendlist is not None:
                friendlist = friendlist.strip()
                if len(friendlist) > 0:
                    templist = friendlist.split(',')
                    templist = ['online_'+item for item in templist]
                    resultlist = await redis_obj.mget_json_value(templist)

                    command = 'select memberid,avatar,nickname,level,activenumber,card from member where memberid in ({0})'.format(friendlist)
                    datalen , data = await self.getdbdata(logintoken , command , True)

                    if datalen > 0 and datalen == len(resultlist):
                        for item,itemdata in zip(resultlist,data):
                            itemdata['isonline'] = True if item is not None else False


                        resultdata = {"friendlist": data}

                result = pg_general.Apiresult.success

            else:
                result = pg_general.Apiresult.success


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getfriendlist ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getfriendlist Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getfriendlist return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getblacklist(self,logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getblacklist memberid:{0},logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {"blacklist": []}

            command = 'select blacklist from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen != 1:
                raise ValueError('getblacklist error 1')

            blacklist = data.get('blacklist')

            if blacklist is not None:
                blacklist = blacklist.strip()

                if len(blacklist) > 0:
                    command = 'select memberid,avatar,nickname,level,activenumber,card from member where memberid in ({0})'.format(blacklist)
                    datalen , data = await self.getdbdata(logintoken , command , True)

                    if datalen > 0:
                        resultdata = {"blacklist": data}

                result = pg_general.Apiresult.success

            else:
                result = pg_general.Apiresult.success


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getblacklist ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getblacklist Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getblacklist return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def updatefriendlist(self,logintoken,memberid,type,friend_memberid,friend_nickname,redis_object): # type = 0:add , 1:remove
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updatefriendlist memberid:{0},logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 如果是 type in [2,3] 先找出 memberid
            if type in [2,3]:
                command = 'select memberid from member where nickname = "{0}"'.format(friend_nickname.strip())
                datalen , data = await self.getdbdata(logintoken,command)
                if datalen == 0:
                    result = pg_general.Apiresult.success
                    resultdata = {"result": 1} # 找不到此會員
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:updatefriendlist return, result:{0},resultdata:{1}'.format(result,
                                                                                                              resultdata))
                    return result , resultdata
                elif datalen == 1:
                    friend_memberid = data.get('memberid')
                else:
                    raise ('get nickname from member error')

                type -=2

            # 抓新朋友是否在線
            tempvalue = await redis_object.get_value('online_{}'.format(str(friend_memberid)))
            isonline = True if tempvalue is not None else False

            if type ==0 : # add
                # 抓對象的資料
                command = 'select avatar,nickname,level,activenumber,card from member where memberid="{0}"'.format(friend_memberid)
                datalen , data = await self.getdbdata(logintoken, command)
                if datalen ==0:
                    result = pg_general.Apiresult.success
                    resultdata = {"result": 1}  # 找不到此會員
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:updatefriendlist return, result:{0},resultdata:{1}'.format(result,
                                                                                                              resultdata))
                    return result, resultdata
                elif datalen < 0:
                    raise ValueError('get member info is error')

                resultdata = {
                    "memberid": friend_memberid,
                    "avatar": data.get('avatar'),
                    "nickname": data.get('nickname'),
                    "level": data.get('level'),
                    "activenumber": data.get('activenumber'),
                    "card": data.get('card'),
                    "isonline": isonline,
                    "result": 0
                }

                # 抓現有的好友名單
                command = 'select friendlist from member where memberid = "{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken, command)
                friendlist = data.get('friendlist').strip()
                if len(friendlist)>0:
                    friendlist = friendlist.split(',')
                else:
                    friendlist = []

                if str(friend_memberid) not in friendlist:  # 不存在, 新增
                    friendlist.append(str(friend_memberid))
                    command = 'update member set friendlist="{0}" where memberid = "{1}"'.format(','.join(friendlist),memberid)
                    updateresult = await self.updatedbdata(logintoken,command)

            else:       # remove
                # 抓現有的好友名單
                command = 'select friendlist from member where memberid = "{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken, command)
                friendlist = data.get('friendlist').strip()
                if len(friendlist) > 0 :
                    friendlist = friendlist.split(',')
                    if str(friend_memberid) in friendlist:
                        friendlist.remove(str(friend_memberid))
                        if len(friendlist) > 0:
                            command = 'update member set friendlist="{0}" where memberid ="{1}"'.format(','.join(friendlist),memberid)
                        else:
                            command = 'update member set friendlist="" where memberid = "{0}"'.format(memberid)
                        updateresult = await self.updatedbdata(logintoken, command)
                resultdata = {"result": 0}

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatefriendlist ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatefriendlist Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updatefriendlist return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def updateblacklist(self,logintoken,memberid,type,black_memberid,black_nickname):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updateblacklist memberid:{0},logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if type in [2,3]:
                # if type in [2,3] 確認是否有此 member and get memberid
                command = 'select memberid from member where nickname = "{0}"'.format(black_nickname.strip())
                datalen , data = await self.getdbdata(logintoken, command)
                if datalen == 0:
                    result = pg_general.Apiresult.success
                    resultdata = {"result": 1}  # 找不到此會員
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:updateblacklist return, result:{0},resultdata:{1}'.format(result,
                                                                                                              resultdata))
                    return result , resultdata
                elif datalen == 1:
                    black_memberid = data.get('memberid')
                else:
                    raise ('get nickname from member error')

                type -=2

            # 抓現有的列表
            command = 'select blacklist from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get blacklist error')

            blacklist = data.get('blacklist').strip()
            if len(blacklist) ==0:
                blacklist = []
            else:
                blacklist = blacklist.split(',')

            # memberid *
            # avatar *
            # nickname *
            # level *
            # activenumber *
            # card *
            # 抓此為黑名單的資料
            command = 'select avatar, nickname, level, activenumber,card from member where memberid="{0}"'.format(black_memberid)
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen != 1:
                raise ValueError('get black memberid is error')

            black_avatar = data.get('avatar')
            black_nickname = data.get('nickname')
            black_level = data.get('level')
            black_activenumber = data.get('activenumber')
            black_card = data.get('card')

            if type ==0 : # add
                if str(black_memberid) not in blacklist:
                    blacklist.append(str(black_memberid))
                    # udpate black list to db
                    command = 'update member set blacklist="{0}" where memberid="{1}"'.format(','.join(blacklist),memberid)
                    updateresul = await self.updatedbdata(logintoken, command)

                resultdata = {
                    "memberid": black_memberid,
                    "avatar": black_avatar,
                    "nickname": black_nickname,
                    "level": black_level,
                    "activenumber": black_activenumber,
                    "card": black_card,
                    "result": 0
                }


            else:       # remove
                if str(black_memberid) in blacklist:
                    blacklist.remove(str(black_memberid))
                    # update black list to db
                    command = 'update member set blacklist="{0}" where memberid = "{1}"'.format(','.join(blacklist),memberid)
                    updateresult = await self.updatedbdata(logintoken, command)
                resultdata= {"result":0}
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateblacklist ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateblacklist Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updateblacklist return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def safetask(self,logintoken,memberid,type,amount=None):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:safetask memberid:{0},logintoken:{1} , type:{2},amount:{3}'.format(memberid, logintoken,type,amount))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select credit,safe from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get safe amount error')

            credit = data.get('credit')
            safeamount = data.get('safe')

            if type ==2: # 查詢保險箱裡的分數
                resultdata = {
                    "credit": credit,
                    "safeamount": safeamount,
                    "errcode": 0
                }

            elif type == 0: # 存入
                if amount > credit:
                    resultdata = {
                        "credit":0,
                        "safeamount": 0,
                        "errcode": 1,
                        "errdescription": '金幣餘額不足'
                    }
                elif amount <1:
                    result = pg_general.Apiresult.parametererror
                    raise ValueError('amount < 1')
                else:
                    command = 'update member set credit=credit-"{0}",safe=safe+"{0}" where memberid = "{1}"'.format(amount,memberid)
                    updateresult = await self.updatedbdata(logintoken,command)
                    if updateresult == True:
                        resultdata = {
                            "credit": credit - amount,
                            "safeamount": safeamount + amount,
                            "errcode": 0

                        }
                        param = {
                            "frommemberid": memberid,
                            "tomemberid": memberid,
                            "type": pg_general.transactiontype.savetosafe,
                            "amount": amount,
                            "otherdata": "savetosafe"
                        }
                        asyncio.ensure_future(self.writetransactionlog(logintoken,param))
            elif type == 1:  # 提出
                if safeamount < amount:
                    resultdata = {
                        "credit": 0,
                        "safeamount": 0,
                        "errcode": 1,
                        "errdescription": '保險箱餘額不足'
                    }
                elif amount < 1:
                    result = pg_general.Apiresult.parametererror
                    raise ValueError('amount < 1')
                else:
                    command = 'update member set credit = credit + "{0}",safe= safe-"{0}" where memberid = "{1}"'.format(amount,memberid)
                    updateresult = await self.updatedbdata(logintoken,command)
                    if updateresult == True:
                        resultdata = {
                            "credit": credit + amount,
                            "safeamount": safeamount - amount,
                            "errcode": 0
                        }
                        param = {
                            "frommemberid":memberid,
                            "tomemberid": memberid,
                            "type": pg_general.transactiontype.getfromsafe,
                            "amount":amount,
                            "otherdata": "getfromsafe"
                        }
                        asyncio.ensure_future(self.writetransactionlog(logintoken,param))
            else:
                result = pg_general.Apiresult.parametererror
                raise ValueError('type error')

            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:safetask ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:safetask Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:safetask return, result:{0},resultdata:{1}'.format(result,resultdata))
            return result, resultdata


    async def webapi_serial_input(self,logintoken,memberid,serial):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:serialinput memberid:{0},logintoken:{1} , serial:{2}'.format(memberid, logintoken,serial))
            result = pg_general.Apiresult.connectdberror

            resultdata = {
                "credit": 0,
                "silvercredit": 0,
                "errcode": 1,
                "errdescription": "序號錯誤, 請重新輸入 !",
                "award": 0,
                "award_s": 0
            }




            if serial.strip() == '':
                result = pg_general.Apiresult.success
                return result, resultdata

            # 全部轉小寫
            serial = serial.lower()

            prefix = serial[:3]
            serialvalueinput = serial[3:]

            command = 'select * from serialmode where prefix = "{0}" and enable = 1'.format(prefix)
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                result = pg_general.Apiresult.success
                return result , resultdata


            serialvalue = data.get('serialvalue')
            modetype = data.get('modetype')
            duration = json.loads(data.get('duration'))
            leftamount = data.get('leftamount')
            awardcontent = json.loads(data.get('awardcontent'))
            amountlimitflag = data.get('amountlimitflag')
            serialmodeindex = data.get('serialmodeindex')
            groupnum = data.get('groupnum')
            limitation = json.loads(data.get('limitation'))

            if None in [serialmodeindex,modetype,duration,leftamount,awardcontent,amountlimitflag,groupnum,limitation]:
                result = pg_general.Apiresult.success
                return result , resultdata

            if modetype ==0:
                if serialvalue != serialvalueinput:
                    result = pg_general.Apiresult.success
                    return result, resultdata

            limitation_card = 0 if limitation.get('card') is None else limitation.get('card')
            limitation_level = 0 if limitation.get('level') is None else limitation.get('level')


            # 處理是否過期 或是時間還沒到
            starttimestr = duration.get('starttime')
            endtimestr = duration.get('endtime')

            starttimepass = False
            endtimepass = False
            nowdatetimeutc = pg_general.getutcnow_datetime()

            if starttimestr is not None:
                starttime = pg_general.strtodatetime_nof(starttimestr)
                if nowdatetimeutc > starttime:
                    starttimepass = True
            else:
                starttimepass = True

            if endtimestr is not None:
                endtime = pg_general.strtodatetime_nof(endtimestr)
                if nowdatetimeutc < endtime:
                    endtimepass = True
            else:
                endtimepass = True


            if False in [starttimepass,endtimepass]:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉!! 此序號已過期或尚未開始,謝謝您!!'
                return result, resultdata

            # 共用序號模式 有數量限制 數量 <=0 代表發完
            if modetype == 0 and leftamount <=0 and amountlimitflag == 1:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉!! 此序號已達發送數量,已無法取得獎勵!!'
                return result , resultdata

            award = awardcontent.get('award')
            award_s = awardcontent.get('award_s')
            if award is None:
                award = 0
            if award_s is None:
                award_s = 0

            # get member phone
            command = 'select phone,phonebindstatus,card,level from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen !=1:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '要先綁定手機門號才能領取喔,請至App中綁定手機門號喔,謝謝您!!'
                return result, resultdata

            phone = data.get('phone')
            phonebindstatus = data.get('phonebindstatus')
            membercard = data.get('card')
            memberlevel = data.get('level')

            if phonebindstatus != 2:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '要先綁定手機門號才能領取喔,請至App中綁定手機門號喔,謝謝您!!'
                return result, resultdata

            # 檢查 limitation 是否有達到
            if membercard < limitation_card:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉,您的卡別未達,無法領取,謝謝您!!'
                return result, resultdata

            if memberlevel < limitation_level:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉,您的等級未達,無法領取,謝謝您!!'
                return result, resultdata


            if modetype == 0:       # 共用序號
                # 查詢是否有領過同一種序號
                command = 'select * from seriallog where (memberid="{0}" or phone="{2}") and (serialmodeindex="{1}" or groupnum="{3}")'.format(memberid,serialmodeindex,phone,groupnum)
                datalen , data = await self.getdbdata(logintoken,command)
                if datalen >=1:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = '您已經領過搂,無法重複領取喔,謝謝您!!'
                    return result, resultdata

                # 更新 serialmode leftamount
                if amountlimitflag == 1:
                    command = 'update serialmode set leftamount = leftamount-1 where serialmodeindex = "{0}"'.format(serialmodeindex)
                    updateresult = await self.updatedbdata(logintoken,command)

                # 更新玩家 credit ,silvercredit
                command = 'update member set credit= credit+"{0}",silvercredit= silvercredit+"{1}" where memberid="{2}"'.format(award,award_s,memberid)
                updateresult = await self.updatedbdata(logintoken,command)

                # 寫 log
                command = 'insert into seriallog(usedtime,memberid,award,award_s,modetype,prefix,serialvalue,serialmodeindex,phone,groupnum)values' \
                          '("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")'.format(nowdatetimeutc,memberid,award,award_s,modetype,prefix,serialvalue,serialmodeindex,phone,groupnum)
                updateresult = await self.updatedbdata(logintoken,command)

                # get member credit, silvercredit
                credit = 0
                silvercredit = 0
                command = 'select credit,silvercredit from member where memberid="{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken,command,False,True)
                if datalen ==1 :
                    credit = data.get('credit')
                    silvercredit = data.get('silvercredit')

                # write transaction log
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.serial,
                    "amount": award,
                    "amount_silver": award_s,
                    "otherdata": 'award:{},award_s:{},modetype:{},serialmodeindex:{}'.format(award,award_s,modetype,serialmodeindex)
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

                awardstr = "恭喜您獲得獎勵 !!"
                if award > 0 :
                    awardstr = awardstr + ' 金幣 {} '.format(award)
                if award_s > 0:
                    awardstr = awardstr + ' 銀幣 {}'.format(award_s)

                resultdata = {
                    "credit": credit,
                    "silvercredit": silvercredit,
                    "errcode": 0,
                    "errdescription": awardstr,
                    "award": award,
                    "award_s": award_s
                }
            else:   # modetype ==1

                command = 'select * from serialtable where serialvalue = "{0}" and  modeindex = "{1}"'.format(serialvalueinput,serialmodeindex)
                datalen, data = await self.getdbdata(logintoken,command)
                if datalen != 1:
                    result = pg_general.Apiresult.success
                    return result,resultdata
                serialtableindex = data.get('serialtableindex')
                used = data.get('used')
                if used ==1:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = '此序號已被使用過, 請重新輸入!!'
                    return result,resultdata

                # 查詢是否有領過同一種序號
                command = 'select * from seriallog where (memberid="{0}" or phone="{2}") and modetype=1 and (serialmodeindex="{1}" or groupnum="{3}")'.format(memberid, serialmodeindex,phone,groupnum)
                datalen , data = await self.getdbdata(logintoken,command)
                if datalen >=1:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = '您已經領過搂,無法重複領取喔,謝謝您!!'
                    return result, resultdata

                # update serialtable
                command = 'update serialtable set used = 1,usedtime="{0}" where serialtableindex="{1}" '.format(nowdatetimeutc,serialtableindex)
                updateresult = await self.updatedbdata(logintoken,command)

                # update member credit, silvercredit
                command = 'update member set credit = credit+"{0}",silvercredit=silvercredit+"{1}" where memberid ="{2}"'.format(
                    award, award_s, memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                # 寫 log
                command = 'insert into seriallog(usedtime,memberid,award,award_s,modetype,prefix,serialvalue,serialmodeindex,phone,groupnum)values' \
                          '("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")'.format(nowdatetimeutc, memberid, award, award_s,
                                                                        modetype, prefix, serialvalueinput,serialmodeindex,phone,groupnum)
                updateresult = await self.updatedbdata(logintoken, command)

                # get member credit, silvercredit
                credit = 0
                silvercredit = 0
                command = 'select credit,silvercredit from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                if datalen == 1:
                    credit = data.get('credit')
                    silvercredit = data.get('silvercredit')

                # write transaction log
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.serial,
                    "amount": award,
                    "amount_silver": award_s,
                    "otherdata": 'award:{},award_s:{},modetype:{},serialmodeindex:{},serialtableindex:{}'.format(award, award_s,
                                                                                             modetype,
                                                                                             serialmodeindex,serialtableindex)
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

                awardstr = "恭喜您獲得獎勵 !!"
                if award > 0:
                    awardstr = awardstr + ' 金幣 {} '.format(award)
                if award_s > 0:
                    awardstr = awardstr + ' 銀幣 {}'.format(award_s)

                resultdata = {
                    "credit": credit,
                    "silvercredit": silvercredit,
                    "errcode": 0,
                    "errdescription": awardstr,
                    "award": award,
                    "award_s": award_s
                }


            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:serialinput ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:serialinput Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:serialinput return, result:{0},resultdata:{1}'.format(result,resultdata))
        return result, resultdata

    async def makelike(self,logintoken, memberid,likememberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makelike memberid:{0},logintoken:{1} , likememberid:{2}'.format(memberid, logintoken,likememberid))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 紀錄 like log
            logtime = pg_general.getutcnow_datetime()
            command = 'insert into likelog (logtime,frommemberid,tomemberid) values("{0}","{1}","{2}")'.format(logtime,memberid,likememberid)
            updateresult = await self.updatedbdata(logintoken,command)

            # update member.likeamount
            command = 'update member set likeamount = likeamount+1 where memberid = "{0}"'.format(likememberid)
            updateresult = await self.updatedbdata(logintoken,command)

            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makelike ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makelike Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makelike return, result:{0},resultdata:{1}'.format(result,resultdata))
            return result, resultdata

    async def sendprivatchat(self,logintoken,memberid,chatmemberid,type,content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendprivatchat memberid:{0},logintoken:{1} , chatmemberid:{2},type:{3},content:{4}'.format(memberid, logintoken,chatmemberid,type,content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # check black content
            result_blackcontent = await self.check_black_chat_content(logintoken,content)
            if result_blackcontent == True:
                result = pg_general.Apiresult.success
                resultdata = {"black_chat_content": True}
                return result, resultdata


            # 紀錄 chatlog
            nowdatetime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')



            command = 'select blacklist from member where memberid="{0}"'.format(chatmemberid)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen >0:
                blacklist = data.get('blacklist')
                if blacklist is not None:
                    if str(memberid) in blacklist.split(','):
                        result = pg_general.Apiresult.blackme
                        return result,resultdata

            # 抓 基本資料
            command = 'select avatar,nickname,card,level,activenumber from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken, command)
            if datalen == 1:
                card = data.get('card')
                if card ==0:
                    result = pg_general.Apiresult.success
                    resultdata ={"card_0": True}
                    return result, resultdata

                resultdata = {
                    "time": nowdatetime,
                    "avatar": data.get('avatar'),
                    "nickname": data.get('nickname'),
                    "type": type,
                    "content": content,
                    "memberid": memberid,
                    "card": data.get('card'),
                    "level": data.get('level'),
                    "activenumber": data.get('activenumber')
                }
                asyncio.ensure_future(self.savechatlog(logintoken, memberid, chatmemberid, "0", "0", type, content))  # 寫道 chatlog
                result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendprivatchat ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendprivatchat Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendprivatchat return, result:{0},resultdata:{1}'.format(result,resultdata))
            return result, resultdata

    async def sendphonevalidate(self, logintoken, memberid,phone):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendphonevalidate memberid:{0},logintoken:{1},phone:{2}'.format(
                                    memberid, logintoken, phone))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            # 確認格式是否正確
            if '09' != phone[:2] or phone.isdigit() ==False:
                result = pg_general.Apiresult.success
                resultdata = {'result': 2}
                raise ValueError("phone number is wrong",pg_general.PG_LogerLevel.warn)

            # 檢查是否是 門號黑名單 如果是的話 直接 封鎖
            command = 'select phone from blackphone where phone = "{0}"'.format(phone)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen ==1: # 是黑名單
                command = 'update member set enable ="3" where memberid="{0}"'.format(memberid)
                updateresult2 = await self.updatedbdata(logintoken,command)
                return result,resultdata




            # 抓取此會員綁定狀態
            command = 'select phone , phonebindstatus,phonevalidatecode,phonevalidatetime from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member phone status error',pg_general.PG_LogerLevel,error)

            member_phone = data.get('phone')
            member_phonebindstatus = data.get('phonebindstatus')
            member_phonevalidatecode = data.get('phonevalidatecode')
            member_phonevalidatetime = data.get('phonevalidatetime')

            nowdatetime = pg_general.getutcnow_datetime()
            difftime = (nowdatetime - member_phonevalidatetime).total_seconds()

            if None in [member_phone,member_phonebindstatus,member_phonevalidatecode,member_phonevalidatetime]:
                raise ValueError('get member phone data error',pg_general.PG_LogerLevel.error)

            if member_phonebindstatus ==2:
                resultdata = {"result": 1}
            elif member_phonebindstatus ==1 and difftime <= 60:
                resultdata = {'result': 4}
            elif (member_phonebindstatus ==1 and difftime > 60) or member_phonebindstatus == 0:
                # # 搜尋此手機是否綁定過
                command = 'select memberid , phone from member where phone = "{0}"'.format(phone)
                datalen , data = await self.getdbdata(logintoken, command)
                if datalen >0:
                    result = pg_general.Apiresult.success
                    resultdata = {'result': 3}
                    raise ValueError('this number is used', pg_general.PG_LogerLevel.warn)


                validatecode = random.randint(100000,999999)
                # 發送 code to phone
                await pg_sms.sendsms(phone,validatecode)

                # 紀錄 db
                command = 'update member set phonebindstatus=1,phonevalidatecode="{0}",phonevalidatetime="{1}",tempphone="{3}" where memberid = "{2}"'.format(validatecode,nowdatetime,memberid,phone)
                updateresult = await self.updatedbdata(logintoken, command)
                resultdata = {'result':0}

                # insert into phonevalidatelog
                command = 'insert into phonevalidatelog (logtime,phone,memberid,validatecode) values("{0}","{1}","{2}","{3}")'.format(nowdatetime,phone,memberid,validatecode)
                insertresult = await self.updatedbdata(logintoken,command)
            result = pg_general.Apiresult.success

        except ValueError as e:
            description , loglevel = e.args
            pg_general.writelog(loglevel,
                                'pg_asqldb:sendphonevalidate ValueError except:{0}'.format(description))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendphonevalidate Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendphonevalidate return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata


    async def feedbackvalidatecode(self,logintoken,memberid,code):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:feedbackvalidatecode memberid:{0},logintoken:{1},code:{2}'.format(
                                    memberid, logintoken, code))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 檢查驗證碼格式是否有錯
            code = code.strip()
            if code.isdigit() == False:
                result = pg_general.Apiresult.success
                resultdata = {'result':2}
                raise ValueError('code is wrong',pg_general.PG_LogerLevel.warn)

            # get member 驗證相關資料
            command = 'select card,phone,tempphone,phonebindstatus,phonevalidatecode,phonevalidatetime,setting2.bindphonereward,setting2.bindphonecardminindex from member,setting2 where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                raise ValueError('get member data error',pg_general.PG_LogerLevel.error)

            card = data.get('card')
            phone = data.get('phone')
            tempphone = data.get('tempphone')
            phonebindstatus = data.get('phonebindstatus')
            phonevalidatecode = data.get('phonevalidatecode')
            phonevalidatetime = data.get('phonevalidatetime')
            bindphonereward = data.get('bindphonereward')
            bindphonecardminindex = data.get('bindphonecardminindex')


            if phonebindstatus ==2:
                result = pg_general.Apiresult.success
                resultdata = {'result':3}
                raise ValueError('already bind phone',pg_general.PG_LogerLevel.warn)

            if phonebindstatus != 1:
                result = pg_general.Apiresult.success
                resultdata = {'result':4}
                raise ValueError('phonebindstatus is not 1',pg_general.PG_LogerLevel.warn)

            nowdatetime = pg_general.getutcnow_datetime()
            if (nowdatetime - phonevalidatetime).total_seconds() > 600:  # 驗證時間超過 10 分鐘
                result = pg_general.Apiresult.success
                resultdata = {'result': 1}
                raise ValueError('validate over 600 seconds',pg_general.PG_LogerLevel.warn)

            if code != phonevalidatecode:
                result = pg_general.Apiresult.success
                resultdata = {'result':2}
                raise ValueError('validate number is wrong with db',pg_general.PG_LogerLevel.warn)

            param = ''
            cardlevelupflag = False
            if bindphonecardminindex > card:
                param = ',card="{0}",cardlevelchangetime="{1}"'.format(bindphonecardminindex,nowdatetime)
                cardlevelupflag = True


            yesterdaydatetime = phonevalidatetime-timedelta(days=1)
            # 通過驗證
            command = 'update member set phone="{0}",phonebindstatus="2",credit=credit+"{2}",phonevalidatetime="{4}"{3} where memberid="{1}"'.format(tempphone,memberid,bindphonereward,param,yesterdaydatetime)
            updateresult = await self.updatedbdata(logintoken,command)

            if cardlevelupflag == True: # write cardlevelchangelog
                # write 升級卡別 log
                asyncio.ensure_future(self.writecardchangelog([[memberid, nowdatetime, card, bindphonecardminindex, 'bindphone']]))


            # get credit and card
            command = 'select card,credit from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command,False,True)
            resultdata = {
                'result':0,
                'aftercredit': data.get('credit'),
                'card': data.get('card')
            }

            if bindphonereward > 0:
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.bindphonereward,
                    "amount": bindphonereward,
                    "otherdata": 'bindphonereward'
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

            result = pg_general.Apiresult.success

        except ValueError as e:
            description , loglevel = e.args
            pg_general.writelog(loglevel,
                                'pg_asqldb:feedbackvalidatecode ValueError except:{0}'.format(description))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:feedbackvalidatecode Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:feedbackvalidatecode return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getgiftdata(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getgiftdata memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 抓取 member.credit,todaygiftamount,todaygifttimes and cardinfo.maxgiftamount,maxgifttimes
            command = 'select member.membertype,member.card,member.level,member.credit,member.todaygiftamount,member.todaygifttimes,cardinfo.maxgiftamount,cardinfo.maxgifttimes,giftlist,cardinfo.maxgiftlistamount from member,cardinfo' \
                      ' where member.memberid = "{0}" and member.card=cardinfo.card'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                raise ValueError('get card or member error')

            credit = data.get('credit')
            card = data.get('card')
            level = data.get('level')
            todaygiftamount = data.get('todaygiftamount')
            todaygifttimes = data.get('todaygifttimes')
            todaytotalcreditamount = data.get('maxgiftamount')
            todaytotaltimes = data.get('maxgifttimes')
            membertype = data.get('membertype')

            if card in [2,3,4] and level >=50:
                todaytotalcreditamount = 20000000

            if todaytotalcreditamount == -1:
                todayleftcreditamount = -1
            else:
                todayleftcreditamount = todaytotalcreditamount - todaygiftamount
                if todayleftcreditamount <0:
                    todayleftcreditamount = 0

            if todaytotaltimes == -1:
                todaylefttimes = -1
            else:
                todaylefttimes = todaytotaltimes - todaygifttimes
                if todaylefttimes < 0:
                    todaylefttimes = 0

            giftlistdata = data.get('giftlist')
            maxgiftlistamount = data.get('maxgiftlistamount')


            # 抓取 db.gift
            command =  'select giftindex,frommemberid,tomemberid,gifttime,type,amount,status,password, ' \
                       't1.nickname as fromnickname,t2.nickname as tonickname,t1.avatar as fromavatar,t2.avatar as toavatar ' \
                       ' from gift,(select nickname,memberid,avatar from member) as t1, ' \
                       '(select nickname , memberid,avatar from member) as t2 where gift.frommemberid = "{0}" ' \
                       'and t1.memberid = gift.frommemberid and t2.memberid = gift.tomemberid ' \
                       'union all ' \
                       'select giftindex,frommemberid,tomemberid,gifttime,type,amount,status,password, ' \
                       't1.nickname as fromnickname,t2.nickname as tonickname,t1.avatar as fromavatar,t2.avatar as toavatar ' \
                       ' from gift,(select nickname,memberid,avatar from member) as t1, ' \
                       '(select nickname,memberid,avatar from member) as t2 where gift.tomemberid = "{0}" ' \
                       'and t1.memberid = gift.frommemberid and t2.memberid = gift.tomemberid'.format(memberid)

            datalen , data = await self.getdbdata(logintoken,command , True)
            giftcenter = []
            giftrecord = []

            if datalen >0:
                # 程序還沒結束的 贈禮
                giftcentertemp = [item for item in data if item.get('status')==0]
                giftcentertemp = sorted(giftcentertemp, key=lambda k: (k['giftindex']), reverse=True)

                for item in giftcentertemp:
                    giftcenter.append({
                        'num': str(item.get('giftindex')),
                        'memberid': item.get('frommemberid') if item.get('tomemberid') == memberid else item.get('tomemberid'),
                        'sendtime': pg_general.get_utc_to_local_datetime(item.get('gifttime')).strftime('%Y-%m-%d %H:%M:%S'),
                        'nickname': item.get('fromnickname') if item.get('tomemberid') ==  memberid else item.get('tonickname'),
                        'avatar': item.get('fromavatar') if item.get('tomemberid') == memberid else item.get('toavatar'),
                        'content': {'type':item.get('type'),'amount': item.get('amount')},
                        'op': 0 if item.get('tomemberid') == memberid else 1
                    })

                giftrecordtemp = [item for item in data if item.get('status') != 0]
                giftrecordtemp = sorted(giftrecordtemp,key=lambda k: (k['giftindex']), reverse=True)

                for item in giftrecordtemp:
                    giftrecord.append({
                        'num': str(item.get('giftindex')),
                        'memberid': item.get('frommemberid') if item.get('tomemberid') == memberid else item.get('tomemberid'),
                        'sendtime': pg_general.get_utc_to_local_datetime(item.get('gifttime')).strftime('%Y-%m-%d %H:%M:%S'),
                        'nickname': item.get('fromnickname') if item.get('tomemberid') == memberid else item.get('tonickname'),
                        'avatar': item.get('fromavatar') if item.get('tomemberid') == memberid else item.get('toavatar'),
                        'optype': 0 if item.get('tomemberid') == memberid else 1,
                        'status': item.get('status'),
                        'content': {'type':item.get('type'),'amount': item.get('amount')}
                    })

            # 抓常用名單的 member data
            giftlist = []
            giftlistamount = 0
            if len(giftlistdata)>0:
                command = 'select memberid,avatar,nickname,level,card,activenumber from member where memberid in ({0})'.format(giftlistdata)
                datalen , data = await self.getdbdata(logintoken,command,True)

                if datalen >0:
                    giftlistamount = datalen
                    for item in data:
                        giftlist.append({
                            "memberid": item.get('memberid'),
                            "nickname": item.get('nickname'),
                            "avatar": item.get('avatar'),
                            "level": item.get('level'),
                            "card": item.get('card'),
                            "activenumber": item.get('activenumber')
                        })
            if membertype != 0:
                todaylefttimes = 0
                todayleftcreditamount = 0

            # 抓取 凍結贈禮資訊
            giftfreezedata = await self.getgiftfreezedata(logintoken,memberid)


            result = pg_general.Apiresult.success
            resultdata = {
                'credit': credit,
                'todayleftcreditamount': todayleftcreditamount,
                'todaytotalcreditamount': todaytotalcreditamount,
                'todaylefttimes': todaylefttimes,
                'todaytotaltimes': todaytotaltimes,
                'giftcenter': giftcenter,
                'giftrecord': giftrecord,
                'giftlist': giftlist,
                'maxgiftlistamount': maxgiftlistamount,
                'giftlistamount': giftlistamount,
                'giftfreezedata': giftfreezedata
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgiftdata ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgiftdata Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getgiftdata return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getcardinfo(self,logintoken,memberid,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getcardinfo memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # get member card, cardbuy, cardbet
            command = 'select card from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen !=1:
                raise ValueError('get memeber card data error')

            card = data.get('card')
            cardbuy = 0
            cardbet = 0


            # 抓 cardbet & cardbuy from redis
            if card in [2,3,4,5]:
                valuelist = await redis_obj.hvals('bethistory_gold_{}'.format(memberid))
                if len(valuelist)>0:
                    valuelist = list(map(int,valuelist))
                    cardbet = sum(valuelist)

                valuelist = await redis_obj.hvals('cardbuy_{}'.format(memberid))
                if len(valuelist)> 0:
                    valuelist = list(map(int,valuelist))
                    cardbuy = sum(valuelist)

            # get 所有卡的資訊
            command = 'select * from cardinfo order by card'
            datalen , data = await self.getdbdata(logintoken,command,True)

            if datalen !=6:
                raise ValueError('get cardinfo error')

            itemdata = []
            lifetime = ''

            for item in data:
                tempdata = {}
                tempdata['card'] = item.get('card')

                twomonthaccbuy = item.get('twomonthaccbuy')
                if twomonthaccbuy ==-3:
                    tempdata['twomonthaccbuy'] = '-'
                elif twomonthaccbuy ==-2:
                    tempdata['twomonthaccbuy'] = '綁定門號'
                elif twomonthaccbuy ==-1:
                    tempdata['twomonthaccbuy'] = '首儲'
                else:
                    tempdata['twomonthaccbuy'] = format(twomonthaccbuy,',')+ '元'

                twomonthaccbet = item.get('twomonthaccbet')
                if twomonthaccbet == -1:
                    tempdata['twomonthaccbet'] = '-'
                else:
                    tempdata['twomonthaccbet'] = format(int(twomonthaccbet/10000),',') + '萬\n\r(金幣)'

                dailygiftamount = item.get('maxgiftamount')
                if dailygiftamount ==-1:
                    tempdata['dailygiftamount'] = '無限制'
                elif dailygiftamount ==0:
                    tempdata['dailygiftamount'] = '不可'
                else:
                    tempdata['dailygiftamount'] = format(int(dailygiftamount/10000),',') +'萬\n\r(金幣)'

                giftlistamount = item.get('maxgiftlistamount')
                if giftlistamount ==0:
                    tempdata['giftlistamount'] = '-'
                else:
                    tempdata['giftlistamount'] = format(giftlistamount,',') + '筆'

                cangetgift = item.get('cangetgift')
                if cangetgift ==0:
                    tempdata['cangetgift'] = '不可'
                else:
                    tempdata['cangetgift'] = '可以'

                cardlifetime = item.get('cardlifetime')
                if cardlifetime ==0:
                    tempdata['cardlifetime'] = '永久'
                else:
                    tempdata['cardlifetime'] = '一個月'

                if item.get('card') == card:
                    lifetime = tempdata['cardlifetime']


                freecoin = item.get('freecoin')
                if freecoin == 0:
                    tempdata['freecoin'] = '-'
                else:
                    tempdata['freecoin'] = format(freecoin) + '金幣'

                keepseatstr = item.get('keepseatstr')
                tempdata['keepseat'] = keepseatstr

                tmpdailybonusinf = item.get('dailybonusinfo')
                tempdata['dailybonusinfo'] = tmpdailybonusinf

                itemdata.append(tempdata)

            # 準備該會員的一些資料
            buypoint = ''
            accbet = ''
            if card in [2,3,4]:
                buypoint = format(cardbuy,',')+ ' / ' + format(data[card+1].get('twomonthaccbuy'),',') + '元'
                accbet = format(int(cardbet/10000),',') + ' / ' + format(int(data[card+1].get('twomonthaccbet')/10000),',') + '萬'





            result = pg_general.Apiresult.success
            resultdata = {
                "lifetime": lifetime,
                "buypoint": buypoint,
                "accbet": accbet,
                "card": card,
                "itemdata": itemdata


            }


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getcardinfo ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getcardinfo Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getcardinfo return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getchannellist(self,logintoken,memberid,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getchannellist memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command  = 'select channelindex,channelname from channel where enable=1 order by posindex'
            datalen , data = await  self.getdbdata(logintoken,command,True)

            channellist = []
            if datalen <1:
                raise ValueError('get channel error')
            channellist = data.copy()

            for item in channellist:
                channelindex = item.get('channelindex')
                # get redis 資料
                redischannellist = await redis_obj.get_all_keys('channel_{0}_*'.format(channelindex))
                item['amount'] = len(redischannellist)

            result = pg_general.Apiresult.success
            resultdata = {
                "channellist": channellist
            }


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getchannellist ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getchannellist Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getcardinfo return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata
    async def getchannelmember(self,logintoken,memberid,channelindex,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getchannelmember memberid:{0},logintoken:{1},channelindex:{2}'.format(
                                    memberid, logintoken,channelindex))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # get redis channel all joined member
            channelmemberlist = await redis_obj.get_all_keys('channel_{0}_*'.format(channelindex))
            memberlisttemp = [item.split('_')[2] for item in channelmemberlist]
            memberlist = []
            if len(memberlisttemp) > 0:
                # get all member
                command = 'select memberid,card,level,nickname,avatar from member where memberid in ({})'.format(','.join(memberlisttemp))
                datalen ,data = await self.getdbdata(logintoken,command,True)
                for item in data:
                    memberlist.append({
                        "memberid": item.get('memberid'),
                        "card": item.get('card'),
                        "level": item.get('level'),
                        "nickname": item.get('nickname'),
                        "avatar": item.get('avatar')
                    })


            resultdata = {"memberlist": memberlist}

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getchannelmember ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getchannelmember Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getchannelmember return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def joinchannel(self,logintoken,memberid,channelindex,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joinchannel memberid:{0},logintoken:{1},channelindex:{2}'.format(
                                    memberid, logintoken,channelindex))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 抓此 channel 人數上限
            command = 'select maxuser from channel where channelindex="{0}" and enable=1'.format(channelindex)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen !=1 :
                raise ValueError('get maxuser in channel error')

            maxuser = data.get('maxuser')

            # get all member on this channel at redis
            channelmemberlist = await redis_obj.get_all_keys('channel_{0}_*'.format(channelindex))
            if len(channelmemberlist) < maxuser:
                # clear all this member key at redis
                oldmemberchannel = await redis_obj.get_all_keys('channel_*_{0}'.format(memberid))
                for item in oldmemberchannel:
                    await redis_obj.del_key(item)

                # add this member redis data
                await redis_obj.set_value('channel_{0}_{1}'.format(channelindex,memberid),'1',180)

                # update db.member.channel
                command = 'update member set channel="{0}" where memberid="{1}"'.format(channelindex,memberid)
                updateresult = await self.updatedbdata(logintoken,command)

                resultdata = {"result": 0}
            else:  # 人數超過上限
                resultdata = {"result": 1}



            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:joinchannel ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:joinchannel Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joinchannel return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata


    async def receivegift(self,logintoken,memberid,num,validate_password):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:receivegift memberid:{0},logintoken:{1},num:{2},password:{3}'.format(
                                    memberid, logintoken, num, validate_password))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 撈這筆單
            command = 'select * from gift where giftindex="{0}" and status =0'.format(num)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                raise ValueError('receivegift get gift error')

            frommemberid = data.get('frommemberid')
            tomemberid = data.get('tomemberid')
            type = data.get('type')
            amount = data.get('amount')
            password = data.get('password')

            if password ==validate_password and str(tomemberid) == memberid:
                # update member.credit
                command = 'update member set credit=credit+"{0}" where memberid = "{1}"'.format(amount,memberid)
                updateresult = await self.updatedbdata(logintoken,command)

                # update gift 該筆狀態
                command = 'update gift set status =1 where giftindex ="{0}"'.format(num)
                updateresult = await self.updatedbdata(logintoken,command)

                # 在撈一次 該會員 credit
                command = 'select credit from member where memberid="{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken,command,False,True)

                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 0,
                    "aftercredit": data.get('credit')
                }

                #write to transaction log
                param = {
                    "frommemberid": frommemberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.receivegift,
                    "amount": amount,
                    "otherdata": "receivegift"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken,param))


            else:
                resultdata = {
                    "result": 1
                }


            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:receivegift ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:receivegift Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:receivegift return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def noticeusercredit(self,redis_obj,memberid,logintoken):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:noticeusercredit memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))

            # 抓 lobbyserver ip
            ip = await redis_obj.get_value('online_{}'.format(memberid))
            if ip is None:
                return

            # get logintoken
            tologintoken = await redis_obj.get_value('{}'.format(memberid))
            if tologintoken is None:
                return

            # get credit
            command = 'select credit,silvercredit from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command,False,True)

            if datalen ==1:
                credit = data.get('credit')
                silvercredit = data.get('silvercredit')
                sendmsg = {
                    "type": SendMsgType.server_to_client,
                    "logintoken": tologintoken,
                    "msg": {"commandid": 3000016, "data": {"credit": credit,"silvercredit": silvercredit}}
                }
                if env_setting.LOCAL_SERVER == False:
                    realurl = 'http://{}/broadcasttoall'.format(ip)
                else:
                    realurl = 'http://127.0.0.1/broadcasttoall'
                async with aiohttp.ClientSession() as session:
                    async with session.get(realurl, json=sendmsg) as response:
                        if response.status == 200:
                            data = await response.text()
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'noticeusercredit response:{0},sendmsg:{1}'.format(data, sendmsg))


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:noticeusercredit except:{0}'.format(e))

    async def rejectgift(self,redis_obj,logintoken,memberid,num):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:rejectgift memberid:{0},logintoken:{1},num:{2}'.format(
                                    memberid, logintoken, num))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 撈這筆單
            command = 'select * from gift where giftindex="{0}" and status=0'.format(num)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen != 1:
                raise ValueError('reject gift get gift error')

            frommemberid = data.get('frommemberid')
            tomemberid = data.get('tomemberid')
            type = data.get('type')
            amount = data.get('amount')
            ori_amount = data.get('ori_amount')

            if str(tomemberid) != memberid:
                raise ValueError('tomemberid != memberid')

            # 退回原始帳戶
            command = 'update member set credit=credit+"{0}" where memberid="{1}"'.format(ori_amount,frommemberid)
            updateresult = await self.updatedbdata(logintoken,command)

            # 改 status to 3
            command = 'update gift set status = 3 where giftindex="{0}"'.format(num)
            updateresult = await self.updatedbdata(logintoken,command)

            result = pg_general.Apiresult.success

            # notice user
            asyncio.ensure_future(self.noticeusercredit(redis_obj,frommemberid,logintoken))

            # write to transaction log
            param = {
                "frommemberid": frommemberid,
                "tomemberid": memberid,
                "type": pg_general.transactiontype.rejectgift,
                "amount": ori_amount,
                "otherdata": "rejectgift"
            }
            asyncio.ensure_future(self.writetransactionlog(logintoken,param))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:rejectgift ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:rejectgift Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:rejectgift return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata


    async def sendchannelchat(self,redis_obj,logintoken,memberid,channelindex,type,content,bubbleinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchannelchat memberid:{0},logintoken:{1},channelindex:{2},type:{3},content:{4}'.format(
                                    memberid, logintoken, channelindex,type,content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # check black content
            result_blackcontent = await self.check_black_chat_content(logintoken, content)
            if result_blackcontent == True:
                result = pg_general.Apiresult.success
                resultdata = {"black_chat_content": True}
                return result, resultdata




            chattime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')
            # 抓自己的 資料
            command = 'select nickname,level,card,avatar from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken,command)

            if datalen != 1:
                raise ValueError('get self data error')

            card = data.get('card')
            if card == 0:
                result = pg_general.Apiresult.success
                resultdata = {"card_0": True}
                return result, resultdata

            if bubbleinfo =={}:
                bubbleinfo = {
                    "memberid": int(memberid),
                    "nickname": data.get('nickname'),
                    "avatar": data.get('avatar')
                }


            resultdata = {
                "data" :{
                    "channelindex": int(channelindex),
                    "memberid": int(memberid),
                    "nickname": data.get('nickname'),
                    "level": pg_general.converttype(data.get('level'),int),
                    "card": pg_general.converttype(data.get('card'),int),
                    "avatar": data.get('avatar'),
                    "type": int(type),
                    "content": content,
                    "time":chattime,
                    "bubbleinfo": bubbleinfo
                }
            }
            # 紀錄 log
            asyncio.ensure_future(self.savechatlog(logintoken, memberid, "0", channelindex, "2", type, content))  # save to db.chatlog

            # add to redis chatroom_channel_{}
            redischanneldata = resultdata.get('data')
            await redis_obj.lpush('chatroom_channel_{}'.format(channelindex),json.dumps(redischanneldata))
            await redis_obj.ltrim('chatroom_channel_{}'.format(channelindex),0,100)

            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchannelchat ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchannelchat Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchannelchat return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata


    async def signal_action_future(self,redis_obj,logintoken,memberid,content,signaldata):
        try:

            id = signaldata.get('id')
            signal = signaldata.get('signal')
            promotionid = signaldata.get('promotionid')
            passcontent = signaldata.get('passcontent')
            timefailcontent = signaldata.get('timefailcontent')
            cardfailcontent = signaldata.get('cardfailcontent')
            dupphonefailcontent = signaldata.get('dupphonefailcontent')
            dupmemberfailcontent = signaldata.get('dupmemberfailcontent')
            bindphonefailcontent = signaldata.get('bindphonefailcontent')
            inboxtitle = signaldata.get('inboxtitle')
            inboxcontent = signaldata.get('inboxcontent')
            inboxdateline = signaldata.get('inboxdateline')

            if content.strip() != signal:
                return
            await asyncio.sleep(0.5)
            # 先判斷卡別與電話
            command = 'select memberid,card,phone,level from member where memberid= "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen !=1 :
                raise Exception('can not get card  phone')

            card = data.get('card')
            phone = data.get('phone')
            level = data.get('level')
            feedbackstr = ''
            if phone == '0':                        # 是否綁定手機
                feedbackstr = bindphonefailcontent
                raise ValueError('binphoneerror')
            if card < 2:                            # card >=2
                feedbackstr = cardfailcontent
                raise ValueError('cardfail')
            phonereceiveflag = await redis_obj.hget('signal_action_phone_{}'.format(id),phone)
            if phonereceiveflag is not None:        # phone 領過不能領
                feedbackstr = dupphonefailcontent
                raise ValueError('phonereceive')
            memberreceiveflag = await redis_obj.hget('signal_action_member_{}'.format(id),str(memberid))
            if memberreceiveflag is not None:       # member 領過不能領
                feedbackstr = dupmemberfailcontent
                raise ValueError('memberreceive')

            if content.strip() == signal:
                # 答對了 寫入 inbox
                credit_award = 1000 + (level*5)
                if credit_award >= 3688:
                    credit_award = 3688


                command = 'insert into memberinbox(memberid,inboxuri,mailtype,inboxtitle,inboxcontent,receivestate,dateline,promotionid,credit_award) values' \
                          '("{0}","uri","6","{1}","{2}","1","{3}","{4}","{5}")'.format(memberid,inboxtitle,inboxcontent,inboxdateline,promotionid,credit_award)
                insertresult = await self.insertdbdata(logintoken,command)


                # 寫入 redis
                await redis_obj.hset('signal_action_phone_{}'.format(id), phone,'1')
                await redis_obj.hset('signal_action_member_{}'.format(id),str(memberid),'1')

                # 寫入 signallog
                logtime = pg_general.getutcnow_datetime()
                command = 'insert into signallog(memberid,logtime,signalid)values("{0}","{1}","{2}")'.format(memberid,logtime,id)
                inserresult = await self.insertdbdata(logintoken,command)

                # 回傳 passcontent
                # await self.servicetouser(redis_obj, memberid, passcontent)
                result, clientdata = await self.servicetouser(redis_obj, memberid, passcontent)
                if result == pg_general.Apiresult.success:
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
                        if env_setting.LOCAL_SERVER == False:
                            realurl = 'http://' + userip + "/broadcasttoall"
                        else:
                            realurl = 'http://127.0.0.1/broadcasttoall'

                        async with aiohttp.ClientSession() as session:
                            async with session.get(realurl, json=sendmsg) as response:
                                if response.status == 200:
                                    data = await response.text()
                                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                        'send_to_all_lobbyserver_future response:{0}'.format(data))
            else:
                feedbackstr = '通關密語錯誤, 快上官方粉絲團查看, 時間有限, 快把握機會 !!'
                raise ValueError('signal error')
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                'pg_asqldb:signal_action_future ValueError except:{0}'.format(e))
            # await self.servicetouser(redis_obj, memberid, feedbackstr)
            result, clientdata = await self.servicetouser(redis_obj, memberid, feedbackstr)

            if result == pg_general.Apiresult.success:
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
                    if env_setting.LOCAL_SERVER == False:
                        realurl = 'http://' + userip + "/broadcasttoall"
                    else:
                        realurl = 'http://127.0.0.1/broadcasttoall'

                    async with aiohttp.ClientSession() as session:
                        async with session.get(realurl, json=sendmsg) as response:
                            if response.status == 200:
                                data = await response.text()
                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                    'send_to_all_lobbyserver_future response:{0}'.format(data))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:signal_action_future Exception except:{0}'.format(e))




    async def sendservicechat(self,redis_obj,logintoken,memberid,type,content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendservicechat memberid:{0},logintoken:{1},type:{2},content:{3}'.format(
                                    memberid, logintoken, type,content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 先做任務 通關密語任務
            signaldata = await redis_obj.get_json_value('signal_action')
            if signaldata is not None:
                asyncio.ensure_future(self.signal_action_future(redis_obj,logintoken,memberid,content,signaldata))

            # get member chatroom_service
            command = 'select * from chatroom_service where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen == 0:  # 沒資料
                savetime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
                chatlist = [{
                    "time":savetime,
                    "type": type,
                    "content": content}
                ]
                command = 'insert into chatroom_service (memberid,content,flag) values("{0}",\'{1}\',"{2}")'.format(memberid,json.dumps(chatlist, ensure_ascii=False),0)
                updateresult = await self.updatedbdata(logintoken,command)

            elif datalen ==1:
                chatlist = data.get('content')
                if chatlist!=None:
                    chatlist = json.loads(chatlist, encoding='utf-8')

                    savetime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
                    chatdict = {
                        "time": savetime,
                        "type": type,
                        "content": content
                    }
                    chatlist.append(chatdict)
                    lenofchatlist = len(chatlist)
                    if lenofchatlist>5:
                        chatlist = chatlist[lenofchatlist-5:]
                    command = 'update chatroom_service set content=\'{0}\',flag=0 where memberid="{1}"'.format(json.dumps(chatlist, ensure_ascii=False),memberid)
                    udpateresult = await self.updatedbdata(logintoken,command)
                else:
                    savetime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
                    chatlist = [{
                        "time": savetime,
                        "type": type,
                        "content": content
                    }]
                    command = 'update chatroom_service set content=\'{0}\',flag=0 where memberid="{1}"'.format(
                        json.dumps(chatlist, ensure_ascii=False), memberid)
                    udpateresult = await self.updatedbdata(logintoken, command)
            else:
                raise ValueError('get charoom service error')

            # 紀錄 log
            asyncio.ensure_future(self.savechatlog(logintoken, memberid, "0", 0, "3", type, content))  # save to db.chatlog

            # 發 telegram
            if env_setting.PRODUCTION_MODE == False:
                telebot_msg = "***這是測試機測試資料***\n"
            else:
                telebot_msg = ''
            telebot_msg += "時間:{}\n".format(pg_general.datetimetostr_nof(pg_general.get_tw_datetime()))
            telebot_msg += "會員編號:{}\n".format(memberid)
            telebot_msg += "內容:{}\n".format(content)
            

            asyncio.ensure_future(self.sendtelebot(telebot_msg))

            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendservicechat ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendservicechat Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendservicechat return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def sendgift(self,logintoken,memberid,nickname,ori_amount,password,addflag,code):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgift memberid:{0},logintoken:{1},nickname:{2},amount:{3},password:{4},addflag:{5},code:{6}'.format(
                                    memberid, logintoken, nickname,ori_amount,password,addflag,code))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}




            # 比對 password 是否為六位數字
            if len(password) !=6 or password.isdigit() == False:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 3
                }
                return result , resultdata

            if ori_amount <20000:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 4
                }
                return result, resultdata

            # 找對方 memberid , 限制對方比較要為銀卡以上 card > 0
            command = 'select memberid,avatar from member where nickname="{0}" and card > 0'.format(nickname.strip())
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen <=0:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 2
                }
                return result , resultdata
            tomemberid = data.get('memberid')
            toavatar = data.get('avatar')

            # 檢查驗證碼是否錯誤 或是 驗證碼超過 10 分鐘過期
            command = 'select member.membertype,member.card,member.level,phonebindstatus,phonevalidatecode,phonevalidatetime,todaygiftamount,todaygifttimes, ' \
                      'cardinfo.maxgifttimes,cardinfo.maxgiftamount,member.credit as membercredit,setting2.giftreservecredit from member,cardinfo,setting2 where memberid="{0}" and cardinfo.card = member.card'.format(memberid)
            datalen,data = await self.getdbdata(logintoken,command)
            if datalen != 1:
                raise ValueError('get member info error')

            membercard = data.get('card')
            memberlevel = data.get('level')
            gifttime = pg_general.getutcnow_datetime()
            maxgifttimes = data.get('maxgifttimes')
            maxgiftamount = data.get('maxgiftamount')
            todaygifttimes = data.get('todaygifttimes')
            todaygiftamount = data.get('todaygiftamount')
            phonebindstatus = data.get('phonebindstatus')
            phonevalidatecode = data.get('phonevalidatecode')
            phonevalidatetime = data.get('phonevalidatetime')
            membercredit = data.get('membercredit')
            giftreservecredit = data.get('giftreservecredit')
            membertype = data.get('membertype')

            if membercard in [2,3,4] and memberlevel >=50:
                maxgiftamount = 20000000

            if membertype != 0:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 9
                }
                return result,resultdata

            if phonebindstatus !=2:         # 手機沒綁定
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 6
                }
                return result,resultdata

            overseconds = (gifttime-phonevalidatetime).total_seconds()
            if overseconds > 600:   # 驗證碼過期
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 5
                }
                return result,resultdata

            if code != phonevalidatecode:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 7
                }
                return result,resultdata

            if todaygifttimes + 1> maxgifttimes and maxgifttimes != -1:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 8
                }
                return result , resultdata

            if todaygiftamount + ori_amount > maxgiftamount and maxgiftamount != -1:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 9
                }
                return result , resultdata

            lockgiftdata = await self.getgiftfreezedata(logintoken,memberid)
            lockgiftamount = lockgiftdata.get('freezetotalamount')


            # 檢查帳戶是否有大於等於(強制保留值+凍結額度)
            if (membercredit-ori_amount) < (giftreservecredit+lockgiftamount):
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 10
                }
                return result, resultdata


            # 直接扣款順便檢查是否餘額足夠
            command = 'update member set credit = credit - "{0}" , phonevalidatetime="{2}", todaygifttimes=todaygifttimes+1, ' \
                      'todaygiftamount = todaygiftamount + "{3}" where memberid ="{1}" and credit >= "{0}" and credit >= "{4}"'.format(ori_amount,memberid,gifttime-timedelta(days=1),ori_amount,(ori_amount+giftreservecredit))
            updaterows = await self.updatedbdata_affectrows(logintoken,command)

            if updaterows <1: # 餘額不足
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 1
                }
                return result, resultdata

            # write to transaction log
            param = {
                "frommemberid": memberid,
                "tomemberid": tomemberid,
                "type": pg_general.transactiontype.gift,
                "amount": ori_amount,
                "otherdata": "gift"
            }
            asyncio.ensure_future(self.writetransactionlog(logintoken,param))



            type = 0
            amount = int(ori_amount*0.98)
            status = 0

            # insert into gift table
            command = 'insert into gift (frommemberid,tomemberid,gifttime,type,amount,ori_amount,password,status) values ' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}")'.format(memberid,tomemberid,gifttime,type,amount,ori_amount,password,status)
            insertresult,rowindex = await self.insertdbdata(logintoken,command)


            if addflag == 1:
                # 加入常用名單
                command = 'select giftlist from member where memberid="{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken , command )
                if datalen >0:
                    if str(tomemberid) not in data.get('giftlist'):
                        giftlistdata = data.get('giftlist').strip()
                        if len(giftlistdata) ==0:
                            giftlistdata = str(tomemberid)
                        else:
                            giftlistdata = giftlistdata + ',{0}'.format(tomemberid)
                        command = 'update member set giftlist = "{0}" where memberid = "{1}"'.format(giftlistdata,memberid)
                        updateresult = await self.updatedbdata(logintoken , command)



            # 抓  todayleftcreditamount todaylefttimes , aftercredit
            # 抓取 member.credit,todaygiftamount,todaygifttimes and cardinfo.maxgiftamount,maxgifttimes
            command = 'select member.card,member.level,member.credit, member.todaygiftamount,member.todaygifttimes,cardinfo.maxgiftamount,cardinfo.maxgifttimes, ' \
                      'member.giftlist from member,cardinfo' \
                      ' where member.memberid = "{0}" and member.card=cardinfo.card'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command,False,True)
            if datalen != 1:
                raise ValueError('get card or member error')

            membercard = data.get('card')
            memberlevel = data.get('level')
            aftercredit= data.get('credit')
            todaygiftamount = data.get('todaygiftamount')
            todaygifttimes = data.get('todaygifttimes')
            todaytotalcreditamount = data.get('maxgiftamount')
            todaytotaltimes = data.get('maxgifttimes')
            giftlist = data.get('giftlist')

            if membercard in [2,3,4] and memberlevel >= 50:
                todaytotalcreditamount = 20000000

            if len(giftlist.strip()) == 0:
                giftlistamount = 0
            else:
                giftlistamount = len(giftlist.split(','))

            if todaytotalcreditamount == -1:
                todayleftcreditamount = -1
            else:
                todayleftcreditamount = todaytotalcreditamount - todaygiftamount
                if todayleftcreditamount < 0:
                    todayleftcreditamount = 0

            if todaytotaltimes == -1:
                todaylefttimes = -1
            else:
                todaylefttimes = todaytotaltimes - todaygifttimes
                if todaylefttimes < 0:
                    todaylefttimes = 0

            updategiftlist = []
            if len(giftlist.strip())>0:
                command = 'select memberid,nickname,avatar,level,activenumber,card from member where memberid in ({})'.format(giftlist)
                datalen , data = await self.getdbdata(logintoken, command , True)
                if datalen > 0 :
                    for item in data:
                        updategiftlist.append({
                            "memberid": item.get('memberid'),
                            "nickname": item.get('nickname'),
                            "avatar": item.get('avatar'),
                            "level": item.get('level'),
                            "activenumber": item.get('activenumber'),
                            "card": item.get('card')
                        })


            resultdata = {
                "result": 0,
                "aftercredit": aftercredit,
                "sendtime": pg_general.get_utc_to_local_datetime(gifttime).strftime('%Y-%m-%d %H:%M:%S'),
                "num": str(rowindex),
                "tonickname": nickname,
                "amount": amount,
                "password": password,
                "todayleftcreditamount" : todayleftcreditamount,
                "todaylefttimes" : todaylefttimes,
                "giftlistamount": giftlistamount,
                "giftlist": updategiftlist,
                "toavatar": toavatar

            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgift ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgift Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgift return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata


    async def sendgiftsms(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgiftsms memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 撈此玩家 資料
            command = 'select phone,phonebindstatus,phonevalidatecode,phonevalidatetime from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get member info error')

            phonebindstatus = data.get('phonebindstatus')
            phonevalidatecode = data.get('phonevalidatecode')
            phonevalidatetime = data.get('phonevalidatetime')
            phone = data.get('phone')

            if phonebindstatus !=2 : # 未完成綁定手機
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 1
                }
                return result , resultdata

            nowutcdatetime = pg_general.getutcnow_datetime()
            overseconds = (nowutcdatetime - phonevalidatetime).total_seconds()
            if overseconds <60:  # 一分鐘未到
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 2
                }
                return result,resultdata

            validatecode = random.randint(100000, 999999)
            # 發送 code to phone
            await pg_sms.sendsms(phone, validatecode)

            # 紀錄 db
            command = 'update member set phonevalidatecode="{0}",phonevalidatetime="{1}" where memberid = "{2}"'.format(
                validatecode, nowutcdatetime, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            # insert into phonevalidatelog
            command = 'insert into phonevalidatelog (logtime,phone,memberid,validatecode) values("{0}","{1}","{2}","{3}")'.format(
                nowutcdatetime, phone, memberid, validatecode)
            insertresult = await self.updatedbdata(logintoken, command)

            resultdata = {
                "result": 0
            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgiftsms ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgiftsms Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgiftsms return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getspecialaction(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getspecialaction memberid:{0},logintoken:{1}'.format(memberid,logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select specialactionurlnew from setting2'
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen > 0 :
                result = pg_general.Apiresult.success

                resultdata = {
                    "specialactionurlnew": data.get('specialactionurlnew')
                }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getspecialaction Exception except:{0}'.format(e))


        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getspecialaction return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getfirstbuymallinfo(self,logintoken,memberid):    # 取得首購商城資料
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getfirstbuymallinfo logintoken:{0},memberid:{1}'.format(logintoken,memberid))
            clientdata = {}
            firstbuycountdownsec = 0
            firstbuytotalpercent = 0
            # get setting2.firstbuycountdownsec , setting2.firstbuytotalpercent
            command = 'select firstbuycountdownsec,firstbuytotalpercent from setting2'
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen ==1:
                firstbuycountdownsec = data.get('firstbuycountdownsec')
                firstbuytotalpercent = data.get('firstbuytotalpercent')

            firstbuymallinfo = []
            command = 'select * from mallinfofirstbuy order by showindex'
            datalen, data = await self.getdbdata(logintoken,command,True)
            if datalen > 0 :
                for item in data:
                    firstbuymallinfo.append({
                        "shopid": item.get('shopid'),
                        "cash": item.get('cash'),
                        "showindex": item.get('showindex'),
                        "oricredit": item.get('oricredit'),
                        "offerpercent": item.get('offerpercent'),
                        "aftercredit": item.get('aftercredit')

                    })
                
            clientdata = {
                "firstbuymallinfo": firstbuymallinfo,
                "firstbuycountdownsec": firstbuycountdownsec,
                "firstbuytotalpercent": firstbuytotalpercent
            }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getfirstbuymallinfo logintoken:{0},memberid:{1}'.format(logintoken,memberid))

        return clientdata

    async def normalmall(self,logintoken,memberid,shopid,mode):      # 正常商城
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:normalmall logintoken:{0},memberid:{1},shopid:{2}:mode:{3}'.format(logintoken,memberid,shopid,mode))
            ret_data= {
                "credit": 0,
                "buycredit": 0,
                "content": {}
            }
            result = pg_general.Apiresult.connectdberror

            getmall_result, clientdata = await self.getmallinfo(logintoken,memberid,mode)
            if getmall_result != pg_general.Apiresult.success:
                raise ValueError('getmallinfo error')

            mallcontentlist = clientdata.get('mallcontent')
            mallcontent = {}
            for _item in mallcontentlist:
                if _item.get('shopid') == shopid:
                    mallcontent = _item.copy()
                    break
            buycredit = mallcontent.get('credit')
            cash = int(mallcontent.get('cash'))
            command = 'select member.card,member.point,member.credit from member where member.memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen != 1:
                raise ValueError('get member levelinfo is wrong')

            aftercredit = data.get('credit')
            afterpoint = data.get('point')
            card = data.get('card')

            # update member credit
            command = 'update member set point=point+"{0}",isfirstbuy=0 where memberid="{1}"'.format(buycredit,memberid)
            update_result = await self.updatedbdata(logintoken,command)
            if update_result == False:
                raise ValueError('update member credit error')

            # prepare return data
            result = pg_general.Apiresult.success
            ret_data = {
                "credit": aftercredit,
                "buycredit": buycredit,
                "content": {},
                "cash": cash,
                "card": card
            }
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:normalmall ValueError:{0},memberid:{1},shopid:{2}'.format(e, memberid, shopid))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:normalmall except:{0},memberid:{1},shopid:{2}'.format(e, memberid, shopid))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:normalmall return result:{0},ret_data:{1}'.format(result,ret_data))
            return result,ret_data
    async def firstbuymall(self,logintoken,memberid,shopid): # 首購商城
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:firstbuymall logintoken:{0},memberid:{1},shopid:{2}'.format(logintoken, memberid,
                                                                                                    shopid))
            ret_data = {
                "credit": 0,
                "buycredit": 0,
                "content": {}
            }
            result = pg_general.Apiresult.connectdberror

            command = 'select * from mallinfofirstbuy where shopid ="{0}"'.format(shopid)
            datalen, data = await self.getdbdata(logintoken,command)

            if datalen !=1:
                raise ValueError('get member credit is wrong')


            buycredit = data.get('point')
            cash = data.get('cash')

            # get member credit,secretmallid , secretoffermall.buycredit
            command = 'select member.card,member.credit from member ' \
                      ' where member.memberid="{0}"'.format(memberid)

            datalen , data = await self.getdbdata(logintoken,command)
            if datalen != 1:
                raise ValueError('get member credit is wrong')

            aftercredit = data.get('credit')
            card = data.get('card')

            # update member.credit
            command = 'update member set point = point+ "{0}",isfirstbuy=0 where memberid="{1}"'.format(buycredit,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == True:
                ret_data = {
                    "credit": aftercredit,
                    "buycredit": buycredit,
                    "content": {},
                    "cash": cash,
                    "card": card
                }
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:firstbuymall ValueError:{0},memberid:{1},shopid:{2}'.format(e, memberid, shopid))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:firstbuymall except:{0},memberid:{1},shopid:{2}'.format(e, memberid, shopid))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:firstbuymall return result:{0},ret_data:{1}'.format(result,ret_data))
            return result,ret_data



    async def secretoffermall(self,logintoken,memberid,shopid): # secret offer 商城
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:secretoffermall logintoken:{0},memberid:{1},shopid:{2}'.format(logintoken, memberid,
                                                                                                    shopid))
            ret_data = {
                "credit": 0,
                "buycredit": 0,
                "content": {}
            }
            result = pg_general.Apiresult.connectdberror

            # get member credit,secretmallid , secretoffermall.buycredit
            command = 'select member.card,member.credit,secretoffermall.buypoint,secretoffermall.cost from member,secretoffermall ' \
                      ' where member.memberid="{0}" and secretoffermall.id = member.secretmallid'.format(memberid)

            datalen , data = await self.getdbdata(logintoken,command)
            if datalen != 1:
                raise ValueError('get member credit is wrong')

            buycredit = data.get('buypoint')
            aftercredit = data.get('credit')
            cash = data.get('cost')
            card = data.get('card')

            # update member.credit
            command = 'update member set point = point+ "{0}",isfirstbuy=0 where memberid="{1}"'.format(buycredit,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == True:
                ret_data = {
                    "credit": aftercredit,
                    "buycredit": buycredit,
                    "content": {},
                    "cash": cash,
                    "card": card
                }
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:secretoffermall ValueError:{0},memberid:{1},shopid:{2}'.format(e, memberid, shopid))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:secretoffermall except:{0},memberid:{1},shopid:{2}'.format(e, memberid, shopid))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:secretoffermall return result:{0},ret_data:{1}'.format(result,ret_data))
            return result,ret_data


    async def write_mall_history(self,logintoken,memberid,shopid,price,transaction_id,malltype,platform,statuscode,receipt_data,currencycode,response_data=None):
        try:
            buytime = datetime.utcnow()
            command = 'insert into mallhistory (shopid,buytime,cost,transactionid,malltype,memberid,logintoken,platform,statuscode,receipt,currencycode,response_data)' \
                      'values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}")'.format(shopid,buytime,price,transaction_id,malltype,memberid,logintoken,platform,statuscode,receipt_data,currencycode,response_data)
            result_insert , index = await self.insertdbdata(logintoken,command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:write_mall_history exception:{0}'.format(e))




    async def servicetouser(self,redis_obj,memberid,content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:servicetouser memberid:{0},content:{1}'.format(memberid, content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 先抓此玩家是否在線上 判斷 ttl online_(mmeberid) >=10
            ttltime = await redis_obj.ttl('online_{0}'.format(memberid))

            asyncio.ensure_future(self.savechatlog('servicetouser', 0, memberid, 0, 3, 0, content))

            nowtwtime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')
            nowutctime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
            if ttltime >=10: # 代表在線上 傳給 lobby server 直接傳給 member 將資料帶回上層
                # 抓 user ip
                userip = await redis_obj.get_value('online_{0}'.format(memberid))
                memberlogintoken = await redis_obj.get_value(memberid)
                resultdata = {
                    "result" : 0,
                    "userip": userip,
                    "logintoken": memberlogintoken,
                    "msg": {
                        "commandid":3000012,
                        "data":{
                            "time": nowtwtime,
                            "contentlist":[content]
                         }
                    }
                }


            else: # 不在線上 存到 redis service_(memberid) lpush
                await redis_obj.lpush('servicechat_{0}'.format(memberid),content)
                await redis_obj.expire('servicechat_{0}'.format(memberid),604800) # 七天過期
                resultdata = {'result': 1} # 代表 save to redis

            # save to chatroom_service
            command = 'update chatroom_service set flag = "1" ,content = json_array_append(content, "$",json_object("time","{0}","type",0,"content","{1}")) ' \
                      'where memberid = "{2}"'.format(nowutctime,content,memberid)

            updateresult = await self.updatedbdata('insert into chatroom_service',command)

            result = pg_general.Apiresult.success



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:servicetouser except:{0}'.format(e))

        return result,resultdata



    async def getuncompletedgame(self,seatid):
        try:
            result = False
            clientdata = {"result": False}
            # 抓取此玩家 還有的 未完成遊戲
            if seatid[0] == 'g':
                url = env_setting.PS_UNCOMPLETEGAME_URL.format(env_setting.PS_HOST_ID, seatid)
            elif seatid[0] == 's':
                url = env_setting.PS_UNCOMPLETEGAME_URL.format(env_setting.PS_HOST_ID_S, seatid)
            elif seatid[0] == 't':
                url = env_setting.PS_UNCOMPLETEGAME_URL.format(env_setting.PS_HOST_ID_T, seatid)

            errcount = 0
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response:
                            if response.status == 200:
                                data1 = await response.json()
                                result1 = pg_general.Apiresult.success
                                break
                            else:
                                errcount += 1
                                await asyncio.sleep(0)

                except Exception as e:
                    errcount += 1
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'pg_asqldb:getuncompletedgame exception 1: {0},errcount:{1},seatid:{2}'.format(e, errcount,seatid))

            if errcount >= 3:
                result = False

                return result,clientdata
            if data1 != {}:  # 代表有位完成遊戲
                clientdata={"result":True}

            result = True



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getuncompletedgame exception 2: {0}'.format(e))


        return result , clientdata


    async def backtohall(self,app,redis_obj,logintoken,memberid,gamelogdataindex,seat_data):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:backtohall memberid:{0},logintoken:{1},gamelogdataindex:{2},seat_data:{3}'.format(memberid,logintoken,gamelogdataindex,seat_data))
            result = pg_general.Apiresult.connectdberror
            resultdata = {"result": 0}

            nowutcdatetime = pg_general.getutcnow_datetime()
            command = 'update membergamelog set leavetime="{0}" where memberid="{1}" and logintoken="{2}" and membergameindex ="{3}"'.format(nowutcdatetime,memberid,logintoken,gamelogdataindex)
            updateresult = await self.updatedbdata(logintoken,command)


            # seatmemberid = '{}_{}_{}'.format(seatname, gameid, joinseatstatus.get('seatnum'))

            keepseatsecondslist = [{"keepseatseconds":item.get("keepseatseconds")} for item in app['cardinfo']]

            valuelist = seat_data.split('_')
            tempgametype = valuelist[0]
            if tempgametype == 'seatsgold':
                tempgametype = 'goldseats'
                tempgametype2 = 'seatsgold'
                tempseatid = 'gseat'
                tempdirtyseattype = 'g'
            elif tempgametype == 'seatssilver':
                tempgametype = 'silverseats'
                tempgametype2 = 'seatssilver'
                tempseatid = 'sseat'
                tempdirtyseattype = 's'
            elif tempgametype == 'seatstutorial':
                tempgametype = 'tutorialseats'
                tempgametype2 = 'seatstutorial'
                tempseatid = 'tseat'
                tempdirtyseattype = 't'
            elif tempgametype == 'seatsfishg':
                hostid = env_setting.PS_HOST_ID
                await self.call_gameapi_transferAllCreditToHost(logintoken,memberid,hostid, 0)
                # del member fish redis key
                tempgameid = valuelist[1].split('@')[0]
                await redis_obj.del_key('fish_g_{}_{}'.format(tempgameid,memberid))
                # del dirtyfish key
                await redis_obj.hdel('dirtyfish','g_{}_{}'.format(tempgameid,memberid))
                # notice credit and silvercredit
                asyncio.ensure_future(self.noticeusercredit(redis_obj, memberid, logintoken))
                result = pg_general.Apiresult.success
                return  result,resultdata
            elif tempgametype == 'seatsfishs':
                hostid = env_setting.PS_HOST_ID_S
                await self.call_gameapi_transferAllCreditToHost(logintoken, memberid, hostid, 1)
                # del member fish redis key
                tempgameid = valuelist[1].split('@')[0]
                await redis_obj.del_key('fish_s_{}_{}'.format(tempgameid, memberid))
                # del dirtyfish key
                await redis_obj.hdel('dirtyfish', 's_{}_{}'.format(tempgameid, memberid))
                # notice credit and silvercredit
                asyncio.ensure_future(self.noticeusercredit(redis_obj, memberid, logintoken))
                result = pg_general.Apiresult.success
                return result,resultdata

            tempgameid = valuelist[1].split('@')[0]
            tempseatnum = valuelist[1].split('@')[1]
            seatkey = tempgametype + '_' + tempgameid + '@' + tempseatnum

            valuelist2 = await redis_obj.hmget(seatkey, ['memberid', 'status', 'dateline', 'card'])

            tempmemberid = pg_general.converttype(valuelist2[0], int)
            tempstatus = pg_general.converttype(valuelist2[1], int)

            if valuelist2[2] is None or valuelist2[2] == '':
                valuelist2[2] = '2020-05-01 00:00:00'

            tempdateline = pg_general.strtodatetime_nof(valuelist2[2])

            tempcard = pg_general.converttype(valuelist2[3], int)

            tempkeepseconds = keepseatsecondslist[tempcard].get('keepseatseconds')
            tempnowutcdatetime = pg_general.getutcnow_datetime()
            tempuserseatkey = '{}_{}@{}_{}'.format(tempgametype2, tempgameid, tempseatnum, tempmemberid)
            seatid = '{}_{}_{}'.format(tempseatid, tempgameid, tempseatnum)
            uncompletedresult, uncomplietedclientdata = await self.getuncompletedgame(seatid)
            if uncompletedresult == True and uncomplietedclientdata.get('result') == True:  # 有未完成的遊戲 設定 status = 3 , dateline + 30 天
                newdateline_str = pg_general.datetime_to_str(tempnowutcdatetime + timedelta(days=30))
                await redis_obj.hmset(seatkey, {"dateline": newdateline_str, "status": 3})
                # set uncompletegame
                await redis_obj.hset('uncompletedgame', seatkey, 1)
                await redis_obj.set_value(tempuserseatkey, 3, 2592000)  # 位完成遊戲 保留 30 天
            else:   # 沒有未完成的遊戲
                if tempkeepseconds > 0 and tempdirtyseattype != 't':  # 要保留,  turtorial 強制不保留
                    newdateline_str = pg_general.datetime_to_str(tempnowutcdatetime + timedelta(seconds=tempkeepseconds))
                    await redis_obj.hmset(seatkey, {"dateline": newdateline_str, "status": 2})
                    await redis_obj.set_value(tempuserseatkey, 2, tempkeepseconds)
                    await redis_obj.hdel('uncompletedgame',seatkey)
                else:  # 不保留
                    # 清除 dirtyseat
                    await redis_obj.hdel('dirtyseat', '{}_{}_{}'.format(tempdirtyseattype,tempgameid,tempseatnum))
                    # 設定為空機台
                    if tempdirtyseattype == 'g':
                        await redis_obj.hset('gemptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                    elif tempdirtyseattype == 's':
                        await redis_obj.hset('semptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                    elif tempdirtyseattype == 't':
                        await redis_obj.hset('temptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                    # 刪除未完成遊戲紀錄
                    await redis_obj.hdel('uncompletedgame', seatkey)
                    # 設定座位狀態為 空台 : status = 0
                    await redis_obj.hmset(seatkey, {'status': 0})

            # notice credit and silvercredit
            asyncio.ensure_future(self.noticeusercredit(redis_obj, memberid, logintoken))
            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:backtohall except:{0}'.format(e))

        return result,resultdata

    async def joingameseat(self,redis_obj, logintoken, memberid,jsoncontent):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joingameseat memberid:{0},param:{1}'.format(memberid, jsoncontent))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            gameid = jsoncontent.get('gameid')
            gametype = jsoncontent.get('gametype')      # 0 : gold hall , 1: silver hall 2:
            seatnum = jsoncontent.get('seatnum')

            joinseatstatus = {
                "isjoin": False,
                "seatnum": 0

            }

            # check 教學模式資料正確性
            if gametype == 2 and seatnum != 0:
                return result,resultdata


            # get member info
            command = 'select memberid,tutorialbetfinish,card,avatar from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                return result,resultdata

            # 使用過 教學 強制 錯誤
            tutorialbetfinish = data.get('tutorialbetfinish')
            if gametype ==2 and tutorialbetfinish != 0:
                return result,resultdata

            card = data.get('card')
            avatar = data.get('avatar')

            # 找出機台數量
            command = 'select seatsamount,seatsamount_s,seatsamount_t from game where gameid="{0}"'.format(gameid)
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                return result,resultdata

            seatsamount = data.get('seatsamount')
            seatsamount_s = data.get('seatsamount_s')
            seatsamount_t = data.get('seatsamount_t')

            nowutctimestr = pg_general.datetime_to_str(pg_general.getutcnow_datetime())

            # 找出 自己的機台
            if gametype ==0: # gold
                seatlist = await redis_obj.get_all_keys('seatsgold_{}@*_{}'.format(gameid,memberid))
                temmpseatkey = 'goldseats'
            elif gametype ==1:  # silver
                seatlist = await redis_obj.get_all_keys('seatssilver_{}@*_{}'.format(gameid,memberid))
                temmpseatkey = 'silverseats'
            elif gametype ==2: # 教學模式
                seatlist = await redis_obj.get_all_keys('seatstutorial_{}@*_{}'.format(gameid,memberid))
                temmpseatkey = 'tutorialseats'
            else:
                return result,resultdata


            if seatlist is not None and seatlist !=[]:  # 有找到機台
                # 找出機台號碼
                for item in seatlist:
                    reservedseatnum = pg_general.converttype(item.split('@')[1].split('_')[0],int)
                    selfseatvalue = await redis_obj.get_value(item)
                    selfseatvalue = pg_general.converttype(selfseatvalue,int)
                    if selfseatvalue == 3:  # 有未完成遊戲 強制選此台
                        seatnum = reservedseatnum
                        break
                    elif selfseatvalue ==2: # 保留中
                        if reservedseatnum != seatnum or seatnum==0:  # 刪除不同機台編號的保留資訊,隨機選台刪除所有自己站位機台
                            await redis_obj.del_key(item)
                            await redis_obj.hmset('{}_{}@{}'.format(temmpseatkey,gameid,reservedseatnum),{"dateline":nowutctimestr} )   # 設定現在時間讓 control 回收
                        else:
                            await redis_obj.expire(item,30)  # 如果進去保留的機台 讓他時間維持 30 秒 ttl
                    elif selfseatvalue ==1: # playing
                        if reservedseatnum != seatnum or seatnum ==0:  # 刪除不同機台編號的保留資訊,隨機選台刪除所有自己站位機台
                            await redis_obj.del_key(item)
                            await redis_obj.hmset('{}_{}@{}'.format(temmpseatkey, gameid, reservedseatnum), {"dateline": nowutctimestr})  # 設定現在時間讓 control 回收
                        else:
                            await redis_obj.expire(item,30)  # 如果進去保留的機台 讓他時間維持 30 秒 ttl


            if seatnum !=0: # 進去某一台
                # 查詢該台是否是自己的
                if gametype == 0:
                    seatkey = 'goldseats_{}@{}'
                    selfseatkey = 'seatsgold_{}@{}_{}'
                elif gametype ==1:
                    seatkey = 'silverseats_{}@{}'
                    selfseatkey = 'seatssilver_{}@{}_{}'
                elif gametype ==2:
                    seatkey = 'tutorialseats_{}@{}'
                    selfseatkey = 'seatstutorial_{}@{}_{}'

                valuelist = await redis_obj.hmget(seatkey.format(gameid,seatnum),['memberid','status'])
                reservememberid = pg_general.converttype(valuelist[0],int)
                reservestatus = pg_general.converttype(valuelist[1],int)

                if memberid == reservememberid:     # 自己的,直接進去改狀態
                    await redis_obj.hmset(seatkey.format(gameid,seatnum),{"memberid":memberid,"status": 1,"card": card,"avatar": avatar})
                    await redis_obj.set_value(selfseatkey.format(gameid,seatnum,memberid),'1',30)
                    if gametype == 0:
                        await redis_obj.hdel('gemptyseats_{}'.format(gameid),str(seatnum))
                    elif gametype ==1:
                        await redis_obj.hdel('semptyseats_{}'.format(gameid),str(seatnum))
                    elif gametype ==2:
                        await redis_obj.hdel('temptyseats_{}'.format(gameid),str(seatnum))
                    joinseatstatus = {"isjoin": True,"seatnum": seatnum}
                elif memberid !=reservememberid and reservestatus !=0:  # 機台是別人的
                    result = pg_general.Apiresult.success
                    resultdata={
                        "result": 1,
                        "errdescription": '此機台已經有人搶先搂\n請換一台試試看!'
                    }
                    return result,resultdata
                else:       # 沒人的台子 , 可以進去
                    await redis_obj.hmset(seatkey.format(gameid,seatnum),{"memberid": memberid, "status": 1,"card": card,"avatar":avatar})
                    # 設定自己的 機台
                    await redis_obj.set_value(selfseatkey.format(gameid, seatnum, memberid), '1',30)
                    if gametype ==0:
                        await redis_obj.hdel('gemptyseats_{}'.format(gameid), str(seatnum))
                    elif gametype ==1:
                        await redis_obj.hdel('semptyseats_{}'.format(gameid),str(seatnum))
                    elif gametype ==2:
                        await redis_obj.hdel('temptyseats_{}'.format(gameid),str(seatnum))
                    joinseatstatus = {"isjoin": True, "seatnum": seatnum}



            else:           # 隨機挑台
                # 抓所有機台 key
                if gametype == 0:
                    seatkey = 'goldseats_{}@{}'
                    selfseatkey = 'seatsgold_{}@{}_{}'
                    emptyseatnumlist = await redis_obj.hkeys('gemptyseats_{}'.format(gameid))
                elif gametype ==1:
                    seatkey = 'silverseats_{}@{}'
                    selfseatkey = 'seatssilver_{}@{}_{}'
                    emptyseatnumlist = await redis_obj.hkeys('semptyseats_{}'.format(gameid))
                elif gametype ==2:
                    seatkey = 'tutorialseats_{}@{}'
                    selfseatkey = 'seatstutorial_{}@{}_{}'
                    emptyseatnumlist = await redis_obj.hkeys('temptyseats_{}'.format(gameid))


                while True:
                    if emptyseatnumlist is None:
                        emptyseatnum = None
                    elif len(emptyseatnumlist) == 0:
                        emptyseatnum = None
                    else:
                        emptyseatnum = random.choice(emptyseatnumlist)
                        emptyseatnumlist.remove(emptyseatnum)
                        if gametype == 0:
                            await redis_obj.hdel('gemptyseats_{}'.format(gameid), emptyseatnum)
                        elif gametype ==1:
                            await redis_obj.hdel('semptyseats_{}'.format(gameid), emptyseatnum)
                        elif gametype ==2:
                            await redis_obj.hdel('temptyseats_{}'.format(gameid), emptyseatnum)

                        emptyseatnum = int(emptyseatnum)


                    if emptyseatnum is not None:
                        # 找出那台機台佔位資訊
                        valuelist = await redis_obj.hmget(seatkey.format(gameid, emptyseatnum), ['memberid', 'status'])
                        reservememberid = pg_general.converttype(valuelist[0],int)
                        reservestatus = pg_general.converttype(valuelist[1],int)
                        if reservestatus == 0: # 空台
                            await redis_obj.hmset(seatkey.format(gameid, emptyseatnum),
                                                  {"memberid": memberid, "status": 1,"card": card,"avatar": avatar})
                            # 設定自己的 機台
                            await redis_obj.set_value(selfseatkey.format(gameid, emptyseatnum, memberid), '1',30)
                            joinseatstatus = {"isjoin": True, "seatnum": emptyseatnum}
                            break

                    else:   # 滿台
                        result = pg_general.Apiresult.success
                        resultdata = {
                            "result": 1,
                            "errdescription": "所有座位都已滿\n請稍後再試!!"
                        }
                        return result,resultdata

            if joinseatstatus.get('isjoin') == True:

                # 設定 dirty 座位
                dirtyseatnum = joinseatstatus.get('seatnum')
                if gametype == 0:
                    await redis_obj.hset('dirtyseat','g_{}_{}'.format(gameid,dirtyseatnum),1)
                elif gametype ==1:
                    await redis_obj.hset('dirtyseat', 's_{}_{}'.format(gameid, dirtyseatnum), 1)
                elif gametype ==2:
                    await redis_obj.hset('dirtyseat', 't_{}_{}'.format(gameid, dirtyseatnum), 1)

                # 執行 Sigin 作業
                # memberid = gseat or sseat_gameid_seatnum_nowcont

                if env_setting.SIGNINPS_FLAG == True:
                    data = ''
                    # call ps game server sign in
                    if gametype ==0:
                        seatname = 'gseat'
                        PREFIX = 'PG'
                    elif gametype ==1:
                        seatname = 'sseat'
                        PREFIX = 'PGS'
                    elif gametype ==2:
                        seatname = 'tseat'
                        PREFIX = 'PGB'

                    seatmemberid = '{}_{}_{}'.format(seatname,gameid,joinseatstatus.get('seatnum'))
                    seatlogintoken = '{}_{}_{}*****{}'.format(seatname,gameid,joinseatstatus.get('seatnum'),logintoken)
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'joingameseat signin ps seatmemberid:{0},seatlogintoken:{1}'.format(seatmemberid,seatlogintoken))

                    psgameserverresult = pg_general.Apiresult.psloginerror
                    psgameserverresult_silver = pg_general.Apiresult.psloginerror
                    # call ps signin for gold
                    url = env_setting.PS_API_SERVER_URL + 'host/signin/?prefix={0}&member_id={1}&password={2}'.format(PREFIX,seatmemberid,seatlogintoken)
                    errcount = 0
                    pg_general.writelog(pg_general.PG_LogerLevel.debug, 'joingameseat sign url:{0}'.format(url))

                    uidparam = {}
                    for _err in range(3):
                        try:
                            # call ps signin api
                            if env_setting.LOCAL_SERVER == False:

                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url, timeout=60) as response:
                                        if response.status == 200:
                                            data = await response.json()
                                            if int(data.get('status_code')) != 0:
                                                psgameserverresult = pg_general.Apiresult.connectdberror
                                                raise ValueError('can not sign in user gold')
                                            psgameserverresult = pg_general.Apiresult.success
                                            resultdata['gameserver'] = data.get("server_info").get("slot")
                                            hostid = data.get('host_id')
                                            resultdata['logintoken'] = seatlogintoken + '(*--)' + hostid
                                            uidparam['uid_g'] = data.get('uid')
                                            break
                                        else:
                                            data = await response.text()
                            else:
                                psgameserverresult = pg_general.Apiresult.success
                            await asyncio.sleep(0)
                        except ValueError as e:
                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                'joingameseats  signin ValueError:{0}'.format(e))
                            break
                        except Exception as e:
                            errcount += 1
                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                'joingameseats  signin except:{0},errcount:{1},data:{2}'.format(e,
                                                                                                                   errcount,
                                                                                                                   data))
                            await asyncio.sleep(0)
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'joingameseats signin  signin result:{0}, recv:{1}'.format(psgameserverresult,
                                                                                               data))
                # get seat data
                if gametype == 0: # gold
                    seatvaluedatalist = await redis_obj.hmget('goldseats_{}@{}'.format(gameid,joinseatstatus.get('seatnum')),["unopenturn","avgturn","his1turn","his2turn","his3turn","his1multi","his2multi","his3multi"])
                elif gametype ==1:           # silver
                    seatvaluedatalist = await redis_obj.hmget('silverseats_{}@{}'.format(gameid,joinseatstatus.get('seatnum')),["unopenturn","avgturn","his1turn","his2turn","his3turn","his1multi","his2multi","his3multi"])
                elif gametype ==2:          # tutorial
                    seatvaluedatalist = await redis_obj.hmget('tutorialseats_{}@{}'.format(gameid,joinseatstatus.get('seatnum')),["unopenturn","avgturn","his1turn","his2turn","his3turn","his1multi","his2multi","his3multi"])

                result = pg_general.Apiresult.success
                resultdata['result'] = 0
                resultdata['errdescription'] = ''
                resultdata['seatnum'] = joinseatstatus.get('seatnum')
                resultdata['hallid'] = gametype
                resultdata['gameid'] = gameid
                resultdata['unopenturn'] = pg_general.converttype(seatvaluedatalist[0],int)
                resultdata['avgturn'] = pg_general.converttype(seatvaluedatalist[1],int)
                resultdata['his1turn'] = pg_general.converttype(seatvaluedatalist[2],int)
                resultdata['his2turn'] = pg_general.converttype(seatvaluedatalist[3],int)
                resultdata['his3turn'] = pg_general.converttype(seatvaluedatalist[4],int)
                resultdata['his1multi'] = 0 if seatvaluedatalist[5] is None else pg_general.converttype(seatvaluedatalist[5],int)
                resultdata['his2multi'] = 0 if seatvaluedatalist[6] is None else pg_general.converttype(seatvaluedatalist[6],int)
                resultdata['his3multi'] = 0 if seatvaluedatalist[7] is None else pg_general.converttype(seatvaluedatalist[7],int)

                # write membergamelog
                nowutctime = pg_general.getutcnow()
                command = 'insert into membergamelog(memberid, gameid, joingametime, logintoken,gametype,seatnum) values("{0}", "{1}", "{2}", "{3}","{4}","{5}")'.format(
                    memberid, gameid, nowutctime, logintoken, gametype, joinseatstatus.get('seatnum'))
                updateresult, dataindex = await self.insertdbdata(logintoken,command)
                if updateresult == True:
                    resultdata['logdataindex'] = dataindex
            else:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 1,
                    "errdescription": '進入座位失敗\n請重新嘗試!!',
                    "seatnum": 0
                }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:joingameseat except:{0}'.format(e))

        return result,resultdata

    async def getnewdragontigerrank(self, redis_obj, logintoken, memberid, jsoncontent):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getnewdragontigerrank memberid:{0},logintoken:{1},jsoncontent:{2}'.format(memberid,logintoken,jsoncontent))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            gameid = jsoncontent.get('gameid')

            topwinrankdata = await redis_obj.get_json_value('topwinrankdictlive')
            topmultipilierrankdata = await redis_obj.get_json_value('topmultipilierdictlive')
            topweekwinrankdictlive = await redis_obj.get_json_value('topweekwinrankdictlive')
            topweekmultipilierdictlive = await redis_obj.get_json_value('topweekmultipilierdictlive')
            rankdescription = ''

            gametodaytopmultipilierrankinfo = topmultipilierrankdata.get(gameid)
            if gametodaytopmultipilierrankinfo is None:
                gametodaytopmultipilierrankinfo = []
            gametodaytopwinrankinfo = topwinrankdata.get(gameid)
            if gametodaytopwinrankinfo is None:
                gametodaytopwinrankinfo = []
            gameweektopmultipilierrankinfo = topweekmultipilierdictlive.get(gameid)
            if gameweektopmultipilierrankinfo is None:
                gameweektopmultipilierrankinfo = []
            gameweektopwinrankinfo = topweekwinrankdictlive.get(gameid)
            if gameweektopwinrankinfo is None:
                gameweektopwinrankinfo = []


            # get game setting
            command = 'select ranktype,rankdescription from game where gameid="{0}" '.format(gameid)
            datalen,data = await self.getdbdata('get rank description',command)
            if datalen != 1:
                raise Exception('get game desc data error')

            rankdescription = data.get('rankdescription')
            ranktype = data.get('ranktype')

            # get self data
            command = 'select avatar from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen !=1 :
                raise Exception('get member data error')

            memberavatar = data.get('avatar')

            # 計算今天結算還有多少秒
            localdatetime = pg_general.get_local_datetime()
            localdate = localdatetime.date()

            endtime = pg_general.strtodatetime(str(localdate) + ' 23:59:59.00')
            dailyresetcountdown = pg_general.converttype((endtime - localdatetime).total_seconds() + 1, int)

            # 計算這周結算還有多少秒
            enddate = localdate + timedelta(days=(6-((localdate.weekday()+1)%7)))
            endtime = pg_general.strtodatetime(str(enddate) + ' 23:59:59.00')
            weeklyresetcountdown = pg_general.converttype((endtime - localdatetime).total_seconds() + 1,int)


            # gametodaytopmultipilierrankinfo check self for selftodaytopmultipilierrankinfo
            selftodaytopmultipilierrankinfo = {"rank":-1,"amount": 0,"extraaward": 0}
            for item in gametodaytopmultipilierrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself": True})
                    selftodaytopmultipilierrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself":False})


            # gametodaytopwinrankinfo check self for selftodaytopwinrankinfo
            selftodaytopwinrankinfo = {"rank":-1,"amount": 0,"extraaward": 0}
            for item in gametodaytopwinrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself":True})
                    selftodaytopwinrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself":False})

            # gameweektopmultipilierrankinfo check self for selfweektopmultipilierrankinfo
            selfweektopmultipilierrankinfo = {"rank":-1,"amount": 0,"extraaward": 0}
            for item in gameweektopmultipilierrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself":True})
                    selfweektopmultipilierrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself":False})

            # gameweektopwinrankinfo check self for selfweektopwinrankinfo
            selfweektopwinrankinfo = {"rank":-1,"amount": 0,"extraaward": 0}
            for item in gameweektopwinrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself":True})
                    selfweektopwinrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself":False})





            resultdata = {
                "ranktype": ranktype,
                "selfavatar": memberavatar,
                "dailyresetcountdown": dailyresetcountdown,
                "weeklyresetcountdown": weeklyresetcountdown,
                "description": rankdescription,
                "selftodaytopmultipilierrankinfo": selftodaytopmultipilierrankinfo,
                "selftodaytopwinrankinfo": selftodaytopwinrankinfo,
                "selfweektopmultipilierrankinfo": selfweektopmultipilierrankinfo,
                "selfweektopwinrankinfo": selfweektopwinrankinfo,
                "gametodaytopmultipilierrankinfo": gametodaytopmultipilierrankinfo,
                "gametodaytopwinrankinfo": gametodaytopwinrankinfo,
                "gameweektopmultipilierrankinfo": gameweektopmultipilierrankinfo,
                "gameweektopwinrankinfo": gameweektopwinrankinfo


            }




            
            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getnewdragontigerrank except:{0}'.format(e))

        return result,resultdata

    async def getnewtotalrank(self,redis_obj,logintoken,memberid):
        """
            取得陣營排行榜
            從DB  camprankdetail 取得要找的陣營排行榜
            """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getnewtotalrank logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        # initial variables area
        clientdata = {}

        richestrankinfo = []
        jinsongrankinfo = []
        likerank = []
        selfrankdata = {}
        selfrichrank = -1

        selflikerank = -1
        selfjinsongrank = -1
        selfjinsongbonus = 0

        selftodayrank = -1          # 今日積分榜
        selftodayranksumwin = 0     # 今日積分榜贏分

        try:
            command = 'select member.avatar,member.nickname,member.level,member.credit,member.activenumber,card from member where memberid = "{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen < 0:
                result = pg_general.Apiresult.connectdberror
                raise ValueError
            elif datalen == 0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError

            selfavatar = pg_general.converttype(data.get('avatar'), str)
            selfnickname = pg_general.converttype(data.get('nickname'), str)
            selflevel = pg_general.converttype(data.get('level'), int)
            selfcredit = pg_general.converttype(data.get('credit'), int)
            selfactivenumber = data.get('activenumber')
            selfcard = data.get('card')
            selfsumwin = 0
            selflikeamount = 0
            # 富豪榜資料
            command = 'select * from richrank order by rank'
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen == -1:
                result = pg_general.Apiresult.connectdberror
                raise ValueError

            if datalen > 0:
                for item in data:
                    rankmemberid = pg_general.converttype(item.get("memberid"), int)
                    rank = pg_general.converttype(item.get("rank"), int)
                    avatar = pg_general.converttype(item.get("avatar"), str)
                    nickname = pg_general.converttype(item.get("nickname"), str)
                    level = pg_general.converttype(item.get("level"), int)
                    credit = pg_general.converttype(item.get("credit"), int)
                    activenumber = item.get('activenumber')
                    card = item.get('card')

                    if None not in [rankmemberid, rank, avatar, nickname, level, credit, activenumber, card]:
                        # 找出自己的 rank
                        if int(memberid) == rankmemberid:
                            selfrichrank = rank

                        temprichrankinfo = {
                            "rank": rank,
                            "avatar": avatar,
                            "nickname": nickname,
                            "level": level,
                            "credit": credit,
                            "memberid": rankmemberid,
                            "activenumber": activenumber,
                            "card": card
                        }
                        richestrankinfo.append(temprichrankinfo)

            # 金爽榜資料
            # from redis
            jinsongranklive = await redis_obj.get_json_value('jinsongranklive')

            # find self rank and bonus
            if jinsongranklive is not None:
                if len(jinsongranklive)> 0:
                    jinsongrankinfo = jinsongranklive.copy()
                    for item in jinsongranklive:
                        if item.get('memberid') == memberid:
                            selfjinsongrank = item.get('rank')
                            selfsumwin = item.get('sumwin')
                            selfjinsongbonus = item.get('bonus')
                            break
            else:
                jinsongranklive = []

            # 人氣榜資料
            command = 'select * from likerank'
            datalen, data = await self.getdbdata(logintoken, command, True)
            if datalen > 0:
                likerank = sorted(data, key=lambda k: (k['rank']), reverse=False)
                # find self like rank
                for item in likerank:
                    if item.get('memberid') == memberid:
                        selflikerank = item.get('rank')
                        selflikeamount = item.get('likeamount')
                        break

            # 積分榜資料 from redis gametotalrank
            gametotalranklist = await redis_obj.get_json_value('gametotalrank')
            if gametotalranklist is not None:
                if len(gametotalranklist) > 0:
                    for item in gametotalranklist:
                        if item.get('memberid') == memberid:
                            selftodayrank = item.get('rank')
                            selftodayranksumwin = item.get('sumwin')
                            break
            else:
                gametotalranklist = []

            # 計算金爽榜倒數時間
            localdate = pg_general.get_tw_datetime()
            if localdate.day >= 16:
                enddatetime = datetime(localdate.year,localdate.month,calendar.monthrange(localdate.year,localdate.month)[1],23,59,59)
            else:
                enddatetime = datetime(localdate.year,localdate.month,15,23,59,59)
            
            diffseconds = pg_general.converttype((enddatetime - localdate).total_seconds(),int)


            # 準備 selfrank

            selfrankdata['avatar'] = selfavatar
            selfrankdata['nickname'] = selfnickname
            selfrankdata['level'] = selflevel
            selfrankdata['richrank'] = selfrichrank
            selfrankdata['credit'] = selfcredit
            selfrankdata['memberid'] = memberid
            selfrankdata['activenumber'] = selfactivenumber
            selfrankdata['likerank'] = selflikerank
            selfrankdata['card'] = selfcard
            selfrankdata['sumwin'] = selfsumwin
            selfrankdata['likeamount'] = selflikeamount
            selfrankdata['jinsongrank'] = selfjinsongrank
            selfrankdata['jinsongrankbonus'] = selfjinsongbonus
            selfrankdata['gametodayrank'] = selftodayrank
            selfrankdata['gametodayranksumwin'] = selftodayranksumwin
            clientdata = {
                "jinsongrankcountdownsec" : diffseconds,
                "selfrankdata": selfrankdata,
                "richestrankinfo": richestrankinfo,
                "jinsongrankinfo": jinsongrankinfo,
                "likerankinfo": likerank,
                "gametodayrankinfo":  gametotalranklist

            }
            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getnewtotalrank except : {0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getnewtotalrank result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                            logintoken,
                                                                                                            clientdata))
            return result, clientdata
        


    async def psapi_logout(self,redis_obj,logintoken,seatinfo):     # just use in new mode
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:psapi_logout logintoken:{0},seatinfo:{1}'.format(logintoken, seatinfo))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # infolist = seatinfo.split('_')
            # gameid = infolist[1]
            # seatnum = pg_general.converttype(infolist[2],int)
            # nowcount = pg_general.converttype(infolist[3],int)
            #
            # # get memberid , card from redis
            # goldseatinfolist = await redis_obj.hmget('goldseats_{}@{}',["memberid","card"])
            # memberid = pg_general.converttype(goldseatinfolist[0],int)
            # card = pg_general.converttype(goldseatinfolist[1],int)







        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_logout except:{}'.format(e))

        return result,resultdata

    async def getseatsinfo(self,redis_obj,logintoken, memberid, gameid, type):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getseatsinfo memberid:{0},gameid:{1},type:{2}'.format(memberid, gameid,type))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # if type ==0: #gold
            #     seatkey = 'goldseats_{}@{}'.format(gameid)
            # else: # silver
            #     seatkey = 'silverseats_{}@{}'.format(gameid)
            #
            # allseatslist = await redis_obj.get_all_keys(seatkey)
            command = 'select seatsamount,seatsamount_s from game where gameid ="{0}"'.format(gameid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                return result,resultdata

            seatsamount = data.get('seatsamount')
            seatsamount_s = data.get('seatsamount_s')

            if type ==0: #gold
                seatkey = 'goldseats_{}@'.format(gameid)
                seatamount = seatsamount
            else: # silver
                seatkey = 'silverseats_{}@'.format(gameid)
                seatamount = seatsamount_s

            seatlist = []
            # get self selfreservenum selfreserveseconds
            selflist = []
            selfreservenum = 0
            selfreserveseconds = 0
            for temp_i in range(seatamount):
                valuelist = await redis_obj.hmget(seatkey+str(temp_i+1),['unopenturn','avgturn','his1turn','his2turn','his3turn','memberid','status','avatar','dateline','his1multi','his2multi','his3multi'])

                tempstatus = pg_general.converttype(valuelist[6], int)
                tempseatsvalue = {
                    "num": temp_i+1,
                    "unopenturn": pg_general.converttype(valuelist[0],int),
                    "avgturn": pg_general.converttype(valuelist[1],int),
                    "his1turn": pg_general.converttype(valuelist[2],int),
                    "his2turn": pg_general.converttype(valuelist[3],int),
                    "his3turn": pg_general.converttype(valuelist[4],int),
                    "his1multi": 0 if pg_general.converttype(valuelist[9],int) is None else pg_general.converttype(valuelist[9],int),
                    "his2multi": 0 if pg_general.converttype(valuelist[10],int) is None else pg_general.converttype(valuelist[10],int),
                    "his3multi": 0 if pg_general.converttype(valuelist[11],int) is None else pg_general.converttype(valuelist[11],int),
                    "status": 2 if tempstatus in [2,3] else tempstatus
                }

                if tempstatus == 1:
                    tempseatsvalue['avatar'] = valuelist[7]
                    tempseatsvalue['memberid'] = pg_general.converttype(valuelist[5],int)
                elif tempseatsvalue == 2:
                    tempseatsvalue['avatar'] = ''
                    tempseatsvalue['memberid'] = 0
                else:
                    tempseatsvalue['avatar'] = ''
                    tempseatsvalue['memberid'] = 0

                seatlist.append(tempseatsvalue)

                if memberid == pg_general.converttype(valuelist[5],int) and tempstatus in [2,3]:
                    selflist.append({"seatnum":temp_i+1,"dateline": pg_general.converttype(valuelist[8],str)})



            if len(selflist) > 0:  # 保留中
                nowutcdatetime = pg_general.getutcnow_datetime()
                tempdateline = pg_general.strtodatetime_nof(selflist[0].get('dateline'))

                selfreservenum = selflist[0].get('seatnum')
                selfreserveseconds = 0 if tempdateline <= nowutcdatetime else pg_general.converttype((tempdateline-nowutcdatetime).total_seconds(),int)
            else:
                selfreservenum = 0
                selfreserveseconds = 0


            if selfreserveseconds <0:
                selfreserveseconds = 0


            resultdata = {
                "selfreservenum": selfreservenum,
                "selfreserveseconds": selfreserveseconds,
                "seatlist": seatlist
            }


            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getseatsinfo except:{0}'.format(e))

        return result,resultdata



    async def web_getserverstatus(self):
        try:
            command = 'select * from webserversetting'
            datalen , data = await self.getdbdata('web_getserverstatus',command)

            resultdata = {
                "status": 0
            }
            if datalen == 1:
                resultdata = {
                    "status": data.get('serverstatus')
                }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:web_getserverstatus except:{0}'.format(e))

        return resultdata

    async def webapi_loginfb(self,fbavatarobj,fbid,fbtoken,user_region,user_region_sub,user_city,user_ip):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:webapi_loginfb fbid:{0},fbtoken:{1}'.format(fbid,fbtoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}



            command = 'select memberid,nickname,avatar,credit,card,level,activenumber,enable,silvercredit,point,membertype from member where fbid="{0}"'.format(fbid)
            datalen , data = await self.getdbdata('webapi_loginfb',command,False,True)

            if datalen <0:
                raise ValueError('can not find this user by fbid')

            if datalen ==0:
                result = pg_general.Apiresult.success
                clientdata = {
                    "statuscode": 1
                }
                return result , clientdata

            enable = data.get('enable')
            if enable !=1:
                clientdata = {
                    "statuscode": 2
                }
            else:

                # 確認 fb toekn is right
                memberid = data.get('memberid')

                fbuserresult, fbuserdata = await fbavatarobj.getfbdata('web fb login confirm', memberid, fbtoken)
                if fbuserresult != pg_general.Apiresult.success:
                    result = pg_general.Apiresult.success
                    clientdata = {
                        "statuscode": 3
                    }
                    return result, clientdata
                weblogintoken = pg_general.generatorsha256()


                logintime = pg_general.getutcnow_datetime()
                # save to member db
                command = 'update member set weblastlogintime = "{0}",weblastlogouttime=null,weblogintoken="{1}" where memberid ="{2}"'.format(logintime,weblogintoken,memberid)
                updateresult = await self.updatedbdata('update web logintime',command)

                # save to memberloginlog db
                command = 'insert into memberloginlog (memberid,logintime,platform,deviceid,ip,logintoken,region,city,region_sub,fbid,loginmethod,fbtoken) ' \
                          ' values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}")'
                command = command.format(memberid,logintime,"2","web",user_ip,weblogintoken,user_region,user_city,user_region_sub,fbid,"2",fbtoken)
                updateresult = await self.updatedbdata('insert into memberloginlog',command)

                clientdata = {
                    "statuscode": 0,
                    "memberid": data.get('memberid'),
                    "nickname": data.get('nickname'),
                    "avatar": data.get('avatar'),
                    "card": data.get('card'),
                    "level": data.get('level'),
                    "point": data.get('point'),
                    "credit": data.get('credit'),
                    "silvercredit": data.get('silvercredit'),
                    "activenumber": data.get('activenumber'),
                    "weblogintoken": weblogintoken,
                    "fbid": fbid,
                    "membertype": data.get('membertype')

                }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_loginfb ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_loginfb except:{0}'.format(e))
        return result,clientdata

    async def webapi_loginbytoken(self,fbid,weblogintoken,username):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:webapi_loginbytoken fbid:{0},username:{1},weblogintoken:{2}'.format(fbid,username,weblogintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            newweblogintoken = pg_general.generatorsha256()
            if fbid is not None: # use fb search
                # get this member by token and fbid
                command = 'select memberid,nickname,avatar,card,level,credit,activenumber,silvercredit,point,membertype from member where fbid="{0}"'.format(fbid)
                datalen, data = await self.getdbdata('get member by fbid',command)

                if datalen !=1:
                    result = pg_general.Apiresult.success
                    clientdata = {'statuscode': 1}
                    return result , clientdata

                memberid = data.get('memberid')

                clientdata = {
                    "statuscode": 0,
                    "memberid": data.get('memberid'),
                    "nickname": data.get('nickname'),
                    "avatar": data.get('avatar'),
                    "card": data.get('card'),
                    "point": data.get('point'),
                    "level": data.get('level'),
                    "credit": data.get('credit'),
                    "silvercredit": data.get('silvercredit'),
                    "activenumber": data.get('activenumber'),
                    "weblogintoken": newweblogintoken,
                    "fbid": fbid,
                    "username": None,
                    "membertype": data.get('membertype')

                }

                command = 'update member set weblogintoken="{0}" where memberid="{1}"'.format(newweblogintoken,memberid)
                resultrows = await self.updatedbdata('webapi_loginbytoken',command)

                result = pg_general.Apiresult.success
            else:               # use username search
                # get member by username & weblogintoken
                command = 'select memberid,nickname,avatar,card,level,credit,activenumber,silvercredit,point,membertype from member where username="{0}"'.format(username)
                datalen , data = await self.getdbdata('get member by username',command)
                if datalen !=1:
                    result = pg_general.Apiresult.success
                    clientdata = {'statuscode': 1}
                    return result , clientdata

                memberid = data.get('memberid')
                clientdata = {
                    "statuscode": 0,
                    "memberid": data.get('memberid'),
                    "nickname": data.get('nickname'),
                    "avatar": data.get('avatar'),
                    "card": data.get('card'),
                    "level": data.get('level'),
                    "point": data.get('point'),
                    "credit": data.get('credit'),
                    "silvercredit": data.get('silvercredit'),
                    "activenumber": data.get('activenumber'),
                    "weblogintoken": newweblogintoken,
                    "username": username,
                    "fbid": None,
                    "membertype": data.get('membertype')

                }
                command = 'update member set weblogintoken="{0}" where memberid="{1}"'.format(newweblogintoken,
                                                                                              memberid)
                resultrows = await self.updatedbdata('webapi_loginbytoken', command)


                result = pg_general.Apiresult.success
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_loginbytoken ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_loginbytoken except:{0}'.format(e))
        return result, clientdata



    async def webapi_loginusername(self,username,password,user_region,user_region_sub,user_city,user_ip):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:webapi_loginusername username:{0},password:{1}'.format(username,password))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            username = username.strip()
            password = password.strip()

            command = 'select memberid,nickname,avatar,credit,card,level,activenumber,enable,password,silvercredit,point,membertype from member where username="{0}"'.format(username)
            datalen , data = await self.getdbdata('webapi_loginusername',command,False,True)

            if datalen <0:
                raise ValueError('can not find this user by fbid')

            if datalen ==0:
                result = pg_general.Apiresult.success
                clientdata = {
                    "statuscode": 1   # 帳號或是密碼錯誤
                }
                return result , clientdata
            enable = data.get('enable')
            if enable !=1:
                clientdata = {
                    "statuscode": 2
                }
            else:
                userpassword = data.get('password')
                if password != userpassword:
                    result = pg_general.Apiresult.success
                    clientdata = {
                        "statuscode": 1  # 帳號或是密碼錯誤
                    }
                    return result, clientdata


                weblogintoken = pg_general.generatorsha256()
                memberid = data.get('memberid')

                logintime = pg_general.getutcnow_datetime()
                # save to member db
                command = 'update member set weblastlogintime = "{0}",weblastlogouttime=null,weblogintoken="{1}" where memberid ="{2}"'.format(logintime,weblogintoken,memberid)
                updateresult = await self.updatedbdata('update web logintime',command)

                # save to memberloginlog db
                command = 'insert into memberloginlog (memberid,logintime,platform,deviceid,ip,logintoken,region,city,region_sub,username,loginmethod) ' \
                          ' values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}")'
                command = command.format(memberid,logintime,"2","web",user_ip,weblogintoken,user_region,user_city,user_region_sub,username,"1")
                updateresult = await self.updatedbdata('insert into memberloginlog',command)


                clientdata = {
                    "statuscode": 0,
                    "memberid": data.get('memberid'),
                    "nickname": data.get('nickname'),
                    "avatar": data.get('avatar'),
                    "card": data.get('card'),
                    "point": data.get('point'),
                    "level": data.get('level'),
                    "credit": data.get('credit'),
                    "silvercredit": data.get('silvercredit'),
                    "activenumber": data.get('activenumber'),
                    "weblogintoken": weblogintoken,
                    "username": username,
                    "membertype": data.get('membertype')
                }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_loginusername ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_loginusername except:{0}'.format(e))
        return result,clientdata






    async def webapi_logout(self,fbid,weblogintoken,username):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:webapi_logout fbid:{0},weblogintoken:{1}'.format(fbid,weblogintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            logouttime = pg_general.getutcnow_datetime()
            if fbid is not None:
                command = 'update member set lastlogouttime="{0}" where fbid = "{1}" and weblogintoken ="{2}"'.format(logouttime,fbid,weblogintoken)
            else:       # username
                command = 'update member set lastlogouttime="{0}" where username = "{1}" and weblogintoken ="{2}"'.format(
                    logouttime, username, weblogintoken)

            updateresult = await self.updatedbdata('webapi_logout',command)

            clientdata={
                'statuscode':0
            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_logout ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_logout except:{0}'.format(e))
        return result,clientdata

    async def creditexchange(self,logintoken,memberid,type,amount):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:creditexchange logintoken:{0},memberid:{1},type:{2},amount:{3}'.format(logintoken,memberid,type,amount))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # get setting2 silvertogoldenable setting
            command = 'select silvertogoldenable from setting2'
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen !=1:
                raise ValueError('can not get silvertogold setting')

            silvertogoldenable = data.get('silvertogoldenable')



            # type 0: 金轉銀, 1: 銀轉金
            # 檢查 type=1 , amount 是否有大於 100,type ==0 , amount >0
            if type==1 and amount <100:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                raise ValueError('type error 1')
            elif type == 0 and amount <1:
                result = pg_general.Apiresult.parametererror
                raise ValueError('type error 2')

            if type == 0:
                command = 'update member set credit= credit -"{0}",silvercredit = silvercredit + "{1}" ' \
                          'where memberid = "{2}" and credit >= "{0}"'.format(amount,amount*100,memberid)
                updaterows = await self.updatedbdata_affectrows(logintoken, command)
                if updaterows ==0:
                    result = pg_general.Apiresult.success
                    clientdata = {
                        "result":1
                    }
                    return result , clientdata

                #write to transaction log
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.goldtosilver,
                    "amount": amount,
                    "otherdata": "goldtosilver"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken,param))

            elif type ==1 and silvertogoldenable ==1 :
                goldcredit = int(amount/100)
                silvercredit = goldcredit * 100
                command = 'update member set silvercredit=silvercredit-"{0}",credit=credit+"{1}" ' \
                          'where memberid= "{2}" and silvercredit>="{0}"'.format(silvercredit,goldcredit,memberid)
                updaterows = await self.updatedbdata_affectrows(logintoken, command)
                if updaterows == 0:
                    result = pg_general.Apiresult.success
                    clientdata = {
                        "result": 1
                    }
                    return result , clientdata

                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.silvertogold,
                    "amount": amount,
                    "otherdata": "silvertogold"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken,param))
            elif type ==1 and silvertogoldenable == 0:
                result = pg_general.Apiresult.othererror
                raise ValueError('silvertogold is 0')
            else:
                result = pg_general.Apiresult.parametererror
                raise ValueError('type error 3')
            # get final credit & silvercredit
            command = 'select credit , silvercredit from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken, command, False, True)
            if datalen ==1:
                clientdata = {
                    "result": 0,
                    "credit": data.get('credit'),
                    "silvercredit": data.get('silvercredit')
                }
                result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:creditexchange ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:creditexchange except:{0}'.format(e))
        return result,clientdata

    async def pointtocredit(self,logintoken, memberid,type,amount):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:pointtocredit logintoken:{0},memberid:{1},type:{2},amount:{3}'.format(logintoken,memberid,type,amount))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # 檢查資料
            if type==0 and amount <1:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return result , clientdata

            # type 0: 點數換金幣, 1: 查詢點數
            if type == 0:
                command = 'update member set point=point-"{0}",credit=credit+"{1}" where memberid = "{2}" and point >="{0}"'.format(amount,amount*100,memberid)
                updaterows = await self.updatedbdata_affectrows(logintoken,command)
                if updaterows ==1:
                    # get final point and credit
                    command = 'select credit,point from member where memberid ="{0}"'.format(memberid)
                    datalen , data = await self.getdbdata(logintoken,command,False,True)
                    clientdata = {
                        "result": 0,
                        "point": data.get('point'),
                        "credit": data.get('credit')
                    }

                    # write to transaction log
                    param = {
                        "frommemberid": memberid,
                        "tomemberid": memberid,
                        "type": pg_general.transactiontype.pointtocredit,
                        "amount": amount,
                        "otherdata": "pointtocredit"
                    }
                    asyncio.ensure_future(self.writetransactionlog(logintoken,param))

                else:
                    clientdata = {
                        "result":1
                    }

            elif type ==1:
                command = 'select point from member where memberid = "{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken,command,False,True)
                if datalen ==1:
                    clientdata = {
                        "result": 0,
                        "point": data.get('point')
                    }
            else:
                result = pg_general.Apiresult.parametererror
                raise ValueError('type error')

            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:pointtocredit ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:pointtocredit except:{0}'.format(e))
        return result,clientdata

    async def getfreeboxstatus(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:getfreeboxstatus logintoken:{0},memberid:{1}'.format(logintoken,memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # get cardinfo.freecoin , freecointimes
            command = 'select member.todayfreeboxgettimes,member.lastfreecoingettime,member.credit,member.safe,cardinfo.freecoin,cardinfo.freecointimes,silvercredit,setting2.freeboxcdseconds,setting2.freeboxmode from member,cardinfo,setting2 ' \
                      ' where member.memberid="{0}" and cardinfo.card = member.card'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)

            if datalen ==1 :
                nowdatetime = pg_general.getutcnow_datetime()
                todayfreeboxgettimes = data.get('todayfreeboxgettimes')
                lastfreecoingettime = data.get('lastfreecoingettime')
                freecoin = data.get('freecoin')
                freecointimes = data.get('freecointimes')
                freeboxcdseconds = data.get('freeboxcdseconds')
                credit = data.get('credit')
                safe = data.get('safe')
                silvercredit = data.get('silvercredit')
                if silvercredit is None:
                    silvercredit = 0
                freeboxmode = data.get('freeboxmode')
                timeleft = int(freeboxcdseconds - (nowdatetime - lastfreecoingettime).total_seconds())
                if timeleft < 0:
                    timeleft = 0
                # 檢查次數 or freecoin == 0
                if (credit+safe+silvercredit/100)>= 100 and freeboxmode ==1:     # freeboxmode ==1 代表帳戶餘額要小於 100
                    clientdata = {
                        "enable": 0,
                        "timeleft": timeleft,
                        "gettimes": todayfreeboxgettimes,
                        "totalamount": freecointimes

                    }
                elif freecoin ==0 or todayfreeboxgettimes >= freecointimes:
                    clientdata = {
                        "enable": 0,
                        "timeleft": timeleft,
                        "gettimes": todayfreeboxgettimes,
                        "totalamount": freecointimes
                    }
                else:
                    clientdata = {
                        "enable": 1,
                        "timeleft": timeleft,
                        "gettimes": todayfreeboxgettimes,
                        "totalamount": freecointimes
                    }


                result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getfreeboxstatus ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getfreeboxstatus except:{0}'.format(e))
        return result,clientdata

    async def receivefreebox(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:receivefreebox logintoken:{0},memberid:{1}'.format(logintoken,memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # get cardinfo.freecoin , freecointimes
            command = 'select member.todayfreeboxgettimes,member.lastfreecoingettime,member.credit,member.safe,cardinfo.freecoin,cardinfo.freecointimes,setting2.freeboxcdseconds,silvercredit,setting2.freeboxmode from member,cardinfo,setting2 ' \
                      '  where member.memberid="{0}" and cardinfo.card = member.card'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 1:
                nowdatetime = pg_general.getutcnow_datetime()
                todayfreeboxgettimes = data.get('todayfreeboxgettimes')
                lastfreecoingettime = data.get('lastfreecoingettime')
                freecoin = data.get('freecoin')
                freecointimes = data.get('freecointimes')
                freeboxcdseconds = data.get('freeboxcdseconds')
                timeleft = freeboxcdseconds - (nowdatetime - lastfreecoingettime).total_seconds()
                credit = data.get('credit')
                safe = data.get('safe')
                silvercredit = data.get('silvercredit')
                if silvercredit is None:
                    silvercredit = 0
                freeboxmode = data.get('freeboxmode')
                if timeleft < 0:
                    timeleft = 0

                # 檢查次數 or freecoin == 0 or timeleft >0
                if (credit+safe+silvercredit/100)>= 100 and freeboxmode ==1:
                    clientdata = {
                        "result": 1         # 領取失敗
                    }
                    result = pg_general.Apiresult.success
                elif freecoin == 0 or todayfreeboxgettimes >= freecointimes or timeleft >0:
                    clientdata = {
                        "result": 1         # 領取失敗
                    }
                    result = pg_general.Apiresult.success
                else:   # 領取成功
                    command = 'update member set todayfreeboxgettimes= todayfreeboxgettimes+1,lastfreecoingettime="{0}",credit=credit+"{1}" where ' \
                              'memberid="{2}"'.format(nowdatetime,freecoin,memberid)
                    updateresult = await self.updatedbdata(logintoken,command)

                    # write transaction log
                    param = {
                        "frommemberid": memberid,
                        "tomemberid": memberid,
                        "type": pg_general.transactiontype.freebox,
                        "amount": freecoin,
                        "amount_silver": 0,
                        "otherdata": 'freebox'
                    }
                    asyncio.ensure_future(self.writetransactionlog(logintoken, param))

                    # get after credit
                    command = 'select credit from member where memberid="{0}"'.format(memberid)
                    datalen , data = await self.getdbdata(logintoken,command,False,True)

                    if datalen == 1:
                        clientdata = {
                            "result": 0,
                            "aftercredit": data.get('credit'),
                            "getcredit": freecoin
                        }
                    result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:receivefreebox ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:receivefreebox except:{0}'.format(e))
        return result,clientdata

    async def forgetpasssms(self,logintoken,username,phone):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:forgetpasssms logintoken:{0},username:{1},phone:{2}'.format(logintoken,username,phone))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # 先確認資料正確性
            if None in [username,phone]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return result , clientdata

            phone = phone.strip()
            username = username.strip()

            if '09' != phone[:2] or phone.isdigit() ==False:
                result = pg_general.Apiresult.success
                clientdata = {'result': 2}
                return result , clientdata

            # find in db
            command = 'select memberid,phonevalidatetime from member where phonebindstatus=2 and phone ="{0}" and username="{1}"'.format(phone,username)
            datalen, data = await self.getdbdata(logintoken,command)

            if datalen !=1:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 1
                }
                return result , clientdata

            # 撈是否有超過一分鐘
            phonevalidatetime = data.get('phonevalidatetime')
            memberid = data.get('memberid')
            nowdatetime= pg_general.getutcnow_datetime()
            if (nowdatetime-phonevalidatetime).total_seconds() <60:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 4
                }
                return result, clientdata


            validatecode = random.randint(100000, 999999)
            # 發送 code to phone
            await pg_sms.sendsms(phone, validatecode)


            # 紀錄 db
            command = 'update member set phonevalidatecode="{0}",phonevalidatetime="{1}" where memberid = "{2}"'.format(
                validatecode, nowdatetime, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            # insert into phonevalidatelog
            command = 'insert into phonevalidatelog (logtime,phone,memberid,validatecode) values("{0}","{1}","{2}","{3}")'.format(
                nowdatetime, phone, memberid, validatecode)
            insertresult = await self.updatedbdata(logintoken, command)

            clientdata = {
                "result": 0
            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:forgetpasssms ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:forgetpasssms except:{0}'.format(e))
        return result,clientdata

    async def changenewpassword(self,logintoken,username,phone,validatecode,newpassword):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:changenewpassword logintoken:{0},username:{1},phone:{2}'.format(logintoken,username,phone))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # 先確認資料正確性
            if None in [username,phone,validatecode,newpassword]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return result , clientdata

            phone = phone.strip()
            username = username.strip()
            validatecode = validatecode.strip()
            newpassword = newpassword.strip()

            if '09' != phone[:2] or phone.isdigit() ==False:
                result = pg_general.Apiresult.success
                clientdata = {'result': 2}
                return result , clientdata

            # 檢查資料
            pattern = re.compile(r'[a-zA-Z0-9]+')
            password_result = pattern.match(newpassword)
            password_lenresult = len(newpassword) >= 6 and len(newpassword) <= 12

            if password_result == False or password_lenresult == False:
                result = pg_general.Apiresult.success
                clientdata = {'result': 5}
                return result , clientdata


            # find in db
            command = 'select memberid,phonevalidatetime,phonevalidatecode from member where phonebindstatus=2 and phone ="{0}" and username="{1}"'.format(phone,username)
            datalen, data = await self.getdbdata(logintoken,command)

            if datalen !=1:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 1
                }
                return result , clientdata

            phonevalidatecode = data.get('phonevalidatecode')

            nowdatetime = pg_general.getutcnow_datetime()
            phonevalidatetime = data.get('phonevalidatetime')
            if (nowdatetime-phonevalidatetime).total_seconds() >= 600:  # 驗證碼超過 10 分鐘
                result = pg_general.Apiresult.success
                clientdata = {'result': 4}
                return result , clientdata

            if phonevalidatecode != validatecode:           # 驗證碼錯誤
                result = pg_general.Apiresult.success
                clientdata = {'result':1}
                return result , clientdata

            memberid = data.get('memberid')

            # write to db new password
            command = 'update member set password ="{0}",phonevalidatetime="{2}" where memberid="{1}"'.format(newpassword,memberid,nowdatetime-timedelta(days=1))
            updateresult = await self.updatedbdata(logintoken,command)


            clientdata = {
                "result": 0
            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:changenewpassword ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:changenewpassword except:{0}'.format(e))
        return result,clientdata

    async def bindusername(self,logintoken,memberid,username,password):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:bindusername logintoken:{0},memberid:{1},username:{2},password:{3}'.format(logintoken,memberid,username,password))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            comfirmresult = await self.confirmregisterdata(logintoken,username,password)
            if  comfirmresult == False:
                clientdata={
                    "result": 1
                }
                result = pg_general.Apiresult.success
                return result,clientdata

            command = 'update member set username="{0}",password="{1}" where memberid="{2}"'.format(username,password,memberid)
            updateresultrows = await self.updatedbdata_affectrows(logintoken,command)

            if updateresultrows <=0 :
                clientdata = {
                    "result": 2
                }
                result = pg_general.Apiresult.success
                return result , clientdata


            clientdata = {
                "result":0
            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:bindusername ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:bindusername except:{0}'.format(e))
        return result,clientdata

    async def friendonlinestatus(self,logintoken,memberid,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:friendonlinestatus logintoken:{0},memberid:{1}'.format(logintoken,memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = []

            # get member friendlist
            command = 'select friendlist from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen ==1:
                friendlist = data.get('friendlist')
                if friendlist is not None:
                    friendlist = friendlist.strip()
                    if friendlist == '':
                        result = pg_general.Apiresult.success
                        return result,clientdata

            friendlist = friendlist.split(',')
            if len(friendlist) == 0:
                result = pg_general.Apiresult.success
                return result,clientdata

            newfriendlist = ['online_' +item for item in friendlist]

            friendonlinelist = await redis_obj.mget(newfriendlist)

            if len(friendlist) != len(friendonlinelist):
                raise ValueError('friendlist friendonlinelist is diff')


            for x,y in zip(friendlist,friendonlinelist):
                clientdata.append({
                    "memberid": int(x),
                    "online": 0 if y is None else 1
                })


            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:friendonlinestatus ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:friendonlinestatus except:{0}'.format(e))
        return result,clientdata

    async def updatemembermessage(self,logintoken,memberid,message):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:updatemembermessage logintoken:{0},memberid:{1},messae:{2}'.format(logintoken,memberid,message))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            if len(message)> 120:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result":1
                }
                return result,clientdata

            command = 'update member set message="{0}" where memberid = "{1}"'.format(message,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

            result = pg_general.Apiresult.success
            clientdata = {
                "result": 0
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatemembermessage ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatemembermessage except:{0}'.format(e))
        return result,clientdata


    async def reportmember(self,logintoken,memberid,tomemberid,content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:reportmember logintoken:{0},memberid:{1},tomemberid:{2},content:{3}'.format(logintoken,memberid,tomemberid,content))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # insert into db reportmember
            utcnowdatetime = pg_general.getutcnow_datetime()
            command = 'insert into reportmember(frommemberid,tomemberid,reportdatetime,content) values("{0}","{1}","{2}","{3}")'.format(memberid,tomemberid,utcnowdatetime,content)
            updateresult = await self.updatedbdata(logintoken,command)

            result = pg_general.Apiresult.success
            clientdata = {
                "result": 0
            }
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:reportmember ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:reportmember except:{0}'.format(e))
        return result,clientdata


    async def actionframe(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:actionframe logintoken:{0},memberid:{1}'.format(logintoken,memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # get nowutc time
            nowutcdattime = pg_general.getutcnow_datetime()

            command = 'select * from action where starttime <= "{0}" and (endtime>="{0}" or endtime is null) order by listtype,listpos,contentpos'.format(nowutcdattime)
            datalen , data = await self.getdbdata(logintoken,command,True)

            if datalen ==0:
                clientdata = {
                    "action":{},
                    "official":{}
                }
                result = pg_general.Apiresult.success
                return result , clientdata
            elif datalen >0:
                actionlist = [item for item in data if item.get('listtype')==0]
                officiallist = [item for item in data if item.get('listtype')==1]

                actiondict = {}
                officialdict = {}

                for item in actionlist:
                    listpos = item.get('listpos')

                    if actiondict.get(listpos) is None:
                        actiondict[listpos]={}
                        actiondict[listpos]['content'] = []
                    actiondict[listpos]['actionnumber'] = item.get('actionnumber')
                    actiondict[listpos]['buttonurl'] = item.get('buttonurl')
                    actiondict[listpos]['newflag'] = item.get('newflag')
                    tempstarttime = item.get('starttime')
                    tempstarttime = pg_general.get_utc_to_local_datetime(tempstarttime)
                    tempendtime = item.get('endtime')
                    if tempendtime == '0000-00-00 00:00:00':
                        actiondict[listpos]['duration'] = tempstarttime.__str__() + ' ~ 官方停止活動'
                    else:
                        tempendtime = pg_general.get_utc_to_local_datetime(tempendtime)
                        actiondict[listpos]['duration'] = tempstarttime.__str__() + ' ~ ' + tempendtime.__str__()

                    clickurl = item.get('clickurl')
                    if clickurl is not None:
                        clickurl = clickurl.strip()
                    if clickurl == '':
                        clickurl = None

                    actiondict[listpos]['content'].append({
                        "type": item.get('contenttype'),
                        "incontent": item.get('content'),
                        "size": item.get('size'),
                        "clickurl": clickurl
                    })

                action = []
                tempactionkeys = list(actiondict.keys())
                tempactionkeys.sort()
                if len(tempactionkeys)> 0:
                    for item in tempactionkeys:
                        action.append(actiondict[item])


                for item in officiallist:
                    listpos = item.get('listpos')
                    if officialdict.get(listpos) is None:
                        officialdict[listpos] = {}
                        officialdict[listpos]['content'] = []

                    officialdict[listpos]['content'].append({
                        "type": item.get('contenttype'),
                        "incontent": item.get('content'),
                        "size": item.get('size')
                    })

                official = []
                tempofficialkeys = list(officialdict.keys())
                tempofficialkeys.sort()
                if len(tempofficialkeys)>0:
                    for item in tempofficialkeys:
                        official.append(officialdict[item])

                result = pg_general.Apiresult.success
                clientdata = {
                    "action": action,
                    "official": official
                }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:actionframe ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:actionframe except:{0}'.format(e))
        return result,clientdata


    async def restoreIAP(self,logintoken, memberid,jsoncontent):
        result = pg_general.Apiresult.success
        clientdata = {"result": 0}

        return result , clientdata

    async def getselfrankgamesort(self,redis_obj,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getselfrankgamesort logintoken:{0}'.format(
                                    logintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {"selfrankgamelist": []}

            gametodayrank = await redis_obj.get_json_value('rank_gametodayrank')
            if gametodayrank is None:
                result = pg_general.Apiresult.success
                clientdata = {
                    "selfrankgamelist": []
                }
                return result,clientdata

            gametodayrank_new = [item for item in gametodayrank if item.get('memberid') == memberid]
            selfrankgamesort = []
            selfrankgamedict = {}
            for item in gametodayrank_new:
                ranktype = item.get('ranktype')
                rank = pg_general.converttype(item.get('rank'),int)
                if rank >5:
                    continue

                gameid = item.get('gameid')
                if selfrankgamedict.get(gameid) is None:
                    selfrankgamedict[gameid] = {"gameid": gameid}
                if ranktype ==0:
                    selfrankgamedict[gameid]["topmultiplierrank"] = rank
                elif ranktype ==1:
                    selfrankgamedict[gameid]["topwinrank"] = rank
                    
            if selfrankgamedict != {}:
                for item in selfrankgamedict.keys():
                    selfrankgamesort.append(selfrankgamedict.get(item))

            clientdata['selfrankgamelist'] = selfrankgamesort

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getselfrankgamesort except:{0}'.format(e))

        return result,clientdata

    async def getselfrankgamesortnew(self,redis_obj,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getselfrankgamesortnew logintoken:{0}'.format(
                                    logintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}


            topwinrankdictlive = await redis_obj.get_json_value('topwinrankdictlive')
            if topwinrankdictlive is None:
                topwinrankdictlive = {}
            topmultipilierdictlive = await redis_obj.get_json_value('topmultipilierdictlive')
            if topmultipilierdictlive is None:
                topmultipilierdictlive = {}

            selfrankgamelist = []
            selfrankgamedict = {}

            totalaward_g = 0
            totalaward_s = 0

            for tempgameid , tempvalue in topwinrankdictlive.items():
                for item in tempvalue:
                    if item.get('memberid') == memberid:
                        rank = item.get('rank')
                        ranktype = item.get('ranktype')
                        extraaward = item.get('extraaward')
                        if ranktype ==0 and extraaward >0:
                            totalaward_g += extraaward
                        elif ranktype ==1 and extraaward > 0:
                            totalaward_s += extraaward
                        if rank <=5:
                            if selfrankgamedict.get(tempgameid) is None:
                                selfrankgamedict[tempgameid] = {}
                            selfrankgamedict[tempgameid]['topwinrank'] = rank
                            break
            for tempgameid , tempvalue in topmultipilierdictlive.items():
                for item in tempvalue:
                    if item.get('memberid') == memberid:
                        rank = item.get('rank')
                        ranktype = item.get('ranktype')
                        extraaward = item.get('extraaward')
                        if ranktype ==0 and extraaward >0:
                            totalaward_g += extraaward
                        elif ranktype ==1 and extraaward > 0:
                            totalaward_s += extraaward
                        if rank <= 5:
                            if selfrankgamedict.get(tempgameid) is None:
                                selfrankgamedict[tempgameid] = {}
                            selfrankgamedict[tempgameid]['topmultiplierrank'] = rank
                            break

            for tempgameid , tempvalue in selfrankgamedict.items():
                tempdict ={"gameid":tempgameid}
                if tempvalue.get('topmultiplierrank') is not None:
                    tempdict.update({'topmultiplierrank': tempvalue.get('topmultiplierrank')})

                if tempvalue.get('topwinrank') is not None:
                    tempdict.update({'topwinrank': tempvalue.get('topwinrank')})

                selfrankgamelist.append(tempdict)

            clientdata['selfrankgamelist'] = selfrankgamelist
            clientdata['totalaward'] = {
                "award_g": totalaward_g,
                "award_s": totalaward_s
            }
            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getselfrankgamesortnew except:{0}'.format(e))

        return result, clientdata



    async def getavatarlist(self,logintoken,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getavatarlist logintoken:{0}'.format(
                                    logintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {"avatarlist": []}
            avatarlist = []
            # get fb avatar
            command = 'select isbindfb from member where memberid="{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen > 0:
                isbindfb = data.get('isbindfb')
                if isbindfb == 1:
                    avatarlist.append(pg_fbavatar.AVATAR_URL.format(memberid))


            command = 'select * from memberavatarlist order by avatarindex'
            datalen , data = await self.getdbdata(logintoken,command,True)
            if datalen > 0:
                for item in data:
                    avatarlist.append(item.get('avatarurl'))

                clientdata ={
                    "avatarlist": avatarlist
                }
            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getavatarlist except:{0}'.format(e))

        return result, clientdata


    async def setavatarfromlist(self,logintoken,memberid,avatarurl):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:setavatarfromlist logintoken:{0}'.format(
                                    logintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result": 1}

            # check url 正確性
            if "resource-avatar.playgems.net" not in avatarurl:
                result = pg_general.Apiresult.success
                clientdata = {"result":1 }
                return result , clientdata

            command = 'update member set avatar="{0}",isavatarchanged="1" where memberid = "{1}"'.format(avatarurl,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

            if updateresult == True:
                clientdata = {"result": 0}
            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:setavatarfromlist except:{0}'.format(e))

        return result, clientdata





    async def confirmregisterdata(self,logintoken,username,password):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:confirmregisterdata logintoken:{0},username:{1},password:{2}'.format(logintoken,username,password))
            result = False

            # 檢查資料
            pattern = re.compile(r'[a-zA-Z0-9]+')
            pattern2 = re.compile(r'[a-zA-Z]+')
            username_result = pattern.match(username)
            password_result = pattern.match(password)
            username_lenresult = len(username) >=6 and len(username) <=12
            password_lenresult = len(password) >=6 and len(password) <=12
            username_firstcharresult = pattern2.match(username[0])

            if username_result and password_result and username_lenresult and password_lenresult and username_firstcharresult:
                if username_result.group() == username and password_result.group() == password:
                    result = True

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:confirmregisterdata ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:confirmregisterdata except:{0}'.format(e))
        return result

    async def writegiftfreeze(self,logintoken,param):
        try:

            # 確認 setting2.giftfreezeenable = 1
            command = 'select giftfreezeenable from setting2 where giftfreezeenable = 1'
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen != 1:
                return


            memberid = param.get('memberid')
            type = param.get('type')
            amount = param.get('amount')

            starttime = pg_general.getutcnow_datetime()
            starttime_str = pg_general.datetimetostr_nof(starttime)
            endtime = starttime + timedelta(days=7)
            endtime_str = pg_general.datetimetostr_nof(endtime)

            command = 'insert into giftfreeze (memberid,starttime,endtime,type,amount) values ("{0}","{1}","{2}","{3}","{4}")'.format(memberid,starttime_str,endtime_str,type,amount)
            insertresult = await self.insertdbdata(logintoken,command)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writegiftfreeze except:{0}'.format(e))

    async def getgiftfreezedata(self,logintoken,memberid):
        try:
            nowutcdatetime = pg_general.getutcnow_datetime()
            giftfreezedata = {"freezetotalamount":0,"freezelist":[]}
            sumamount = 0
            templist = []

            command = 'select memberid,amount,endtime,type from giftfreeze where memberid = "{0}" and "{1}" between starttime and endtime order by endtime'.format(memberid,nowutcdatetime)
            datalen , data = await self.getdbdata(logintoken,command,True)

            if datalen > 0 :
                for idx,item in enumerate(data):
                    tempamount = item.get('amount')
                    sumamount += tempamount
                    temptypeint = item.get('type')
                    if temptypeint == 0:
                        temptype = 'Apple內購'
                    elif temptypeint == 1:
                        temptype = 'Google內購'
                    elif temptypeint == 2:
                        temptype = '官網信用卡'
                    elif temptypeint == 3:
                        temptype = '官網Gash點卡'
                    elif temptypeint == 4:
                        temptype = '官網Gash錢包'
                    else:
                        temptype = '其他'

                    tempendtime = (item.get('endtime')+timedelta(hours=8)).__str__()
                    templist.append({
                        "num": idx+1,
                        "buytype": temptype,
                        "freezeamount": tempamount,
                        "unlocktime": tempendtime
                    })
                giftfreezedata = {
                    "freezetotalamount": sumamount,
                    "freezelist": templist
                }



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgiftfreezeamount except:{0}'.format(e))
        return giftfreezedata

    async def writetransactionlog(self,logintoken,param):
        # db.transaction
        # type : 參考 pg_general.transactiontype
        try:
            transtime= pg_general.getutcnow_datetime()
            frommemberid = param.get('frommemberid')
            tomemberid = param.get('tomemberid')
            type = param.get('type')
            amount = param.get('amount')
            amount_silver = param.get('amount_silver')
            otherdata = param.get('otherdata')

            if amount is None:
                amount = 0
            if amount_silver is None:
                amount_silver = 0


            command = 'insert into transaction (transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata) values ' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata)

            updateresult = await self.updatedbdata(logintoken,command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writetransactionlog except:{0}'.format(e))


    async def webapi_getgashwalletitem(self):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            command = 'select gashwalletflag from webserversetting'
            datalen, data = await self.getdbdata('get gashwalletflag',command)
            if datalen ==1:
                gashwalletflag = data.get('gashwalletflag')
                if gashwalletflag ==0:
                    result = pg_general.Apiresult.success
                    clientdata = {"status_code": 2}         # gash wallet 維護中
                    return result, clientdata


            command = 'select * from gashwalletinfo order by itemcode'
            datalen , data = await self.getdbdata('webapi_getgashwalletitem',command,True)

            if datalen > 0 :
                clientdata = {
                    "status_code": 0,
                    "data":data.copy()
                }
                result = pg_general.Apiresult.success


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_getgashwalletitem except:{0}'.format(e))

        return result , clientdata

    async def webapi_getgashpointitem(self):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}



            command = 'select gashpointflag from webserversetting'
            datalen, data = await self.getdbdata('get webserver gashflag',command,False)

            if datalen ==1:
                gashpointflag = data.get('gashpointflag')
                if gashpointflag ==0:
                    result = pg_general.Apiresult.success
                    clientdata={"status_code": 2}    # 維護中
                    return result,clientdata

            command = 'select * from gashpointinfo order by itemcode'
            datalen, data = await self.getdbdata('webapi_getgashpointitem', command, True)

            if datalen > 0 :
                clientdata = {
                    "status_code": 0,
                    "data":data.copy()
                }
                result = pg_general.Apiresult.success


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_getgashpointitem except:{0}'.format(e))

        return result , clientdata

    # 3-1-get 取得mycardinfo資料庫的預設值
    async def get_mycardinfo(self):
        try:
            # 取得資料庫內容
            command = 'select * from mycardinfo'
            datalen, data = await self.getdbdata("get_mycardinfo", command, fetchall=False)
            return data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "pg_asqldb: get_mycardinfo in 3-1 except:{0}".format(e))
            return None

    # 3-1-insert 驗證MyCard授權參數，並將結果回傳給廠商 → 廠商將結果新增至資料庫
    async def mycard_gashpoints(self, inter_3_1, returnMsg):
        try:
            # 目前在3-1流程
            statusapi = 31
            # 前端輸入參數，新增資料庫用小寫
            facserviceid = inter_3_1["FacServiceId"]
            factradeseq = inter_3_1["FacTradeSeq"]
            tradetype = inter_3_1["TradeType"]
            serverid = inter_3_1["ServerId"]
            customerid = inter_3_1["CustomerId"]
            paymenttype = inter_3_1["PaymentType"]
            itemcode = inter_3_1["ItemCode"]
            productname = inter_3_1["ProductName"]
            amount = inter_3_1["Amount"]
            currency = inter_3_1["Currency"]
            sandboxmode = inter_3_1["SandBoxMode"]
            facreturnurl = inter_3_1["FacReturnURL"]
            hash = inter_3_1["Hash"]
            # 智冠MyCard回傳參數，回傳變數是大寫
            returncode = returnMsg.get("ReturnCode", "")  # 授權結果代碼
            returnmsg = returnMsg.get("ReturnMsg", "")  # ReturnCode的訊息描述
            authcode = returnMsg.get("AuthCode", "")  # 交易授權碼
            tradeseq = returnMsg.get("TradeSeq", "")  # MyCard交易序號
            ingamesavetype = returnMsg.get("InGameSaveType", "")  # 儲值服務的使用者介面，使用2；web-site
            insertutcnowdate = pg_general.getutcnow()  # 目前英國格林威治時間

            command = 'insert into mycardhistory(statusapi, facserviceid, factradeseq, tradetype, serverid, customerid, paymenttype, itemcode, productname, amount, currency, sandboxmode, facreturnurl, hash, returncode, returnmsg, authcode, tradeseq, ingamesavetype, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}","{13}","{14}","{15}","{16}","{17}","{18}","{19}")'.format(statusapi, facserviceid, factradeseq, tradetype, serverid, customerid, paymenttype, itemcode, productname, amount, currency, sandboxmode, facreturnurl, hash, returncode, returnmsg, authcode, tradeseq, ingamesavetype, insertutcnowdate)
            await self.insertdbdata('mycard_gashpoints', command)
            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: insertmycardhistory failed in 3-1 except:{0}'.format(e))
            return False

    # 3-2-4 確認交易並回傳交易結果給廠商 → 廠商接收回傳交易結果 → 廠商將結果新增至資料庫
    async def mycard_mcresult(self, Json3_4_2):
        try:
            # 智冠MyCard回傳參數
            ReturnCode = Json3_4_2["ReturnCode"]  # 授權結果代碼
            ReturnMsg = Json3_4_2["ReturnMsg"]  # ReturnCode的訊息描述
            PayResult = Json3_4_2["PayResult"]  # 交易結果代碼
            FacTradeSeq = Json3_4_2["FacTradeSeq"]  # 廠商交易序號
            PaymentType = Json3_4_2["PaymentType"]  # 付費方式
            Amount = Json3_4_2["Amount"]  # 金額
            Currency = Json3_4_2["Currency"]  # 幣別

            MyCardTradeNo = Json3_4_2["MyCardTradeNo"]  # 卡片號碼，或會員扣點交易序號，端看PaymentType而定
            # PaymentType = INGAME時，傳MyCard卡片號碼
            # PaymentType = COSTPOINT時，傳會員扣點交易序號，格式為MMS開頭+數字
            # 其餘PaymentType為Billing小額付款交易，傳Billing交易序號

            MyCardType = Json3_4_2["MyCardType"]  # 通路代碼，PaymentType = INGAME時才有值
            PromoCode = Json3_4_2["PromoCode"]  # 活動代碼
            Hash = Json3_4_2["Hash"]
            insertutcnowdate = pg_general.getutcnow()  # 目前英國格林威治時間

            # 在3-2流程新增資料庫
            statusapi = 32
            command = 'insert into mycardhistory(statusapi, returncode, returnmsg, payresult, factradeSeq, paymenttype, amount, currency, mycardtradeno, mycardtype, promocode, hash, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}")'.format(statusapi, ReturnCode, ReturnMsg, PayResult, FacTradeSeq, PaymentType, Amount, Currency, MyCardTradeNo, MyCardType, PromoCode, Hash, insertutcnowdate)
            await self.insertdbdata('mycard_mcresult', command)

            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: insert mycardhistory failed in 3-2-4 except:{0}'.format(e))
            return False

    # 3-3 從資料表取得請求智冠必要的AuthCode與SandBoxMode與Amount與CustomerId
    async def get_mycardhistory_AuthCode_SandBoxMode(self, FacTradeSeq):
        try:
            # 取得資料庫內容fetchall=False，只抓第1筆3-1流程的就好
            statusapi = 31
            command = 'select authcode, sandboxmode, amount, customerid, tradeseq, mycardtradeno, factradeseq, currency, paymenttype from mycardhistory where factradeseq="{0}" and statusapi="{1}"'.format(FacTradeSeq, statusapi)
            datalen, data = await self.getdbdata("get_mycardhistory_AuthCode_SandBoxMode", command, fetchall=False)
            return data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:get AuthCode and SandBoxMode in 3-3 except:{0}'.format(e))
            return None

    # 3-3 廠商查詢交易結果 → 智冠回傳交易結果 → 廠商將結果新增至資料庫
    async def mycard_checkMyCardTradeResult(self, AuthCode, returnMsg):
        try:
            # 新增3-3資料庫
            statusapi = 33
            # 廠商輸入參數
            AuthCode = AuthCode  # 交易授權碼
            # 智冠MyCard回傳參數
            ReturnCode = returnMsg.get("ReturnCode", "")  # 授權結果代碼
            ReturnMsg = returnMsg.get("ReturnMsg", "")  # ReturnCode的訊息描述
            PayResult = returnMsg.get("PayResult", "")  # 交易結果代碼
            FacTradeSeq = returnMsg.get("FacTradeSeq", "")  # 廠商交易序號
            PaymentType = returnMsg.get("PaymentType", "")  # 付費方式，是INGAME
            Amount = returnMsg.get("Amount", "")  # 金額
            Currency = returnMsg.get("Currency", "")  # 幣別
            MyCardTradeNo = returnMsg.get("MyCardTradeNo", "")  # 卡片號碼，或會員扣點交易序號，端看PaymentType而定
            # PaymentType = INGAME時，傳MyCard卡片號碼
            # PaymentType = COSTPOINT時，傳會員扣點交易序號，格式為MMS開頭+數字
            # 其餘PaymentType為Billing小額付款交易，傳Billing交易序號

            MyCardType = returnMsg.get("MyCardType", "")  # 通路代碼
            PromoCode = returnMsg.get("PromoCode", "")  # 活動代碼
            SerialId = returnMsg.get("SerialId", "")  # 連續扣款序號
            insertutcnowdate = pg_general.getutcnow()  # 目前英國格林威治時間

            command = 'insert into mycardhistory(statusapi, authcode, returncode, returnmsg, payresult, factradeseq, paymenttype, amount, currency, mycardtradeno, mycardtype, promocode, serialid, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}","{13}")'.format(statusapi, AuthCode, ReturnCode, ReturnMsg, PayResult, FacTradeSeq, PaymentType, Amount, Currency, MyCardTradeNo, MyCardType, PromoCode, SerialId, insertutcnowdate)
            await self.insertdbdata('mycard_checkMyCardTradeResult', command)
            return True, MyCardTradeNo

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: insert mycardhistory failed in 3-3 except:{0}'.format(e))
            return False

    # 3-4 廠商做入點，確認MyCard交易 → 智冠請款 → 智冠回傳請款結果 → 廠商將結果新增至資料庫
    async def mycard_mycardReturnInvoiceResult(self, AuthCode, returnMsg):
        try:
            # 目前在3-4流程
            statusapi = 34
            # 廠商輸入參數
            AuthCode = AuthCode  # 交易授權碼
            # 智冠MyCard回傳參數
            ReturnCode = returnMsg.get("ReturnCode", "")  # 授權結果代碼
            ReturnMsg = returnMsg.get("ReturnMsg", "")  # ReturnCode的訊息描述
            FacTradeSeq = returnMsg.get("FacTradeSeq", "")  # 廠商交易序號
            TradeSeq = returnMsg.get("TradeSeq", "")  # MyCard交易序號
            SerialId = returnMsg.get("SerialId", "")  # 連續扣款序號
            insertutcnowdate = pg_general.getutcnow()  # 目前英國格林威治時間

            command = 'insert into mycardhistory(statusapi, authcode, returncode, returnmsg, factradeseq, tradeseq, serialid, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}")'.format(statusapi, AuthCode, ReturnCode, ReturnMsg, FacTradeSeq, TradeSeq, SerialId, insertutcnowdate)
            await self.insertdbdata('mycard_mycardReturnInvoiceResult', command)
            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: insert mycardhistory failed in 3-4 except:{0}'.format(e))
            return False

    # 結束3-4後，update member acc 發送點數給玩家 = 更新點數至資料庫
    async def mycard_update_member_point(self, Amount, CustomerId, TradeSeq, MyCardTradeNo, FacTradeSeq, Currency, PaymentType, redis_obj, cardinfo):
        try:
            # 由智冠面額取得金爽點數
            # 取得mycardmapping，智冠點數 → 金爽點數
            command = 'select * from mycardpointmapping where mycardpoint="{0}"'.format(Amount)
            datalen, jinsongpoint = await self.getdbdata('get mycardpointmapping', command, fetchall=False)

            # write transaction log
            param = {
                "frommemberid": CustomerId,
                "tomemberid": CustomerId,
                "type": pg_general.transactiontype.gashpoint,
                "amount": jinsongpoint["jinsongpoint"],
                "otherdata": {"MyCardTradeNo": MyCardTradeNo, "FacTradeSeq": FacTradeSeq}
            }
            asyncio.ensure_future(self.writetransactionlog('web gash point buy point', param))

            # 將金爽點數充值到member
            jinsong_point = jinsongpoint["jinsongpoint"]
            command = 'update member set point=point+"{0}" where memberid="{1}"'.format(jinsong_point, CustomerId)
            await self.updatedbdata('update member point', command)

            # update member card when card <2
            command = 'update member set card=2 where memberid="{0}" and card<2'.format(CustomerId)
            await self.updatedbdata('update member level', command)

            # get member info
            card = None
            command = 'select card from member where memberid="{0}"'.format(CustomerId)
            datalen, data = await self.getdbdata('get member card', command, False, True)
            if datalen == 1:
                card = data.get('card')

            # update redis cardbuy_{}
            twnowdate = pg_general.get_tw_datetime().date()
            firstdate = pg_general.get_tw_2020_first_date().date()
            datekey = str((twnowdate - firstdate).days % 60)
            result = await redis_obj.hincrby('cardbuy_{}'.format(CustomerId), datekey, Amount)

            # make level up future
            if card in [0, 1, 2, 3, 4]:
                logintoken = await redis_obj.get_value('{}'.format(CustomerId))
                apporweb = 1  # 0: app, 1: web
                asyncio.ensure_future(self.buycardlevelup_future(apporweb, logintoken, CustomerId, card, redis_obj, cardinfo))

            # 新增請款成功交易資料至3-7階段
            statusapi = 37
            insertutcnowdate = pg_general.getutcnow()  # 目前英國格林威治時間
            command = 'insert into mycardhistory(statusapi, paymenttype, tradeseq, mycardtradeno, factradeseq, customerid, amount, jinsongpoints, currency, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}")'.format(statusapi, PaymentType, TradeSeq, MyCardTradeNo, FacTradeSeq, CustomerId, Amount, jinsong_point, Currency, insertutcnowdate)
            await self.insertdbdata('mycard_mcresultcheck', command)

            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: update member points failed in mycard_status point except:{0}'.format(e))
            return False

    # 3-6 補儲值 → 新增智冠補儲值輸入值至資料庫
    async def mycard_mcredeposit(self, Json3_6):
        try:
            # 目前在3-6流程
            statusapi = 36
            # 智冠MyCard回傳參數
            ReturnCode = Json3_6["ReturnCode"]  # 授權結果代碼
            ReturnMsg = Json3_6["ReturnMsg"]  # ReturnCode的訊息描述
            FacServiceId = Json3_6["FacServiceId"]  # 廠商服務代碼
            FacTradeSeq = Json3_6["FacTradeSeq"]  # 廠商交易序號
            insertutcnowdate = pg_general.getutcnow()  # 目前英國格林威治時間

            command = 'insert into mycardhistory(statusapi, returncode, returnmsg, facserviceid, factradeseq, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}")'.format(statusapi, ReturnCode, ReturnMsg, FacServiceId, FacTradeSeq, insertutcnowdate)
            await self.insertdbdata('mycard_mcredeposit', command)
            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: insert mycardhistory failed in 3-6 except:{0}'.format(e))
            return False

    # 3-7-single-get 廠商從資料庫取得單筆交易查詢的時間區間 → 回傳供智冠MyCard查詢
    async def mycard_mcresultcheck_single_get(self, trade_number):
        try:
            # 用卡片號碼查詢
            MyCardTradeNo = trade_number.get("MyCardTradeNo")

            # 取得3-7資料庫內容
            statusapi = 37
            command = 'select * from mycardhistory where mycardtradeno="{0}" and statusapi="{1}"'.format(MyCardTradeNo, statusapi)
            part_3_7_datalen, part_3_7_data = await self.getdbdata("mycard_mcresultcheck_single_get", command, fetchall=False)

            return part_3_7_data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: get single data in 3-7 except:{0}'.format(e))
            return None

    # 3-7-multi-get 廠商從資料庫取得多筆交易查詢的時間區間 → 回傳供智冠MyCard查詢
    async def mycard_mcresultcheck_multi_get(self, datetime_range):
        try:
            # 用起始時間至結束時間查詢
            StartDateTime = datetime_range.get("StartDateTime")
            EndDateTime = datetime_range.get("EndDateTime")

            # 取得3-7資料庫內容
            statusapi = 37
            command = 'select * from mycardhistory where statusapi="{0}" and insertutcnowdate between "{1}" and "{2}"'.format(statusapi, StartDateTime, EndDateTime)
            part_3_7_datalen, part_3_7_data = await self.getdbdata("mycard_mcresultcheck_multi_get", command, fetchall=True)

            return part_3_7_data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: get multi data in 3-7 except:{0}'.format(e))
            return None

    async def webapi_get_gash_wallet_base64(self,memberid,itemid,amount):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 比對 itemid and amount 是否符合
            command = 'select * from gashwalletinfo where itemcode="{0}"'.format(itemid)
            datalen , data = await self.getdbdata("webapi_get_gash_wallet_base64",command)
            if datalen !=1:
                return result,clientdata

            cashamount = data.get('cashamount')
            if amount != cashamount:
                return result,clientdata

            utcnowdate = pg_general.getutcnow_datetime()
            command = 'insert into gashwalletdeposite(type,memberid,amount,starttime,status,itemcode)values("0","{0}","{1}","{2}","{3}","{4}")'.format(memberid,amount,utcnowdate,'0',itemid)

            insertresult,index = await self.insertdbdata('webapi_get_gash_wallet_base64',command)
            if insertresult == True:
                transid = index
                gash_base64 = Gash.Make_Wallet_SendOder(memberid,transid,amount)
                command = 'update gashwalletdeposite set base64="{0}" where transid="{1}"'.format(gash_base64,transid)
                updateresult = await self.updatedbdata('webapi_get_gash_wallet_base64',command)

                clientdata = {
                    "status_code": 0,
                    "base64": gash_base64,
                    "redirecturl": Gash.GASH_ORDER_URL
                }
                result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_get_gash_wallet_base64 except:{0}'.format(e))

        return result , clientdata

    async def webapi_get_gash_point_base64(self,memberid,itemid,amount):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 比對 itemid and amount 是否符合
            command = 'select * from gashpointinfo where itemcode="{0}"'.format(itemid)
            datalen , data = await self.getdbdata("webapi_get_gash_point_base64",command)
            if datalen !=1:
                return result,clientdata

            cashamount = data.get('cashamount')
            if amount != cashamount:
                return result,clientdata

            utcnowdate = pg_general.getutcnow_datetime()
            command = 'insert into gashwalletdeposite(type,memberid,amount,starttime,status,itemcode)values("1","{0}","{1}","{2}","{3}","{4}")'.format(memberid,amount,utcnowdate,'0',itemid)

            insertresult,index = await self.insertdbdata('webapi_get_gash_point_base64',command)
            if insertresult == True:
                transid = index
                gash_base64 = Gash.Make_Point_SendOder(memberid,transid,amount)
                command = 'update gashwalletdeposite set base64="{0}" where transid="{1}"'.format(gash_base64,transid)
                updateresult = await self.updatedbdata('webapi_get_gash_wallet_base64',command)

                clientdata = {
                    "status_code": 0,
                    "base64": gash_base64,
                    "redirecturl": Gash.GASH_ORDER_URL
                }
                result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_get_gash_point_base64 except:{0}'.format(e))

        return result , clientdata

    async def webapi_ret_gash_wallet_base64(self,base64,redis_obj,cardinfo):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 解開 base64 data
            xmldict = Gash.decode_b64xml(base64)
            if xmldict is None:
                return result , clientdata

            trans = xmldict.get('TRANS')

            memberid = pg_general.converttype(trans.get('USER_ACCTID'),int)
            transid = pg_general.converttype(trans.get('COID'),int)
            pay_rcode = trans.get('PAY_RCODE')
            pay_status = pg_general.converttype(trans.get('PAY_STATUS'),str)
            amount = pg_general.converttype(trans.get('AMOUNT'),int)
            ip = trans.get('USER_IP')
            # 先 update 那筆單
            utcnowdatetime = pg_general.getutcnow_datetime()
            command = 'update gashwalletdeposite set pay_rcode="{0}",pay_status="{6}",return_base64="{1}",ip="{2}",status="1",endtime="{5}" where status="0" ' \
                      'and memberid = "{3}" and transid="{4}"'.format(pay_rcode,base64,ip,memberid,transid,utcnowdatetime,pay_status)
            updaterows = await self.updatedbdata_affectrows('update gash wallet return data',command)

            if updaterows ==1 and pay_rcode =='0000' and pay_status=='S':     # 交易成功
                command= 'select gashwalletinfo.*, gashwalletdeposite.itemcode as itemid, gashwalletdeposite.amount as buyamount from gashwalletdeposite,gashwalletinfo ' \
                         'where  gashwalletinfo.itemcode=gashwalletdeposite.itemcode and gashwalletdeposite.transid = "{0}"'.format(transid)

                datalen , data = await self.getdbdata('get gashwalletinfo',command,False,True)
                if datalen == 1:
                    itemcode = data.get('itemcode')
                    cashamount = data.get('cashamount')
                    buyamount = data.get('buyamount')
                    pointamount = data.get('pointamount')

                    if cashamount == buyamount == amount:
                        # write transaction log
                        param = {
                            "frommemberid": memberid,
                            "tomemberid": memberid,
                            "type": pg_general.transactiontype.gashwallet,
                            "amount": pointamount,
                            "otherdata": {"type": "gashwallet","transid": transid}
                        }
                        asyncio.ensure_future(self.writetransactionlog('web gash wallet buy point', param))

                        # 寫入凍結額度
                        param = {
                            "memberid": memberid,
                            "type": 4,          # gash wallet
                            "amount": pointamount * 100  # 轉成金幣
                        }
                        # asyncio.ensure_future(self.writegiftfreeze('gash wallet deposite', param))

                        # update member acc
                        command = 'update member set point=point+"{0}" where memberid="{1}"'.format(pointamount,memberid)
                        updateresult = await self.updatedbdata('update member point',command)

                        # update mmeber card when card <2
                        command = 'update member set card=2 where memberid="{0}" and card<2'.format(memberid)
                        updateresult = await self.updatedbdata('update member level',command)

                        # get member info
                        card = None
                        command = 'select card from member where memberid="{0}"'.format(memberid)
                        datalen , data = await self.getdbdata('get member card',command,False,True)
                        if datalen ==1:
                            card = data.get('card')

                        # update redis cardbuy_{}
                        twnowdate = pg_general.get_tw_datetime().date()
                        firstdate = pg_general.get_tw_2020_first_date().date()
                        datekey = str((twnowdate - firstdate).days % 60)

                        result = await redis_obj.hincrby('cardbuy_{}'.format(memberid), datekey, amount)

                        # make level up future
                        if card in [0, 1, 2, 3, 4]:
                            logintoken = await redis_obj.get_value('{}'.format(memberid))
                            apporweb = 1 # 0: app, 1: web
                            asyncio.ensure_future(self.buycardlevelup_future(apporweb,logintoken, memberid, card, redis_obj, cardinfo))

                        clientdata = {
                            "status_code": 0,
                            "showstr": "儲值成功,感謝您使用 Gash錢包購買遊戲點數,您購買的點數 {} 點, 已經存入您 APP 遊戲帳戶,請至 App 將點數轉換成金幣或銀幣進行遊戲 !!".format(pointamount)
                        }

                        # make settle future

                        asyncio.ensure_future(self.Gash_Wallet_Settle_Future(memberid,transid,amount))
            elif updaterows ==1 and pay_status == '0':
                clientdata = {
                    "status_code": 0,
                    "showstr": "儲值未完成, 稍後系統將會幫您確認此筆訂單, 如訂單付款成功, 稍後系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows ==1 and pay_status == 'W':
                clientdata = {
                    "status_code": 0,
                    "showstr": "此筆交易訂單需要再次確認, 稍後系統將會自動為您確認, 如訂單成功付款, 系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows ==0:
                clientdata = {
                    "status_code": 99
                }

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_ret_gash_wallet_base64 except:{0}'.format(e))

        return result , clientdata


    async def webapi_ret_gash_point_base64(self,base64,redis_obj,cardinfo):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 解開 base64 data
            xmldict = Gash.decode_b64xml(base64)
            if xmldict is None:
                return result, clientdata

            trans = xmldict.get('TRANS')

            memberid = pg_general.converttype(trans.get('USER_ACCTID'),int)
            transid = pg_general.converttype(trans.get('COID'),int)
            pay_rcode = trans.get('PAY_RCODE')
            pay_status = pg_general.converttype(trans.get('PAY_STATUS'),str)
            amount = pg_general.converttype(trans.get('AMOUNT'),int)
            ip = trans.get('USER_IP')
            # 先 update 那筆單
            utcnowdatetime = pg_general.getutcnow_datetime()
            command = 'update gashwalletdeposite set pay_rcode="{0}",pay_status="{6}",return_base64="{1}",ip="{2}",status="1",endtime="{5}" where status="0" ' \
                      'and memberid = "{3}" and transid="{4}"'.format(pay_rcode,base64,ip,memberid,transid,utcnowdatetime,pay_status)
            updaterows = await self.updatedbdata_affectrows('update gash wallet return data',command)

            if updaterows ==1 and pay_rcode =='0000' and pay_status=='S':     # 交易成功
                command= 'select gashpointinfo.*, gashwalletdeposite.itemcode as itemid, gashwalletdeposite.amount as buyamount from gashwalletdeposite,gashpointinfo ' \
                         'where  gashpointinfo.itemcode=gashwalletdeposite.itemcode and gashwalletdeposite.transid = "{0}"'.format(transid)

                datalen , data = await self.getdbdata('get gashpointinfo',command,False,True)
                if datalen == 1:
                    itemcode = data.get('itemcode')
                    cashamount = data.get('cashamount')
                    buyamount = data.get('buyamount')
                    pointamount = data.get('pointamount')

                    if cashamount == buyamount == amount:
                        # write transaction log
                        param = {
                            "frommemberid": memberid,
                            "tomemberid": memberid,
                            "type": pg_general.transactiontype.gashpoint,
                            "amount": pointamount,
                            "otherdata": {"type":"gashpoint","transid": transid}
                        }
                        asyncio.ensure_future(self.writetransactionlog('web gash point buy point', param))

                        # 寫入凍結額度
                        param = {
                            "memberid": memberid,
                            "type": 3,  # gash point
                            "amount": pointamount * 100  # 轉成金幣
                        }
                        # asyncio.ensure_future(self.writegiftfreeze('gash point deposite', param))

                        # update member acc
                        command = 'update member set point=point+"{0}" where memberid="{1}"'.format(pointamount,memberid)
                        updateresult = await self.updatedbdata('update member point',command)

                        # update mmeber card when card <2
                        command = 'update member set card=2 where memberid="{0}" and card<2'.format(memberid)
                        updateresult = await self.updatedbdata('update member level',command)

                        # get member info
                        card = None
                        command = 'select card from member where memberid="{0}"'.format(memberid)
                        datalen , data = await self.getdbdata('get member card',command,False,True)
                        if datalen ==1:
                            card = data.get('card')

                        # update redis cardbuy_{}
                        twnowdate = pg_general.get_tw_datetime().date()
                        firstdate = pg_general.get_tw_2020_first_date().date()
                        datekey = str((twnowdate - firstdate).days % 60)

                        result = await redis_obj.hincrby('cardbuy_{}'.format(memberid), datekey, amount)

                        # make level up future
                        if card in [0, 1, 2, 3, 4]:
                            logintoken = await redis_obj.get_value('{}'.format(memberid))
                            apporweb = 1 # 0: app, 1: web
                            asyncio.ensure_future(self.buycardlevelup_future(apporweb,logintoken, memberid, card, redis_obj, cardinfo))

                        clientdata = {
                            "status_code": 0,
                            "showstr": "儲值成功,感謝您使用 Gash點數購買遊戲點數,您購買的點數 {} 點, 已經存入您 APP 遊戲帳戶,請至 App 將點數轉換成金幣或銀幣進行遊戲 !!".format(pointamount)
                        }

                        # make settle future

                        asyncio.ensure_future(self.Gash_Point_Settle_Future(memberid,transid,amount))
            elif updaterows ==1 and pay_status == '0':
                clientdata = {
                    "status_code": 0,
                    "showstr": "儲值未完成, 稍後系統將會幫您確認此筆訂單, 如訂單付款成功, 稍後系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows ==1 and pay_status == 'W':
                clientdata = {
                    "status_code": 0,
                    "showstr": "此筆交易訂單需要再次確認, 稍後系統將會自動為您確認, 如訂單成功付款, 系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows ==0:
                clientdata = {
                    "status_code": 99
                }

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_ret_gash_point_base64 except:{0}'.format(e))

        return result , clientdata

    async def Gash_Wallet_Settle_Future(self,memberid,transid,amount):
        try:
            settlebase64 = Gash.Make_Wallet_Settle(memberid, transid, amount)

            if settlebase64 is not None:
                url = Gash.GASH_SETTLE_URL

                myClient = sudscl.Client(url)
                resultb64 = myClient.service.getResponse(settlebase64)

                data = Gash.decode_b64xml(resultb64).get('TRANS')

                if data is not None:
                    pay_status = data.get('PAY_STATUS')
                    pay_rcode = data.get('PAY_RCODE')
                    return_transid = pg_general.converttype(data.get('COID'),int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'),int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'),int)
                    if pay_status =='S' and pay_rcode =='0000' and transid==return_transid and memberid==return_memberid and amount ==return_amount: # 請款成功
                        command = 'update gashwalletdeposite set settlebase64="{0}",settlereturnbase64="{1}",status="2" where transid="{2}"'.format(settlebase64,resultb64,transid)
                        updateresult = await self.updatedbdata('update settle',command)

                await self.Gash_Wallet_Check_Future(memberid,transid,amount)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Wallet_Settle_Future except:{0}'.format(e))
        finally:
            pass
    async def Gash_Point_Settle_Future(self,memberid,transid,amount):
        try:
            settlebase64 = Gash.Make_Point_Settle(memberid, transid, amount)

            if settlebase64 is not None:
                url = Gash.GASH_SETTLE_URL

                myClient = sudscl.Client(url)
                resultb64 = myClient.service.getResponse(settlebase64)

                data = Gash.decode_b64xml(resultb64).get('TRANS')

                if data is not None:
                    pay_status = data.get('PAY_STATUS')
                    pay_rcode = data.get('PAY_RCODE')
                    return_transid = pg_general.converttype(data.get('COID'),int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'),int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'),int)
                    if pay_status =='S' and pay_rcode =='0000' and transid==return_transid and memberid==return_memberid and amount ==return_amount: # 請款成功
                        command = 'update gashwalletdeposite set settlebase64="{0}",settlereturnbase64="{1}",status="2" where transid="{2}"'.format(settlebase64,resultb64,transid)
                        updateresult = await self.updatedbdata('update settle',command)

                await self.Gash_Point_Check_Future(memberid,transid,amount)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Point_Settle_Future except:{0}'.format(e))
        finally:
            pass

    async def Gash_Wallet_Check_Future(self,memberid,transid,amount):
        try:
            checkbase64 = Gash.Make_Wallet_Check(memberid, transid, amount)

            if checkbase64 is not None:
                url = Gash.GASH_CHECKORDER_URL

                myClient = sudscl.Client(url)
                resultb64 = myClient.service.getResponse(checkbase64)

                data = Gash.decode_b64xml(resultb64).get('TRANS')

                if data is not None:
                    pay_status = data.get('PAY_STATUS')
                    pay_rcode = data.get('PAY_RCODE')
                    return_transid = pg_general.converttype(data.get('COID'),int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'),int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'),int)
                    if pay_status =='S' and pay_rcode =='0000' and transid==return_transid and memberid==return_memberid and amount ==return_amount: # 查帳成功
                        command = 'update gashwalletdeposite set checkbase64="{0}",checkreturnbase64="{1}",status="3" where transid="{2}"'.format(checkbase64,resultb64,transid)
                        updateresult = await self.updatedbdata('update settle',command)





        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Wallet_Check_Future except:{0}'.format(e))
        finally:
            pass

    async def Gash_Point_Check_Future(self,memberid,transid,amount):
        try:
            checkbase64 = Gash.Make_Point_Check(memberid, transid, amount)

            if checkbase64 is not None:
                url = Gash.GASH_CHECKORDER_URL

                myClient = sudscl.Client(url)
                resultb64 = myClient.service.getResponse(checkbase64)

                data = Gash.decode_b64xml(resultb64).get('TRANS')

                if data is not None:
                    pay_status = data.get('PAY_STATUS')
                    pay_rcode = data.get('PAY_RCODE')
                    return_transid = pg_general.converttype(data.get('COID'),int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'),int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'),int)
                    if pay_status =='S' and pay_rcode =='0000' and transid==return_transid and memberid==return_memberid and amount ==return_amount: # 查帳成功
                        command = 'update gashwalletdeposite set checkbase64="{0}",checkreturnbase64="{1}",status="3" where transid="{2}"'.format(checkbase64,resultb64,transid)
                        updateresult = await self.updatedbdata('update settle',command)





        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Point_Check_Future except:{0}'.format(e))
        finally:
            pass

    async def webapi_ecpay_credit_start_purchase(self,ecpaydata):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:webapi_ecpay_credit_start_purchase ecpaydata:{0}'.format(ecpaydata))

            result = False
            clientdata = {}
            # 產生單號
            starttimedatetime = pg_general.getutcnow_datetime()
            MerchantTradeDate = starttimedatetime.strftime('%Y/%m/%d %H:%M:%S')

            command = 'insert into creditcarddeposite(memberid,starttime,ProductName,Amount,ProductNum,token,paymentStr,' \
                      'paymentType,CarruerType,Donation,LoveCode,CarruerNum,CustomerAddr,CustomerPhone,CustomerEmail,CustomerName,' \
                      'invoiceAgent,CustomerIdentifier) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'

            param=[[
                ecpaydata.get('memberid'),
                starttimedatetime,
                ecpaydata.get('ProductName'),
                ecpaydata.get('Amount'),
                ecpaydata.get('ProductNum'),
                ecpaydata.get('token'),
                ecpaydata.get('paymentStr'),
                ecpaydata.get('paymentType'),
                ecpaydata.get('CarruerType'),
                ecpaydata.get('Donation'),
                ecpaydata.get('LoveCode'),
                ecpaydata.get('CarruerNum'),
                ecpaydata.get('CustomerAddr'),
                ecpaydata.get('CustomerPhone'),
                ecpaydata.get('CustomerEmail'),
                ecpaydata.get('CustomerName'),
                ecpaydata.get('invoiceAgent'),
                ecpaydata.get('CustomerIdentifier')
            ]]
            insertresult, MerchantTradeNo = await self.insertdbdata('write credit card log', command, True, param)

            # get credit card item
            command = 'select * from creditcardinfo where itemcode ="{0}"'.format(ecpaydata.get('ProductNum'))
            datalen , data = await self.getdbdata('get credit card item',command)
            if datalen != 1:
                raise('get credit card item erro')

            itemcode = ecpaydata.get('ProductName')
            cashamount = data.get('cashamount')
            pointamount = data.get('pointamount')

            clientdata= {
                "BindingCard": 0,           # 是否記憶信用卡
                "MerchantTradeDate": MerchantTradeDate,
                "PaymentType": "aio",
                "ReturnURL": ECPay.ReturnURL,
                "ChoosePayment": "Credit",
                "EncryptType": 1,
                "MerchantMemberID": ecpaydata.get('memberid'),
                "Redeem": 'Y',
                "MerchantID": ECPay.MerchantID,
                "MerchantTradeNo": 'c' + pg_general.converttype(MerchantTradeNo,str),
                "ItemName": itemcode,
                "UnionPay": 2,
                "TotalAmount": cashamount,
                "TradeDesc": "金爽娛樂遊戲點數",#urllib.parse.quote_plus("金爽娛樂遊戲點數"),
                "InvoiceMark": 'Y',
                "CustomerAddr": ecpaydata.get('CustomerAddr'),
                "TaxType": '1',
                "CarruerType": ecpaydata.get('CarruerType'),
                "CarruerNum": ecpaydata.get('CarruerNum'),
                "Donation": ecpaydata.get('Donation'),
                "LoveCode": ecpaydata.get('LoveCode'),
                "Print": '1' if ecpaydata.get('CustomerIdentifier') or ecpaydata.get('CustomerName') else '0',                             # 是否要列印發票要判斷
                "InvoiceItemName": "遊戲點數", #urllib.parse.quote_plus("點數內購"),
                "InvoiceItemCount": '1',
                "InvoiceItemWord": '組', #urllib.parse.quote_plus("個"),
                "InvoiceItemPrice": pg_general.converttype(cashamount,str),
                "InvoiceItemTaxType": '1',
                "DelayDay": 0,
                "InvType": '07',
                "RelateNumber": 'creditcard'+ pg_general.converttype(MerchantTradeNo,str),   # 發票不可重複隨機碼
                "CustomerPhone": ecpaydata.get('CustomerPhone'),
                "CustomerEmail": ecpaydata.get('CustomerEmail'),
                "CustomerName": ecpaydata.get('CustomerName'),
                "CustomerIdentifier": ecpaydata.get('CustomerIdentifier'),
                "OrderResultURL": ECPay.ClientBackURL

            }

            final_order_params = ecpay_payment_sdk.create_order(clientdata)
            html = ecpay_payment_sdk.gen_html_post_form(ECPay.Action, final_order_params)

            clientdata.update({
                "Action": ECPay.Action,
                "code": "200",
                "CheckMacValue": final_order_params.get('CheckMacValue'),
                "html": html

            })

            result = True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_ecpay_credit_start_purchase except:{0}'.format(e))

        return result , clientdata

    async def writegashwalleterrorlog(self,transid,memberid,amount,type,param):
        try:
            logtimeutc = pg_general.getutcnow()

            base64 = param.get('base64')
            returnbase64 = param.get('returnbase64')

            command = 'insert into gashwalleterror (transid,memberid,logtime,type,amount,base64,returnbase64) values' \
                      '(%s,%s,%s,%s,%s,%s,%s)'

            insertparam = []
            insertparam.append([transid,memberid,logtimeutc,type,amount,base64,returnbase64])

            insertresult,insertindex = await self.insertdbdata('insert into gashwalleterrorlog',command,many=True,manydata=insertparam)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writegashwalleterrorlog except:{0}'.format(e))

    async def saveloginuid(self,logintoken,memberid,param):
        try:

            uid_g = param.get('uid_g')
            uid_s = param.get('uid_s')

            command = 'update member set uid_g="{0}",uid_s="{1}" where memberid = "{2}"'.format(uid_g,uid_s,memberid)
            updateresult = await self.updatedbdata(logintoken,command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:saveloginuid except:{0}'.format(e))

    async def webapi_add_comment(self,memberid,typeid,content):
        try:
            logtime = pg_general.getutcnow_datetime()

            command = 'insert into webcommentlog(logtime,typeid,status,content,memberid) values("{0}","{1}","{2}","{3}","{4}")'.format(logtime,typeid,0,content,memberid)
            insertresult = await self.insertdbdata('insert web comment',command)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_add_comment except:{0}'.format(e))


    async def testgoogleiapconfirm(self):
        try:
            response_data = GOOGLE_IAP_SERVICE.purchases().products().get(packageName=GOOGLE_IAP_BUNDLE_ID,
                                                                          productId="shopmall_02", token="mlohliddmhghoeonjklhoegk.AO-J1Oyj77u0dO9EnIpqdnggZz4N5YRGf5Xyzvduqv2iuZ8XIKzoNg0dZ8KPWmBQspj2mPysZXs9tsHPGmn6gR20MyV6uUaKPfmXbK_VMM292AQnicO_WDqfkaAy3MB8OW4QnIADU2_A").execute()
        except Exception as e:
            print(e)
        pass

    async def webapi_ecpay_credit_order_result(self,redis_obj,cardinfo,orderresultdata):
        try:

            result = pg_general.Apiresult.connectdberror

            CheckMacValue = orderresultdata.get('CheckMacValue')  # 先將 此東西移除 dict
            MerchantTradeNo = orderresultdata.get('MerchantTradeNo')
            SimulatePaid = orderresultdata.get('SimulatePaid')
            TradeNo = orderresultdata.get('TradeNo')
            PaymentTypeChargeFee = orderresultdata.get('PaymentTypeChargeFee')
            MerchantID = orderresultdata.get('MerchantID')
            RtnCode = orderresultdata.get('RtnCode')
            PaymentType = orderresultdata.get('PaymentType')
            TradeAmt = orderresultdata.get('TradeAmt')
            RtnMsg = orderresultdata.get('RtnMsg')
            PaymentDate = orderresultdata.get('PaymentDate')
            TradeDate = orderresultdata.get('TradeDate')

            # 先寫紀錄
            transid = MerchantTradeNo[1:]
            command = 'update creditcarddeposite set order_result=\'{0}\',status="{2}" where transid="{1}"'.format(json.dumps(orderresultdata), transid,RtnCode)
            updateresult = await self.updatedbdata('write creditcarddeposite order_result', command)

            # 抓原始單 比對是否與原始單 內容相同
            checkoriginal = False
            command = 'select creditcarddeposite.memberid,creditcarddeposite.Amount,creditcardinfo.cashamount,creditcardinfo.pointamount ' \
                      'from creditcarddeposite,creditcardinfo where creditcarddeposite.transid = "{0}" and creditcardinfo.itemcode=creditcarddeposite.ProductNum'.format(transid)
            datalen ,data = await self.getdbdata('get creditcarddeposite 2',command)
            if datalen == 1:
                memberid = data.get('memberid')
                Amount = data.get('Amount')
                cashamount = data.get('cashamount')
                pointamount = data.get('pointamount')
                if Amount == pg_general.converttype(TradeAmt,int) == cashamount:
                    checkoriginal = True

            checkmacvalue_again = ecpay_payment_sdk.generate_check_value(orderresultdata)
            if checkmacvalue_again != CheckMacValue or RtnCode!='1' or checkoriginal == False:
                clientdata = {
                    "status_code": 1,
                    "showstr": "購買此商品失敗!!"
                }
            else:
                # update point to member account
                command = 'update member set point=point+"{0}" where memberid = "{1}"'.format(pointamount,memberid)
                updateresult2 = await self.updatedbdata('update member point',command)

                # update mmeber card when card <2
                command = 'update member set card=2 where memberid="{0}" and card<2'.format(memberid)
                updateresult = await self.updatedbdata('update member card', command)

                # get member info
                card = None
                command = 'select card from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata('get member card', command, False, True)
                if datalen == 1:
                    card = data.get('card')

                # update redis cardbuy_{}
                twnowdate = pg_general.get_tw_datetime().date()
                firstdate = pg_general.get_tw_2020_first_date().date()
                datekey = str((twnowdate - firstdate).days % 60)

                result = await redis_obj.hincrby('cardbuy_{}'.format(memberid), datekey, cashamount)

                # make level up future
                if card in [0, 1, 2, 3, 4]:
                    logintoken = await redis_obj.get_value('{}'.format(memberid))
                    apporweb = 1  # 0: app, 1: web
                    asyncio.ensure_future(
                        self.buycardlevelup_future(apporweb, logintoken, memberid, card, redis_obj, cardinfo))

                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.webcreditcard,
                    "amount": pg_general.converttype(TradeAmt,int),
                    "otherdata": {"type":"webcreditcard","transid": transid}
                }
                asyncio.ensure_future(self.writetransactionlog('web ecpay credit card buy point', param))

                # 寫入凍結額度
                param = {
                    "memberid": memberid,
                    "type": 2,  # credit card
                    "amount": pointamount * 100  # 轉成金幣
                }
                # asyncio.ensure_future(self.writegiftfreeze('credit card deposite', param))

                clientdata = {
                    "status_code": 0,
                    "showstr": "謝謝您使用信用卡購買金爽娛樂城遊戲點數,請至遊戲內兌換成金爽幣遊戲 !!"
                }

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_ecpay_credit_order_result except:{0}'.format(e))

        return result , clientdata


    async def getmemberinfolessdata(self,redis_obj,logintoken,memberid,findmemberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {
                "result":1
            }
            command = 'select nickname,avatar from member where memberid = "{0}"'.format(findmemberid)
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen >0:
                nickname = data.get('nickname')
                avatar = data.get('avatar')

                clientdata ={
                    "result": 0,
                    "memberid": findmemberid,
                    "nickname": nickname,
                    "avatar": avatar
                }


            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getmemberinfolessdata except:{0}'.format(e))

        return result , clientdata

    async def getboxinfo(self,redis_obj,logintoken,memberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'select dayamount,cost,goldpossible,member.todayboxtimes,member.silvercredit from boxsetting,member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken,command)
            if datalen > 0:
                dayamount = data.get('dayamount')
                goldpossible = data.get('goldpossible')
                cost = json.loads(data.get('cost'))
                todayboxtimes = data.get('todayboxtimes')
                silvercredit = data.get('silvercredit')
                if None in [dayamount,goldpossible,cost,todayboxtimes]:
                    raise Exception('get boxsetting error')

                clientdata = {
                    "totaltimes": dayamount,
                    "usedtimes": todayboxtimes,
                    "silvercredit": silvercredit,
                    "goldpossible": goldpossible,
                    "cost1": cost.get('cost1'),
                    "cost10": cost.get('cost10')
                }

                result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getboxinfo except:{0}'.format(e))

        return result , clientdata


    async def buybox(self,redis_obj,logintoken,memberid,item):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result":1}

            command = 'select boxsetting.*,member.silvercredit,member.todayboxtimes from boxsetting,member ' \
                      'where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken,command)

            todayboxtimes = data.get('todayboxtimes')
            silvercredit = data.get('silvercredit')

            dayamount = data.get('dayamount')
            boxweight = json.loads(data.get('boxweight'))
            takeweight = json.loads(data.get('takeweight'))
            cost = json.loads(data.get('cost'))

            # check all data
            if None in [todayboxtimes,silvercredit,dayamount,boxweight,takeweight,cost]:
                raise Exception('buybox data error 1 ')

            goldboxweight = boxweight.get('gold')
            silverboxweight = boxweight.get('silver')
            take1weight = takeweight.get('take1')
            take10weight = takeweight.get('take10')
            cost1 = cost.get('cost1')
            cost10 = cost.get('cost10')

            if None in [goldboxweight,silverboxweight,take1weight,take10weight,cost1,cost10]:
                raise Exception('buybox data error 2')

            if item not in [0,1]:
                raise Exception('item is error')

            # 今天次數是否已經購買完
            if todayboxtimes >= dayamount and item==0:
                result = pg_general.Apiresult.success
                return result, clientdata

            if todayboxtimes + 10 > dayamount and item ==1 :
                result = pg_general.Apiresult.success
                return result, clientdata

            #  看銀幣是否足夠
            if item == 0:   # take1
                if silvercredit < cost1:
                    result = pg_general.Apiresult.success
                    return result, clientdata
            else:   # take 10
                if silvercredit < cost10:
                    result = pg_general.Apiresult.success
                    return result, clientdata


            if item == 0:    # take 1
                templist = []
                for item in take1weight:
                    tempvalue = item.get('value')
                    tempweight = item.get('weight')
                    for _ in range(tempweight):
                        templist.append(tempvalue)

                random.random()
                takechoice = random.choice(templist)

                if takechoice == 1: # 金寶相
                    templist2 = []
                    for tempitem in goldboxweight:
                        tempvalue = tempitem.get('value')
                        tempweight = tempitem.get('weight')
                        for _ in range(tempweight):
                            templist2.append(tempvalue)
                else:               # 銀寶箱
                    templist2 = []
                    for tempitem in silverboxweight:
                        tempvalue = tempitem.get('value')
                        tempweight = tempitem.get('weight')
                        for _ in range(tempweight):
                            templist2.append(tempvalue)

                random.random()
                takeboxvalue = random.choice(templist2)
                # update member
                command = 'update member set credit=credit+"{0}",todayboxtimes=todayboxtimes+1,silvercredit=silvercredit-"{1}" ' \
                          'where memberid = "{2}"'.format(takeboxvalue,cost1,memberid)
                upateresult = await self.updatedbdata(logintoken,command)

                # get silvercredit,credit,
                command = 'select credit,silvercredit from member where memberid="{0}"'.format(memberid)
                datalen,data = await self.getdbdata(logintoken,command,False,True)
                aftersilvercredit = data.get('silvercredit')
                aftercredit = data.get('credit')

                clientdata = {
                    "result": 0,
                    "getgoldcredit": takeboxvalue,
                    "silvercredit": aftersilvercredit,
                    "credit": aftercredit,
                    "boxresult":[{"type": takechoice,"amount":takeboxvalue}]

                }
                # write to transaction log cost
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.buyboxcost,
                    "amount_silver": cost1,
                    "otherdata": "buyboxcost1"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))
                # write to transaction log get
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.buyboxget,
                    "amount": takeboxvalue,
                    "otherdata": "buyboxget1"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

            elif item ==1: # take 10
                templist = []
                for tempitem in take10weight:
                    tempvalue = tempitem.get('value')
                    tempweight = tempitem.get('weight')
                    for _ in range(tempweight):
                        templist.append(tempvalue)

                random.random()
                random.shuffle(templist)
                takegoldamount = random.choice(templist)
                takesilveramount = 10 - takegoldamount
                takeboxlist = []
                for _ in range(takegoldamount):
                    takeboxlist.append(1)
                for _ in range(takesilveramount):
                    takeboxlist.append(0)

                boxresult = []
                getgoldcredit = 0
                random.shuffle(takeboxlist)
                for takechoice in takeboxlist:
                    if takechoice == 1:  # 金寶相
                        templist2 = []
                        for tempitem in goldboxweight:
                            tempvalue = tempitem.get('value')
                            tempweight = tempitem.get('weight')
                            for _ in range(tempweight):
                                templist2.append((1,tempvalue))
                    else:  # 銀寶箱
                        templist2 = []
                        for tempitem in silverboxweight:
                            tempvalue = tempitem.get('value')
                            tempweight = tempitem.get('weight')
                            for _ in range(tempweight):
                                templist2.append((0,tempvalue))

                    random.random()
                    takebox = random.choice(templist2)
                    takeboxvalue = takebox[1]
                    takeboxtype = takebox[0]
                    getgoldcredit += takeboxvalue
                    boxresult.append({"type":takeboxtype,"amount":takeboxvalue})

                if item == 0 :
                    addtimes = 1
                elif item ==1 :
                    addtimes = 10
                # update member
                command = 'update member set credit=credit+"{0}",todayboxtimes=todayboxtimes+"{3}",silvercredit=silvercredit-"{1}" ' \
                          'where memberid = "{2}"'.format(getgoldcredit, cost10, memberid,addtimes)
                upateresult = await self.updatedbdata(logintoken, command)

                # get silvercredit,credit,
                command = 'select credit,silvercredit from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                aftersilvercredit = data.get('silvercredit')
                aftercredit = data.get('credit')

                clientdata = {
                    "result": 0,
                    "getgoldcredit": getgoldcredit,
                    "silvercredit": aftersilvercredit,
                    "credit": aftercredit,
                    "boxresult": boxresult

                }
                # write to transaction log cost
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.buyboxcost,
                    "amount_silver": cost10,
                    "otherdata": "buyboxcost10"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))
                # write to transaction log get
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.buyboxget,
                    "amount": getgoldcredit,
                    "otherdata": "buyboxget10"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))


            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:buybox except:{0}'.format(e))

        return result , clientdata

    async def skiptutorial(self,redis_obj,logintoken,memberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result":0}

            command = 'update member set tutorialbetfinish ="3" where memberid = "{0}"'.format(memberid)
            updateresult = await self.updatedbdata(logintoken,command)


            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:skiptutorial except:{0}'.format(e))

        return result , clientdata
    
    async def gettutorialguide(self,redis_obj,logintoken,memberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'select * from guidesetting order by posindex'
            datalen, data = await self.getdbdata(logintoken,command,True)
            if datalen > 0:
                guidelist = []
                for item in data:
                    guidelist.append({
                        "posindex": item.get('posindex'),
                        "buttonurl": item.get('buttonurl'),
                        "picurl": item.get('picurl'),
                        "size": item.get('size')
                    })
                clientdata = {"guidelist": guidelist}

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:gettutorialguide except:{0}'.format(e))

        return result , clientdata




    async def joinfishgame(self,redis_obj,logintoken,memberid,hallid,gameid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result":1}

            # get member level data
            command = 'select level from member where memberid = "{0}"'.format(memberid)
            datalen , data = await self.getdbdata(logintoken,command)
            if datalen != 1:
                return result, clientdata
            level = data.get('level')
            if level < 5:
                el = 1
            elif level < 25:
                el = 2
            else:
                el = 3

            if hallid == 0: # gold
                host_id = env_setting.PS_HOST_ID
                gametype = 3
                hallkey = 'g'
            elif hallid ==1: # silver
                host_id = env_setting.PS_HOST_ID_S
                gametype = 4
                hallkey = 's'
            else:
                return result,clientdata

            # call createplayer
            result = await self.call_gameapi_createplay(logintoken,memberid,host_id)
            if result == False:
                return result, clientdata

            result = await self.call_gameapi_transferAllCreditToGame(logintoken,memberid,host_id,hallid)
            if result == False:
                return result, clientdata

            # set redis dirtyfish
            await redis_obj.hset('dirtyfish', '{}_{}_{}'.format(hallkey,gameid,memberid), 1)
            await redis_obj.set_value('fish_{}_{}_{}'.format(hallkey,gameid,memberid),1,15)

            access_token = 'fish*****{}'.format(logintoken)
            # write membergamelog
            nowutctime = pg_general.getutcnow()
            command = 'insert into membergamelog(memberid, gameid, joingametime, logintoken,gametype,seatnum) values("{0}", "{1}", "{2}", "{3}","{4}","{5}")'.format(
                memberid, gameid, nowutctime, logintoken, gametype, 0)
            updateresult, dataindex = await self.insertdbdata(logintoken, command)
            if updateresult == True:

                # get fish launch url
                fishurl = await self.call_gameapi_getFishLaunchUrl(logintoken,memberid,host_id,gameid,access_token)
                clientdata['logdataindex'] = dataindex
                clientdata['result'] = 0
                # clientdata['url'] = env_setting.PS_API_SERVER_URL + 'launch/?host_id={}&game_id={}&lang=zh-TW' \
                #                                                     '&access_token={}&el={}'.format(host_id,gameid,access_token,el)
                if env_setting.PRODUCTION_MODE == True:
                    clientdata['url'] = fishurl + '&el={}'.format(el)
                else:
                    clientdata['url'] = env_setting.PS_API_SERVER_URL + fishurl[2:] + '&el={}'.format(el)

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:gettutorialguide except:{0}'.format(e))

        return result , clientdata


    async def call_gameapi_createplay(self,logintoken,memberid,host_id):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:call_gameapi_createplay host_id:{},logintoken:{},memberid:{}'.format(host_id,logintoken,memberid))

            result = False

            # call createplay
            url = env_setting.PS_API_SERVER_URL + 'funds/createplayer/?host_id={}&member_id={}&purpose=1'.format(host_id,'fish_{}'.format(memberid))

            errcount = 0
            for _ in range(3):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=60) as response:
                        if response.status == 200:
                            data = await response.text()
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'call_gameapi_createplay response:{},logintoken:{},url:{}'.format(data, logintoken,url))
                            result = True
                            break
                        else:
                            errcount+=1
                            await asyncio.sleep(0)
            if errcount >= 3:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:call_gameapi_createplay error errcount:{0}'.format(errcount))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_createplay except:{0}'.format(e))

        return result

    async def call_gameapi_transferAllCreditToGame(self,logintoken,memberid,host_id,hallid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:call_gameapi_transferAllCreditToGame logintoken:{},memberid:{},host_id:{}:hallid:{}'.format(logintoken,memberid,host_id,hallid))
            result = False

            # get credit
            if hallid ==0: # gold
                command = 'select credit from member where memberid = "{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken,command,False,True)
                if datalen !=1:
                    return result
                creditamount = data.get('credit')
                if creditamount > 0:
                    # 扣款
                    command = 'update member set credit = credit - "{0}" where memberid ="{1}" and credit >= "{0}"'.format(creditamount,memberid)
                    affectrows = await self.updatedbdata_affectrows(logintoken,command)
                    if affectrows !=1:
                        return result
                elif creditamount ==0:
                    pass
                else:
                    raise Exception('creditamount < 0')
                amount = creditamount
                amount_silver = 0
            elif hallid ==1: # silver
                command = 'select silvercredit from member where memberid = "{0}"'.format(memberid)
                datalen , data = await self.getdbdata(logintoken,command,False,True)
                if datalen !=1:
                    return result
                creditamount = data.get('silvercredit')
                if creditamount > 0:
                    # 扣款
                    command = 'update member set silvercredit = silvercredit -"{0}" where memberid="{1}" and silvercredit >= "{0}"'.format(creditamount,memberid)
                    affectrows = await self.updatedbdata_affectrows(logintoken,command)
                    if affectrows != 1:
                        return result
                elif creditamount ==0:
                    pass
                else:
                    raise Exception('creditamount < 0')
                amount = 0
                amount_silver = creditamount
            else:           # other error
                return result

            # make transaction log and
            transtime = pg_general.getutcnow_datetime()
            type = pg_general.transactiontype.depositefishgame
            otherdata = 'fishgame deposite'
            command = 'insert into transaction (transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata) values ' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime,memberid,memberid,type,amount,amount_silver,otherdata)
            updateresult, txn_id = await self.insertdbdata(logintoken,command)

            if creditamount ==0:
                return True     # 如果要轉的分數 ==0, 不用轉
            # call funds transfer to ps
            url = env_setting.PS_API_SERVER_URL + 'funds/deposit/?host_id={}&member_id=fish_{}&txn_id={}&amount={}&purpose=1'.format(host_id,memberid,txn_id,creditamount)
            errcount = 0
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response:
                            if response.status == 200:
                                data = await response.json()
                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                    'call_gameapi_transferAllCreditToGame response:{},logintoken:{},url:{}'.format(data,logintoken,url))

                                break
                            else:
                                errcount += 1
                                await asyncio.sleep(0)
                except Exception as e:
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'pg_asqldb:call_gameapi_transferAllCreditToGame transfer error e:{0}'.format(e))
                    await asyncio.sleep(0.1)
            if errcount >= 3:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:call_gameapi_transferAllCreditToGame error errcount:{0}'.format(errcount))
            else:
                if data.get('status_code') == 0 :
                    result = True
                else:
                    result = False
                    raise Exception('response not 200:{}'.format(json.dumps(data)))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_transferAllCreditToGame except:{0}'.format(e))

        return result

    async def call_gameapi_transferAllCreditToHost(self,logintoken,memberid,host_id,hallid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:call_gameapi_transferAllCreditToHost logintoken:{},memberid:{},host_id:{},hallid:{}'.format(logintoken,memberid,host_id,hallid))

            # make transaction log and get txn_id
            transtime = pg_general.getutcnow_datetime()
            type = pg_general.transactiontype.withdrawfishgame
            otherdata = 'fishgame withdraw'
            command = 'insert into transaction (transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata) values ' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime, memberid, memberid, type, 0,
                                                                           0, otherdata)
            updateresult, txn_id = await self.insertdbdata(logintoken, command)

            url = env_setting.PS_API_SERVER_URL + 'funds/withdrawall/?host_id={}&member_id=fish_{}&txn_id={}&purpose=1'.format(host_id,memberid,txn_id,)
            errcount = 0
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response:
                            if response.status == 200:
                                data = await response.json()
                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                    'call_gameapi_transferAllCreditToHost response:{},logintoken:{},url:{}'.format(
                                                        data, logintoken, url))

                                break
                            else:

                                errcount += 1
                                await asyncio.sleep(0)
                except Exception as e:
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'pg_asqldb:call_gameapi_transferAllCreditToGame transfer error e:{0}'.format(e))
                    await asyncio.sleep(0.1)
            if errcount >= 3:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:call_gameapi_transferAllCreditToGame error errcount:{0}'.format(
                                        errcount))
            else:
                if data.get('status_code') == 0:

                    result = True
                    if hallid ==0:
                        amount = data.get('amount')
                        amount_silver = 0
                    elif hallid ==1:
                        amount = 0
                        amount_silver = data.get('amount')
                    # update transaction log amount or amount_silver
                    command = 'update transaction set amount="{0}",amount_silver="{1}" where transactionindex = "{2}"'.format(amount,amount_silver,txn_id)
                    updateresult = await self.updatedbdata_affectrows(logintoken,command)

                    # update member credit and silvercredit
                    command = 'update member set credit= credit+"{0}" ,silvercredit = silvercredit+"{1}" where memberid = "{2}"'.format(amount,amount_silver,memberid)
                    updateresult = await self.updatedbdata_affectrows(logintoken,command)
                else:
                    result = False
                    raise Exception('response not 200:{}'.format(json.dumps(data)))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_transferAllCreditToHost except:{0}'.format(e))

    async def call_gameapi_getFishLaunchUrl(self,logintoken,memberid,hostid,gameid,access_token):
        try:
            url = env_setting.PS_GETLAUNCHURL_FISH.format(hostid, gameid, 'zh-TW',access_token)
            errcount = 0
            fishurl = ''
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response:
                            if response.status == 200:
                                data = await response.json()
                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                    'call_gameapi_getFishLaunchUrl response:{},logintoken:{},url:{}'.format(
                                                        data, logintoken, url))

                                break
                            else:

                                errcount += 1
                                await asyncio.sleep(0)
                except Exception as e:
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'pg_asqldb:call_gameapi_getFishLaunchUrl transfer error e:{0}'.format(e))
                    await asyncio.sleep(0.1)
            if errcount >= 3:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:call_gameapi_getFishLaunchUrl error errcount:{0}'.format(
                                        errcount))
            else:
                if data.get('status_code') == 0:
                    fishurl = data.get('url')

                else:
                    raise Exception('response not 200:{}'.format(json.dumps(data)))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_getFishLaunchUrl except:{0}'.format(e))
        return fishurl