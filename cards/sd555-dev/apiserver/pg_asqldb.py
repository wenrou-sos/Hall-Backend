import asyncio
import aiomysql
import time
import os
import env_setting
import pg_general
import random
import json
import jwt
from datetime import timedelta, datetime
from traceback import format_exc
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
from difflib import SequenceMatcher
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import Gash
import suds.client as sudscl
import ECPay
# import FlashPay
import urllib.parse
import importlib.util
import applesignin
import calendar
import math
import base64

from data_class import ClubRight

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
    MerchantID=ECPay.MerchantID,
    HashKey=ECPay.HashKey,
    HashIV=ECPay.HashIV
)

from pg_redis import PGRedis, DEFAULT_EXPIRE_SECONDS

if env_setting.LOCAL_SERVER == True:
    DB_HOST = '35.234.43.196'
    DB_HOST_READ = '35.234.43.196'
else:
    if env_setting.PRODUCTION_MODE == False:
        DB_HOST = '10.13.64.4'
        DB_HOST_READ = '10.13.64.4'
    else:
        DB_HOST = '10.13.64.4'
        DB_HOST_READ = '10.13.64.4'

DB_USER = 'root'
DB_NAME = 'slotwarapp'
if env_setting.PRODUCTION_MODE == False:
    DB_PASSWORD = '1EHhbNow3yxKcEmD'
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

# if env_setting.LOCAL_SERVER:
#    AUTH_GOOGLE_IAP_FILE = "api-5948518497852894469-486172-a6232afe0253.json"
# else:
#    AUTH_GOOGLE_IAP_FILE = os.path.dirname(os.path.abspath(__file__)) + "//api-5948518497852894469-486172-a6232afe0253.json"

if env_setting.LOCAL_SERVER:
    AUTH_GOOGLE_IAP_FILE = "play-integrity-qvqousqcsyfbhsv-7ca38589bb06.json"
else:
    AUTH_GOOGLE_IAP_FILE = os.path.dirname(
        os.path.abspath(__file__)) + "//play-integrity-qvqousqcsyfbhsv-7ca38589bb06.json"

import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

GOOGLE_IAP_CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(AUTH_GOOGLE_IAP_FILE,
                                                                          scopes='https://www.googleapis.com/auth/androidpublisher')
GOOGLE_IAP_SERVICE = googleapiclient.discovery.build("androidpublisher", "v3", credentials=GOOGLE_IAP_CREDENTIALS)
# GOOGLE_IAP_BUNDLE_ID = "com.slots.casino.jinsong"
GOOGLE_IAP_BUNDLE_ID = "com.cards.casino.sd555"


# result = GOOGLE_IAP_SERVICE.purchases().products().get(packageName=GOOGLE_IAP_BUNDLE_ID, productId="shop_lv_04", token="fnbdbnppcfppkfhembnoncdp.AO-J1OzLi2HbKFUKK95ZUhI5CmYvdXXjTNrnBtjh0CilcAh2DbaJPixeTdN_bbDfFoi9qye4IDTKHTdO4Vj5BBAKoj8s9uhZdHaXcG8aUEEofBGwqMWAkx6q6jDD3cRsOOaoTb2gN3TX").execute()
#

class GameID:
    dummy = 'PSC-APP-00006'
    dummy_king = 'PSC-APP-00011'
    pok_deng = 'PSC-APP-00005'
    pai_kang = 'PSC-APP-00007'
    u4 = 'PSC-APP-00014'


class PG_ASQLDB:

    def set_slot_game_db(self, db):
        self.slot_game_db = db

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
                                                            password=DB_PASSWORD, db=DB_NAME, maxsize=1024,
                                                            autocommit=True)
                pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                    "pg_asqldb:createpool: repplication db create pool done")
            else:
                self.pool = await aiomysql.create_pool(host=DB_HOST, port=3306, user=DB_USER,
                                                       password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

                self.pool_read = await aiomysql.create_pool(host=DB_HOST_READ, port=3306, user=DB_USER,
                                                            password=DB_PASSWORD, db=DB_NAME, maxsize=1024,
                                                            autocommit=True)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                "pg_asqldb:createpool except: {0}".format(e))

    async def closepool(self):
        await self.pool.close()
        await self.pool.wait_closed()

        await self.pool_read.close()
        await self.pool_read.wait_closed()

    async def getdbdata(self, logintoken, command=None, fetchall=False, fromwritedb=False):
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
                # connectionpool.release(conn)
                break
            except Exception as e:
                errcount += 1
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:getdbdata exception:{0}, command:{1}, logintoken:{2},errcount:{3}'.format(
                                        e, command,
                                        logintoken, errcount))
                await asyncio.sleep(0)
        try:

            if datalen >= 10000:
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                    "pg_asqldb:getdbdata:finally datalen:{0}, logintoken:{1}".format(datalen,
                                                                                                     logintoken))
            else:
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                    "pg_asqldb:getdbdata:finally datalen:{0}, data:{1}, logintoken:{2}".format(datalen,
                                                                                                               data,
                                                                                                               logintoken))
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getdbdata ValueError:{0}, logintoken:{1}'.format(format_exc(), logintoken))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getdbdata except:{0}, logintoken:{1}'.format(format_exc(), logintoken))

        return datalen, data

    async def insertdbdata(self, logintoken, command=None, many=False, manydata=[]):
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
                    if many == False:
                        datarows = await cur.execute(command)
                    elif many == True:
                        datarows = await cur.executemany(command, manydata)
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

    async def updatedbdata_affectrows(self, logintoken, command=None):
        affectrows = 0
        if command is None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:updatedbdata_affectrows:command=None logintoken:{0}".format(logintoken))
            return affectrows
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        "pg_asqldb:updatedbdata_affectrows:execute command:{0}, logintoken:{1}".format(
                                            command,
                                            logintoken))
                    datarows = await cur.execute(command)
                    await conn.commit()
                    affectrows = datarows
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatedbdata_affectrows exception:{0}, command:{1}, logintoken:{2}'.format(e,
                                                                                                                      command,
                                                                                                                      logintoken))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_asqldb:updatedbdata_affectrows:finally datarows:{0}, logintoken:{1}".format(
                                    affectrows, logintoken))
            return affectrows

    async def getserverinfo(self, logintoken, ver=None, rer=None, platform=None):
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
            datalen, data = await self.getdbdata(logintoken, command)
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
                    if platform is None:  # old version
                        if len(ver.split('.')) == 3 and len(rer.split('.')) == 3:
                            tempver = rerobjectnew.get(ver)
                            if tempver is not None:
                                temprer = tempver.get(rer)
                                if temprer is not None:
                                    if temprer.get('rer') is not None and temprer.get('size') is not None:
                                        isnewversion = True
                                        tempneedask = temprer.get('needask')
                                        if tempneedask is None:
                                            needask = True
                                        else:
                                            needask = tempneedask

                                        rerdata = {
                                            ver: {"rer": temprer.get('rer'),
                                                  "rersize": temprer.get('size')
                                                  }
                                        }
                    else:  # new version with  ios and android seperate
                        if platform == 0:  # ios
                            rerobjectnew = rerobjectnew.get('ios')
                        else:  # android
                            rerobjectnew = rerobjectnew.get('android')

                        if rerobjectnew is not None:
                            if len(ver.split('.')) == 3 and len(rer.split('.')) == 3:
                                tempver = rerobjectnew.get(ver)
                                if tempver is not None:
                                    temprer = tempver.get(rer)
                                    if temprer is not None:
                                        if temprer.get('rer') is not None and temprer.get('size') is not None:
                                            isnewversion = True
                                            tempneedask = temprer.get('needask')
                                            if tempneedask is None:
                                                needask = True
                                            else:
                                                needask = tempneedask

                                            rerdata = {
                                                ver: {"rer": temprer.get('rer'),
                                                      "rersize": temprer.get('size')
                                                      }
                                            }

                # tips
                tips = []
                command = 'select * from loadingtips'
                datalen, data = await self.getdbdata(logintoken, command, True)
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
                            'pg_asqldb:getserverinfo result:{0}, clientdata:{1}, logintoken:{2}'.format(result,
                                                                                                        clientdata,
                                                                                                        logintoken))
        return result, clientdata

    async def write_redis_member_join_channel_future(self, redis_obj, memberid, channel, expiretime=180):
        try:
            # 先抓取 member channel info
            oldchannel = await redis_obj.get_all_keys('channel_*_{}'.format(memberid))
            if len(oldchannel) > 0:  # 如果有存在加入的 channel 則刪除舊有的 data
                for item in oldchannel:
                    await redis_obj.del_key(item)

            await redis_obj.set_value('channel_{}_{}'.format(channel, memberid), str(1), expiretime)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'write_redis_member_join_channel_future memberid:{0},channel:{1}'.format(memberid,
                                                                                                         channel))

    async def write_redis_member_join_clubchannel_future(self, redis_obj, memberid, clubid, expiretime=180):
        try:
            # 先抓取 member channel info
            oldclubchannel = await redis_obj.get_all_keys('clubchannel_*_{}'.format(memberid))
            if len(oldclubchannel) > 0:  # 如果有存在加入的 channel 則刪除舊有的 data
                for item in oldclubchannel:
                    await redis_obj.del_key(item)

            await redis_obj.set_value('clubchannel_{}_{}'.format(clubid, memberid), str(1), expiretime)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'write_redis_member_join_clubchannel_future memberid:{0},channel:{1}'.format(memberid,
                                                                                                             clubid))

    async def generate_nickname_for_line(self, nickname):
        """產生 line 登入使用的名稱

        line 登入的方式可能會發生重複的名字
        在名字後面加上 @{五位數亂碼} 做區隔
        """
        i = 0
        range_start = 0
        range_end = (10 ** 6) - 1

        while True:  # 產生亂碼，若重覆就再產生
            i += 1
            tag = str(randint(range_start, range_end)).zfill(6)
            new_nickname = nickname + '@' + tag

            command = '''SELECT * FROM member WHERE nickname="{}"
            '''.format(new_nickname)

            datalen, data = await self.getdbdata('generate_nickname_for_line', command)

            if datalen == 0:
                break

            if i > 100:
                break

        return new_nickname

    async def login(self, redis_obj, fblink, defaultchannelindex, fbavatarobj, logintoken,
                    deviceid, fbid, fbtoken, fbavatar, fbnickname, ip, platform,
                    devicedescription, lobbyserverip, region, region_sub, city, fcmtoken,
                    ver=None, rer=None, username=None, password=None, newaccflag=None,
                    connecttype=None, auserid=None, aauthcode=None, atoken=None, linecode=None, linestate=None,
                    lineaccesstoken=None):
        """
        登入
        先找出memberid (參照 function findmemberidandlasttoken) 找不到memberid則建立新會員 (參照 function createmember)
        有memberid後更新DB登入資料 (參照 function updatememberlogin)
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:login logintoken:{0}, deviceid:{1}, fbid:{2},'
                                                            'fbtoken:{3},ip:{4}, platform:{5}, devicedescription:{6},lobbyserverip:{7},'
                                                            'fbavatar:{8},fbnickname:{9},fcmtoken:{10},username:{11},password:{12},newaccflag:{13}, linecode:{14}, linestate:{15}, lineaccesstoken:{16}'.format(
            logintoken, deviceid,
            fbid, fbtoken, ip, platform, devicedescription, lobbyserverip, fbavatar, fbnickname, fcmtoken, username,
            password, newaccflag, linecode, linestate, lineaccesstoken))

        totalresult = pg_general.Apiresult.connectdberror  # test
        try:
            clientdata = {}
            serverdata = {}

            memberresult = pg_general.Apiresult.connectdberror
            memberid = None
            createresult = None

            registerflag = 0

            # 檢查 data
            if linecode and linestate:
                command = 'SELECT linecode, linesub, nickname from member WHERE linecode = "{0}"'.format(linecode)
                datalen, data = await self.getdbdata(logintoken, command)

                pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:login select data:{0}'.format(data))

                if datalen == 1:
                    linesub = data.get('linesub')
                    line_nickname = data.get('nickname')

                else:
                    linesub = None
                    line_nickname = None

                if linesub is None and line_nickname is None:
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'pg_asqldb:login gettoken linecode:{0}, linestate:{1}'.format(linecode,
                                                                                                      linestate))
                    line_result, line_clientdata = await self.linelogincallback(linecode, linestate)
                    linesub = line_clientdata.get('sub')
                    line_nickname = line_clientdata.get('name')
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'pg_asqldb:login line_clientdata:{0}, linesub:{1}, line_nickname:{2}'.format(
                                            line_clientdata,
                                            linesub, line_nickname))
                if linesub is None and line_nickname is None:
                    totalresult = pg_general.Apiresult.success
                    clientdata = {
                        "errormsg": "line ID token encoded error"
                    }
                    raise ValueError('line ID token encoded error')

            elif lineaccesstoken:
                command = 'SELECT member.linesub, member.nickname, member.line_access_token, line_profile.access_token from member, line_profile WHERE member.line_access_token = "{0}" AND member.line_access_token = line_profile.access_token'.format(
                    lineaccesstoken)
                datalen, data = await self.getdbdata(logintoken, command)

                pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:login select data:{0}'.format(data))

                if datalen == 1:
                    linesub = data.get('linesub')
                    line_nickname = data.get('nickname')

                else:
                    command = 'SELECT sub, name from line_profile WHERE access_token = {0}'.format(lineaccesstoken)
                    datalen, data = await self.getdbdata(logintoken, command)

                    linesub = data.get('sub')
                    line_nickname = await self.generate_nickname_for_line(data.get('name'))

            else:
                linesub = None
                line_nickname = None

            if newaccflag == 1:
                confirmresult = await self.confirmregisterdata(logintoken, username, password)
                if confirmresult == False:
                    totalresult = pg_general.Apiresult.success
                    clientdata = {
                        "result": 5
                    }
                    return totalresult, clientdata, serverdata
                # use username create member
                createresult, creatememberid = await self.createmember_by_username(deviceid, platform, logintoken,
                                                                                   username, password)
                if createresult == pg_general.Apiresult.success:
                    memberid = creatememberid
                    registerflag = 1  # 註冊成功
                elif createresult == pg_general.Apiresult.duplicationacc:
                    totalresult = pg_general.Apiresult.success
                    clientdata = {
                        "result": 4
                    }
                    return totalresult, clientdata, serverdata

            # 找memberid
            memberidresult, getmemberid, lasttoken, otherdata, loginmethod = await self.findmemberidandlasttoken(
                deviceid, fbid, logintoken, username, password, auserid, aauthcode, atoken, linesub)
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:login findmemberidandlasttoken memberidresult:{0}, loginmethod:{1}'.format(
                                    memberidresult, loginmethod))

            if memberidresult == pg_general.Apiresult.success:
                memberid = getmemberid
            elif memberidresult == pg_general.Apiresult.dbnodata:
                # 找不到memberid 新增會員
                createresult, creatememberid = await self.createmember(deviceid, platform,
                                                                       logintoken)  # create member by deviceid

                if createresult == pg_general.Apiresult.success:
                    memberid = creatememberid
                    registerflag = 1  # 註冊成功
            elif memberidresult == pg_general.Apiresult.accountfreeze:  # 帳號凍結
                totalresult = pg_general.Apiresult.success
                serverdata = {
                    "memberid": getmemberid
                }
                clientdata = {
                    "result": 3
                }
                return totalresult, clientdata, serverdata
            elif memberidresult == pg_general.Apiresult.accpasserror:  # 帳號或是密碼錯誤
                totalresult = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return totalresult, clientdata, serverdata
            elif memberidresult == pg_general.Apiresult.hasusernameacc:  # 使用　fb 登入的時候有查到　此　deviceid 已經綁定 username
                totalresult = pg_general.Apiresult.success
                clientdata = {
                    "result": 6
                }
                return totalresult, clientdata, serverdata
            elif memberidresult == pg_general.Apiresult.hasanotherfbid:  # 使用 fb 登入的時候有查到此 deviceid 已經綁過 fbid
                totalresult = pg_general.Apiresult.success
                clientdata = {
                    "result": 7
                }
                return totalresult, clientdata, serverdata
            elif memberidresult == pg_general.Apiresult.hasanotherlinesub:  # 使用Line登入的時候有查到此deviceid已經綁過line
                totalresult = pg_general.Apiresult.success
                clientdata = {
                    "result": 8
                }
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
            datalen, data = await self.getdbdata(logintoken, command, False, True)
            isavatarchanged = 0
            if datalen == 1:
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
            if fbtoken is not None and loginmethod == 2:
                if fbtoken != '':
                    fbuserresult, fbuserdata = await fbavatarobj.getfbdata(logintoken, memberid, fbtoken)
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
            updateloginresult, otherdict = await self.updatememberlogin(memberid, deviceid, fbid, fbtoken, fbavatar,
                                                                        fbnickname, fbemail,
                                                                        ip, platform, devicedescription, logintoken,
                                                                        lobbyserverip, region, region_sub, city,
                                                                        fcmtoken, otherdata, ver, rer, loginmethod,
                                                                        username, connecttype, isavatarchanged, auserid,
                                                                        aauthcode, atoken, linesub, line_nickname,
                                                                        linecode, lineaccesstoken)

            errormsg = otherdict.get('errormsg')
            if errormsg is not None:
                clientdata['errormsg'] = errormsg

            if linesub is not None:
                command = 'UPDATE member set lastdeviceid = "0" WHERE linesub = "{0}"'.format(linesub)
                updateresult = await self.updatedbdata(logintoken, command)

            if updateloginresult == pg_general.Apiresult.success:
                memberresult = pg_general.Apiresult.success

            if memberresult != pg_general.Apiresult.success:  # member 處理完後 先判斷一次 如果 memberresult 出錯則跳Except返回
                raise ValueError('1')

            getmemberinforesult, data = await self.getmemberinfo(redis_obj, logintoken, memberid)
            if getmemberinforesult != pg_general.Apiresult.success:  # getmemberinfo 如果出錯 except 返回
                raise ValueError('getmemberinfo error memberid:{0},logintoken:{1}'.format(memberid, logintoken))

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
            isbindline = data.get('isbindline')
            isbindphone = data.get('isbindphone')
            isbindacc = data.get('isbindacc')
            isfirstbuy = data.get('isfirstbuy')
            registrationdatetime = data.get('registrationdatetime')
            needtutorialflag = data.get('needtutorialflag')
            firstlogin = data.get('firstlogin')

            if None in [avatar, exppercent, credit, level, exptonextlevel, maxbet, isfirstbuy]:  # 都要有資料
                raise ValueError('4')

            firstbuymalldata = {}
            firstbuymalldata = await self.getfirstbuymallinfo(logintoken, memberid)

            firstbuymallinfo = firstbuymalldata.get('firstbuymallinfo')
            firstbuycountdownsec = firstbuymalldata.get('firstbuycountdownsec')
            firstbuytotalpercent = firstbuymalldata.get('firstbuytotalpercent')

            now = pg_general.getutcnow_datetime()
            firstbuydifftime = pg_general.converttype(
                firstbuycountdownsec - (now - registrationdatetime).total_seconds(), int)
            if firstbuydifftime < 0:
                firstbuydifftime = 0

            getdailybonusinforesult, data = await self.getdailybonusinfo(logintoken, memberid)
            if getdailybonusinforesult != pg_general.Apiresult.success:
                raise ValueError('11')

            isspin = data.get('isspin')
            if isspin is None:
                raise ValueError('12')

            # reddot 通知
            reddot = []
            getreddotresult, data = await self.getreddotinfo(logintoken, memberid)
            reddot = data

            # feedbacktype
            feedbacktyperesult, data = await self.getfeedbacktype(logintoken, memberid)
            if feedbacktyperesult != pg_general.Apiresult.success:
                raise ValueError('16')

            feedbacktype = data.get('feedbacktype')

            # get announcement
            getannoucementresult, data = await self.getannouncement()
            if getannoucementresult != pg_general.Apiresult.success:
                raise ValueError('17')

            announcementdict = data

            getspecialactionimageresult, data = await self.getspecialaction(logintoken, memberid)

            specialactionurlnew = []
            tempspecialactionurlnew = data.get('specialactionurlnew')
            if tempspecialactionurlnew is not None:
                tempspecialactionurlnew = tempspecialactionurlnew.strip()
                if len(tempspecialactionurlnew) > 0:
                    specialactionurlnew = tempspecialactionurlnew.split(',')

            totalresult = pg_general.Apiresult.success

            if channel == 0:
                channel = defaultchannelindex
                command = 'update member set channel="{0}" where memberid = "{1}"'.format(channel, memberid)
                await self.updatedbdata(logintoken, command)

            # 抓 setting.bindphonereward and weburl and firstbuyflag
            command = 'select mallserialcount,bindphonereward,weburl,firstbuyflag from setting2'
            datalen, data = await self.getdbdata(logintoken, command)

            bindphonereward = 0
            weburl = ''
            firstbuyflag = 0
            mallserialcount = 0
            if datalen == 1:
                bindphonereward = data.get('bindphonereward')
                weburl = data.get('weburl')
                firstbuyflag = data.get('firstbuyflag')
                mallserialcount = data.get('mallserialcount')

            lobbyaction = []
            # 抓 lobbyaction
            command = 'select * from lobbyaction'
            datalen, data = await self.getdbdata(logintoken, command, True)
            if datalen > 0:
                for item in data:
                    posid = item.get('posid')
                    picurl = item.get('picurl')
                    tempcontent = json.loads(item.get('content'))
                    actiontype = tempcontent.get('actiontype')
                    pageid = None
                    posindex = None
                    openurl = None
                    if actiontype == 0:  # internal page
                        pageid = tempcontent.get('pageid')
                        if pageid == 3:
                            posindex = tempcontent.get('posindex')
                    elif actiontype == 1:  # open url
                        openurl = tempcontent.get('openurl')

                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:tempcontent pageid:{0}, posindex = {1}'.format(pageid, posindex))

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

                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:lobbyaction lobbyaction:{0}'.format(lobbyaction))

            # 重新對 lobbyaction 排序
            if len(lobbyaction) > 0:
                lobbyaction = sorted(lobbyaction, key=lambda k: (k['posid']), reverse=False)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:lobbyaction_sort lobbyaction:{0}'.format(lobbyaction))

            # 強制關閉首購
            if firstbuyflag == 0:
                isfirstbuy = 0

            # 不需要首購, 強制時間設定 = 0
            if isfirstbuy == 0:
                firstbuydifftime = 0

            # 抓 actionnumbers  from action table
            nowutcdattime = pg_general.getutcnow_datetime()
            command = 'select distinct(actionnumber) as actionnumber from action where starttime <= "{0}" and (endtime>="{0}" or endtime is null) and listtype = "0" order by listtype,listpos,contentpos'.format(
                nowutcdattime)
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen > 0:
                actionnumbers = [item.get('actionnumber') for item in data]

            # 抓clubid用於俱樂部聊天室
            command = 'SELECT clubid FROM memberclub WHERE memberid = {0} ORDER BY clubid DESC;'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if data is None:
                clubid = 0
            else:
                clubid = data.get("clubid")

            if clubid is None:
                clubid = 0

            login_time = pg_general.datetimetostr_nof(pg_general.getutcnow_datetime())
            session_log_command = '''
            INSERT INTO `session_log` (`session_id`, `host_id`, `member_id`, `game_id`, `subgame_id`, `remote_ip`, `user_agent`, `create_time`, `left_time`)
            VALUES ('{}', '{}', '{}', '{}', 0, '{}', '', '{}', '{}');
            '''.format(logintoken + '==', env_setting.PS_HOST_NAME_S, memberid, 'LOBBY', ip, login_time, login_time)
            await self.slot_game_db.insertdbdata("slot_game_sb", session_log_command)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:login clubid:{0}, type(clubid) = {1}'.format(clubid, type(clubid)))

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
                "memberid": pg_general.converttype(memberid, str),
                "maxbet": maxbet,
                "exptonextlevel": exptonextlevel,
                "fblink": fblink,
                "announcement": announcementdict,
                "isbindfb": isbindfb,
                'isbindline': isbindline,
                "isbindacc": isbindacc,
                "isbindphone": isbindphone,
                "specialactionurlnew": [],
                # "specialactionurlnew": specialactionurlnew, # TODO 用回傳空串列取消大公告
                "channel": channel,
                "bindphonereward": bindphonereward,
                "weburl": weburl,
                # "lobbyaction": [],            # TODO 用回傳空串列取消側欄公告
                "lobbyaction": lobbyaction,
                "isfirstbuy": isfirstbuy,
                "firstbuycountdownsec": firstbuydifftime,
                "firstbuytotalpercent": firstbuytotalpercent,
                "firstbuymallinfo": firstbuymallinfo,
                "actionnumbers": actionnumbers,
                # "actionnumbers": actionnumbers, #TODO 回傳空串列取消活動公告和紅點
                "mallserialcount": mallserialcount,
                "needtutorialflag": needtutorialflag,
                "firstlogin": firstlogin,
                "clubid": clubid
            }

            await self.write_redis_member_join_channel_future(redis_obj, memberid, channel)
            await self.write_redis_member_join_clubchannel_future(redis_obj, memberid, clubid)

            serverdata = {
                "memberid": memberid
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:login ValueError:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:login exception:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:login totalresult:{0}, clientdata:{1}, serverdata:{2}, logintoken:{3}'.format(
                                    totalresult, clientdata, serverdata, logintoken))

            return totalresult, clientdata, serverdata

    async def _send_post_to_get_token(self, code):
        try:
            send_param = {}
            line_login_get_token_url = 'https://api.line.me/oauth2/v2.1/token'
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            grant_type = 'authorization_code'
            redirect_uri = env_setting.SD555_LOBBY_URL
            client_id = '1657282971'
            client_secret = 'bfe61d630d44308d2efee72b8a6edf80'
            send_param = {
                "grant_type": grant_type,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code
            }

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:_send_post_to_get_token send_param:{0}'.format(send_param))

            async with aiohttp.ClientSession() as session:
                async with session.post(line_login_get_token_url, data=send_param, headers=headers) as response:
                    if response.status != 200:
                        raise ValueError('send request to get line token error {}'.format(response.status))

                    lineloginresult = await response.text()

                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'pg_asqldb:_send_post_to_get_token lineloginresult:{0}'.format(lineloginresult))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:linelogincallback ValueError:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:linelogincallback Exception:{0}'.format(format_exc()))

        return lineloginresult

    async def linelogincallback(self, code, state):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linelogincallback code:{0}, status:{1}'.format(code, state))

            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            lineloginresult = await self._send_post_to_get_token(code)
            lineloginresult = json.loads(lineloginresult)
            id_token = lineloginresult.get('id_token')

            options = {'verify_signature': False}
            encoded = id_token

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linelogincallback encode:{0}, type:{1}'.format(encoded, type(encoded)))

            id_token_decode = jwt.decode(encoded, "secret", audience="1657282971", algorithms=["HS256"],
                                         options=options)

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linelogincallback jwt.decode:{0}'.format(id_token_decode))

            clientdata = id_token_decode
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:linelogincallback ValueError:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:linelogincallback Exception:{0}'.format(format_exc()))

        return result, clientdata

    async def get_use_agreement(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:get_use_agreement')
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'SELECT useagreement FROM setting2'
            datalen, data = await self.getdbdata('get_use_agreement', command)

            clientdata['useagreement'] = data.get('useagreement') if datalen != 0 else ''

            result = pg_general.Apiresult.success
        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_use_agreement ValueError:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_use_agreement Exception:{0}'.format(format_exc()))

        return result, clientdata

    async def get_privacy_agreement(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:get_privacy_agreement')
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'SELECT privacyagreement FROM setting2'
            datalen, data = await self.getdbdata('get_privacy_agreement', command)

            clientdata['privacyagreement'] = data.get('privacyagreement') if datalen != 0 else ''

            result = pg_general.Apiresult.success
        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_privacy_agreement ValueError:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_privacy_agreement Exception:{0}'.format(format_exc()))

        return result, clientdata

    async def getfeedbacktype(self, logintoken, memberid):
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
            "feedbacktype": feedbacktype
        }
        result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:gettipsinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                      logintoken,
                                                                                                      clientdata))
        return result, clientdata

    async def findmemberidandlasttoken(self, deviceid, fbid, logintoken, username, password, auserid, aauthcode, atoken,
                                       linesub):
        """
        找memberid和最後登入的token
        從DB member 撈取memberid和logintoken
        membeid的規則 fbid優先度大於deviceid
        因此先利用fbid反查memberid
        找不到時再用deviceid反查memberid
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:findmemberid logintoken:{0}, deviceid:{1}, fbid:{2},username:{3},password:{4},auserid:{5},aauthcode:{6},atoken:{7},linesub:{8}'.format(
                                    logintoken, deviceid, fbid, username, password, auserid, aauthcode, atoken,
                                    linesub))
            result = pg_general.Apiresult.connectdberror
            memberid = None
            lasttoken = None
            otherdata = {}
            isbindfb = None

            loginmethod = None  # 1: username , 2: fb , 3: deviceid , 4: app sign in , 5: line login

            if username is not None:
                username = username.strip()
            if password is not None:
                password = password.strip()

            # 找memberid(username>fbid>linesub>apple sign in>deviceid)
            if None not in [username, password]:
                # user username & password to find memberid
                command = 'select * from member where username ="{0}"'.format(username)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                if datalen != 1:
                    result = pg_general.Apiresult.accpasserror
                    return result, memberid, lasttoken, otherdata
                elif datalen < 0:
                    result = pg_general.Apiresult.connectdberror
                    raise ValueError('get data error')
                else:
                    userpassword = data.get('password')
                    enable = data.get('enable')
                    getmemberid = pg_general.converttype(data.get('memberid'), int)
                    lasttoken = data.get('logintoken')
                    isbindfb = data.get('isbindfb')
                    isbindline = data.get('isbindline')

                    if enable != 1:  # 帳戶凍結
                        result = pg_general.Apiresult.accountfreeze
                        memberid = getmemberid
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if userpassword != password:  # 密碼錯誤
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
                    isbindline = data.get('isbindline')

                    if enable != 1:  # 帳戶凍結
                        result = pg_general.Apiresult.accountfreeze
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if getmemberid is not None:
                        memberid = getmemberid
                        result = pg_general.Apiresult.success
                        loginmethod = 2
            elif linesub is not None:
                # 用linesub找memberid
                command = 'select * from member where linesub = "{0}"'.format(linesub)
                datalen, data = await self.getdbdata(logintoken, command)

                if datalen == 1:
                    enable = data.get('enable')
                    getmemberid = pg_general.converttype(data.get('memberid'), int)
                    lasttoken = data.get('logintoken')
                    isbindfb = data.get('isbindfb')
                    isbindline = data.get('isbindline')

                    if enable != 1:  # 帳戶凍結
                        result = pg_general.Apiresult.accountfreeze
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if getmemberid is not None:
                        memberid = getmemberid
                        result = pg_general.Apiresult.success
                        loginmethod = 5
                else:
                    result = pg_general.Apiresult.dbnodata
                    return result, memberid, lasttoken, otherdata, loginmethod
            elif None not in [auserid, aauthcode, atoken]:  # apple sign in
                # 確認 data 正確性
                confirmresult, confirmdata = await applesignin.apple_sign_in_check(logintoken, auserid, atoken,
                                                                                   aauthcode)

                if confirmresult == False:
                    result = pg_general.Apiresult.othererror
                    return result, memberid, lasttoken, otherdata, loginmethod

                command = 'select * from member where auserid="{0}"'.format(auserid)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen == 1:
                    enable = data.get('enable')
                    getmemberid = pg_general.converttype(data.get('memberid'), int)
                    lasttoken = data.get('logintoken')
                    isbindfb = data.get('isbindfb')

                    if enable != 1:  # 帳戶凍結
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
                    isbindline = data.get('isbindline')

                    confirmfbid = data.get('fbid')
                    if enable != 1:  # 凍結
                        result = pg_general.Apiresult.accountfreeze
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if confirmusername is not None and confirmusername != '' and fbid is not None:  # 找不到 fbid 但是有找到 deviceid and username 表示之前有使用 username 綁過此帳號
                        result = pg_general.Apiresult.hasusernameacc
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if confirmfbid is not None and fbid is not None:
                        if len(confirmfbid) > 1:
                            result = pg_general.Apiresult.hasanotherfbid
                            return result, memberid, lasttoken, otherdata, loginmethod

                    confirmlinesub = data.get('linesub')
                    if confirmusername is not None and confirmusername != '' and confirmlinesub is not None:  # 找不到 linesub 但是有找到 deviceid and username 表示之前有使用 username 綁過此帳號
                        result = pg_general.Apiresult.hasusernameacc
                        return result, memberid, lasttoken, otherdata, loginmethod

                    if confirmlinesub is not None and linesub is not None:
                        if len(confirmfbid) > 1:
                            result = pg_general.Apiresult.hasanotherlinesub
                            return result, memberid, lasttoken, otherdata, loginmethod

                    if getmemberid is not None:
                        memberid = getmemberid
                        result = pg_general.Apiresult.success
                        loginmethod = 3

                elif datalen == 0:
                    result = pg_general.Apiresult.dbnodata
            if None not in [memberid]:  # 有找到加入otherdata
                otherdata = {
                    "isbindfb": isbindfb,
                    "isbindline": isbindline
                }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:findmemberid ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:findmemberid exception:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:findmemberid result:{0}, memberid:{1}, logintoken:{2},otherdata:{3}'.format(
                                    result, memberid, logintoken, otherdata))
            return result, memberid, lasttoken, otherdata, loginmethod

    async def createmember_by_username(self, deviceid, platform, logintoken, username, password):
        """
        建立新會員
        DB member insert 一筆會員資料
        有memberid後再建立其他與會員相關的table (參照 function createothermembertable)
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:createmember logintoken:{0}, deviceid:{1}, platform:{2},username:{3},password:{4}'.format(
                                logintoken, deviceid, platform, username, password))

        result = pg_general.Apiresult.connectdberror
        memberid = None

        now = pg_general.getutcnow()
        nowdatetime = pg_general.strtodatetime(now)
        yesterday = nowdatetime - timedelta(days=1)

        # TODO tutorialbetfinish 這個欄位是為了要跳過新手教學而加的，之後若要跳教學的話再刪除
        insertkey = 'registrationdatetime, lastlogintime, adcountdown, lastdeviceid, platform, logintoken, lastchoosecamp, silvercredit, roomcard, tutorialbetfinish'
        insertvalue = ' "{0}", "{0}", "{0}", "{1}", "{2}", "{3}", "{4}", "{5}", {6}, {7}'.format(now, deviceid,
                                                                                                 platform, logintoken,
                                                                                                 yesterday, 1000000, 20,
                                                                                                 3)

        insertkey = insertkey + ',username,password'
        insertvalue = insertvalue + ',"{0}","{1}"'.format(username, password)

        command = 'insert into member({0}) values({1})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            memberid = index

            # 改一個預設的暱稱
            await pg_namesample.makeanewname(self, memberid)

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
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:createmember logintoken:{0}, deviceid:{1}, platform:{2}'.format(logintoken,
                                                                                                       deviceid,
                                                                                                       platform))

        result = pg_general.Apiresult.connectdberror
        memberid = None

        now = pg_general.getutcnow()
        nowdatetime = pg_general.strtodatetime(now)
        yesterday = nowdatetime - timedelta(days=1)

        # TODO tutorialbetfinish 這個欄位是為了要跳過新手教學而加的，之後若要跳教學的話再刪除
        insertkey = 'registrationdatetime, lastlogintime, adcountdown, lastdeviceid, platform, logintoken, lastchoosecamp, silvercredit, roomcard, tutorialbetfinish'
        insertvalue = ' "{0}", "{0}", "{0}", "{1}", "{2}", "{3}", "{4}", "{5}", {6}, {7}'.format(now, deviceid,
                                                                                                 platform, logintoken,
                                                                                                 yesterday, 1000000, 20,
                                                                                                 3)

        command = 'insert into member({0}) values({1})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            memberid = index

            # 改一個預設的暱稱
            await pg_namesample.makeanewname(self, memberid)

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
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:createothermembertable logintoken:{0}, memberid:{1}, nowdatetime:{2}'.format(
                                logintoken, memberid, nowdatetime))

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
        command = 'insert into memberfreecoins (memberid,lastgettime) values ( {0},"{1}")'.format(memberid, yesterday)
        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            insertcount += 1

        if insertcount == 3:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:createothermembertable result:{0}, logintoken{1}'.format(result, logintoken))
        return result

    async def updatememberlogin(self, memberid, deviceid, fbid, fbtoken, fbavatar, fbnickname, fbemail, ip, platform,
                                devicedescription, logintoken, lobbyserverip, region, region_sub, city, fcmtoken,
                                otherdata, ver, rer, loginmethod, username, connecttype, isavatarchanged, auserid,
                                aauthcode, atoken, linesub, line_nickname, linecode, lineaccesstoken):
        """
        更新member登入資料
        DB member 更新member的logintoken 登入時間 登入裝置....
        存入 fbavatar , fbnickname into member(avatar,nickname)
        DB memberloginlog 新增一筆會員登入的時間
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:updatememberlogin logintoken:{0}, memberid:{1}, deviceid:{2}, fbid:{3}, ip:{4},' \
                            ' platform:{5}, devicedescription:{6},lobbyserverip:{7},region:{8},region_sub:{9},city:{10},fbtoken:{11},fbavatar:{12},fbnickname:{13},fcmtoken:{14},linesub:{15},line_nickname:{16}, linecode:{17}, loginmethod:{18}, lineaccesstoken:{19}'.
                            format(logintoken, memberid, deviceid, fbid, ip, platform, devicedescription, lobbyserverip,
                                   region, region_sub, city, fbtoken, fbavatar, fbnickname, fcmtoken, linesub,
                                   line_nickname, linecode, loginmethod, lineaccesstoken))
        result = pg_general.Apiresult.connectdberror
        await asyncio.sleep(0)
        otherdict = {}

        isbindfb = 0
        isbindline = 0

        if otherdata != {}:
            isbindfb = otherdata.get('isbindfb')
            isbindline = otherdata.get('isbindline')

        if line_nickname:
            command = 'SELECT * from member WHERE nickname = "{0}"'.format(line_nickname)
            datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

            if datalen > 1:
                await pg_namesample.makeanewname(self, memberid)
                otherdict['errormsg'] = 'The nickname is in used, create a random nickname'

        now = pg_general.getutcnow()
        updatestr = 'lastlogintime="{0}", platform="{1}", logintoken="{2}",lobbyserverip="{3}"'.format(now, platform,
                                                                                                       logintoken,
                                                                                                       lobbyserverip)
        insertkey = 'memberid, logintime, platform, deviceid, logintoken,lobbyserverip'
        insertvalue = '{0}, "{1}", {2}, "{3}", "{4}","{5}"'.format(memberid, now, platform, deviceid, logintoken,
                                                                   lobbyserverip)

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

        if linesub is not None:
            updatestr = updatestr + ', linesub="{0}"'.format(linesub)
            updatestr = updatestr + ', isbindline="1"'

        if line_nickname is not None:
            updatestr = updatestr + ', nickname="{0}"'.format(line_nickname)

        if linecode is not None:
            updatestr = updatestr + ', linecode="{0}"'.format(linecode)

        if lineaccesstoken is not None:
            updatestr = updatestr + ', line_access_token="{0}"'.format(lineaccesstoken)

        if isavatarchanged == 0:  # 有改過不更換 avatar
            if fbavatar is not None:
                updatestr = updatestr + ',avatar="{0}"'.format(fbavatar)
            else:  # 如果沒有 fbavatar 表示沒有綁定 fb , avatar 設定 default avatar
                if isbindfb == 0:
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
            updatestr = updatestr + ',region="{0}"'.format(pg_general.converttype(region, str).lower())

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
            insertvalue = insertvalue + ',"{0}","{1}"'.format(loginmethod, username)

        if fbtoken is not None and fbid is not None:
            insertkey = insertkey + ',fbtoken,fbid'
            insertvalue = insertvalue + ',"{0}","{1}"'.format(fbtoken, fbid)

        if connecttype is not None:
            insertkey = insertkey + ',connecttype'
            insertvalue = insertvalue + ',"{0}"'.format(connecttype)

        # 更新member 資料表
        command = 'update member set {0} where memberid = "{1}"'.format(updatestr, memberid)
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:login updatememberlogin command:{0}'.format(command))
        updateresult = await self.updatedbdata(logintoken, command)

        # 新增memberloginlog 記錄
        command = 'insert into memberloginlog({0}) values({1})'.format(insertkey, insertvalue)
        insertresult, index = await self.insertdbdata(logintoken, command)

        if updateresult == True and insertresult == True:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:updatememberlogin result:{0}, logintoken:{1}'.format(result, logintoken))
        return result, otherdict

    async def updatememberlogout(self, memberid, logintoken, redis_obj=None):
        """
        更新member登出資料
        DB member 更新member的最後登出時間  及清空logintoken
        DB memberloginlog 更新登出時間
        清除玩家組房相關 redis
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:updatememberlogout logintoken:{0}, memberid:{1}'.format(logintoken,
                                                                                                   memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            now = pg_general.getutcnow()

            # 更新member 資料表
            command = 'update member set lastlogouttime="{0}",logintoken=null where memberid = "{1}"'.format(now,
                                                                                                             memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            # 更新memberloginlog 記錄
            command = 'select * from memberloginlog where memberid = "{0}" and logintoken = "{1}"'.format(memberid,
                                                                                                          logintoken)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                index = pg_general.converttype(data.get('index'), int)
                command = 'update memberloginlog set logouttime="{0}" where memberloginlog.index = "{1}"'.format(now,
                                                                                                                 index)
                updateresult = await self.updatedbdata(logintoken, command)
                if updateresult == True:
                    result = pg_general.Apiresult.success

            if redis_obj is not None:
                room_key = await redis_obj.hget('play_room_record', memberid)

                if room_key is not None:
                    if 'club' in room_key:
                        club_id = room_key.split('_')[1]
                        room_id = room_key.split('_')[3]
                    else:
                        club_id = ''
                        room_id = room_key.split('_')[2]

                    msg = '''pg_asqldb:updatememberlogout room_key:{}, club_id:{}, room_id:{}
                    '''.format(room_key, club_id, room_id)
                    pg_general.writelog(pg_general.PG_LogerLevel.error, msg)

                    data = await redis_obj.hgetall(room_key)

                    if not data:
                        raise ValueError('no room info')

                    room_status = data.get('status')
                    msg = '''pg_asqldb:updatememberlogout room_status:{}
                                        '''.format(room_status)
                    pg_general.writelog(pg_general.PG_LogerLevel.error, msg)

                    if room_status == 'wait':
                        result, clientdata = await self.leave_room(memberid, logintoken, redis_obj, club_id, room_id)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatememberlogout Except:{0}'.format(format_exc()))
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:updatememberlogout result:{0}, logintoken:{1}'.format(result, logintoken))
        return result, clientdata

    async def getmemberinfo(self, redis_obj, logintoken, memberid, param_memberid=None):
        """
        取得玩家資料結果
        DB member 撈取會員基本資料 根據member.level 關聯DB levelinfo 該會員等級的資料
        玩家經驗值百分比需根據DB member 的exp 和levelinfo的newlevelexp 進行運算
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getmemberinfo logintoken:{0}, memberid:{1}'.format(logintoken, memberid))
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
                update_result = await self.updatedbdata(logintoken, command)

            # 抓取 setting2.errordescription for changenickname error description
            command = 'select errordescription from setting2'
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:
                errordescription = data.get('errordescription')
                if errordescription is not None:
                    errordescription = json.loads(errordescription)
                else:
                    errordescription = {}

            command = 'select member.*, levelinfo.newlevelexp, levelinfo.maxbet from member, levelinfo where member.memberid = "{0}" and member.level = levelinfo.level'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command, False, True)

            if datalen == 1:
                exp = pg_general.converttype(data.get('exp'), int)
                newlevelexp = pg_general.converttype(data.get('newlevelexp'), int)
                exppercent = int((exp / newlevelexp) * 100)
                exppercent = 100 if exppercent > 100 else exppercent
                now = pg_general.strtodatetime(pg_general.getutcnow())

                maxbet = pg_general.converttype(data.get("maxbet"), int)
                exptonextlevel = newlevelexp - exp

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
                if username is not None and username != '0' and username != '':
                    isbindacc = True

                registrationdatetime = data.get('registrationdatetime')

                tutorialbetfinish = data.get('tutorialbetfinish')
                if tutorialbetfinish == 0:
                    needtutorialflag = 1
                else:
                    needtutorialflag = 0

                    # 抓取今日總押分 金幣與銀幣
                twtodaydatestr = pg_general.get_tw_date_str()

                daybet = await redis_obj.hget('daybet_{}'.format(twtodaydatestr), '{}'.format(memberid))
                if daybet is None:
                    daybet = 0
                daybets = await redis_obj.hget('daybets_{}'.format(twtodaydatestr), '{}'.format(memberid))
                if daybets is None:
                    daybets = 0

                clientdata = {
                    "nickname": pg_general.converttype(data.get('nickname'), str),
                    "avatar": pg_general.converttype(data.get('avatar'), str),
                    "level": pg_general.converttype(data.get('level'), int),
                    "card": data.get('card'),
                    "exppercent": exppercent,
                    # TODO 先將金幣欄位改成回傳房卡數量，可減少前端作業量，待後續更正
                    "credit": pg_general.converttype(data.get('roomcard'), int),
                    "silvercredit": pg_general.converttype(data.get('silvercredit'), int),
                    "biggestmultiplier": pg_general.converttype(data.get('biggestmultiplier'), int),
                    "biggestwins": pg_general.converttype(data.get('biggestwins'), int),
                    "totaltopmultiplier": pg_general.converttype(data.get('totaltopmultiplier'), int),
                    "totaltopwin": pg_general.converttype(data.get('totaltopwin'), int),
                    "isbindfb": pg_general.converttype(data.get('isbindfb'), bool),
                    "isbindline": pg_general.converttype(data.get('isbindline'), bool),
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
                    "daybets": daybets,
                    "firstlogin": data.get("firstlogin")
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
                                'pg_asqldb:getmemberinfo result:{0}, clientdata:{1}, logintoken:{2}'.format(result,
                                                                                                            clientdata,
                                                                                                            logintoken))
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
                                'pg_asqldb:updateprofile logintoken:{0}, memberid:{1}, nickname:{2}'.format(logintoken,
                                                                                                            memberid,
                                                                                                            nickname))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            transformed_nickname = HanziConv.toTraditional(nickname)

            # 檢查格式 檢查是否有符號與英文數字 以及是否有簡體字
            if pg_general.check_english(nickname) == False or len(
                    nickname) > 16:  # or nickname != transformed_nickname:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": "2"
                }
                raise ValueError('has simplied chinese or number')

            # 先找是否可以 change nickname
            command = 'select canchangenickname from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen < 1:
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
                command = 'select nickname from member where nickname = "{0}" and memberid != "{1}"'.format(nickname,
                                                                                                            memberid)
                datalen, data = await self.getdbdata(logintoken, command)
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
                                'pg_asqldb:updateprofile result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                            logintoken,
                                                                                                            clientdata))

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
                      ' and member.memberid = memberdailybonus.memberid and dailybonusInfo.dailybonusgroup = member.card and dailybonusInfo.promotionid = promotion.promotionindex'.format(
                memberid)

            datalen, data = await self.getdbdata(logintoken, command, True, True)
            if datalen == 12:
                lastspintime_utctime = data[0].get("lastspintime")
                if lastspintime_utctime is not None:
                    nowdatetime_localtime = pg_general.get_local_datetime()  # tw time
                    if pg_general.get_utc_to_local_datetime(
                            lastspintime_utctime).date() != nowdatetime_localtime.date():
                        isspin = False
                    else:
                        isspin = True

                for item in data:
                    promotiontype = pg_general.converttype(item.get("promotiontype"), int)
                    awardcontent = pg_general.converttype(item.get("content"), int)
                    posid = pg_general.converttype(item.get('posid'), int)
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
                datalen, data = await self.getdbdata(logintoken, command)

                if datalen == 1:
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
                                'pg_asqldb:getdailybonusinfo result:{0}, clientdata:{1}, logintoken:{2}'.format(result,
                                                                                                                clientdata,
                                                                                                                logintoken))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getdailybonusinfo except:{0}, clientdata:{1}, logintoken:{2}, result:{3}'.format(
                                    e,
                                    clientdata,
                                    logintoken, result))
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
        command = 'select dailybonusflag from setting2'
        datalen, data = await self.getdbdata(logintoken, command)
        if datalen == 1:
            dailybonusflag = data.get('dailybonusflag')
            if dailybonusflag == 0:
                return result, clientdata

        command = 'select memberdailybonus.*, member.credit,member.silvercredit,member.card, promotion.*, dailybonusInfo.* from memberdailybonus, member, promotion, dailybonusInfo where memberdailybonus.memberid = "{0}" ' \
                  ' and member.memberid = memberdailybonus.memberid and promotion.promotionindex = dailybonusInfo.promotionid and dailybonusInfo.dailybonusgroup = member.card '.format(
            memberid)
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
                    if type == 0:  # 金幣
                        aftercredit = credit + award
                    elif type == 1:  # 銀幣
                        aftersilvercredit = silvercredit + award

                    now = pg_general.getutcnow()
                    # 測試使用 lastspin 改為 2000-01-01 00:00:00
                    if env_setting.PRODUCTION_MODE == False:
                        now = pg_general.strtodatetime('2000-01-01 00:00:00.00')

                    command = 'update member, memberdailybonus set member.credit= "{0}",member.silvercredit="{3}", memberdailybonus.lastspintime = "{1}" where member.memberid = "{2}" and memberdailybonus.memberid = "{2}"'.format(
                        aftercredit, now_utctime, memberid, aftersilvercredit)
                    updateresult = await self.updatedbdata(logintoken, command)

                    if updateresult == True and None not in [award, aftercredit, aftersilvercredit, rngindex]:
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
                            "amount": award if type == 0 else 0,
                            "amount_silver": award if type == 1 else 0,
                            "otherdata": 'spindailybonus'
                        }
                        asyncio.ensure_future(self.writetransactionlog(logintoken, param))


                    else:
                        result = pg_general.Apiresult.othererror
        else:
            result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:spindailybonus result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                         logintoken,
                                                                                                         clientdata))
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

        command = 'select memberpiggyinfo.piggycredit,setting2.minipiggytake,setting2.piggyshowamount from memberpiggyinfo,setting2 where memberpiggyinfo.memberid = "{0}"'.format(
            memberid)

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
                            'pg_asqldb:getpiggyinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                       logintoken,
                                                                                                       clientdata))
        return result, clientdata

    async def getmallinfo(self, logintoken, memberid, mode):
        """
        取得商城資訊
        從DB member 找isfirstbuy 判斷此玩家是否為首購
        再決定找的商城種類(一般或首購)
        從DB mall的 malltype關聯 DB mallinfo的malltype 取得商城資訊
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getmallinfo logintoken:{0}, memberid:{1}:mode:{2}'.format(logintoken, memberid,
                                                                                                 mode))
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
                    "credit": pg_general.converttype(tempdata.get("point"), int),  # 轉換成 cent * 100
                    "cash": pg_general.converttype(tempdata.get("cash"), int),
                    "shopid": pg_general.converttype(tempdata.get("shopid"), str),
                    "flag": pg_general.converttype(tempdata.get('tag'), int)

                }

                # 檢查是否有值為空
                if None not in tempmallcontent.values():
                    mallcontent.append(tempmallcontent)

            # get mallserialcount from seting2
            command = 'select mallserialcount from setting2'
            datalen, data = await self.getdbdata('get mallserialcount', command)
            if datalen == 1:
                mallserialcount = data.get('mallserialcount')

            if len(mallcontent) > 0:
                clientdata = {
                    "mallcontent": mallcontent,
                    "mallserialcount": mallserialcount
                }

                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.othererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getmallinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                      logintoken,
                                                                                                      clientdata))
        return result, clientdata

    async def shopping(self, redis_obj, logintoken, memberid, cardinfo, jsoncontent, mode):
        """
        所有商城功能集中在這邊處理
        """
        # shopid =  'secretoffer_lv_01'
        # result_shop, ret_data = await self.secretoffermall(logintoken, memberid, shopid)

        try:
            MALL_SHOP_ID = ['shopmall_lv_01', 'shopmall_lv_02', 'shopmall_lv_03', 'shopmall_lv_04', 'shopmall_lv_05',
                            'shopmall_lv_06']
            PIGGY_SHOP_ID = ['piggy_lv_01', 'piggy_lv_02', 'piggy_lv_03', 'piggy_lv_04', 'piggy_lv_05', 'piggy_lv_06',
                             'piggy_lv_07', 'piggy_lv_08', 'piggy_lv_09', 'piggy_lv_10']
            SECRETOFFER_SHOP_ID = ['secretoffer_lv_01', 'secretoffer_lv_02', 'secretoffer_lv_03', 'secretoffer_lv_04',
                                   'secretoffer_lv_05']

            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                'pg_asqldb:shopping logintoken:{0}, memberid:{1}, jsoncontent:{2},mode:{3}'.format(
                                    logintoken, memberid, jsoncontent, mode))
            result = pg_general.Apiresult.connectdberror
            clientdata = {
                "result": 1,
                "buycredit": 0,
                "credit": 0,
                "content": {}
            }

            # 確認資料正確性
            jsondata = jsoncontent.get('data')
            if jsondata is None:
                raise ValueError('jsondata is None')

            platform = jsondata.get('platform')  # 0: ios , 1: android
            shopid = jsondata.get('shopid')
            if None in [platform, shopid] or platform not in [0, 1]:
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

                if malltype == -1:  # shopid 不正確
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        "shopid:{} is not in any SHOP_ID".format(shopid))
                    raise ValueError('shopid is wrong')

            elif version == 'new':
                # integer
                # 商城
                # number
                # 0: 一般商城, 1: luckybuy, 2: piggy, 3: 神秘商人, 4: Super Wheel
                if num == 0:  # normal mall
                    malltype = 0
                elif num == 3:  # secret offer
                    malltype = 3
                elif num == 5:  # 首購商城
                    malltype = 5
                else:
                    raise ValueError('shop num is wrong')

            jsoncontent_2 = jsondata.get('jsoncontent')
            if jsoncontent_2 is None:
                raise ValueError('jsoncontent_2 is None')

            internal_shopid = jsoncontent_2.get('id')
            if shopid != internal_shopid:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    "shopid:{} is not as same as content's shopid:{}".format(shopid, internal_shopid))
                raise ValueError('internal shopid error')

            if platform == 0:  # ios

                receipt_data = jsoncontent_2.get('receiptCipheredPayload')
                currency_code = jsoncontent_2.get('currencyCode')
                transaction_id = pg_general.converttype(jsoncontent_2.get('transactionID'), str)
                price = jsoncontent_2.get('price')


            else:  # android
                receipt_data = jsoncontent_2.get('receiptCipheredPayload')
                currency_code = jsoncontent_2.get('currencyCode')
                transaction_id = pg_general.converttype(jsoncontent_2.get('transactionID'), str)
                price = jsoncontent_2.get('price')
                receipt = jsoncontent_2.get('receipt')
                receipt = json.loads(receipt)

            if None in [receipt_data, currency_code, transaction_id, price]:  # receipt data is 為空
                raise ValueError('receiptCipheredPayload data is None')

            if platform == 1:
                if receipt is None:
                    raise ValueError('android receipt data is None')
                purchaseToken = receipt.get('purchaseToken')
                if purchaseToken is None:
                    raise ValueError('android purchaseToken data is None')

            statuscode = -1
            # server 驗證流程
            if platform == 0:  # ios
                url = IOS_IAP_VALIDATE_URL
                production_verify_flag = False
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json={"receipt-data": receipt_data}) as response:
                        # response = await session.post(url, json={"receipt-data":receipt_data})
                        if response.status != 200:
                            result = pg_general.Apiresult.othererror
                            raise ValueError('iap validate error')
                        response_data = await response.text()
                        response_data = json.loads(response_data)
                        statuscode = response_data.get('status')
                        if statuscode == 0:
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

                    if statuscode != 0 and production_verify_flag == False:  # change to verify sandbox
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

            else:  # android
                response_data = GOOGLE_IAP_SERVICE.purchases().products().get(packageName=GOOGLE_IAP_BUNDLE_ID,
                                                                              productId=shopid,
                                                                              token=purchaseToken).execute()
                if response_data is None:
                    raise ValueError('result_google_iap_validate data is None')
                if len(response_data) == 0:
                    raise ValueError('result_google_iap_validate data is NULL')

                statuscode = response_data.get('purchaseState')

            # 確認此單是否已經重複
            command = 'select transactionid from mallhistory where transactionid = "{0}"'.format(transaction_id)
            datalen, data = await self.getdbdata(logintoken, command, True, True)
            if datalen > 0:
                clientdata = {
                    "result": 2
                }
                result = pg_general.Apiresult.success
                return result, clientdata

            if statuscode != 0:
                await self.write_mall_history(logintoken, memberid, shopid, price, transaction_id, malltype, platform,
                                              statuscode, receipt_data, currency_code, None)
                raise ValueError('receipt status != 0')

            await self.write_mall_history(logintoken, memberid, shopid, price, transaction_id, malltype, platform,
                                          statuscode, receipt_data, currency_code, response_data)
            if malltype == 0:  # normal mall
                result_shop, ret_data = await self.normalmall(logintoken, memberid, shopid, mode, transaction_id)
            elif malltype == 3:  # secret offer mall
                result_shop, ret_data = await self.secretoffermall(logintoken, memberid, shopid)
            elif malltype == 5:
                result_shop, ret_data = await self.firstbuymall(logintoken, memberid, shopid)
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
                "type": 0 if platform == 0 else 1,
                "amount": pg_general.converttype(ret_data.get('buycredit'), int) * 100  # 轉成金幣
            }
            asyncio.ensure_future(self.writegiftfreeze(logintoken, param))

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
                asyncio.ensure_future(
                    self.buycardlevelup_future(apporweb, logintoken, memberid, card, redis_obj, cardinfo))

            if result_shop == pg_general.Apiresult.success:
                clientdata = {
                    "result": 0,
                    "buycredit": ret_data.get('buycredit'),
                    "credit": ret_data.get('credit'),
                    "content": ret_data.get('content'),
                    "mode": mode
                }
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.othererror


        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:shopping ValueError:{0},memberid:{1},jsoncontent:{2}'.format(format_exc(),
                                                                                                        memberid,
                                                                                                        jsoncontent))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:shopping Exception:{0},memberid:{1},jsoncontent:{2}'.format(format_exc(),
                                                                                                       memberid,
                                                                                                       jsoncontent))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:shopping result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                       logintoken,
                                                                                                       clientdata))
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
        command = 'select * from memberinbox, promotion where memberinbox.memberid = "{0}" and memberinbox.promotionid = promotion.promotionindex order by memberinbox.index desc;'.format(
            memberid)

        datalen, data = await self.getdbdata(logintoken, command, True)
        if datalen > 0:
            now = pg_general.strtodatetime(pg_general.getutcnow())
            history_mail_count = 0

            for tempdata in data:
                promotiontype = pg_general.converttype(tempdata.get("promotiontype"), int)
                promotionid = pg_general.converttype(tempdata.get("promotionid"), int)
                # dateline = pg_general.strtodatetime_nof(tempdata.get("dateline")) # utc time
                dateline = tempdata.get("dateline")
                send_datetime = tempdata.get("sendtime")

                if dateline is None and promotionid == 6:
                    countdownseconds = 1

                else:
                    countdownseconds = pg_general.converttype((dateline - now).total_seconds(), int)
                receivestate = pg_general.converttype(tempdata.get("receivestate"), int)
                inboxtype = None
                award = 0
                awardtype = 1
                gameid = ""

                if None not in [promotiontype, dateline, countdownseconds, receivestate]:
                    if promotiontype == 0:  # 金幣 參照 promotion content
                        inboxtype = 0
                        awardtype = 0
                        award = pg_general.converttype(tempdata.get("content"), int)

                    elif promotiontype == 1:  # free game 還沒完成
                        inboxtype = 1
                        content = json.loads(tempdata.get("content"))
                        award = content.get("freespin")
                        gameid = content.get("gameid")
                    elif promotiontype == 4:  # 金幣直接抓 memberinbox credit_award
                        award = tempdata.get('credit_award')
                        awardtype = 0
                        inboxtype = 0
                    elif promotiontype == 5:  # 銀幣 參照 promotion content
                        inboxtype = 0
                        award = pg_general.converttype(tempdata.get("content"), int)
                        awardtype = 1
                    elif promotiontype == 6:  # 免費轉輪
                        inboxtype = 3
                        award = 0
                        awardtype = 0
                    elif promotiontype == 7:  # 銀幣 直接抓 memberinbox credit_award
                        inboxtype = 0
                        award = tempdata.get('credit_award')
                        awardtype = 1
                    elif promotiontype == 8:  # 金幣直接抓 memberinbox credit_award
                        award = tempdata.get('credit_award')
                        awardtype = 2
                        inboxtype = 0

                    if receivestate == 1 and countdownseconds <= 0:
                        receivestate = -1

                    # 將 dateline 轉為 localtime datetime
                    dateline = pg_general.get_utc_to_local_datetime(dateline)
                    send_datetime = pg_general.get_utc_to_local_datetime(send_datetime)
                    tempinboxinfo = {
                        "inboxid": pg_general.converttype(tempdata.get("index"), int),
                        "inboxtype": inboxtype,
                        "inboxuri": pg_general.converttype(tempdata.get("inboxuri"), str),
                        "mailtype": pg_general.converttype(tempdata.get('mailtype'), int),
                        "inboxtitle": pg_general.converttype(tempdata.get("inboxtitle"), str),
                        "inboxcontent": pg_general.converttype(tempdata.get("inboxcontent"), str),
                        "receivestate": receivestate,
                        "expiredday": dateline.strftime('%Y-%m-%d %H:%M').replace('-', '/'),
                        "senddatetime": send_datetime.__str__().replace('-', '/'),
                        "award": award,
                        "awardtype": awardtype,
                        "gameid": gameid
                    }

                    if receivestate == 0 or receivestate == -1:
                        history_mail_count += 1

                    # 檢查是否有值為空
                    if None not in tempinboxinfo.values():
                        if history_mail_count <= 30 or receivestate == 1:
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
                            'pg_asqldb:getinboxinfo result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                       logintoken,
                                                                                                       clientdata))
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
                            'pg_asqldb:receiveinbox logintoken:{0}, memberid:{1}, inboxid:{2}'.format(logintoken,
                                                                                                      memberid,
                                                                                                      inboxid))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        credit = None
        totalaward = 0
        totalaward_silver = 0
        totalaward_roomcard = 0
        afterroomcard = 0
        finishinboxid = []
        now = pg_general.strtodatetime(pg_general.getutcnow())
        if inboxid != -1:
            command = 'select memberinbox.*, member.credit, member.silvercredit, member.roomcard, promotion.* from memberinbox, member, promotion where member.memberid = "{0}" and memberinbox.index = "{1}" and promotion.promotionindex = memberinbox.promotionid and memberinbox.memberid = member.memberid and memberinbox.receivestate="1"'.format(
                memberid, inboxid)
            datalen, data = await self.getdbdata(logintoken, command, True)
        else:
            command = 'select memberinbox.*, member.credit, member.silvercredit, member.roomcard, promotion.* from memberinbox, member, promotion where member.memberid = "{0}" and promotion.promotionindex = memberinbox.promotionid and memberinbox.memberid = member.memberid and memberinbox.receivestate="1" and memberinbox.promotionid != 6'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command, True)

        if datalen > 0:
            result = pg_general.Apiresult.othererror
            credit = pg_general.converttype(data[0].get('credit'), int)
            silvercredit = pg_general.converttype(data[0].get('silvercredit'), int)
            roomcard = pg_general.converttype(data[0].get('roomcard'), int)
            award_type = 1

            for item in data:
                inboxindex = pg_general.converttype(item.get('index'), int)
                receivestate = pg_general.converttype(item.get('receivestate'), int)
                promotiontype = pg_general.converttype(item.get("promotiontype"), int)
                dateline = item.get("dateline")  # utc time
                countdownseconds = pg_general.converttype((dateline - now).total_seconds(), int)
                award = 0
                award_s = 0
                award_r = 0
                wheeldata = []

                inboxcontent = {}

                if receivestate is not None and promotiontype is not None and credit is not None and countdownseconds is not None:
                    if promotiontype == 0:
                        award = pg_general.converttype(item.get("content"), int)
                    elif promotiontype == 1:
                        award = 0
                    elif promotiontype == 4:  # 金幣可變
                        award = item.get('credit_award')
                    elif promotiontype == 7:  # 銀幣可變
                        award_s = item.get('credit_award')
                    elif promotiontype == 8:  # 房卡可變
                        award_r = item.get('credit_award')
                        award_type = 0

                    elif promotiontype == 5:  # 銀幣
                        award_s = pg_general.converttype(item.get('content'), int)
                    elif promotiontype == 6:  # 免費轉輪
                        # 抓轉輪倍數
                        dailywheelinboxtimes = 1
                        command = 'select dailywheelinboxtimes from setting2'
                        datalen, data = await self.getdbdata(logintoken, command)
                        if datalen == 1:
                            dailywheelinboxtimes = data.get('dailywheelinboxtimes')

                        # 抓 轉輪資料
                        command = 'select dailybonusInfo_inbox.*,promotion.* from dailybonusInfo_inbox,member,promotion where ' \
                                  ' dailybonusInfo_inbox.dailybonusgroup = member.card and member.memberid = "{0}" and promotionindex = ' \
                                  'dailybonusInfo_inbox.promotionid order by posid'.format(memberid)
                        datalen, data = await self.getdbdata(logintoken, command, True)
                        if datalen != 12:
                            result = pg_general.Apiresult.connectdberror
                            clientdta = {}
                            return result, clientdata
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
                        if windata.get('type') == 0:  # 金幣
                            awardori = pg_general.converttype(windata.get('pay'), int)
                            award = awardori * dailywheelinboxtimes
                            awardextra = award - awardori
                        elif windata.get('type') == 5:  # 銀幣
                            awardori_s = pg_general.converttype(windata.get('pay'), int)
                            award_s = awardori_s * dailywheelinboxtimes
                            awardextra_s = award_s - awardori_s
                        inboxcontent['awardori'] = awardori
                        inboxcontent['awardori_s'] = awardori_s
                        inboxcontent['awardextra'] = awardextra
                        inboxcontent['awardextra_s'] = awardextra_s

                    if countdownseconds > 0 and receivestate == 1:
                        totalaward += award
                        totalaward_silver += award_s
                        totalaward_roomcard += award_r
                        finishinboxid.append(inboxindex)
                        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                            'pg_asqldb:receiveinbox finishinboxid:{0}'.format(
                                                finishinboxid))

            if roomcard is not None and len(finishinboxid) > 0 and totalaward_roomcard != 0:
                roomcard_before = roomcard
                command = 'update memberinbox, member set memberinbox.receivestate = 0, member.roomcard = member.roomcard + "{0}"' \
                          'where memberinbox.memberid = "{1}" and memberinbox.index in ({2}) and member.memberid = "{1}"'.format(
                    totalaward_roomcard, memberid, str(finishinboxid).replace('[', '').replace(']', ''))

                updateresult = await self.updatedbdata(logintoken, command)

                if updateresult == True:
                    command = 'select roomcard from member where memberid="{0}"'.format(memberid)
                    datalen, data = await self.getdbdata(logintoken, command, False, True)
                    if datalen == 1:
                        roomcard = data.get('roomcard')

                    clientdata = {
                        "result": 0,
                        "award": totalaward,
                        "award_s": totalaward_silver,
                        "award_r": totalaward_roomcard,
                        "credit": credit,
                        "credit_s": silvercredit,
                        "roomcard": roomcard,
                        "content": inboxcontent
                    }

                    param = {
                        "frommemberid": memberid,
                        "tomemberid": memberid,
                        "type": pg_general.transactiontype.inboxfreewheel if promotiontype == 6 else pg_general.transactiontype.receiveinbox,
                        "amount": totalaward,
                        "amount_silver": totalaward_silver,
                        "amount_roomcard": totalaward_roomcard,
                        "otherdata": 'receiveinbox' + ('' if promotiontype != 6 else ' :free wheel')
                    }
                    # asyncio.ensure_future(self.writetransactionlog(logintoken, param))
                    transtime = pg_general.getutcnow_datetime()
                    otherdata = param.get('otherdata')
                    type = param.get('type')

                    command = 'insert into transaction (transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata) values ' \
                              '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime, memberid, memberid, type,
                                                                                   totalaward, totalaward_roomcard,
                                                                                   otherdata)

                    updateresult = await self.updatedbdata(logintoken, command)

                    command = 'INSERT INTO `slot-game`.member_wallet_log (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time) values("{0}", "{1}", {2}, {3}, "{4}", {5}, {6}, "{7}", "{8}")' \
                        .format(env_setting.PS_HOST_NAME_S, memberid, 3, 7, "0", totalaward_roomcard, roomcard_before,
                                "API", transtime)
                    insertresult, index = await self.slot_game_db.insertdbdata(logintoken, command)

                result = pg_general.Apiresult.success

            if credit is not None and len(finishinboxid) > 0 and totalaward_silver != 0:
                aftercredit = credit + totalaward

                command = 'update memberinbox, member set memberinbox.receivestate = 0, member.credit =member.credit+ "{0}",' \
                          'member.silvercredit=member.silvercredit+"{3}" where memberinbox.memberid = "{1}" and memberinbox.index in ({2}) and member.memberid = "{1}"'.format(
                    totalaward, memberid, str(finishinboxid).replace('[', '').replace(']', ''), totalaward_silver)

                updateresult = await self.updatedbdata(logintoken, command)
                if updateresult == True:
                    command = 'select credit,silvercredit, roomcard from member where memberid="{0}"'.format(memberid)
                    datalen, data = await self.getdbdata(logintoken, command, False, True)
                    if datalen == 1:
                        aftercredit = data.get('credit')
                        aftersilvercredit = data.get('silvercredit')
                        roomcard = data.get('roomcard')

                    clientdata = {
                        "result": 0,
                        "award": totalaward,
                        "award_s": totalaward_silver,
                        "award_r": totalaward_roomcard,
                        "credit": aftercredit,
                        "credit_s": aftersilvercredit,
                        "roomcard": roomcard,
                        "content": inboxcontent
                    }

                    param = {
                        "frommemberid": memberid,
                        "tomemberid": memberid,
                        "type": pg_general.transactiontype.inboxfreewheel if promotiontype == 6 else pg_general.transactiontype.receiveinbox,
                        "amount": totalaward,
                        "amount_silver": totalaward_silver,
                        "amount_roomcard": totalaward_roomcard,
                        "otherdata": 'receiveinbox' + ('' if promotiontype != 6 else ' :free wheel')
                    }
                    # asyncio.ensure_future(self.writetransactionlog(logintoken, param))
                    transtime = pg_general.getutcnow_datetime()
                    otherdata = param.get('otherdata')
                    type = param.get('type')

                    command = 'insert into transaction (transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata) values ' \
                              '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime, memberid, memberid, type,
                                                                                   totalaward, totalaward_silver,
                                                                                   otherdata)

                    updateresult = await self.updatedbdata(logintoken, command)

                    command = 'INSERT INTO `slot-game`.member_wallet_log (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time) values("{0}", "{1}", {2}, {3}, "{4}", {5}, {6}, "{7}", "{8}")' \
                        .format(env_setting.PS_HOST_NAME_S, memberid, 2, 7, "0", totalaward_silver, silvercredit, "API",
                                transtime)
                    insertresult, index = await self.slot_game_db.insertdbdata(logintoken, command)

                result = pg_general.Apiresult.success

        else:
            result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:receiveinbox result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                       logintoken,
                                                                                                       clientdata))
        return result, clientdata

    async def feedback(self, logintoken, memberid, email, content, typeid):
        """
        意見及Bug回報
        將相關資料(email、content) insert到DB feedback
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:feedback logintoken:{0}, memberid:{1}, email:{2}, content:{3},typeid:{4}'.format(
                                logintoken, memberid, email, content, typeid))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        now = pg_general.getutcnow()
        command = 'insert into feedback(memberid, logintoken, time, email, content,typeid) values({0}, "{1}", "{2}", "{3}", "{4}","{5}")'.format(
            memberid, logintoken, now, email, content, typeid)
        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            clientdata = {
                "result": 0,
            }

            result = pg_general.Apiresult.success
        else:
            result = pg_general.Apiresult.othererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:feedback result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken,
                                                                                                   clientdata))
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
            newsort = []
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
                    gametype = item.get('gametype')

                    if gametype == gametype:  # slot
                        rankprize = json.loads(item.get('rankprize'))
                        rankweekprize = json.loads(item.get('rankweekprize'))
                        totalrankreward = 0
                        tmptopwinlist = rankprize.get('topwin')
                        for tempitem in tmptopwinlist:
                            totalrankreward += pg_general.converttype(tempitem, int)
                        tmptopmultipilierlist = rankprize.get('topmultipilier')
                        for tempitem in tmptopmultipilierlist:
                            totalrankreward += pg_general.converttype(tempitem, int)
                        tmptopwinlist = rankweekprize.get('topwin')
                        for tempitem in tmptopwinlist:
                            totalrankreward += pg_general.converttype(tempitem, int)
                        tmptopmultipilierlist = rankweekprize.get('topmultipilier')
                        for tempitem in tmptopmultipilierlist:
                            totalrankreward += pg_general.converttype(tempitem, int)
                    else:
                        totalrankreward = 0

                    if member_level >= 5:
                        gamepos = gameidlist.split(',')
                    else:
                        gamepos = newbiesort.split(',')
                    posindex = gamepos.index(str(gameindex)) + 1

                    gameidlist_hotsort = item.get('hotsort')
                    gamepos_hotsort = gameidlist_hotsort.split(',')
                    if str(gameindex) in gamepos_hotsort:
                        posindex_hotsort = gamepos_hotsort.index(str(gameindex)) + 1
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
                        rerobjectnew_version_data = rerobjectnew.get('v' + member_ver)
                        if rerobjectnew_version_data is not None:
                            rerobject = rerobjectnew_version_data

                    if None not in [posindex, gameid, enable, posindex_hotsort, posindex_newsort, posindex_mastersort,
                                    posindex_newgamesort, posindex_goodranksort]:
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
                            tempgamelist[
                                "topmultiplieravatar"] = "" if topmultiplieravatar is None else topmultiplieravatar
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
                datalen, data = await self.getdbdata(logintoken, command, True)
                if datalen > 0:
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
                            "enable": enable
                        }

                        for item in sortpos.keys():
                            fishsort.append((
                                gameid,
                                item,  # sort type
                                sortpos[item]  # sort pos
                            ))

                if len(gamelist) > 0:

                    clientdata['gamelist'] = tempclientdatagamelist

                    gamelist = sorted(gamelist, key=lambda k: k['gameid'].split('-')[2])  # 針對 game_id 的數字做排序
                    clientdata['normalsort'] = [item.get('gameid') for item in gamelist]

                    gamelist = sorted(gamelist, key=lambda k: (k['posindex_goodranksort']), reverse=False)
                    clientdata['goodranksort'] = [item.get('gameid') for item in gamelist if
                                                  item.get('posindex_goodranksort') != -1]

                    gamelist = sorted(gamelist, key=lambda k: (k['posindex_hotsort']), reverse=False)
                    clientdata['hotsort'] = [item.get('gameid') for item in gamelist if
                                             item.get('posindex_hotsort') != -1]

                    gamelist = sorted(gamelist, key=lambda k: (k['posindex_mastersort']), reverse=False)
                    clientdata['mastersort'] = [item.get('gameid') for item in gamelist if
                                                item.get('posindex_mastersort') != -1]

                    gamelist = sorted(gamelist, key=lambda k: (k['posindex_newsort']), reverse=False)
                    clientdata['newsort'] = [item.get('gameid') for item in gamelist if
                                             item.get('posindex_newsort') != -1]

                    gamelist = sorted(gamelist, key=lambda k: (k['posindex_newgamesort']), reverse=False)
                    clientdata['newgamesort'] = [item.get('gameid') for item in gamelist if
                                                 item.get('posindex_newgamesort') != -1]

                    for item in fishsort:
                        gameid = item[0]
                        sorttype = item[1]
                        sortpos = item[2]

                        if clientdata.get(sorttype) is not None:
                            clientdata[sorttype].insert(sortpos, gameid)

                    result = pg_general.Apiresult.success
                # else:
                #     result = pg_general.Apiresult.othererror
            else:
                result = pg_general.Apiresult.dbnodata
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgamelist ValueError:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgamelist except:{0}'.format(format_exc()))

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getgamelist result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                      logintoken,
                                                                                                      clientdata))
        return result, clientdata

    async def joingame(self, logintoken, memberid, gameid, gametype):
        """
        加入遊戲
        新增遊戲記錄到DB membergamelog
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:joingame logintoken:{0}, memberid:{1}, gameid:{2}, gametype:{3}'.format(
                                logintoken, memberid, gameid, gametype))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        now = pg_general.getutcnow()

        command = 'insert into membergamelog(memberid, gameid, joingametime, logintoken,gametype) values("{0}", "{1}", "{2}", "{3}","{4}")'.format(
            memberid, gameid, now, logintoken, gametype)
        insertresult, index = await self.insertdbdata(logintoken, command)
        if insertresult == True:
            clientdata = {
                "result": 0,
            }
            result = pg_general.Apiresult.success
        else:
            result = pg_general.Apiresult.othererror

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:joingame result:{0}, logintoken:{1}, clientdata:{2}'.format(result, logintoken,
                                                                                                   clientdata))
        return result, clientdata

    async def getgamerank(self, logintoken, memberid, gameid, redis_obj):
        """
        取得遊戲龍虎榜單
        DB Tables : gametodayrank , gamethismonthrank, gamehistoryrank
        """

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getgamerank logintoken:{0}, memberid:{1}, gameid:{2}'.format(logintoken,
                                                                                                    memberid, gameid))
        result = pg_general.Apiresult.connectdberror

        memberid = pg_general.converttype(memberid, int)

        # get rank award setting
        rankawardtodaytopmultipilier = []
        rankawardtodaytopwin = []
        rankawardthismonthtopmultipilier = []
        rankawardthismonthtopwin = []

        # get self avatar
        command = 'select avatar from member where memberid = "{0}"'.format(memberid)
        datalen, data = await self.getdbdata(logintoken, command)
        if datalen < 1:
            result = pg_general.Apiresult.connectdberror
            raise ValueError('get member avatar error')

        selfavatar = data.get('avatar')

        # get gamerankaward
        command = 'select * from gamerankaward'
        datalen, data = await self.getdbdata(logintoken, command, True)

        if datalen == -1:
            result = pg_general.Apiresult.connectdberror
            raise ValueError('get gamerankaward error')

        for item in data:
            ranktype = item.get('ranktype')
            ranktime = item.get('ranktime')

            if ranktype == 0 and ranktime == 0:
                rankawardtodaytopmultipilier = item.get('award').split(',')
                rankawardtodaytopmultipilier = [int(i) for i in rankawardtodaytopmultipilier]
            elif ranktype == 0 and ranktime == 1:
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
            data = await redis_obj.get_json_value('rank_' + gameid)
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
                    ranktype = pg_general.converttype(item.get("ranktype"), int)
                    tempmemberid = pg_general.converttype(item.get('memberid'), int)
                    card = pg_general.converttype(item.get('card'), int)

                    if None not in [rank, avatar, nickname, level, amount, ranktype, memberid, card]:
                        extraaward = 0
                        if ranktype == 0 and rank <= len(rankawardtodaytopmultipilier):
                            extraaward = rankawardtodaytopmultipilier[rank - 1]
                        else:
                            if rank <= len(rankawardtodaytopwin):
                                extraaward = rankawardtodaytopwin[rank - 1]

                        if ranktype == 0:  # make selftodaytopmultipilierrankinfo
                            if selftodaytopmultipilierrankinfo.get('rank') == -1 and memberid == tempmemberid:
                                selftodaytopmultipilierrankinfo['rank'] = rank
                                selftodaytopmultipilierrankinfo['amount'] = amount
                        else:  # make selftodaytopwinrankinfo
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
                        if ranktype == 0:
                            gametodaytopmultipilierrankinfo.append(tempgamerankinfo)
                        elif ranktype == 1:
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
                    tempmemberid = pg_general.converttype(item.get('memberid'), int)
                    card = pg_general.converttype(item.get('card'), int)

                    if None not in [rank, avatar, nickname, level, amount, ranktype, card]:
                        if ranktype == 0 and len(rankawardthismonthtopmultipilier) >= rank:
                            extraaward = rankawardthismonthtopmultipilier[rank - 1]
                        elif ranktype == 1 and len(rankawardthismonthtopwin) >= rank:
                            extraaward = rankawardthismonthtopwin[rank - 1]
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
            command = 'select max(monthdata) as maxmonth, min(monthdata) as minmonth from gamehistoryrank where ranktype ="0" and gameid ="{0}"'.format(
                gameid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen > 0:
                topmultipilierhistoryrankstart = data.get('minmonth')
                topmultipilierhistoryrankend = data.get('maxmonth')

            # 抓取 history rank 最高與最低範圍 ranktype =1
            command = 'select max(monthdata) as maxmonth, min(monthdata) as minmonth from gamehistoryrank where ranktype ="1" and gameid="{}"'.format(
                gameid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen > 0:
                topwinhistoryrankstart = data.get('minmonth')
                topwinhistoryrankend = data.get('maxmonth')

            # 抓取歷史排名, 先抓全部的 history rank by gameid
            command = 'select * from gamehistoryrank where gameid ="{0}" order by rank'.format(gameid)
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen > 0:
                if None not in [topmultipilierhistoryrankstart, topmultipilierhistoryrankend]:
                    for monthdata in range(topmultipilierhistoryrankstart, topmultipilierhistoryrankend + 1):
                        tempmonth = monthdata % 100
                        if tempmonth > 12 or tempmonth == 0:
                            continue
                        tempdata = [item for item in data if
                                    item.get('monthdata') == monthdata and item.get('ranktype') == 0]
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
                if None not in [topwinhistoryrankstart, topwinhistoryrankend]:
                    for monthdata in range(topwinhistoryrankstart, topwinhistoryrankend + 1):
                        tempmonth = monthdata % 100
                        if tempmonth > 12 or tempmonth == 0:
                            continue
                        tempdata = [item for item in data if
                                    item.get('monthdata') == monthdata and item.get('ranktype') == 1]
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
                "resetcountdown": resetcountdown,
                "selftodaytopmultipilierrankinfo": selftodaytopmultipilierrankinfo,
                "selftodaytopwinrankinfo": selftodaytopwinrankinfo,
                "gametodaytopmultipilierrankinfo": gametodaytopmultipilierrankinfo,
                "gametodaytopwinrankinfo": gametodaytopwinrankinfo,
                "gamethismonthtopmultipilierrankinfo": gamethismonthtopmultipilierrankinfo,
                "gamethismonthtopwinrankinfo": gamethismonthtopwinrankinfo,
                "gamehistorytopmultipilierrankinfo": gamehistorytopmultipilierrankinfo,
                "gamehistorytopwinrankinfo": gamehistorytopwinrankinfo

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
                                'pg_asqldb:getgamerank result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                          logintoken,
                                                                                                          clientdata))
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

            # 積分榜資料
            command = 'select * from gametotalrank'
            datalen, data = await self.getdbdata(logintoken, command, True)
            if datalen > 0:

                gametotalrank = sorted(data, key=lambda k: (k['rank']), reverse=False)
                # find self totalgame rank
                for item in gametotalrank:
                    if item.get('memberid') == memberid:
                        selfgametotalrank = item.get('rank')
                        selfsumwin = item.get('sumwin')

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

            # 抓 settting2.leaderboardactionsetting
            actionrankurl = ''

            command = 'select leaderboardactionsetting from setting2'
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 1:
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
                "selfrankdata": selfrankdata,
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
                                'pg_asqldb:getleaderrank result:{0}, logintoken:{1}, clientdata:{2}'.format(result,
                                                                                                            logintoken,
                                                                                                            clientdata))
            return result, clientdata

    async def setlobbyip(self, ip):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:setlobbyip IP:{0}'.format(ip))
        result = pg_general.Apiresult.connectdberror

        command = 'select * from lobbyserversetting where ip = "{0}"'.format(ip)
        datalen, data = await self.getdbdata('setlobbyserverip', command, True)

        if datalen == 0:
            command = 'insert into lobbyserversetting (ip) values ("{0}")'.format(ip)
            resultdata = await self.updatedbdata('setlobbyserverip', command)
            if resultdata == True:
                result = pg_general.Apiresult.success
        elif datalen > 0:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:setlobbyip IP:{0},result:{1}'.format(ip, result))

        return result

    async def callpsgamelist(self, gamelist):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:callpsgamelist gamelist:{0}'.format(gamelist))
        result = pg_general.Apiresult.connectdberror

        command = 'delete from gamelist'
        dbresult = await self.updatedbdata("delete all gamelist", command)

        # find all values

        parametertext = ''

        for item in gamelist:
            gameid = item.get('game_id')
            gamename = item.get('game_name').get('zh-TW')
            gamedescription = item.get('feature')
            enable = 1
            unlocklevel = 0
            minbet = item.get('min_bet')
            maxbet = item.get('max_bet')

            if parametertext == '':
                parametertext = '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(gameid, gamename, gamedescription,
                                                                                     enable, unlocklevel, minbet,
                                                                                     maxbet)
            else:
                parametertext = parametertext + ',("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(gameid, gamename,
                                                                                                      gamedescription,
                                                                                                      enable,
                                                                                                      unlocklevel,
                                                                                                      minbet, maxbet)

        if dbresult == True:
            command = 'insert into gamelist (gameid,gamename,gamedescription,enable,unlocklevel,minbet,maxbet) values {0}'.format(
                parametertext)
            dbresult = await self.updatedbdata("insert new game list", command)

            if dbresult == True:
                result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:callpsgamelist gamelist:{0},result:{1}'.format(gamelist, result))
        return result

    async def psapi_signin(self, logintoken, memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_signin logintoken:{0},memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        command = 'select memberid from member where memberid ="{0}" and logintoken="{1}"'.format(memberid, logintoken)
        datalen, data = await self.getdbdata(logintoken, command, fromwritedb=True)

        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_signin logintoken:{0},memberid:{1},result:{2}'.format(logintoken, memberid,
                                                                                                   result))
        return result

    async def psapis_signin(self, access_token, memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_signin access_token:{0},memberid:{1}'.format(access_token, memberid))
        result = pg_general.Apiresult.connectdberror

        command = 'select memberid from member where memberid ="{0}" and access_token="{1}"'.format(memberid,
                                                                                                    access_token)
        datalen, data = await self.getdbdata(access_token, command, fromwritedb=True)

        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_signin access_token:{0},memberid:{1},result:{2}'.format(access_token,
                                                                                                      memberid, result))
        return result

    async def psapit_signin(self, logintoken, memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_signin logintoken:{0},memberid:{1}'.format(logintoken, memberid))
        result = pg_general.Apiresult.connectdberror

        command = 'select memberid from member where memberid ="{0}" and logintoken="{1}"'.format(memberid, logintoken)
        datalen, data = await self.getdbdata(logintoken, command, fromwritedb=True)

        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_signin logintoken:{0},memberid:{1},result:{2}'.format(logintoken,
                                                                                                    memberid, result))
        return result

    async def psapi_authenticate(self, logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_authenticate logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        command = 'select memberid,credit,account_type,nickname from member where logintoken ="{0}"'.format(logintoken)
        datalen, data = await self.getdbdata(logintoken, command)
        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            memberid = pg_general.converttype(data.get("memberid"), str)
            credit = pg_general.converttype(data.get("credit"), int)
            account_type = pg_general.converttype(data.get('account_type'), int)
            nickname = data.get('nickname')
            if None not in [memberid, credit]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "memberid": memberid,
                    "credit": credit,
                    "account_type": account_type,
                    "nickname": nickname
                }

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_authenticate logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                           result,
                                                                                                           clientdata))
        return result, clientdata

    async def psapis_authenticate(self, access_token):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_authenticate access_token:{0}'.format(access_token))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        command = 'select memberid, silvercredit,account_type,nickname from member where access_token ="{0}"'.format(
            access_token)
        datalen, data = await self.getdbdata(access_token, command)
        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            memberid = pg_general.converttype(data.get("memberid"), str)
            credit = pg_general.converttype(data.get("silvercredit"), int)
            account_type = pg_general.converttype(data.get('account_type'), int)
            nickname = data.get('nickname')
            if None not in [memberid, credit]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "memberid": memberid,
                    "silvercredit": credit,
                    "account_type": account_type,
                    "nickname": nickname
                }

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_authenticate access_token:{0},result:{1},clientdata:{2}'.format(
                                access_token, result, clientdata))
        return result, clientdata

    async def psapit_authenticate(self, logintoken):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_authenticate logintoken:{0}'.format(logintoken))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        command = 'select memberid, silvercredit from member where logintoken ="{0}"'.format(logintoken)
        datalen, data = await self.getdbdata(logintoken, command)
        if datalen == 0:
            result = pg_general.Apiresult.dbnodata
        elif datalen > 0:
            memberid = pg_general.converttype(data.get("memberid"), str)
            credit = pg_general.converttype(data.get("silvercredit"), int)
            if None not in [memberid, credit]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "memberid": memberid,
                    "silvercredit": credit
                }

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_authenticate logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                            result,
                                                                                                            clientdata))
        return result, clientdata

    async def writecardchangelog(self, param):
        try:

            command = 'insert into cardlevelchangelog (memberid,logtime,oldcard,newcard,memo) values(%s,%s,%s,%s,%s)'
            insertresult, index = await self.insertdbdata('write card level change log', command, True, param)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:writecardchangelog Exception : {}'.format(e))

    async def buycardlevelup_future(self, apporweb, logintoken, memberid, card, redis_obj, cardinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:buycardlevelup_future logintoken:{0},memberid:{1},apporweb:{2}'.format(
                                    logintoken, memberid, apporweb))

            # get all sum bet from redis
            valuelist = await redis_obj.hvals('cardbuy_{}'.format(memberid))
            if len(valuelist) > 0:
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
                        asyncio.ensure_future(
                            self.writecardchangelog([[memberid, nowutctime, card, card + upgrade_level, 'buy']]))

                        # update member card
                        command = 'update member set card = card+{},cardlevelchangetime="{}" where memberid="{}"'.format(
                            upgrade_level, nowutctime, memberid)
                        updateresult = await self.updatedbdata(logintoken, command)

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
                                        "msg": {"commandid": 3000013, "data": {"card": card + upgrade_level}}
                                    }

                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(realurl, json=sendmsg) as response:
                                            if response.status == 200:
                                                data = await response.text()
                                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                    'sendcardlevelup response:{0},sendmsg:{1}'.format(
                                                                        data, sendmsg))



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

    async def betcardlevelup_future(self, logintoken, memberid, card, redis_obj, cardinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:betcardlevelup_future logintoken:{0},memberid:{1}'.format(logintoken,
                                                                                                     memberid))

            # get all sum bet from redis
            valuelist = await redis_obj.hvals('bethistory_gold_{}'.format(memberid))
            if len(valuelist) > 0:
                valuelist = list(map(int, valuelist))
                cardbet = sum(valuelist)
                nextlevelneedbet = cardinfo[card + 1].get('twomonthaccbet')
                if nextlevelneedbet > 0:
                    if cardbet >= nextlevelneedbet:  # 生卡等級
                        # 清空所有 bethistory from redis
                        nowutctime = pg_general.getutcnow_datetime()

                        await redis_obj.del_key('bethistory_gold_{}'.format(memberid))
                        await redis_obj.del_key('bethistory_silver_{}'.format(memberid))
                        await redis_obj.del_key('cardbuy_{}'.format(memberid))
                        await redis_obj.del_key('cardlevelupdays_{}'.format(memberid))

                        # write 升級卡別 log
                        asyncio.ensure_future(self.writecardchangelog([[memberid, nowutctime, card, card + 1, 'bet']]))

                        # update member card
                        command = 'update member set card = card+1,cardlevelchangetime="{1}" where memberid="{0}"'.format(
                            memberid, nowutctime)
                        updateresult = await self.updatedbdata(logintoken, command)

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
                                        "msg": {"commandid": 3000013, "data": {"card": card + 1}}
                                    }

                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(realurl, json=sendmsg) as response:
                                            if response.status == 200:
                                                data = await response.text()
                                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                    'sendcardlevelup response:{0},sendmsg:{1}'.format(
                                                                        data, sendmsg))



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

    async def make_seats_data_update(self, redis_obj, clientdata, gametype):
        try:
            result = False
            resultdata = {}

            logintoken = clientdata.get('token')
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:make_seats_data_update start, clientdata:{0} ,logintoken:{1}'.format(
                                    clientdata, logintoken))

            has_bonus = clientdata.get('has_bonus')
            seat_data = clientdata.get('seat_data')
            multipilier = clientdata.get('multipilier')

            tempgameid = seat_data.split('_')[1]
            tempseatnum = seat_data.split('_')[2]

            if gametype == 'gold':
                seatkey = 'goldseats_{}@{}'.format(tempgameid, tempseatnum)
            else:
                seatkey = 'silverseats_{}@{}'.format(tempgameid, tempseatnum)

            # get goldseats_{}@{} information
            valuelist = await redis_obj.hmget(seatkey,
                                              ["unopenturn", "avgturn", "his1turn", "his2turn", "his3turn", "his1multi",
                                               "his2multi", "his3multi"])
            if valuelist is None or valuelist == []:
                raise Exception('get seat data error')

            unopenturn = pg_general.converttype(valuelist[0], int)
            avgturn = pg_general.converttype(valuelist[1], int)
            his1turn = pg_general.converttype(valuelist[2], int)
            his2turn = pg_general.converttype(valuelist[3], int)
            his3turn = pg_general.converttype(valuelist[4], int)
            his1multi = pg_general.converttype(valuelist[5], int)
            if his1multi is None:
                his1multi = 0
            his2multi = pg_general.converttype(valuelist[6], int)
            if his2multi is None:
                his2multi = 0
            his3multi = pg_general.converttype(valuelist[7], int)
            if his3multi is None:
                his3multi = 0

            unopenturn += 1
            if has_bonus == 0:  # 沒開
                pass
            else:  # 有開

                his3turn = his2turn
                his3multi = his2multi

                his2turn = his1turn
                his2multi = his1multi

                his1turn = unopenturn
                his1multi = multipilier
                unopenturn = 0
                avgturn = pg_general.converttype((his1turn + his2turn + his3turn) / 3, int)

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

            await redis_obj.hmset(seatkey, updatedata)

            result = True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_seats_data_update except:{0} ,logintoken:{1}'.format(e, logintoken))

        return result, resultdata

    async def psapi_bet(self, redis_obj, logintoken, betdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_bet logintoken:{0},betdata:{1}'.format(logintoken, betdata))
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
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1}
                raise ValueError('status_code 1')

            beforecredit = pg_general.converttype(data.get('credit'), int)
            memberid = pg_general.converttype(data.get("memberid"), int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"), str)

            card = data.get('card')

            # update member
            command = 'update member set credit=credit-"{0}" where memberid ="{1}" and credit >="{0}"'.format(total_bet,
                                                                                                              memberid)
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            if updaterows < 1:
                result = pg_general.Apiresult.balanceerror
                clientdata = {'status_code': 3}
                raise ValueError('status_code 3')

            aftercredit = beforecredit - total_bet

            # 確認是否可以寫入 bethistory , 等於檢查 txn_id 是否重複
            command = 'insert into bethistory (txn_id,memberid,beforecredit,aftercredit,gameid,total_bet,logintoken,bettime,subgameid)' \
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
                "aftercredit": aftercredit,
                "card": card
            }
            # 寫入 redis hincyby daybet_date 設定  ttl = 10 天 864000 秒
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()
            await redis_obj.hincrby('daybet_{}'.format(twdatetimestr), '{}'.format(memberid), total_bet)
            await redis_obj.incrby('totaldaybet_{}'.format(twdatetimestr), total_bet)

            # 做金爽榜及時榜單 total bet 累積
            twtodaydate = pg_general.get_tw_datetime().date()
            if twtodaydate.day >= 1 and twtodaydate.day <= 15:
                await redis_obj.incrby('totalmonthbet_{}'.format(twdatetimemonthstr), total_bet)
            else:
                await redis_obj.incrby('totalmonthbet2_{}'.format(twdatetimemonthstr), total_bet)

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_bet ValueError:{0} ,logintoken:{1}'.format(e, logintoken))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapi_bet except:{0} ,logintoken:{1}'.format(e, logintoken))
        finally:
            pass

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapi_bet logintoken:{0},result:{1},clientdata:{2}'.format(logintoken,
                                                                                                  result,
                                                                                                  clientdata))
        return result, clientdata

    async def write_to_slot_game_member_wallet_log(self, host_id, member_id, sg_action,
                                                   amount, member_credit):
        """

        Args:
            amount (int): 此筆交易記錄更動數量
            member_credit (int): 此筆交易記錄更動前總量
        """
        current_time = pg_general.getutcnow()

        insert_command = '''
        INSERT INTO `slot-game`.`member_wallet_log`
        (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time)
        VALUES("{}", "{}", 2, {}, "0", {}, {}, "API", "{}")
        '''.format(host_id, member_id, sg_action, amount, member_credit, current_time)
        msg = "wrote_to_slot_game_member_wallet_log: {}".format(member_id)
        insert_result, index = await self.slot_game_db.insertdbdata(msg, insert_command)

    async def write_to_slotwarapp_member_wallet_log(self, host_id, member_id, sg_action,
                                                    amount, member_credit, txn_id):
        """

        Args:
            amount (int): 此筆交易記錄更動數量
            member_credit (int): 此筆交易記錄更動前總量
        """
        current_time = pg_general.getutcnow()

        insert_command = '''
        INSERT INTO member_wallet_log
        (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time)
        VALUES("{}", "{}", 2, {}, "0", {}, {}, "{}", "{}")
        '''.format(host_id, member_id, sg_action, amount, member_credit, txn_id, current_time)
        msg = "write_to_slotwarapp_member_wallet_log: {}".format(member_id)
        insert_result, index = await self.insertdbdata(msg, insert_command)

    async def _delete_bethistory_s(self, access_token, txn_id):
        command = '''
            DELETE FROM bethistory_s WHERE txn_id={}
        '''.format(txn_id)
        updateresult = await self.updatedbdata('_delete_bethistory_s:{}'.format(access_token), command)

    async def psapis_bet(self, redis_obj, access_token, betdata):
        """共享錢包下注

        玩家從 APP 轉錢到 GS

        1. 寫記錄到 bethistory_s 中(bet 紀錄)
        2. 寫記錄到 slot-game.member_wallet_log 中
        3. member 表扣錢 (玩家錢包)
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_bet access_token:{0},betdata:{1}'.format(access_token, betdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        txn_id = betdata.get("txn_id")
        total_bet = betdata.get("total_bet")
        game_id = betdata.get("game_id")
        subgame_id = betdata.get("subgame_id")
        bettime = betdata.get("bettime")

        try:
            # 先確認 access_token , silvercredit 是否足夠
            command = '''
            SELECT silvercredit, lobbyserverip, memberid FROM member WHERE access_token="{}"
            '''.format(access_token)
            datalen, data = await self.getdbdata(access_token, command)

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

            aftercredit = beforecredit - total_bet

            # 確認是否可以寫入 bethistory , 等於檢查 txn_id 是否重複
            command = '''
            INSERT INTO bethistory_s (txn_id, memberid, beforecredit, aftercredit, gameid,
            total_bet, logintoken, bettime, subgameid)
            VALUES ("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}")
            '''.format(txn_id, memberid, beforecredit, aftercredit,
                       game_id, total_bet,
                       access_token, bettime, subgame_id)

            insertresult, index = await self.insertdbdata(access_token, command)
            if insertresult == False:
                result = pg_general.Apiresult.othererror
                clientdata = {'status_code': 2}
                raise ValueError('status_code 2')

            await self.write_to_slot_game_member_wallet_log(
                env_setting.PS_HOST_NAME_S,
                memberid, 0,
                total_bet, beforecredit)

            # update member
            command = '''UPDATE member SET silvercredit=silvercredit-{0}
            WHERE memberid={1} and silvercredit>={0}
            '''.format(total_bet, memberid)
            updaterows = await self.updatedbdata_affectrows(access_token, command)

            if updaterows < 1:  # 確認 credit 是否足夠 bet
                await self._delete_bethistory_s(access_token, txn_id)

                result = pg_general.Apiresult.balanceerror
                clientdata = {'status_code': 3}
                raise ValueError('status_code 3')

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
        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_bet ValueError:{0} ,access_token:{1}'.format(format_exc(),
                                                                                               access_token))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_bet except:{0} ,access_token:{1}'.format(format_exc(), access_token))
        finally:
            pass

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_bet access_token:{0},result:{1},clientdata:{2}'.format(access_token,
                                                                                                     result,
                                                                                                     clientdata))

        return result, clientdata

    async def psapit_bet(self, redis_obj, logintoken, betdata):
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
            command = 'update member set silvercredit=silvercredit - "{0}",tutorialbetfinish = "1" where memberid ="{1}" and silvercredit >= "{0}"'.format(
                total_bet, memberid)
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            if updaterows < 1:  # 確認 credit 是否足夠 bet
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

    async def psapi_result(self, redis_obj, logintoken, apiresultdata, rankminwin, rankminmultipilier):
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
            command = 'select lobbyserverip, memberid, credit,nickname,avatar,card,level from member where logintoken="{0}"'.format(
                logintoken)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('2')

            memberid = pg_general.converttype(data.get("memberid"), int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"), str)
            beforecredit = pg_general.converttype(data.get("credit"), int)
            aftercredit = beforecredit + total_win
            nickname = data.get('nickname')
            avatar = data.get('avatar')
            card = data.get('card')
            level = data.get('level')

            # 確認 txn_id 是否已經寫過 resutltime
            command = 'select bethistory.resulttime,game.gamename,memberid from bethistory,game where bethistory.txn_id ="{0}" and bethistory.gameid = game.gameid'.format(
                txn_id)
            datalen, data = await self.getdbdata(logintoken, command, fromwritedb=True)
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
                clientdata = {'status_code': 99, "balance": 0}
                raise ValueError('5')

            gamename = data.get('gamename')
            betmemberid = pg_general.converttype(data.get('memberid'), int)

            # 確認 txn_id in bethistory
            command = 'update bethistory set total_win="{0}",base_win="{1}",bonus_win="{2}",resulttime="{3}",has_bonus="{5}" where txn_id="{4}"'.format(
                total_win, base_win, bonus_win, resulttime, txn_id, has_bonus)
            updateresult = await self.updatedbdata(logintoken, command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2, "balance": 0}
                raise ValueError('6')

            if betmemberid != memberid:  # 此筆單不是這位的
                result = pg_general.Apiresult.success
                clientdata = {'status_code': 98, "balance": beforecredit}
                raise ValueError('98,betmemberid:{},memberid:{}'.format(betmemberid, memberid))

            # 抓 bethistroy 該筆單的 total_bet
            command = 'select total_bet from bethistory where txn_id ="{0}"'.format(txn_id)
            datalen, data = await self.getdbdata(logintoken, command, fromwritedb=True)

            if datalen > 0:
                total_bet = data.get('total_bet')

            # update member credit
            command = 'update member set credit=credit+"{0}" where memberid ="{1}"'.format(total_win, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
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

            tmpmultipilier = pg_general.converttype(total_win / total_bet, int)

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
            # if tmpmultipilier >= rankminmultipilier:
            #    await redis_obj.hincrby('daymultipilier_{}'.format(twdatetimestr), '{}'.format(memberid), tmpmultipilier)
            # await redis_obj.hincrby('monthwin_{}'.format(twdatetimemonthstr),'{}'.format(memberid), total_win)
            await redis_obj.incrby('totaldaywin_{}'.format(twdatetimestr), total_win)
            await redis_obj.incrby('totalmonthwin_{}'.format(twdatetimemonthstr), total_win)

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

    async def psapis_result(self, redis_obj, access_token, apiresultdata):
        """共享錢包回傳結果

        玩家把錢從 GS 存回到 APP

        1. 查詢 bethistory_s(bet 紀錄)
        2. 查詢 token 是否有效 (玩家 token)
        3. 把錢存回 member 資料表(玩家錢包)
        4. 寫入 slot-game.member_wallet_log
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_result access_token:{0},apiresultdata:{1}'.format(access_token,
                                                                                                apiresultdata))
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
            command = '''
            SELECT lobbyserverip, memberid, silvercredit, nickname, avatar, card 
            FROM member WHERE access_token="{}"
            '''.format(access_token)

            datalen, data = await self.getdbdata(access_token, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('2')

            memberid = pg_general.converttype(data.get("memberid"), int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"), str)
            beforecredit = pg_general.converttype(data.get("silvercredit"), int)
            aftercredit = beforecredit + total_win
            nickname = data.get('nickname')
            avatar = data.get('avatar')
            card = data.get('card')

            # 確認 txn_id 是否已經寫過 resutltime
            command = '''
            SELECT total_bet, game.gamename, resulttime, memberid FROM bethistory_s, game 
            WHERE game.gameid=bethistory_s.gameid AND txn_id ={}
            '''.format(txn_id)
            datalen, data = await self.getdbdata(access_token, command, fromwritedb=True)

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
                clientdata = {'status_code': 99, "balance": 0}
                raise ValueError('5')

            betmemberid = pg_general.converttype(data.get('memberid'), int)
            total_bet = data.get('total_bet')
            gamename = data.get('gamename')

            # 確認 txn_id in bethistory
            command = '''
            UPDATE bethistory_s SET total_win="{}", base_win="{}", bonus_win="{}",
            resulttime="{}",has_bonus="{}" WHERE txn_id="{}"
            '''.format(total_win, base_win, bonus_win, resulttime, has_bonus, txn_id)
            updateresult = await self.updatedbdata(access_token, command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2, "balance": 0}
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
            command = '''UPDATE member SET silvercredit=silvercredit+{} WHERE memberid={}
            '''.format(total_win, memberid)
            updateresult = await self.updatedbdata(access_token, command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('7')

            await self.write_to_slot_game_member_wallet_log(env_setting.PS_HOST_NAME_S,
                                                            memberid, 1, total_win, beforecredit)

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
                                'pg_asqldb:psapis_result access_token:{0},ValueError:{1}'.format(access_token, e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_result access_token:{0},except:{1}'.format(access_token, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapis_result access_token:{0},result:{1},clientdata:{2}'.format(
                                    access_token,
                                    result,
                                    clientdata))
            return result, clientdata

    async def psapit_result(self, redis_obj, logintoken, apiresultdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapit_result logintoken:{0},apiresultdata:{1}'.format(logintoken,
                                                                                              apiresultdata))
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
            command = 'select lobbyserverip, memberid, silvercredit,nickname,avatar,card from member where logintoken="{0}"'.format(
                logintoken)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('1')
            elif datalen == -1:
                result = pg_general.Apiresult.connectdberror
                clientdata = {'status_code': 1, "balance": 0}
                raise ValueError('2')

            memberid = pg_general.converttype(data.get("memberid"), int)
            lobbyserverip = pg_general.converttype(data.get("lobbyserverip"), str)
            beforecredit = pg_general.converttype(data.get("silvercredit"), int)
            aftercredit = beforecredit + total_win
            nickname = data.get('nickname')
            avatar = data.get('avatar')
            card = data.get('card')

            # 確認 txn_id 是否已經寫過 resutltime
            command = 'select total_bet,game.gamename,resulttime,memberid from bethistory_s,game where game.gameid = bethistory_s.gameid and txn_id ="{0}"'.format(
                txn_id)
            datalen, data = await self.getdbdata(logintoken, command, fromwritedb=True)
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
                clientdata = {'status_code': 99, "balance": 0}
                raise ValueError('5')

            betmemberid = pg_general.converttype(data.get('memberid'), int)
            total_bet = data.get('total_bet')
            gamename = data.get('gamename')

            # 確認 txn_id in bethistory
            command = 'update bethistory_s set total_win="{0}",base_win="{1}",bonus_win="{2}",resulttime="{3}",has_bonus="{5}" where txn_id="{4}"'.format(
                total_win, base_win, bonus_win, resulttime, txn_id, has_bonus)
            updateresult = await self.updatedbdata(logintoken, command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 2, "balance": 0}
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
            command = 'update member set silvercredit=silvercredit+"{0}",tutorialbetfinish= "2" where memberid ="{1}"'.format(
                total_win, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            if updateresult == False:
                result = pg_general.Apiresult.dbnodata
                clientdata = {'status_code': 1, "balance": 0}
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

            # 寫入 tranaction log
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

    async def psapi_getbalance(self, logintoken):
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
                "balance": balance
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

    async def psapis_getbalance(self, access_token):
        """共享錢包取得金錢

        取得玩家在 APP 有多少錢

        1. 從 member 查金額 (玩家錢包)
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:psapis_getbalance access_token:{0}'.format(access_token))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        try:
            command = '''SELECT silvercredit FROM member WHERE access_token="{}"
            '''.format(access_token)
            datalen, data = await self.getdbdata(access_token, command)

            result = pg_general.Apiresult.success
            clientdata = {
                'status_code': 0 if datalen == 1 else 2,
                'balance': data.get('silvercredit', 0) if datalen == 1 else 0,
            }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_getbalance access_token:{0},except:{1}'.format(access_token, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapis_getbalance access_token:{0},result:{1},clientdata:{2}'.format(
                                    access_token,
                                    result,
                                    clientdata))
            return result, clientdata

    async def psapis_refund(self, access_token, txn_id):
        """共享錢包還錢

        1. 從 bethistory_s 資料表查金額
        2. 確認金額
        2.1 錯誤 raise 錯誤代碼 2
        3. 檢查 token 是否有效
        3.1 無效 raise 錯誤代碼 1
        4. 存錢回 member 資料表
        5. 取得 member 資料表的錢
        6. 寫入 slot-game.member_wallet_log

        Returns:
            clientdata = {
                'status_code': 0,  # 0 成功，1 token 無效，2 txn_id 無效
                'balance': 123456,  # 玩家還錢後的金額
            }
        """
        msg = '''pg_asqldb:psapis_refund access_token: {}, txn_id: {}
        '''.format(access_token, txn_id)
        pg_general.writelog(pg_general.PG_LogerLevel.debug, msg)

        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        status_code = 0
        balance = 0

        try:
            bet_select_command = '''
            SELECT total_bet FROM bethistory_s WHERE txn_id={}
            '''.format(txn_id)
            bet_datalen, bet_data = await self.getdbdata(access_token, bet_select_command)

            if bet_datalen != 1:
                status_code = 2
                raise ValueError('txn_id: {} is not found'.format(txn_id))

            refund_bet = bet_data.get('total_bet')

            select_command = '''
            SELECT silvercredit, memberid FROM member WHERE access_token="{}"
            '''.format(access_token)
            datalen, data = await self.getdbdata(access_token, select_command)

            if datalen != 1:
                status_code = 1
                raise ValueError('acces_token: {} is not found'.format(access_token))

            before_credit = data.get('silvercredit')
            member_id = data.get('memberid')

            update_command = '''
            UPDATE member SET silvercredit=silvercredit+{} WHERE access_token="{}"
            '''.format(bet_data.get('total_bet'), access_token)
            update_result = await self.updatedbdata(access_token, update_command)

            balance = before_credit + refund_bet

            await self.write_to_slot_game_member_wallet_log(env_setting.PS_HOST_NAME_S,
                                                            member_id, 2, refund_bet, before_credit)

            await self.write_to_slotwarapp_member_wallet_log(env_setting.PS_HOST_NAME_S,
                                                             member_id, 2, refund_bet, before_credit, txn_id)

            result = pg_general.Apiresult.success

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapis_refund access_token:{0},except:{1}'.format(access_token,
                                                                                             format_exc()))
        finally:
            clientdata = {
                'status_code': status_code,
                'balance': balance,
            }

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapis_refund access_token:{0},result:{1},clientdata:{2}'.format(
                                    access_token,
                                    result, clientdata))
            return result, clientdata

    async def set_game_status(self, member_id, game_id):
        """設定玩家遊玩狀態
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:set_game_status member_id:{}, game_id:{}'.format(member_id, game_id))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        try:
            command = '''
                UPDATE member
                SET playing_game_id="{}"
                WHERE memberid="{}"
            '''.format(game_id, member_id)
            result = await self.updatedbdata('set_game_status:{}'.format(member_id), command)

            result = pg_general.Apiresult.success

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:set_game_status member_id: {0},except:{1}'.format(member_id, format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:set_game_status member_id:{0},result:{1},clientdata:{2}'.format(member_id,
                                                                                                           result,
                                                                                                           clientdata))
            return result, clientdata

    async def dummy_login(self, access_token):
        """dummy 登入檢查

        1. 查 token 是否有效 (玩家 token)
        1.1 無效 raise 回傳錯誤代碼 1

        Returns:
            clientdata = {
                'status_code': 0,  # 0 正確，1 token 無效
                'member_id': '91403',
                'member_name': "fTonia",
                'balance' : 123456
            }
        """
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:dummy_login access_token:{0}'.format(access_token))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        status_code = 0
        member_id = ''
        member_name = ''
        balance = 0

        try:
            command = '''
                SELECT memberid, nickname, silvercredit FROM member WHERE access_token="{}"
            '''.format(access_token)

            datalen, data = await self.getdbdata(access_token, command)

            if datalen != 1:
                status_code = 1
                raise ValueError('access_token: {} is not found'.format(access_token))

            member_id = str(data.get('memberid'))
            member_name = data.get('nickname')
            balance = data.get('silvercredit')
            result = pg_general.Apiresult.success

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:dummy_login access_token:{0},except:{1}'.format(access_token, format_exc()))
        finally:
            clientdata = {
                'status_code': status_code,
                'member_id': member_id,
                'member_name': member_name,
                'balance': balance,
            }
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:dummy_login access_token:{0},result:{1},clientdata:{2}'.format(access_token,
                                                                                                          result,
                                                                                                          clientdata))
            return result, clientdata

    async def psapit_getbalance(self, logintoken):
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
                "balance": balance
            }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:psapit_getbalance logintoken:{0},except:{1}'.format(logintoken, e))
        finally:

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:psapit_getbalance logintoken:{0},result:{1},clientdata:{2}'.format(
                                    logintoken,
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
                "ip": ['127.0.0.1']
            }

        else:
            command = 'select ip from lobbyserversetting'
            datalen, data = await self.getdbdata('getlobbyserverip', command, True)

            if datalen > 0:
                result = pg_general.Apiresult.success
                clientdata = {
                    "ip": [item.get("ip") for item in data]
                }

            elif datalen == 0:
                result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getlobbyserverip result:{0},clientdata:{1}'.format(result, clientdata))
        return result, clientdata

    async def bet_process(self, betdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:bet_process , betdata:{0}'.format(betdata))
        result = pg_general.Apiresult.connectdberror
        clientdata = {}

        # prepare data
        cmd = betdata.get('cmd')
        token = betdata.get('token')
        game_id = betdata.get('game_id')
        total_bet = pg_general.converttype(betdata.get('total_bet'), int)
        memberid = pg_general.converttype(betdata.get('memberid'), int)
        lobbyserverip = betdata.get('lobbyserverip')

        # 計算 exp, and piggy 累積
        command = 'select member.credit as credit ,member.exp as exp,member.level as level, ' \
                  'levelinfo.newlevelexp as newlevelexp,' \
                  'levelinfo.rebate as rebate,memberpiggyinfo.index as memberpiggyinfoindex, ' \
                  'memberpiggyinfo.piggycredit as piggycredit ' \
                  'from  member,levelinfo,memberpiggyinfo ' \
                  'where member.memberid="{0}" and levelinfo.level=member.level and memberpiggyinfo.memberid = member.memberid'.format(
            memberid)

        datalen, data = await self.getdbdata(token, command)

        if datalen > 0:
            level = pg_general.converttype(data.get("level"), int)
            exp = pg_general.converttype(data.get("exp"), int)
            newlevelexp = pg_general.converttype(data.get("newlevelexp"), int)

            memberpiggyinfoindex = data.get('memberpiggyinfoindex')

            rebate = data.get('rebate')

            # 處理 piggy
            pluspiggycredit = (total_bet * rebate)
            command = 'update memberpiggyinfo set piggycredit=piggycredit+ "{0}" where memberpiggyinfo.index="{1}"'.format(
                pluspiggycredit, memberpiggyinfoindex)
            result = await self.updatedbdata(token, command)

            spinexp = total_bet

            exp = exp + spinexp
            levelup = 0
            if exp >= newlevelexp:
                level = level + 1
                exp = exp - newlevelexp
                levelup = 1

            unlockgame = []
            if levelup == 1:
                # update exp and credit
                command = 'update member set exp="{0}",level="{1}" where memberid = "{2}"'.format(exp, level, memberid)
                result = await self.updatedbdata(token, command)

                # get unlockgame gameid
                command = 'select gameid from game where unlocklevel = "{0}"'.format(level)
                datalen, data = await self.getdbdata(token, command, True)
                if datalen > 0:
                    for item in data:
                        unlockgame.append(item.get('gameid'))

                # write to leveluplog
                nowdatetime = pg_general.getutcnow_datetime()
                command = 'insert into leveluplog ( memberid,leveluptime,fromlevel,tolevel) values( "{0}","{1}","{2}","{3}")'.format(
                    memberid, nowdatetime, level - 1, level)
                result = await self.updatedbdata(token, command)

            else:
                command = 'update member set exp="{0}" where memberid = "{1}"'.format(exp, memberid)
                result = await self.updatedbdata(token, command)

            command = 'select maxbet,newlevelexp from levelinfo where level = "{0}"'.format(level)
            datalen, data = await self.getdbdata(token, command)

            newlevelexp = pg_general.converttype(data.get('newlevelexp'), int)
            maxbet = pg_general.converttype(data.get("maxbet"), int)

            exppercent = int((exp / newlevelexp) * 100)
            exppercent = 100 if exppercent > 100 else exppercent

            exptonextlevel = newlevelexp - exp

            clientdata = {
                "cmd": cmd,
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
                            'pg_asqldb:bet_process , result:{0},clientdata:{1}'.format(result, clientdata))
        return result, clientdata

    async def _send_post_to_get_linegame_url(self, line_uid, cash, point, shopid, mode, pay_method):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping _send_post_to_get_linegame_url , line_uid:{0}, cash:{1}, point:{2}, shopid:{3}, mode:{4}'
                                .format(line_uid, cash, point, shopid, mode))
            send_param = {}
            line_game_get_url = 'https://linegame.sd555.online/order/skypay'
            headers = {"Content-Type": "application/json;charset=utf-8"}
            send_param = json.dumps({
                "line_uid": line_uid,
                "amount": cash,
                "product_name": shopid,
                "product_number": point,
                "product_mode": mode,
                "pay_method": pay_method
            })

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping _send_post_to_get_linegame_url send_param:{0}'.format(
                                    send_param))

            async with aiohttp.ClientSession() as session:
                async with session.post(line_game_get_url, data=send_param,
                                        headers=headers) as response:  # , headers=headers
                    if response.status != 200:
                        raise ValueError('send request to get line token error {}'.format(response.status))

                    linegameurl = await response.json()

                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'pg_asqldb:_send_post_to_get_token lineloginresult:{0}'.format(linegameurl))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:linegameshopping _send_post_to_get_linegame_url ValueError:{0}'.format(
                                    format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:linegameshopping _send_post_to_get_linegame_url Exception:{0}'.format(
                                    format_exc()))

        return linegameurl

    async def linegameshopping(self, redis_obj, memberid, logintoken, platform, shopid, num, mode, pay_method):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping , logintoken:{0}, memberid:{1}, platform:{2}, shopid:{3}, num:{4}, mode:{5}, pay_method"{6}'
                                .format(logintoken, memberid, platform, shopid, num, mode, pay_method))

            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            if platform != 3:
                clientdata = {
                    "errormsg": "platform parameter error"
                }
                result = pg_general.Apiresult.parametererror
                return result, clientdata

            command = 'SELECT linesub from member WHERE memberid = {0}'.format(memberid)  # 取得member的Line uuid
            datalen, data = await self.getdbdata(logintoken, command)
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping SELECT linesub from member, datalen:{0}, data:{1}'.format(
                                    datalen, data))

            if datalen != 1:
                clientdata = {
                    "errormsg": "get line_uuid from member table error"
                }
                result = pg_general.Apiresult.parametererror
                return result, clientdata

            line_uid = pg_general.converttype((data.get('linesub')), str)
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping , line_uid:{0}'.format(line_uid))

            command = 'SELECT cash, point from mallinfo WHERE shopid = "{0}"'.format(shopid)  # 取得購買品項的金額與購買的寶石或房卡
            datalen, data = await self.getdbdata(logintoken, command)

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping SELECT cash, point from mallinfo, datalen:{0}, data:{1}'.format(
                                    datalen, data))

            if datalen != 1:
                clientdata = {
                    "errormsg": "get info from mallinfo table error"
                }
                result = pg_general.Apiresult.parametererror
                return result, clientdata

            cash = pg_general.converttype(data.get('cash'), int)
            point = pg_general.converttype(data.get('point'), int)
            point = point  # 轉為cent* 100

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping cash:{0}, point:{1}'.format(cash, point))

            responce = await self._send_post_to_get_linegame_url(line_uid, cash, point, shopid, mode, pay_method)

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping responce:{0}'.format(responce))

            status_code = pg_general.converttype(responce.get('status_code'), str)

            if status_code == "200":
                skypay_data = responce.get('data')
                skypay_url = skypay_data.get('url')
                skypay_order_id = skypay_data.get('merchant_order_id')

                clientdata['skypay_url'] = skypay_url
                result = pg_general.Apiresult.success

                pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                    'pg_asqldb:linegameshopping clientdata:{0}, result:{1}'.format(clientdata, result))

            elif status_code == "422":
                clientdata['errormsg'] = responce.get('message')
                result = pg_general.Apiresult.parametererror

            elif status_code == "S1000":
                error = responce.get('data')
                clientdata['errormsg'] = error.get('message')
                result = pg_general.Apiresult.othererror

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:linegameshopping Exception:{0}'.format(format_exc()))

        return result, clientdata

    async def getroomsharingurl(self, memberid, logintoken, room_id):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getroomsharingurl , logintoken:{0}, memberid:{1}, room_id:{2}'
                                .format(logintoken, memberid, room_id))

            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'SELECT linesub FROM member WHERE memberid = {0}'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            line_uid = pg_general.converttype(data.get('linesub'), str)
            room_id = pg_general.converttype(room_id, str)

            if line_uid == "0":
                result = pg_general.Apiresult.parametererror
                clientdata['errormsg'] = 'This member is not login with linegame'
                return result, clientdata

            param = 'sender_line_uid=' + line_uid + '&room_id=' + room_id

            aes = AES.new(env_setting.AES256_key.encode('utf-8'), AES.MODE_CBC, env_setting.AES256_IV.encode('utf-8'))
            param_bytes = param.encode('utf-8')

            cc = base64.b64encode(aes.encrypt(pad(param_bytes, AES.block_size)))

            cc = cc.decode('utf-8')
            cc_url = urllib.parse.quote_plus(cc)

            clientdata = {
                "gameroom_url": env_setting.Linegame_mgm + cc_url,
                "result": True
            }
            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getroomsharingurl ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getroomsharingurl Exception:{0}'.format(format_exc()))

        return result, clientdata

    async def sendlinedepositanimation(self, memberid, logintoken):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:sendlinedepositanimation , logintoken:{0}, memberid:{1}'
                                .format(logintoken, memberid))

            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = '''
            SELECT * FROM line_trade_log WHERE member_id={} AND animation_mark=0
            '''.format(memberid)
            datalen, deposit_data = await self.getdbdata(logintoken, command)

            if datalen == 0:  # 沒資料代表不用播動畫
                result = pg_general.Apiresult.success
                return result, clientdata

            command = '''
            SELECT silvercredit, roomcard FROM member WHERE memberid={}
            '''.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                raise ValueError('get member data error')

            mode = deposit_data.get('mode')
            if mode == 2:
                gem_amount = deposit_data.get('amount')
                roomcard_amount = 0

            elif mode == 3:
                gem_amount = 0
                roomcard_amount = deposit_data.get('amount')

            clientdata = {
                'member_id': memberid,
                'credit_s': data.get('silvercredit'),
                'credit_s_amount': gem_amount,
                'roomcard': data.get('roomcard'),
                'roomcard_amount': roomcard_amount,
                'mode': mode,
                'commandid': 3000032
            }

            command = '''
            UPDATE line_trade_log SET animation_mark=1
            WHERE trade_index={}
            '''.format(deposit_data.get('trade_index'))
            updateresult = await self.updatedbdata(logintoken, command)

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:sendlinedepositanimation ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:sendlinedepositanimation Exception:{0}'.format(format_exc()))

        return result, clientdata

    async def playingstatus(self, memberid, logintoken):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:playingstatus , logintoken:{0}, memberid:{1}'
                                .format(logintoken, memberid))

            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = '''
            SELECT playing_game_id from member WHERE memberid={}
            '''.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                clientdata = {
                    "errormsg": "playingstatus: get playing_game_id from member table error"
                }
                result = pg_general.Apiresult.parametererror
                return result, clientdata

            clientdata['game_id'] = data.get('playing_game_id')
            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:playingstatus ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:playingstatus Exception:{0}'.format(format_exc()))

        return result, clientdata

    async def getreddotinfo(self, logintoken, memberid):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getreddotinfo , logintoken:{0},memberid:{1}'.format(logintoken, memberid))

        result = pg_general.Apiresult.connectdberror
        clientdata = []

        now = pg_general.strtodatetime(pg_general.getutcnow())

        try:
            # inbox reddot
            command = 'select dateline,receivestate from memberinbox where memberid ="{0}" and receivestate = "1"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command, True)

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

            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                piggycredit = data.get('piggycredit')
                minipiggytake = data.get('minipiggytake')
                if piggycredit >= minipiggytake:
                    clientdata.append("piggy")

            # gift reddot
            command = 'select * from gift where tomemberid = "{0}" and status="0"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                clientdata.append('gift')

            # freebox reddot
            # freeboxresult, freeboxclientdata = await self.getfreeboxstatus(logintoken,memberid)
            # if freeboxresult == pg_general.Apiresult.success:
            #     if freeboxclientdata.get('enable') == 1:
            #
            #         timeleft = freeboxclientdata.get('timeleft')
            #         gettimes = freeboxclientdata.get('gettimes')
            #         totalamount = freeboxclientdata.get('totalamount')
            #
            #         if timeleft <=0 and totalamount > gettimes:
            #             clientdata.append('freebox')
            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getreddotinfo , except: {0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:getreddotinfo , result:{0},clientdata:{1}'.format(result, clientdata))
            return result, clientdata

    async def getannouncement(self):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:getannouncement')

        result = pg_general.Apiresult.connectdberror
        clientdata = {}
        announcementarray = []
        try:
            command = 'select groupid,comment from announcement'
            datalen, data = await self.getdbdata("getannouncement", command, True)

            if datalen > 0 and data is not None:
                groupid = pg_general.converttype(data[0].get('groupid'), int)
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
            return result, clientdata

    async def do_biggest_multiplier_wins(self, msg_info):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:do_biggest_multiplier_wins , memberid:{0},msg_info:{1}'.format(
                                msg_info.get('memberid'), msg_info))
        result = pg_general.Apiresult.connectdberror

        try:
            total_win = msg_info.get('total_win')
            multipilier = msg_info.get('multipilier')
            memberid = msg_info.get('memberid')
            logintoken = msg_info.get('token')

            command = 'update member set biggestmultiplier="{0}" where memberid="{1}" and biggestmultiplier<"{0}"'.format(
                multipilier, memberid)
            resultbiggestmultiplier = await self.updatedbdata(logintoken, command)

            command = 'update member set biggestwins="{0}" where memberid="{1}" and biggestwins<"{0}"'.format(total_win,
                                                                                                              memberid)
            resultbiggestwins = await self.updatedbdata(logintoken, command)

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

    async def make_free_wheel_action(self, redis_obj, clientdata):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:make_free_wheel_action, clientdata:{}'.format(clientdata))
        result = pg_general.Apiresult.connectdberror

        try:
            result = pg_general.Apiresult.success
            card = clientdata.get('card')

            if card < 2:
                return result
            multipilier = clientdata.get('multipilier')
            if multipilier < 50:
                return result
            logintoken = clientdata.get('token')
            memberid = clientdata.get('memberid')
            tomorrowdateline = (pg_general.get_tw_datetime() + timedelta(days=1)).date().__str__() + ' 15:59:59'
            # 判斷今天是否已經三次
            nowdatestr = pg_general.get_tw_datetime().date().__str__()
            timevalue = await redis_obj.get_value('freewheelaction_{}_{}'.format(memberid, nowdatestr))
            totalfreewheeltimes = await redis_obj.get_value('freewheelaction_acttimes')
            if timevalue is not None:
                if totalfreewheeltimes is None:
                    if pg_general.converttype(timevalue, int) >= 3:
                        return result
                else:
                    if pg_general.converttype(timevalue, int) >= pg_general.converttype(totalfreewheeltimes, int):
                        return result
            # 判斷是否活動期間

            getvalue = await redis_obj.get_value('freewheelaction')
            if getvalue is not None:
                if pg_general.converttype(getvalue, int) == 1:
                    command = 'insert into memberinbox(memberid,inboxuri,mailtype,inboxtitle,inboxcontent,receivestate,dateline,promotionid)values' \
                              '("{0}","uri","7","超級轉輪活動","恭喜您獲得 {1}\n免費超級轉輪一次","1","{2}","29")'.format(
                        memberid, nowdatestr, tomorrowdateline)
                    updateresult = await self.updatedbdata(logintoken, command)
                    await redis_obj.incr('freewheelaction_{}_{}'.format(memberid, nowdatestr))
                    # write action_freewheel_log
                    command = 'insert into action_freewheel_log(memberid,freedate) values("{0}","{1}")'.format(memberid,
                                                                                                               nowdatestr)
                    updateresult = await self.updatedbdata(logintoken, command)




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

        datalen, data = await self.getdbdata('get_all_setting', command)

        if datalen > 0:
            resultdata = {
                "headline_multipilier_content": data.get('headline_multipilier_content'),
                "headline_multipilier_setting": data.get('headline_multipilier_setting'),
                "headline_win_setting": data.get('headline_win_setting'),
                "headline_win_content": data.get('headline_win_content'),
                "fblink": data.get('fblink'),
                "rankminwin": data.get('rankminwin'),
                "rankminmultipilier": data.get('rankminmultipilier')

            }

        command = 'select * from setting2'
        datalen, data = await self.getdbdata('get_all_setting2', command)
        if datalen > 0:
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
            resultdata['gameagreement2'] = data.get('gameagreement2').split('**********')
            resultdata['bigwincontent_publicchat'] = data.get('bigwincontent_publicchat')
            resultdata['bigmultipliercontent_publicchat'] = data.get('bigmultipliercontent_publicchat')
            resultdata['jpenable'] = data.get('jpenable')
            resultdata['jinsongprizeenable'] = data.get('jinsongprizeenable')
        # get cardinfo all data
        command = 'select * from cardinfo order by card'
        datalen, data = await self.getdbdata('get all card info data on initial apiserver', command, True)
        if datalen > 0:
            resultdata['cardinfo'] = data

        result = pg_general.Apiresult.success
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:get_all_settings return, result:{0},resultdata:{1}'.format(result, resultdata))
        return result, resultdata

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

    async def savechatlog(self, logintoken, memberid, tomemberid, roomid, roomtype, type, content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:savechatlog logintoken:{5},memberid:{0},tomemberid:{6},rommid:{1},roomtype:{2},type:{3},content:{4}'.format(
                                    memberid, roomid, roomtype, type, content, logintoken, tomemberid))

            logtime = pg_general.getutcnow_datetime()
            command = 'insert into chatlog (logtime,memberid,tomemberid,roomid,roomtype,type,content) values' \
                      ' ("{0}","{1}","{2}","{3}","{4}","{5}","{6}") '.format(logtime, memberid, tomemberid, roomid,
                                                                             roomtype, type, content)
            insert_result = await self.insertdbdata(logintoken, command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:savechatlog except: {0}'.format(e))

    async def sendtelebot(self, msg):
        try:

            SERVICE_CHATROOM_URL = 'https://api.telegram.org/bot' + '5284330212:AAHCNldt3smmZPE_2G_mn47-c_2Rv3cF1WE' + '/sendMessage?chat_id=' + str(
                -636859017) + '&text={}'.format(msg)
            async with aiohttp.ClientSession() as session:
                async with session.get(SERVICE_CHATROOM_URL, timeout=60) as response:
                    pass
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendtelebot except: {0}'.format(e))

    async def check_black_chat_content(self, logintoken, contentdata):
        try:
            result = False
            command = 'select content from blackchatcontent'
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen > 0:
                for item in data:
                    if item.get('content') in contentdata:
                        result = True
                        break



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:check_black_chat_content except:{} ,contentdata:{}'.format(e, contentdata))
        return result

    async def sendchat_public(self, redis_obj, logintoken, memberid, contentdata):
        try:

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchat_public memberid{0}, logintoken:{1},contentdata:{2}'.format(memberid,
                                                                                                               logintoken,
                                                                                                               contentdata))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # check black content
            result_blackcontent = await self.check_black_chat_content(logintoken, contentdata.get('content'))
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

                command = 'select level,activenumber,card, nickname, avatar from member where memberid ="{0}"'.format(
                    memberid)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen <= 0:
                    raise ValueError('db error or no member data')

                nickname = data.get('nickname')
                avatar = data.get('avatar')
                level = data.get('level')
                card = data.get('card')
                activenumber = data.get('activenumber')

                # if card == 0:
                #     result = pg_general.Apiresult.success
                #     resultdata = {"card_0": True}
                #     return result, resultdata

            nowtime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
            command = 'insert into chatroom_public (chattime,memberid,content_type,content) values ("{0}","{1}","{2}","{3}")' \
                .format(nowtime, memberid, content_type, content)
            result_insert, index_insert = await self.insertdbdata(logintoken, command)

            chattime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')

            if result_insert == True:
                result = pg_general.Apiresult.success
                resultdata = {
                    "time": chattime,
                    "avatar": avatar,
                    "nickname": nickname,
                    "content_type": content_type,
                    "content": content,
                    "memberid": memberid,
                    "card": card,
                    "level": level,
                    "activenumber": activenumber,
                    "isuserflag": isuserflag
                }
                if isuserflag == True:  # user 才紀錄 chatlog
                    asyncio.ensure_future(
                        self.savechatlog(logintoken, memberid, "0", "0", "0", content_type, content))  # 寫道 chatlog

                # save to redis chatroom_public
                await redis_obj.lpush('chatroom_public', json.dumps(resultdata))
                await redis_obj.ltrim('chatroom_public', 0, 100)

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchat_public ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchat_public Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchat_public return, result:{0},resultdata:{1}'.format(result,
                                                                                                     resultdata))
            return result, resultdata

    async def getsettingcontent(self, logintoken, memberid, type):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getsettingcontent memberid{0}, logintoken:{1},type:{2}'.format(memberid,
                                                                                                          logintoken,
                                                                                                          type))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 抓取 content
            command = 'select content from guide where type="{0}"'.format(type)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen > 0:
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
                                'pg_asqldb:getsettingcontent return, result:{0},resultdata:{1}'.format(result,
                                                                                                       resultdata))
            return result, resultdata

    async def getsecretmall(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getsecretmall memberid{0}, logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select secretoffermall.* from secretoffermall,member where member.memberid="{0}" and member.secretmallid = secretoffermall.id'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)

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

    async def senddownloadsignal(self, logintoken, memberid, state, region):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:senddownloadsignal memberid:{0},logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            logtime = pg_general.getutcnow_datetime()
            command = 'insert into downloadsignal (logintoken,state,logtime,region) values ("{0}","{1}","{2}","{3}")'.format(
                logintoken, state, logtime, region)

            result_insert, index = await self.insertdbdata(logintoken, command)

            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:senddownloadsignal Exception except:{0}'.format(e))


        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:senddownloadsignal return, result:{0},resultdata:{1}'.format(result,
                                                                                                        resultdata))
            return result, resultdata

    async def getpiggycredit(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getpiggycredit memberid:{0},logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select member.credit,memberpiggyinfo.piggycredit,setting2.minipiggytake from member,memberpiggyinfo,setting2 where memberpiggyinfo.memberid = "{0}" ' \
                      'and member.memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                minipiggytake = data.get('minipiggytake')
                piggycredit = int(data.get('piggycredit'))
                membercredit = data.get('credit')
                if piggycredit < minipiggytake:
                    raise ValueError('memberid :{0},piggycredit < minipiggytake'.format(memberid))

                command = 'update member , memberpiggyinfo  set member.credit = member.credit + "{1}" , memberpiggyinfo.piggycredit = 0 ' \
                          'where member.memberid = "{0}" and memberpiggyinfo.memberid = "{0}";'.format(memberid,
                                                                                                       piggycredit)

                update_result = await self.updatedbdata(logintoken, command)
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
                        "amount_silver": 0,
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

    async def getfriendlist(self, logintoken, memberid, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getfriendlist memberid:{0},logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {"friendlist": []}

            command = 'select friendlist from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('getfriendlist error 1')

            friendlist = data.get('friendlist')

            if friendlist is not None:
                friendlist = friendlist.strip()
                if len(friendlist) > 0:
                    templist = friendlist.split(',')
                    templist = ['online_' + item for item in templist]
                    resultlist = await redis_obj.mget_json_value(templist)

                    command = 'select memberid,avatar,nickname,level,activenumber,card from member where memberid in ({0})'.format(
                        friendlist)
                    datalen, data = await self.getdbdata(logintoken, command, True)

                    if datalen > 0 and datalen == len(resultlist):
                        for item, itemdata in zip(resultlist, data):
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

    async def getblacklist(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getblacklist memberid:{0},logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {"blacklist": []}

            command = 'select blacklist from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('getblacklist error 1')

            blacklist = data.get('blacklist')

            if blacklist is not None:
                blacklist = blacklist.strip()

                if len(blacklist) > 0:
                    command = 'select memberid,avatar,nickname,level,activenumber,card from member where memberid in ({0})'.format(
                        blacklist)
                    datalen, data = await self.getdbdata(logintoken, command, True)

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

    async def updatefriendlist(self, logintoken, memberid, type, friend_memberid, friend_nickname,
                               redis_object):  # type = 0:add , 1:remove
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updatefriendlist memberid:{0},logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 如果是 type in [2,3] 先找出 memberid
            if type in [2, 3]:
                command = 'select memberid from member where nickname = "{0}"'.format(friend_nickname.strip())
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen == 0:
                    result = pg_general.Apiresult.success
                    resultdata = {"result": 1}  # 找不到此會員
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:updatefriendlist return, result:{0},resultdata:{1}'.format(result,
                                                                                                              resultdata))
                    return result, resultdata
                elif datalen == 1:
                    friend_memberid = data.get('memberid')
                else:
                    raise ('get nickname from member error')

                type -= 2

            # 抓新朋友是否在線
            tempvalue = await redis_object.get_value('online_{}'.format(str(friend_memberid)))
            isonline = True if tempvalue is not None else False

            if type == 0:  # add
                # 抓對象的資料
                command = 'select avatar,nickname,level,activenumber,card from member where memberid="{0}"'.format(
                    friend_memberid)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen == 0:
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
                datalen, data = await self.getdbdata(logintoken, command)
                friendlist = data.get('friendlist')  # .strip()
                if friendlist is not None:
                    if len(friendlist) > 0:
                        friendlist = friendlist.split(',')
                    else:
                        friendlist = []

                    if str(friend_memberid) not in friendlist:  # 不存在, 新增
                        friendlist.append(str(friend_memberid))
                        command = 'update member set friendlist="{0}" where memberid = "{1}"'.format(
                            ','.join(friendlist), memberid)
                        updateresult = await self.updatedbdata(logintoken, command)

                elif friendlist is None:
                    # friendlist.append(str(friend_memberid))
                    command = 'update member set friendlist="{0}" where memberid = "{1}"'.format(friend_memberid,
                                                                                                 memberid)
                    updateresult = await self.updatedbdata(logintoken, command)

            else:  # remove
                # 抓現有的好友名單
                command = 'select friendlist from member where memberid = "{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command)
                friendlist = data.get('friendlist').strip()
                if len(friendlist) > 0:
                    friendlist = friendlist.split(',')
                    if str(friend_memberid) in friendlist:
                        friendlist.remove(str(friend_memberid))
                        if len(friendlist) > 0:
                            command = 'update member set friendlist="{0}" where memberid ="{1}"'.format(
                                ','.join(friendlist), memberid)
                        else:
                            command = 'update member set friendlist="" where memberid = "{0}"'.format(memberid)
                        updateresult = await self.updatedbdata(logintoken, command)
                resultdata = {"result": 0}

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatefriendlist ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatefriendlist Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updatefriendlist return, result:{0},resultdata:{1}'.format(result,
                                                                                                      resultdata))
            return result, resultdata

    async def updateblacklist(self, logintoken, memberid, type, black_memberid, black_nickname):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updateblacklist memberid:{0},logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if type in [2, 3]:
                # if type in [2,3] 確認是否有此 member and get memberid
                command = 'select memberid from member where nickname = "{0}"'.format(black_nickname.strip())
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen == 0:
                    result = pg_general.Apiresult.success
                    resultdata = {"result": 1}  # 找不到此會員
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:updateblacklist return, result:{0},resultdata:{1}'.format(result,
                                                                                                             resultdata))
                    return result, resultdata
                elif datalen == 1:
                    black_memberid = data.get('memberid')
                else:
                    raise ('get nickname from member error')

                type -= 2

            # memberid *
            # avatar *
            # nickname *
            # level *
            # activenumber *
            # card *
            # 抓此為黑名單的資料
            command = 'select avatar, nickname, level, activenumber,card from member where memberid="{0}"'.format(
                black_memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get black memberid is error')

            black_avatar = data.get('avatar')
            black_nickname = data.get('nickname')
            black_level = data.get('level')
            black_activenumber = data.get('activenumber')
            black_card = data.get('card')

            if type == 0:  # add

                # 抓現有的列表
                command = 'select blacklist from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen != 1:
                    raise ValueError('get blacklist error')

                blacklist = data.get('blacklist')  # .strip()
                if blacklist is not None:
                    if len(blacklist) == 0:
                        blacklist = []
                    else:
                        blacklist = blacklist.split(',')

                    if str(black_memberid) not in blacklist:
                        blacklist.append(str(black_memberid))
                        # udpate black list to db
                        command = 'update member set blacklist="{0}" where memberid="{1}"'.format(','.join(blacklist),
                                                                                                  memberid)
                        updateresul = await self.updatedbdata(logintoken, command)

                elif blacklist is None:
                    command = 'update member set blacklist="{0}" where memberid="{1}"'.format(black_memberid, memberid)
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


            else:  # remove
                command = 'select blacklist from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen != 1:
                    raise ValueError('get blacklist error')
                blacklist = data.get('blacklist').strip()

                if len(blacklist) > 0:
                    blacklist = blacklist.split(',')
                    if str(black_memberid) in blacklist:
                        blacklist.remove(str(black_memberid))
                        # update black list to db
                        command = 'update member set blacklist="{0}" where memberid = "{1}"'.format(','.join(blacklist),
                                                                                                    memberid)
                        updateresult = await self.updatedbdata(logintoken, command)
                    resultdata = {"result": 0}
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateblacklist ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateblacklist Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updateblacklist return, result:{0},resultdata:{1}'.format(result,
                                                                                                     resultdata))
            return result, resultdata

    async def safetask(self, logintoken, memberid, type, amount=None):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:safetask memberid:{0},logintoken:{1} , type:{2},amount:{3}'.format(memberid,
                                                                                                              logintoken,
                                                                                                              type,
                                                                                                              amount))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select credit,safe from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get safe amount error')

            credit = data.get('credit')
            safeamount = data.get('safe')

            if type == 2:  # 查詢保險箱裡的分數
                resultdata = {
                    "credit": credit,
                    "safeamount": safeamount,
                    "errcode": 0
                }

            elif type == 0:  # 存入
                if amount > credit:
                    resultdata = {
                        "credit": 0,
                        "safeamount": 0,
                        "errcode": 1,
                        "errdescription": '金幣餘額不足'
                    }
                elif amount < 1:
                    result = pg_general.Apiresult.parametererror
                    raise ValueError('amount < 1')
                else:
                    command = 'update member set credit=credit-"{0}",safe=safe+"{0}" where memberid = "{1}"'.format(
                        amount, memberid)
                    updateresult = await self.updatedbdata(logintoken, command)
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
                        asyncio.ensure_future(self.writetransactionlog(logintoken, param))
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
                    command = 'update member set credit = credit + "{0}",safe= safe-"{0}" where memberid = "{1}"'.format(
                        amount, memberid)
                    updateresult = await self.updatedbdata(logintoken, command)
                    if updateresult == True:
                        resultdata = {
                            "credit": credit + amount,
                            "safeamount": safeamount - amount,
                            "errcode": 0
                        }
                        param = {
                            "frommemberid": memberid,
                            "tomemberid": memberid,
                            "type": pg_general.transactiontype.getfromsafe,
                            "amount": amount,
                            "otherdata": "getfromsafe"
                        }
                        asyncio.ensure_future(self.writetransactionlog(logintoken, param))
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
                                'pg_asqldb:safetask return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def webapi_serial_input(self, logintoken, memberid, serial):
        """送序號禮物

        1. 處理資料，整理序號、資料庫撈序號的資料、判斷是否過期、玩家是否有資格領取
        2. 根據序號的型別進行不同的處理
        3. 通用型
        3.1 是否有領取過相同類型的禮物，有則直接回傳
        3.2 如果有數量限制就更新該序號的領取數量
        3.3 將禮物寫入玩家的資料表中
        3.4 寫領取 LOG & traction LOG
        4. 一般型
        4.1 檢查該序號是否可以使用，若無法則回傳
        4.2 是否有領取過相同類型的禮物，有則直接回傳
        4.3 將禮物寫入玩家的資料表中
        4.4 寫領取 LOG & traction LOG
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:serialinput memberid:{0},logintoken:{1} , serial:{2}'.format(memberid,
                                                                                                        logintoken,
                                                                                                        serial))
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
                resultdata['errdescription'] = 'serial is ""'
                return result, resultdata

            # 全部轉小寫
            serial = serial.lower()

            prefix = serial[:3]
            serialvalueinput = serial[3:]

            command = 'select * from serialmode where prefix = "{0}" and enable = 1'.format(prefix)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = 'no serialmode data'
                return result, resultdata

            serialvalue = data.get('serialvalue')
            modetype = data.get('modetype')
            duration = json.loads(data.get('duration'))
            leftamount = data.get('leftamount')
            awardcontent = json.loads(data.get('awardcontent'))
            amountlimitflag = data.get('amountlimitflag')
            serialmodeindex = data.get('serialmodeindex')
            groupnum = data.get('groupnum')
            limitation = json.loads(data.get('limitation'))

            if None in [serialmodeindex, modetype, duration, leftamount, awardcontent, amountlimitflag, groupnum,
                        limitation]:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = 'serialmode data has none'
                return result, resultdata

            if modetype == 0:
                if serialvalue != serialvalueinput:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = 'modetype=0 and serialvalue error'
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

            if False in [starttimepass, endtimepass]:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉!! 此序號已過期或尚未開始,謝謝您!!'
                return result, resultdata

            # 共用序號模式 有數量限制 數量 <=0 代表發完
            if modetype == 0 and leftamount <= 0 and amountlimitflag == 1:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉!! 此序號已達發送數量,已無法取得獎勵!!'
                return result, resultdata

            award = awardcontent.get('award', 0)
            award_s = awardcontent.get('award_s', 0)

            # get member data
            command = 'select card,level from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = 'no member data'
                return result, resultdata

            membercard = data.get('card')
            memberlevel = data.get('level')

            # 檢查 limitation 是否有達到
            if membercard < limitation_card:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉,您的卡別未達,無法領取,謝謝您!!'
                return result, resultdata

            if memberlevel < limitation_level:
                result = pg_general.Apiresult.success
                resultdata['errdescription'] = '很抱歉,您的等級未達,無法領取,謝謝您!!'
                return result, resultdata

            if modetype == 0:  # 共用序號
                # 查詢是否有領過同一種序號
                command = 'select * from seriallog where memberid="{0}" and (serialmodeindex="{1}" or groupnum="{2}")'.format(
                    memberid, serialmodeindex, groupnum)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen >= 1:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = '您已經領過搂,無法重複領取喔,謝謝您!!'
                    return result, resultdata

                # 更新 serialmode leftamount
                if amountlimitflag == 1:
                    command = 'update serialmode set leftamount = leftamount-1 where serialmodeindex = "{0}"'.format(
                        serialmodeindex)
                    updateresult = await self.updatedbdata(logintoken, command)

                # 更新玩家 roomcard ,silvercredit
                command = 'update member set roomcard= roomcard+"{0}",silvercredit= silvercredit+"{1}" where memberid="{2}"'.format(
                    award, award_s, memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                # 寫 log
                command = 'insert into seriallog(usedtime,memberid,award,award_s,modetype,prefix,serialvalue,serialmodeindex,groupnum)values' \
                          '("{}","{}","{}","{}","{}","{}","{}","{}","{}")'.format(nowdatetimeutc, memberid, award,
                                                                                  award_s, modetype, prefix,
                                                                                  serialvalue, serialmodeindex,
                                                                                  groupnum)
                updateresult = await self.updatedbdata(logintoken, command)

                # get member roomcard, silvercredit
                credit = 0
                silvercredit = 0
                command = 'select roomcard,silvercredit from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                if datalen == 1:
                    credit = data.get('roomcard')
                    silvercredit = data.get('silvercredit')

                # write transaction log
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.serial,
                    "amount": award,
                    "amount_silver": award_s,
                    "otherdata": 'award:{},award_s:{},modetype:{},serialmodeindex:{}'.format(award, award_s, modetype,
                                                                                             serialmodeindex)
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

                awardstr = "恭喜您獲得獎勵 !!"
                if award > 0:
                    awardstr = awardstr + ' 房卡 {} '.format(award)
                if award_s > 0:
                    awardstr = awardstr + ' 寶石 {}'.format(award_s)

                resultdata = {
                    "credit": credit,
                    "silvercredit": silvercredit,
                    "errcode": 0,
                    "errdescription": awardstr,
                    "award": award,
                    "award_s": award_s
                }
            else:  # modetype ==1

                command = 'select * from serialtable where serialvalue = "{0}" and  modeindex = "{1}"'.format(
                    serialvalueinput, serialmodeindex)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen != 1:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = 'modetype == 1 has serialtable data error'
                    return result, resultdata
                serialtableindex = data.get('serialtableindex')
                used = data.get('used')
                if used == 1:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = '此序號已被使用過, 請重新輸入!!'
                    return result, resultdata

                # 查詢是否有領過同一種序號
                command = 'select * from seriallog where memberid="{0}" and modetype=1 and (serialmodeindex="{1}" or groupnum="{2}")'.format(
                    memberid, serialmodeindex, groupnum)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen >= 1:
                    result = pg_general.Apiresult.success
                    resultdata['errdescription'] = '您已經領過搂,無法重複領取喔,謝謝您!!'
                    return result, resultdata

                # update serialtable
                command = 'update serialtable set used = 1,usedtime="{0}" where serialtableindex="{1}" '.format(
                    nowdatetimeutc, serialtableindex)
                updateresult = await self.updatedbdata(logintoken, command)

                # update member roomcard, silvercredit
                command = 'update member set roomcard=roomcard+"{0}",silvercredit=silvercredit+"{1}" where memberid ="{2}"'.format(
                    award, award_s, memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                # 寫 log
                command = 'insert into seriallog(usedtime,memberid,award,award_s,modetype,prefix,serialvalue,serialmodeindex,groupnum)values' \
                          '("{}","{}","{}","{}","{}","{}","{}","{}","{}")'.format(nowdatetimeutc, memberid, award,
                                                                                  award_s,
                                                                                  modetype, prefix, serialvalueinput,
                                                                                  serialmodeindex, groupnum)
                updateresult = await self.updatedbdata(logintoken, command)

                # get member roomcard, silvercredit
                credit = 0
                silvercredit = 0
                command = 'select roomcard,silvercredit from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                if datalen == 1:
                    credit = data.get('roomcard')
                    silvercredit = data.get('silvercredit')

                # write transaction log
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.serial,
                    "amount": award,
                    "amount_silver": award_s,
                    "otherdata": 'award:{},award_s:{},modetype:{},serialmodeindex:{},serialtableindex:{}'.format(award,
                                                                                                                 award_s,
                                                                                                                 modetype,
                                                                                                                 serialmodeindex,
                                                                                                                 serialtableindex)
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

                awardstr = "恭喜您獲得獎勵 !!"
                if award > 0:
                    awardstr = awardstr + ' 房卡 {} '.format(award)
                if award_s > 0:
                    awardstr = awardstr + ' 寶石 {}'.format(award_s)

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
                                'pg_asqldb:serialinput return, result:{0},resultdata:{1}'.format(result, resultdata))
        return result, resultdata

    async def makelike(self, logintoken, memberid, likememberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makelike memberid:{0},logintoken:{1} , likememberid:{2}'.format(memberid,
                                                                                                           logintoken,
                                                                                                           likememberid))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 紀錄 like log
            logtime = pg_general.getutcnow_datetime()
            command = 'insert into likelog (logtime,frommemberid,tomemberid) values("{0}","{1}","{2}")'.format(logtime,
                                                                                                               memberid,
                                                                                                               likememberid)
            updateresult = await self.updatedbdata(logintoken, command)

            # update member.likeamount
            command = 'update member set likeamount = likeamount+1 where memberid = "{0}"'.format(likememberid)
            updateresult = await self.updatedbdata(logintoken, command)

            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makelike ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makelike Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makelike return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def sendprivatchat(self, logintoken, memberid, chatmemberid, type, content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendprivatchat memberid:{0},logintoken:{1} , chatmemberid:{2},type:{3},content:{4}'.format(
                                    memberid, logintoken, chatmemberid, type, content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # check black content
            result_blackcontent = await self.check_black_chat_content(logintoken, content)
            if result_blackcontent == True:
                result = pg_general.Apiresult.success
                resultdata = {"black_chat_content": True}
                return result, resultdata

            # 紀錄 chatlog
            nowdatetime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')

            command = 'select blacklist from member where memberid="{0}"'.format(chatmemberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen > 0:
                blacklist = data.get('blacklist')
                if blacklist is not None:
                    if str(memberid) in blacklist.split(','):
                        result = pg_general.Apiresult.blackme
                        return result, resultdata

            # 抓 基本資料
            command = 'select avatar,nickname,card,level,activenumber from member where memberid = "{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:
                card = data.get('card')
                # if card ==0:
                #     result = pg_general.Apiresult.success
                #     resultdata ={"card_0": True}
                #     return result, resultdata

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
                asyncio.ensure_future(
                    self.savechatlog(logintoken, memberid, chatmemberid, "0", "0", type, content))  # 寫道 chatlog
                result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendprivatchat ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendprivatchat Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendprivatchat return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def sendphonevalidate(self, logintoken, memberid, phone):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendphonevalidate memberid:{0},logintoken:{1},phone:{2}'.format(
                                    memberid, logintoken, phone))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            # 確認格式是否正確
            if phone.isdigit() == False:
                result = pg_general.Apiresult.success
                resultdata = {'result': 2}
                raise ValueError("phone number is wrong", pg_general.PG_LogerLevel.warn)

            # 檢查是否是 門號黑名單 如果是的話 直接 封鎖
            command = 'select phone from blackphone where phone = "{0}"'.format(phone)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:  # 是黑名單
                command = 'update member set enable ="3" where memberid="{0}"'.format(memberid)
                updateresult2 = await self.updatedbdata(logintoken, command)
                return result, resultdata

            # 抓取此會員綁定狀態
            command = 'select phone , phonebindstatus,phonevalidatecode,phonevalidatetime from member where memberid="{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member phone status error', pg_general.PG_LogerLevel.error)

            member_phone = data.get('phone')
            member_phonebindstatus = data.get('phonebindstatus')
            member_phonevalidatecode = data.get('phonevalidatecode')
            member_phonevalidatetime = data.get('phonevalidatetime')

            nowdatetime = pg_general.getutcnow_datetime()
            difftime = (nowdatetime - member_phonevalidatetime).total_seconds()

            if None in [member_phone, member_phonebindstatus, member_phonevalidatecode, member_phonevalidatetime]:
                raise ValueError('get member phone data error', pg_general.PG_LogerLevel.error)

            if member_phonebindstatus == 2:
                resultdata = {"result": 1}
            elif member_phonebindstatus == 1 and difftime <= 60:
                resultdata = {'result': 4}
            elif (member_phonebindstatus == 1 and difftime > 60) or member_phonebindstatus == 0:
                # # 搜尋此手機是否綁定過
                command = 'select memberid , phone from member where phone = "{0}"'.format(phone)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen > 0:
                    result = pg_general.Apiresult.success
                    resultdata = {'result': 3}
                    raise ValueError('this number is used', pg_general.PG_LogerLevel.warn)

                validatecode = random.randint(100000, 999999)
                # 發送 code to phone
                await pg_sms.sendsms(phone, validatecode)

                # 紀錄 db
                command = 'update member set phonebindstatus=1,phonevalidatecode="{0}",phonevalidatetime="{1}",tempphone="{3}" where memberid = "{2}"'.format(
                    validatecode, nowdatetime, memberid, phone)
                updateresult = await self.updatedbdata(logintoken, command)
                resultdata = {'result': 0}

                # insert into phonevalidatelog
                command = 'insert into phonevalidatelog (logtime,phone,memberid,validatecode) values("{0}","{1}","{2}","{3}")'.format(
                    nowdatetime, phone, memberid, validatecode)
                insertresult = await self.updatedbdata(logintoken, command)
            result = pg_general.Apiresult.success

        except ValueError as e:
            description, loglevel = e.args
            pg_general.writelog(loglevel,
                                'pg_asqldb:sendphonevalidate ValueError except:{0}'.format(description))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendphonevalidate Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendphonevalidate return, result:{0},resultdata:{1}'.format(result,
                                                                                                       resultdata))
            return result, resultdata

    async def sendemailvalidate(self, logintoken, memberid, email):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendemailvalidate memberid:{0},logintoken:{1},email:{2}'.format(
                                    memberid, logintoken, email))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            # 確認格式是否正確
            if "@" not in email:
                result = pg_general.Apiresult.success
                resultdata = {
                    'result': 2
                }
                raise ValueError("email format is wrong", pg_general.PG_LogerLevel.warn)

            # 檢查是否是 黑名單信箱 如果是的話 直接 封鎖
            command = 'select email from blackemail where email = "{0}"'.format(email)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:  # 是黑名單
                command = 'update member set enable ="3" where memberid="{0}"'.format(memberid)
                updateresult2 = await self.updatedbdata(logintoken, command)
                return result, resultdata

            # 抓取此會員綁定狀態
            command = 'select email, emailbindstatus, emailvalidatecode, emailvaliddatetime from member where memberid="{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member email status error', pg_general.PG_LogerLevel.error)

            member_email = data.get('email')
            member_emailbindstatus = data.get('emailbindstatus')
            member_emailvalidatecode = data.get('emailvalidatecode')
            member_emailvalidatetime = data.get('emailvaliddatetime')

            nowdatetime = pg_general.strtodatetime(pg_general.getutcnow())

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendemailvalidate type nowdatetime:{0}, nowdatetime:{1} , type member_emailvalidatetime:{2}, member_emailvalidatetime:{3}'.format(
                                    type(nowdatetime), nowdatetime, type(member_emailvalidatetime),
                                    member_emailvalidatetime))

            difftime = pg_general.converttype((nowdatetime - member_emailvalidatetime).total_seconds(), int)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendemailvalidate member_email:{0}, member_emailbindstatus:{1} , member_emailvalidatecode:{2}, member_emailvalidatetime:{3}'.format(
                                    member_email, member_emailbindstatus, member_emailvalidatecode,
                                    member_emailvalidatetime))

            if None in [member_email, member_emailbindstatus, member_emailvalidatecode, member_emailvalidatetime]:
                raise ValueError('get member email data error', pg_general.PG_LogerLevel.error)

            if member_emailbindstatus == 2:
                resultdata = {"result": 1}
            elif member_emailbindstatus == 1 and difftime <= 60:
                resultdata = {'result': 4}
            elif (member_emailbindstatus == 1 and difftime > 60) or member_emailbindstatus == 0:
                # # 搜尋此信箱是否綁定過
                command = 'select memberid , email from member where email = "{0}"'.format(email)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen > 0:
                    result = pg_general.Apiresult.success
                    resultdata = {'result': 3}
                    raise ValueError('this email is used', pg_general.PG_LogerLevel.warn)

                validatecode = str(random.randint(100000, 999999))

                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                    'pg_asqldb:sendemail email:{0},validatecode:{1}'.format(
                                        email, validatecode))

                # 發送 code to phone
                await pg_sms.sendemail(email, validatecode)

                # 紀錄 db
                command = 'update member set emailbindstatus=1, emailvalidatecode="{0}",emailvaliddatetime="{1}",tempemail="{3}" where memberid = "{2}"'.format(
                    validatecode, nowdatetime, memberid, email)
                updateresult = await self.updatedbdata(logintoken, command)
                resultdata = {'result': 0}

                # insert into phonevalidatelog
                command = 'insert into emailvalidatelog (logtime, email, memberid, validatecode) values("{0}", "{1}", "{2}", "{3}")'.format(
                    nowdatetime, email, memberid, validatecode)
                insertresult = await self.updatedbdata(logintoken, command)
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendemailvalidate ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendemailvalidate Exception except:{0}'.format(format_exc()))

        return result, resultdata

    async def feedbackvalidatecode(self, logintoken, memberid, code):
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
                resultdata = {'result': 2}
                raise ValueError('code is wrong', pg_general.PG_LogerLevel.warn)

            # get member 驗證相關資料
            command = 'select card,phone,tempphone,phonebindstatus,phonevalidatecode,phonevalidatetime,setting2.bindphonereward,setting2.bindphonecardminindex from member,setting2 where memberid="{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member data error', pg_general.PG_LogerLevel.error)

            card = data.get('card')
            phone = data.get('phone')
            tempphone = data.get('tempphone')
            phonebindstatus = data.get('phonebindstatus')
            phonevalidatecode = data.get('phonevalidatecode')
            phonevalidatetime = data.get('phonevalidatetime')
            bindphonereward = data.get('bindphonereward')
            bindphonecardminindex = data.get('bindphonecardminindex')

            if phonebindstatus == 2:
                result = pg_general.Apiresult.success
                resultdata = {'result': 3}
                raise ValueError('already bind phone', pg_general.PG_LogerLevel.warn)

            if phonebindstatus != 1:
                result = pg_general.Apiresult.success
                resultdata = {'result': 4}
                raise ValueError('phonebindstatus is not 1', pg_general.PG_LogerLevel.warn)

            nowdatetime = pg_general.getutcnow_datetime()
            if (nowdatetime - phonevalidatetime).total_seconds() > 600:  # 驗證時間超過 10 分鐘
                result = pg_general.Apiresult.success
                resultdata = {'result': 1}
                raise ValueError('validate over 600 seconds', pg_general.PG_LogerLevel.warn)

            if code != phonevalidatecode:
                result = pg_general.Apiresult.success
                resultdata = {'result': 2}
                raise ValueError('validate number is wrong with db', pg_general.PG_LogerLevel.warn)

            param = ''
            cardlevelupflag = False
            if bindphonecardminindex > card:
                param = ',card="{0}",cardlevelchangetime="{1}"'.format(bindphonecardminindex, nowdatetime)
                cardlevelupflag = True

            yesterdaydatetime = phonevalidatetime - timedelta(days=1)
            # 通過驗證
            command = 'update member set phone="{0}",phonebindstatus="2",credit=credit+"{2}",phonevalidatetime="{4}"{3} where memberid="{1}"'.format(
                tempphone, memberid, bindphonereward, param, yesterdaydatetime)
            updateresult = await self.updatedbdata(logintoken, command)

            if cardlevelupflag == True:  # write cardlevelchangelog
                # write 升級卡別 log
                asyncio.ensure_future(
                    self.writecardchangelog([[memberid, nowdatetime, card, bindphonecardminindex, 'bindphone']]))

            # get credit and card
            command = 'select card,credit from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command, False, True)
            resultdata = {
                'result': 0,
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
            description, loglevel = e.args
            pg_general.writelog(loglevel,
                                'pg_asqldb:feedbackvalidatecode ValueError except:{0}'.format(description))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:feedbackvalidatecode Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:feedbackvalidatecode return, result:{0},resultdata:{1}'.format(result,
                                                                                                          resultdata))
            return result, resultdata

    async def feedbackemailvalidatecode(self, logintoken, memberid, code):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:feedbackemailvalidatecode memberid:{0}, logintoken:{1}, code:{2}'.format(
                                    memberid, logintoken, code))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 檢查驗證碼格式是否有錯
            code = code.strip()
            if code.isdigit() == False:
                result = pg_general.Apiresult.success
                resultdata = {'result': 2}
                raise ValueError('code is wrong', pg_general.PG_LogerLevel.warn)

            # get member 驗證相關資料
            command = 'select card,email,tempemail, emailbindstatus, emailvalidatecode, emailvaliddatetime, setting2.bindemailreward, setting2.bindemailcardminindex from member,setting2 where memberid="{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member data error', pg_general.PG_LogerLevel.error)

            card = data.get('card')
            phone = data.get('email')
            tempemail = data.get('tempemail')
            emailbindstatus = data.get('emailbindstatus')
            emailvalidatecode = data.get('emailvalidatecode')
            emailvaliddatetime = data.get('emailvaliddatetime')
            bindemailreward = data.get('bindemailreward')
            bindemailcardminindex = data.get('bindemailcardminindex')

            if emailbindstatus == 2:
                result = pg_general.Apiresult.success
                resultdata = {'result': 3}
                raise ValueError('already bind email', pg_general.PG_LogerLevel.warn)

            if emailbindstatus != 1:
                result = pg_general.Apiresult.success
                resultdata = {'result': 4}
                raise ValueError('Has not send the validation code', pg_general.PG_LogerLevel.warn)

            nowdatetime = pg_general.strtodatetime(pg_general.getutcnow())
            difftime = pg_general.converttype((nowdatetime - emailvaliddatetime).total_seconds(), int)
            if difftime > 600:  # 驗證時間超過 10 分鐘
                result = pg_general.Apiresult.success
                resultdata = {'result': 1}
                raise ValueError('validate over 600 seconds', pg_general.PG_LogerLevel.warn)

            if code != emailvalidatecode:
                result = pg_general.Apiresult.success
                resultdata = {'result': 2}
                raise ValueError('validate number is wrong with db', pg_general.PG_LogerLevel.warn)

            param = ''
            cardlevelupflag = False
            if bindemailcardminindex > card:
                param = ',card="{0}",cardlevelchangetime="{1}"'.format(bindemailcardminindex, nowdatetime)
                cardlevelupflag = True

            yesterdaydatetime = emailvaliddatetime - timedelta(days=1)
            command = 'update member set email="{0}", emailbindstatus="2", credit=credit+"{2}", emailvaliddatetime="{4}"{3} where memberid="{1}"'.format(
                tempemail, memberid, bindemailreward, param, yesterdaydatetime)
            updateresult = await self.updatedbdata(logintoken, command)

            if cardlevelupflag == True:  # write cardlevelchangelog
                # write 升級卡別 log
                asyncio.ensure_future(
                    self.writecardchangelog([[memberid, nowdatetime, card, bindemailcardminindex, 'bindemail']]))

            # get credit and card
            command = 'select card, credit from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command, False, True)
            resultdata = {
                'result': 0,
                'aftercredit': data.get('credit'),
                'card': data.get('card')
            }

            if bindemailreward > 0:
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.emailbindreward,
                    "amount": bindemailreward,
                    "otherdata": 'bindemailreward'
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:feedbackemailvalidatecode ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:feedbackemailvalidatecode Exception except:{0}'.format(format_exc()))

        return result, resultdata

    async def getgiftdata(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getgiftdata memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 抓取 member.credit,todaygiftamount,todaygifttimes and cardinfo.maxgiftamount,maxgifttimes
            command = 'select member.membertype,member.card,member.level,member.credit,member.todaygiftamount,member.todaygifttimes,cardinfo.maxgiftamount,cardinfo.maxgifttimes,giftlist,cardinfo.maxgiftlistamount from member,cardinfo' \
                      ' where member.memberid = "{0}" and member.card=cardinfo.card'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get card or member error')

            credit = data.get('credit')
            card = data.get('card')
            level = data.get('level')
            todaygiftamount = data.get('todaygiftamount')
            todaygifttimes = data.get('todaygifttimes')
            todaytotalcreditamount = data.get('maxgiftamount')
            todaytotaltimes = data.get('maxgifttimes')
            membertype = data.get('membertype')

            if card in [2, 3, 4] and level >= 50:
                todaytotalcreditamount = 20000000

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

            giftlistdata = data.get('giftlist')
            maxgiftlistamount = data.get('maxgiftlistamount')

            # 抓取 db.gift
            command = 'select giftindex,frommemberid,tomemberid,gifttime,type,amount,status,password, ' \
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

            datalen, data = await self.getdbdata(logintoken, command, True)
            giftcenter = []
            giftrecord = []

            if datalen > 0:
                # 程序還沒結束的 贈禮
                giftcentertemp = [item for item in data if item.get('status') == 0]
                giftcentertemp = sorted(giftcentertemp, key=lambda k: (k['giftindex']), reverse=True)

                for item in giftcentertemp:
                    giftcenter.append({
                        'num': str(item.get('giftindex')),
                        'memberid': item.get('frommemberid') if item.get('tomemberid') == memberid else item.get(
                            'tomemberid'),
                        'sendtime': pg_general.get_utc_to_local_datetime(item.get('gifttime')).strftime(
                            '%Y-%m-%d %H:%M:%S'),
                        'nickname': item.get('fromnickname') if item.get('tomemberid') == memberid else item.get(
                            'tonickname'),
                        'avatar': item.get('fromavatar') if item.get('tomemberid') == memberid else item.get(
                            'toavatar'),
                        'content': {'type': item.get('type'), 'amount': item.get('amount')},
                        'op': 0 if item.get('tomemberid') == memberid else 1
                    })

                giftrecordtemp = [item for item in data if item.get('status') != 0]
                giftrecordtemp = sorted(giftrecordtemp, key=lambda k: (k['giftindex']), reverse=True)

                for item in giftrecordtemp:
                    giftrecord.append({
                        'num': str(item.get('giftindex')),
                        'memberid': item.get('frommemberid') if item.get('tomemberid') == memberid else item.get(
                            'tomemberid'),
                        'sendtime': pg_general.get_utc_to_local_datetime(item.get('gifttime')).strftime(
                            '%Y-%m-%d %H:%M:%S'),
                        'nickname': item.get('fromnickname') if item.get('tomemberid') == memberid else item.get(
                            'tonickname'),
                        'avatar': item.get('fromavatar') if item.get('tomemberid') == memberid else item.get(
                            'toavatar'),
                        'optype': 0 if item.get('tomemberid') == memberid else 1,
                        'status': item.get('status'),
                        'content': {'type': item.get('type'), 'amount': item.get('amount')}
                    })

            # 抓常用名單的 member data
            giftlist = []
            giftlistamount = 0
            if giftlistdata is not None:
                if len(giftlistdata) > 0:
                    command = 'select memberid,avatar,nickname,level,card,activenumber from member where memberid in ({0})'.format(
                        giftlistdata)
                    datalen, data = await self.getdbdata(logintoken, command, True)

                    if datalen > 0:
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
            giftfreezedata = await self.getgiftfreezedata(logintoken, memberid)

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
                                'pg_asqldb:getgiftdata ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgiftdata Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getgiftdata return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getcardinfo(self, logintoken, memberid, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getcardinfo memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # get member card, cardbuy, cardbet
            command = 'select card from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get memeber card data error')

            card = data.get('card')
            cardbuy = 0
            cardbet = 0

            # 抓 cardbet & cardbuy from redis
            if card in [2, 3, 4, 5]:
                valuelist = await redis_obj.hvals('bethistory_gold_{}'.format(memberid))
                if len(valuelist) > 0:
                    valuelist = list(map(int, valuelist))
                    cardbet = sum(valuelist)

                valuelist = await redis_obj.hvals('cardbuy_{}'.format(memberid))
                if len(valuelist) > 0:
                    valuelist = list(map(int, valuelist))
                    cardbuy = sum(valuelist)

            # get 所有卡的資訊
            command = 'select * from cardinfo order by card'
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen != 6:
                raise ValueError('get cardinfo error')

            itemdata = []
            lifetime = ''

            for item in data:
                tempdata = {}
                tempdata['card'] = item.get('card')

                twomonthaccbuy = item.get('twomonthaccbuy')
                if twomonthaccbuy == -3:
                    tempdata['twomonthaccbuy'] = '-'
                elif twomonthaccbuy == -2:
                    tempdata['twomonthaccbuy'] = 'ការភ្ជាប់តឆា\r\nមទូរស័ព្ទ'  # '綁定門號'
                elif twomonthaccbuy == -1:
                    tempdata['twomonthaccbuy'] = 'ដើមទុន'  # '首儲'
                else:
                    tempdata['twomonthaccbuy'] = format(twomonthaccbuy, ',') + ' USD'

                twomonthaccbet = item.get('twomonthaccbet')
                if twomonthaccbet == -1:
                    tempdata['twomonthaccbet'] = '-'
                else:
                    tempdata['twomonthaccbet'] = format(int(twomonthaccbet / 1000),
                                                        ',') + 'K\n\r(កាក់មាស)'  # 'K\n\r(金幣)'

                dailygiftamount = item.get('maxgiftamount')
                if dailygiftamount == -1:
                    tempdata['dailygiftamount'] = 'គ្មានដែនកំណត់'  # '無限制'
                elif dailygiftamount == 0:
                    tempdata['dailygiftamount'] = '不可'
                else:
                    tempdata['dailygiftamount'] = format(int(dailygiftamount / 1000),
                                                         ',') + 'K\n\r(កាក់មាស)'  # 'K\n\r(金幣)'

                giftlistamount = item.get('maxgiftlistamount')
                if giftlistamount == 0:
                    tempdata['giftlistamount'] = '-'
                else:
                    tempdata['giftlistamount'] = format(giftlistamount, ',')  # + '筆'

                cangetgift = item.get('cangetgift')
                if cangetgift == 0:
                    tempdata['cangetgift'] = '不可'
                else:
                    tempdata['cangetgift'] = '可以'

                cardlifetime = item.get('cardlifetime')
                if cardlifetime == 0:
                    tempdata['cardlifetime'] = 'អចិន្រ្តៃយ៍'  # '永久'
                else:
                    tempdata['cardlifetime'] = '1 ខែ'  # '一個月'

                if item.get('card') == card:
                    lifetime = tempdata['cardlifetime']

                freecoin = item.get('freecoin')
                if freecoin == 0:
                    tempdata['freecoin'] = '-'
                else:
                    tempdata['freecoin'] = format(freecoin) + '\n\rកាក់មាស'  # '金幣'

                keepseatstr = item.get('keepseatstr')
                tempdata['keepseat'] = keepseatstr

                tmpdailybonusinf = item.get('dailybonusinfo')
                tempdata['dailybonusinfo'] = tmpdailybonusinf

                itemdata.append(tempdata)

            # 準備該會員的一些資料
            buypoint = ''
            accbet = ''
            if card in [2, 3, 4]:
                buypoint = format(cardbuy, ',') + ' / ' + format(data[card + 1].get('twomonthaccbuy'),
                                                                 ',') + 'USD'  # '元'
                accbet = format(int(cardbet / 1000), ',') + ' / ' + format(
                    int(data[card + 1].get('twomonthaccbet') / 1000), ',') + 'K'

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

    async def getclubchannellist(self, logintoken, memberid, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getclubchannellist memberid:{0},logintoken:{1}'.format(memberid, logintoken))

            clubchannellist = []

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT clubid FROM memberclub WHERE memberid = {0}'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

            if datalen < 1:
                raise ValueError('get member clubid error')

            for i in range(datalen):
                clubid = data[i].get('clubid')

                command = 'SELECT channelindex, clubname, clubid FROM clubchannel WHERE clubid = {0}'.format(clubid)
                datalenclub, dataclubchannel = await self.getdbdata(logintoken, command)

                if datalenclub < 1:
                    raise ValueError('get clubchannel error')

                redisclubchannellist = await redis_obj.get_all_keys('clubchannel_{0}_*'.format(clubid))
                dataclubchannel['amount'] = len(redisclubchannellist)

                clubchannellist.append(dataclubchannel)

            result = pg_general.Apiresult.success
            resultdata = {
                "clubchannellist": clubchannellist
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getclubchannellist ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getclubchannellist Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getclubchannellist return, result:{0}, resultdata:{1}'.format(result,
                                                                                                         resultdata))
            return result, resultdata

    async def getchannellist(self, logintoken, memberid, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getchannellist memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select channelindex,channelname from channel where enable=1 order by posindex'
            datalen, data = await  self.getdbdata(logintoken, command, True)

            channellist = []
            if datalen < 1:
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
                                'pg_asqldb:getchannellist return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def getchannelmember(self, logintoken, memberid, channelindex, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getchannelmember memberid:{0},logintoken:{1},channelindex:{2}'.format(
                                    memberid, logintoken, channelindex))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # get redis channel all joined member
            channelmemberlist = await redis_obj.get_all_keys('channel_{0}_*'.format(channelindex))
            memberlisttemp = [item.split('_')[2] for item in channelmemberlist]
            memberlist = []
            if len(memberlisttemp) > 0:
                # get all member
                command = 'select memberid,card,level,nickname,avatar from member where memberid in ({})'.format(
                    ','.join(memberlisttemp))
                datalen, data = await self.getdbdata(logintoken, command, True)
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
                                'pg_asqldb:getchannelmember return, result:{0},resultdata:{1}'.format(result,
                                                                                                      resultdata))
            return result, resultdata

    async def getclubchannelmember(self, logintoken, memberid, clubid, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getclubchannelmember memberid:{0},logintoken:{1},clubid:{2}'.format(
                                    memberid, logintoken, clubid))

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # get redis channel all joined member
            channelmemberlist = await redis_obj.get_all_keys('clubchannel_{0}_*'.format(clubid))
            memberlisttemp = [item.split('_')[2] for item in channelmemberlist]
            clubmemberlist = []

            if len(memberlisttemp) > 0:
                # get all member
                command = 'select memberid,card,level,nickname,avatar from member where memberid in ({})'.format(
                    ','.join(memberlisttemp))
                datalen, data = await self.getdbdata(logintoken, command, True)
                for item in data:
                    clubmemberlist.append({
                        "memberid": item.get('memberid'),
                        "card": item.get('card'),
                        "level": item.get('level'),
                        "nickname": item.get('nickname'),
                        "avatar": item.get('avatar')
                    })

            resultdata = {"clubmemberlist": clubmemberlist}
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getclubchannelmember ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getclubchannelmember Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getclubchannelmember return, result:{0},resultdata:{1}'.format(result,
                                                                                                          resultdata))
            return result, resultdata

    async def joinchannel(self, logintoken, memberid, channelindex, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joinchannel memberid:{0},logintoken:{1},channelindex:{2}'.format(
                                    memberid, logintoken, channelindex))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 抓此 channel 人數上限
            command = 'select maxuser from channel where channelindex="{0}" and enable=1'.format(channelindex)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
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
                await redis_obj.set_value('channel_{0}_{1}'.format(channelindex, memberid), '1', 180)

                # update db.member.channel
                command = 'update member set channel="{0}" where memberid="{1}"'.format(channelindex, memberid)
                updateresult = await self.updatedbdata(logintoken, command)

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

    async def joinclubchannel(self, logintoken, memberid, clubid, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joinclubchannel logintoken:{0}, memberid:{1}, clubid:{2}'.format(
                                    logintoken, memberid, clubid))

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 抓此 clubchannel 人數上限
            command = 'select maxuser from clubchannel where clubid="{0}" and enable=1'.format(clubid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get maxuser in channel error')

            maxuser = data.get('maxuser')

            # get all member on this channel at redis
            channelmemberlist = await redis_obj.get_all_keys('clubchannel_{0}_*'.format(clubid))
            if len(channelmemberlist) < maxuser:
                # clear all this member key at redis
                oldmemberchannel = await redis_obj.get_all_keys('clubchannel_*_{0}'.format(memberid))
                for item in oldmemberchannel:
                    await redis_obj.del_key(item)

                # add this member redis data
                await redis_obj.set_value('clubchannel_{0}_{1}'.format(clubid, memberid), '1', 180)

                # update db.member.channel
                command = 'update member set clubchannel="{0}" where memberid="{1}"'.format(clubid, memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                resultdata = {
                    "result": 0
                }
            else:  # 人數超過上限
                resultdata = {
                    "result": 1
                }

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:joinclubchannel ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:joinclubchannel Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joinclubchannel return, result:{0}, resultdata:{1}'.format(result,
                                                                                                      resultdata))

            return result, resultdata

    async def receivegift(self, logintoken, memberid, num, validate_password):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:receivegift memberid:{0},logintoken:{1},num:{2},password:{3}'.format(
                                    memberid, logintoken, num, validate_password))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 撈這筆單
            command = 'select * from gift where giftindex="{0}" and status =0'.format(num)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('receivegift get gift error')

            frommemberid = data.get('frommemberid')
            tomemberid = data.get('tomemberid')
            type = data.get('type')
            amount = data.get('amount')
            password = data.get('password')

            if password == validate_password and str(tomemberid) == memberid:
                # update member.credit
                command = 'update member set credit=credit+"{0}" where memberid = "{1}"'.format(amount, memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                # update gift 該筆狀態
                command = 'update gift set status =1 where giftindex ="{0}"'.format(num)
                updateresult = await self.updatedbdata(logintoken, command)

                # 在撈一次 該會員 credit
                command = 'select credit from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)

                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 0,
                    "aftercredit": data.get('credit')
                }

                # write to transaction log
                param = {
                    "frommemberid": frommemberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.receivegift,
                    "amount": amount,
                    "otherdata": "receivegift"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))


            else:
                resultdata = {
                    "result": 1
                }

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:receivegift ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:receivegift Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:receivegift return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def noticeusercredit(self, redis_obj, memberid, logintoken):
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
            datalen, data = await self.getdbdata(logintoken, command, False, True)

            if datalen == 1:
                credit = data.get('credit')
                silvercredit = data.get('silvercredit')
                sendmsg = {
                    "type": SendMsgType.server_to_client,
                    "logintoken": tologintoken,
                    "msg": {"commandid": 3000016, "data": {"credit": credit, "silvercredit": silvercredit}}
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

    async def rejectgift(self, redis_obj, logintoken, memberid, num):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:rejectgift memberid:{0},logintoken:{1},num:{2}'.format(
                                    memberid, logintoken, num))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 撈這筆單
            command = 'select * from gift where giftindex="{0}" and status=0'.format(num)
            datalen, data = await self.getdbdata(logintoken, command)

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
            command = 'update member set credit=credit+"{0}" where memberid="{1}"'.format(ori_amount, frommemberid)
            updateresult = await self.updatedbdata(logintoken, command)

            # 改 status to 3
            command = 'update gift set status = 3 where giftindex="{0}"'.format(num)
            updateresult = await self.updatedbdata(logintoken, command)

            result = pg_general.Apiresult.success

            # notice user
            asyncio.ensure_future(self.noticeusercredit(redis_obj, frommemberid, logintoken))

            # write to transaction log
            param = {
                "frommemberid": frommemberid,
                "tomemberid": memberid,
                "type": pg_general.transactiontype.rejectgift,
                "amount": ori_amount,
                "otherdata": "rejectgift"
            }
            asyncio.ensure_future(self.writetransactionlog(logintoken, param))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:rejectgift ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:rejectgift Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:rejectgift return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def sendchannelchat(self, redis_obj, logintoken, memberid, channelindex, type, content, bubbleinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchannelchat memberid:{0},logintoken:{1},channelindex:{2},type:{3},content:{4}'.format(
                                    memberid, logintoken, channelindex, type, content))
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
            command = 'select nickname, level, card, avatar, emailbindstatus from member where memberid="{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get self data error')

            card = data.get('card')
            # if card == 0:
            #     result = pg_general.Apiresult.success
            #     resultdata = {"card_0": True}
            #     return result, resultdata

            # emailbindstatus = data.get('emailbindstatus')
            # if emailbindstatus != 2:
            #     result = pg_general.Apiresult.othererror
            #     resultdata = {
            #         "errormsg": "Please bind the account first"
            #     }
            #     return result, resultdata

            if bubbleinfo == {}:
                bubbleinfo = {
                    "memberid": int(memberid),
                    "nickname": data.get('nickname'),
                    "avatar": data.get('avatar')
                }

            resultdata = {
                "data": {
                    "channelindex": int(channelindex),
                    "memberid": int(memberid),
                    "nickname": data.get('nickname'),
                    "level": pg_general.converttype(data.get('level'), int),
                    "card": pg_general.converttype(data.get('card'), int),
                    "avatar": data.get('avatar'),
                    "type": int(type),
                    "content": content,
                    "time": chattime,
                    "bubbleinfo": bubbleinfo
                }
            }
            # 紀錄 log
            asyncio.ensure_future(
                self.savechatlog(logintoken, memberid, "0", channelindex, "2", type, content))  # save to db.chatlog

            # add to redis chatroom_channel_{}
            redischanneldata = resultdata.get('data')
            await redis_obj.lpush('chatroom_channel_{}'.format(channelindex), json.dumps(redischanneldata))
            await redis_obj.ltrim('chatroom_channel_{}'.format(channelindex), 0, 100)

            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchannelchat ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendchannelchat Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendchannelchat return, result:{0},resultdata:{1}'.format(result,
                                                                                                     resultdata))
            return result, resultdata

    async def sendclubchannelchat(self, redis_obj, logintoken, memberid, clubid, type, content, bubbleinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendclubchannelchat memberid:{0}, logintoken:{1}, clubid:{2}, type:{3}, content:{4}'.format(
                                    memberid, logintoken, clubid, type, content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # check black content
            result_blackcontent = await self.check_black_chat_content(logintoken, content)
            if result_blackcontent == True:
                result = pg_general.Apiresult.success
                resultdata = {
                    "black_chat_content": True
                }
                return result, resultdata

            chattime = pg_general.get_tw_datetime().strftime('%Y-%m-%d %H:%M:%S')
            # 抓自己的 資料
            command = 'select nickname,level,card,avatar from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get self data error')

            bubbleinfo = {
                "memberid": int(memberid),
                "nickname": data.get('nickname'),
                "avatar": data.get('avatar')
            }

            resultdata = {
                "data": {
                    "channelclub": int(clubid),
                    "memberid": int(memberid),
                    "nickname": data.get('nickname'),
                    "level": pg_general.converttype(data.get('level'), int),
                    "card": pg_general.converttype(data.get('card'), int),
                    "avatar": data.get('avatar'),
                    "type": int(type),
                    "content": content,
                    "time": chattime,
                    "bubbleinfo": bubbleinfo
                }
            }

            # 紀錄 log
            asyncio.ensure_future(
                self.savechatlog(logintoken, memberid, "0", clubid, "2", type, content))  # save to db.chatlog

            # add to redis chatroom_channel_{}
            redischanneldata = resultdata.get('data')

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendclubchannelchat redischanneldata:{0}'.format(redischanneldata))

            await redis_obj.lpush('clubchatroom_channel_{}'.format(clubid), json.dumps(redischanneldata))
            await redis_obj.ltrim('clubchatroom_channel_{}'.format(clubid), 0, 100)

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendclubchannelchat ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendclubchannelchat Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendclubchannelchat return, result:{0},resultdata:{1}'.format(result,
                                                                                                         resultdata))
            return result, resultdata

    async def getgameroomchat(self, redis_obj, logintoken, memberid, clubid, roomid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getgameroomchat memberid:{0}, logintoken:{1}, clubid:{2}, roomid:{3}'.format(
                                    memberid, logintoken, clubid, roomid))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            chatinfo_list = []
            chatinfo_reverse = []

            if clubid:
                roomkey = 'club_{0}_room_{1}'.format(clubid, roomid)
                chatroom = 'chatroom_channel_' + roomkey
            else:
                roomkey = 'normal_room_{0}'.format(roomid)
                chatroom = 'chatroom_channel_' + roomkey

            redis_data = await redis_obj.hgetall(roomkey)

            if not redis_data:
                resultdata['errormsg'] = 'no room info'

                raise ValueError('no room info')

            chattime = pg_general.get_th_datetime().strftime('%H:%M')
            # 抓自己的 資料
            command = 'select nickname,level,card,avatar from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get self data error')

            room_player_info = redis_obj.str_to_dict(redis_data.get('room_player_info'))
            chatinfo = await redis_obj.lrange(chatroom, 0, -2)
            chatinfo_reverse = list(reversed(chatinfo))
            chatinfo_list = [json.loads(item.decode('utf-8')) for item in chatinfo_reverse]

            resultdata["talklist"] = chatinfo_list
            resultdata["logintoken"] = logintoken

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgameroomchat ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getgameroomchat Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getgameroomchat return, result:{0},resultdata:{1}'.format(result,
                                                                                                     resultdata))

            return result, resultdata

    async def sendgameroomchat(self, redis_obj, logintoken, memberid, clubid, roomid, content, bubbleinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgameroomchat memberid:{0}, logintoken:{1}, clubid:{2}, roomid:{3}, content:{4}'.format(
                                    memberid, logintoken, clubid, roomid, content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            chatinfo_list = []
            chatinfo_reverse = []
            if clubid:
                type_chat = 4
                roomkey = 'club_{0}_room_{1}'.format(clubid, roomid)
                chatroom = 'chatroom_channel_' + roomkey
            else:
                type_chat = 5
                roomkey = 'normal_room_{0}'.format(roomid)
                chatroom = 'chatroom_channel_' + roomkey

            redis_data = await redis_obj.hgetall(roomkey)

            if not redis_data:
                resultdata['errormsg'] = 'no room info'

                raise ValueError('no room info')

            # check black content
            result_blackcontent = await self.check_black_chat_content(logintoken, content)
            if result_blackcontent == True:
                result = pg_general.Apiresult.success
                resultdata = {
                    "black_chat_content": True
                }
                return result, resultdata

            chattime = pg_general.get_th_datetime().strftime('%H:%M')
            # 抓自己的 資料
            command = 'select nickname,level,card,avatar from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get self data error')

            room_player_info = redis_obj.str_to_dict(redis_data.get('room_player_info'))
            logintoken_ls = [v.get('logintoken') for k, v in room_player_info.items()]

            if bubbleinfo == {}:
                bubbleinfo = {
                    "nickname": data.get('nickname'),
                    "avatar": data.get('avatar'),
                    "time": chattime,
                    "content": content,
                }

            await redis_obj.lpush(chatroom, json.dumps(bubbleinfo))

            chatinfo = await redis_obj.lrange(chatroom, 0, -2)
            chatinfo_reverse = list(reversed(chatinfo))
            chatinfo_list = [json.loads(item.decode('utf-8')) for item in chatinfo_reverse]

            if not chatinfo:
                resultdata['errormsg'] = 'no chatroom info'

                raise ValueError('no room info')

            resultdata["talklist"] = chatinfo_list
            resultdata["logintoken"] = logintoken_ls

            # 紀錄 log
            asyncio.ensure_future(
                self.savechatlog(logintoken, memberid, "0", roomid, "2", type_chat, content))  # save to db.chatlog

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgameroomchat ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgameroomchat Exception except:{0}'.format(format_exc()))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgameroomchat return, result:{0},resultdata:{1}'.format(result,
                                                                                                      resultdata))

            return result, resultdata

    async def signal_action_future(self, redis_obj, logintoken, memberid, content, signaldata):
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
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise Exception('can not get card  phone')

            card = data.get('card')
            phone = data.get('phone')
            level = data.get('level')
            feedbackstr = ''
            if phone == '0':  # 是否綁定手機
                feedbackstr = bindphonefailcontent
                raise ValueError('binphoneerror')
            if card < 2:  # card >=2
                feedbackstr = cardfailcontent
                raise ValueError('cardfail')
            phonereceiveflag = await redis_obj.hget('signal_action_phone_{}'.format(id), phone)
            if phonereceiveflag is not None:  # phone 領過不能領
                feedbackstr = dupphonefailcontent
                raise ValueError('phonereceive')
            memberreceiveflag = await redis_obj.hget('signal_action_member_{}'.format(id), str(memberid))
            if memberreceiveflag is not None:  # member 領過不能領
                feedbackstr = dupmemberfailcontent
                raise ValueError('memberreceive')

            if content.strip() == signal:
                # 答對了 寫入 inbox
                credit_award = 1000 + (level * 5)
                if credit_award >= 3688:
                    credit_award = 3688

                command = 'insert into memberinbox(memberid,inboxuri,mailtype,inboxtitle,inboxcontent,receivestate,dateline,promotionid,credit_award) values' \
                          '("{0}","uri","6","{1}","{2}","1","{3}","{4}","{5}")'.format(memberid, inboxtitle,
                                                                                       inboxcontent, inboxdateline,
                                                                                       promotionid, credit_award)
                insertresult = await self.insertdbdata(logintoken, command)

                # 寫入 redis
                await redis_obj.hset('signal_action_phone_{}'.format(id), phone, '1')
                await redis_obj.hset('signal_action_member_{}'.format(id), str(memberid), '1')

                # 寫入 signallog
                logtime = pg_general.getutcnow_datetime()
                command = 'insert into signallog(memberid,logtime,signalid)values("{0}","{1}","{2}")'.format(memberid,
                                                                                                             logtime,
                                                                                                             id)
                inserresult = await self.insertdbdata(logintoken, command)

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

    async def sendservicechat(self, redis_obj, logintoken, memberid, type, content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendservicechat memberid:{0},logintoken:{1},type:{2},content:{3}'.format(
                                    memberid, logintoken, type, content))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 先做任務 通關密語任務
            signaldata = await redis_obj.get_json_value('signal_action')
            if signaldata is not None:
                asyncio.ensure_future(self.signal_action_future(redis_obj, logintoken, memberid, content, signaldata))

            # get member chatroom_service
            command = 'select * from chatroom_service where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 0:  # 沒資料
                savetime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
                chatlist = [{
                    "time": savetime,
                    "type": type,
                    "content": content}
                ]
                command = 'insert into chatroom_service (memberid,content,flag) values("{0}",\'{1}\',"{2}")'.format(
                    memberid, json.dumps(chatlist, ensure_ascii=False), 0)
                updateresult = await self.updatedbdata(logintoken, command)

            elif datalen == 1:
                chatlist = data.get('content')
                if chatlist != None:
                    chatlist = json.loads(chatlist, encoding='utf-8')

                    savetime = pg_general.getutcnow_datetime().strftime('%Y-%m-%d %H:%M:%S')
                    chatdict = {
                        "time": savetime,
                        "type": type,
                        "content": content
                    }
                    chatlist.append(chatdict)
                    lenofchatlist = len(chatlist)
                    if lenofchatlist > 5:
                        chatlist = chatlist[lenofchatlist - 5:]
                    command = 'update chatroom_service set content=\'{0}\',flag=0 where memberid="{1}"'.format(
                        json.dumps(chatlist, ensure_ascii=False), memberid)
                    udpateresult = await self.updatedbdata(logintoken, command)
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
            asyncio.ensure_future(
                self.savechatlog(logintoken, memberid, "0", 0, "3", type, content))  # save to db.chatlog

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
                                'pg_asqldb:sendservicechat return, result:{0},resultdata:{1}'.format(result,
                                                                                                     resultdata))
            return result, resultdata

    async def sendgift(self, logintoken, memberid, nickname, ori_amount, password, addflag, code):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgift memberid:{0},logintoken:{1},nickname:{2},amount:{3},password:{4},addflag:{5},code:{6}'.format(
                                    memberid, logintoken, nickname, ori_amount, password, addflag, code))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 比對 password 是否為六位數字
            if len(password) != 6 or password.isdigit() == False:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 3
                }
                return result, resultdata

            if ori_amount < 20000:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 4
                }
                return result, resultdata

            # 找對方 memberid , 限制對方比較要為銀卡以上 card > 0
            command = 'select memberid,avatar from member where nickname="{0}" and card > 0'.format(nickname.strip())
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen <= 0:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 2
                }
                return result, resultdata
            tomemberid = data.get('memberid')
            toavatar = data.get('avatar')

            # 檢查驗證碼是否錯誤 或是 驗證碼超過 10 分鐘過期
            command = 'select member.membertype, member.card, member.level, emailbindstatus, emailvalidatecode, emailvaliddatetime, todaygiftamount, todaygifttimes, cardinfo.maxgifttimes, cardinfo.maxgiftamount, member.credit as membercredit, setting2.giftreservecredit from member, cardinfo, setting2 where memberid="{0}" and cardinfo.card = member.card'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member info error')

            membercard = data.get('card')
            memberlevel = data.get('level')
            gifttime = pg_general.getutcnow_datetime()
            maxgifttimes = data.get('maxgifttimes')
            maxgiftamount = data.get('maxgiftamount')
            todaygifttimes = data.get('todaygifttimes')
            todaygiftamount = data.get('todaygiftamount')
            emailbindstatus = data.get('emailbindstatus')
            emailvalidatecode = data.get('emailvalidatecode')
            emailvaliddatetime = data.get('emailvaliddatetime')
            # phonebindstatus = data.get('phonebindstatus')
            # phonevalidatecode = data.get('phonevalidatecode')
            # phonevalidatetime = data.get('phonevalidatetime')
            membercredit = data.get('membercredit')
            giftreservecredit = data.get('giftreservecredit')
            membertype = data.get('membertype')

            if membercard in [2, 3, 4] and memberlevel >= 50:
                maxgiftamount = 20000000

            if membertype != 0:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 9
                }
                return result, resultdata

            if emailbindstatus != 2:  # 手機沒綁定
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 6
                }
                return result, resultdata

            overseconds = pg_general.converttype((gifttime - emailvaliddatetime).total_seconds(), int)
            if overseconds > 600:  # 驗證碼過期
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 5
                }
                return result, resultdata

            if code != emailvalidatecode:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 7
                }
                return result, resultdata

            if todaygifttimes + 1 > maxgifttimes and maxgifttimes != -1:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 8
                }
                return result, resultdata

            if todaygiftamount + ori_amount > maxgiftamount and maxgiftamount != -1:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 9
                }
                return result, resultdata

            lockgiftdata = await self.getgiftfreezedata(logintoken, memberid)
            lockgiftamount = lockgiftdata.get('freezetotalamount')

            # 檢查帳戶是否有大於等於(強制保留值+凍結額度)
            if (membercredit - ori_amount) < (giftreservecredit + lockgiftamount):
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 10
                }
                return result, resultdata

            # 直接扣款順便檢查是否餘額足夠
            command = 'update member set credit = credit - "{0}" , phonevalidatetime="{2}", todaygifttimes=todaygifttimes+1, ' \
                      'todaygiftamount = todaygiftamount + "{3}" where memberid ="{1}" and credit >= "{0}" and credit >= "{4}"'.format(
                ori_amount, memberid, gifttime - timedelta(days=1), ori_amount, (ori_amount + giftreservecredit))
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            if updaterows < 1:  # 餘額不足
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
            asyncio.ensure_future(self.writetransactionlog(logintoken, param))

            type = 0
            amount = int(ori_amount * 0.98)
            status = 0

            # insert into gift table
            command = 'insert into gift (frommemberid,tomemberid,gifttime,type,amount,ori_amount,password,status) values ' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}")'.format(memberid, tomemberid, gifttime, type,
                                                                                 amount, ori_amount, password, status)
            insertresult, rowindex = await self.insertdbdata(logintoken, command)

            if addflag == 1:
                # 加入常用名單
                command = 'select giftlist from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command)
                if datalen > 0:
                    if str(tomemberid) not in data.get('giftlist'):
                        giftlistdata = data.get('giftlist').strip()
                        if len(giftlistdata) == 0:
                            giftlistdata = str(tomemberid)
                        else:
                            giftlistdata = giftlistdata + ',{0}'.format(tomemberid)
                        command = 'update member set giftlist = "{0}" where memberid = "{1}"'.format(giftlistdata,
                                                                                                     memberid)
                        updateresult = await self.updatedbdata(logintoken, command)

            # 抓  todayleftcreditamount todaylefttimes , aftercredit
            # 抓取 member.credit,todaygiftamount,todaygifttimes and cardinfo.maxgiftamount,maxgifttimes
            command = 'select member.card,member.level,member.credit, member.todaygiftamount,member.todaygifttimes,cardinfo.maxgiftamount,cardinfo.maxgifttimes, ' \
                      'member.giftlist from member,cardinfo' \
                      ' where member.memberid = "{0}" and member.card=cardinfo.card'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command, False, True)
            if datalen != 1:
                raise ValueError('get card or member error')

            membercard = data.get('card')
            memberlevel = data.get('level')
            aftercredit = data.get('credit')
            todaygiftamount = data.get('todaygiftamount')
            todaygifttimes = data.get('todaygifttimes')
            todaytotalcreditamount = data.get('maxgiftamount')
            todaytotaltimes = data.get('maxgifttimes')
            giftlist = data.get('giftlist')

            if membercard in [2, 3, 4] and memberlevel >= 50:
                todaytotalcreditamount = 20000000

            if giftlist is not None:
                if len(giftlist.strip()) == 0:
                    giftlistamount = 0
                else:
                    giftlistamount = len(giftlist.split(','))
            else:
                giftlistamount = 0

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
            if giftlist is not None:
                if len(giftlist.strip()) > 0:
                    command = 'select memberid,nickname,avatar,level,activenumber,card from member where memberid in ({})'.format(
                        giftlist)
                    datalen, data = await self.getdbdata(logintoken, command, True)
                    if datalen > 0:
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
                "todayleftcreditamount": todayleftcreditamount,
                "todaylefttimes": todaylefttimes,
                "giftlistamount": giftlistamount,
                "giftlist": updategiftlist,
                "toavatar": toavatar

            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgift ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgift Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgift return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def gettransferdata(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:gettransferdata memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select member.credit from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get member info error')

            membercredit = data.get('credit')

            # amount = INT, status = INT, rate = INT，status預設為0，若判斷可兌換此金額，status會變成1
            # 出金與贈禮共用相同的保留金額度
            command = 'select amount, status from transfer_setting'
            datalen, data = await self.getdbdata(logintoken, command, True)

            pg_general.writelog(pg_general.PG_LogerLevel.error, 'CCCCCCCCCC:{0}'.format(data))
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'CCCCCCCCCC:{0}'.format(datalen))

            pg_general.writelog(pg_general.PG_LogerLevel.error, 'AAAAAAAAAAAAA')
            if datalen <= 0:
                raise ValueError('get transfer_setting info error')
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'BBBBBBBBBBBBB')

            command1 = 'select transfer_cash_rate, giftreservecredit from setting2'
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'CCCCCCCCCCCCC')
            datalen1, data1 = await self.getdbdata(logintoken, command1)

            pg_general.writelog(pg_general.PG_LogerLevel.error, 'DDDDDDDDDDDD:{0}'.format(data1))

            if datalen1 != 1:
                raise ValueError('get setting2 info error')

            rate = data1.get('transfer_cash_rate')
            transferreservecredit = data1.get('giftreservecredit')

            pg_general.writelog(pg_general.PG_LogerLevel.error, 'EEEEEEEEEEE')
            for item in data:
                gold_amount = item['amount'] * rate
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'GGGGGGGGGG:{0}{1}'.format(type(gold_amount), gold_amount))
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'GGGGGGGGGG:{0}{1}'.format(type(item['amount']), item['amount']))
                pg_general.writelog(pg_general.PG_LogerLevel.error, 'GGGGGGGGGG:{0}{1}'.format(type(rate), rate))
                if membercredit - transferreservecredit >= gold_amount:
                    item['status'] = 1

            pg_general.writelog(pg_general.PG_LogerLevel.error, 'FFFFFFFFFFFF')
            result = pg_general.Apiresult.success
            resultdata = {
                "data": data,
                "goldreservecredit": transferreservecredit,  # X2 保留金幣
                "rate": rate  # 當前1USD = 多少金幣的匯率
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:gettransferdata ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:gettransferdata Exception except:{0}'.format(e))

        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:gettransferdata return, result:{0},resultdata:{1}'.format(result,
                                                                                                     resultdata))
            return result, resultdata

    async def savetransferdata(self, logintoken, memberid, member_id, usdamount, banktype, bankacc, bankphone):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:savetransferdata memberid:{0},logintoken:{1},member_id:{2},usdamount:{3},banktype:{4},bankacc:{5},bankphone:{6}'.format(
                                    memberid, logintoken, member_id, usdamount, banktype, bankacc, bankphone))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************aaa")

            # 抓取今日的金幣匯率
            command = 'select setting2.transfer_cash_rate from setting2'
            datalen, data = await self.getdbdata(logintoken, command)

            rate = data.get('transfer_cash_rate')
            goldamount = usdamount * rate  # 匯率轉換

            if goldamount < 1 * rate:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 1  # 最低金幣轉出量至少為5000
                }
                return result, resultdata

            # 抓取保留金的數量

            command = 'select setting2.giftreservecredit from setting2'
            datalen, data = await self.getdbdata(logintoken, command)

            transferreservecredit = data.get('giftreservecredit')

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************eee")

            # 出金與贈禮共用相同的兌換次數與額度設定
            # 抓取會員的卡片類別、金幣數量、今日兌換額度與次數、會員等級
            # 抓取該會員卡片類別的最大兌換次數與額度
            pg_general.writelog(pg_general.PG_LogerLevel.error, '************************mmm:{0}'.format(member_id))
            command1 = 'select member.card, member.credit, member.todaytransferamount, member.todaytransfertimes, member.level ' \
                       'from member where memberid="{0}"'.format(member_id)
            pg_general.writelog(pg_general.PG_LogerLevel.error, '************************nnn{0}'.format(member_id))

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************ooo4")
            datalen1, data1 = await self.getdbdata(logintoken, command1)
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************ooo logintoken{0}'.format(logintoken))
            pg_general.writelog(pg_general.PG_LogerLevel.error, '************************ooo len{0}'.format(datalen1))
            pg_general.writelog(pg_general.PG_LogerLevel.error, '************************ooo item{0}'.format(data1))
            if datalen1 != 1:
                raise ValueError('get member info error')

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************ooo1")

            membercard = data1.get('card')
            pg_general.writelog(pg_general.PG_LogerLevel.error, '************************ooo2{0}'.format(membercard))

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************fff")

            command2 = 'select cardinfo.maxgiftamount, cardinfo.maxgifttimes, cardinfo.card ' \
                       'from cardinfo where cardinfo.card="{0}"'.format(membercard)

            datalen, data2 = await self.getdbdata(logintoken, command2)

            if datalen != 1:
                raise ValueError('get card info error')

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************ggg")

            membercredit = data1.get('credit')
            memberlevel = data1.get('level')
            maxtransferamount = data2.get('maxgiftamount')
            maxtransfertimes = data2.get('maxgifttimes')
            todaytransferamount = data1.get('todaytransferamount')
            todaytransfertimes = data1.get('todaytransfertimes')
            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************xxx")
            transfertime = pg_general.get_cb_datetime_nof()
            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************zzz")

            if membercard not in [2, 3, 4, 5]:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 2  # 您的卡別不為金卡以上
                }
                return result, resultdata

            if membercredit - transferreservecredit < goldamount:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 3  # (帳戶金幣 - 保留金)未達欲轉出金幣量
                }
                return result, resultdata

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************hhh")

            # 贈禮功能裡有多判斷會員等級，並提高贈禮額度，這邊是沿用贈禮功能
            if membercard in [2, 3, 4] and memberlevel >= 50:
                maxtransferamount = 20000000

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************iii")

            # -1為黑卡的設定，排除黑卡
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************1oo logintoken{0}'.format(todaytransfertimes))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************2oo logintoken{0}'.format(maxtransfertimes))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************3oo logintoken{0}'.format(type(todaytransfertimes)))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************4oo logintoken{0}'.format(type(maxtransfertimes)))
            if todaytransfertimes + 1 > maxtransfertimes and maxtransfertimes != -1:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 4  # 已達今日兌換次數
                }
                return result, resultdata

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************jjj")

            # -1為黑卡的設定，排除黑卡
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************7oo logintoken{0}'.format(todaytransferamount))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************8oo logintoken{0}'.format(goldamount))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************9oo logintoken{0}'.format(maxtransferamount))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************10oo logintoken{0}'.format(type(todaytransferamount)))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************11oo logintoken{0}'.format(type(goldamount)))
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                '************************12oo logintoken{0}'.format(type(maxtransferamount)))

            if todaytransferamount + goldamount > maxtransferamount and maxtransferamount != -1:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 5  # 已達今日兌換額度
                }
                return result, resultdata

            # 餘額未超過保留金
            if transferreservecredit > membercredit - goldamount:
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 6  # 已達今日兌換額度
                }
                return result, resultdata

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************000")

            # 今日兌換次數與額度存在member資料表中，這裡是更新今日兌換額度與次數
            command = 'update member set credit = credit - "{0}", todaytransfertimes = todaytransfertimes+1, todaytransferamount = todaytransferamount + "{1}"' \
                      'where memberid ="{2}"'.format(goldamount, goldamount, member_id)
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************111")

            #  memberid = BIGINT, membercard = INT goldamount = BIGINT, usdamount = BIGINT, banktype = VARCHAR, bankacc = VARCHAR, bankphone = VARCHAR
            #  需要一個欄位儲存玩家轉出幾次、時間
            command = 'insert into transfergoldinfo (memberid, membercard, goldamount, usdamount, banktype, bankacc, bankphone, transfertime) values' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}")'.format(member_id, membercard, goldamount,
                                                                                 usdamount, banktype, bankacc,
                                                                                 bankphone, transfertime)

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************222")

            insertresult, rowindex = await self.insertdbdata(logintoken, command)

            pg_general.writelog(pg_general.PG_LogerLevel.error, "************************333")

            result = pg_general.Apiresult.success
            resultdata = {
                "result": 0,
                "credit": membercredit - goldamount
            }

            bankname = ['ABA', 'Wing']
            telebot_msg = ''
            telebot_msg += "Time: {}\n".format(transfertime)
            telebot_msg += "Member ID: {}\n".format(member_id)
            telebot_msg += "ExchangeUSD: {:,}".format(usdamount) + " USD\n"
            telebot_msg += "ExchangeRate: {:,}".format(rate) + "/USD\n"
            telebot_msg += "ExchangeCoin: {:,}\n".format(goldamount)
            telebot_msg += "BankName: {}\n".format(bankname[int(banktype)])
            telebot_msg += "Player's Acc: {}\n".format(bankacc)
            telebot_msg += "Player's Phone: {}\n".format(bankphone)
            asyncio.ensure_future(self.sendtelebot(telebot_msg))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:savetransferdata ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:savetransferdata Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:savetransferdata return, result:{0},resultdata:{1}'.format(result,
                                                                                                      resultdata))
            return result, resultdata

    async def get_member_club_amount(self, member_id):
        """取得該名玩家有幾個俱樂部

        Returns:
            int: 有參加/申請的俱樂部數量
        """
        command = '''SELECT * FROM memberclub
            WHERE memberid={}
        '''.format(member_id)

        datalen, data = await self.getdbdata('get_member_club_number:{}'.format(member_id),
                                             command, fetchall=True)

        log_msg = 'pg_asqldb:create_club count:{} count:{}'.format(
            datalen, datalen)
        pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

        return datalen

    async def _generate_club_id(self, logintoken):
        """產生隨機 7 位數俱樂部編號

        產生後檢查是否重複，不重複就直接回傳
        若執行超過 100 次，就是為失敗，回傳 -1 代表錯誤
        """
        i = 0
        range_start = 10 ** 6
        range_end = (10 ** 7) - 1

        while True:  # 產生房號，若房號重覆就再產生
            i += 1

            club_id = str(randint(range_start, range_end))

            command = 'SELECT clubid FROM club WHERE clubid="{}"'.format(club_id)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                break

            if i == 100:
                return -1

        return club_id

    async def _create_club_insert_club(self, logintoken, club_name, create_time, member_id, club_id):

        insertkey = 'name, createtime, chairmanid, clubid'
        insertvalue = '"{}", "{}", {}, "{}"'.format(club_name, create_time, member_id,
                                                    club_id)
        command = 'INSERT INTO club({}) VALUE({})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)

        return insertresult

    async def _create_club_insert_memberclub(self, logintoken, member_id, club_id, create_time):
        command = '''
            INSERT INTO memberclub(memberid, clubid, jointime, position)
            VALUE({}, "{}", "{}", 0)
        '''.format(member_id, club_id, create_time)

        result, index = await self.insertdbdata(logintoken, command)

        return result

    async def _create_club_insert_clubchannel(self, logintoken, club_name, member_id, create_time, clubid):
        command = '''
            INSERT INTO clubchannel(clubname, ownermemberid, starttime, clubid)
            VALUE("{}", {}, "{}", "{}")
        '''.format(club_name, member_id, create_time, clubid)

        result, index = await self.insertdbdata(logintoken, command)

        return result

    async def _create_club_insert_club_right(self, logintoken, club_id, member_id):
        """
        寫入所有職位權限到 club_right 資料表
        寫入玩家佔成到 host_holding 資料表
        寫入玩家資料到 host_holding 資料表
        """
        cr = ClubRight(club_id)

        for i in range(9):
            command = cr.generate_sql_insert_command(i)
            result, index = await self.insertdbdata(logintoken, command)

            if not result:
                return False

        now_time = pg_general.getutcnow()

        command = '''
            INSERT INTO host_holding(host_id, clubid, upper_host_id, host_level, 
            history, holding, created_at)
            VALUE("{}", "{}", "", 0, "**", 100, "{}")
        '''.format(member_id, club_id, now_time)

        result, index = await self.insertdbdata(logintoken, command)

        if not result:
            return False

        command = '''
            INSERT INTO host_id(host_id, clubid, upper_host_id, host_level, history)
            VALUE("{}", "{}", "", 0, "**")
        '''.format(member_id, club_id)

        result, index = await self.insertdbdata(logintoken, command)

        return result

    async def _get_club_lobby_info_get_data(self, logintoken, club_id, member_id):
        """從資料表撈資料

        1. 撈資料
        1.1. 若查無回傳空 dict
        2.1 將職位轉換成字串
        """

        select_command = '''
            SELECT c.name AS clubname, c.clubid, c.roomcard, c.avatar AS clubavatar,
                c.postmsg, c.introduction, c.applymode, c.line,
                mc.credit, mc.position,
                m.avatar AS playavator, m.nickname  
            FROM club AS c, memberclub AS mc, member AS m
            WHERE c.clubid="{0}"
                AND
                    mc.memberid={1} AND mc.clubid="{0}"
                AND
                    m.memberid={1}
        '''.format(club_id, member_id)

        datalen, data = await self.getdbdata(logintoken, select_command)

        if datalen == 0:
            return {}

        data['position'] = data['position']

        return data

    async def _get_club_lobby_info_get_club_room_setting(self, logintoken, club_id):
        select_command = '''
            SELECT *  FROM club_room_setting WHERE clubid="{}"
        '''.format(club_id)

        datalen, data = await self.getdbdata(logintoken, select_command, fetchall=True)

        if datalen == 0:
            return {}

        return data

    async def _get_club_lobby_info_get_room_info(self, logintoken, redis_obj, club_id):
        room_key = 'club_{}_room_*'.format(club_id)
        room_key_ls = await redis_obj.get_all_keys(room_key)

        room_info_ls = []

        for key in room_key_ls:
            room_info = await redis_obj.hgetall(key)

            for k, v in room_info.items():
                try:  # 有些可能是英數交雜，會出錯，那就讓他維持原本的樣子
                    room_info[k] = eval(v)
                except:
                    pass

            player_info_ls = []  # dict 轉成 list 給前端
            for k, v in room_info['room_player_info'].items():
                v['logintoken'] = k
                player_info_ls.append(v)

            room_info['room_player_info'] = player_info_ls

            room_info_ls.append(room_info)

        return room_info_ls

    async def get_club_lobby_info(self, redis_obj, logintoken, member_id, club_id):
        """取得遊戲大廳所需資料

        1. 撈俱樂部 & 玩家個人資料
        2. 撈開房設定組合資料
        3. 撈現有房間資訊
        """
        try:
            log_msg = '''pg_asqldb:get_club_lobby_info logintoken:{}, member_id:{}, club_id:{}
            '''.format(logintoken, member_id, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            data = await self._get_club_lobby_info_get_data(logintoken, club_id, member_id)

            if len(data) == 0:
                resultdata['errormsg'] = 'get club lobby info error'
                raise ValueError('get club lobby info error')

            for key, value in data.items():  # 把撈到的資料放入 resultdata 中
                resultdata[key] = value

            data = await self._get_club_lobby_info_get_club_room_setting(logintoken, club_id)
            resultdata['roomsetting'] = data

            room_info_ls = await self._get_club_lobby_info_get_room_info(logintoken,
                                                                         redis_obj, club_id)

            resultdata['room_info_list'] = room_info_ls

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_lobby_info ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_lobby_info Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_club_lobby_info return, result:{0},resultdata:{1}'.format(result,
                                                                                                         resultdata))
            return result, resultdata

    async def check_club_name(self, logintoken, member_id, club_name):
        """
        1. 檢查俱樂部名稱是否已經有人命名
        """
        try:
            log_msg = 'pg_asqldb:check_club_name logintoken:{}, member_id:{}, club_name:{}'.format(logintoken,
                                                                                                   member_id, club_name)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT id FROM club WHERE name="{}"'.format(club_name)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 0:
                result = pg_general.Apiresult.connectdberror
                raise ValueError('club_name is duplicate')

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:check_club_name ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:check_club_name Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:check_club_name return, result:{0},resultdata:{1}'.format(result,
                                                                                                     resultdata))
            return result, resultdata

    async def _create_club_get_create_verity(self, logintoken, member_id):
        """取得該名成員是否有權限建立俱樂部

        回傳 0 代表沒有 1 代表有
        """
        # 欄位名稱剛好和語法一樣吧，所以用 ``
        command = '''
            SELECT `right` FROM create_club_verify_list
            WHERE member_id={}
        '''.format(member_id)

        datalen, data = await self.getdbdata('_create_club_get_create_verity:{}'.format(member_id), command)

        if datalen == 0:
            return 0

        log_msg = 'pg_asqldb:get_create_verity'
        pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

        return data.get('right')

    async def create_club(self, logintoken, member_id, club_name, redis_obj):
        """
        檢查俱樂部名稱是否相同
        產生不重複的房號
        檢查玩家是否可建立俱樂部（參與的俱樂部數量 <= 3 & 通過客服審核）
        建立俱樂部資料
            寫入 club 表
            寫入 memberclub 表
            寫入 club_right 表
        """
        try:
            log_msg = 'pg_asqldb:create_club logintoken:{}, member_id:{}, club_name:{}'.format(logintoken, member_id,
                                                                                               club_name)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            check_result, _ = await self.check_club_name(logintoken, member_id, club_name)

            if check_result != 0:
                result = pg_general.Apiresult.parametererror
                raise ValueError('duplicate club name')

            club_amount = await self.get_member_club_amount(member_id)
            if club_amount >= 3:
                raise ValueError('amount of member\'s club over 3')

            create_club_verity = await self._create_club_get_create_verity(
                logintoken, member_id)
            if create_club_verity == 0:
                raise ValueError('you don\'t have right')

            club_id = await self._generate_club_id(logintoken)
            resultdata['clubid'] = club_id

            if club_id == -1:
                result = pg_general.Apiresult.parametererror
                raise ValueError('generate club_id failed')

            create_time = pg_general.getutcnow()

            insert_club_result = await self._create_club_insert_club(logintoken, club_name, create_time,
                                                                     member_id, club_id)

            insert_memberclub_result = await self._create_club_insert_memberclub(logintoken, member_id, club_id,
                                                                                 create_time)

            insert_club_right_result = await self._create_club_insert_club_right(logintoken, club_id, member_id)

            insert_clubchannel_result = await self._create_club_insert_clubchannel(logintoken, club_name, member_id,
                                                                                   create_time, club_id)

            command = 'UPDATE member set clubchannel = {0} WHERE memberid = {1}'.format(club_id, member_id)
            updateresult = await self.updatedbdata(logintoken, command)

            await redis_obj.lpush('clubchatroom_channel_{}'.format(club_id), '{}')

            if insert_club_result and insert_memberclub_result and insert_club_right_result and insert_clubchannel_result:
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.connectdberror

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:create_club ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:create_club Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:create_club return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _apply_club_check_apply_mode(self, logintoken, member_id, club_id):
        """檢查是否符合俱樂部申請條件

        True 代表符合

        1. 撈出俱樂部 apply mode
        2. 根據 apply mode 比對相對應的資料
        2.1 apply mode = 0 直接回傳 True
        3. 取得玩家的登入方式資料
        3.1 apply mode = 1 判斷玩家是否為 line 登入
        3.2 apply mode = 2 判斷玩家是否為非訪客登入
        4. 都沒有通過驗證代表不符合，回傳 Flase
        """
        command = '''SELECT applymode FROM club WHERE clubid="{}"
        '''.format(club_id)
        datalen, data = await self.getdbdata(logintoken, command)

        apply_mode = data.get('applymode')

        if apply_mode == 0:
            return True

        command = '''
        SELECT lineid, username FROM member WHERE memberid={}
        '''.format(member_id)

        datalen, data = await self.getdbdata(logintoken, command)

        if apply_mode == 1 and data.get('lineid'):
            return True

        if apply_mode == 2 and (data.get('lineid') or data.get('username')):
            return True

        return False

    async def _apply_club_check_club_member_limit(self, logintoken, club_id):
        """檢查俱樂部人數是否超過上限值 6000 人
        """
        command = '''
        SELECT COUNT(*) as amount FROM memberclub WHERE clubid="{}"
        '''.format(club_id)
        datalen, data = await self.getdbdata(logintoken, command)

        return data.get('amount') >= 6000

    async def apply_club(self, logintoken, member_id, club_id):
        """
        1. 檢查是否符合俱樂部申請條件
        2. 檢查俱樂部人數是否達到上限
        3. 檢查是否重複申請 & 已加入俱樂部
        4. 寫入到資料表中
        """
        try:
            log_msg = 'pg_asqldb:apply_club logintoken:{}, member_id:{}, club_id:{}'.format(logintoken, member_id,
                                                                                            club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # allow_apply = await self._apply_club_check_apply_mode(logintoken, member_id, club_id)
            # if not allow_apply:
            #     resultdata['errormsg'] = 'the club not allow you apply this club'
            #     raise ValueError('the club not allow you apply this club')

            over_limit = await self._apply_club_check_club_member_limit(logintoken, club_id)

            if over_limit:
                resultdata['errormsg'] = 'the club member number is over 6000'
                raise ValueError('the club member number is over 6000')

            club_amount = await self.get_member_club_amount(member_id)
            if club_amount >= 3:
                raise ValueError('amount of member\' club already over 3!!')

            command = '''SELECT * FROM club_apply_list
                WHERE memberid={} and clubid="{}"
            '''.format(member_id, club_id)

            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:
                raise ValueError('{} has already apply club {}'.format(member_id, club_id))

            command = '''SELECT * FROM memberclub
                WHERE memberid={} and clubid="{}"
            '''.format(member_id, club_id)

            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:
                raise ValueError('{} has already join club {}'.format(member_id, club_id))

            apply_time = pg_general.datetime_to_str(pg_general.getutcnow_datetime())

            command = '''INSERT INTO club_apply_list(memberid, clubid, applytime)
                VALUE({}, "{}", "{}")
            '''.format(member_id, club_id, apply_time)
            apply_result = await self.updatedbdata(logintoken, command)

            if apply_result:
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.connectdberror

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:apply_club ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:apply_club Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:apply_club return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def get_club_apply_list(self, logintoken, club_id):
        """
        從 club_apply_list 表中查詢 玩家資料
        取得玩家的 lastlogintime, joinclubtime

        Returns:
            list: [
                {
                    'memberid': 123456,
                    'lastlogintime': 2022-05-12 14:40:30,
                    'joinclubtime': 2022-05-12 14:40:30
                }, ...
            ]
        """
        try:
            log_msg = 'pg_asqldb:get_club_apply_list logintoken:{}, club_id:{}'.format(
                logintoken, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''
                SELECT cal.memberid, cal.applytime, m.avatar, m.nickname
                FROM club_apply_list AS cal
                LEFT JOIN member AS m ON m.memberid=cal.memberid
                WHERE cal.clubid="{}"
            '''.format(club_id)

            datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

            if datalen == 0:
                data = []  # 沒資料就預設 data 為串列

            for dc in data:
                member_id = dc['memberid']

                lastlogintime = dc.get('lastlogintime', '')

                if lastlogintime != '':  # 若有資料要轉換成字串
                    lastlogintime = pg_general.datetime_to_str(lastlogintime)

                dc['lastlogintime'] = lastlogintime
                dc['applytime'] = pg_general.datetime_to_str(dc['applytime'])

            result = pg_general.Apiresult.success
            resultdata['applydata'] = data

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_apply_list ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_apply_list Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_club_apply_list return, result:{0},resultdata:{1}'.format(result,
                                                                                                         resultdata))
            return result, resultdata

    async def _get_club_member_list_get_game_count(self, logintoken, member_id, club_id):
        """到 PS DB 計算該名玩家的遊玩次數

        accoungint 這張表的 host_id 會等於 club_id
        """
        command = '''
            SELECT COUNT(*) AS c FROM accounting
            WHERE host_id="{}" AND member_id={}
        '''.format(club_id, member_id)

        datalen, data = await self.slot_game_db.getdbdata(logintoken, command)

        if datalen == 0:
            return 0

        return data.get('c')

    async def get_club_member_list(self, redis_obj, logintoken, club_id, member_id, mode):
        """
        取得玩家職位
        撈該職位可見的成員
            館主、管理員、mode 1: 撈所有成員
            各級代理: 自己底下的成員
            一般成員: 同層級成員

        整理出這些成員的 ID，去撈取他們的名稱、登入時間
        最後在將撈出來的資料整理後回傳

        Returns:
            list: [
                {
                    "banchat": 0,
                    "nickname": "龍魂高歌晨星",
                    "lastlogintime": "2020-06-03 17:49:59",
                    "memberid": 24550,
                    "position": 8,
                    "jointime": "2022-05-23 01:49:44",
                    "clubid": "3589863",
                    "proxy": 91403,
                    "banplayergame": 0,
                    "online": True,
                    "avator": "..."
                }, ...
            ]
        """
        try:
            log_msg = 'pg_asqldb:get_club_member_list logintoken:{}, club_id:{}'.format(
                logintoken, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            select_command = '''
                SELECT mc.position, mc.proxy, m.nickname FROM memberclub as mc, member as m
                WHERE mc.memberid={} and mc.clubid="{}" and m.memberid={}
            '''.format(member_id, club_id, member_id)
            datalen, data = await self.getdbdata(logintoken, select_command)

            if datalen == 0:
                raise ValueError('memberclub no {}'.format(member_id))

            position = data.get('position')
            proxy_id = data.get('proxy')
            proxy_nickname = data.get('nickname')

            if position in (0, 7) or mode == 1:  # 館主、管理者撈全部成員
                command = '''
                    SELECT mc.*, m.nickname AS proxynickname 
                    FROM memberclub as mc LEFT JOIN member as m
                    ON m.memberid=mc.proxy
                    WHERE mc.clubid="{}"
                '''.format(club_id)

            elif position == 8:  # 一般成員撈所屬代理成員和代理者
                command = '''
                    SELECT mc.*, m.nickname AS proxynickname 
                    FROM memberclub as mc
                    LEFT JOIN member as m 
                    ON m.memberid=mc.proxy
                    WHERE (mc.clubid="{0}" and mc.proxy={1} and mc.position=8)
                    OR (mc.memberid={1} AND mc.clubid="{0}")
                '''.format(club_id, proxy_id)

            else:  # 代理者，撈出自己和代理下成員
                command = '''
                    SELECT mc.* FROM memberclub as mc
                    LEFT JOIN member as m 
                    ON m.memberid=mc.proxy
                    WHERE (mc.clubid="{0}" and proxy={1})
                    OR (mc.memberid={1} AND mc.clubid="{0}")
                '''.format(club_id, member_id)

            # 撈俱樂部成員資料
            club_member_datalen, club_member_data = await self.getdbdata(logintoken, command, fetchall=True)

            tmp_club_member_dc = {}  # 整理資料時使用
            # 過濾出所有會員 id
            club_member_id_ls = []
            for dc in club_member_data:
                club_member_id_ls.append(str(dc['memberid']))  # 轉成 str 才可以用 join
                tmp_club_member_dc[str(dc['memberid'])] = dc

            # 查詢成員名稱、上次登入時間
            select_command = '''
                SELECT nickname, lastlogintime, memberid, avatar, credit FROM member 
                WHERE memberid IN ({})
            '''.format(','.join(club_member_id_ls))

            info_datalen, info_data = await self.getdbdata(logintoken, select_command, fetchall=True)

            # 檢查資料筆數是否相同
            if info_datalen != club_member_datalen:
                raise ValueError('amount of data error')

            # 整理資料輸出格式
            for dc in info_data:
                tmp_member_id = dc['memberid']

                tmp_dc = tmp_club_member_dc[str(tmp_member_id)]

                del tmp_dc['id']
                tmp_dc['nickname'] = dc['nickname']

                lastlogintime = dc['lastlogintime']
                if lastlogintime != '':  # 若有資料要轉換成字串
                    lastlogintime = pg_general.datetime_to_str(lastlogintime)

                tmp_dc['lastlogintime'] = lastlogintime
                tmp_dc['jointime'] = pg_general.datetime_to_str(tmp_dc['jointime'])
                tmp_dc['avatar'] = dc['avatar']
                tmp_dc['credit'] = dc['credit']

                online_result = await redis_obj.get_value('online_{}'.format(tmp_member_id))
                tmp_dc['online'] = True if online_result is not None else False

                tmp_dc['gamecount'] = await self._get_club_member_list_get_game_count(logintoken, tmp_dc['memberid'],
                                                                                      club_id)

            result = pg_general.Apiresult.success
            resultdata['position'] = position
            resultdata['proxyid'] = proxy_id
            resultdata['proxynickname'] = proxy_nickname
            resultdata['data'] = [v for k, v in tmp_club_member_dc.items()]

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_member_list ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_member_list Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_club_member_list return, result:{0},resultdata:{1}'.format(result,
                                                                                                          resultdata))
            return result, resultdata

    async def _get_club_proxy_list_get_self_data(self, logintoken, club_id, member_id):
        """取得該名成員在俱樂部的資料

        1. 資料表撈資料
        2. 轉換資料
        """
        command = '''
        SELECT mc.memberid, mc.proxy, mc.position, mc.credit, m.avatar, m.nickname, hh.holding
        FROM memberclub AS mc
        LEFT JOIN member AS m ON mc.memberid=m.memberid
        LEFT JOIN host_holding AS hh ON (mc.memberid=hh.host_id AND mc.clubid=hh.clubid)
        WHERE mc.clubid="{}" AND mc.memberid={}
        '''.format(club_id, member_id)

        datalen, data = await self.getdbdata(logintoken, command)

        if datalen == 0:
            raise ValueError('get_club_proxy_list_get_self_data: {} failed'.format(member_id))

        holding = data.get('holding')
        data['holding'] = str(holding) if holding else '0'

        return data

    async def _get_club_proxy_list_get_proxy_data(self, logintoken, club_id, member_id, position):
        """取得該名成員在俱樂部內可以看到的代理人

        1. 資料表撈資料
        2. 轉換資料
        """
        p = position + 1 if position < 6 else -1  # 只有五級代理以上的人可能會有代理者，-1 就撈不到資料這樣

        command = '''
        SELECT mc.memberid, mc.proxy, mc.position, mc.credit, m.avatar, m.nickname, hh.holding
        FROM memberclub AS mc
        LEFT JOIN member AS m ON mc.memberid=m.memberid
        LEFT JOIN host_holding AS hh ON mc.memberid=hh.host_id
        WHERE mc.clubid="{}" AND mc.proxy={} AND mc.position={}
        '''.format(club_id, member_id, p)

        datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

        if data is None:
            data = []

        for dc in data:
            holding = dc.get('holding')
            dc['holding'] = str(holding) if holding else '0'

        return data

    async def get_club_proxy_list(self, redis_obj, logintoken, club_id, member_id, position):
        """取得該職位底下的代理人

        1. 撈查詢者的資料
        2. 撈查詢者可見的代理

        Args:
            member_id (int): 查看者的 ID
            position (int): 查看者的代理階級
        """
        try:
            log_msg = 'pg_asqldb:get_club_proxy_list logintoken:{}, club_id:{}'.format(
                logintoken, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            self_data = await self._get_club_proxy_list_get_self_data(logintoken,
                                                                      club_id, member_id)

            proxy_data = await self._get_club_proxy_list_get_proxy_data(logintoken, club_id,
                                                                        member_id, position)
            resultdata['selfdata'] = self_data
            resultdata['proxydata'] = proxy_data

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_proxy_list ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_proxy_list Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_club_proxy_list return, result:{0},resultdata:{1}'.format(result,
                                                                                                         resultdata))
            return result, resultdata

    async def modfirstlogin(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:modfirstlogin memberid:{0}, logintoken:{1}'.format(
                                    memberid, logintoken))

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT firstlogin FROM member WHERE memberid = {0}'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            firstlogin = data.get('firstlogin')

            if datalen != 1:
                result = pg_general.Apiresult.success
                resultdata = {'errormsg': 'get member info from db error'}
                raise ValueError('get member info error', pg_general.PG_LogerLevel.warn)

            if firstlogin != 0:
                result = pg_general.Apiresult.success
                resultdata = {'errormsg': 'member does not login first'}
                raise ValueError('member does not login first', pg_general.PG_LogerLevel.warn)

            if firstlogin == 0:
                command = 'UPDATE member set firstlogin = 1 WHERE memberid = {0}'.format(memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                title = 'Congrats to get newbie gift!!'
                content_gem = 'Gem*1000000'
                amount_gem = 1000000
                promotionid_gem = 67
                content_roomcard = 'Roomcard*20'
                amount_roomcard = 20
                promotionid_roomcard = 71
                uri = "uri"
                dateline = pg_general.getutcnow()
                memberlist = [memberid]
                main_type = 0
                send_mode = 0

                result_gem, resultdata_gem = await self.send_inbox_to_member(title, content_gem, uri, promotionid_gem,
                                                                             amount_gem, main_type, dateline,
                                                                             memberlist, send_mode)
                result_roomcard, resultdata_roomcard = await self.send_inbox_to_member(title, content_roomcard, uri,
                                                                                       promotionid_roomcard,
                                                                                       amount_roomcard, main_type,
                                                                                       dateline, memberlist, send_mode)

                command = 'UPDATE memberinbox set receivestate =0 WHERE memberid = {0} and inboxtitle = "Congrats to get newbie gift!!"'.format(
                    memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                if None in [resultdata_gem['error_list'], resultdata_roomcard['error_list']]:
                    result = pg_general.Apiresult.success
                    resultdata = {
                        'error_list_gem': resultdata_gem['error_list'],
                        'error_list_roomcard': result_roomcard['error_list'],
                        'errormsg': 'Send newbie gift mail error'
                    }
                    raise ValueError('send newbie gift mail error', pg_general.PG_LogerLevel.warn)

                result = pg_general.Apiresult.success
                resultdata = {
                    'result': 0
                }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:modfirstlogin ValueError except:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:modfirstlogin ValueError except:{0}'.format(format_exc()))

        return result, resultdata

    async def verify_apply(self, logintoken, club_id, applicant_id, action, member_id):
        """
        根據 action 決定是否讓玩家加入俱樂部
        接受:
            insert memberclub 表
            delete club_apply_list 表
            insert club_post 表
        拒絕:
            delete club_apply_list 表

        Args:
            logintoken (str):
            club_id (str): 欲加入的俱樂部編號
            application_id (int): 欲加入的玩家
            action (str): 操作選擇，accept (接受)，reject (拒絕)
            member_id (int): 執行審核的玩家 ID
        """
        try:
            log_msg = 'pg_asqldb:verify_apply logintoken:{}, club_id:{}, applicant_id:{}, action:{}'.format(
                logintoken, club_id, applicant_id, action)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            delete_command = '''
                DELETE FROM club_apply_list WHERE memberid={} and clubid="{}" 
            '''.format(applicant_id, club_id)

            delete_result = await self.updatedbdata(logintoken, delete_command)

            join_time = pg_general.getutcnow()

            if action == 'accept':
                club_amount = await self.get_member_club_amount(applicant_id)
                if club_amount >= 3:
                    raise ValueError('amount of member\'s club already over 3!!')

                # 8 是一般會員
                insert_command = '''
                    INSERT INTO memberclub(memberid, clubid, jointime, position, proxy)
                    VALUE({}, "{}", "{}", 8, {})
                '''.format(applicant_id, club_id, join_time, member_id)

                insert_result = await self.insertdbdata(logintoken, insert_command)

                select_command = 'SELECT nickname FROM member WHERE memberid={}'.format(
                    applicant_id)
                datalen, data = await self.getdbdata(logintoken, select_command)

                name = data.get('nickname')

                select_command = 'SELECT name FROM club WHERE clubid="{}"'.format(
                    club_id)
                datalen, data = await self.getdbdata(logintoken, select_command)

                club_name = data.get('name')

                post_time = pg_general.getutcnow()
                content = '歡迎「{}」成功加入「{}」！'.format(name, club_name)

                insertkey = 'createtime, clubid, content'

                insertvalue = '"{}", "{}", "{}"'.format(post_time, club_id,
                                                        content)

                command = 'INSERT INTO club_post({}) VALUE({})'.format(
                    insertkey, insertvalue)

                insertresult, index = await self.insertdbdata(logintoken,
                                                              command)

                command = 'UPDATE member SET clubchannel = {0} WHERE memberid = {1}'.format(club_id, applicant_id)
                updateresult = await self.updatedbdata(logintoken, command)

            if insertresult:
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.connectdberror

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:verify_apply ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:verify_apply Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:verify_apply return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _do_quit_club_delete_memberclub(self, logintoken, member_id, club_id):
        command = '''DELETE FROM memberclub WHERE memberid={} and clubid="{}"
        '''.format(member_id, club_id)

        result = await self.updatedbdata(logintoken, command)

        return result

    async def _do_quit_club_send_inbox_process(self, logintoken, member_id, action, name, club_id):
        """
        寄信給退出者 & 館主
        """
        select_command = '''SELECT chairmanid FROM club WHERE clubid="{}"
        '''.format(club_id)
        datalen, data = await self.getdbdata(logintoken, select_command)

        chairman_id = data.get('chairmanid')

        if action == 'quit':
            member_title = '退出俱樂部通知'
            member_msg = '您已退出俱樂部。'
            chair_title = '成員退出俱樂部通知'
            chairman_msg = '「{}」已退出俱樂部。'.format(name)

        elif action == 'kick':
            member_title = '被踢出俱樂部通知'
            member_msg = '您已被館主踢出俱樂部。'
            chair_title = '成員被踢出俱樂部通知'
            chairman_msg = '「{}」已被您踢出俱樂部。'.format(name)

        insertkey = 'memberid, inboxuri, mailtype, inboxtitle, inboxcontent, receivestate, promotionid'
        insertvalue = '"{}", "uri", "6", "{}", "{}", "0", "6"'.format(member_id, member_title, member_msg)
        command = 'INSERT INTO memberinbox({}) VALUE({})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)

        insertvalue = '"{}", "uri", "6", "{}", "{}", "0", "6"'.format(chairman_id, chair_title, chairman_msg)
        command = 'INSERT INTO memberinbox({}) VALUE({})'.format(insertkey, insertvalue)
        insertresult, index = await self.insertdbdata(logintoken, command)

        return insertresult

    async def _do_quit_club_insert_club_post_process(self, logintoken, club_id, action, name):
        if action == 'quit':
            content = '「{}」已退出俱樂部。'.format(name)

        elif action == 'kick':
            content = '「{}」已被館主踢出俱樂部。'.format(name)

        post_time = pg_general.getutcnow()

        insertkey = 'createtime, clubid, content'

        insertvalue = '"{}", "{}", "{}"'.format(post_time, club_id, content)
        command = 'INSERT INTO club_post({}) VALUE({})'.format(insertkey, insertvalue)

        insertresult, index = await self.insertdbdata(logintoken, command)

        return insertresult

    async def quit_club(self, logintoken, club_id, member_id, action):
        """玩家退出、被踢出俱樂部

        刪除 memberclub 表中的 row
        玩家會收到確認信、館主會收到通知信
        寫公告到 club_post 表中

        Args:
            member_id (int): 要退出的玩家
            action (str): quit (玩家退出)、 kick (玩家被踢出)
        """
        try:
            log_msg = 'pg_asqldb:quit_club logintoken:{}, club_id:{}, member_id:{} action:{}'.format(
                logintoken, club_id, member_id, action)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            select_command = 'SELECT nickname FROM member WHERE memberid="{}"'.format(member_id)
            datalen, data = await self.getdbdata(logintoken, select_command)

            name = data.get('nickname')

            delete_memberclub_result = await self._do_quit_club_delete_memberclub(logintoken, member_id, club_id)
            insert_inbox_result = await self._do_quit_club_send_inbox_process(logintoken, member_id, action, name,
                                                                              club_id)
            insert_post_result = await self._do_quit_club_insert_club_post_process(logintoken, club_id, action, name)

            if delete_memberclub_result and insert_post_result and insert_inbox_result:
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.connectdberror

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:quit_club ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:quit_club Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:quit_club return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _get_history(self, member_id):
        history_ls = []
        tmp_member_id = member_id

        while True:  # 透過 proxy 一路往上個階層找紀錄
            command = '''
                SELECT proxy FROM memberclub WHERE memberid={}
            '''.format(tmp_member_id)

            datalen, data = await self.getdbdata(
                'get {} proxy'.format(tmp_member_id), command)

            if datalen == 0:
                raise ValueError('get member proxy failed')

            proxy = data.get('proxy')

            if not proxy:
                break

            history_ls.append(str(proxy))

            tmp_member_id = proxy

        history = '*' + '*'.join(history_ls[::-1]) + '*'

        return history

    async def _mod_club_proxy_holding_already_proxy(self, logintoken, club_id,
                                                    member_id, holding):
        """
        新增資料到 club_holding_schedule 資料表
        等待後續排成自動更新到 host_holding 資料表
        """
        history = await self._get_history(member_id)
        command = '''
            INSERT INTO club_holding_schedule (clubid, memberid, holding, history)
            VALUES ("{}", {}, "{}", "{}")
        '''.format(club_id, member_id, holding, history)

        result, index = await self.insertdbdata(logintoken, command)

        return result

    async def _mod_club_proxy_holding_new_proxy(self, logintoken, club_id, member_id,
                                                holding, position, proxy):
        """
        更新 memberclub 資料表
        新增 club_holding_sechdule、host_id 資料表
        等待後續排成自動更新到 host_holding 資料表
        """
        history = await self._get_history(member_id)
        command = '''
            UPDATE memberclub SET position={}, proxy={} WHERE clubid="{}" AND memberid={}
        '''.format(position, proxy, club_id, member_id)

        update_result = await self.updatedbdata(logintoken, command)

        command = '''
            INSERT INTO club_holding_schedule (clubid, memberid, holding)
            VALUES ("{}", {}, "{}")
        '''.format(club_id, member_id, holding)

        result, index = await self.insertdbdata(logintoken, command)

        command = '''
            INSERT INTO host_holding (host_id, clubid, upper_host_id, host_level)
            VALUES ("{}", {}, "{}")
        '''.format(club_id, member_id, holding)

        result, index = await self.insertdbdata(logintoken, command)

    async def mod_club_proxy_holding(self, member_id, logintoken, club_id, proxyid, position, holding):
        """更新俱樂部代理人的佔成

        會有兩種情況，一種是已經是代理人了，一種是原本是一般成員變成代理人

        1. 判斷修改對象是否已經是代理人
        1.1 是代理人
        1.2 不是代理人

        Args:
            logintoken
            club_id (str):
            target_member_id (int): 被修改者的 ID
            target_position (int): 被修改者目前的階級，用來判斷是否已經是代理人了
            position (int): 被修改者被設定的階級
            holding (str): 佔成值
            member_id (int): 執行者的 ID
        """
        try:
            log_msg = '''pg_asqldb:mod_club_proxy_holding logintoken:{}, club_id:{}, 
            proxyid:{}, position:{}, holding:{}, member_id: {}
            '''.format(logintoken, club_id, proxyid, position, holding, member_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            memberposition = await self._retrieve_money_get_member_position(member_id, logintoken, club_id)
            if memberposition != 8:
                process_result = await self._mod_club_proxy_holding_already_proxy(logintoken,
                                                                                  club_id, proxyid, holding)
            else:
                process_result = await self._mod_club_proxy_holding_new_proxy(logintoken,
                                                                              club_id, proxyid, holding,
                                                                              position, member_id)

            if process_result:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:mod_club_proxy_holding ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:mod_club_proxy_holding Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:mod_club_proxy_holding return, result:{0},resultdata:{1}'.format(result,
                                                                                                            resultdata))

            return result, resultdata

    async def mod_club_member_win_limit(self, logintoken, club_id, member_id, limit):
        try:
            log_msg = '''pg_asqldb:mod_club_member_win_limit 
            logintoken:{}, club_id:{}, member_id:{}, limit:{}
            '''.format(logintoken, club_id, member_id, limit)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''UPDATE memberclub SET winlimit={}
            WHERE clubid="{}" AND memberid={}
            '''.format(limit, club_id, member_id)

            updateresult = await self.updatedbdata(logintoken, command)

            if updateresult:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:mod_club_member_win_limit ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:mod_club_member_win_limit Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:mod_club_member_win_limit return, result:{0},resultdata:{1}'.format(result,
                                                                                                               resultdata))

            return result, resultdata

    async def update_club_right_setting(self, logintoken, member_id, club_id, ratio_ls):
        """更新俱樂部獎勵比例
        """
        try:
            log_msg = 'pg_asqldb:update_club_right_setting logintoken:{}, member_id:{}, club_id:{}, ratio_ls:{}'.format(
                logintoken, member_id, club_id, ratio_ls)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            for i in range(7):
                ratio = ratio_ls[i]
                command = '''UPDATE club_right SET rewardratio={}
                    WHERE clubid="{}" and position={}
                    '''.format(ratio, club_id, i)

                update_result = await self.updatedbdata(logintoken, command)

                if not update_result:
                    raise ValueError('update_club_right_setting update failed!!')

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:update_club_right_setting ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:update_club_right_setting Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:update_club_right_setting return, result:{0},resultdata:{1}'.format(result,
                                                                                                               resultdata))

            return result, resultdata

    async def prohibitplayerclub(self, memberid, logintoken, clubid, proxyid, banplayergame, banchat):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:prohibitplayerclub memberid:{0},logintoken:{1}, clubid:{2}, banplayergame:{3}, banchat:{4}'.format(
                                    memberid, logintoken, clubid, banplayergame, banchat))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'update memberclub set banplayergame = {0}, banchat = {1}  WHERE clubid = {2} and memberid = {3}'.format(
                banplayergame, banchat, clubid, proxyid)
            updateresult = await self.updatedbdata(logintoken, command)

            if updateresult == True:
                result = pg_general.Apiresult.success
                resultdata = {
                    "data": updateresult
                }

            else:
                result = pg_general.Apiresult.parametererror
                resultdata = {
                    "data": updateresult,
                    "errormsg": "this member is not in this club"
                }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:prohibitplayerclub ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:prohibitplayerclub Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:prohibitplayerclub return, result:{0},resultdata:{1}'.format(result,
                                                                                                        resultdata))
            return result, resultdata

    async def _transfer_club_credit_transaction(self, logintoken, club_id, action,
                                                amount, member_id, target_member_id, member_credit):
        """交易明細

        1. 寫到 club_transaction 表，0: 給、1: 收
        2. 寫到 slot-game.member_wallet_log 表
        """
        current_time = pg_general.getutcnow()

        insert_command = '''
        INSERT INTO club_transaction(clubid, executor, target, action, time, balance, amount)
        VALUES("{}", {}, {}, {}, "{}", {}, {})
        '''.format(club_id, member_id, target_member_id, action, current_time,
                   member_credit, amount)

        insert_result, index = await self.insertdbdata(logintoken, insert_command)

        if action == 0:
            sg_action = 5
        elif action == 1:
            sg_action = 6

        insert_command = '''
        INSERT INTO `slot-game`.`member_wallet_log`
        (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time)
        VALUES("{}", "{}", 4, {}, "0", {}, {}, "API", "{}")
        '''.format(club_id, member_id, sg_action, amount, member_credit, current_time)
        sg_insert_result, sg_index = await self.slot_game_db.insertdbdata(logintoken, insert_command)

        return insert_result and sg_insert_result

    async def transfer_club_credit(self, member_id, logintoken, club_id,
                                   target_member_id, amount, action):
        """派收金幣

        根據 action 判斷 member_id 發錢給 target_member_id 或是 member_id 從 target_member_id 收錢

        1. 檢查 member_id 是否有足夠的金錢可以轉移
        2. 取得執行者、被執行者的金幣數量
        3. 計算後更新執行者、被執行者的金幣數量
        4. 寫入交易明細

        Args:
            member_id (int): 執行者的 ID
            logintoken (str):
            club_id (str): 俱樂部 ID
            target_member_id (int): 被執行者的 ID
            amount (int): 轉移的金額
            action (int): 0: member_id -> target_member_id，1: member_id <- target_member_id
        """
        try:
            log_msg = '''
            pg_asqldb:transfer_club_credit member_id:{}, logintoken:{}, club_id:{}, 
            target_member_id:{}, amount:{} action:{}
            '''.format(member_id, logintoken, club_id, target_member_id, amount, action)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            select_command = '''
                SELECT credit, memberid FROM memberclub
                WHERE clubid="{}" and memberid IN ({}, {})
            '''.format(club_id, member_id, target_member_id)

            datalen, data = await self.getdbdata(logintoken, select_command, fetchall=True)

            if datalen != 2:
                raise ValueError('select SELECT credit FROM memberclub no data')

            member_credit = 0
            target_member_credit = 0

            for dc in data:
                tmp_member_id = dc.get('memberid')
                tmp_credit = dc.get('credit')

                if tmp_member_id == member_id:
                    member_credit = tmp_credit

                elif tmp_member_id == target_member_id:
                    target_member_credit = tmp_credit

            if action == 0:
                if member_credit < amount:
                    raise ValueError('action=0 Insufficient amount')

                member_credit -= amount
                target_member_credit += amount
            else:
                if target_member_credit < amount:
                    raise ValueError('action=1 Insufficient amount')

                member_credit += amount
                target_member_credit -= amount

            update_command = '''
                UPDATE memberclub SET credit={} WHERE clubid="{}" and memberid={}
            '''

            m_update_result = await self.updatedbdata(logintoken,
                                                      update_command.format(member_credit, club_id, member_id))

            r_update_result = await self.updatedbdata(logintoken,
                                                      update_command.format(target_member_credit, club_id,
                                                                            target_member_id))

            insert_result = await self._transfer_club_credit_transaction(logintoken,
                                                                         club_id, action, amount, member_id,
                                                                         target_member_id, member_credit)

            if m_update_result and r_update_result and insert_result:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:transfer_club_credit ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:transfer_club_credit Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:transfer_club_credit return, result:{0},resultdata:{1}'.format(result,
                                                                                                          resultdata))
            return result, resultdata

    async def _remove_proxy_under_member_check(self, logintoken, member_id, club_id):
        """確認該名管理員底下是否還有成員(一般 + 管理)

        Returns:
            True: 有成員
            False: 無成員
        """
        command = '''
            SELECT memberid, position, proxy FROM memberclub
            WHERE clubid="{}" AND proxy={}
        '''.format(club_id, member_id)

        datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

        return datalen != 0

    async def _remove_proxy_money_check(self, logintoken, member_id, club_id):
        """確認該名管理員底下是否還有金幣

        Returns:
            True: 還有錢
            False: 沒有錢
        """
        command = '''
            SELECT credit FROM memberclub WHERE clubid="{}" AND memberid={}
        '''.format(club_id, member_id)

        datalen, data = await self.getdbdata(logintoken, command)

        credit = data.get('credit')

        return credit != 0

    async def remove_proxy_right(self, logintoken, club_id, proxy_id):
        """刪除管理者權限

        1. 確認該管理員底下是否有其他成員
        2. 確認該管理員是否有金幣
        3. 沒有錢 & 沒有其他成員就刪除管理者權限 # TODO 尚未開發
        """
        try:
            log_msg = '''
            pg_asqldb:remove_proxy_right logintoken:{}, club_id:{}, proxy_id:{}
            '''.format(logintoken, club_id, proxy_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            has_under_member = await self._remove_proxy_under_member_check(logintoken, proxy_id,
                                                                           club_id)

            has_money = await self._remove_proxy_money_check(logintoken, proxy_id, club_id)

            if not has_under_member and not has_money:
                pass

            result = pg_general.Apiresult.success

            resultdata['has_under_member'] = has_under_member
            resultdata['has_money'] = has_money

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:remove_proxy_right ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:remove_proxy_right Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:remove_proxy_right return, result:{0},resultdata:{1}'.format(result,
                                                                                                        resultdata))
            return result, resultdata

    async def _retrieve_money_get_member_position(self, member_id, logintoken, club_id):
        command = '''
            SELECT position FROM memberclub WHERE memberid={} AND clubid="{}"
        '''.format(member_id, club_id)

        datalen, data = await self.getdbdata(logintoken, command)

        if datalen == 0:
            raise ValueError('get member {} position failed!'.format(member_id))

        return data['position']

    async def _retrieve_money_get_under_member(self, member_id, logintoken, club_id, flag=0):
        """取得該名管理員底下的成員(一般 + 管理)

        透過遞迴的方式抓取該管理者底下的一般成員 + 管理者

        Args:
            member_id (int): 管理者 ID
            flag (int): 如果是 1 要把 member_id 放入回傳值中，避免第一次查詢時沒有查到第一位管理者
        """
        member_id_ls = [member_id] if flag == 1 else []

        command = '''
            SELECT memberid, position, proxy FROM memberclub
            WHERE clubid="{}" AND proxy={}
        '''.format(club_id, member_id)

        datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

        if datalen == 0:
            return []

        proxy_member_id_ls = [dc['memberid'] for dc in data if dc['position'] != 8]
        normal_member_id_ls = [dc['memberid'] for dc in data if dc['position'] == 8]

        member_id_ls += proxy_member_id_ls  # 加入管理員

        for m_id in proxy_member_id_ls:  # 加入管理員底下的成員
            tmp_member_ls = await self._retrieve_money_get_under_member(m_id, logintoken, club_id)
            member_id_ls += tmp_member_ls

        member_id_ls += normal_member_id_ls  # 加入一般成員

        return member_id_ls

    async def _retrieve_money_transfer(self, member_id, member_id_ls, logintoken, club_id):
        """將清單中玩家的錢轉移至管理者上

        1. 將所有玩家的錢轉移到管理者上
        1.1 取得玩家持有金幣
        1.2 將玩家持有金幣歸零
        1.3 轉移至管理者上
        1.4 寫明細 # TODO

        Args:
            member_id (int): 管理者的 ID
            member_id_ls (list): list of int. 所有要被回收金幣的玩家 ID
        """
        msg_ls = []

        for m_id in member_id_ls:
            command = '''
                SELECT credit FROM memberclub WHERE memberid={} AND clubid="{}"
            '''.format(m_id, club_id)
            datalen, data = await self.getdbdata(logintoken, command)

            credit = data.get('credit')

            if credit == 0:
                continue

            command = '''
                UPDATE memberclub SET credit=0 WHERE memberid={} AND clubid="{}"
            '''.format(m_id, club_id)
            result = await self.updatedbdata(logintoken, command)

            command = '''
                UPDATE memberclub SET credit=credit+{} WHERE memberid={} AND clubid="{}"
            '''.format(credit, member_id, club_id)
            result = await self.updatedbdata(logintoken, command)

            log_msg = '''
                translate {} from {} to {}
            '''.format(credit, m_id, member_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            msg_ls.append(log_msg)

        return msg_ls

    async def retrieve_money(self, member_id, target_member_id, logintoken, club_id):
        """回收該名管理及以下所屬成員之金幣

        1. 撈該名成員所屬管理階級
        1.1 沒權限直接報錯
        2. 找出所有旗下成員 id
        3. 將旗下成員的金幣轉到管理員上

        Args:
            member_id (int): 執行金幣回收的玩家 ID
            target_member_id (int): 被回收的玩家 ID
        """
        try:
            log_msg = '''
            pg_asqldb:retrieve_money member_id:{}, target_member_id:{}, logintoken:{}, club_id:{}
            '''.format(member_id, target_member_id, logintoken, club_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            position = await self._retrieve_money_get_member_position(target_member_id, logintoken, club_id)

            if position == 8:
                raise ValueError('no permission!!')

            member_id_ls = await self._retrieve_money_get_under_member(target_member_id,
                                                                       logintoken, club_id, 1)
            msg_ls = await self._retrieve_money_transfer(member_id, member_id_ls, logintoken, club_id)

            resultdata['msg'] = '\n'.join(msg_ls)
            resultdata['member_id_ls'] = member_id_ls
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:retrieve_money ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:retrieve_money Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:retrieve_money return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def get_money_detail(self, logintoken, club_id, member_id, start_datetime, end_datetime):
        """
        金幣明細
        """
        try:
            log_msg = '''
            pg_asqldb:get_money_detail logintoken:{}, club_id:{}, start_datetime:{}, end_datetime:{}
            '''.format(logintoken, club_id, start_datetime, end_datetime)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            club_transaction = await self._get_club_transaction(logintoken, club_id, member_id, start_datetime, end_datetime)

            result = pg_general.Apiresult.success
            increase = 0
            reduce = 0
            for tran in club_transaction:
                if (tran.action % 2) == 0:
                    increase += tran.get('amount')
                else:
                    reduce += tran.get('amount')
            resultdata['increase'] = increase
            resultdata['reduce'] = reduce
            resultdata['balance'] = increase - reduce

            resultdata['transactiondata'] = club_transaction

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_money_detail ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_money_detail Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_money_detail return, result:{0},resultdata:{1}'.format(result,
                                                                                                      resultdata))
            return result, resultdata

    async def _get_club_transaction(self, logintoken, club_id, start_datetime, end_datetime):
        """取得俱樂部的交易明細資料
        交易明細

        1. club_transaction 表，0: 給、1: 收
        2. slot-game.member_wallet_log 表
         Args:
            executor: 執行交易者的 memberid
            target:   被執行的對象 memberid
            action:   0: 給、1: 收
        """
        
        command = '''
        SELECT ct.*, tm.nickname AS targetname, tm.avatar AS targetavatar, em.nickname AS executorname
        FROM club_transaction AS ct
        LEFT JOIN member AS tm ON tm.memberid=ct.target
        LEFT JOIN member AS em ON em.memberid=ct.executor
        WHERE club_transaction.clubid="{}"
        AND time>="{}" AND time<="{}"
        '''.format(club_id, start_datetime, end_datetime)

        datalen, data = await self.getdbdata(logintoken, command)

        if datalen == 0:
            raise ValueError('get_club_transaction: {} failed'.format(club_id))


        return data

    async def get_member_money_detail(self, logintoken, member_id ,club_id, start_datetime, end_datetime):
        """
        個人金幣明細
        """
        try:
            log_msg = '''
            pg_asqldb:get_member_money_detail logintoken:{}, club_id:{}, start_datetime:{}, end_datetime:{}
            '''.format(logintoken, club_id, start_datetime, end_datetime)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            # 抓自己的 資料
            command = 'select memberid, nickname, avatar, memberid from member where memberid="{0}"'.format(member_id)
            datalen, data = await self.getdbdata(logintoken,command)

            if datalen != 1:
                raise ValueError('get self data error')

            resultdata = data
            club_transaction = await self._get_member_club_transaction(logintoken, member_id, club_id, start_datetime, end_datetime)
            result = pg_general.Apiresult.success
            increase = 0
            reduce = 0
            for tran in club_transaction:
                if (tran.action % 2) == 0:
                    increase += tran.get('amount')
                else:
                    reduce += tran.get('amount')
            resultdata['increase'] = increase
            resultdata['reduce'] = reduce
            resultdata['balance'] = increase - reduce

            resultdata['transactiondata'] = club_transaction
            
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_member_money_detail ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_member_money_detail Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_member_money_detail return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _get_member_club_transaction(self, logintoken, member_id, club_id, start_datetime, end_datetime):
        """取得該名成員在俱樂部的交易明細資料
        交易明細

        1. club_transaction 表，0: 給、1: 收
        2. slot-game.member_wallet_log 表
         Args:
            executor: 執行交易者的 memberid
            target:   被執行的對象 memberid
            action:   0: 給、1: 收
        """
        command = '''
        SELECT ct.*, em.nickname AS executornickname
        FROM club_transaction AS ct
        LEFT JOIN member AS em ON em.memberid=ct.executor
        WHERE club_transaction.clubid="{}" AND club_transaction.target={}
        AND time>="{}" AND time<="{}"
        '''.format(club_id, member_id, start_datetime, end_datetime)
        datalen, data = await self.getdbdata(logintoken, command)

        return data

    async def get_game_record(self, logintoken, sn):
        """
        遊戲紀錄
        """
        try:
            log_msg = '''
            pg_asqldb:get_performance logintoken:{}, sn:{}
            '''.format(logintoken, sn)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            """到 PS DB 該名玩家俱樂部遊戲記錄
            """
            command = '''
            SELECT *game_data FROM accounting
            WHERE  sn="{}" 
            '''.format(sn)
            datalen, data = await self.slot_game_db.getdbdata(logintoken, command)
            result = pg_general.Apiresult.success
            resultdata['gamedata'] = data

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_game_record ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_game_record Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_game_record return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _get_room_info_record(self, logintoken, member_id, club_id, game_id, start_datetime, end_datetime):
        """玩家建立房間的資料
        """
        command = '''
            SELECT * FROM room_info_record
            WHERE AND club_id="{}" AND game_id="{}" AND create_time>="{}" AND create_time<="{}  
        '''.format(club_id, game_id, start_datetime, end_datetime)
        

        if member_id :
            command +='''AND memberid={}''' .format(member_id)

        datalen, data = await self.slot_game_db.getdbdata(logintoken, command)

        if datalen > 0:
            for record in data:
              record["player_info"] = self._get_room_player_info(logintoken, record.room_id)
              
        return datalen, data

    async def _get_club_accounting(self, logintoken, club_id, game_id, start_datetime, end_datetime):
        """到 PS DB 俱樂部遊戲記錄

        accounting 這張表的 host_id 會等於 club_id
        """
        command = '''
            SELECT * FROM accounting
            WHERE game_end=1 AND host_id="{}" AND game_id="{}" AND game_time>="{}" AND game_time<="{}  
        '''.format(club_id, game_id, start_datetime, game_id, end_datetime)

        datalen, data = await self.slot_game_db.getdbdata(logintoken, command)

        return datalen, data

    async def get_self_record(self, logintoken, member_id, club_id, game_id, start_datetime, end_datetime, room_id):
        """
        我的戰績
        """
        try:
            log_msg = '''
            pg_asqldb:get_self_record logintoken:{}, member_id{}, club_id:{}, game_id{}, start_datetime:{}, end_datetime:{}, room_id:{}
            '''.format(logintoken, member_id, club_id, game_id, start_datetime, end_datetime, room_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            # 抓自己的 資料
            command = '''
            SELECT *
            FROM room_player_info
            WHERE create_time>="{}" AND create_time<="{}
            '''.format(member_id, start_datetime, end_datetime)
            if room_id:
                command +='''AND room_id={}'''.format(room_id)

            datalen, roomdata = await self.getdbdata(logintoken, command)
            owner_accounting_ls =[]

            for record in roomdata:
                 command = '''
                 SELECT * FROM room_info_record
                 WHERE AND club_id="{}" AND game_id="{}" AND room_id="{}" 
                 '''.format(club_id, game_id, record.get('room_id'))
                 datalen, roominfodata = await self.getdbdata(logintoken, command)
                 if roominfodata.get('dismiss_time')!= '0000-00-00 00:00:00':
                    accounting = await self._get_accounting(logintoken, roominfodata.get('owner'), game_id, roominfodata.get('create_time'), roominfodata.get('dismiss_time'))
                    if len(accounting) > 0:
                        for account in accounting:
                            account['roominfo'] = roominfodata
                            owner_accounting_ls.append(account)

            for accounting in owner_accounting_ls:
                command = '''
                SELECT m.*
                FROM room_player_info AS rp
                LEFT JOIN member AS m ON rp.member_id=m.memberid
                WHERE room_id="{}
                '''.format(accounting['roominfo']['room_id'])
                datalen, roomplayer = await self.getdbdata(logintoken, command)
                for play in roomplayer:
                    command = '''
                    SELECT * FROM accounting
                    WHERE game_end=1 AND memberid={} AND game_id="{}" AND game_time>="{}" AND game_time<="{} 
                    '''.format(play.get('memberid'), game_id, accounting.get('begin_time'), accounting.get('game_time'))
                    datalen, data = await self.slot_game_db.getdbdata(logintoken, command)
                    play['accounting'] =data[0]
                        
                accounting['roomplayer'] = roomplayer
                
            result = pg_general.Apiresult.success
            resultdata['data'] = owner_accounting_ls

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_self_record ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_self_record Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_self_record return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _get_accounting(self, logintoken, member_id, game_id, start_datetime, end_datetime):
        """到 PS DB 該名玩家遊戲記錄
        """
        command = '''
            SELECT * FROM accounting
            WHERE game_end=1 AND memberid={} AND game_id="{}" AND game_time>="{}" AND game_time<="{} 
        '''.format( member_id, game_id, start_datetime, end_datetime)

        datalen, data = await self.slot_game_db.getdbdata(logintoken, command)
        
        if datalen > 0 :
            command = '''
            SELECT name FROM gameroomsetting WHERE gameid="{}"
            '''.format(game_id)
            datalen, data = await self.getdbdata(logintoken, command)
            for accounting in data:
                data['gamename'] = data.get('name')
        return datalen, data

    async def _get_room_player_info(self, logintoken, room_id):
        """房間的玩家資料
        """
        command = '''
        SELECT *
        FROM room_player_info
        WHERE room_id="{} AND time>="{}" AND time<="{}
        '''.format(room_id)
        datalen, data = await self.getdbdata(logintoken, command)

        return data

    async def get_member_record(self, logintoken, club_id, game_id, start_datetime, end_datetime, room_id, search):
        """
        會員戰績
        """
        try:
            log_msg = '''
            pg_asqldb:get_member_record logintoken:{}, club_id:{}, game_id:{}, start_datetime:{}, end_datetime:{}, room_id:{}, search:{}
            '''.format(logintoken, club_id, game_id, start_datetime, end_datetime, room_id, search)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            if search :
                command = 'select memberid from member where memberid="{0}" or memberid="{0}"'.format(search)
                datalen, data = await self.getdbdata(logintoken,command)
                member_id = data
            
            command = '''
            SELECT *
            FROM room_player_info
            WHERE create_time>="{}" AND create_time<="{}
            '''.format(start_datetime, end_datetime)
            if member_id:
                command +='''AND member_id={}'''.format(member_id)
            
            if room_id:
                command +='''AND room_id={}'''.format(room_id)

            datalen, roomdata = await self.getdbdata(logintoken, command)
            owner_accounting_ls =[]

            for record in roomdata:
                 command = '''
                 SELECT * FROM room_info_record
                 WHERE AND club_id="{}" AND game_id="{}" AND room_id="{}" 
                 '''.format(club_id, game_id, record.get('room_id'))
                 datalen, roominfodata = await self.getdbdata(logintoken, command)
                 if roominfodata.get('dismiss_time') != '0000-00-00 00:00:00':
                    accounting = await self._get_accounting(logintoken, roominfodata.get('owner'), game_id, roominfodata.get('create_time'), roominfodata.get('dismiss_time'))
                    if len(accounting) > 0:
                        for account in accounting:
                            account['roominfo'] = roominfodata
                            owner_accounting_ls.append(account)

            for accounting in owner_accounting_ls:
                command = '''
                SELECT m.*
                FROM room_player_info AS rp
                LEFT JOIN member AS m ON rp.member_id=m.memberid
                WHERE room_id="{}
                '''.format(accounting['roominfo']['room_id'])
                datalen, roomplayer = await self.getdbdata(logintoken, command)
                for play in roomplayer:
                    command = '''
                    SELECT * FROM accounting
                    WHERE game_end=1 AND memberid={} AND game_id="{}" AND game_time>="{}" AND game_time<="{} 
                    '''.format(play['memberid'], game_id, accounting['begin_time'], accounting['game_time'])
                    datalen, data = await self.slot_game_db.getdbdata(logintoken, command)
                    play['accounting'] = data[0]
                        
                accounting['roomplayer'] = roomplayer
                
            result = pg_general.Apiresult.success
            resultdata['data'] = owner_accounting_ls

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_member_record ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_member_record Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_member_record return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def get_performance(self, logintoken, sn):
        """
        績效
        """
        try:
            log_msg = '''
            pg_asqldb:get_performance logintoken:{}, sn:{}
            '''.format(logintoken, sn)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_performance ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_performance Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_performance return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def save_club_info(self, logintoken, club_id, introduction, post_msg,
                             apply_mode, line):
        """更新俱樂部資料

        1. 寫入資料表

        """
        try:
            log_msg = '''
            pg_asqldb:save_club_info logintoken: {}, club_id: {}, introduction: {},
             post_msg: {}, apply_mode: {}, line: {}
            '''.format(logintoken, club_id, introduction, post_msg, apply_mode, line)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''
            UPDATE club SET introduction="{}", postmsg="{}", applymode={}, line="{}"
            WHERE clubid="{}" 
            '''.format(introduction, post_msg, apply_mode, line, club_id)

            update_result = await self.updatedbdata(logintoken, command)

            if update_result is True:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:save_club_info ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:save_club_info Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:save_club_info return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def close_club(self, logintoken, club_id):
        """俱樂部打烊

        1. 更新資料表
        """
        try:
            log_msg = '''pg_asqldb:close_club logintoken: {}, club_id: {}
            '''.format(logintoken, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''UPDATE club SET closestatus=1 WHERE clubid="{}"
            '''.format(club_id)

            update_result = await self.updatedbdata(logintoken, command)

            if update_result:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:close_club ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:close_club Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:close_club return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def set_club_room_password(self, logintoken, club_id, password):
        """設定俱樂部房間密碼

        1. 更新資料表
        """
        try:
            log_msg = '''pg_asqldb:set_club_room_password logintoken: {}, club_id: {}
            '''.format(logintoken, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''UPDATE club SET roompassword="{}" WHERE clubid="{}"
            '''.format(password, club_id)

            update_result = await self.updatedbdata(logintoken, command)

            if update_result:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:set_club_room_password ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:set_club_room_password Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:set_club_room_password return, result:{0},resultdata:{1}'.format(result,
                                                                                                            resultdata))
            return result, resultdata

    async def add_club_room_setting(self, logintoken, club_id, game_id, setting_name,
                                    bet, outtax, same_ip, similar, player, thinktime, rounds, walletrange, setting):
        """設定俱樂部房間玩法

        1. 檢查是否重複名稱
        1.1 重複就離開
        2. 寫入資料表
        """
        try:
            log_msg = '''
            pg_asqldb:add_club_room_setting logintoken:{}, club_id:{}, game_id:{}, setting_name:{},
            bet:{}, outtax:{}, same_ip:{}, similar:{}, player:{}, thinktime:{}, rounds:{}, walletrange:{}, setting:{}
            '''.format(logintoken, club_id, game_id, setting_name, bet, outtax, same_ip,
                       similar, player, thinktime, rounds, walletrange, setting)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''
            SELECT * FROM club_room_setting WHERE settingname="{}" AND clubid="{}"
            '''.format(setting_name, club_id)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 0:
                resultdata['errormsg'] = 'setting name has already exists'
                raise ValueError('setting name has already exists')

            command = '''
            INSERT INTO club_room_setting 
                (clubid, gameid, settingname, bet, outtax, sameip, similar, player, 
                thinktime, rounds, walletrange, setting)
            VALUES ("{}", "{}", "{}", {}, {}, {}, {}, {}, {}, {}, "{}", "{}") 
            '''.format(club_id, game_id, setting_name,
                       bet, outtax, same_ip, similar, player, thinktime, rounds, walletrange, setting)

            insert_result, index = await self.insertdbdata(logintoken, command)

            if insert_result:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:add_club_room_setting ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:add_club_room_setting Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:add_club_room_setting return, result:{0},resultdata:{1}'.format(result,
                                                                                                           resultdata))
            return result, resultdata

    async def mod_club_room_setting(self, logintoken, club_id, setting_id,
                                    bet, outtax, same_ip, similar, player, thinktime, rounds, walletrange, setting):
        """更新俱樂部房間玩法

        1. 更新資料表
        """
        try:
            log_msg = '''
            pg_asqldb:mod_club_room_setting logintoken:{}, club_id:{}, setting_id:{},
            bet, outtax:{}, same_ip:{}, similar:{}, player:{}, thinktime:{}, rounds:{},
            walletrange:{}, setting:{}
            '''.format(logintoken, club_id, setting_id, bet, outtax, same_ip, similar,
                       player, thinktime, rounds, walletrange, setting)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''
            UPDATE club_room_setting SET bet={}, outtax={}, sameip={}, similar={},
            player={}, thinktime={}, rounds={}, walletrange="{}", setting="{}"
            WHERE clubid="{}" AND id={}
            '''.format(bet, outtax, same_ip, similar, player, thinktime, rounds,
                       walletrange, setting, club_id, setting_id)

            update_result = await self.updatedbdata(logintoken, command)

            if update_result:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:mod_club_room_setting ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:mod_club_room_setting Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:mod_club_room_setting return, result:{0},resultdata:{1}'.format(result,
                                                                                                           resultdata))
            return result, resultdata

    async def delete_club_room_setting(self, logintoken, club_id, setting_id):
        """刪除樂部房間玩法

        1. 刪除資料表中的資料
        """
        try:
            log_msg = '''
            pg_asqldb:delete_club_room_setting logintoken: {}, club_id: {}, setting_id: {}
            '''.format(logintoken, club_id, setting_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = '''
            DELETE FROM club_room_setting WHERE clubid="{}" AND id={}
            '''.format(club_id, setting_id)

            update_result = await self.updatedbdata(logintoken, command)

            if update_result:
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:delete_club_room_setting ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:delete_club_room_setting Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:delete_club_room_setting return, result:{0},resultdata:{1}'.format(result,
                                                                                                              resultdata))
            return result, resultdata

    async def room_fresh_logintoken(self, room_player_info):
        """更新組房 redis 中玩家的 logintoken

        避免因為玩家斷線重連更新 logintoken 之後沒有收到廣播訊息

        Args:
            room_player_info(dict): 請看 create_room 的 room_player_info 註解
        """
        command = '''SELECT memberid, logintoken FROM member WHERE memberid IN ({})
        '''.format(', '.join([k for k in room_player_info]))

        datalen, data = await self.getdbdata('room_fresh_logintoken', command, fetchall=True)

        if datalen == 0:
            return {}

        for d in data:
            member_id = d.get('memberid')
            logintoken = d.get('logintoken')

            # TODO 先應急咧，不然玩家剛好斷線又更新下去會變成 None 解析上有問題
            # 後續應該要對於斷線玩家做其他的處理
            if logintoken is not None:
                room_player_info[str(member_id)]['logintoken'] = logintoken

        return room_player_info

    async def _generate_club_room_key(self, redis_obj, club_id):
        """產生房號

        若沒有帶 club_id 就產生一般房間的 key
        """
        i = 0
        range_start = 10 ** 5
        range_end = (10 ** 6) - 1

        while True:  # 產生房號，若房號重覆就再產生
            i += 1

            room_id = str(randint(range_start, range_end))

            if not club_id:
                room_key = 'normal_room_{}'.format(room_id)
            else:
                room_key = 'club_{}_room_{}'.format(club_id, room_id)

            data = await redis_obj.get_value(room_key)

            if not data:
                break

            if i == 1000000:
                return -1

        return room_key

    async def _create_room_check_roomcard(self, logintoken, club_id, member_id, amount):
        """檢查玩家 or 俱樂部的房卡數量是否足夠"""

        table_name = 'club' if club_id else 'member'

        if club_id:
            where_search = 'clubid="{}"'.format(club_id)
        else:
            where_search = 'memberid={}'.format(member_id)

        command = '''
            SELECT roomcard FROM {}
            WHERE {}
        '''.format(table_name, where_search)

        datalen, data = await self.getdbdata(logintoken, command)

        if datalen != 0:
            return int(data.get('roomcard', 0)) >= amount

        return False

    async def _create_room_consume_roomcard(self, logintoken, club_id, amount, member_id, game_id):
        """從資料庫中扣除房卡

        1. 根據類型從俱樂部或玩加本身刪除卡片
        2. 寫房卡使用記錄
        """
        now_datetime = pg_general.datetimetostr_nof(pg_general.getutcnow_datetime())
        if club_id:
            update_command = '''
                UPDATE club SET roomcard=roomcard-{}
                WHERE clubid="{}"
            '''.format(amount, club_id)
            insert_command = '''
                INSERT INTO roomcard_log
                (member_id, game_id, roomcard, datetime, transfer_type, club_id)
                VALUES ({}, "{}", {}, "{}", 0, "{}")
            '''.format(member_id, game_id, amount, now_datetime, club_id)
        else:
            update_command = '''
                UPDATE member SET roomcard=roomcard-{}
                WHERE memberid={}
            '''.format(amount, member_id)
            insert_command = '''
                INSERT INTO roomcard_log
                (member_id, game_id, roomcard, datetime, transfer_type)
                VALUES ({}, "{}", {}, "{}", 0)
            '''.format(member_id, game_id, amount, now_datetime)

        update_result = await self.updatedbdata(logintoken, update_command)

        if not update_result:
            raise ValueError('update club roomcard failed')

        insert_result, index = await self.insertdbdata(logintoken, insert_command)
        if not insert_result:
            raise ValueError('insert club roomcard failed')

    async def _create_room_get_player_info(self, logintoken, game_setting, member_id, club_id):
        if game_setting.get('cointype') == 1:  # 銀幣
            command = '''
                SELECT nickname, silvercredit AS credit, lastip FROM member WHERE memberid={}
            '''.format(member_id)
        else:
            command = '''
                SELECT m.nickname AS nickname, mc.credit AS credit, lastip FROM member AS m
                LEFT JOIN memberclub AS mc ON mc.memberid=m.memberid
                WHERE m.memberid={} AND mc.clubid="{}"
            '''.format(member_id, club_id)

        datalen, data = await self.getdbdata(logintoken, command)

        nickname = data.get('nickname')  # 注意 SQL 語法
        playercent = data.get('credit')  # 注意 SQL 語法
        ip = data.get('lastip')

        return nickname, playercent, ip

    async def _create_room_get_club_password(self, logintoken, club_id):
        command = '''SELECT roompassword FROM club WHERE clubid="{}"
        '''.format(club_id)

        datalen, data = await self.getdbdata(logintoken, command)

        return data.get('roompassword')

    async def create_room(self, member_id, logintoken, redis_obj, club_id, game_id,
                          game_setting, amount, rounds, password_room, club_room_setting_id):
        """建立一般 or 俱樂部房間

        檢查房卡數量是否足夠
        扣除俱樂部房卡
        寫入資料到 redis 中
            redis key 格式:
                俱樂部: club_{俱樂部 ID}_{房間 ID}
                一般房: normal_room_{房間 ID}
            redis 儲存房間相關設定
                {
                    "roomid": "123456"
                    "thinktime": 10,
                    "sameip": True,
                    "fee": 5,  # 手續費
                    "owner": 91391,  # 房主 ID
                    "rounds": 5,  # 遊玩回合
                    "similar": True,
                    "room_player_info": [{
                        '91403': {
                            'ready': 1,  # 是否準備開始遊戲
                            'memberid': 91403,
                            'logintoken': '...',
                            'nickname': 'fTonia',
                            'playercent': 10000,  # 玩家的錢
                            'ip': '127.0.0.1',
                            'iphintstatus': 0,  # 是否為相同 IP
                            'idhintstatus': 0,  # 是否為相似名稱
                            'owner': 1,  # 是否為房主
                        }],{...}
                    },
                    "autooperate": 0,
                    "minbet": 500,  # 房間底注
                    "banker": 0,
                    "game_id": "PSC-APP-00005",
                    "walletrange": [100, 500],  # 錢包範圍
                    "player": 2,  # 遊玩人數
                    "gamename": "POK DENG",
                    "clubroomsettingid": 1, 俱樂部玩法ID
                    "already_play_round": 0,  # 已遊玩回合數
                    "cointype": 0,  # 0 是金幣, 1 是銀幣
                    "status": 'wait',  # wait, start
                    "create_time": "2022-02-02 02:02:02",
                }

        整理回傳值

        Args:
            member_id:
            redis_obj:
            club_id (str): 俱樂部 ID，可為空值
            game_id (str): 遊戲 ID
            game_setting (dict): 房間設定參數
            amount (int): 消耗房卡數量
            rounds (int): 總遊玩場次
        """
        try:
            log_msg = '''
            pg_asqldb:create_room member_id:{}, logintoken:{}, club_id:{}, game_id:{}, 
            game_setting:{}, amount:{} rounds:{} password_room:{}, club_room_setting_id:{}
            '''.format(member_id, logintoken, club_id, game_id, game_setting, amount, rounds,
                       password_room, club_room_setting_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            await self._confirm_no_duplicate_room(logintoken, redis_obj, member_id)
            is_not_enough_card = not await self._create_room_check_roomcard(logintoken, club_id,
                                                                            member_id, amount)
            if is_not_enough_card:
                resultdata['errormsg'] = 'room card not enough'
                raise ValueError('room card not enough')

            room_key = await self._generate_club_room_key(redis_obj, club_id)
            chatroom = 'chatroom_channel_{}'.format(room_key)

            if room_key == -1:
                resultdata['errormsg'] = 'generate room id error'
                raise ValueError('generate room id error')

            await self._create_room_consume_roomcard(logintoken, club_id, amount, member_id, game_id)

            nickname, playercent, ip = await self._create_room_get_player_info(logintoken,
                                                                               game_setting, member_id, club_id)
            member_dc = {
                str(member_id): {
                    'ready': 1,
                    'memberid': member_id,
                    'logintoken': logintoken,
                    'nickname': nickname,
                    'playercent': playercent,
                    'ip': ip,
                    'iphintstatus': 0,
                    'idhintstatus': 0,
                    'owner': 1,
                }
            }

            room_setting_dc = game_setting
            room_setting_dc['game_id'] = game_id
            room_setting_dc['owner'] = member_id
            room_setting_dc['rounds'] = rounds
            # 建立房間的人，配合 redis 儲存格式
            room_setting_dc['room_player_info'] = member_dc
            room_setting_dc['already_play_round'] = 0
            room_setting_dc['roomcard'] = amount
            split_mark = 3 if club_id else 2  # 有無俱樂部的代號不同， split 後要取得的位置也不同
            room_setting_dc['roomid'] = room_key.split('_')[split_mark]
            room_setting_dc['status'] = 'wait'
            room_setting_dc['create_time'] = pg_general.datetimetostr_nof(pg_general.getutcnow_datetime())

            if password_room:  # 是否為密碼房，否的話預設空值
                password = await self._create_room_get_club_password(logintoken, club_id)
                room_setting_dc['password'] = password
            else:
                room_setting_dc['password'] = ''

            room_setting_dc['club_id'] = club_id if club_id else ''
            room_setting_dc['club_room_setting_id'] = club_room_setting_id if club_id else -1

            await redis_obj.hmset(room_key, room_setting_dc)
            await redis_obj.lpush(chatroom, '{}')
            # 記錄該名玩家在哪間房間
            await redis_obj.hset('play_room_record', member_id, room_key)

            command = '''
                SELECT name FROM gameroomsetting WHERE gameid="{}"
            '''.format(game_id)

            datalen, data = await self.getdbdata(logintoken, command)

            result = pg_general.Apiresult.success
            resultdata['roomid'] = room_key.split('_')[split_mark]
            resultdata['gamename'] = data.get('name')
            resultdata['cointype'] = game_setting.get('cointype')
            resultdata['minbet'] = game_setting.get('minbet')
            resultdata['fee'] = game_setting.get('fee')
            resultdata['minwalletrange'] = game_setting.get('walletrange')[0]
            resultdata['maxwalletrange'] = game_setting.get('walletrange')[1]
            resultdata['player'] = game_setting.get('player')
            resultdata['rounds'] = game_setting.get('rounds')
            resultdata['thinktime'] = game_setting.get('thinktime')
            resultdata['status'] = 'wait'
            resultdata['clubroomsettingid'] = club_room_setting_id
            resultdata['password'] = room_setting_dc['password']

            resultdata['room_player_info'] = []
            for k, v in member_dc.items():  # 廣播用的
                resultdata['room_player_info'].append(v)

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:create_room ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:create_room Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:create_room return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def find_join_room(self, member_id, logintoken, club_id, redis_obj,
                             club_room_setting_id):
        """找出可加入的房間

        只有俱樂部才有的功能

        1. 取得房間資訊
        2. 找出可加入的房間（相同玩法 & 等待中 & 人數沒滿），回傳 room id
        3. 若沒房間就回傳空值
        """
        try:
            log_msg = '''
            pg_asqldb:find_join_room member_id:{}, logintoken:{}, club_id:{}
            '''.format(member_id, logintoken, club_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            room_key = 'club_{}_room_*'.format(club_id)
            room_key_ls = await redis_obj.get_all_keys(room_key)

            for key in room_key_ls:
                room_info = await redis_obj.hgetall(key)

                player_amount = len(redis_obj.str_to_dict(room_info.get('room_player_info')))
                is_not_full = player_amount < int(room_info.get('player'))
                is_waiting = room_info['status'] == 'wait'
                is_same_setting = room_info['club_room_setting_id'] == club_room_setting_id

                if is_not_full and is_waiting and is_same_setting:
                    resultdata['room_key'] = key.split('_')[3]
                    result = pg_general.Apiresult.success
                    break

            if result == pg_general.Apiresult.connectdberror:
                resultdata['room_key'] = ''

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:find_join_room ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:find_join_room Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:find_join_room return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    def _join_room_id_ip_check_process(self, room_player_info):
        """檢查是否有相似的 ID 或相同的 IP

        從第一個開始往後比對，所以用兩個迴圈
        """

        player_num = len(room_player_info)
        member_id_ls = [k for k in room_player_info]

        for i in range(player_num):
            member_id_one = member_id_ls[i]
            ip_one = room_player_info[member_id_one].get('ip')
            name_one = room_player_info[member_id_one].get('nickname')

            for j in range(i + 1, player_num):
                member_id_two = member_id_ls[j]
                ip_two = room_player_info[member_id_two].get('ip')
                name_two = room_player_info[member_id_two].get('nickname')

                is_same_ip = ip_one == ip_two
                room_player_info[member_id_one]['iphintstatus'] = 1 if is_same_ip else 0
                room_player_info[member_id_two]['iphintstatus'] = 1 if is_same_ip else 0

                is_similar_id = SequenceMatcher(None, name_one, name_two).quick_ratio() >= 0.82
                room_player_info[member_id_one]['idhintstatus'] = 1 if is_similar_id else 0
                room_player_info[member_id_two]['idhintstatus'] = 1 if is_similar_id else 0

        return room_player_info

    async def _join_room_get_data(self, redis_obj, club_id, room_id, resultdata):
        if club_id:
            room_key = 'club_{}_room_{}'.format(club_id, room_id)
        else:
            room_key = 'normal_room_{}'.format(room_id)

        data = await redis_obj.hgetall(room_key)

        if not data:
            resultdata['errormsg'] = '1'  # 跟前端討論過後傳遞固定的

            raise ValueError('no room info')

        if data.get('status') == 'start':
            resultdata['errormsg'] = '1'  # 跟前端討論過後傳遞固定的

            raise ValueError('no room info')

        return data, room_key

    async def join_room(self, member_id, logintoken, redis_obj, club_id, room_id):
        """加入一般 or 俱樂部房間

        1. 取得房間 redis 資料
        2. 檢查是否可以加入房間（房間人數、俱樂部是否打烊）
        3. 寫入玩家 memberid 到 該房間的 redis 中，並刷新所有玩家 token
        4. 設定要透過 socket 給前端的資料
        5. 設定要給前端的資料

        Args:
            member_id:
            redis_obj:
            club_id (str): 俱樂部 ID，可為空值
            room_id (str): 房號
        """
        try:
            log_msg = '''
            pg_asqldb:join_room member_id:{}, logintoken:{}, club_id:{}, room_id:{}
            '''.format(member_id, logintoken, club_id, room_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            redis_data, room_key = await self._join_room_get_data(redis_obj, club_id,
                                                                  room_id, resultdata)

            # 計算房間人數
            player_amount = len(redis_obj.str_to_dict(redis_data.get('room_player_info')))

            if player_amount >= int(redis_data.get('player')):
                resultdata['errormsg'] = '2'  # 跟前端討論過後傳遞固定的
                resultdata['player_amount'] = player_amount
                resultdata['player'] = int(redis_data.get('player'))

                raise ValueError('player limit')

            if club_id != '':
                command = '''SELECT closestatus FROM club WHERE clubid="{}"
                        '''.format(club_id)

                datalen, data = await self.getdbdata(logintoken, command)

                if data.get('closestatus') == 1:
                    resultdata['errormsg'] = 'club closed'
                    raise ValueError('club closed')

            if int(redis_data.get('cointype')) == 1:  # 銀幣
                command = '''
                    SELECT nickname, silvercredit AS credit, lastip FROM member WHERE memberid={}
                '''.format(member_id)
            else:
                command = '''
                    SELECT m.nickname AS nickname, mc.credit AS credit, lastip FROM member AS m
                    LEFT JOIN memberclub AS mc ON mc.memberid=m.memberid
                    WHERE m.memberid={} AND mc.clubid="{}"
                '''.format(member_id, club_id)

            datalen, sql_data = await self.getdbdata(logintoken, command)

            room_player_info = redis_obj.str_to_dict(redis_data.get('room_player_info'))
            room_player_info[str(member_id)] = {
                'ready': 1,
                'memberid': member_id,
                'logintoken': logintoken,
                'nickname': sql_data.get('nickname'),
                'playercent': sql_data.get('credit'),
                'ip': sql_data.get('lastip'),
                'owner': 0,
            }

            room_player_info = self._join_room_id_ip_check_process(room_player_info)

            room_player_info = await self.room_fresh_logintoken(room_player_info)

            if len(room_player_info) == 0:
                resultdata['errormsg'] = 'room fresh logintoken failed'
                raise ValueError('room fresh logintoken failed')

            await redis_obj.hset(room_key, 'room_player_info', room_player_info)
            # 記錄該名玩家在哪間房間
            await redis_obj.hset('play_room_record', member_id, room_key)

            resultdata['room_player_info'] = []

            for k, v in room_player_info.items():
                resultdata['room_player_info'].append(v)

            command = '''
                SELECT name FROM gameroomsetting WHERE gameid="{}"
            '''.format(redis_data.get('game_id'))

            datalen, db_data = await self.getdbdata(logintoken, command)

            resultdata['roomid'] = redis_data.get('roomid')
            resultdata['gamename'] = db_data.get('name')
            resultdata['gameid'] = redis_data.get('game_id')
            resultdata['cointype'] = int(redis_data.get('cointype'))
            resultdata['minbet'] = int(redis_data.get('minbet'))
            resultdata['fee'] = int(redis_data.get('fee'))
            resultdata['minwalletrange'] = int(eval(redis_data.get('walletrange'))[0])
            resultdata['maxwalletrange'] = int(eval(redis_data.get('walletrange'))[1])
            resultdata['player'] = int(redis_data.get('player'))
            resultdata['rounds'] = int(redis_data.get('rounds'))
            resultdata['thinktime'] = int(redis_data.get('thinktime'))

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:join_room ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:join_room Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:join_room return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def room_ready(self, member_id, logintoken, redis_obj, club_id, room_id):
        """玩家在一般 or 俱樂部房間設定狀態為準備

        修改該玩家在房間中的 redis 資料
        刷新所有玩家 token

        Args:
            member_id:
            redis_obj:
            club_id (str): 俱樂部 ID，可為空值
            room_id (str): 房號
        """
        try:
            log_msg = '''
            pg_asqldb:room_ready member_id:{}, logintoken:{}, club_id:{}, room_id:{}
            '''.format(member_id, logintoken, club_id, room_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if club_id:
                room_key = 'club_{}_room_{}'.format(club_id, room_id)
            else:
                room_key = 'normal_room_{}'.format(room_id)

            room_player_info = await redis_obj.hget(room_key, 'room_player_info')
            room_player_info = redis_obj.str_to_dict(room_player_info)
            ready_status = int(room_player_info[str(member_id)]['ready'])
            room_player_info[str(member_id)]['ready'] = 1 - ready_status  # 0/1 互切，像 not 一樣

            room_player_info = await self.room_fresh_logintoken(room_player_info)

            if len(room_player_info) == 0:
                resultdata['errormsg'] = 'room fresh logintoken failed'
                raise ValueError('room fresh logintoken failed')

            await redis_obj.hset(room_key, 'room_player_info', room_player_info)

            resultdata['room_player_info'] = []

            for k, v in room_player_info.items():
                resultdata['room_player_info'].append(v)

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:room_ready ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:room_ready Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:room_ready return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _leave_room_return_roomcard(self, logintoken, room_info, member_id, club_id, already_play_round=0):
        """將剩餘的卡片返回給玩家

        1. 取得遊戲房卡設定
        2. 計算返還的卡片數量
        2.1 有開始玩過遊戲
            消耗房卡數量 = 無條件進位(已經遊玩局數/遊玩最小單位局數)
            歸還房卡數量 = 開局預扣房卡數量 - 消耗房卡數量
        2.2 沒玩過遊戲，直接全部退還
        3. 更新資料表（member、roomcard_log）
        """
        now_datetime = pg_general.datetimetostr_nof(pg_general.getutcnow_datetime())
        game_id = room_info.get('game_id')
        command = '''
            SELECT roomcard FROM gameroomsetting WHERE gameid="{}"
        '''.format(game_id)
        datalem, data = await self.getdbdata(logintoken, command)

        round_unit = int(data.get('roomcard').split(':')[0])

        if room_info.get('status') == 'wait':
            return_roomcard = room_info.get('roomcard')  # 開局預扣的房卡數量
        else:
            consume_roomcard = int(math.ceil(already_play_round / round_unit))
            return_roomcard = int(room_info.get('roomcard')) - consume_roomcard

        if club_id:
            update_command = '''
                UPDATE club SET roomcard=roomcard+{}
                WHERE clubid="{}"
            '''.format(return_roomcard, club_id)
            insert_command = '''
                INSERT INTO roomcard_log
                (member_id, game_id, roomcard, datetime, transfer_type, club_id)
                VALUES ({}, "{}", {}, "{}", 1, "{}")
            '''.format(member_id, game_id, return_roomcard, now_datetime, club_id)
        else:
            update_command = '''
                UPDATE member SET roomcard=roomcard+{}
                WHERE memberid={}
            '''.format(return_roomcard, member_id)
            insert_command = '''
                INSERT INTO roomcard_log
                (member_id, game_id, roomcard, datetime, transfer_type)
                VALUES ({}, "{}", {}, "{}", 1)
            '''.format(member_id, game_id, return_roomcard, now_datetime)

        update_result = await self.updatedbdata(logintoken, update_command)
        insert_result, result_index = await self.insertdbdata(logintoken, insert_command)

        log_msg = '''
            pg_asqldb:_leave_room_return_roomcard logintoken:{} return {} roomcard to {}, update_result={}, insert_result={}
        '''.format(logintoken, return_roomcard, member_id, update_result, insert_result)
        pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

    async def leave_room(self, member_id, logintoken, redis_obj, club_id, room_id):
        """踢出、離開、解散一般 or 俱樂部房間

        取得房間 redis 資料、刷新所有玩家的 logintoken
        若為房長就解散，從 redis 中刪除資料，並返還剩餘房卡
        若為房員就離開，從該房間的 redis 中移除玩家 logintoken

        Args:
            member_id:
            redis_obj:
            club_id (str): 俱樂部 ID，可為空值
            room_id (str): 房號
        """
        try:
            log_msg = '''
            pg_asqldb:leave_room member_id:{}, logintoken:{}, club_id:{}, room_id:{}
            '''.format(member_id, logintoken, club_id, room_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if club_id:
                room_key = 'club_{}_room_{}'.format(club_id, room_id)
            else:
                room_key = 'normal_room_{}'.format(room_id)

            chatroom = 'chatroom_channel_' + room_key

            data = await redis_obj.hgetall(room_key)

            if not data:
                resultdata['errormsg'] = 'no room info'

                raise ValueError('no room info')

            room_player_info = redis_obj.str_to_dict(data.get('room_player_info'))
            room_player_info = await self.room_fresh_logintoken(room_player_info)

            if len(room_player_info) == 0:
                resultdata['errormsg'] = 'room fresh logintoken failed'
                raise ValueError('room fresh logintoken failed')

            logintoken_ls = [v.get('logintoken') for k, v in room_player_info.items()]

            if str(member_id) == str(data.get('owner')):
                await self._leave_room_return_roomcard(logintoken, data, member_id, club_id)
                await redis_obj.del_key(room_key)
                await redis_obj.del_key(chatroom)
                # 刪除所有玩家在哪間房間
                for k, v in room_player_info.items():
                    await redis_obj.hdel('play_room_record', k)
                room_player_info = {}  # 關房間，房間資訊為空

            else:
                del room_player_info[str(member_id)]

                await redis_obj.hset(room_key, 'room_player_info', room_player_info)
                # 刪除該名玩家在哪間房間
                await redis_obj.hdel('play_room_record', member_id)

            resultdata['logintoken_list'] = logintoken_ls
            resultdata['room_player_info'] = []

            for k, v in room_player_info.items():
                resultdata['room_player_info'].append(v)

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:leave_room ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:leave_room Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:leave_room return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def dismiss_room(self, redis_obj, room_key, already_play_round):
        """提供 dummy GS 結束遊戲時同步 SD555 的房間資訊

        GS 遊戲結束之後解散 SD555 redis 房間資訊，並計算是否該歸還房卡

        Args:
            room_key (str): 房間 ID
            already_play_round (int): 以遊玩過的局數
        """
        try:
            log_msg = '''pg_asqldb:dismiss_room room_key:{}, already_play_round:{}
            '''.format(room_key, already_play_round)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            data = await redis_obj.hgetall(room_key)

            if not data:
                resultdata['errormsg'] = 'no room info'

                raise ValueError('no room info')

            room_player_info = redis_obj.str_to_dict(data.get('room_player_info'))
            for member_id, v in room_player_info.items():
                # 記錄該名玩家在哪間房間
                await redis_obj.hdel('play_room_record', member_id)

            chatroom = 'chatroom_channel_' + room_key

            if 'club' in room_key:
                club_id = room_key.split('_')[1]
            else:
                club_id = None

            await self._leave_room_return_roomcard('dismiss_room {}'.format(room_key), data,
                                                   data.get('owner'), club_id, already_play_round)
            await redis_obj.del_key(room_key)
            await redis_obj.del_key(chatroom)

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:dismiss_room ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:dismiss_room Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:dismiss_room return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def _clear_room_data(self, redis_obj):
        """清除 redis 房間相關資料 TODO for test
        """
        room_key = '*_room_*'

        room_key_ls = await redis_obj.get_all_keys(room_key)

        for key in room_key_ls:
            await redis_obj.del_key(key)

        return room_key_ls

    async def _room_start_send_info_to_GS(self, room_key, room_info, player_info_ls):
        """

        Args:
            player_info_ls (list): 用外面整理成串列的資料
        """
        game_id = room_info.get('game_id')

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'room_start _room_start_send_info_to_GS: game_id{}'.format(game_id))

        command = '''
            SELECT roomcard, playermin FROM gameroomsetting WHERE gameid="{}"
        '''.format(game_id)
        datalem, data = await self.getdbdata('_room_start_send_info_to_GS get roomcard', command)

        round_unit = int(data.get('roomcard').split(':')[0])

        if len(player_info_ls) < int(data.get('playermin')):  # 檢查是否有達到最少人數
            return False

        if game_id in (GameID.dummy, GameID.dummy_king):
            json_dc = {
                "host_api_key": env_setting.PS_HOST_ID_S,
                "room_key": room_key,
                "ipfilter": int(eval(room_info.get('sameip'))),
                "cellscore": int(room_info.get('minbet')),
                "thinktime": int(room_info.get('thinktime')),
                "accessscore": int(eval(room_info.get('walletrange'))[0]),
                "max_score": int(eval(room_info.get('walletrange'))[1]),
                "pre_arbitrage": 0,
                "out_tax": int(room_info.get('fee')),
                "game_count": int(room_info.get('rounds')),
                "player_info": player_info_ls,
                "round_unit": round_unit
            }
            if game_id == GameID.dummy:
                url = env_setting.DUMMY_CREATE_ROOM_URL
            elif game_id == GameID.dummy_king:
                url = env_setting.DUMMY_KING_CREATE_ROOM_URL

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'room_start _room_start_send_info_to_GS:{}, json:{}'.format(url, json_dc))

            # call ps signin api
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=60, json=json_dc) as response:
                    if response.status == 200:
                        data = await response.json()
                        if int(data.get('status_code')) == 0:
                            return True
            return False
        elif game_id == GameID.pok_deng:

            new_player_info_ls = []
            for member_data in player_info_ls:
                member_data["memberid"] = str(member_data["memberid"])
                new_player_info_ls.append(member_data)

            subgameid = 0
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'room_start walletrange:{}'.format(int(eval(room_info.get('walletrange'))[0])))
            accessscore_list = [500, 2000, 5000, 20000, 50000, 100000]
            for i in range(len(accessscore_list)):
                if accessscore_list[i] == int(room_info.get('minbet')):
                    subgameid = i
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'room_start walletrange:{}'.format(subgameid))
            json_dc = {
                "host_api_key": env_setting.PS_HOST_ID_S,
                "room_key": room_key,
                "gameid": GameID.pok_deng,
                "subgameid": subgameid,
                "addbot": 0,
                "blacklistvalue": 0,
                "ipblock": int(eval(room_info.get('sameip'))),
                "roundstartwaitingtime": int(room_info.get('thinktime')),
                "pre_arbitrage": 0,
                "out_tax": int(room_info.get('fee')),
                "roundcount": int(room_info.get('rounds')),
                "player_info": new_player_info_ls,
            }
            url = env_setting.POK_DENG_CREATE_ROOM_URL

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'room_start _room_start_send_info_to_GS:{}, json:{}'.format(url, json_dc))

            # call ps signin api
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=60, json=json_dc) as response:
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'room_start _room_start_send_info_to_GS:{}, json:{}'.format(url, response))
                    if response.status == 200:
                        data = await response.json()
                        if int(data.get('status_code')) == 0:
                            return True
            return False

    async def room_start(self, member_id, logintoken, redis_obj, club_id, room_id):
        """房間開始遊戲

        1. 取得房間資訊後、刷新所有玩家 logintoken 回傳，要讓前端做操作使用的
        2. 將房間設定寫到 GS
        3. 修改房間狀態為開始中
        """
        try:
            log_msg = '''
            pg_asqldb:room_start member_id:{}, logintoken:{}, club_id:{}, room_id:{}
            '''.format(member_id, logintoken, club_id, room_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if club_id:
                room_key = 'club_{}_room_{}'.format(club_id, room_id)
            else:
                room_key = 'normal_room_{}'.format(room_id)

            data = await redis_obj.hgetall(room_key)

            if not data:
                resultdata['errormsg'] = 'no room info'

                raise ValueError('no room info')

            room_player_info = redis_obj.str_to_dict(data.get('room_player_info'))

            room_player_info = await self.room_fresh_logintoken(room_player_info)

            if len(room_player_info) == 0:
                resultdata['errormsg'] = 'room fresh logintoken failed'
                raise ValueError('room fresh logintoken failed')

            player_info_ls = []
            for k, v in room_player_info.items():
                player_info_ls.append(v)

            logintoken_ls = [v.get('logintoken') for k, v in room_player_info.items()]

            resultdata['logintoken_list'] = logintoken_ls

            gs_result = await self._room_start_send_info_to_GS(room_key, data, player_info_ls)
            if gs_result is False:
                raise ValueError('send info to GS failed')

            await redis_obj.hset(room_key, 'status', 'start')

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:room_start ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:room_start Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:room_start return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def get_game_room_setting(self, logintoken):
        try:
            log_msg = '''
            pg_asqldb:get_geme_room_setting logintoken:{}
            '''.format(logintoken)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            select_command = 'SELECT * FROM gameroomsetting'

            datalen, data = await self.getdbdata(logintoken, select_command, fetchall=True)

            if datalen == 0:
                resultdata['errormsg'] = 'no game room setting data'

                raise ValueError('no game room setting data')

            for dc in data:
                tmp_game_setting_dc = {}

                tmp_data = json.loads(dc.get('setting', '{}'))
                tmp_data['betlist'] = dc.get('betlist', '').split(',')
                tmp_data['outtaxmin'] = dc.get('outtaxmin')
                tmp_data['outtaxmax'] = dc.get('outtaxmax')
                tmp_data['playermin'] = dc.get('playermin')
                tmp_data['playermax'] = dc.get('playermax')
                tmp_data['thinktimemin'] = dc.get('thinktimemin')
                tmp_data['thinktimemax'] = dc.get('thinktimemax')
                tmp_data['scoretimes'] = dc.get('scoretimes')
                tmp_data['autooperate'] = dc.get('autooperate')
                round_unit, consume_roomcard = dc.get('roomcard', '').split(':')

                tmp_data['roundunit'] = int(round_unit)
                tmp_data['consumeroomcard'] = int(consume_roomcard)

                tmp_game_setting_dc['gameid'] = dc.get('gameid')
                tmp_game_setting_dc['name'] = dc.get('name')
                tmp_game_setting_dc['setting'] = tmp_data

                resultdata[dc.get('gameid')] = tmp_game_setting_dc

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_geme_room_setting ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_geme_room_setting Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_geme_room_setting return, result:{0},resultdata:{1}'.format(result,
                                                                                                           resultdata))
            return result, resultdata

    async def get_room_card(self, logintoken, member_id, club_id):
        try:
            log_msg = '''
            pg_asqldb:get_room_card logintoken:{}, member_id:{}, club_id:{}
            '''.format(logintoken, member_id, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if club_id:
                select_command = '''
                    SELECT roomcard FROM club WHERE clubid="{}" 
                '''.format(club_id)

            elif member_id:
                select_command = '''
                    SELECT roomcard FROM member WHERE memberid="{}" 
                '''.format(member_id)

            datalen, data = await self.getdbdata(logintoken, select_command)

            if datalen != 1:
                resultdata['errormsg'] = 'no room card data'

                raise ValueError('no room card data')

            resultdata['roomcard'] = data.get('roomcard')

            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_room_card ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_room_card Exception except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_room_card return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def get_room_info(self, logintoken, member_id, club_id, redis_obj):
        try:
            log_msg = '''
            pg_asqldb:get_room_info logintoken:{}, member_id:{}, club_id:{}
            '''.format(logintoken, member_id, club_id)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if club_id:
                room_key = 'club_{}_room_*'.format(club_id)
            else:
                room_key = 'normal_room_*'

            room_key_ls = await redis_obj.get_all_keys(room_key)

            room_info_ls = []

            for key in room_key_ls:
                room_info = await redis_obj.hgetall(key)
                room_info_ls.append(room_info)

            resultdata['room_info_list'] = room_info_ls
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_room_info ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_room_info Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_room_info return, result:{0},resultdata:{1}'.format(result, resultdata))
            return result, resultdata

    async def prohibitplayerall(self, banplayerall, memberlist):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:prohibitplayerall banplayerall:{0}, memberlist:{1}'.format(
                                    banplayerall, memberlist))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            error_list = []
            logintoken = 0
            if banplayerall == 1:

                banplayergame = 1
                banchat = 1

                for memberid in memberlist:
                    command = 'update memberclub set banplayergame = {0}, banchat = {1}  WHERE  memberid = {2}'.format(
                        banplayergame, banchat, memberid)
                    updateresultclub = await self.updatedbdata(logintoken, command)

                    command = 'update member set banplayergame = {0}, banchat = {1}  WHERE  memberid = {2}'.format(
                        banplayergame, banchat, memberid)
                    updateresultmember = await self.updatedbdata(logintoken, command)

                    command = 'select banplayergame, banchat FROM memberclub WHERE memberid = {0}'.format(memberid)
                    datalen, dataclub = await self.getdbdata(logintoken, command)

                    club_banplayergame = dataclub.get('banplayergame')
                    club_banchat = dataclub.get('banchat')

                    command = 'select banplayergame, banchat FROM member WHERE memberid = {0}'.format(memberid)
                    datalen, datamember = await self.getdbdata(logintoken, command)

                    member_banplayergame = dataclub.get('banplayergame')
                    member_banchat = dataclub.get('banchat')

                    if club_banplayergame != 1 or club_banchat != 1 or member_banplayergame != 1 or member_banchat != 1:
                        error_list.append(memberid)

                result = pg_general.Apiresult.success
                resultdata = {
                    "error_list": error_list
                }

            elif banplayerall == 0:

                banplayergame = 0
                banchat = 0

                for memberid in memberlist:
                    command = 'update memberclub set banplayergame = {0}, banchat = {1}  WHERE  memberid = {2}'.format(
                        banplayergame, banchat, memberid)
                    updateresultclub = await self.updatedbdata(logintoken, command)

                    command = 'update member set banplayergame = {0}, banchat = {1}  WHERE  memberid = {2}'.format(
                        banplayergame, banchat, memberid)
                    updateresultmember = await self.updatedbdata(logintoken, command)

                    command = 'select banplayergame, banchat FROM memberclub WHERE memberid = {0}'.format(memberid)
                    datalen, dataclub = await self.getdbdata(logintoken, command)

                    club_banplayergame = dataclub.get('banplayergame')
                    club_banchat = dataclub.get('banchat')

                    command = 'select banplayergame, banchat FROM member WHERE memberid = {0}'.format(memberid)
                    datalen, datamember = await self.getdbdata(logintoken, command)

                    member_banplayergame = dataclub.get('banplayergame')
                    member_banchat = dataclub.get('banchat')

                    if club_banplayergame != 0 or club_banchat != 0 or member_banplayergame != 0 or member_banchat != 0:
                        error_list.append(memberid)

                result = pg_general.Apiresult.success
                resultdata = {
                    "error_list": error_list
                }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:prohibitplayerall ValueError except:{0}, memberid:{1}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:prohibitplayerall Exception except:{0}'.format(format_exc()))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:prohibitplayerall return, result:{0},resultdata:{1}'.format(result,
                                                                                                       resultdata))
        return result, resultdata

    async def getprohibitplayer(self, memberlist, clubid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getprohibitplayer member_id:{0} clubid:{1}'.format(memberlist, clubid))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            error_list = []
            dataclub_list = []
            logintoken = "123456789"

            for member_id in memberlist:
                if clubid is not "":
                    command = '''SELECT c.name, mc.clubid, mc.banplayergame, mc.banchat, mb.lastip, mb.lastlogintime FROM member AS mb
                                 LEFT JOIN memberclub AS mc ON mc.memberid = mb.memberid
                                 LEFT JOIN club AS c ON c.clubid = mc.clubid
                                 WHERE mb.memberid = {0} AND mc.clubid = {1}'''.format(member_id, clubid)

                else:
                    command = '''SELECT c.name, mc.clubid, mc.banplayergame, mc.banchat, mb.lastip, mb.lastlogintime FROM member AS mb
                                 LEFT JOIN memberclub AS mc ON mc.memberid = mb.memberid
                                 LEFT JOIN club AS c ON c.clubid = mc.clubid
                                 WHERE mb.memberid = {0}'''.format(member_id)

                datalen, dataclub = await self.getdbdata(logintoken, command, fetchall=True)

                for i in range(datalen):

                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        'pg_asqldb:getprohibitplayer member_id:{0} dataclub[{1}]:{2}'.format(memberlist,
                                                                                                             i,
                                                                                                             dataclub[
                                                                                                                 i]))

                    lastlogintime = pg_general.converttype(dataclub[i].get('lastlogintime'), str)
                    banplayergame = dataclub[i].get('banplayergame')
                    banchat = dataclub[i].get('banchat')

                    dataclub[i]['lastlogintime'] = lastlogintime
                    dataclub[i]['memberid'] = member_id
                    dataclub_list.append(dataclub[i])

                    if banplayergame not in [0, 1] or banchat not in [0, 1]:
                        error_list.append(member_id)

                result = pg_general.Apiresult.success
                resultdata = {
                    "dataclub": dataclub_list,
                    "error_list": error_list
                }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getprohibitplayer ValueError:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getprohibitplayer except:{0}'.format(format_exc()))

        return result, resultdata

    async def sendgiftsms(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgiftsms memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 撈此玩家 資料
            command = 'select phone,phonebindstatus,phonevalidatecode,phonevalidatetime from member where memberid="{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get member info error')

            phonebindstatus = data.get('phonebindstatus')
            phonevalidatecode = data.get('phonevalidatecode')
            phonevalidatetime = data.get('phonevalidatetime')
            phone = data.get('phone')

            if phonebindstatus != 2:  # 未完成綁定手機
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 1
                }
                return result, resultdata

            nowutcdatetime = pg_general.getutcnow_datetime()
            overseconds = (nowutcdatetime - phonevalidatetime).total_seconds()
            if overseconds < 60:  # 一分鐘未到
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 2
                }
                return result, resultdata

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

    async def _send_get_to_lobbyserver(self, logintoken, silvercredit, roomcard, mode, amount, member_id):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:line_deposit_log _send_get_to_lobbyserver , logintoken:{0}, silvercredit:{1}, roomcard:{2}, mode:{3}, amount:{4}, member_id:{5}'
                                .format(logintoken, silvercredit, roomcard, mode, amount, member_id))

            if mode == 2:
                gem_amount = amount
                roomcard_amount = 0

            elif mode == 3:
                gem_amount = 0
                roomcard_amount = amount

            msg = {
                'member_id': member_id,
                'credit_s': silvercredit,
                'credit_s_amount': gem_amount,
                'roomcard': roomcard,
                'roomcard_amount': roomcard_amount,
                'mode': mode,
                'commandid': 3000032
            }

            line_game_get_url = 'http://10.148.0.6:80/putinbroadcastqueue'
            headers = {"Content-Type": "application/json;charset=utf-8"}
            send_param = json.dumps({
                "msg": msg,
                "logintoken": logintoken
            })

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'pg_asqldb:line_deposit_log _send_get_to_lobbyserver send_param:{0}'.format(send_param))

            async with aiohttp.ClientSession() as session:
                async with session.get(line_game_get_url, data=send_param,
                                       headers=headers) as response:  # , headers=headers
                    if response.status != 200:
                        raise ValueError('send request for WS error {}'.format(response.status))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:line_deposit_log _send_get_to_lobbyserver ValueError:{0}'.format(
                                    format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:line_deposit_log _send_get_to_lobbyserver Exception:{0}'.format(
                                    format_exc()))

    async def line_deposit_log(self, order_num, product_name, line_sub, trade_time, cash, amount, mode, status, method):
        try:
            log_msg = """pg_asqldb:line_deposit_log order_num:{0}, product_name:{1}, line_sub:{2}, trade_time:{3}, 
            cash:{4}, amount:{5}, mode:{6}, status:{7}""".format(order_num, product_name, line_sub, trade_time, cash,
                                                                 amount, mode, status, method)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT memberid, roomcard, silvercredit from member WHERE linesub = "{0}"'.format(line_sub)
            datalen, data = await self.getdbdata('SELECT memberid', command)

            if datalen != 1:
                resultdata['result'] = False
                resultdata['errormsg'] = 'This user data is not in SD555 member table'
                return result, resultdata

            member_id = data.get('memberid')
            roomcard = data.get('roomcard')
            silvercredit = data.get('silvercredit')

            if mode == 2:
                content = 'Gem * {0}'.format(amount)
                updatestr = 'silvercredit = {0} + {1}'.format(silvercredit, amount)
                purpose = 2
                buybefore = silvercredit
            elif mode == 3:
                content = 'roomcard * {0}'.format(amount)
                updatestr = 'roomcard = {0} + {1}'.format(roomcard, amount)
                purpose = 3
                buybefore = roomcard

            command = 'UPDATE member set {0} WHERE linesub = "{1}" '.format(updatestr, line_sub)
            updateresult = await self.updatedbdata('deposit to DB', command)

            if updateresult is not True:
                resultdata['result'] = False
                resultdata['errormsg'] = 'Deposit to member table error'
                return result, resultdata

            command = 'SELECT roomcard, silvercredit, logintoken FROM member WHERE linesub = "{0}"'.format(line_sub)
            datalen, data = await self.getdbdata('Send WS', command)

            roomcard = data.get('roomcard')
            silvercredit = data.get('silvercredit')
            logintoken = data.get('logintoken')

            insert_str = """order_number, product_name, uuid, member_id, trade_time, cash, amount, mode, status, method"""
            insert_value = """ "{0}", "{1}", "{2}", {3}, "{4}", {5}, {6}, {7}, {8}, "{9}" """.format(order_num,
                                                                                                     product_name,
                                                                                                     line_sub,
                                                                                                     member_id,
                                                                                                     trade_time, cash,
                                                                                                     amount, mode,
                                                                                                     status, method)

            command = 'insert into line_trade_log({0}) values({1})'.format(insert_str, insert_value)
            insertresult, index = await self.insertdbdata('insert line_trade_log', command)

            if insertresult is not True:
                resultdata['result'] = False
                resultdata['errormsg'] = 'insert line trade log error'
                return result, resultdata

            await self._send_get_to_lobbyserver(logintoken, silvercredit, roomcard, mode, amount, member_id)

            command = 'INSERT INTO `slot-game`.member_wallet_log (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time) values("{0}", "{1}", {2}, {3}, "{4}", {5}, {6}, "{7}", "{8}")' \
                .format(env_setting.PS_HOST_NAME_S, member_id, purpose, 3, order_num, amount, buybefore, "API",
                        trade_time)
            insertresult, index = await self.slot_game_db.insertdbdata('line_deposit_log insert_member_wallet_log',
                                                                       command)

            title = 'Deposit Success !!'
            amount_mail = 0
            promotionid_mail = 6
            main_type = 6
            main_type_deposit = 0
            uri = "uri"
            dateline = pg_general.datetimetostr_nof(pg_general.getutcnow_datetime() + timedelta(hours=24))
            memberlist = [member_id]
            send_mode = 0

            result_common, resultdata_common = await self.send_inbox_to_member(title, content, uri, promotionid_mail,
                                                                               amount_mail, main_type, dateline,
                                                                               memberlist, send_mode)

            if None in [resultdata_common['error_list']]:
                result = pg_general.Apiresult.success
                resultdata = {
                    'result': False,
                    'error_list_deposit': resultdata_common['error_list'],
                    'errormsg': 'send Deposit mail error'
                }
                return result, resultdata

            resultdata = {
                "result": True
            }

            result = pg_general.Apiresult.success

            log_msg = """pg_asqldb:line_deposit_log resultdata:{0}""".format(resultdata)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:line_deposit_log ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:line_deposit_log Exception except:{0}'.format(format_exc()))

        return result, resultdata

    async def _create_line_access_token(self):
        try:
            log_msg = """pg_asqldb:_create_line_access_token"""
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            access_token = "%.3d%.13d%.3d" % (
            random.randint(100, 999), (int(round(time.time() * 1000))), random.randint(100, 999))

            log_msg = """pg_asqldb:_create_access_token access_token:{0}""".format(access_token)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            if access_token is None:
                raise ValueError('create line_access_token error')

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:_create_line_access_token ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:_create_line_access_token Exception except:{0}'.format(format_exc()))

        return access_token

    async def _check_line_access_token_valid(self, access_token, sub, name):
        try:
            log_msg = """pg_asqldb:_check_line_access_token_valid access_token:{0}, sub:{1}, name:{2}""".format(
                access_token, sub, name)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            create_line_token_time = pg_general.strtodatetime(pg_general.getutcnow())

            command = 'SELECT line_access_token, line_access_token_valid_datetime from member WHERE linesub = "{0}"'.format(
                sub)
            datalen, data = await self.getdbdata('Get line_access_token_time', command)

            if data is None:
                command = 'UPDATE line_profile set access_token="{0}" WHERE sub = "{1}"'.format(access_token, sub)
                updateresult = await self.updatedbdata('update_access_token', command)
                return access_token

            else:
                line_token_valid_datetime = data.get('line_access_token_valid_datetime')
                diff_time = pg_general.converttype((create_line_token_time - line_token_valid_datetime).total_seconds(),
                                                   int)

                if diff_time > 3600:
                    command = 'UPDATE member, line_profile set line_profile.access_token="{0}", member.line_access_token = "{0}", member.line_access_token_valid_datetime = "{1}" WHERE member.linesub = "{2}" AND line_profile.sub = "{2}" '.format(
                        access_token, create_line_token_time, sub)
                    updateresult = await self.updatedbdata('update_member_table', command)
                else:
                    access_token = data.get('line_access_token')

            log_msg = """pg_asqldb:_check_line_access_token_valid return access_token:{0}""".format(access_token)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:_check_line_access_token_valid ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:_check_line_access_token_valid Exception except:{0}'.format(format_exc()))

        return access_token

    async def _clean_line_nickname_charactor(self, nickname):
        try:
            log_msg = '''pg_asqldb:_clean_line_nickname_charactor nickname:{0}'''.format(nickname)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            pattern = re.compile(r"[^\u0E00-\u0E7F\u4e00-\u9fa5a-zA-Z0-9]")

            char_to_remove = re.findall(pattern, nickname)
            list_with_char_removed = [char for char in nickname if not char in char_to_remove]
            clean_nickname = ''.join(list_with_char_removed)

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:_clean_line_nickname_charactor ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:_clean_line_nickname_charactor Exception except:{0}'.format(format_exc()))

        return clean_nickname

    async def bind_line_proflie(self, sub, name, picture, email):
        try:
            log_msg = """pg_asqldb:bind_line_proflie sub:{0}, name:{1}, picture:{2}, email:{3}""".format(
                sub, name, picture, email)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT * from line_profile WHERE sub = "{0}"'.format(sub)
            datalen, data = await self.getdbdata('select line_profile', command, fetchall=True)

            if datalen == 1:
                pg_general.writelog(pg_general.PG_LogerLevel.info, "bind_line_proflie 123")
                clean_nickname = await self._clean_line_nickname_charactor(name)

                if clean_nickname == '':
                    clean_nickname = await pg_namesample.makeanewnameforline(self)

                command = 'UPDATE line_profile set sub = "{0}", name = "{1}", picture = "{2}", line_email = "{3}"'.format(
                    sub, clean_nickname, picture, email)
                updateresult = await self.updatedbdata("update line_profile table", command)

                access_token = await self._create_line_access_token()
                access_token = await self._check_line_access_token_valid(access_token, sub, clean_nickname)

            elif datalen == 0:
                access_token = await self._create_line_access_token()
                clean_nickname = await self._clean_line_nickname_charactor(name)

                if clean_nickname == '':
                    clean_nickname = await pg_namesample.makeanewnameforline(self)

                command = 'insert into line_profile(access_token, sub, name, picture, line_email) values("{0}", "{1}", "{2}", "{3}", "{4}")'.format(
                    access_token, sub, clean_nickname, picture, email)
                insertresult, index = await self.insertdbdata('insert line_profile', command)

                if insertresult is not True:
                    resultdata['Member'] = False
                    resultdata['errormsg'] = 'insert to line_profile table error'
                    return result, resultdata

            else:
                resultdata['Member'] = False
                resultdata['errormsg'] = 'get sub from line_profile table error'
                return result, resultdata

            resultdata = {
                "Member": True,
                "access_token": access_token,
                "redirect_uri": env_setting.SD555_LOBBY_URL + '?line_access_token={0}'.format(access_token)
            }
            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:bind_line_proflie ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:bind_line_proflie ValueError except:{0}'.format(format_exc()))

        return result, resultdata

    async def updatepopulargame(self, game_name):
        try:
            log_msg = """pg_asqldb:updatepopulargame game_name:{0}""".format(game_name)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'UPDATE popular_game SET game_name = "{0}"'.format(game_name)
            updateresult = await self.updatedbdata('update popular game', command)

            if updateresult is not True:
                resultdata['result'] = False
                resultdata['errormsg'] = 'update popular_game table error'
                return result, resultdata

            command = 'SELECT game_name from popular_game WHERE game_name = "{0}"'.format(game_name)
            datalen, data = await self.getdbdata('SELECT game_name after update', command)

            if datalen != 1 or data is None:
                resultdata['result'] = False
                resultdata['errormsg'] = 'SELECT game_name after update error'
                return result, resultdata

            popular_game_name = data.get('game_name')
            result = pg_general.Apiresult.success
            resultdata = {
                "result": True,
                "game_name": popular_game_name
            }

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatepopulargame ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updatepopulargame ValueError except:{0}'.format(format_exc()))

        return result, resultdata

    async def populargame(self, redis_obj, sub, name, picture, email, ip):
        try:
            log_msg = """pg_asqldb:populargame sub:{0}, name:{1}, picture:{2}, email:{3}, ip:{4}""".format(
                sub, name, picture, email, ip)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT game.gameid, game.gamename from game, popular_game WHERE popular_game.game_name = game.gamename'
            datalen, data = await self.getdbdata('SELECT popular game', command)

            if datalen != 1:
                resultdata['result'] = False
                resultdata['errormsg'] = 'SELECT popular gameid error'
                return result, resultdata

            game_id = data.get('gameid')

            command = 'SELECT * from line_profile WHERE sub = "{0}"'.format(sub)
            datalen, data = await self.getdbdata('select line_profile', command, fetchall=True)

            if datalen == 1:
                access_token = await self._create_line_access_token()
                access_token = await self._check_line_access_token_valid(access_token, sub, name)

            elif datalen == 0:
                access_token = await self._create_line_access_token()
                clean_nickname = await self._clean_line_nickname_charactor(name)

                if clean_nickname == '':
                    clean_nickname = await pg_namesample.makeanewnameforline(self)

                command = 'insert into line_profile(access_token, sub, name, picture, line_email) values("{0}", "{1}", "{2}", "{3}", "{4}")'.format(
                    access_token, sub, clean_nickname, picture, email)
                insertresult, index = await self.insertdbdata('insert line_profile', clean_nickname)

                if insertresult is not True:
                    resultdata['Member'] = False
                    resultdata['errormsg'] = 'insert to line_profile table error'
                    return result, resultdata

            else:
                resultdata['Member'] = False
                resultdata['errormsg'] = 'get sub from line_profile table error'
                return result, resultdata

            log_msg = """pg_asqldb:populargame access_token:{0}""".format(access_token)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            i = 0
            while i < 1000:
                logintoken = pg_general.generatorsha256()

                command = '''SELECT * FROM member WHERE logintoken="{}"
                '''.format(logintoken)

                datalen, data = await self.getdbdata(logintoken, command)

                if datalen == 0:
                    i = 1000

            try:
                totalresult, clientdata, serverdata = await self.login(redis_obj=redis_obj, fblink=None,
                                                                       defaultchannelindex=None,
                                                                       fbavatarobj=None, logintoken=logintoken,
                                                                       deviceid="", fbid=None, fbtoken=None,
                                                                       fbavatar=None, fbnickname=None, ip=ip,
                                                                       platform=3, devicedescription=None,
                                                                       lobbyserverip=env_setting.SD555_LOBBY_IP,
                                                                       region=None, region_sub=None, city=None,
                                                                       fcmtoken=None, newaccflag=0, connecttype="0",
                                                                       lineaccesstoken=access_token)

                memberid = clientdata.get('memberid')

            except Exception:
                result = pg_general.Apiresult.parametererror
                resultdata['result'] = False
                resultdata['errormsg'] = 'login to SD555 lobby error'
                return result, resultdata

            jsoncontent = {
                "gameid": game_id,
                "hallid": 1
            }

            try:
                result, resultdata = await self.joincardgame(logintoken, memberid, jsoncontent)

            except Exception:
                result = pg_general.Apiresult.parametererror
                resultdata['result'] = False
                resultdata['errormsg'] = 'login to game server error'
                return result, resultdata

            resultdata.pop("gameserver")
            resultdata['result'] = True

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:populargame ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:populargame ValueError except:{0}'.format(format_exc()))

        return result, resultdata

    async def referralfriendlogin(self, redis_obj, sub, name, picture, email, ip):
        try:
            log_msg = """pg_asqldb:referralfriendlogin sub:{0}, name:{1}, picture:{2}, email:{3}, ip:{4}""".format(
                sub, name, picture, email, ip)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT game.gameid, game.gamename from game, popular_game WHERE popular_game.game_name = game.gamename'
            datalen, data = await self.getdbdata('SELECT popular game', command)

            if datalen != 1:
                resultdata['result'] = False
                resultdata['errormsg'] = 'SELECT popular gameid error'
                return result, resultdata

            game_id = data.get('gameid')

            command = 'SELECT * from line_profile WHERE sub = "{0}"'.format(sub)
            datalen, data = await self.getdbdata('select line_profile', command, fetchall=True)

            if datalen == 1:
                access_token = await self._create_line_access_token()
                access_token = await self._check_line_access_token_valid(access_token, sub, name)

            elif datalen == 0:
                access_token = await self._create_line_access_token()
                clean_nickname = await self._clean_line_nickname_charactor(name)

                if clean_nickname == '':
                    clean_nickname = await pg_namesample.makeanewnameforline(self)

                command = 'insert into line_profile(access_token, sub, name, picture, line_email) values("{0}", "{1}", "{2}", "{3}", "{4}")'.format(
                    access_token, sub, clean_nickname, picture, email)
                insertresult, index = await self.insertdbdata('insert line_profile', command)

                if insertresult is not True:
                    resultdata['Member'] = False
                    resultdata['errormsg'] = 'insert to line_profile table error'
                    return result, resultdata

            else:
                resultdata['Member'] = False
                resultdata['errormsg'] = 'get sub from line_profile table error'
                return result, resultdata

            log_msg = """pg_asqldb:populargame access_token:{0}""".format(access_token)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            i = 0
            while i < 1000:
                logintoken = pg_general.generatorsha256()

                command = '''SELECT * FROM member WHERE logintoken="{}"
                '''.format(logintoken)

                datalen, data = await self.getdbdata(logintoken, command)

                if datalen == 0:
                    i = 1000

            try:
                totalresult, clientdata, serverdata = await self.login(redis_obj=redis_obj, fblink=None,
                                                                       defaultchannelindex=None,
                                                                       fbavatarobj=None, logintoken=logintoken,
                                                                       deviceid="", fbid=None, fbtoken=None,
                                                                       fbavatar=None, fbnickname=None, ip=ip,
                                                                       platform=3, devicedescription=None,
                                                                       lobbyserverip=env_setting.SD555_LOBBY_IP,
                                                                       region=None, region_sub=None, city=None,
                                                                       fcmtoken=None, newaccflag=0, connecttype="0",
                                                                       lineaccesstoken=access_token)

                memberid = clientdata.get('memberid')

            except Exception:
                result = pg_general.Apiresult.parametererror
                resultdata['result'] = False
                resultdata['errormsg'] = 'login to SD555 lobby error'
                return result, resultdata

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriendlogin ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriendlogin ValueError except:{0}'.format(format_exc()))

        return result, resultdata

    async def depositpackage(self, sub, name, picture, email):
        try:
            log_msg = """pg_asqldb:depositpackage sub:{0}, name:{1}, picture:{2}, email:{3}""".format(sub, name,
                                                                                                      picture, email)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT * from line_profile WHERE sub = "{0}"'.format(sub)
            datalen_line, data_line = await self.getdbdata('select line_profile', command)

            log_msg = """pg_asqldb:depositpackage data_line:{0}, datalen_line:{1}""".format(data_line, datalen_line)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            if datalen_line != 1:
                resultdata['errormsg'] = 'line_profile table does not exist this user'
                resultdata['Member'] = False

            access_token = data_line.get('access_token')
            # access_token = await self._check_line_access_token_valid(access_token, sub, name)

            command = 'SELECT * from member WHERE linesub = "{0}"'.format(sub)
            datalen, data = await self.getdbdata('select member for line depositpackage', command)

            # access_token = await self._create_line_access_token()

            if datalen == 0 or datalen_line == 0:
                resultdata = {
                    "Member": False,
                    "access_token": access_token,
                    "redirect_uri": env_setting.SD555_LOBBY_URL + '?line_access_token={0}'.format(access_token)
                }

            elif datalen_line == 1 and datalen == 1:
                resultdata = {
                    "Member": True,
                    "access_token": access_token,
                    "redirect_uri": env_setting.SD555_LOBBY_URL + '?line_access_token={0}&package=store'.format(
                        access_token)
                }

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:depositpackage ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:depositpackage ValueError except:{0}'.format(format_exc()))

        return result, resultdata

    async def gamelobby(self, sub, name, picture, email):
        try:
            log_msg = """pg_asqldb:game_lobby sub:{0}, name:{1}, picture:{2}, email:{3}""".format(sub, name, picture,
                                                                                                  email)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT * from line_profile WHERE sub = "{0}"'.format(sub)
            datalen_line, data = await self.getdbdata('select line_profile', command, fetchall=True)

            command = 'SELECT * from member WHERE linesub = "{0}"'.format(sub)
            datalen, data = await self.getdbdata('select member for line gamelobby', command)

            if datalen_line == 1 and datalen == 1:
                access_token = await self._create_line_access_token()
                access_token = await self._check_line_access_token_valid(access_token, sub, name)

                resultdata = {
                    "Member": True,
                    "access_token": access_token,
                    "redirect_uri": env_setting.SD555_LOBBY_URL + '?line_access_token={0}'.format(access_token)
                }

            elif datalen_line == 0:
                resultdata['errormsg'] = 'line_profile table does not exist this user'
                resultdata['Member'] = False
                if datalen == 0:
                    resultdata['errormsg'] = 'line_profile and member table does not exist this user'

            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:game_lobby ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:game_lobby ValueError except:{0}'.format(format_exc()))

        return result, resultdata

    async def help_member_login(self, redis_obj, sub, ip, access_token):
        try:
            i = 0
            while i < 1000:
                logintoken = pg_general.generatorsha256()

                command = '''SELECT * FROM member WHERE logintoken="{}"
                '''.format(logintoken)

                datalen, data = await self.getdbdata(logintoken, command)

                if datalen == 0:
                    i = 1000

            totalresult, clientdata, serverdata = await self.login(redis_obj=redis_obj, fblink=None,
                                                                   defaultchannelindex=None,
                                                                   fbavatarobj=None, logintoken=logintoken,
                                                                   deviceid="", fbid=None, fbtoken=None,
                                                                   fbavatar=None, fbnickname=None, ip=ip,
                                                                   platform=3, devicedescription=None,
                                                                   lobbyserverip=env_setting.SD555_LOBBY_IP,
                                                                   region=None, region_sub=None, city=None,
                                                                   fcmtoken=None, newaccflag=0, connecttype="0",
                                                                   lineaccesstoken=access_token)

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:game_lobby ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:game_lobby Exception except:{0}'.format(format_exc()))

        return totalresult, clientdata, serverdata

    async def check_and_send_sharing_friend_award(self, redis_obj, referral_sub, sub, referral_ip, sub_ip,
                                                  access_token_referral_sub, sub_nickname):
        try:
            log_msg = """pg_asqldb:referralfriend check_and_send_sharing_friend_award referral_sub:{0}, sub:{1}, 
            referral_ip:{2}, sub_ip:{3}, access_token_referral_sub:{4}, sub_nickname:{5}""".format(referral_sub, sub,
                                                                                                   referral_ip, sub_ip,
                                                                                                   access_token_referral_sub,
                                                                                                   sub_nickname)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            command = 'SELECT memberid FROM member WHERE linesub = "{0}"'.format(referral_sub)
            datalen_referral_sub, data_referral_sub = await self.getdbdata(
                'check member table for referral sub', command)

            command = 'SELECT memberid FROM member WHERE linesub = "{0}"'.format(sub)
            datalen_sub, data_sub = await self.getdbdata('check member table for sub', command)

            if datalen_referral_sub == 0:
                totalresult, clientdata, serverdata = await self.help_member_login(redis_obj, referral_sub,
                                                                                   referral_ip,
                                                                                   access_token_referral_sub)
                referral_member_id = clientdata.get('memberid')

            elif datalen_referral_sub == 1:
                referral_member_id = data_referral_sub.get('memberid')

            if datalen_sub == 0:
                sub_nickname = await self._clean_line_nickname_charactor(sub_nickname)

                if sub_nickname == '':
                    sub_nickname = await pg_namesample.makeanewnameforline(self)
                result, resultdata = await self.referralfriendlogin(redis_obj, sub, sub_nickname, "", "", sub_ip)
                command = 'SELECT memberid FROM member WHERE linesub = "{0}"'.format(sub)
                datalen, data = await self.getdbdata('SELECT memberid for send sharing gift', command)

                member_id = data.get('memberid')

            elif datalen_sub == 1:
                member_id = data_sub.get('memberid')

            title = 'ยิ่งชวนเพื่อน ยิ่งได้รางวัลใหญ่'
            content_gem = 'Gem*5555'
            amount_gem = 555500
            promotionid_gem = 67
            content_roomcard = 'Roomcard*10'
            amount_roomcard = 10
            promotionid_roomcard = 71
            uri = "uri"
            dateline = pg_general.datetimetostr_nof(pg_general.getutcnow_datetime() + timedelta(hours=24))
            memberlist = [member_id, referral_member_id]
            main_type = 0
            send_mode = 0

            result_gem, resultdata_gem = await self.send_inbox_to_member(title, content_gem, uri,
                                                                         promotionid_gem, amount_gem, main_type,
                                                                         dateline, memberlist, send_mode)
            result_roomcard, resultdata_roomcard = await self.send_inbox_to_member(title, content_roomcard, uri,
                                                                                   promotionid_roomcard,
                                                                                   amount_roomcard, main_type,
                                                                                   dateline, memberlist,
                                                                                   send_mode)



        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriend ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriend Exception except:{0}'.format(format_exc()))

        return resultdata_gem, resultdata_roomcard

    async def referralfriend(self, redis_obj, referralsub, sub, referraltime, sub_nickname):
        try:
            log_msg = """pg_asqldb:referralfriend referralsub:{0}, sub:{1}, referraltime:{2}, sub_nickname:{3}""".format(
                referralsub, sub, referraltime, sub_nickname)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            referral_ip = "127.0.0.1"
            sub_ip = "127.0.0.1"

            command = 'SELECT recommender, recommend_time, access_token from line_profile WHERE sub="{0}"'.format(
                referralsub)
            datalen, data = await self.getdbdata('select recommender for referralfriend', command)

            recommender = data.get('recommender')
            recommend_time = data.get('recommend_time')
            access_token_referral_sub = data.get('access_token')

            if recommender is not None and recommend_time is not None:
                recommender = recommender.split(',')
                recommend_time = recommend_time.split(',')

                if str(sub) not in recommender:
                    recommender.append(sub)
                    recommend_time.append(referraltime)
                    command = 'UPDATE line_profile set recommender="{0}", recommend_time="{1}" WHERE sub ="{2}"'.format(
                        ','.join(recommender), ','.join(recommend_time), referralsub)
                    updateresult = await self.updatedbdata('update recommender and recommend_time', command)

                    resultdata_gem, resultdata_roomcard = await self.check_and_send_sharing_friend_award(redis_obj,
                                                                                                         referralsub,
                                                                                                         sub,
                                                                                                         referral_ip,
                                                                                                         sub_ip,
                                                                                                         access_token_referral_sub,
                                                                                                         sub_nickname)

                elif str(sub) in recommender:
                    resultdata = {
                        'result': True
                    }
                    result = pg_general.Apiresult.dbnodata
                    return result, resultdata

            else:
                command = 'UPDATE line_profile set recommender="{0}", recommend_time="{1}" WHERE sub="{2}"'.format(sub,
                                                                                                                   referraltime,
                                                                                                                   referralsub)
                updateresult = await self.updatedbdata('update recommender', command)

                resultdata_gem, resultdata_roomcard = await self.check_and_send_sharing_friend_award(redis_obj,
                                                                                                     referralsub, sub,
                                                                                                     referral_ip,
                                                                                                     sub_ip,
                                                                                                     access_token_referral_sub,
                                                                                                     sub_nickname)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_asqldb:referralfriend updateresult:{0}".format(updateresult))
            if updateresult is not True:
                resultdata['result'] = False
                resultdata['errormsg'] = 'update the sub and referraltime to DB error'
                return result, resultdata

            resultdata = {
                'result': True
            }
            result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriend ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriend Exception except:{0}'.format(format_exc()))

        return result, resultdata

    async def gameroomsharing(self, redis_obj, line_uid, room_id, nickname):
        try:
            log_msg = '''pg_asqldb:gameroomsharing line_uid:{0}, room_id:{1}, nickname:{2}'''.format(redis_obj,
                                                                                                     line_uid, room_id,
                                                                                                     nickname)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            sub_ip = "127.0.0.1"

            command = 'SELECT line_access_token, silvercredit from member WHERE linesub = "{0}"'.format(line_uid)
            datalen, data = await self.getdbdata('SELECT access_token for join gameroom', command)

            if datalen != 1:

                if nickname is None:
                    nickname = await pg_namesample.makeanewnameforline(self)
                else:
                    nickname = await self._clean_line_nickname_charactor(nickname)

                    if nickname == '':
                        nickname = await pg_namesample.makeanewnameforline(self)

                result, resultdata = await self.referralfriendlogin(redis_obj, line_uid, nickname, "", "", sub_ip)

            command = 'SELECT line_access_token, silvercredit from member WHERE linesub = "{0}"'.format(line_uid)
            datalen, data = await self.getdbdata('SELECT access_token for join gameroom', command)

            access_token = data.get('line_access_token')
            silvercredit = data.get('silvercredit')

            if silvercredit < 11000:
                result = 4
                resultdata['result'] = False
                resultdata['errormsg'] = 'this member does not have enough money to join room'
                return result, resultdata

            result = pg_general.Apiresult.success
            resultdata = {
                "result": True,
                "access_token": access_token,
            }

            if silvercredit <= 0:
                resultdata["redirect_uri"] = env_setting.SD555_LOBBY_URL + '?line_access_token={0}'.format(access_token)
            else:
                resultdata["redirect_uri"] = env_setting.SD555_LOBBY_URL + '?line_access_token={0}&room_id={1}'.format(
                    access_token, room_id)

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriend ValueError except:{0}'.format(format_exc()))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:referralfriend Exception except:{0}'.format(format_exc()))

        return result, resultdata

    # async def _generate_trade_no(self, memberid, logintoken):
    #     try:
    #         ret = ""
    #         tradenoflag = True
    #         num = random.randint(5, 31)
    #         if tradenoflag:
    #             for i in range(num):
    #                 num = random.randint(0, 9)
    #                 letter = chr(random.randint(97, 122))
    #                 letter_capital = chr(random.randint(65, 90))
    #                 s = str(random.choice([num, letter, letter_capital]))
    #                 ret = ret + s
    #
    #             command = 'SELECT * from flashpay_trade_log WHERE outTradeNo = {0}'.format(ret)
    #             datalen, data = await self.getdbdata(logintoken, command)
    #
    #             if datalen != 0:
    #                 tradenoflag = False
    #
    #     except ValueError:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:_generate_trade_no ValueError except:{0}'.format(format_exc()))
    #     except Exception:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:_generate_trade_no Except except:{0}'.format(format_exc()))
    #     return ret

    # async def webshopping(self, logintoken, memberid, cash, credit, type):
    #     try:
    #         pg_general.writelog(pg_general.PG_LogerLevel.info,
    #                      'pg_asqldb:webshopping logintoken:{0}, memberid:{1}, cash:{2}, credit:{3}, type:{4}'.format(
    #                          logintoken, memberid, cash, credit, type))
    #         result = pg_general.Apiresult.connectdberror
    #         resultdata = {}
    #         data = {}
    #         outTradeNo = await self._generate_trade_no(memberid, logintoken)
    #
    #         data = {
    #             "outUserId": memberid,
    #             "outTradeNo": outTradeNo,
    #             "outTradeTime": pg_general.get_th_datetime(),
    #             "paymentAmount": cash * 100,
    #             "cur": "THB",
    #             "subject": "SD555-APP-FlashPay",
    #             "notifyUrl":"",
    #             "returnUrl":""
    #         }
    #
    #     except ValueError:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:webshopping ValueError except:{0}'.format(format_exc()))
    #     except Exception:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:webshopping Except except:{0}'.format(format_exc()))
    #     return result, resultdata
    #
    # async def flashpayreturn(self, object_id, status):
    #     try:
    #         pg_general.writelog(pg_general.PG_LogerLevel.info,
    #                             'pg_asqldb:flashpayreturn object_id:{0}, status:{1}'.format(object_id, status))
    #         result = pg_general.Apiresult.connectdberror
    #         resultdata = {}
    #         logintoken = 'flashpay ' + str(object_id)
    #
    #         command = 'UPDATE flashpay_trade_log set result = {0} WHERE out_trade_no = {1}'.format(status, object_id)
    #         updateresult = await self.updatedbdata(logintoken, command)
    #
    #     except ValueError:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:flashpayreturn ValueError except:{0}'.format(format_exc()))
    #     except Exception:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:flashpayreturn Except except:{0}'.format(format_exc()))
    #     return result, resultdata
    #
    # async def flashpaynotify(self, out_trade_no, trade_no, trade_status, trade_time, payment_amount, cur, complete_time):
    #     try:
    #         pg_general.writelog(pg_general.PG_LogerLevel.info,
    #                             'pg_asqldb:flashpaynotify out_trade_no:{0}, trade_no:{1}, trade_status:{2}, trade_time:{3}, payment_amount:{4}, cur:{5}, complete_time:{6}'.format(
    #                                 out_trade_no, trade_no, trade_status, trade_time, payment_amount, cur, complete_time))
    #         logintoken_insert = 'flashpay_insert ' + str(out_trade_no)
    #         logintoken_select = 'flashpay_select ' + str(out_trade_no)
    #
    #         command = 'SELECT mode, credit, memberid from flashpay_trade_log WHERE out_trade_no = "{0}"'.format(out_trade_no)
    #         datalen, data = await self.getdbdata(logintoken_select, command)
    #         mode = data.get('mode')
    #         credit = data.get('credit')
    #         memberid = data.get('memberid')
    #
    #         insertstr = "memberid, out_trade_no, trade_no, out_trade_time, cash, mode, credit, result"
    #         insertvalue = '{0}, "{1}", "{2}", {3}, {4}, {5}, {6}), {7}'.format(memberid, out_trade_no, trade_no,
    #                                                         trade_time, payment_amount, mode, credit, trade_status)
    #         if complete_time is not None:
    #             insertstr = insertstr + ', complete_time'
    #             insertvalue = insertvalue + ', {0}'.format(complete_time)
    #
    #         command = """insert into flashpay_trade_log ({0}) values({1})""".format(insertstr, insertvalue)
    #         updateresult = await self.updatedbdata(logintoken_insert, command)
    #
    #     except ValueError:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:flashpaynotify ValueError except:{0}'.format(format_exc()))
    #     except Exception:
    #         pg_general.writelog(pg_general.PG_LogerLevel.error,
    #                             'pg_asqldb:flashpaynotify Except except:{0}'.format(format_exc()))
    #     return result, resultdata

    async def sendgiftemailsms(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:sendgiftemailsms memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 撈此玩家 資料
            command = 'select email, emailbindstatus, emailvalidatecode, emailvaliddatetime from member where memberid="{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get member info error')

            emailbindstatus = data.get('emailbindstatus')
            emailvalidatecode = data.get('emailvalidatecode')
            emailvaliddatetime = data.get('emailvaliddatetime')
            email = data.get('email')

            if emailbindstatus != 2:  # 未完成綁定信箱
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 1
                }
                return result, resultdata

            nowutcdatetime = pg_general.strtodatetime(pg_general.getutcnow())
            overseconds = pg_general.converttype((nowutcdatetime - emailvaliddatetime).total_seconds(), int)
            if overseconds < 60:  # 一分鐘未到
                result = pg_general.Apiresult.success
                resultdata = {
                    "result": 2
                }
                return result, resultdata

            validatecode = str(random.randint(100000, 999999))
            # 發送 code to email
            await pg_sms.sendemail(email, validatecode)

            # 紀錄 db
            command = 'update member set emailvalidatecode="{0}",emailvaliddatetime="{1}" where memberid = "{2}"'.format(
                validatecode, nowutcdatetime, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            # insert into emailvalidatelog
            command = 'insert into emailvalidatelog (logtime,email,memberid,validatecode) values("{0}","{1}","{2}","{3}")'.format(
                nowutcdatetime, email, memberid, validatecode)
            insertresult = await self.updatedbdata(logintoken, command)

            resultdata = {
                "result": 0
            }
            result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgiftemailsms ValueError except:{0}'.format(format_exc()))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendgiftemailsms Except except:{0}'.format(format_exc()))
        return result, resultdata

    async def getspecialaction(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getspecialaction memberid:{0},logintoken:{1}'.format(memberid, logintoken))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'select specialactionurlnew from setting2'
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                result = pg_general.Apiresult.success

                resultdata = {
                    "specialactionurlnew": data.get('specialactionurlnew')
                }

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getspecialaction Exception except:{0}'.format(e))


        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getspecialaction return, result:{0},resultdata:{1}'.format(result,
                                                                                                      resultdata))
            return result, resultdata

    async def getfirstbuymallinfo(self, logintoken, memberid):  # 取得首購商城資料
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getfirstbuymallinfo logintoken:{0},memberid:{1}'.format(logintoken,
                                                                                                   memberid))
            clientdata = {}
            firstbuycountdownsec = 0
            firstbuytotalpercent = 0
            # get setting2.firstbuycountdownsec , setting2.firstbuytotalpercent
            command = 'select firstbuycountdownsec,firstbuytotalpercent from setting2'
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:
                firstbuycountdownsec = data.get('firstbuycountdownsec')
                firstbuytotalpercent = data.get('firstbuytotalpercent')

            firstbuymallinfo = []
            command = 'select * from mallinfofirstbuy order by showindex'
            datalen, data = await self.getdbdata(logintoken, command, True)
            if datalen > 0:
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
                                'pg_asqldb:getfirstbuymallinfo logintoken:{0},memberid:{1}'.format(logintoken,
                                                                                                   memberid))

        return clientdata

    async def normalmall(self, logintoken, memberid, shopid, mode, transaction_id):  # 正常商城
        """

        1. 從 mallinfo 資料表拿資料，並整理
        2. 從 member 資料表拿資料
        3. 更新 member 資料表內的銀幣 or 房卡 or 點數 (根據 mode)

        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:normalmall logintoken:{0},memberid:{1},shopid:{2}:mode:{3}'.format(
                                    logintoken, memberid, shopid, mode))
            ret_data = {
                "credit": 0,
                "buycredit": 0,
                "content": {}
            }
            result = pg_general.Apiresult.connectdberror

            getmall_result, clientdata = await self.getmallinfo(logintoken, memberid, mode)
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

            # 根據 mode 給予不同的欄位選擇，else 飾金爽專案原本的欄位
            if mode == 2:
                sql_column_one = 'silvercredit'
                sql_column_two = 'silvercredit'
                purpose = 2
            elif mode == 3:
                sql_column_one = 'roomcard'
                sql_column_two = 'roomcard'
                purpose = 3
            else:
                sql_column_one = 'credit'
                sql_column_two = 'point'
                purpose = 4

            # 根據 mode 取得銀幣 or 房卡再命名為 credit
            command = '''
            select member.card, member.point, member.{0} AS credit
            from member where member.memberid="{1}"
            '''.format(sql_column_one, memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member levelinfo is wrong')

            aftercredit = data.get('credit')
            afterpoint = data.get('point')
            card = data.get('card')

            if mode == 2:
                buybefore = data.get('silvercredit')
            elif mode == 3:
                buybefore = data.get('roomcard')
            else:
                buybefore = data.get('credit')

            # update member credit
            command = '''
            update member set {0}={0}+"{1}",isfirstbuy=0 where memberid="{2}"
            '''.format(sql_column_two, buycredit, memberid)
            update_result = await self.updatedbdata(logintoken, command)
            if update_result == False:
                raise ValueError('update member credit error')

            transtime = pg_general.getutcnow_datetime()
            command = 'INSERT INTO `slot-game`.member_wallet_log (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time) values("{0}", "{1}", {2}, {3}, "{4}", {5}, {6}, "{7}", "{8}")' \
                .format(env_setting.PS_HOST_NAME_S, memberid, purpose, 3, transaction_id, buycredit, buybefore, "API",
                        transtime)
            insertresult, index = await self.slot_game_db.insertdbdata('shopping insert_member_wallet_log', command)

            # prepare return data
            result = pg_general.Apiresult.success
            ret_data = {
                "credit": aftercredit,
                "buycredit": buycredit,
                "content": {},
                "cash": cash,
                "card": card
            }
        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:normalmall ValueError:{0},memberid:{1},shopid:{2}'.format(format_exc(),
                                                                                                     memberid, shopid))
        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:normalmall except:{0},memberid:{1},shopid:{2}'.format(format_exc(), memberid,
                                                                                                 shopid))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:normalmall return result:{0},ret_data:{1}'.format(result, ret_data))
            return result, ret_data

    async def firstbuymall(self, logintoken, memberid, shopid):  # 首購商城
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:firstbuymall logintoken:{0},memberid:{1},shopid:{2}'.format(logintoken,
                                                                                                       memberid,
                                                                                                       shopid))
            ret_data = {
                "credit": 0,
                "buycredit": 0,
                "content": {}
            }
            result = pg_general.Apiresult.connectdberror

            command = 'select * from mallinfofirstbuy where shopid ="{0}"'.format(shopid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                raise ValueError('get member credit is wrong')

            buycredit = data.get('point')
            cash = data.get('cash')

            # get member credit,secretmallid , secretoffermall.buycredit
            command = 'select member.card,member.credit from member ' \
                      ' where member.memberid="{0}"'.format(memberid)

            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member credit is wrong')

            aftercredit = data.get('credit')
            card = data.get('card')

            # update member.credit
            command = 'update member set point = point+ "{0}",isfirstbuy=0 where memberid="{1}"'.format(buycredit,
                                                                                                        memberid)
            updateresult = await self.updatedbdata(logintoken, command)

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
                                'pg_asqldb:firstbuymall ValueError:{0},memberid:{1},shopid:{2}'.format(e, memberid,
                                                                                                       shopid))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:firstbuymall except:{0},memberid:{1},shopid:{2}'.format(e, memberid, shopid))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:firstbuymall return result:{0},ret_data:{1}'.format(result, ret_data))
            return result, ret_data

    async def secretoffermall(self, logintoken, memberid, shopid):  # secret offer 商城
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:secretoffermall logintoken:{0},memberid:{1},shopid:{2}'.format(logintoken,
                                                                                                          memberid,
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

            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('get member credit is wrong')

            buycredit = data.get('buypoint')
            aftercredit = data.get('credit')
            cash = data.get('cost')
            card = data.get('card')

            # update member.credit
            command = 'update member set point = point+ "{0}",isfirstbuy=0 where memberid="{1}"'.format(buycredit,
                                                                                                        memberid)
            updateresult = await self.updatedbdata(logintoken, command)

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
                                'pg_asqldb:secretoffermall ValueError:{0},memberid:{1},shopid:{2}'.format(e, memberid,
                                                                                                          shopid))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:secretoffermall except:{0},memberid:{1},shopid:{2}'.format(e, memberid,
                                                                                                      shopid))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:secretoffermall return result:{0},ret_data:{1}'.format(result, ret_data))
            return result, ret_data

    async def write_mall_history(self, logintoken, memberid, shopid, price, transaction_id, malltype, platform,
                                 statuscode, receipt_data, currencycode, response_data=None):
        try:
            buytime = datetime.utcnow()
            command = 'insert into mallhistory (shopid,buytime,cost,transactionid,malltype,memberid,logintoken,platform,statuscode,receipt,currencycode,response_data)' \
                      'values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}")'.format(shopid,
                                                                                                                 buytime,
                                                                                                                 price,
                                                                                                                 transaction_id,
                                                                                                                 malltype,
                                                                                                                 memberid,
                                                                                                                 logintoken,
                                                                                                                 platform,
                                                                                                                 statuscode,
                                                                                                                 receipt_data,
                                                                                                                 currencycode,
                                                                                                                 response_data)
            result_insert, index = await self.insertdbdata(logintoken, command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:write_mall_history exception:{0}'.format(e))

    async def getbanplayer(self, memberlist):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getbanplayer member_id:{0}'.format(memberlist))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            error_list = []
            data_list = []
            logintoken = 0

            if memberlist is not None:
                for member_id in memberlist:
                    command = 'SELECT memberid,account_type FROM member WHERE memberid = {0}'.format(member_id)
                    datalen, data = await self.getdbdata(logintoken, command)

                    if data is None:
                        error_list.append(member_id)
                    else:
                        account_type = data.get('account_type')
                        data_list.append(data)

                result = pg_general.Apiresult.success
                resultdata = {
                    "data": data_list,
                    "error_list": error_list
                }

            else:

                command = 'SELECT memberid,account_type FROM member WHERE account_type = 3'
                datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

                result = pg_general.Apiresult.success
                resultdata = {
                    "data": data
                }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getbanplayer ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getbanplayer except:{0}'.format(e))

        return result, resultdata

    async def banplayer_operate(self, memberlist, account_type):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:banplayer_operate member_id:{0}, account_type:{1}'.format(memberlist,
                                                                                                     account_type))

            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            error_list = []
            logintoken = 0
            for memberid in memberlist:
                command = 'update member set account_type = {0} WHERE memberid = {1}'.format(account_type, memberid)
                updateresult = await self.updatedbdata(logintoken, command)

                command = 'select account_type from member WHERE memberid = {0}'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command)

                account_ban = data.get('account_type')

                if account_ban != account_type:
                    error_list.append(memberid)

            result = pg_general.Apiresult.success
            resultdata = {
                "error_list": error_list
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:banplayer_operate ValueError:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:banplayer_operate except:{0}'.format(format_exc()))

        return result, resultdata

    async def getcreditcardinfo(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getcreditcardinfo')
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            logintoken = 0

            command = 'SELECT * FROM creditcardinfo order by cashamount desc'
            datalen, data = await self.getdbdata(logintoken, command, fetchall=True)

            result = pg_general.Apiresult.success
            resultdata = {
                "data": data
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getcreditcardinfo ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getcreditcardinfo except:{0}'.format(e))

        return result, resultdata

    async def newcreditcardinfo(self, itemcode, cashamount, pointamount, currency, productname):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:newcreditcardinfo itemcode:{0} cashamount:{1}, pointamount:{2}, currency:{3}, productname:{4}'.format(
                                    itemcode, cashamount, pointamount, currency, productname))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            logintoken = 0

            itemdesc = str(cashamount) + ' -> ' + str(pointamount)

            command = 'insert into creditcardinfo (itemcode, itemdesc, cashamount, pointamount, currency, productname) values("{0}", "{1}", "{2}", "{3}", "{4}", "{5}")'.format(
                itemcode, itemdesc, cashamount, pointamount, currency, productname)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:newcreditcardinfo log 222')
            insertresult, rowindex = await self.insertdbdata(logintoken, command)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:newcreditcardinfo insertresult={0}, rowindex={1}'.format(insertresult,
                                                                                                    rowindex))

            result = pg_general.Apiresult.success
            resultdata = {
                "result": pg_general.Apiresult.success
            }

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:creditcardinfo_operate except:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:creditcardinfo_operate except:{0}'.format(e))
        return result, resultdata

    async def delcreditcardinfo(self, itemcode):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:delcreditcardinfo itemcode:{0}'.format(itemcode))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}
            logintoken = 0

            command = 'DELETE FROM creditcardinfo WHERE itemcode={0}'.format(itemcode)

            deleteresult = await self.updatedbdata(logintoken, command)
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:delcreditcardinfo deleteresult={0}'.format(deleteresult))

            result = pg_general.Apiresult.success
            resultdata = {
                "result": pg_general.Apiresult.success
            }
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:delcreditcardinfo result={0}, resultdata={1}'.format(result, resultdata))

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:delcreditcardinfo ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:delcreditcardinfo except:{0}'.format(e))

        return result, resultdata

    async def servicetouser(self, redis_obj, memberid, content):
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
            if ttltime >= 10:  # 代表在線上 傳給 lobby server 直接傳給 member 將資料帶回上層
                # 抓 user ip
                userip = await redis_obj.get_value('online_{0}'.format(memberid))
                memberlogintoken = await redis_obj.get_value(memberid)
                resultdata = {
                    "result": 0,
                    "userip": userip,
                    "logintoken": memberlogintoken,
                    "msg": {
                        "commandid": 3000012,
                        "data": {
                            "time": nowtwtime,
                            "contentlist": [content]
                        }
                    }
                }


            else:  # 不在線上 存到 redis service_(memberid) lpush
                await redis_obj.lpush('servicechat_{0}'.format(memberid), content)
                await redis_obj.expire('servicechat_{0}'.format(memberid), 604800)  # 七天過期
                resultdata = {'result': 1}  # 代表 save to redis

            # save to chatroom_service
            command = 'update chatroom_service set flag = "1" ,content = json_array_append(content, "$",json_object("time","{0}","type",0,"content","{1}")) ' \
                      'where memberid = "{2}"'.format(nowutctime, content, memberid)

            updateresult = await self.updatedbdata('insert into chatroom_service', command)

            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:servicetouser except:{0}'.format(e))

        return result, resultdata

    async def add_action(self, action_number, list_type, list_pos, list_name,
                         button_url, content_pos, content_type, content, click_url,
                         size, start_time, end_time):
        try:
            log_msg = 'pg_asqldb:add_action actionnumber:{}, listtype:{}, listpos:{}, ' \
                      'listname:{}, buttonurl:{}, contentpos:{}, contenttype:{}, ' \
                      'content:{}, clickurl:{}, size:{}, starttime:{}, endtime:{}'.format(
                action_number, list_type, list_pos, list_name,
                button_url, content_pos, content_type, content, click_url,
                size, start_time, end_time)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            insertkey = 'actionnumber, listtype, listpos, listname, ' \
                        'buttonurl, newflag, contentpos, contenttype, content, ' \
                        'clickurl, size, starttime, endtime'

            insertvalue = '{}, {}, {}, "{}", "{}", 1, {}, {}, "{}", "{}", "{}", "{}", "{}"'.format(
                action_number, list_type, list_pos, list_name,
                button_url, content_pos, content_type, content, click_url,
                size, start_time, end_time)

            command = 'INSERT INTO action({}) VALUE({})'.format(
                insertkey,
                insertvalue)

            insertresult, index = await self.insertdbdata('add_action', command)

            if insertresult:
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.connectdberror

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:add_action except:{0}'.format(format_exc()))

        return result, resultdata

    async def get_action(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:get_action')

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'SELECT * FROM action'
            datalen, data = await self.getdbdata('get action', command, fetchall=True)

            for dc in data:  # datetime 轉 str
                s = dc['starttime']
                e = dc['endtime']

                if not isinstance(s, str):
                    dc['starttime'] = pg_general.datetime_to_str(dc['starttime'])

                if not isinstance(e, str):
                    dc['endtime'] = pg_general.datetime_to_str(dc['endtime'])

            result = pg_general.Apiresult.success
            resultdata['data'] = data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'get_action:get_action except:{0}'.format(format_exc()))

        return result, resultdata

    async def delete_action(self, action_index):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:delete_action')

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            command = 'DELETE FROM action WHERE actionindex={}'.format(action_index)
            delete_result = await self.updatedbdata('delte action', command)

            if delete_result:
                result = pg_general.Apiresult.success
            else:
                result = pg_general.Apiresult.connectdberror

        except:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'get_action:delete_action except:{0}'.format(format_exc()))

        return result, resultdata

    async def _get_member_items_dc(self, item, member_ls, club_id):
        """
        1. 根據 club_id 是否為空決定去 memberclub 還是 member 資料表撈玩家的資料
        2. 檢查欲查詢資料數量是否與結果一致
        2.1 不一致就回傳空 dict 作為後續判斷使用
        3. 將資料轉換成 dict

        examples:
            {
                "member id": {
                    'after_amount': 對應品項數量
                }
            }
        """
        where_search_command = ', '.join(str(i) for i in member_ls)

        if club_id == '':
            select_command = '''
            SELECT memberid, {} FROM member WHERE memberid IN ({})
            '''.format(item, where_search_command)
        else:
            select_command = '''
            SELECT memberid, {} FROM memberclub WHERE memberid IN ({}) and clubid="{}"
            '''.format(item, where_search_command, club_id)

        datalen, data = await self.getdbdata('member_item_operate: get_member_items_dc',
                                             select_command, fetchall=True)

        if datalen != len(member_ls):
            return {}

        output_dc = {}

        for dc in data:
            output_dc[dc['memberid']] = {
                'before_amount': dc[item],
                'after_amount': dc[item]
            }

        return output_dc

    async def _update_member_item_and_write_log(self, member_item_dc, item, club_id, operate):
        """

        1. 根據 club_id 是否維空決定去 memberclub 還是 member 資料表修改玩家的資料
        """
        error_ls = []

        for member_id, dc in member_item_dc.items():
            if club_id == "":
                command = '''
                    UPDATE member SET {}={} WHERE memberid={}
                '''.format(item, dc['after_amount'], member_id)
            else:
                command = '''
                    UPDATE memberclub SET {}={} WHERE memberid={} AND clubid="{}"
                '''.format(item, dc['after_amount'], member_id, club_id)

            updateresult = await self.updatedbdata('member_item_operate update_member_item'
                                                   , command)

            if updateresult != True:
                error_ls.append(member_id)

            action = 5 if operate == 'send' else 6
            if item == 'credit':
                purpose = 4
            elif item == 'silvercredit':
                purpose = 2
            else:
                purpose = 3

            transtime = pg_general.getutcnow_datetime()
            command = 'INSERT INTO `slot-game`.member_wallet_log (host_id, member_id, purpose, action, txn_id, amount, balance, note, occur_time) values("{0}", "{1}", {2}, {3}, "{4}", {5}, {6}, "{7}", "{8}")' \
                .format(env_setting.PS_HOST_NAME_S, member_id, purpose, action, "0", abs(dc['amount']),
                        dc['before_amount'], "API", transtime)
            insertresult, index = await self.slot_game_db.insertdbdata('member_item_operate insert_member_wallet_log',
                                                                       command)

        return error_ls

    async def member_item_operate(self, operate, item, amount, member_ls, club_id):
        """發送 / 收回玩家金幣 or 銀幣 or 房卡

        1. 取得要查詢的玩家資料
        1.1 若資料數量有誤則 raise 錯誤
        2. 計算處理後玩家道具擁有數量，若是收回時數量不對(<0) 回傳錯誤
        3. 將計算後的資料寫入資料表
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:member_item_operate operate:{}, item:{}, amount:{}, member_ls:{}'.format(
                                    operate, item, amount, member_ls))

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            member_item_dc = await self._get_member_items_dc(item, member_ls, club_id)

            if len(member_item_dc) == 0:
                resultdata['errormsg'] = 'select data error'
                raise ValueError('member_item_operate: select data error')

            do_amount = amount if operate == 'send' else -amount

            for member_id in member_ls:
                member_item_dc[member_id]['after_amount'] += do_amount
                member_item_dc[member_id]['amount'] = do_amount

                if member_item_dc[member_id]['after_amount'] < 0:
                    error_msg = 'member_id:{} {} is less than {}'.format(
                        member_id, item, amount)
                    resultdata = {'errormsg': error_msg}

                    raise ValueError('member_item_operate' + error_msg)

            error_ls = await self._update_member_item_and_write_log(member_item_dc, item, club_id, operate)

            resultdata['error_list'] = error_ls
            result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:member_item_operate except:{0}'.format(format_exc()))

        return result, resultdata

    async def _get_member_sending_list(self, member_ls):
        """取得要傳送的成員清單

        若沒有指定要傳給誰就是傳給所有玩家
        """
        if len(member_ls) == 0:
            command = 'SELECT memberid FROM member'
            datalen, data = await self.getdbdata(
                'send_inbox_to_member: select all member',
                command, fetchall=True)
            cur_member_ls = [d.get('memberid') for d in data]
        else:
            cur_member_ls = member_ls

        return cur_member_ls

    async def _get_club_member_sending_list(self, club_ls):
        """取得要傳送的成員清單

        若沒有指定要傳給誰就是傳給所有玩家
        """

        if len(club_ls) == 0:
            command = 'SELECT memberid FROM memberclub'
            datalen, data = await self.getdbdata(
                'send_inbox_to_member: select all club member',
                command, fetchall=True)
            cur_member_ls = [d.get('memberid') for d in data]
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'send_inbox_to_member cur_member_ls:{}, type cur_member_ls:{}'.format(cur_member_ls,
                                                                                                      type(
                                                                                                          cur_member_ls)))
        else:
            cur_member_ls = []
            for club_member in club_ls:
                command = 'SELECT memberid FROM memberclub WHERE clubid = {}'.format(club_member)
                datalen, data = await self.getdbdata('send_inbox_to_member: select club member', command, fetchall=True)

                for d in data:
                    member_id = d.get('memberid')
                    cur_member_ls.append(member_id)
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                    'send_inbox_to_member cur_member_ls:{}, type cur_member_ls:{}'.format(cur_member_ls,
                                                                                                          type(
                                                                                                              cur_member_ls)))

        return cur_member_ls

    async def send_inbox_to_member(self, title, content, uri, promotion_id,
                                   amount, main_type, dateline, sending_ls, mode):
        """寄信（獎勵） 給清單中的玩家

        Args:
            title (str): 信件標題
            content (str): 信件內容
            uri (str): 信件圖是 uri
            promotion_id (str):
            amount (int): 給予的獎勵額
            main_type (str): 信件小圖示
            dateline (datetime): 獎勵領取的到期日
            mode (int): 寄件對象累別 0:寄給玩家 1:寄給俱樂部
            sending_ls (list): 寄信的列表，當type = 0時是member_id_list, type = 1時是club_id_list
        """
        try:
            log_msg = 'pg_asqldb:send_inbox_to_member title:{}, content:{}, ' \
                      'uri:{}, promotion_id:{}, amount:{}, main_type:{}, dateline:{},' \
                      ' sending_ls:{}, mode:{}'.format(title, content, uri, promotion_id,
                                                       amount, main_type, dateline, sending_ls, mode)
            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {'error_list': []}

            if mode == 0:
                cur_member_ls = await self._get_member_sending_list(sending_ls)
            elif mode == 1:
                cur_member_ls = await self._get_club_member_sending_list(sending_ls)

            insertkey = 'memberid, inboxuri, mailtype, inboxtitle, inboxcontent, ' \
                        'receivestate, promotionid, credit_award, dateline'

            for member_id in cur_member_ls:
                insertvalue = '{}, "{}", "{}", "{}", "{}", "1", "{}", {}, "{}"'.format(
                    member_id, uri, main_type, title, content, promotion_id, amount, dateline)

                command = 'INSERT INTO memberinbox({}) VALUE({})'.format(insertkey,
                                                                         insertvalue)

                insertresult, index = await self.insertdbdata('send_inbox_to_member: {}'.format(member_id), command)

                if insertresult != True:
                    resultdata['error_list'].append(member_id)

            result = pg_general.Apiresult.success

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:send_inbox_to_member except:{0}'.format(format_exc()))

        return result, resultdata

    async def search_inbox(self, start_datetime, end_datetime, club_type, club, member_id):
        """查詢玩家的信件

        查出指定時間範圍內的信件

        1. 根據 club_type 查詢特定的人
            club_type=0: 無俱樂部的人
            club_type=1: 全部玩家(含俱樂部)
            club_type=2: 俱樂部名稱
            club_type=3: 俱樂部 I D

        Args:
            start_datetime: (str): 開始時間，格式 2022-06-01 12:00:00
            end_datetime: (str): 結束時間，格式 2022-06-01 12:00:00
            club_type (int): 查詢方式
            club (str): 俱樂部 ID 或俱樂部名稱
            member_id (int): 玩家 ID
        """
        try:
            log_msg = '''pg_asqldb:search_inbox
            start_datetime:{}, end_datetime:{}, club_type:{}, club:{}, member_id:{}
            '''.format(start_datetime, end_datetime, club_type, club, member_id)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)

            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            if club_type == 2 and club:
                club_where_search = 'AND cb.name="{}"'.format(club)
            elif club_type == 3 and club:
                club_where_search = 'AND mc.clubid="{}"'.format(club)
            else:
                club_where_search = ''

            member_id_where_search = 'AND mi.memberid={}'.format(member_id) if member_id else ''

            command = '''
                SELECT mi.memberid, mi.inboxtitle, mi.inboxcontent, mi.receivestate,
                mi.inboxuri, mi.mailtype, mi.sendtime, mc.clubid, mi.promotionid, mi.credit_award
                FROM memberinbox AS mi
                LEFT JOIN memberclub AS mc ON mi.memberid=mc.memberid
                LEFT JOIN club AS cb ON cb.clubid=mc.clubid
                WHERE sendtime>="{}" AND sendtime<="{}" {} {}
            '''.format(start_datetime, end_datetime, member_id_where_search, club_where_search)

            search_result_ls = []

            if club_type != 0:
                datalen, data = await self.getdbdata('search_inbox', command, fetchall=True)

                if datalen != 0:
                    search_result_ls += data

            else:  # 撈所有沒有參加俱樂部的人
                command = '''
                    SELECT mi.memberid, mi.inboxtitle, mi.inboxcontent, mi.receivestate,
                    mi.inboxuri, mi.mailtype, mi.sendtime, mi.promotionid, mi.credit_award
                    FROM memberinbox AS mi
                    WHERE mi.memberid NOT IN (SELECT memberid FROM memberclub) {}
                        AND sendtime>="{}" AND sendtime<="{}"
                '''.format(member_id_where_search, start_datetime, end_datetime)

                no_club_datalen, no_club_data = await self.getdbdata('search_inbox',
                                                                     command, fetchall=True)
                if no_club_datalen != 0:
                    search_result_ls += no_club_data

            now_datetime = pg_general.getutcnow_datetime()

            for dc in search_result_ls:
                sendtime = dc['sendtime']
                # 先比完時間再轉成字串
                dc['sendstatus'] = sendtime <= now_datetime
                dc['sendtime'] = pg_general.datetime_to_str(sendtime)

                # 判斷此封信件送的銀幣(寶石)、房卡數量
                promotion_id = dc['promotionid']
                credit_award = dc['credit_award']

                dc['gem'] = 0
                dc['roomcard'] = 0

                if promotion_id == 67:  # 銀幣
                    dc['gem'] = credit_award
                elif promotion_id == 71:  # 房卡
                    dc['roomcard'] = credit_award

                del dc['promotionid']
                del dc['credit_award']

            result = pg_general.Apiresult.success
            resultdata['data'] = search_result_ls

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:search_inbox except:{0}'.format(format_exc()))

        return result, resultdata

    async def getuncompletedgame(self, seatid):
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
                                        'pg_asqldb:getuncompletedgame exception 1: {0},errcount:{1},seatid:{2}'.format(
                                            e, errcount, seatid))

            if errcount >= 3:
                result = False

                return result, clientdata
            if data1 != {}:  # 代表有位完成遊戲
                clientdata = {"result": True}

            result = True



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getuncompletedgame exception 2: {0}'.format(e))

        return result, clientdata

    async def backtohall(self, app, redis_obj, logintoken, memberid, gamelogdataindex, seat_data):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:backtohall memberid:{0},logintoken:{1},gamelogdataindex:{2},seat_data:{3}'.format(
                                    memberid, logintoken, gamelogdataindex, seat_data))
            result = pg_general.Apiresult.connectdberror
            resultdata = {"result": 0}

            nowutcdatetime = pg_general.getutcnow_datetime()
            command = 'update membergamelog set leavetime="{0}" where memberid="{1}" and logintoken="{2}" and membergameindex ="{3}"'.format(
                nowutcdatetime, memberid, logintoken, gamelogdataindex)
            updateresult = await self.updatedbdata(logintoken, command)

            # seatmemberid = '{}_{}_{}'.format(seatname, gameid, joinseatstatus.get('seatnum'))

            keepseatsecondslist = [{"keepseatseconds": item.get("keepseatseconds")} for item in app['cardinfo']]

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
                await self.call_gameapi_transferAllCreditToHost(logintoken, memberid, hostid, 0)
                # del member fish redis key
                tempgameid = valuelist[1].split('@')[0]
                await redis_obj.del_key('fish_g_{}_{}'.format(tempgameid, memberid))
                # del dirtyfish key
                await redis_obj.hdel('dirtyfish', 'g_{}_{}'.format(tempgameid, memberid))
                # notice credit and silvercredit
                asyncio.ensure_future(self.noticeusercredit(redis_obj, memberid, logintoken))
                result = pg_general.Apiresult.success
                return result, resultdata
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
                return result, resultdata

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
            if uncompletedresult == True and uncomplietedclientdata.get(
                    'result') == True:  # 有未完成的遊戲 設定 status = 3 , dateline + 30 天
                newdateline_str = pg_general.datetime_to_str(tempnowutcdatetime + timedelta(days=30))
                await redis_obj.hmset(seatkey, {"dateline": newdateline_str, "status": 3})
                # set uncompletegame
                await redis_obj.hset('uncompletedgame', seatkey, 1)
                await redis_obj.set_value(tempuserseatkey, 3, 2592000)  # 位完成遊戲 保留 30 天
            else:  # 沒有未完成的遊戲
                if tempkeepseconds > 0 and tempdirtyseattype != 't':  # 要保留,  turtorial 強制不保留
                    newdateline_str = pg_general.datetime_to_str(
                        tempnowutcdatetime + timedelta(seconds=tempkeepseconds))
                    await redis_obj.hmset(seatkey, {"dateline": newdateline_str, "status": 2})
                    await redis_obj.set_value(tempuserseatkey, 2, tempkeepseconds)
                    await redis_obj.hdel('uncompletedgame', seatkey)
                else:  # 不保留
                    # 清除 dirtyseat
                    await redis_obj.hdel('dirtyseat', '{}_{}_{}'.format(tempdirtyseattype, tempgameid, tempseatnum))
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

        return result, resultdata

    async def joingameseat(self, redis_obj, logintoken, memberid, jsoncontent):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joingameseat memberid:{0},param:{1}'.format(memberid, jsoncontent))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            gameid = jsoncontent.get('gameid')
            gametype = jsoncontent.get('gametype')  # 0 : gold hall , 1: silver hall 2:
            seatnum = jsoncontent.get('seatnum')

            joinseatstatus = {
                "isjoin": False,
                "seatnum": 0

            }

            # check 教學模式資料正確性
            if gametype == 2 and seatnum != 0:
                return result, resultdata

            # get member info
            command = 'select memberid,tutorialbetfinish,card,avatar from member where memberid = "{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                return result, resultdata

            # 使用過 教學 強制 錯誤
            tutorialbetfinish = data.get('tutorialbetfinish')
            if gametype == 2 and tutorialbetfinish != 0:
                return result, resultdata

            card = data.get('card')
            avatar = data.get('avatar')

            # 找出機台數量
            command = 'select seatsamount,seatsamount_s,seatsamount_t from game where gameid="{0}"'.format(gameid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                return result, resultdata

            seatsamount = data.get('seatsamount')
            seatsamount_s = data.get('seatsamount_s')
            seatsamount_t = data.get('seatsamount_t')

            nowutctimestr = pg_general.datetime_to_str(pg_general.getutcnow_datetime())

            # 找出 自己的機台
            if gametype == 0:  # gold
                seatlist = await redis_obj.get_all_keys('seatsgold_{}@*_{}'.format(gameid, memberid))
                temmpseatkey = 'goldseats'
            elif gametype == 1:  # silver
                seatlist = await redis_obj.get_all_keys('seatssilver_{}@*_{}'.format(gameid, memberid))
                temmpseatkey = 'silverseats'
            elif gametype == 2:  # 教學模式
                seatlist = await redis_obj.get_all_keys('seatstutorial_{}@*_{}'.format(gameid, memberid))
                temmpseatkey = 'tutorialseats'
            else:
                return result, resultdata

            if seatlist is not None and seatlist != []:  # 有找到機台
                # 找出機台號碼
                for item in seatlist:
                    reservedseatnum = pg_general.converttype(item.split('@')[1].split('_')[0], int)
                    selfseatvalue = await redis_obj.get_value(item)
                    selfseatvalue = pg_general.converttype(selfseatvalue, int)
                    if selfseatvalue == 3:  # 有未完成遊戲 強制選此台
                        seatnum = reservedseatnum
                        break
                    elif selfseatvalue == 2:  # 保留中
                        if reservedseatnum != seatnum or seatnum == 0:  # 刪除不同機台編號的保留資訊,隨機選台刪除所有自己站位機台
                            await redis_obj.del_key(item)
                            await redis_obj.hmset('{}_{}@{}'.format(temmpseatkey, gameid, reservedseatnum),
                                                  {"dateline": nowutctimestr})  # 設定現在時間讓 control 回收
                        else:
                            await redis_obj.expire(item, 30)  # 如果進去保留的機台 讓他時間維持 30 秒 ttl
                    elif selfseatvalue == 1:  # playing
                        if reservedseatnum != seatnum or seatnum == 0:  # 刪除不同機台編號的保留資訊,隨機選台刪除所有自己站位機台
                            await redis_obj.del_key(item)
                            await redis_obj.hmset('{}_{}@{}'.format(temmpseatkey, gameid, reservedseatnum),
                                                  {"dateline": nowutctimestr})  # 設定現在時間讓 control 回收
                        else:
                            await redis_obj.expire(item, 30)  # 如果進去保留的機台 讓他時間維持 30 秒 ttl

            if seatnum != 0:  # 進去某一台
                # 查詢該台是否是自己的
                if gametype == 0:
                    seatkey = 'goldseats_{}@{}'
                    selfseatkey = 'seatsgold_{}@{}_{}'
                elif gametype == 1:
                    seatkey = 'silverseats_{}@{}'
                    selfseatkey = 'seatssilver_{}@{}_{}'
                elif gametype == 2:
                    seatkey = 'tutorialseats_{}@{}'
                    selfseatkey = 'seatstutorial_{}@{}_{}'

                valuelist = await redis_obj.hmget(seatkey.format(gameid, seatnum), ['memberid', 'status'])
                reservememberid = pg_general.converttype(valuelist[0], int)
                reservestatus = pg_general.converttype(valuelist[1], int)

                if memberid == reservememberid:  # 自己的,直接進去改狀態
                    await redis_obj.hmset(seatkey.format(gameid, seatnum),
                                          {"memberid": memberid, "status": 1, "card": card, "avatar": avatar})
                    await redis_obj.set_value(selfseatkey.format(gameid, seatnum, memberid), '1', 30)
                    if gametype == 0:
                        await redis_obj.hdel('gemptyseats_{}'.format(gameid), str(seatnum))
                    elif gametype == 1:
                        await redis_obj.hdel('semptyseats_{}'.format(gameid), str(seatnum))
                    elif gametype == 2:
                        await redis_obj.hdel('temptyseats_{}'.format(gameid), str(seatnum))
                    joinseatstatus = {"isjoin": True, "seatnum": seatnum}
                elif memberid != reservememberid and reservestatus != 0:  # 機台是別人的
                    result = pg_general.Apiresult.success
                    resultdata = {
                        "result": 1,
                        "errdescription": '此機台已經有人搶先搂\n請換一台試試看!'
                    }
                    return result, resultdata
                else:  # 沒人的台子 , 可以進去
                    await redis_obj.hmset(seatkey.format(gameid, seatnum),
                                          {"memberid": memberid, "status": 1, "card": card, "avatar": avatar})
                    # 設定自己的 機台
                    await redis_obj.set_value(selfseatkey.format(gameid, seatnum, memberid), '1', 30)
                    if gametype == 0:
                        await redis_obj.hdel('gemptyseats_{}'.format(gameid), str(seatnum))
                    elif gametype == 1:
                        await redis_obj.hdel('semptyseats_{}'.format(gameid), str(seatnum))
                    elif gametype == 2:
                        await redis_obj.hdel('temptyseats_{}'.format(gameid), str(seatnum))
                    joinseatstatus = {"isjoin": True, "seatnum": seatnum}



            else:  # 隨機挑台
                # 抓所有機台 key
                if gametype == 0:
                    seatkey = 'goldseats_{}@{}'
                    selfseatkey = 'seatsgold_{}@{}_{}'
                    emptyseatnumlist = await redis_obj.hkeys('gemptyseats_{}'.format(gameid))
                elif gametype == 1:
                    seatkey = 'silverseats_{}@{}'
                    selfseatkey = 'seatssilver_{}@{}_{}'
                    emptyseatnumlist = await redis_obj.hkeys('semptyseats_{}'.format(gameid))
                elif gametype == 2:
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
                        elif gametype == 1:
                            await redis_obj.hdel('semptyseats_{}'.format(gameid), emptyseatnum)
                        elif gametype == 2:
                            await redis_obj.hdel('temptyseats_{}'.format(gameid), emptyseatnum)

                        emptyseatnum = int(emptyseatnum)

                    if emptyseatnum is not None:
                        # 找出那台機台佔位資訊
                        valuelist = await redis_obj.hmget(seatkey.format(gameid, emptyseatnum), ['memberid', 'status'])
                        reservememberid = pg_general.converttype(valuelist[0], int)
                        reservestatus = pg_general.converttype(valuelist[1], int)
                        if reservestatus == 0:  # 空台
                            await redis_obj.hmset(seatkey.format(gameid, emptyseatnum),
                                                  {"memberid": memberid, "status": 1, "card": card, "avatar": avatar})
                            # 設定自己的 機台
                            await redis_obj.set_value(selfseatkey.format(gameid, emptyseatnum, memberid), '1', 30)
                            joinseatstatus = {"isjoin": True, "seatnum": emptyseatnum}
                            break

                    else:  # 滿台
                        result = pg_general.Apiresult.success
                        resultdata = {
                            "result": 1,
                            "errdescription": "所有座位都已滿\n請稍後再試!!"
                        }
                        return result, resultdata

            if joinseatstatus.get('isjoin') == True:

                # 設定 dirty 座位
                dirtyseatnum = joinseatstatus.get('seatnum')
                if gametype == 0:
                    await redis_obj.hset('dirtyseat', 'g_{}_{}'.format(gameid, dirtyseatnum), 1)
                elif gametype == 1:
                    await redis_obj.hset('dirtyseat', 's_{}_{}'.format(gameid, dirtyseatnum), 1)
                elif gametype == 2:
                    await redis_obj.hset('dirtyseat', 't_{}_{}'.format(gameid, dirtyseatnum), 1)

                # 執行 Sigin 作業
                # memberid = gseat or sseat_gameid_seatnum_nowcont

                if env_setting.SIGNINPS_FLAG == True:
                    data = ''
                    # call ps game server sign in
                    if gametype == 0:
                        seatname = 'gseat'
                        PREFIX = 'SDAP'
                    elif gametype == 1:
                        seatname = 'sseat'
                        PREFIX = 'SDAPS'
                    elif gametype == 2:
                        seatname = 'tseat'
                        PREFIX = 'SDAPT'

                    seatmemberid = '{}_{}_{}'.format(seatname, gameid, joinseatstatus.get('seatnum'))
                    seatlogintoken = '{}_{}_{}*****{}'.format(seatname, gameid, joinseatstatus.get('seatnum'),
                                                              logintoken)
                    pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                        'joingameseat signin ps seatmemberid:{0},seatlogintoken:{1}'.format(
                                            seatmemberid, seatlogintoken))

                    psgameserverresult = pg_general.Apiresult.psloginerror
                    psgameserverresult_silver = pg_general.Apiresult.psloginerror
                    # call ps signin for gold
                    url = env_setting.PS_API_SERVER_URL + 'host/signin/?prefix={0}&member_id={1}&password={2}'.format(
                        PREFIX, seatmemberid, seatlogintoken)
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
                if gametype == 0:  # gold
                    seatvaluedatalist = await redis_obj.hmget(
                        'goldseats_{}@{}'.format(gameid, joinseatstatus.get('seatnum')),
                        ["unopenturn", "avgturn", "his1turn", "his2turn", "his3turn", "his1multi", "his2multi",
                         "his3multi"])
                elif gametype == 1:  # silver
                    seatvaluedatalist = await redis_obj.hmget(
                        'silverseats_{}@{}'.format(gameid, joinseatstatus.get('seatnum')),
                        ["unopenturn", "avgturn", "his1turn", "his2turn", "his3turn", "his1multi", "his2multi",
                         "his3multi"])
                elif gametype == 2:  # tutorial
                    seatvaluedatalist = await redis_obj.hmget(
                        'tutorialseats_{}@{}'.format(gameid, joinseatstatus.get('seatnum')),
                        ["unopenturn", "avgturn", "his1turn", "his2turn", "his3turn", "his1multi", "his2multi",
                         "his3multi"])

                result = pg_general.Apiresult.success
                resultdata['result'] = 0
                resultdata['errdescription'] = ''
                resultdata['seatnum'] = joinseatstatus.get('seatnum')
                resultdata['hallid'] = gametype
                resultdata['gameid'] = gameid
                resultdata['unopenturn'] = pg_general.converttype(seatvaluedatalist[0], int)
                resultdata['avgturn'] = pg_general.converttype(seatvaluedatalist[1], int)
                resultdata['his1turn'] = pg_general.converttype(seatvaluedatalist[2], int)
                resultdata['his2turn'] = pg_general.converttype(seatvaluedatalist[3], int)
                resultdata['his3turn'] = pg_general.converttype(seatvaluedatalist[4], int)
                resultdata['his1multi'] = 0 if seatvaluedatalist[5] is None else pg_general.converttype(
                    seatvaluedatalist[5], int)
                resultdata['his2multi'] = 0 if seatvaluedatalist[6] is None else pg_general.converttype(
                    seatvaluedatalist[6], int)
                resultdata['his3multi'] = 0 if seatvaluedatalist[7] is None else pg_general.converttype(
                    seatvaluedatalist[7], int)

                # write membergamelog
                nowutctime = pg_general.getutcnow()
                command = 'insert into membergamelog(memberid, gameid, joingametime, logintoken,gametype,seatnum) values("{0}", "{1}", "{2}", "{3}","{4}","{5}")'.format(
                    memberid, gameid, nowutctime, logintoken, gametype, joinseatstatus.get('seatnum'))
                updateresult, dataindex = await self.insertdbdata(logintoken, command)
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

        return result, resultdata

    async def _call_dummy_launch_api(self, url, json_dc, call_mark):
        """call GS API

        Args:
            url (str): 網址
            json_dc (dict): 要帶入的網址參數
            call_mark (str): 顯示 log 用的
        """
        errcount = 0
        output_dc = {}

        for _err in range(3):
            try:
                # call ps signin api
                if env_setting.LOCAL_SERVER == False:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, timeout=60, json=json_dc) as response:
                            if response.status == 200:
                                data = await response.json()
                                if int(data.get('status_code')) != 0:
                                    raise Exception('{} can not sign in user gold'.format(call_mark))
                                output_dc['download_url'] = data.get('download_url', '')
                                break
                            else:
                                data = await response.text()

                await asyncio.sleep(0)

            except ValueError:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'joincardgame {} ValueError:{}'.format(call_mark,
                                                                           format_exc()))
                break
            except Exception:
                errcount += 1
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'joincardgame {} except:{},errcount:{}'.format(call_mark,
                                                                                   format_exc(), errcount))
                await asyncio.sleep(0)

        return output_dc

    async def _check_line_game_player(self, access_token):
        command = 'SELECT line_access_token FROM member WHERE access_token = "{0}"'.format(access_token)
        datalen, data = await self.getdbdata('check linegame player', command)

        # 判斷是否為Linegame玩家
        line_access_token = data.get('line_access_token')
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'joincardgame _check_line_game_player type line_access_token:{}, line_access_token:{}'.format(
                                type(line_access_token), line_access_token))

        return_url = env_setting.SD555_LOBBY_URL

        if line_access_token != "0":
            return_url = return_url + '?line_access_token=' + line_access_token

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'joincardgame _check_line_game_player return_url:{}'.format(return_url))

        return return_url

    async def _return_dummy_launch_url(self, gameid, access_token, host_id):
        if gameid == GameID.dummy:
            url = env_setting.DUMMY_LAUNCH_URL
        elif gameid == GameID.dummy_king:
            url = env_setting.DUMMY_KING_LAUNCH_URL

        return_url = await self._check_line_game_player(access_token)

        json_dc = {
            "game_id": gameid,
            "room_id": 0,
            "lang": "zh-CN",
            "access_token": access_token,
            "return_url": return_url,
            "return_target": "top",
            "host_api_key": host_id,
            "host_currency": "THB",
        }

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'joincardgame _return_dummy_launch_url:{}, json:{}'.format(url, json_dc))

        output_dc = await self._call_dummy_launch_api(url, json_dc, '_return_dummy_launch_url')

        return output_dc

    async def _call_ps_launch_api(self, url, params, call_mark):
        """call GS API

        Args:
            url (str): 網址
            params (dict): 要帶入的網址參數
            call_mark (str): 顯示 log 用的
        """
        errcount = 0
        output_dc = {}

        for _err in range(3):
            try:
                # call ps signin api
                if env_setting.LOCAL_SERVER == False:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                if int(data.get('status_code')) != 0:
                                    raise Exception('{} can not sign in user gold'.format(call_mark))
                                output_dc['download_url'] = data.get('download_url', '')
                                break
                            else:
                                data = await response.text()

                await asyncio.sleep(0)

            except ValueError:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'joincardgame {} ValueError:{}'.format(
                                        call_mark,
                                        format_exc()))
                break
            except Exception:
                errcount += 1
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'joincardgame {} except:{},errcount:{},data:{}'.format(
                                        call_mark,
                                        format_exc(), errcount, data))
                await asyncio.sleep(0)

        return output_dc

    async def _return_go_launch_url(self, game_id, access_token, uid, host_id):
        params = {
            'access_token': access_token,
            'host_id': host_id,
            'game_id': game_id,
            'lang': 'zh-TW'
            # 'lang': 'tai',
            # 'ccy': 'CNY',
            # 'sm': '00',
            # 'subid': '0',
            # 'fullscr': '1',
            # 'lc': 'th-TH',
            # 'pm': '0',
            # 'ns': '0',
            # 'origin': 'https%3a%2f%2fdev-api.iplaystar.net',
            # 'uid': uid,
            # 'anal': '8',
            # 'lb': '1',
            # 'stf': '1',
        }
        # launch_url = 'https://dev-api.iplaystar.net/game/{}/?'.format(game_id)
        if game_id == GameID.pok_deng:
            launch_url = env_setting.POK_DENG_LAUNCH_URL
        elif game_id == GameID.pai_kang:
            launch_url = env_setting.PAI_KANG_LAUNCH_URL
        for k, v in params.items():
            launch_url += '{}={}&'.format(k, v)

        # output_dc = await self._call_ps_launch_api(launch_url, params, '_return_go_launch_url')

        return {'download_url': launch_url[:-1]}  # 去除掉最後一個 &

    async def _get_access_token(self, logintoken, member_id):
        """取得玩家的 access_token

        1. 撈資料表
        1.1 有資料就回傳
        2.1 無資料就建立新的檢查無重複之後再回傳
        """

        command = '''SELECT access_token FROM member WHERE memberid={}
        '''.format(member_id)

        datalen, data = await self.getdbdata(logintoken, command)

        if datalen == 1 and data.get('access_token') != '0':  # 資料庫預設這個欄位是 0
            return data.get('access_token')

        i = 0
        while i < 1000:
            access_token = pg_general.generatorsha256()

            command = '''SELECT * FROM member WHERE access_token="{}"
            '''.format(access_token)

            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 0:
                command = '''UPDATE member SET access_token="{}" WHERE memberid={}
                '''.format(access_token, member_id)

                update_result = await self.updatedbdata(logintoken, command)
                return access_token

    async def joincardgame(self, logintoken, memberid, jsoncontent):
        """加入棋牌遊戲

        1. call host/signin API 取得代理商設定的資料 host_id、access_token 等
        2. 根據遊戲取得 download_url 回傳
        """
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:joincardgame memberid:{0},param:{1}'.format(
                                    memberid, jsoncontent))
            result = pg_general.Apiresult.connectdberror
            resultdata = {'result': 1}

            gameid = jsoncontent.get('gameid')
            hallid = jsoncontent.get('hallid')  # 0 : gold hall , 1: silver hall

            if hallid == 0:
                PREFIX = 'SDAP'
            elif hallid == 1:
                PREFIX = 'SDAPS'
            elif hallid == 2:
                PREFIX = 'SDAPT'

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'joincardgame signin ps memberid:{0},logintoken:{1}'.format(
                                    memberid, logintoken))

            access_token = await self._get_access_token(logintoken, memberid)
            url = '''{}host/signin/?prefix={}&member_id={}&password={}'''.format(env_setting.PS_API_SERVER_URL, PREFIX,
                                                                                 memberid, access_token)

            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'joincardgame sign url:{}'.format(url))

            errcount = 0
            psgameserverresult = pg_general.Apiresult.psloginerror
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
                                        raise Exception('can not sign in user gold')
                                    psgameserverresult = pg_general.Apiresult.success
                                    if gameid == GameID.pok_deng:
                                        resultdata['gameserver'] = data.get("server_info").get("card").get('id1')
                                    elif gameid == GameID.pai_kang:
                                        resultdata['gameserver'] = data.get("server_info").get("card").get('id2')
                                    # TODO 2022.07.11 不需要這個回傳值，一段時間沒要求復原就刪除
                                    # resultdata['logintoken'] = data.get('access_token')
                                    # 金爽原本的 token 格式 = logintoken(*--)host_id
                                    host_id = data.get('host_id')
                                    uid = data.get('uid')
                                    access_host_id_token = data.get('access_token')
                                    resultdata['result'] = 0
                                    resultdata['gameid'] = gameid
                                    break
                                else:
                                    data = await response.text()
                    else:
                        psgameserverresult = pg_general.Apiresult.success
                    await asyncio.sleep(0)
                except ValueError:
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'joincardgame  signin ValueError:{}'.format(format_exc()))
                    break
                except Exception:
                    errcount += 1
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'joincardgame  signin except:{},errcount:{},data:{}'.format(
                                            format_exc(), errcount, data))
                    await asyncio.sleep(0)
            pg_general.writelog(pg_general.PG_LogerLevel.debug,
                                'joincardgame signin  signin result:{}, recv:{}'.format(
                                    psgameserverresult, data))

            if resultdata['result'] != 0:
                raise ValueError

            if gameid in (GameID.dummy, GameID.dummy_king):
                output_dc = await self._return_dummy_launch_url(gameid, access_token, host_id)

            elif gameid in (GameID.pok_deng, GameID.pai_kang, GameID.u4):
                output_dc = await self._return_go_launch_url(gameid, access_host_id_token, uid, host_id)

            else:
                output_dc = {
                    'download_url': ''
                }

            resultdata['download_url'] = output_dc['download_url']
            result = pg_general.Apiresult.success

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:joincardgame except:{0}'.format(format_exc()))

        return result, resultdata

    async def getnewdragontigerrank(self, redis_obj, logintoken, memberid, jsoncontent):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getnewdragontigerrank memberid:{0},logintoken:{1},jsoncontent:{2}'.format(
                                    memberid, logintoken, jsoncontent))
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
            datalen, data = await self.getdbdata('get rank description', command)
            if datalen != 1:
                raise Exception('get game desc data error')

            rankdescription = data.get('rankdescription')
            ranktype = data.get('ranktype')

            # get self data
            command = 'select avatar from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise Exception('get member data error')

            memberavatar = data.get('avatar')

            # 計算今天結算還有多少秒
            localdatetime = pg_general.get_cb_datetime()
            localdate = localdatetime.date()

            endtime = pg_general.strtodatetime(str(localdate) + ' 23:59:59.00')
            dailyresetcountdown = pg_general.converttype((endtime - localdatetime).total_seconds() + 1, int)

            # 計算這周結算還有多少秒
            enddate = localdate + timedelta(days=(6 - ((localdate.weekday() + 1) % 7)))
            endtime = pg_general.strtodatetime(str(enddate) + ' 23:59:59.00')
            weeklyresetcountdown = pg_general.converttype((endtime - localdatetime).total_seconds() + 1, int)

            # gametodaytopmultipilierrankinfo check self for selftodaytopmultipilierrankinfo
            selftodaytopmultipilierrankinfo = {"rank": -1, "amount": 0, "extraaward": 0}
            for item in gametodaytopmultipilierrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself": True})
                    selftodaytopmultipilierrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself": False})

            # gametodaytopwinrankinfo check self for selftodaytopwinrankinfo
            selftodaytopwinrankinfo = {"rank": -1, "amount": 0, "extraaward": 0}
            for item in gametodaytopwinrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself": True})
                    selftodaytopwinrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself": False})

            # gameweektopmultipilierrankinfo check self for selfweektopmultipilierrankinfo
            selfweektopmultipilierrankinfo = {"rank": -1, "amount": 0, "extraaward": 0}
            for item in gameweektopmultipilierrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself": True})
                    selfweektopmultipilierrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself": False})

            # gameweektopwinrankinfo check self for selfweektopwinrankinfo
            selfweektopwinrankinfo = {"rank": -1, "amount": 0, "extraaward": 0}
            for item in gameweektopwinrankinfo:
                if item.get('memberid') == memberid:
                    item.update({"isself": True})
                    selfweektopwinrankinfo.update({
                        "rank": item.get('rank'),
                        "amount": item.get('amount'),
                        "extraaward": item.get('extraaward')
                    })
                else:
                    item.update({"isself": False})

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

        return result, resultdata

    async def getnewtotalrank(self, redis_obj, logintoken, memberid):
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

        selftodayrank = -1  # 今日積分榜
        selftodayranksumwin = 0  # 今日積分榜贏分

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
                if len(jinsongranklive) > 0:
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
            localdate = pg_general.get_cb_datetime()
            if localdate.day >= 16:
                enddatetime = datetime(localdate.year, localdate.month,
                                       calendar.monthrange(localdate.year, localdate.month)[1], 23, 59, 59)
            else:
                enddatetime = datetime(localdate.year, localdate.month, 15, 23, 59, 59)

            diffseconds = pg_general.converttype((enddatetime - localdate).total_seconds(), int)

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
                "jinsongrankcountdownsec": diffseconds,
                "selfrankdata": selfrankdata,
                "richestrankinfo": richestrankinfo,
                "jinsongrankinfo": jinsongrankinfo,
                "likerankinfo": likerank,
                "gametodayrankinfo": gametotalranklist

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

    async def psapi_logout(self, redis_obj, logintoken, seatinfo):  # just use in new mode
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

        return result, resultdata

    async def getseatsinfo(self, redis_obj, logintoken, memberid, gameid, type):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getseatsinfo memberid:{0},gameid:{1},type:{2}'.format(memberid, gameid,
                                                                                                 type))
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # if type ==0: #gold
            #     seatkey = 'goldseats_{}@{}'.format(gameid)
            # else: # silver
            #     seatkey = 'silverseats_{}@{}'.format(gameid)
            #
            # allseatslist = await redis_obj.get_all_keys(seatkey)
            command = 'select seatsamount,seatsamount_s from game where gameid ="{0}"'.format(gameid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                return result, resultdata

            seatsamount = data.get('seatsamount')
            seatsamount_s = data.get('seatsamount_s')

            if type == 0:  # gold
                seatkey = 'goldseats_{}@'.format(gameid)
                seatamount = seatsamount
            else:  # silver
                seatkey = 'silverseats_{}@'.format(gameid)
                seatamount = seatsamount_s

            seatlist = []
            # get self selfreservenum selfreserveseconds
            selflist = []
            selfreservenum = 0
            selfreserveseconds = 0
            for temp_i in range(seatamount):
                valuelist = await redis_obj.hmget(seatkey + str(temp_i + 1),
                                                  ['unopenturn', 'avgturn', 'his1turn', 'his2turn', 'his3turn',
                                                   'memberid', 'status', 'avatar', 'dateline', 'his1multi', 'his2multi',
                                                   'his3multi'])

                tempstatus = pg_general.converttype(valuelist[6], int)
                tempseatsvalue = {
                    "num": temp_i + 1,
                    "unopenturn": pg_general.converttype(valuelist[0], int),
                    "avgturn": pg_general.converttype(valuelist[1], int),
                    "his1turn": pg_general.converttype(valuelist[2], int),
                    "his2turn": pg_general.converttype(valuelist[3], int),
                    "his3turn": pg_general.converttype(valuelist[4], int),
                    "his1multi": 0 if pg_general.converttype(valuelist[9], int) is None else pg_general.converttype(
                        valuelist[9], int),
                    "his2multi": 0 if pg_general.converttype(valuelist[10], int) is None else pg_general.converttype(
                        valuelist[10], int),
                    "his3multi": 0 if pg_general.converttype(valuelist[11], int) is None else pg_general.converttype(
                        valuelist[11], int),
                    "status": 2 if tempstatus in [2, 3] else tempstatus
                }

                if tempstatus == 1:
                    tempseatsvalue['avatar'] = valuelist[7]
                    tempseatsvalue['memberid'] = pg_general.converttype(valuelist[5], int)
                elif tempseatsvalue == 2:
                    tempseatsvalue['avatar'] = ''
                    tempseatsvalue['memberid'] = 0
                else:
                    tempseatsvalue['avatar'] = ''
                    tempseatsvalue['memberid'] = 0

                seatlist.append(tempseatsvalue)

                if memberid == pg_general.converttype(valuelist[5], int) and tempstatus in [2, 3]:
                    selflist.append({"seatnum": temp_i + 1, "dateline": pg_general.converttype(valuelist[8], str)})

            if len(selflist) > 0:  # 保留中
                nowutcdatetime = pg_general.getutcnow_datetime()
                tempdateline = pg_general.strtodatetime_nof(selflist[0].get('dateline'))

                selfreservenum = selflist[0].get('seatnum')
                selfreserveseconds = 0 if tempdateline <= nowutcdatetime else pg_general.converttype(
                    (tempdateline - nowutcdatetime).total_seconds(), int)
            else:
                selfreservenum = 0
                selfreserveseconds = 0

            if selfreserveseconds < 0:
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

        return result, resultdata

    async def web_getserverstatus(self):
        try:
            command = 'select * from webserversetting'
            datalen, data = await self.getdbdata('web_getserverstatus', command)

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

    async def webapi_loginfb(self, fbavatarobj, fbid, fbtoken, user_region, user_region_sub, user_city, user_ip):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:webapi_loginfb fbid:{0},fbtoken:{1}'.format(fbid, fbtoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'select memberid,nickname,avatar,credit,card,level,activenumber,enable,silvercredit,point,membertype from member where fbid="{0}"'.format(
                fbid)
            datalen, data = await self.getdbdata('webapi_loginfb', command, False, True)

            if datalen < 0:
                raise ValueError('can not find this user by fbid')

            if datalen == 0:
                result = pg_general.Apiresult.success
                clientdata = {
                    "statuscode": 1
                }
                return result, clientdata

            enable = data.get('enable')
            if enable != 1:
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
                command = 'update member set weblastlogintime = "{0}",weblastlogouttime=null,weblogintoken="{1}" where memberid ="{2}"'.format(
                    logintime, weblogintoken, memberid)
                updateresult = await self.updatedbdata('update web logintime', command)

                # save to memberloginlog db
                command = 'insert into memberloginlog (memberid,logintime,platform,deviceid,ip,logintoken,region,city,region_sub,fbid,loginmethod,fbtoken) ' \
                          ' values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}")'
                command = command.format(memberid, logintime, "2", "web", user_ip, weblogintoken, user_region,
                                         user_city, user_region_sub, fbid, "2", fbtoken)
                updateresult = await self.updatedbdata('insert into memberloginlog', command)

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
        return result, clientdata

    async def webapi_loginbytoken(self, fbid, weblogintoken, username):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:webapi_loginbytoken fbid:{0},username:{1},weblogintoken:{2}'.format(fbid,
                                                                                                               username,
                                                                                                               weblogintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            newweblogintoken = pg_general.generatorsha256()
            if fbid is not None:  # use fb search
                # get this member by token and fbid
                command = 'select memberid,nickname,avatar,card,level,credit,activenumber,silvercredit,point,membertype from member where fbid="{0}"'.format(
                    fbid)
                datalen, data = await self.getdbdata('get member by fbid', command)

                if datalen != 1:
                    result = pg_general.Apiresult.success
                    clientdata = {'statuscode': 1}
                    return result, clientdata

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

                command = 'update member set weblogintoken="{0}" where memberid="{1}"'.format(newweblogintoken,
                                                                                              memberid)
                resultrows = await self.updatedbdata('webapi_loginbytoken', command)

                result = pg_general.Apiresult.success
            else:  # use username search
                # get member by username & weblogintoken
                command = 'select memberid,nickname,avatar,card,level,credit,activenumber,silvercredit,point,membertype from member where username="{0}"'.format(
                    username)
                datalen, data = await self.getdbdata('get member by username', command)
                if datalen != 1:
                    result = pg_general.Apiresult.success
                    clientdata = {'statuscode': 1}
                    return result, clientdata

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

    async def webapi_loginusername(self, username, password, user_region, user_region_sub, user_city, user_ip):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:webapi_loginusername username:{0},password:{1}'.format(username, password))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            username = username.strip()
            password = password.strip()

            command = 'select memberid,nickname,avatar,credit,card,level,activenumber,enable,password,silvercredit,point,membertype from member where username="{0}"'.format(
                username)
            datalen, data = await self.getdbdata('webapi_loginusername', command, False, True)

            if datalen < 0:
                raise ValueError('can not find this user by fbid')

            if datalen == 0:
                result = pg_general.Apiresult.success
                clientdata = {
                    "statuscode": 1  # 帳號或是密碼錯誤
                }
                return result, clientdata
            enable = data.get('enable')
            if enable != 1:
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
                command = 'update member set weblastlogintime = "{0}",weblastlogouttime=null,weblogintoken="{1}" where memberid ="{2}"'.format(
                    logintime, weblogintoken, memberid)
                updateresult = await self.updatedbdata('update web logintime', command)

                # save to memberloginlog db
                command = 'insert into memberloginlog (memberid,logintime,platform,deviceid,ip,logintoken,region,city,region_sub,username,loginmethod) ' \
                          ' values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}")'
                command = command.format(memberid, logintime, "2", "web", user_ip, weblogintoken, user_region,
                                         user_city, user_region_sub, username, "1")
                updateresult = await self.updatedbdata('insert into memberloginlog', command)

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
        return result, clientdata

    async def webapi_logout(self, fbid, weblogintoken, username):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:webapi_logout fbid:{0},weblogintoken:{1}'.format(fbid, weblogintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            logouttime = pg_general.getutcnow_datetime()
            if fbid is not None:
                command = 'update member set lastlogouttime="{0}" where fbid = "{1}" and weblogintoken ="{2}"'.format(
                    logouttime, fbid, weblogintoken)
            else:  # username
                command = 'update member set lastlogouttime="{0}" where username = "{1}" and weblogintoken ="{2}"'.format(
                    logouttime, username, weblogintoken)

            updateresult = await self.updatedbdata('webapi_logout', command)

            clientdata = {
                'statuscode': 0
            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_logout ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_logout except:{0}'.format(e))
        return result, clientdata

    async def silvertogoldswitch(self, silvertogoldenable):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:silvertogoldswitch silvertogoldenable:{0}'.format(silvertogoldenable))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            if silvertogoldenable != 1 and silvertogoldenable != 0:
                raise ValueError('invalid parameter')

            logintoken = 0

            command = 'update setting2 set silvertogoldenable= {0}'.format(silvertogoldenable)
            updaterows = await self.updatedbdata(logintoken, command)

            result = pg_general.Apiresult.success
            clientdata = {
                "result": 1
            }
            return result, clientdata

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:silvertogoldswitch ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:silvertogoldswitch except:{0}'.format(e))
        return result, clientdata

    async def modexchangerateandswitch(self, rate, silvertogoldenable):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:modexchangerateandswitch rate:{0}, silvertogoldenable:{1}'.format(rate,
                                                                                                             silvertogoldenable))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}
            logintoken = 0

            command = 'update setting2 set exchangerate={0}, silvertogoldenable={1} WHERE setting2index = "1"'.format(
                rate, silvertogoldenable)
            updaterows = await self.updatedbdata_affectrows(logintoken, command)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:modexchangerate updaterows:{0}'.format(updaterows))

            command = 'SELECT exchangerate, silvertogoldenable FROM setting2 WHERE setting2index = "1"'
            datalen, data = await self.getdbdata('webapi_loginusername', command, False, True)

            rate = data.get('exchangerate')
            silvertogoldenable = data.get('silvertogoldenable')

            result = pg_general.Apiresult.success
            clientdata = {
                "rate": rate,
                "silvertogoldenable": silvertogoldenable
            }
            return result, clientdata

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:modexchangerateandswitch ValueError:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:modexchangerateandswitch except:{0}'.format(format_exc()))
        return result, clientdata

    async def getexchangerate(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getexchangerate')
            result = pg_general.Apiresult.connectdberror
            clientdata = {}
            logintoken = 0

            command = 'select exchangerate, silvertogoldenable FROM setting2'
            datalen, data = await self.getdbdata(logintoken, command)

            exchangerate = data.get('exchangerate')
            silvertogoldenable = data.get('silvertogoldenable')

            result = pg_general.Apiresult.success
            clientdata = {
                "exchangerate": exchangerate,
                "silvertogoldenable": silvertogoldenable
            }
            return result, clientdata

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getexchangerate ValueError:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getexchangerate except:{0}'.format(format_exc()))
        return result, clientdata

    async def membersearch(self, club_type, club, member_id, username, nickname, position, uuid):
        """成員查詢

        1. 撈有俱樂部的成員資料
        2. 根據 club_type 查詢特定的人
            club_type=0: 無俱樂部的人
            club_type=1: 全部玩家(含俱樂部)
            club_type=2: 俱樂部名稱
            club_type=3: 俱樂部 I D
            club_type=4: 有俱樂部的

        """
        try:
            log_msg = '''
            pg_asqldb:membersearch club_type:{}, club:{}, member_id:{},
            username:{}, nickname:{}, position:{}, uuid:{}
            '''.format(club_type, club, member_id, username, nickname, position, uuid)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            clientdata = {}
            search_result_ls = []

            if club_type == 2 and club:
                club_where_search = 'AND cb.name="{}"'.format(club)
                position_where_search = ''
                if position:
                    position_where_search = 'AND mc.position={}'.format(position)

            elif club_type == 3 and club:
                club_where_search = 'AND mc.clubid="{}"'.format(club)
                position_where_search = ''
                if position:
                    position_where_search = 'AND mc.position={}'.format(position)

            elif club_type == 4 and position:
                club_where_search = ''
                position_where_search = 'AND mc.position={}'.format(position)

            else:
                club_where_search = ''
                position_where_search = ''

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'club_where_search:{0}, position_where_search:{1}'.format(club_where_search,
                                                                                          position_where_search))

            member_id_where_search = 'AND m.memberid={}'.format(member_id) if member_id else ''
            username_where_search = 'AND m.username="{}"'.format(username) if username else ''
            nickname_where_search = 'AND m.nickname="{}"'.format(nickname) if nickname else ''
            uuid_where_search = 'AND m.linesub="{}"'.format(uuid) if uuid else ''

            command = '''
                SELECT mc.memberid, mc.position, mc.proxy, cr.*, hh.holding, cb.name, 
                m.username, m.nickname, m.phone, m.email, m.card, m.level, m.credit, 
                m.silvercredit, m.roomcard, m.avatar, m.message, m.registrationdatetime,
                m.linesub as uuid
                FROM memberclub AS mc
                LEFT JOIN club_right AS cr ON mc.clubid=cr.club_id
                LEFT JOIN host_holding AS hh ON mc.memberid=hh.host_id AND mc.clubid=hh.clubid
                LEFT JOIN club AS cb ON cb.clubid=mc.clubid
                LEFT JOIN member AS m ON m.memberid=mc.memberid
                WHERE mc.position=cr.position {} {} {} {} {} {}
            '''.format(club_where_search, member_id_where_search, username_where_search,
                       nickname_where_search, position_where_search, uuid_where_search)

            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'command:{0}, position_where_search:{1}'.format(command, position_where_search))
            if club_type != 0:
                datalen, data = await self.getdbdata('membersearch', command, fetchall=True)

                if datalen != 0:
                    search_result_ls += data

            if club_type == 0 or club_type == 1:  # 撈所有沒有參加俱樂部的人
                command = '''
                    SELECT m.memberid, 
                    m.username, m.nickname, m.phone, m.email, m.card, m.level, m.credit, 
                    m.silvercredit, m.roomcard, m.avatar, m.message, m.registrationdatetime,
                    m.linesub as uuid
                    FROM member AS m
                    WHERE m.memberid NOT IN (SELECT memberid FROM memberclub) {} {} {} {}
                '''.format(member_id_where_search, username_where_search, nickname_where_search, uuid_where_search)

                no_club_datalen, no_club_data = await self.getdbdata('membersearch',
                                                                     command, fetchall=True)
                if no_club_datalen != 0:
                    search_result_ls += no_club_data

            if len(search_result_ls) != 0:
                for dc in search_result_ls:
                    if dc.get('id'):  # 如果是撈全部的人，就不會有這些資料
                        del dc['id']  # 刪除不必要的欄位
                        del dc['cr.position']

                        holding = dc['holding']
                        dc['holding'] = str(holding) if holding else '0.00'

                    registrationdatetime = dc['registrationdatetime']

                    if registrationdatetime:
                        dc['registrationdatetime'] = pg_general.datetime_to_str(registrationdatetime)

            result = pg_general.Apiresult.success
            clientdata = {
                "data": search_result_ls
            }
            return result, clientdata

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:membersearch ValueError:{0}'.format(format_exc()))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:membersearch except:{0}'.format(format_exc()))
        return result, clientdata

    async def _modmember_update_member(self, phone, email, card, level, member_id):
        command = '''
            UPDATE member
            SET phone="{}", email="{}", card={}, level={}
            WHERE memberid={}
        '''.format(phone, email, card, level, member_id)

        update_result = await self.updatedbdata(
            'modmember {}'.format(member_id),
            command)
        if not update_result:
            raise ValueError('member table error')

    async def _modmember_insert_memberclub(self, member_id, now_time, club_id, position, proxy):
        command = '''
            INSERT INTO memberclub(memberid, jointime, clubid, position, proxy)
            VALUES({}, "{}", "{}", {}, {})
        '''.format(member_id, now_time, club_id, position, proxy)

        insert_result, index = await self.insertdbdata(
            'modmember {}'.format(member_id),
            command)
        if not insert_result:
            raise ValueError('memberclub table error')

    async def _modmember_insert_host_holding(self, member_id, now_time, club_id, position,
                                             proxy, history):
        command = '''
            INSERT INTO host_holding(host_id, clubid, upper_host_id, host_level,
            history, holding, created_at)
            VALUES("{}", "{}", "{}", {}, "{}", "0", "{}")
        '''.format(member_id, club_id, proxy, position, history,
                   now_time)

        insert_result, index = await self.insertdbdata('modmember {}'.format(member_id),
                                                       command)

        if not insert_result:
            raise ValueError('host_holding table error')

    async def _modmember_insert_host_id(self, member_id, club_id, position,
                                        proxy, history):
        command = '''
            INSERT INTO host_id(host_id, clubid, upper_host_id, host_level, history)
            VALUES("{}", "{}", "{}", {}, "{}")
        '''.format(member_id, club_id, proxy, position, history)

        insert_result, index = await self.insertdbdata('modmember {}'.format(member_id),
                                                       command)

        if not insert_result:
            raise ValueError('host_id table error')

    async def modmember(self, member_id, phone, email, card, level, club_id, position, proxy,
                        mode):
        """更新玩家資料 & 俱樂部資料

        除了更新之外也可以將沒有俱樂部的成員加入至俱樂部，但要 mode = 1 的情況下

        1. 更新 member 資料表
        2. insert memberclub 資料表
        3. insert host_holding 資料表
        4. insert host_id 資料表
        """
        try:
            log_msg = '''
            pg_asqldb:modmember member_id: {}, phone: {}, email: {}, card: {}, level: {}, 
            club_id: {}, position: {}, proxy: {}
            '''.format(member_id, phone, email, card, level, club_id, position, proxy)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            now_time = pg_general.getutcnow()

            await self._modmember_update_member(phone, email, card, level, member_id)

            if mode == 1:
                await self._modmember_insert_memberclub(member_id, now_time, club_id, position, proxy)

            history = await self._get_history(member_id)

            if position not in (7, 8) and mode == 1:  # 管理員 & 一般成員不需要加到這些表內
                await self._modmember_insert_host_holding(member_id, now_time,
                                                          club_id, position, proxy, history)

                await self._modmember_insert_host_id(member_id, club_id, position,
                                                     proxy, history)

            result = pg_general.Apiresult.success

            return result, clientdata

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:modmember ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:modmember except:{0}'.format(format_exc()))
        return result, clientdata

    async def update_club_member_holding(self, member_id, club_id, holding):
        try:
            log_msg = '''
            pg_asqldb:update_club_member_holding member_id: {}, club_id: {}, holding: {}
            '''.format(member_id, club_id, holding)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = '''UPDATE host_holding SET holding={} WHERE host_id="{}" AND clubid="{}"
            '''.format(holding, member_id, club_id)

            holding_result = await self.updatedbdata('update_club_member_holding: {}'.format(member_id)
                                                     , command)

            command = 'SELECT holding FROM host_holding WHERE host_id = {0} and clubid = {1}'.format(member_id, club_id)
            datalen, data = await self.getdbdata('select_club_member_holding: {0}'.format(member_id), command)

            holding = pg_general.converttype(data.get('holding'), str)

            clientdata = {
                "holding": holding
            }

            if holding_result:
                result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:update_club_member_holding ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:update_club_member_holding except:{0}'.format(format_exc()))
        return result, clientdata

    async def get_club_list(self):
        """取得可以加入的俱樂部名單

        1. 過濾出未滿 6000 人的俱樂部
        2. 取得俱樂部 id & 名稱
        """
        try:
            log_msg = '''
            pg_asqldb:get_club_list member_id: {}, club_id: {}, holding: {}
            '''

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = '''
                SELECT clubid, name FROM club
                WHERE clubid IN (
                    SELECT clubid FROM memberclub
                    GROUP BY clubid
                    HAVING COUNT(*)<6000
                )
            '''

            datalen, data = await self.getdbdata('get_club_list', command, fetchall=True)

            result = pg_general.Apiresult.success
            clientdata['data'] = data

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_list ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_list except:{0}'.format(format_exc()))
        return result, clientdata

    async def get_club_position_proxy_list(self, club_id, position):
        """取得該職位在俱樂部的上級代理人帳號"""
        try:
            log_msg = '''
            pg_asqldb:get_club_position_proxy_list member_id: {}, club_id: {}, holding: {}
            '''

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            if position == 7:  # 如果是管理員（7）就給 0 代表館主
                proxy_position_command = '(0)'
            elif position == 8:  # 一般成員就顯示所有代理
                proxy_position_command = '(0, 1, 2, 3, 4, 5, 6)'
            else:  # 該職位的上級代理就直接減 1
                proxy_position_command = '({})'.format(position - 1)

            command = '''
                SELECT memberid, position FROM memberclub
                WHERE position IN {} AND clubid="{}"
            '''.format(proxy_position_command, club_id)

            datalen, data = await self.getdbdata('get_club_position_proxy_list', command, fetchall=True)

            result = pg_general.Apiresult.success
            clientdata['data'] = data if datalen != 0 else []

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_position_proxy_list ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_club_position_proxy_list except:{0}'.format(format_exc()))
        return result, clientdata

    async def set_create_club_verify(self, member_id, right):
        """設定該名成員是否可以建立俱樂部"""
        try:
            log_msg = '''
                pg_asqldb:set_create_club_verify member_id: {}, right: {}
            '''.format(member_id, right)

            pg_general.writelog(pg_general.PG_LogerLevel.info, log_msg)
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = '''
                SELECT * FROM create_club_verify_list WHERE member_id={}
            '''.format(member_id)

            datalen, data = await self.getdbdata('get_create_club_verify', command)

            if datalen == 0:
                command = '''
                    INSERT INTO create_club_verify_list (member_id, `right`)
                    VALUES ({}, {})
                '''.format(member_id, right)
                updateresult, insertindex = await self.insertdbdata('insert_create_club_verify', command)
            else:
                command = '''
                    UPDATE create_club_verify_list
                    SET `right`={}
                    WHERE member_id={}
                '''.format(right, member_id)

                updateresult = await self.updatedbdata('update_create_club_verify', command)

            if updateresult:
                result = pg_general.Apiresult.success

        except ValueError:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:set_create_club_verify ValueError:{0}'.format(format_exc()))

        except Exception:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:set_create_club_verify except:{0}'.format(format_exc()))
        return result, clientdata

    async def creditexchange(self, logintoken, memberid, type, amount):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:creditexchange logintoken:{0},memberid:{1},type:{2},amount:{3}'.format(
                                    logintoken, memberid, type, amount))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # get setting2 silvertogoldenable setting
            command = 'select silvertogoldenable, exchangerate from setting2'
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                raise ValueError('can not get silvertogold setting')

            silvertogoldenable = data.get('silvertogoldenable')
            exchangerate = data.get('exchangerate')

            # type 0: 金轉銀, 1: 銀轉金
            # 檢查 type=1 , amount 是否有大於 100,type ==0 , amount >0
            if type == 1 and amount < exchangerate:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                raise ValueError('type error 1')

            elif type == 0 and amount < 1:
                result = pg_general.Apiresult.parametererror
                raise ValueError('type error 2')

            if type == 0:
                command = 'update member set credit= credit -"{0}",silvercredit = silvercredit + "{1}" ' \
                          'where memberid = "{2}" and credit >= "{0}"'.format(amount, amount * exchangerate, memberid)
                updaterows = await self.updatedbdata_affectrows(logintoken, command)
                if updaterows == 0:
                    result = pg_general.Apiresult.success
                    clientdata = {
                        "result": 1
                    }
                    return result, clientdata

                # write to transaction log
                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.goldtosilver,
                    "amount": amount,
                    "otherdata": "goldtosilver"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))

            elif type == 1 and silvertogoldenable == 1:
                goldcredit = int(amount * exchangerate)
                silvercredit = goldcredit * exchangerate
                command = 'update member set silvercredit=silvercredit-"{0}",credit=credit+"{1}" ' \
                          'where memberid= "{2}" and silvercredit>="{0}"'.format(silvercredit, goldcredit, memberid)
                updaterows = await self.updatedbdata_affectrows(logintoken, command)
                if updaterows == 0:
                    result = pg_general.Apiresult.success
                    clientdata = {
                        "result": 1
                    }
                    return result, clientdata

                param = {
                    "frommemberid": memberid,
                    "tomemberid": memberid,
                    "type": pg_general.transactiontype.silvertogold,
                    "amount": amount,
                    "otherdata": "silvertogold"
                }
                asyncio.ensure_future(self.writetransactionlog(logintoken, param))
            elif type == 1 and silvertogoldenable == 0:
                result = pg_general.Apiresult.othererror
                raise ValueError('silvertogold is 0')
            else:
                result = pg_general.Apiresult.parametererror
                raise ValueError('type error 3')
            # get final credit & silvercredit
            command = 'select credit , silvercredit from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command, False, True)
            if datalen == 1:
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
        return result, clientdata

    async def pointtocredit(self, logintoken, memberid, type, amount):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:pointtocredit logintoken:{0},memberid:{1},type:{2},amount:{3}'.format(
                                    logintoken, memberid, type, amount))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # 檢查資料
            if type == 0 and amount < 1:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return result, clientdata

            # type 0: 點數換金幣, 1: 查詢點數
            if type == 0:
                command = 'update member set point=point-"{0}",credit=credit+"{1}" where memberid = "{2}" and point >="{0}"'.format(
                    amount, amount * 100, memberid)
                updaterows = await self.updatedbdata_affectrows(logintoken, command)
                if updaterows == 1:
                    # get final point and credit
                    command = 'select credit,point from member where memberid ="{0}"'.format(memberid)
                    datalen, data = await self.getdbdata(logintoken, command, False, True)
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
                    asyncio.ensure_future(self.writetransactionlog(logintoken, param))

                else:
                    clientdata = {
                        "result": 1
                    }

            elif type == 1:
                command = 'select point from member where memberid = "{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                if datalen == 1:
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
        return result, clientdata

    async def getfreeboxstatus(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getfreeboxstatus logintoken:{0},memberid:{1}'.format(logintoken, memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # get cardinfo.freecoin , freecointimes
            command = 'select member.todayfreeboxgettimes,member.lastfreecoingettime,member.credit,member.safe,cardinfo.freecoin,cardinfo.freecointimes,silvercredit,setting2.freeboxcdseconds,setting2.freeboxmode from member,cardinfo,setting2 ' \
                      ' where member.memberid="{0}" and cardinfo.card = member.card'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen == 1:
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
                if (credit + safe + silvercredit / 100) >= 1000 and freeboxmode == 1:  # freeboxmode ==1 代表帳戶餘額要小於 100
                    clientdata = {
                        "enable": 0,
                        "timeleft": timeleft,
                        "gettimes": todayfreeboxgettimes,
                        "totalamount": freecointimes

                    }
                elif freecoin == 0 or todayfreeboxgettimes >= freecointimes:
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
        return result, clientdata

    async def receivefreebox(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:receivefreebox logintoken:{0},memberid:{1}'.format(logintoken, memberid))
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
                if (credit + safe + silvercredit / 100) >= 1000 and freeboxmode == 1:
                    clientdata = {
                        "result": 1  # 領取失敗
                    }
                    result = pg_general.Apiresult.success
                elif freecoin == 0 or todayfreeboxgettimes >= freecointimes or timeleft > 0:
                    clientdata = {
                        "result": 1  # 領取失敗
                    }
                    result = pg_general.Apiresult.success
                else:  # 領取成功
                    command = 'update member set todayfreeboxgettimes= todayfreeboxgettimes+1,lastfreecoingettime="{0}",credit=credit+"{1}" where ' \
                              'memberid="{2}"'.format(nowdatetime, freecoin, memberid)
                    updateresult = await self.updatedbdata(logintoken, command)

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
                    datalen, data = await self.getdbdata(logintoken, command, False, True)

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
        return result, clientdata

    async def forgetpasssms(self, logintoken, username, phone):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:forgetpasssms logintoken:{0},username:{1},phone:{2}'.format(logintoken,
                                                                                                       username, phone))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # 先確認資料正確性
            if None in [username, phone]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return result, clientdata

            phone = phone.strip()
            username = username.strip()

            if '09' != phone[:2] or phone.isdigit() == False:
                result = pg_general.Apiresult.success
                clientdata = {'result': 2}
                return result, clientdata

            # find in db
            command = 'select memberid,phonevalidatetime from member where phonebindstatus=2 and phone ="{0}" and username="{1}"'.format(
                phone, username)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 1
                }
                return result, clientdata

            # 撈是否有超過一分鐘
            phonevalidatetime = data.get('phonevalidatetime')
            memberid = data.get('memberid')
            nowdatetime = pg_general.getutcnow_datetime()
            if (nowdatetime - phonevalidatetime).total_seconds() < 60:
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
        return result, clientdata

    async def changenewpassword(self, logintoken, username, phone, validatecode, newpassword):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:changenewpassword logintoken:{0},username:{1},phone:{2}'.format(logintoken,
                                                                                                           username,
                                                                                                           phone))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # 先確認資料正確性
            if None in [username, phone, validatecode, newpassword]:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 2
                }
                return result, clientdata

            phone = phone.strip()
            username = username.strip()
            validatecode = validatecode.strip()
            newpassword = newpassword.strip()

            if '09' != phone[:2] or phone.isdigit() == False:
                result = pg_general.Apiresult.success
                clientdata = {'result': 2}
                return result, clientdata

            # 檢查資料
            pattern = re.compile(r'[a-zA-Z0-9]+')
            password_result = pattern.match(newpassword)
            password_lenresult = len(newpassword) >= 6 and len(newpassword) <= 12

            if password_result == False or password_lenresult == False:
                result = pg_general.Apiresult.success
                clientdata = {'result': 5}
                return result, clientdata

            # find in db
            command = 'select memberid,phonevalidatetime,phonevalidatecode from member where phonebindstatus=2 and phone ="{0}" and username="{1}"'.format(
                phone, username)
            datalen, data = await self.getdbdata(logintoken, command)

            if datalen != 1:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 1
                }
                return result, clientdata

            phonevalidatecode = data.get('phonevalidatecode')

            nowdatetime = pg_general.getutcnow_datetime()
            phonevalidatetime = data.get('phonevalidatetime')
            if (nowdatetime - phonevalidatetime).total_seconds() >= 600:  # 驗證碼超過 10 分鐘
                result = pg_general.Apiresult.success
                clientdata = {'result': 4}
                return result, clientdata

            if phonevalidatecode != validatecode:  # 驗證碼錯誤
                result = pg_general.Apiresult.success
                clientdata = {'result': 1}
                return result, clientdata

            memberid = data.get('memberid')

            # write to db new password
            command = 'update member set password ="{0}",phonevalidatetime="{2}" where memberid="{1}"'.format(
                newpassword, memberid, nowdatetime - timedelta(days=1))
            updateresult = await self.updatedbdata(logintoken, command)

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
        return result, clientdata

    async def bindusername(self, logintoken, memberid, username, password):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:bindusername logintoken:{0},memberid:{1},username:{2},password:{3}'.format(
                                    logintoken, memberid, username, password))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            comfirmresult = await self.confirmregisterdata(logintoken, username, password)
            if comfirmresult == False:
                clientdata = {
                    "result": 1
                }
                result = pg_general.Apiresult.success
                return result, clientdata

            command = 'update member set username="{0}",password="{1}" where memberid="{2}"'.format(username, password,
                                                                                                    memberid)
            updateresultrows = await self.updatedbdata_affectrows(logintoken, command)

            if updateresultrows <= 0:
                clientdata = {
                    "result": 2
                }
                result = pg_general.Apiresult.success
                return result, clientdata

            clientdata = {
                "result": 0
            }
            result = pg_general.Apiresult.success
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:bindusername ValueError:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:bindusername except:{0}'.format(e))
        return result, clientdata

    async def friendonlinestatus(self, logintoken, memberid, redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:friendonlinestatus logintoken:{0},memberid:{1}'.format(logintoken, memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = []

            # get member friendlist
            command = 'select friendlist from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen == 1:
                friendlist = data.get('friendlist')
                if friendlist is not None:
                    friendlist = friendlist.strip()
                    if friendlist == '':
                        result = pg_general.Apiresult.success
                        return result, clientdata

            friendlist = friendlist.split(',')
            if len(friendlist) == 0:
                result = pg_general.Apiresult.success
                return result, clientdata

            newfriendlist = ['online_' + item for item in friendlist]

            friendonlinelist = await redis_obj.mget(newfriendlist)

            if len(friendlist) != len(friendonlinelist):
                raise ValueError('friendlist friendonlinelist is diff')

            for x, y in zip(friendlist, friendonlinelist):
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
        return result, clientdata

    async def updatemembermessage(self, logintoken, memberid, message):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updatemembermessage logintoken:{0},memberid:{1},messae:{2}'.format(
                                    logintoken, memberid, message))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            if len(message) > 120:
                result = pg_general.Apiresult.success
                clientdata = {
                    "result": 1
                }
                return result, clientdata

            command = 'update member set message="{0}" where memberid = "{1}"'.format(message, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

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
        return result, clientdata

    async def reportmember(self, logintoken, memberid, tomemberid, content):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:reportmember logintoken:{0},memberid:{1},tomemberid:{2},content:{3}'.format(
                                    logintoken, memberid, tomemberid, content))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # insert into db reportmember
            utcnowdatetime = pg_general.getutcnow_datetime()
            command = 'insert into reportmember(frommemberid,tomemberid,reportdatetime,content) values("{0}","{1}","{2}","{3}")'.format(
                memberid, tomemberid, utcnowdatetime, content)
            updateresult = await self.updatedbdata(logintoken, command)

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
        return result, clientdata

    async def actionframe(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:actionframe logintoken:{0},memberid:{1}'.format(logintoken, memberid))
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            # get nowutc time
            nowutcdattime = pg_general.getutcnow_datetime()

            command = 'select * from action where starttime <= "{0}" and (endtime>="{0}" or endtime is null) order by listtype,listpos,contentpos'.format(
                nowutcdattime)
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen == 0:
                clientdata = {
                    "action": {},
                    "official": {}
                }
                result = pg_general.Apiresult.success
                return result, clientdata
            elif datalen > 0:
                actionlist = [item for item in data if item.get('listtype') == 0]
                officiallist = [item for item in data if item.get('listtype') == 1]

                actiondict = {}
                officialdict = {}

                for item in actionlist:
                    listpos = item.get('listpos')

                    if actiondict.get(listpos) is None:
                        actiondict[listpos] = {}
                        actiondict[listpos]['content'] = []
                    actiondict[listpos]['actionnumber'] = item.get('actionnumber')
                    actiondict[listpos]['buttonurl'] = item.get('buttonurl')
                    actiondict[listpos]['newflag'] = item.get('newflag')
                    tempstarttime = item.get('starttime')
                    tempstarttime = pg_general.get_utc_to_local_datetime(tempstarttime)
                    tempendtime = item.get('endtime')
                    if tempendtime == '0000-00-00 00:00:00':
                        actiondict[listpos]['duration'] = ''
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
                if len(tempactionkeys) > 0:
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
                if len(tempofficialkeys) > 0:
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
        return result, clientdata

    async def restoreIAP(self, logintoken, memberid, jsoncontent):
        result = pg_general.Apiresult.success
        clientdata = {"result": 0}

        return result, clientdata

    async def getselfrankgamesort(self, redis_obj, logintoken, memberid):
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
                return result, clientdata

            gametodayrank_new = [item for item in gametodayrank if item.get('memberid') == memberid]
            selfrankgamesort = []
            selfrankgamedict = {}
            for item in gametodayrank_new:
                ranktype = item.get('ranktype')
                rank = pg_general.converttype(item.get('rank'), int)
                if rank > 5:
                    continue

                gameid = item.get('gameid')
                if selfrankgamedict.get(gameid) is None:
                    selfrankgamedict[gameid] = {"gameid": gameid}
                if ranktype == 0:
                    selfrankgamedict[gameid]["topmultiplierrank"] = rank
                elif ranktype == 1:
                    selfrankgamedict[gameid]["topwinrank"] = rank

            if selfrankgamedict != {}:
                for item in selfrankgamedict.keys():
                    selfrankgamesort.append(selfrankgamedict.get(item))

            clientdata['selfrankgamelist'] = selfrankgamesort

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getselfrankgamesort except:{0}'.format(e))

        return result, clientdata

    async def getselfrankgamesortnew(self, redis_obj, logintoken, memberid):
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

            for tempgameid, tempvalue in topwinrankdictlive.items():
                for item in tempvalue:
                    if item.get('memberid') == memberid:
                        rank = item.get('rank')
                        ranktype = item.get('ranktype')
                        extraaward = item.get('extraaward')
                        if ranktype == 0 and extraaward > 0:
                            totalaward_g += extraaward
                        elif ranktype == 1 and extraaward > 0:
                            totalaward_s += extraaward
                        if rank <= 5:
                            if selfrankgamedict.get(tempgameid) is None:
                                selfrankgamedict[tempgameid] = {}
                            selfrankgamedict[tempgameid]['topwinrank'] = rank
                            break
            for tempgameid, tempvalue in topmultipilierdictlive.items():
                for item in tempvalue:
                    if item.get('memberid') == memberid:
                        rank = item.get('rank')
                        ranktype = item.get('ranktype')
                        extraaward = item.get('extraaward')
                        if ranktype == 0 and extraaward > 0:
                            totalaward_g += extraaward
                        elif ranktype == 1 and extraaward > 0:
                            totalaward_s += extraaward
                        if rank <= 5:
                            if selfrankgamedict.get(tempgameid) is None:
                                selfrankgamedict[tempgameid] = {}
                            selfrankgamedict[tempgameid]['topmultiplierrank'] = rank
                            break

            for tempgameid, tempvalue in selfrankgamedict.items():
                tempdict = {"gameid": tempgameid}
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

    async def getavatarlist(self, logintoken, memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getavatarlist logintoken:{0}'.format(
                                    logintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {"avatarlist": []}
            avatarlist = []
            # get fb avatar
            command = 'select isbindfb from member where memberid="{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                isbindfb = data.get('isbindfb')
                if isbindfb == 1:
                    avatarlist.append(pg_fbavatar.AVATAR_URL.format(memberid))

            command = 'select * from memberavatarlist order by avatarindex'
            datalen, data = await self.getdbdata(logintoken, command, True)
            if datalen > 0:
                for item in data:
                    avatarlist.append(item.get('avatarurl'))

                clientdata = {
                    "avatarlist": avatarlist
                }
            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getavatarlist except:{0}'.format(e))

        return result, clientdata

    async def setavatarfromlist(self, logintoken, memberid, avatarurl):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:setavatarfromlist logintoken:{0}'.format(
                                    logintoken))
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result": 1}

            # check url 正確性
            if "resource-avatar.playgems.net" not in avatarurl:
                result = pg_general.Apiresult.success
                clientdata = {"result": 1}
                return result, clientdata

            command = 'update member set avatar="{0}",isavatarchanged="1" where memberid = "{1}"'.format(avatarurl,
                                                                                                         memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            if updateresult == True:
                clientdata = {"result": 0}
            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:setavatarfromlist except:{0}'.format(e))

        return result, clientdata

    async def confirmregisterdata(self, logintoken, username, password):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:confirmregisterdata logintoken:{0},username:{1},password:{2}'.format(
                                    logintoken, username, password))
            result = False

            # 檢查資料
            pattern = re.compile(r'[a-zA-Z0-9]+')
            pattern2 = re.compile(r'[a-zA-Z]+')
            username_result = pattern.match(username)
            password_result = pattern.match(password)
            username_lenresult = len(username) >= 6 and len(username) <= 12
            password_lenresult = len(password) >= 6 and len(password) <= 12
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

    async def writegiftfreeze(self, logintoken, param):
        try:

            # 確認 setting2.giftfreezeenable = 1
            command = 'select giftfreezeenable from setting2 where giftfreezeenable = 1'
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                return

            memberid = param.get('memberid')
            type = param.get('type')
            amount = param.get('amount')

            starttime = pg_general.getutcnow_datetime()
            starttime_str = pg_general.datetimetostr_nof(starttime)
            endtime = starttime + timedelta(days=7)
            endtime_str = pg_general.datetimetostr_nof(endtime)

            command = 'insert into giftfreeze (memberid,starttime,endtime,type,amount) values ("{0}","{1}","{2}","{3}","{4}")'.format(
                memberid, starttime_str, endtime_str, type, amount)
            insertresult = await self.insertdbdata(logintoken, command)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writegiftfreeze except:{0}'.format(e))

    async def getgiftfreezedata(self, logintoken, memberid):
        try:
            nowutcdatetime = pg_general.getutcnow_datetime()
            giftfreezedata = {"freezetotalamount": 0, "freezelist": []}
            sumamount = 0
            templist = []

            command = 'select memberid,amount,endtime,type from giftfreeze where memberid = "{0}" and "{1}" between starttime and endtime order by endtime'.format(
                memberid, nowutcdatetime)
            datalen, data = await self.getdbdata(logintoken, command, True)

            if datalen > 0:
                for idx, item in enumerate(data):
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

                    tempendtime = (item.get('endtime') + timedelta(hours=8)).__str__()
                    templist.append({
                        "num": idx + 1,
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

    async def writetransactionlog(self, logintoken, param):
        # db.transaction
        # type : 參考 pg_general.transactiontype
        try:
            transtime = pg_general.getutcnow_datetime()
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
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime, frommemberid, tomemberid, type,
                                                                           amount, amount_silver, otherdata)

            updateresult = await self.updatedbdata(logintoken, command)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writetransactionlog except:{0}'.format(e))

    async def webapi_getgashwalletitem(self):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            command = 'select gashwalletflag from webserversetting'
            datalen, data = await self.getdbdata('get gashwalletflag', command)
            if datalen == 1:
                gashwalletflag = data.get('gashwalletflag')
                if gashwalletflag == 0:
                    result = pg_general.Apiresult.success
                    clientdata = {"status_code": 2}  # gash wallet 維護中
                    return result, clientdata

            command = 'select * from gashwalletinfo order by itemcode'
            datalen, data = await self.getdbdata('webapi_getgashwalletitem', command, True)

            if datalen > 0:
                clientdata = {
                    "status_code": 0,
                    "data": data.copy()
                }
                result = pg_general.Apiresult.success


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_getgashwalletitem except:{0}'.format(e))

        return result, clientdata

    async def webapi_getgashpointitem(self):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            command = 'select gashpointflag from webserversetting'
            datalen, data = await self.getdbdata('get webserver gashflag', command, False)

            if datalen == 1:
                gashpointflag = data.get('gashpointflag')
                if gashpointflag == 0:
                    result = pg_general.Apiresult.success
                    clientdata = {"status_code": 2}  # 維護中
                    return result, clientdata

            command = 'select * from gashpointinfo order by itemcode'
            datalen, data = await self.getdbdata('webapi_getgashpointitem', command, True)

            if datalen > 0:
                clientdata = {
                    "status_code": 0,
                    "data": data.copy()
                }
                result = pg_general.Apiresult.success


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_getgashpointitem except:{0}'.format(e))

        return result, clientdata

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

            command = 'insert into mycardhistory(statusapi, facserviceid, factradeseq, tradetype, serverid, customerid, paymenttype, itemcode, productname, amount, currency, sandboxmode, facreturnurl, hash, returncode, returnmsg, authcode, tradeseq, ingamesavetype, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}","{13}","{14}","{15}","{16}","{17}","{18}","{19}")'.format(
                statusapi, facserviceid, factradeseq, tradetype, serverid, customerid, paymenttype, itemcode,
                productname, amount, currency, sandboxmode, facreturnurl, hash, returncode, returnmsg, authcode,
                tradeseq, ingamesavetype, insertutcnowdate)
            await self.insertdbdata('mycard_gashpoints', command)
            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb: insertmycardhistory failed in 3-1 except:{0}'.format(e))
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
            command = 'insert into mycardhistory(statusapi, returncode, returnmsg, payresult, factradeSeq, paymenttype, amount, currency, mycardtradeno, mycardtype, promocode, hash, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}")'.format(
                statusapi, ReturnCode, ReturnMsg, PayResult, FacTradeSeq, PaymentType, Amount, Currency, MyCardTradeNo,
                MyCardType, PromoCode, Hash, insertutcnowdate)
            await self.insertdbdata('mycard_mcresult', command)

            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb: insert mycardhistory failed in 3-2-4 except:{0}'.format(e))
            return False

    # 3-3 從資料表取得請求智冠必要的AuthCode與SandBoxMode與Amount與CustomerId
    async def get_mycardhistory_AuthCode_SandBoxMode(self, FacTradeSeq):
        try:
            # 取得資料庫內容fetchall=False，只抓第1筆3-1流程的就好
            statusapi = 31
            command = 'select authcode, sandboxmode, amount, customerid, tradeseq, mycardtradeno, factradeseq, currency, paymenttype from mycardhistory where factradeseq="{0}" and statusapi="{1}"'.format(
                FacTradeSeq, statusapi)
            datalen, data = await self.getdbdata("get_mycardhistory_AuthCode_SandBoxMode", command, fetchall=False)
            return data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get AuthCode and SandBoxMode in 3-3 except:{0}'.format(e))
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

            command = 'insert into mycardhistory(statusapi, authcode, returncode, returnmsg, payresult, factradeseq, paymenttype, amount, currency, mycardtradeno, mycardtype, promocode, serialid, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}","{13}")'.format(
                statusapi, AuthCode, ReturnCode, ReturnMsg, PayResult, FacTradeSeq, PaymentType, Amount, Currency,
                MyCardTradeNo, MyCardType, PromoCode, SerialId, insertutcnowdate)
            await self.insertdbdata('mycard_checkMyCardTradeResult', command)
            return True, MyCardTradeNo

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb: insert mycardhistory failed in 3-3 except:{0}'.format(e))
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

            command = 'insert into mycardhistory(statusapi, authcode, returncode, returnmsg, factradeseq, tradeseq, serialid, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}")'.format(
                statusapi, AuthCode, ReturnCode, ReturnMsg, FacTradeSeq, TradeSeq, SerialId, insertutcnowdate)
            await self.insertdbdata('mycard_mycardReturnInvoiceResult', command)
            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb: insert mycardhistory failed in 3-4 except:{0}'.format(e))
            return False

    # 結束3-4後，update member acc 發送點數給玩家 = 更新點數至資料庫
    async def mycard_update_member_point(self, Amount, CustomerId, TradeSeq, MyCardTradeNo, FacTradeSeq, Currency,
                                         PaymentType, redis_obj, cardinfo):
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
                asyncio.ensure_future(
                    self.buycardlevelup_future(apporweb, logintoken, CustomerId, card, redis_obj, cardinfo))

            # 新增請款成功交易資料至3-7階段
            statusapi = 37
            insertutcnowdate = pg_general.getutcnow()  # 目前英國格林威治時間
            command = 'insert into mycardhistory(statusapi, paymenttype, tradeseq, mycardtradeno, factradeseq, customerid, amount, jinsongpoints, currency, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}")'.format(
                statusapi, PaymentType, TradeSeq, MyCardTradeNo, FacTradeSeq, CustomerId, Amount, jinsong_point,
                Currency, insertutcnowdate)
            await self.insertdbdata('mycard_mcresultcheck', command)

            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb: update member points failed in mycard_status point except:{0}'.format(e))
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

            command = 'insert into mycardhistory(statusapi, returncode, returnmsg, facserviceid, factradeseq, insertutcnowdate)values("{0}","{1}","{2}","{3}","{4}","{5}")'.format(
                statusapi, ReturnCode, ReturnMsg, FacServiceId, FacTradeSeq, insertutcnowdate)
            await self.insertdbdata('mycard_mcredeposit', command)
            return True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb: insert mycardhistory failed in 3-6 except:{0}'.format(e))
            return False

    # 3-7-single-get 廠商從資料庫取得單筆交易查詢的時間區間 → 回傳供智冠MyCard查詢
    async def mycard_mcresultcheck_single_get(self, trade_number):
        try:
            # 用卡片號碼查詢
            MyCardTradeNo = trade_number.get("MyCardTradeNo")

            # 取得3-7資料庫內容
            statusapi = 37
            command = 'select * from mycardhistory where mycardtradeno="{0}" and statusapi="{1}"'.format(MyCardTradeNo,
                                                                                                         statusapi)
            part_3_7_datalen, part_3_7_data = await self.getdbdata("mycard_mcresultcheck_single_get", command,
                                                                   fetchall=False)

            return part_3_7_data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb: get single data in 3-7 except:{0}'.format(e))
            return None

    # 3-7-multi-get 廠商從資料庫取得多筆交易查詢的時間區間 → 回傳供智冠MyCard查詢
    async def mycard_mcresultcheck_multi_get(self, datetime_range):
        try:
            # 用起始時間至結束時間查詢
            StartDateTime = datetime_range.get("StartDateTime")
            EndDateTime = datetime_range.get("EndDateTime")

            # 取得3-7資料庫內容
            statusapi = 37
            command = 'select * from mycardhistory where statusapi="{0}" and insertutcnowdate between "{1}" and "{2}"'.format(
                statusapi, StartDateTime, EndDateTime)
            part_3_7_datalen, part_3_7_data = await self.getdbdata("mycard_mcresultcheck_multi_get", command,
                                                                   fetchall=True)

            return part_3_7_data

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb: get multi data in 3-7 except:{0}'.format(e))
            return None

    async def webapi_get_gash_wallet_base64(self, memberid, itemid, amount):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 比對 itemid and amount 是否符合
            command = 'select * from gashwalletinfo where itemcode="{0}"'.format(itemid)
            datalen, data = await self.getdbdata("webapi_get_gash_wallet_base64", command)
            if datalen != 1:
                return result, clientdata

            cashamount = data.get('cashamount')
            if amount != cashamount:
                return result, clientdata

            utcnowdate = pg_general.getutcnow_datetime()
            command = 'insert into gashwalletdeposite(type,memberid,amount,starttime,status,itemcode)values("0","{0}","{1}","{2}","{3}","{4}")'.format(
                memberid, amount, utcnowdate, '0', itemid)

            insertresult, index = await self.insertdbdata('webapi_get_gash_wallet_base64', command)
            if insertresult == True:
                transid = index
                gash_base64 = Gash.Make_Wallet_SendOder(memberid, transid, amount)
                command = 'update gashwalletdeposite set base64="{0}" where transid="{1}"'.format(gash_base64, transid)
                updateresult = await self.updatedbdata('webapi_get_gash_wallet_base64', command)

                clientdata = {
                    "status_code": 0,
                    "base64": gash_base64,
                    "redirecturl": Gash.GASH_ORDER_URL
                }
                result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_get_gash_wallet_base64 except:{0}'.format(e))

        return result, clientdata

    async def webapi_get_gash_point_base64(self, memberid, itemid, amount):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 比對 itemid and amount 是否符合
            command = 'select * from gashpointinfo where itemcode="{0}"'.format(itemid)
            datalen, data = await self.getdbdata("webapi_get_gash_point_base64", command)
            if datalen != 1:
                return result, clientdata

            cashamount = data.get('cashamount')
            if amount != cashamount:
                return result, clientdata

            utcnowdate = pg_general.getutcnow_datetime()
            command = 'insert into gashwalletdeposite(type,memberid,amount,starttime,status,itemcode)values("1","{0}","{1}","{2}","{3}","{4}")'.format(
                memberid, amount, utcnowdate, '0', itemid)

            insertresult, index = await self.insertdbdata('webapi_get_gash_point_base64', command)
            if insertresult == True:
                transid = index
                gash_base64 = Gash.Make_Point_SendOder(memberid, transid, amount)
                command = 'update gashwalletdeposite set base64="{0}" where transid="{1}"'.format(gash_base64, transid)
                updateresult = await self.updatedbdata('webapi_get_gash_wallet_base64', command)

                clientdata = {
                    "status_code": 0,
                    "base64": gash_base64,
                    "redirecturl": Gash.GASH_ORDER_URL
                }
                result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_get_gash_point_base64 except:{0}'.format(e))

        return result, clientdata

    async def webapi_ret_gash_wallet_base64(self, base64, redis_obj, cardinfo):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 解開 base64 data
            xmldict = Gash.decode_b64xml(base64)
            if xmldict is None:
                return result, clientdata

            trans = xmldict.get('TRANS')

            memberid = pg_general.converttype(trans.get('USER_ACCTID'), int)
            transid = pg_general.converttype(trans.get('COID'), int)
            pay_rcode = trans.get('PAY_RCODE')
            pay_status = pg_general.converttype(trans.get('PAY_STATUS'), str)
            amount = pg_general.converttype(trans.get('AMOUNT'), int)
            ip = trans.get('USER_IP')
            # 先 update 那筆單
            utcnowdatetime = pg_general.getutcnow_datetime()
            command = 'update gashwalletdeposite set pay_rcode="{0}",pay_status="{6}",return_base64="{1}",ip="{2}",status="1",endtime="{5}" where status="0" ' \
                      'and memberid = "{3}" and transid="{4}"'.format(pay_rcode, base64, ip, memberid, transid,
                                                                      utcnowdatetime, pay_status)
            updaterows = await self.updatedbdata_affectrows('update gash wallet return data', command)

            if updaterows == 1 and pay_rcode == '0000' and pay_status == 'S':  # 交易成功
                command = 'select gashwalletinfo.*, gashwalletdeposite.itemcode as itemid, gashwalletdeposite.amount as buyamount from gashwalletdeposite,gashwalletinfo ' \
                          'where  gashwalletinfo.itemcode=gashwalletdeposite.itemcode and gashwalletdeposite.transid = "{0}"'.format(
                    transid)

                datalen, data = await self.getdbdata('get gashwalletinfo', command, False, True)
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
                            "otherdata": {"type": "gashwallet", "transid": transid}
                        }
                        asyncio.ensure_future(self.writetransactionlog('web gash wallet buy point', param))

                        # 寫入凍結額度
                        param = {
                            "memberid": memberid,
                            "type": 4,  # gash wallet
                            "amount": pointamount * 100  # 轉成金幣
                        }
                        # asyncio.ensure_future(self.writegiftfreeze('gash wallet deposite', param))

                        # update member acc
                        command = 'update member set point=point+"{0}" where memberid="{1}"'.format(pointamount,
                                                                                                    memberid)
                        updateresult = await self.updatedbdata('update member point', command)

                        # update mmeber card when card <2
                        command = 'update member set card=2 where memberid="{0}" and card<2'.format(memberid)
                        updateresult = await self.updatedbdata('update member level', command)

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

                        result = await redis_obj.hincrby('cardbuy_{}'.format(memberid), datekey, amount)

                        # make level up future
                        if card in [0, 1, 2, 3, 4]:
                            logintoken = await redis_obj.get_value('{}'.format(memberid))
                            apporweb = 1  # 0: app, 1: web
                            asyncio.ensure_future(
                                self.buycardlevelup_future(apporweb, logintoken, memberid, card, redis_obj, cardinfo))

                        clientdata = {
                            "status_code": 0,
                            "showstr": "儲值成功,感謝您使用 Gash錢包購買遊戲點數,您購買的點數 {} 點, 已經存入您 APP 遊戲帳戶,請至 App 將點數轉換成金幣或銀幣進行遊戲 !!".format(
                                pointamount)
                        }

                        # make settle future

                        asyncio.ensure_future(self.Gash_Wallet_Settle_Future(memberid, transid, amount))
            elif updaterows == 1 and pay_status == '0':
                clientdata = {
                    "status_code": 0,
                    "showstr": "儲值未完成, 稍後系統將會幫您確認此筆訂單, 如訂單付款成功, 稍後系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows == 1 and pay_status == 'W':
                clientdata = {
                    "status_code": 0,
                    "showstr": "此筆交易訂單需要再次確認, 稍後系統將會自動為您確認, 如訂單成功付款, 系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows == 0:
                clientdata = {
                    "status_code": 99
                }

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_ret_gash_wallet_base64 except:{0}'.format(e))

        return result, clientdata

    async def webapi_ret_gash_point_base64(self, base64, redis_obj, cardinfo):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"status_code": 1}

            # 解開 base64 data
            xmldict = Gash.decode_b64xml(base64)
            if xmldict is None:
                return result, clientdata

            trans = xmldict.get('TRANS')

            memberid = pg_general.converttype(trans.get('USER_ACCTID'), int)
            transid = pg_general.converttype(trans.get('COID'), int)
            pay_rcode = trans.get('PAY_RCODE')
            pay_status = pg_general.converttype(trans.get('PAY_STATUS'), str)
            amount = pg_general.converttype(trans.get('AMOUNT'), int)
            ip = trans.get('USER_IP')
            # 先 update 那筆單
            utcnowdatetime = pg_general.getutcnow_datetime()
            command = 'update gashwalletdeposite set pay_rcode="{0}",pay_status="{6}",return_base64="{1}",ip="{2}",status="1",endtime="{5}" where status="0" ' \
                      'and memberid = "{3}" and transid="{4}"'.format(pay_rcode, base64, ip, memberid, transid,
                                                                      utcnowdatetime, pay_status)
            updaterows = await self.updatedbdata_affectrows('update gash wallet return data', command)

            if updaterows == 1 and pay_rcode == '0000' and pay_status == 'S':  # 交易成功
                command = 'select gashpointinfo.*, gashwalletdeposite.itemcode as itemid, gashwalletdeposite.amount as buyamount from gashwalletdeposite,gashpointinfo ' \
                          'where  gashpointinfo.itemcode=gashwalletdeposite.itemcode and gashwalletdeposite.transid = "{0}"'.format(
                    transid)

                datalen, data = await self.getdbdata('get gashpointinfo', command, False, True)
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
                            "otherdata": {"type": "gashpoint", "transid": transid}
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
                        command = 'update member set point=point+"{0}" where memberid="{1}"'.format(pointamount,
                                                                                                    memberid)
                        updateresult = await self.updatedbdata('update member point', command)

                        # update mmeber card when card <2
                        command = 'update member set card=2 where memberid="{0}" and card<2'.format(memberid)
                        updateresult = await self.updatedbdata('update member level', command)

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

                        result = await redis_obj.hincrby('cardbuy_{}'.format(memberid), datekey, amount)

                        # make level up future
                        if card in [0, 1, 2, 3, 4]:
                            logintoken = await redis_obj.get_value('{}'.format(memberid))
                            apporweb = 1  # 0: app, 1: web
                            asyncio.ensure_future(
                                self.buycardlevelup_future(apporweb, logintoken, memberid, card, redis_obj, cardinfo))

                        clientdata = {
                            "status_code": 0,
                            "showstr": "儲值成功,感謝您使用 Gash點數購買遊戲點數,您購買的點數 {} 點, 已經存入您 APP 遊戲帳戶,請至 App 將點數轉換成金幣或銀幣進行遊戲 !!".format(
                                pointamount)
                        }

                        # make settle future

                        asyncio.ensure_future(self.Gash_Point_Settle_Future(memberid, transid, amount))
            elif updaterows == 1 and pay_status == '0':
                clientdata = {
                    "status_code": 0,
                    "showstr": "儲值未完成, 稍後系統將會幫您確認此筆訂單, 如訂單付款成功, 稍後系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows == 1 and pay_status == 'W':
                clientdata = {
                    "status_code": 0,
                    "showstr": "此筆交易訂單需要再次確認, 稍後系統將會自動為您確認, 如訂單成功付款, 系統將會自動為您購買的點數加入您的 APP 遊戲帳戶, 請您耐心等候 !!"
                }
            elif updaterows == 0:
                clientdata = {
                    "status_code": 99
                }

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_ret_gash_point_base64 except:{0}'.format(e))

        return result, clientdata

    async def Gash_Wallet_Settle_Future(self, memberid, transid, amount):
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
                    return_transid = pg_general.converttype(data.get('COID'), int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'), int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'), int)
                    if pay_status == 'S' and pay_rcode == '0000' and transid == return_transid and memberid == return_memberid and amount == return_amount:  # 請款成功
                        command = 'update gashwalletdeposite set settlebase64="{0}",settlereturnbase64="{1}",status="2" where transid="{2}"'.format(
                            settlebase64, resultb64, transid)
                        updateresult = await self.updatedbdata('update settle', command)

                await self.Gash_Wallet_Check_Future(memberid, transid, amount)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Wallet_Settle_Future except:{0}'.format(e))
        finally:
            pass

    async def Gash_Point_Settle_Future(self, memberid, transid, amount):
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
                    return_transid = pg_general.converttype(data.get('COID'), int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'), int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'), int)
                    if pay_status == 'S' and pay_rcode == '0000' and transid == return_transid and memberid == return_memberid and amount == return_amount:  # 請款成功
                        command = 'update gashwalletdeposite set settlebase64="{0}",settlereturnbase64="{1}",status="2" where transid="{2}"'.format(
                            settlebase64, resultb64, transid)
                        updateresult = await self.updatedbdata('update settle', command)

                await self.Gash_Point_Check_Future(memberid, transid, amount)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Point_Settle_Future except:{0}'.format(e))
        finally:
            pass

    async def Gash_Wallet_Check_Future(self, memberid, transid, amount):
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
                    return_transid = pg_general.converttype(data.get('COID'), int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'), int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'), int)
                    if pay_status == 'S' and pay_rcode == '0000' and transid == return_transid and memberid == return_memberid and amount == return_amount:  # 查帳成功
                        command = 'update gashwalletdeposite set checkbase64="{0}",checkreturnbase64="{1}",status="3" where transid="{2}"'.format(
                            checkbase64, resultb64, transid)
                        updateresult = await self.updatedbdata('update settle', command)





        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Wallet_Check_Future except:{0}'.format(e))
        finally:
            pass

    async def Gash_Point_Check_Future(self, memberid, transid, amount):
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
                    return_transid = pg_general.converttype(data.get('COID'), int)
                    return_amount = pg_general.converttype(data.get('AMOUNT'), int)
                    return_memberid = pg_general.converttype(data.get('USER_ACCTID'), int)
                    if pay_status == 'S' and pay_rcode == '0000' and transid == return_transid and memberid == return_memberid and amount == return_amount:  # 查帳成功
                        command = 'update gashwalletdeposite set checkbase64="{0}",checkreturnbase64="{1}",status="3" where transid="{2}"'.format(
                            checkbase64, resultb64, transid)
                        updateresult = await self.updatedbdata('update settle', command)





        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:Gash_Point_Check_Future except:{0}'.format(e))
        finally:
            pass

    async def webapi_ecpay_credit_start_purchase(self, ecpaydata):
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

            param = [[
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
            datalen, data = await self.getdbdata('get credit card item', command)
            if datalen != 1:
                raise ('get credit card item erro')

            itemcode = ecpaydata.get('ProductName')
            cashamount = data.get('cashamount')
            pointamount = data.get('pointamount')

            clientdata = {
                "BindingCard": 0,  # 是否記憶信用卡
                "MerchantTradeDate": MerchantTradeDate,
                "PaymentType": "aio",
                "ReturnURL": ECPay.ReturnURL,
                "ChoosePayment": "Credit",
                "EncryptType": 1,
                "MerchantMemberID": ecpaydata.get('memberid'),
                "Redeem": 'Y',
                "MerchantID": ECPay.MerchantID,
                "MerchantTradeNo": 'c' + pg_general.converttype(MerchantTradeNo, str),
                "ItemName": itemcode,
                "UnionPay": 2,
                "TotalAmount": cashamount,
                "TradeDesc": "金爽娛樂遊戲點數",  # urllib.parse.quote_plus("金爽娛樂遊戲點數"),
                "InvoiceMark": 'Y',
                "CustomerAddr": ecpaydata.get('CustomerAddr'),
                "TaxType": '1',
                "CarruerType": ecpaydata.get('CarruerType'),
                "CarruerNum": ecpaydata.get('CarruerNum'),
                "Donation": ecpaydata.get('Donation'),
                "LoveCode": ecpaydata.get('LoveCode'),
                "Print": '1' if ecpaydata.get('CustomerIdentifier') or ecpaydata.get('CustomerName') else '0',
                # 是否要列印發票要判斷
                "InvoiceItemName": "遊戲點數",  # urllib.parse.quote_plus("點數內購"),
                "InvoiceItemCount": '1',
                "InvoiceItemWord": '組',  # urllib.parse.quote_plus("個"),
                "InvoiceItemPrice": pg_general.converttype(cashamount, str),
                "InvoiceItemTaxType": '1',
                "DelayDay": 0,
                "InvType": '07',
                "RelateNumber": 'creditcard' + pg_general.converttype(MerchantTradeNo, str),  # 發票不可重複隨機碼
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

        return result, clientdata

    async def writegashwalleterrorlog(self, transid, memberid, amount, type, param):
        try:
            logtimeutc = pg_general.getutcnow()

            base64 = param.get('base64')
            returnbase64 = param.get('returnbase64')

            command = 'insert into gashwalleterror (transid,memberid,logtime,type,amount,base64,returnbase64) values' \
                      '(%s,%s,%s,%s,%s,%s,%s)'

            insertparam = []
            insertparam.append([transid, memberid, logtimeutc, type, amount, base64, returnbase64])

            insertresult, insertindex = await self.insertdbdata('insert into gashwalleterrorlog', command, many=True,
                                                                manydata=insertparam)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writegashwalleterrorlog except:{0}'.format(e))

    async def saveloginuid(self, logintoken, memberid, param):
        try:

            uid_g = param.get('uid_g')
            uid_s = param.get('uid_s')

            command = 'update member set uid_g="{0}",uid_s="{1}" where memberid = "{2}"'.format(uid_g, uid_s, memberid)
            updateresult = await self.updatedbdata(logintoken, command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:saveloginuid except:{0}'.format(e))

    async def webapi_add_comment(self, memberid, typeid, content):
        try:
            logtime = pg_general.getutcnow_datetime()

            command = 'insert into webcommentlog(logtime,typeid,status,content,memberid) values("{0}","{1}","{2}","{3}","{4}")'.format(
                logtime, typeid, 0, content, memberid)
            insertresult = await self.insertdbdata('insert web comment', command)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:webapi_add_comment except:{0}'.format(e))

    async def testgoogleiapconfirm(self):
        try:
            response_data = GOOGLE_IAP_SERVICE.purchases().products().get(packageName=GOOGLE_IAP_BUNDLE_ID,
                                                                          productId="shopmall_02",
                                                                          token="mlohliddmhghoeonjklhoegk.AO-J1Oyj77u0dO9EnIpqdnggZz4N5YRGf5Xyzvduqv2iuZ8XIKzoNg0dZ8KPWmBQspj2mPysZXs9tsHPGmn6gR20MyV6uUaKPfmXbK_VMM292AQnicO_WDqfkaAy3MB8OW4QnIADU2_A").execute()
        except Exception as e:
            print(e)
        pass

    async def webapi_ecpay_credit_order_result(self, redis_obj, cardinfo, orderresultdata):
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
            command = 'update creditcarddeposite set order_result=\'{0}\',status="{2}" where transid="{1}"'.format(
                json.dumps(orderresultdata), transid, RtnCode)
            updateresult = await self.updatedbdata('write creditcarddeposite order_result', command)

            # 抓原始單 比對是否與原始單 內容相同
            checkoriginal = False
            command = 'select creditcarddeposite.memberid,creditcarddeposite.Amount,creditcardinfo.cashamount,creditcardinfo.pointamount ' \
                      'from creditcarddeposite,creditcardinfo where creditcarddeposite.transid = "{0}" and creditcardinfo.itemcode=creditcarddeposite.ProductNum'.format(
                transid)
            datalen, data = await self.getdbdata('get creditcarddeposite 2', command)
            if datalen == 1:
                memberid = data.get('memberid')
                Amount = data.get('Amount')
                cashamount = data.get('cashamount')
                pointamount = data.get('pointamount')
                if Amount == pg_general.converttype(TradeAmt, int) == cashamount:
                    checkoriginal = True

            checkmacvalue_again = ecpay_payment_sdk.generate_check_value(orderresultdata)
            if checkmacvalue_again != CheckMacValue or RtnCode != '1' or checkoriginal == False:
                clientdata = {
                    "status_code": 1,
                    "showstr": "購買此商品失敗!!"
                }
            else:
                # update point to member account
                command = 'update member set point=point+"{0}" where memberid = "{1}"'.format(pointamount, memberid)
                updateresult2 = await self.updatedbdata('update member point', command)

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
                    "amount": pg_general.converttype(TradeAmt, int),
                    "otherdata": {"type": "webcreditcard", "transid": transid}
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

        return result, clientdata

    async def getmemberinfolessdata(self, redis_obj, logintoken, memberid, findmemberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {
                "result": 1
            }
            command = 'select nickname,avatar from member where memberid = "{0}"'.format(findmemberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                nickname = data.get('nickname')
                avatar = data.get('avatar')

                clientdata = {
                    "result": 0,
                    "memberid": findmemberid,
                    "nickname": nickname,
                    "avatar": avatar
                }

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getmemberinfolessdata except:{0}'.format(e))

        return result, clientdata

    async def getboxinfo(self, redis_obj, logintoken, memberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'select dayamount,cost,goldpossible,member.todayboxtimes,member.silvercredit from boxsetting,member where memberid = "{0}"'.format(
                memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen > 0:
                dayamount = data.get('dayamount')
                goldpossible = data.get('goldpossible')
                cost = json.loads(data.get('cost'))
                todayboxtimes = data.get('todayboxtimes')
                silvercredit = data.get('silvercredit')
                if None in [dayamount, goldpossible, cost, todayboxtimes]:
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

        return result, clientdata

    async def buybox(self, redis_obj, logintoken, memberid, item):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result": 1}

            command = 'select boxsetting.*,member.silvercredit,member.todayboxtimes from boxsetting,member ' \
                      'where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)

            todayboxtimes = data.get('todayboxtimes')
            silvercredit = data.get('silvercredit')

            dayamount = data.get('dayamount')
            boxweight = json.loads(data.get('boxweight'))
            takeweight = json.loads(data.get('takeweight'))
            cost = json.loads(data.get('cost'))

            # check all data
            if None in [todayboxtimes, silvercredit, dayamount, boxweight, takeweight, cost]:
                raise Exception('buybox data error 1 ')

            goldboxweight = boxweight.get('gold')
            silverboxweight = boxweight.get('silver')
            take1weight = takeweight.get('take1')
            take10weight = takeweight.get('take10')
            cost1 = cost.get('cost1')
            cost10 = cost.get('cost10')

            if None in [goldboxweight, silverboxweight, take1weight, take10weight, cost1, cost10]:
                raise Exception('buybox data error 2')

            if item not in [0, 1]:
                raise Exception('item is error')

            # 今天次數是否已經購買完
            if todayboxtimes >= dayamount and item == 0:
                result = pg_general.Apiresult.success
                return result, clientdata

            if todayboxtimes + 10 > dayamount and item == 1:
                result = pg_general.Apiresult.success
                return result, clientdata

            #  看銀幣是否足夠
            if item == 0:  # take1
                if silvercredit < cost1:
                    result = pg_general.Apiresult.success
                    return result, clientdata
            else:  # take 10
                if silvercredit < cost10:
                    result = pg_general.Apiresult.success
                    return result, clientdata

            if item == 0:  # take 1
                templist = []
                for item in take1weight:
                    tempvalue = item.get('value')
                    tempweight = item.get('weight')
                    for _ in range(tempweight):
                        templist.append(tempvalue)

                random.random()
                takechoice = random.choice(templist)

                if takechoice == 1:  # 金寶相
                    templist2 = []
                    for tempitem in goldboxweight:
                        tempvalue = tempitem.get('value')
                        tempweight = tempitem.get('weight')
                        for _ in range(tempweight):
                            templist2.append(tempvalue)
                else:  # 銀寶箱
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
                          'where memberid = "{2}"'.format(takeboxvalue, cost1, memberid)
                upateresult = await self.updatedbdata(logintoken, command)

                # get silvercredit,credit,
                command = 'select credit,silvercredit from member where memberid="{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                aftersilvercredit = data.get('silvercredit')
                aftercredit = data.get('credit')

                clientdata = {
                    "result": 0,
                    "getgoldcredit": takeboxvalue,
                    "silvercredit": aftersilvercredit,
                    "credit": aftercredit,
                    "boxresult": [{"type": takechoice, "amount": takeboxvalue}]

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

            elif item == 1:  # take 10
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
                                templist2.append((1, tempvalue))
                    else:  # 銀寶箱
                        templist2 = []
                        for tempitem in silverboxweight:
                            tempvalue = tempitem.get('value')
                            tempweight = tempitem.get('weight')
                            for _ in range(tempweight):
                                templist2.append((0, tempvalue))

                    random.random()
                    takebox = random.choice(templist2)
                    takeboxvalue = takebox[1]
                    takeboxtype = takebox[0]
                    getgoldcredit += takeboxvalue
                    boxresult.append({"type": takeboxtype, "amount": takeboxvalue})

                if item == 0:
                    addtimes = 1
                elif item == 1:
                    addtimes = 10
                # update member
                command = 'update member set credit=credit+"{0}",todayboxtimes=todayboxtimes+"{3}",silvercredit=silvercredit-"{1}" ' \
                          'where memberid = "{2}"'.format(getgoldcredit, cost10, memberid, addtimes)
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

        return result, clientdata

    async def skiptutorial(self, redis_obj, logintoken, memberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result": 0}

            command = 'update member set tutorialbetfinish ="3" where memberid = "{0}"'.format(memberid)
            updateresult = await self.updatedbdata(logintoken, command)

            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:skiptutorial except:{0}'.format(e))

        return result, clientdata

    async def gettutorialguide(self, redis_obj, logintoken, memberid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {}

            command = 'select * from guidesetting order by posindex'
            datalen, data = await self.getdbdata(logintoken, command, True)
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

        return result, clientdata

    async def joinfishgame(self, redis_obj, logintoken, memberid, hallid, gameid):
        try:
            result = pg_general.Apiresult.connectdberror
            clientdata = {"result": 1}

            # get member level data
            command = 'select level from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata(logintoken, command)
            if datalen != 1:
                return result, clientdata
            level = data.get('level')
            if level < 5:
                el = 1
            elif level < 25:
                el = 2
            else:
                el = 3

            if hallid == 0:  # gold
                host_id = env_setting.PS_HOST_ID
                gametype = 3
                hallkey = 'g'
            elif hallid == 1:  # silver
                host_id = env_setting.PS_HOST_ID_S
                gametype = 4
                hallkey = 's'
            else:
                return result, clientdata

            # call createplayer
            result = await self.call_gameapi_createplay(logintoken, memberid, host_id)
            if result == False:
                return result, clientdata

            result = await self.call_gameapi_transferAllCreditToGame(logintoken, memberid, host_id, hallid)
            if result == False:
                return result, clientdata

            # set redis dirtyfish
            await redis_obj.hset('dirtyfish', '{}_{}_{}'.format(hallkey, gameid, memberid), 1)
            await redis_obj.set_value('fish_{}_{}_{}'.format(hallkey, gameid, memberid), 1, 15)

            access_token = 'fish*****{}'.format(logintoken)
            # write membergamelog
            nowutctime = pg_general.getutcnow()
            command = 'insert into membergamelog(memberid, gameid, joingametime, logintoken,gametype,seatnum) values("{0}", "{1}", "{2}", "{3}","{4}","{5}")'.format(
                memberid, gameid, nowutctime, logintoken, gametype, 0)
            updateresult, dataindex = await self.insertdbdata(logintoken, command)
            if updateresult == True:

                # get fish launch url
                fishurl = await self.call_gameapi_getFishLaunchUrl(logintoken, memberid, host_id, gameid, access_token)
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

        return result, clientdata

    async def call_gameapi_createplay(self, logintoken, memberid, host_id):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:call_gameapi_createplay host_id:{},logintoken:{},memberid:{}'.format(host_id,
                                                                                                                logintoken,
                                                                                                                memberid))

            result = False

            # call createplay
            url = env_setting.PS_API_SERVER_URL + 'funds/createplayer/?host_id={}&member_id={}&purpose=1'.format(
                host_id, 'fish_{}'.format(memberid))

            errcount = 0
            for _ in range(3):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=60) as response:
                        if response.status == 200:
                            data = await response.text()
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'call_gameapi_createplay response:{},logintoken:{},url:{}'.format(data,
                                                                                                                  logintoken,
                                                                                                                  url))
                            result = True
                            break
                        else:
                            errcount += 1
                            await asyncio.sleep(0)
            if errcount >= 3:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:call_gameapi_createplay error errcount:{0}'.format(errcount))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_createplay except:{0}'.format(e))

        return result

    async def call_gameapi_transferAllCreditToGame(self, logintoken, memberid, host_id, hallid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:call_gameapi_transferAllCreditToGame logintoken:{},memberid:{},host_id:{}:hallid:{}'.format(
                                    logintoken, memberid, host_id, hallid))
            result = False

            # get credit
            if hallid == 0:  # gold
                command = 'select credit from member where memberid = "{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                if datalen != 1:
                    return result
                creditamount = data.get('credit')
                if creditamount > 0:
                    # 扣款
                    command = 'update member set credit = credit - "{0}" where memberid ="{1}" and credit >= "{0}"'.format(
                        creditamount, memberid)
                    affectrows = await self.updatedbdata_affectrows(logintoken, command)
                    if affectrows != 1:
                        return result
                elif creditamount == 0:
                    pass
                else:
                    raise Exception('creditamount < 0')
                amount = creditamount
                amount_silver = 0
            elif hallid == 1:  # silver
                command = 'select silvercredit from member where memberid = "{0}"'.format(memberid)
                datalen, data = await self.getdbdata(logintoken, command, False, True)
                if datalen != 1:
                    return result
                creditamount = data.get('silvercredit')
                if creditamount > 0:
                    # 扣款
                    command = 'update member set silvercredit = silvercredit -"{0}" where memberid="{1}" and silvercredit >= "{0}"'.format(
                        creditamount, memberid)
                    affectrows = await self.updatedbdata_affectrows(logintoken, command)
                    if affectrows != 1:
                        return result
                elif creditamount == 0:
                    pass
                else:
                    raise Exception('creditamount < 0')
                amount = 0
                amount_silver = creditamount
            else:  # other error
                return result

            # make transaction log and
            transtime = pg_general.getutcnow_datetime()
            type = pg_general.transactiontype.depositefishgame
            otherdata = 'fishgame deposite'
            command = 'insert into transaction (transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata) values ' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime, memberid, memberid, type, amount,
                                                                           amount_silver, otherdata)
            updateresult, txn_id = await self.insertdbdata(logintoken, command)

            if creditamount == 0:
                return True  # 如果要轉的分數 ==0, 不用轉
            # call funds transfer to ps
            url = env_setting.PS_API_SERVER_URL + 'funds/deposit/?host_id={}&member_id=fish_{}&txn_id={}&amount={}&purpose=1'.format(
                host_id, memberid, txn_id, creditamount)
            errcount = 0
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response:
                            if response.status == 200:
                                data = await response.json()
                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                    'call_gameapi_transferAllCreditToGame response:{},logintoken:{},url:{}'.format(
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
                else:
                    result = False
                    raise Exception('response not 200:{}'.format(json.dumps(data)))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_transferAllCreditToGame except:{0}'.format(e))

        return result

    async def call_gameapi_transferAllCreditToHost(self, logintoken, memberid, host_id, hallid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:call_gameapi_transferAllCreditToHost logintoken:{},memberid:{},host_id:{},hallid:{}'.format(
                                    logintoken, memberid, host_id, hallid))

            # make transaction log and get txn_id
            transtime = pg_general.getutcnow_datetime()
            type = pg_general.transactiontype.withdrawfishgame
            otherdata = 'fishgame withdraw'
            command = 'insert into transaction (transtime,frommemberid,tomemberid,type,amount,amount_silver,otherdata) values ' \
                      '("{0}","{1}","{2}","{3}","{4}","{5}","{6}")'.format(transtime, memberid, memberid, type, 0,
                                                                           0, otherdata)
            updateresult, txn_id = await self.insertdbdata(logintoken, command)

            url = env_setting.PS_API_SERVER_URL + 'funds/withdrawall/?host_id={}&member_id=fish_{}&txn_id={}&purpose=1'.format(
                host_id, memberid, txn_id, )
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
                    if hallid == 0:
                        amount = data.get('amount')
                        amount_silver = 0
                    elif hallid == 1:
                        amount = 0
                        amount_silver = data.get('amount')
                    # update transaction log amount or amount_silver
                    command = 'update transaction set amount="{0}",amount_silver="{1}" where transactionindex = "{2}"'.format(
                        amount, amount_silver, txn_id)
                    updateresult = await self.updatedbdata_affectrows(logintoken, command)

                    # update member credit and silvercredit
                    command = 'update member set credit= credit+"{0}" ,silvercredit = silvercredit+"{1}" where memberid = "{2}"'.format(
                        amount, amount_silver, memberid)
                    updateresult = await self.updatedbdata_affectrows(logintoken, command)
                else:
                    result = False
                    raise Exception('response not 200:{}'.format(json.dumps(data)))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_transferAllCreditToHost except:{0}'.format(e))

    async def call_gameapi_getFishLaunchUrl(self, logintoken, memberid, hostid, gameid, access_token):
        try:
            url = env_setting.PS_GETLAUNCHURL_FISH.format(hostid, gameid, 'zh-TW', access_token)
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

    async def _confirm_no_duplicate_room(self, logintoken, redis_obj, member_id):
        try:
            club_name = await redis_obj.hget('play_room_record', member_id)
            if club_name is not None:
                await self.leave_room(member_id, logintoken, redis_obj, club_name.split("_")[1],
                                      club_name.split("_")[3])
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:_confirm_no_duplicate_room club_name:{0}'.format(club_name))