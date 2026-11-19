import asyncio
import aiomysql
import os
import env_setting
import pg_general
import random
import json
from datetime import timedelta, datetime
import avatar
from pg_redis import PGRedis , DEFAULT_EXPIRE_SECONDS
import aiohttp.web
from pg_general import SendMsgType
import pg_fcm

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


if env_setting.LOCAL_SERVER ==True:
    APISERVERURL = 'http://localhost:81/jinsong/servicetouser/'
    APISERVER_CHANNEL_CHAT_URL = 'http://localhost:81/sendchannelchat/2/1234/?channelindex={}&type=0&content={}&memberid={}&nickname={}&avatar={}'
else:
    if env_setting.PRODUCTION_MODE == True:
        APISERVERURL = 'http://production-jinsong-apiserver.playgems.net:81/jinsong/servicetouser/'
        APISERVER_CHANNEL_CHAT_URL = 'http://production-jinsong-apiserver.playgems.net:81/sendchannelchat/2/1234/?channelindex={}&type=0&content={}&memberid={}&nickname={}&avatar={}'
    else:
        APISERVERURL = 'http://10.140.0.36:81/jinsong/servicetouser/'
        APISERVER_CHANNEL_CHAT_URL = 'http://10.140.0.36:81/sendchannelchat/2/1234/?channelindex={}&type=0&content={}&memberid={}&nickname={}&avatar={}'



if env_setting.LOCAL_SERVER == True:
    PS_API_SERVER_URL = 'https://dev-api.iplaystar.net/'
    PS_UNCOMPLETEGAME_URL = 'https://dev-api.iplaystar.net/feed/uncompletedgames?host_id={0}&member_id={1}'
    PS_FORCE_DELETE_GAME = 'https://dev-api.iplaystar.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
else:
    if env_setting.PRODUCTION_MODE == True:
        PS_API_SERVER_URL = 'http://pg-api.playgems.net/'
        PS_UNCOMPLETEGAME_URL = 'http://pg-api.playgems.net/feed/uncompletedgames?host_id={0}&member_id={1}'
        PS_FORCE_DELETE_GAME = 'http://pg-api.playgems.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
    else:
        PS_API_SERVER_URL = 'https://dev-api.iplaystar.net/'
        PS_UNCOMPLETEGAME_URL = 'https://dev-api.iplaystar.net/feed/uncompletedgames?host_id={0}&member_id={1}'
        PS_FORCE_DELETE_GAME = 'https://dev-api.iplaystar.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'

PREFIX = 'PG'
PREFIX_S = 'PGS'


if env_setting.PRODUCTION_MODE == True:
    PS_HOST_ID = '2fa00c5c09708683f0dc7fe5cd9a8e7c'
    PS_HOST_ID_S = '12c68ff93b5607c5465413b403aaa8d2'
    PS_HOST_ID_T = '15b41411999301f5a178af526f31cb14'
else:
    PS_HOST_ID = '9f6301a3d76cdb56de4b747ecc999e6b'
    PS_HOST_ID_S = 'a7f2403adb0fd1fb885828b253f709cf'
    PS_HOST_ID_T = '486b194456a1b202254493db18894350'





# if env_setting.PRODUCTION_MODE == True:
#     CLOUDSQL_CONNECTION_NAME = 'playgemsforfunbackend:us-east1:production-slotwar'
#     CLOUDSQL_CONNECTION_NAME_READ = 'playgemsforfunbackend:us-east1:production-slotwar-replica'
# else:
#     CLOUDSQL_CONNECTION_NAME = 'playgemsforfunbackend:asia-east1:slotbackend'
#     CLOUDSQL_CONNECTION_NAME_READ = 'playgemsforfunbackend:asia-east1:slotbackend-replica'

class PG_ASQLDB:

    async def createpool(self):
        if not env_setting.LOCAL_SERVER:
            # cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)
            # cloudsql_unix_socket_read = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME_READ)
            # self.pool = await aiomysql.create_pool(unix_socket=cloudsql_unix_socket, port=3306, user=DB_USER,
            #                                        password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
            # self.pool_read = await aiomysql.create_pool(unix_socket=cloudsql_unix_socket_read, port=3306, user=DB_USER,
            #                                        password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
            self.pool = await aiomysql.create_pool(host=DB_HOST, port=3306, user=DB_USER,
                                                   password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

            self.pool_read = await aiomysql.create_pool(host=DB_HOST_READ, port=3306, user=DB_USER,
                                                        password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
        else:
            self.pool = await aiomysql.create_pool(host=DB_HOST, port=3306, user=DB_USER,
                                                   password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

            self.pool_read = await aiomysql.create_pool(host=DB_HOST_READ, port=3306, user=DB_USER,
                                                   password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

    async def closepool(self):
        await self.pool.close()
        await self.pool.wait_closed()

        await self.pool_read.close()
        await self.pool_read.wait_closed()

    async def getdbdata(self, logintoken, command=None, fetchall=False,fromwritedb=False):
        datalen = -1
        data = None
        if command == None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:getdbdata:command=None logintoken:{0}".format(logintoken))
            return datalen, data

        connectionpool = None
        if fromwritedb == True:
            self.connectionpool = self.pool
        else:
            self.connectionpool = self.pool_read

        try:
            async with self.connectionpool.acquire() as conn:
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

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getdbdata exception:{0}, command:{1}, logintoken:{2}'.format(e, command,
                                                                                                        logintoken))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_asqldb:getdbdata:finally datalen:{0}, logintoken:{1}".format(datalen, logintoken))
            return datalen, data

    async def insertdbdata(self, logintoken, command=None,many=False,manydata=[]):
        result = False
        index = 0
        if command == None:
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
    async def callproc(self, logintoken, command=None,insertdata=None):
        result = False
        index = 0
        if command == None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:callproc:command=None logintoken:{0}".format(logintoken))
            return result, index
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        "pg_asqldb:callproc:execute command:{0}, logintoken:{1}".format(command,
                                                                                                            logintoken))
                    kk= json.dumps(insertdata)
                    listkkk =[]
                    listkkk.append(kk)
                    await cur.callproc(command,listkkk)
                   # datarows = await cur.executemany(command)
                    await conn.commit()
                    #index = cur.lastrowid
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
        if command == None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_asqldb:updatedbdata:command={1} logintoken:{0}".format(logintoken,command))
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




    async def get_all_settings(self):
        # 拿到 server 所有的設定
        result = pg_general.Apiresult.connectdberror
        resultdata = {}
        successtimes = 0
        # 抓 setting 裡面的資料
        command = 'select rankminwin, rankminmultipilier,rankdaybonuscountdown,rankdaymultipilierinboxcontent,rankdaywininboxcontent,' \
                  'rankdaymultipilierinboxtitle,rankdaywininboxtitle,rankmonthbonuscountdown,rankmonthmultipilierinboxcontent,' \
                  'rankmonthmultipilierinboxtitle,rankmonthwininboxcontent,rankmonthwininboxtitle ' \
                  ' from setting'
        datalen , data = await self.getdbdata('get_all_setting',command)

        if datalen > 0:
            resultdata ={
                "rankminwin" : data.get('rankminwin'),
                "rankminmultipilier": data.get('rankminmultipilier'),
                "rankdaybonuscountdown": data.get('rankdaybonuscountdown'),
                "rankdaymultipilierinboxcontent": data.get('rankdaymultipilierinboxcontent'),
                "rankdaywininboxcontent": data.get('rankdaywininboxcontent'),
                "rankdaymultipilierinboxtitle": data.get('rankdaymultipilierinboxtitle'),
                "rankdaywininboxtitle": data.get('rankdaywininboxtitle'),
                "rankmonthbonuscountdown": data.get('rankmonthbonuscountdown'),
                "rankmonthmultipilierinboxcontent": data.get('rankmonthmultipilierinboxcontent'),
                "rankmonthmultipilierinboxtitle": data.get('rankmonthmultipilierinboxtitle'),
                "rankmonthwininboxcontent": data.get('rankmonthwininboxcontent'),
                "rankmonthwininboxtitle": data.get('rankmonthwininboxtitle'),

            }
            successtimes = successtimes + 1

        # 抓 setting2 資料
        command = 'select * from setting2'
        datalen , data = await self.getdbdata('get_setting2 data',command)
        if datalen >0:
            resultdata['jpenable'] = data.get('jpenable')
            successtimes = successtimes + 1

        # 抓 所有 cardinfo 資料
        command = 'select * from cardinfo order by card'
        datalen , data = await self.getdbdata('get all card info',command,True)
        if datalen > 0:
            resultdata["cardinfo"] = data.copy()
            successtimes = successtimes + 1

        # 抓所有　game 資料
        command = 'select gameindex,gameid,enable,unlocklevel from game'
        datalen , data = await self.getdbdata('get_all_game_data',command,True)

        if datalen > 0:
            resultdata['gameInfo'] = data
            successtimes = successtimes + 1

        successtimes = successtimes + 1
        # 抓所有 enable 的遊戲數量
        command = 'select count(1) as c1 from game where enable = 1 '
        datalen , data = await self.getdbdata('get all enabled game amount',command)

        if datalen == 1:
            total_enabled_game_amount = data.get('c1')
            resultdata['total_enabled_game_amount'] = total_enabled_game_amount
            successtimes = successtimes + 1

        if successtimes == 6:
            result = pg_general.Apiresult.success

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:get_all_settings return, result:{0},resultdata:{1}'.format(result,resultdata))
        return result , resultdata

    async def get_lobby_server_ips(self):
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'pg_asqldb:get_lobby_server_ips start')
        result = pg_general.Apiresult.connectdberror
        resultdata = []
        try:

            command = 'select ip from lobbyserversetting'
            datalen , data = await self.getdbdata('get_lobby_server_ips',command,True)
            if datalen >0:
                for item in data:
                    resultdata.append(item.get('ip'))
                result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_lobby_server_ips except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_lobby_server_ips return result:{0},resultdata:{1}'.format(result,resultdata))
            return result , resultdata

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

    async def get_last_task_info(self):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:get_last_task_info start')
        result = pg_general.Apiresult.connectdberror
        resultdata = {}

        command = 'select * from taskinfo'
        datalen , data = await self.getdbdata('get_last_task_info',command)

        if datalen > 0 :
            resultdata = {
                "todayranktime":data.get('todayranktime'),
                "todayrankindex": data.get('todayrankindex')
            }
            result = pg_general.Apiresult.success
        elif datalen == 0:
            result = pg_general.Apiresult.dbnodata

        pg_general.writelog(pg_general.PG_LogerLevel.debug,
                            'pg_asqldb:get_last_task_info result:{0},resultdata:{1}'.format(result,resultdata))
        return result , resultdata

    async def savetoredisandmakeranktouser(self,redis_obj,rank_game_list,rankmode):
        ranking = []
        try:

            for item in rank_game_list:
                for temp_key in item.keys():
                    if item[temp_key] == []:    # 新榜單沒資料不用作
                        await redis_obj.del_key(temp_key)
                        continue

                    oldrankdata = await redis_obj.get_json_value(temp_key)
                    newrankdata = [tempitem for tempitem in item[temp_key] if tempitem.get('rank') <=3]

                    if oldrankdata is None or oldrankdata == []:
                        ranking.extend(newrankdata)
                    else:
                        oldrankdata = [tempitem for tempitem in oldrankdata if tempitem.get('rank')<=3]
                        for tempitem in newrankdata:
                            new_rank = tempitem.get('rank')
                            new_ranktype = tempitem.get('ranktype')
                            new_memberid = tempitem.get('memberid')
                            new_amount = tempitem.get('amount')
                            newtempdata = {
                                "memberid": new_memberid,
                                "amount": new_amount
                            }
                            if new_rank == 1:
                                old_temp = [
                                    {
                                        "memberid": oldtempdata.get('memberid'),
                                        "amount": oldtempdata.get('amount')
                                    } for oldtempdata in oldrankdata if oldtempdata.get('rank') ==1 and oldtempdata.get('ranktype') == new_ranktype
                                ]
                                if newtempdata not in old_temp:
                                    ranking.append(tempitem)
                            elif new_rank ==2:
                                old_temp = [
                                    {
                                        "memberid": oldtempdata.get('memberid'),
                                        "amount": oldtempdata.get('amount')
                                    } for oldtempdata in oldrankdata if oldtempdata.get('rank') in [1,2] and oldtempdata.get('ranktype') == new_ranktype
                                ]
                                if newtempdata not in old_temp:
                                    ranking.append(tempitem)
                            elif new_rank ==3:
                                old_temp = [
                                    {
                                        "memberid": oldtempdata.get('memberid'),
                                        "amount": oldtempdata.get('amount')
                                    } for oldtempdata in oldrankdata if oldtempdata.get('rank') in [1,2,3] and oldtempdata.get('ranktype') == new_ranktype
                                ]
                                if newtempdata not in old_temp:
                                    ranking.append(tempitem)




                    result = await redis_obj.set_json_value(temp_key, item[temp_key], DEFAULT_EXPIRE_SECONDS)


            if ranking != [] and rankmode ==1:
                sendmsg = {"type":0, "msg": {"commandid": 3000007,"ranking":ranking}}
                # get lobby server ips
                if env_setting.LOCAL_SERVER == False:
                    command = 'select ip from lobbyserversetting'
                    datalen , data = await self.getdbdata('get all lobby server ips',command,True)
                    if datalen > 0:
                        try:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
                            lobbyserverips = data
                            if lobbyserverips != []:
                                for item in lobbyserverips:
                                    realurl = 'http://{0}/broadcasttoall'.format(item.get('ip'))
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(realurl, json=sendmsg)
                                        if response.status == 200:
                                            data = await response.text()
                                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                'send_to_all_lobbyserver_future response:{0}'.format(data))
                                    await asyncio.sleep(0)

                        except Exception as e:
                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                'send_to_all_lobbyserver , except:{0}'.format(e))
                        finally:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , done')

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'savetoredisandmakeranktouser , except:{0}'.format(e))

    async def get_rank_mode(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:get_rank_mode start')
            rankmode = -1

            command = 'select rankmode from setting2'
            datalen, data = await self.getdbdata('get rankmode from setting2', command)
            if datalen == 1:
                rankmode = data.get('rankmode')


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:get_rank_mode except:{}'.format(e))

        return rankmode

    async def get_bethistory(self,todayrankstarttime,todayrankendtime,todayrankindex,rankminwin,rankminmultipilier,redis_obj,upload_obj,rankmode):
        pg_general.writelog(pg_general.PG_LogerLevel.info,
                            'pg_asqldb:get_bethistory start todayrankstarttime:{0},todayrankendtime:{1},todayrankindex:{2},'
                            'rankminwin:{3},rankminmultipilier:{4}'.format(todayrankstarttime,todayrankendtime,todayrankindex,rankminwin,rankminmultipilier))
        result = pg_general.Apiresult.connectdberror
        resultdata = []
        gametotalrank = []

        try:

            # 抓最後一筆的 bethistory txn_id
            command = 'select max(txn_id) as max_txn_id from bethistory where bettime >="{0}" and bettime <= "{1}"'.format(
                todayrankstarttime, todayrankendtime)
            datalen, data = await self.getdbdata('get bet history max txn_id', command)

            max_txn_id = data.get('max_txn_id')
            if max_txn_id is None:  # 有資料表示 可以產生榜單, 沒資料下面不用做
                result = pg_general.Apiresult.success
                # # check gametodayrank 是否有資料, 有資料就清空
                # command = 'select count(1) as c1 from gametodayrank'
                # datalen , data = await self.getdbdata('get_count_gametodyarank',command)
                # if datalen >0:
                #     if data.get('c1') > 0:
                #         command = 'delete from gametodayrank'
                #         result = await self.updatedbdata('del_gametodayrank',command)
            if datalen < 0 :
                raise ValueError('get bethistory max_txn_id error')


            # 抓章節與 game 相關資料
            command = 'select chapterInfo.chapterid,chapterInfo.gameidlist,game.gameindex,game.gameid,game.rankminibet from chapterInfo,game ' \
                      'where FIND_IN_SET(game.gameindex,chapterInfo.gameidlist) and chapterInfo.chapterenable = 1 and game.enable = 1'
            datalen , data = await self.getdbdata('get_bethistory_chapter_info',command,True)
            if datalen == 0:
                result = pg_general.Apiresult.success
                raise ValueError('chapter info no data')
            elif datalen < 0:
                raise ValueError('chapter info except')

            chapterinfolist = []
            for item in data:
                gamelist = item.get('gameidlist').split(',')

                chapterinfodict ={
                    "posindex": gamelist.index(str(item.get('gameindex'))) + 1,
                    "gameindex": item.get('gameindex'),
                    "gameid": item.get('gameid'),
                    "rankminibet": item.get('rankminibet')
                }
                chapterinfolist.append(chapterinfodict)

            tempgametotalrank = []

            # 抓總和贏分做 gametotalrank
            command = 'select memberid,cast(sum(sumwin) as UNSIGNED) sumwin, nickname,avatar,level,card from (select bethistory.memberid,CAST(sum(bethistory.total_win) as UNSIGNED) as sumwin, ' \
                      ' member.nickname,member.avatar,member.level,member.card from bethistory,member where bethistory.memberid = member.memberid and bettime >="{0}" and bettime <= "{1}"  ' \
                      ' group by bethistory.memberid union all select bethistory_fish_g.memberid,CAST(sum(bethistory_fish_g.win) as UNSIGNED) as sumwin, member.nickname,member.avatar,member.level,member.card ' \
                      ' from bethistory_fish_g,member where bethistory_fish_g.memberid = member.memberid and resulttime >="{0}" and resulttime <= "{1}" group by bethistory_fish_g.memberid) t1 ' \
                      ' group by memberid'.format(todayrankstarttime,todayrankendtime)
            datalen , data = await self.getdbdata('get sum of total_win',command,True)
            if datalen > 0:
                tempgametotalrank = data.copy()



            # 抓 贏分榜單
            command = 'select bethistory.total_bet as total_bet,bethistory.txn_id as txn_id,1 as ranktype,bethistory.memberid,bethistory.total_win as amount,bethistory.gameid,' \
                      'member.nickname,member.avatar,member.level,member.card ' \
                        ' from bethistory,member where bethistory.memberid = member.memberid and bettime >="{0}" and bettime <= "{1}" and total_win>="{3}" ' \
                        ' and txn_id >"{2}"'.format(todayrankstarttime,todayrankendtime,todayrankindex,rankminwin)
            datalen , datarankwin = await self.getdbdata('get_bethistory rank win',command, True)
            if datalen < 0:
                raise ValueError('get win rank error')
            elif datalen > 0:  # 處理 rank win
                for item in chapterinfolist:
                    gameid = item.get('gameid')
                    rankminibet = item.get('rankminibet')
                    temprank = [ i for i in datarankwin if (i.get('gameid')==gameid and i.get('total_bet')>=rankminibet)]  # 要超過設定最小押分
                    # 根據倍數排序
                    newtemprank= sorted(temprank, key=lambda k: (k['amount']),reverse=True)

                    # 拿掉重複的
                    temprankmemberidlist = []
                    tempranklistnew = []
                    if len(newtemprank)> 0:
                        for _item in newtemprank:
                            if _item.get('memberid') not in temprankmemberidlist:
                                temprankmemberidlist.append(_item.get('memberid'))
                                tempranklistnew.append(_item)

                    # 抓最多一百名
                    newtemprank = tempranklistnew[:100]
                    for item_newtemprank in newtemprank:
                        item_newtemprank['rank'] = newtemprank.index(item_newtemprank)+1

                    item['rankwin'] = newtemprank
            elif datalen ==0:   # 如果都沒有 bet history 則加入空 []
                for item in chapterinfolist:
                    item['rankwin'] = []



            # 抓 倍數榜單
            command = 'select bethistory.total_bet as total_bet,bethistory.txn_id as txn_id, 0 as ranktype,bethistory.memberid,bethistory.gameid,' \
                      'member.nickname,member.avatar,member.level,member.card,cast(floor(bethistory.total_win/bethistory.total_bet) as SIGNED)  as amount,' \
                      'bethistory.total_win as total_win ' \
                      ' from bethistory,member where bethistory.memberid = member.memberid and bettime >="{0}" and bettime <= "{1}"' \
                      ' and floor(bethistory.total_win/bethistory.total_bet)>="{3}" ' \
                      ' and txn_id >"{2}"'.format(todayrankstarttime, todayrankendtime,todayrankindex, rankminmultipilier)
            datalen, datamultipilier = await self.getdbdata('get_bethistory rank win', command, True)
            if datalen < 0:
                raise ValueError('get win rank error')
            elif datalen > 0:   # # 處理 rank multipilier


                for item in chapterinfolist:
                    gameid = item.get('gameid')
                    rankminibet = item.get('rankminibet')
                    temprank = [ i for i in datamultipilier if (i.get('gameid')==gameid and i.get('total_bet')>=rankminibet)]  # 要超過設定最小押分
                    newtemprank= sorted(temprank, key=lambda k: (k['amount']),reverse=True)

                    # 拿掉重複的
                    temprankmemberidlist = []
                    tempranklistnew = []
                    if len(newtemprank) > 0:
                        for _item in newtemprank:
                            if _item.get('memberid') not in temprankmemberidlist:
                                temprankmemberidlist.append(_item.get('memberid'))
                                tempranklistnew.append(_item)

                    # 抓最多一百名
                    newtemprank = tempranklistnew[:100]

                    for item_newtemprank in newtemprank:
                        item_newtemprank['rank'] = newtemprank.index(item_newtemprank)+1

                    item['rankmultipilier'] = newtemprank
            elif datalen == 0:      # 如果都沒有 bet history 則加入空 []
                for item in chapterinfolist:
                    item['rankmultipilier'] = []


            newsortedchapterinfolist = sorted(chapterinfolist, key=lambda k: (k['posindex']))



            # 準備要 insert 的資料
            testinsertdata =[]

            rank_game_list = []

            for item in newsortedchapterinfolist:
                temp_json_list = []
                for temprankwin in item['rankwin']:

                    testinsertdata.append({
                        "gameid":temprankwin.get('gameid'),
                        "ranktype":temprankwin.get('ranktype'),
                        "rank":temprankwin.get('rank'),
                        "memberid":temprankwin.get('memberid'),
                        "avatar":temprankwin.get('avatar'),
                        "nickname":temprankwin.get('nickname'),
                        "level":temprankwin.get('level'),
                        "amount":temprankwin.get('amount'),
                        "card": temprankwin.get('card')

                    })
                    temp_json_list.append({
                        "gameid":temprankwin.get('gameid'),
                        "ranktype":temprankwin.get('ranktype'),
                        "rank":temprankwin.get('rank'),
                        "memberid":temprankwin.get('memberid'),
                        "avatar":temprankwin.get('avatar'),
                        "nickname":temprankwin.get('nickname'),
                        "level":temprankwin.get('level'),
                        "amount":temprankwin.get('amount'),
                        "card": temprankwin.get('card')
                    })
                for temprankmultipilier in item['rankmultipilier']:

                    testinsertdata.append({
                        "gameid": temprankmultipilier.get('gameid'),
                        "ranktype": temprankmultipilier.get('ranktype'),
                        "rank": temprankmultipilier.get('rank'),
                        "memberid": temprankmultipilier.get('memberid'),
                        "avatar": temprankmultipilier.get('avatar'),
                        "nickname": temprankmultipilier.get('nickname'),
                        "level": temprankmultipilier.get('level'),
                        "amount": temprankmultipilier.get('amount'),
                        "card": temprankmultipilier.get('card')

                    })
                    temp_json_list.append({
                        "gameid": temprankmultipilier.get('gameid'),
                        "ranktype": temprankmultipilier.get('ranktype'),
                        "rank": temprankmultipilier.get('rank'),
                        "memberid": temprankmultipilier.get('memberid'),
                        "avatar": temprankmultipilier.get('avatar'),
                        "nickname": temprankmultipilier.get('nickname'),
                        "level": temprankmultipilier.get('level'),
                        "amount": temprankmultipilier.get('amount'),
                        "card": temprankmultipilier.get('card')

                    })
                rank_game_list.append({'rank_' + item['gameid'] : temp_json_list})


            # for test
            # result = await self.callproc('callproc','writenewtodayrank',testinsertdata)

            # await redis_obj.set_json_value('rank_gametodayrank',testinsertdata)

            # 將所有龍虎榜紀錄寫入 redis 並且比對 差異化上榜者 通知 user
            asyncio.ensure_future(self.savetoredisandmakeranktouser(redis_obj,rank_game_list,rankmode))

            result = pg_general.Apiresult.success
            resultdata = newsortedchapterinfolist

            # 做 gametotalrank from tempgametotalrank
            if len(tempgametotalrank) > 0:
                tempgametotalrank = sorted(tempgametotalrank, key=lambda k: (k['sumwin']),reverse=True) # 排序
                tempgametotalrank = [item for item in tempgametotalrank if item.get('sumwin') > 0]
                tempgametotalrank = tempgametotalrank[:100] # 取一百名
                tempranknumber = 1
                uploadtotalranklist = []

                for item in tempgametotalrank:
                    gametotalrank.append([
                        tempranknumber,
                        item.get('memberid'),
                        item.get('nickname'),
                        item.get('level'),
                        item.get('card'),
                        item.get('sumwin'),
                        item.get('avatar')
                    ])
                    uploadtotalranklist.append({
                        "rank": tempranknumber,
                        "nickname": item.get('nickname'),
                        "level": item.get('level'),
                        "card": item.get('card'),
                        "sumwin": item.get('sumwin'),
                        "avatar": item.get('avatar'),
                        "memberid": item.get('memberid')
                    })

                    tempranknumber = tempranknumber + 1


                command = 'delete from gametotalrank'
                updateresult = await self.updatedbdata('delete gametotalrank',command)

                command = 'insert into gametotalrank (rank,memberid,nickname,level,card,sumwin,avatar) values ' \
                          '(%s,%s,%s,%s,%s,%s,%s)'
                resultinsert, insertindex = await self.insertdbdata('insert gametotalrank', command, many=True,
                                                              manydata=gametotalrank)

                await redis_obj.set_json_value('gametotalrank',uploadtotalranklist)

                upload_obj.upload_bucket('rankdata/rank_totalrank_live.json', {"rankInfoList":uploadtotalranklist})


            elif len(tempgametotalrank) == 0:
                command = 'delete from gametotalrank'
                updateresult = await self.updatedbdata('delete gametotalrank 2', command)

            if max_txn_id is None:
                max_txn_id = 0

            # 寫入taskinfo , todayrankendtime , max_txn_id
            command = 'update taskinfo set todayranktime="{0}",todayrankindex="{1}"'.format(todayrankendtime,max_txn_id)
            resultupdate = await self.updatedbdata('update taskinfo todayranktime,todayrankindex',command)



        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'get_bethistory , ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'get_bethistory , except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_bethistory result:{0},resultdata:{1}'.format(result,resultdata))
            return result , resultdata

    async def makerichrank(self,redis_obj,upload_obj):
        pg_general.writelog(pg_general.PG_LogerLevel.debug,'pg_asqldb:makerichrank start')
        result = pg_general.Apiresult.connectdberror

        try:
            now = pg_general.getutcnow_nof()
            nowdatetime = pg_general.strtodatetime(now)

            # 先抓之前做過的時間點
            command = 'select richranktime , richranktimediff from taskinfo'
            datalen , data = await self.getdbdata('get_rich_rank_info',command)
            if datalen >0:
                richranktime = data.get('richranktime')  # datetime
                richranktimediff = data.get('richranktimediff')


                # 只顯示最近七天有登入紀錄
                nowutcdatetime = datetime.utcnow()
                filterdate = nowutcdatetime - timedelta(days=7)


                if nowdatetime >= (richranktime + timedelta(seconds=richranktimediff)):  # 時間到才做 榜單
                    command = 'select credit , memberid,avatar,nickname,level,card,activenumber from member where credit >=1000000 and lastlogintime >= "{0}"'.format(filterdate)
                    datalen , data = await self.getdbdata('get_member_for_richrank',command,True)
                    if datalen < 0 :
                        raise ValueError('connecttion db error')
                    elif datalen ==0:
                        result = pg_general.Apiresult.success
                        raise ValueError('no member records')
                    else:
                        data = sorted(data, key=lambda k: (k['credit']),reverse=True)
                        # 只留下前面一百名
                        data = data[:100]

                        rank = 0
                        manydata = []
                        redis_richest_rank_data = []
                        for item in data:
                            item['rank'] = rank + 1
                            rank+=1
                            manydata.append([
                                item.get('rank'),
                                item.get('memberid'),
                                item.get('avatar'),
                                item.get('nickname'),
                                item.get('level'),
                                item.get('credit'),
                                item.get('activenumber'),
                                item.get('card')

                            ])
                            redis_richest_rank_data.append({
                                "rank": item.get('rank'),
                                "memberid": item.get('memberid'),
                                "avatar": item.get('avatar'),
                                "nickname": item.get('nickname'),
                                "level": item.get('level'),
                                "credit": item.get('credit'),
                                "card": item.get('card'),
                                "activenumber": item.get('activenumber'),

                            })

                        # 清除 rich rank table
                        command = 'delete from richrank'
                        result = await self.updatedbdata('clear data from richrank', command)

                        # insert rich rank data
                        command = 'insert into richrank (rank,memberid,avatar,nickname,level,credit,activenumber,card) values ' \
                                  '(%s,%s,%s,%s,%s,%s,%s,%s)'
                        result = await self.insertdbdata('insert rank data to richrank', command, many=True,
                                                         manydata=manydata)

                        # update rich rank task time
                        command = 'update taskinfo set richranktime="{0}"'.format(nowdatetime)
                        result = await self.updatedbdata('update_richrank_task_ranktime',command)

                        # update rich rank to redis
                        await redis_obj.set_json_value('rank_richest',redis_richest_rank_data)
                        rankdata = {"rankInfoList": redis_richest_rank_data}
                        upload_obj.upload_bucket('rankdata/rank_richest.json',rankdata)

                        result = pg_general.Apiresult.success
                else:
                    result = pg_general.Apiresult.success
                    raise ValueError('time not yet')
            else:
                raise ValueError('can not get richrank config')

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.warn, 'pg_asqldb:makerichrank except:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:makerichrank except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:makerichrank result:{0}'.format(result))
            return result

    async def senddailyrankrewardnotification(self,userlist):
        try:
            title = '獎金已發送至App信箱'
            msg = '恭喜您獲得龍虎榜日冠獎金, 快進來領取再次創造奇蹟!!'

            fcmtokenlist = []
            command = 'select fcmtoken from member where memberid in({0}) and fcmtoken not in("0"," ")'.format(','.join(userlist))
            datalen, data = await self.getdbdata('get member fcmtoken',command,True)
            if datalen >0:
                for item in data:
                    fcmtokenlist.append(item.get('fcmtoken'))

                if len(fcmtokenlist)> 0:
                    pg_fcm.send_notification_multiple_device(title,msg,fcmtokenlist)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:senddailyrankrewardnotification except:{0}'.format(e))

    async def sendweeklyrankrewardnotification(self,userlist):
        try:
            title = '獎金已發送至App信箱'
            msg = '恭喜您獲得龍虎榜周冠獎金, 快進來領取再次創造奇蹟!!'

            fcmtokenlist = []
            command = 'select fcmtoken from member where memberid in({0}) and fcmtoken not in("0"," ")'.format(','.join(userlist))
            datalen, data = await self.getdbdata('get member fcmtoken',command,True)
            if datalen >0:
                for item in data:
                    fcmtokenlist.append(item.get('fcmtoken'))

                if len(fcmtokenlist)> 0:
                    pg_fcm.send_notification_multiple_device(title,msg,fcmtokenlist)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:sendweeklyrankrewardnotification except:{0}'.format(e))

    async def sendmonthlyjinsongrewardnotification(self,userlist):
        try:
            title = '獎金已發送至App信箱'
            msg = '恭喜您獲得金爽榜獎金, 大獎永遠屬於您!!'

            fcmtokenlist = []
            command = 'select fcmtoken from member where memberid in({0}) and fcmtoken not in("0"," ")'.format(
                ','.join(userlist))
            datalen, data = await self.getdbdata('get member fcmtoken', command, True)
            if datalen > 0:
                for item in data:
                    fcmtokenlist.append(item.get('fcmtoken'))

                if len(fcmtokenlist) > 0:
                    pg_fcm.send_notification_multiple_device(title, msg, fcmtokenlist)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:sendmonthlyjinsongrewardnotification except:{0}'.format(e))

    async def sendmonthlyrankrewardnotification(self,userlist):
        try:
            title = '獎金已發送至App信箱'
            msg = '恭喜您獲得龍虎榜月冠獎金, 大獎永遠屬於您!!'

            fcmtokenlist = []
            command = 'select fcmtoken from member where memberid in({0}) and fcmtoken not in("0"," ")'.format(','.join(userlist))
            datalen, data = await self.getdbdata('get member fcmtoken',command,True)
            if datalen >0:
                for item in data:
                    fcmtokenlist.append(item.get('fcmtoken'))

                if len(fcmtokenlist)> 0:
                    pg_fcm.send_notification_multiple_device(title,msg,fcmtokenlist)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:senddailyrankrewardnotification except:{0}'.format(e))


    async def makedayranksettle(self,app):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:makedayranksettle start')
        result = pg_general.Apiresult.connectdberror

        rankminwin = app['rankminwin']
        rankminmultipilier = app['rankminmultipilier']
        rankdaybonuscountdown = app['rankdaybonuscountdown']
        rankdaymultipilierinboxcontent = app['rankdaymultipilierinboxcontent']
        rankdaywininboxcontent = app['rankdaywininboxcontent']
        rankdaymultipilierinboxtitle = app['rankdaymultipilierinboxtitle']
        rankdaywininboxtitle = app['rankdaywininboxtitle']

        notificationuserlist= []       # fcmtoken list
        try:

            # 抓 龍虎榜模式設定
            rankmode = await self.get_rank_mode()
            if rankmode ==-1:
                raise Exception('get rankmode error')

            # 先抓 setting.gamedayranksettledate 處理哪一天沒有做
            command = 'select gamedayranksettledate from setting'
            datalen , data = await self.getdbdata('get_setting_gamedayranksettledate',command)

            if datalen ==0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('setting.gamedayranksettledate no data')
            elif datalen <0 :
                raise Exception('setting.gamedayranksettledate db connection error')
            gamedayranksettledate = []
            gamedayranksettledate = data.get('gamedayranksettledate').strip().split(',')
            gamedayranksettledate = [pg_general.strtodate(i).date() for i in gamedayranksettledate if i.strip() != '']

            # 抓是否已經做過 昨天的月份的月榜單結算, 如果做過則不在做
            command = 'select monthrankdone from taskinfo'
            datalen , data = await self.getdbdata('get_monthrankdone',command)
            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('setting2.monthrankdone no data')
            elif datalen < 0:
                raise Exception('setting2.monthrankdone db connection error')

            monthrankdone = data.get('monthrankdone')
            monthrankdone = pg_general.strtomonth(monthrankdone)


            nowdate = pg_general.get_local_nowdatetime().date()
            yesterdaydate = nowdate - timedelta(days=1)

            # 如果昨天的月份已經做過月綁單結算則返回不做
            if yesterdaydate.year == monthrankdone.year and yesterdaydate.month == monthrankdone.month:
                result = pg_general.Apiresult.success
                raise ValueError('month rank already done, no need to do ')


            monthfirstdate = pg_general.strtodate(str(yesterdaydate.year) + '-' + str(yesterdaydate.month) + '-' + '01').date()
            dolistdate = []
            delta = timedelta(days=1)
            startdate = monthfirstdate
            while startdate <= yesterdaydate:
                if startdate not in gamedayranksettledate:
                    temp_starttime , temp_endtime = pg_general.get_date_to_utc_start_end_time(startdate)

                    dolistdate.append({"date":startdate,"starttime":temp_starttime,"endtime":temp_endtime})
                startdate = startdate + delta



            # 抓 rankaward
            command = 'select ranktype,award,promotionid from gamerankaward where ranktime="0"'
            datalen, data = await self.getdbdata('get_rank_award_today', command, True)
            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db_no_rank_award_data')
            elif datalen < 0:
                raise Exception('db_connection_error_rank_award')

            for item in data:
                if item.get('ranktype') == 0:
                    multipilierrankaward = item.get('award').split(',')
                    multipilierrankpromotionid = item.get('promotionid').split(',')
                elif item.get('ranktype') == 1:
                    winrankaward = item.get('award').split(',')
                    winrankpromotionid = item.get('promotionid').split(',')

            # 抓所有 game list from table game
            command = 'select gameid,gamename,rankminibet from game'
            datalen, data = await self.getdbdata('get_all_gameid', command, True)

            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no game list data')
            elif datalen < 0:
                raise Exception("db connection error")

            gameidlist = []
            for item in data:
                gameidlist.append({
                    "gameid": item.get('gameid'),
                    "gamename": item.get('gamename'),
                    "rankminibet": item.get('rankminibet')
                })



            for dotimedate in dolistdate:

                # do day rank
                # get multipilier bet history
                command = 'select bethistory.total_bet as total_bet,"0" as ranktype,cast(floor(bethistory.total_win/bethistory.total_bet) as SIGNED) as amount,' \
                          'bethistory.memberid as memberid,bethistory.gameid as gameid, ' \
                          ' member.nickname as nickname, member.avatar as avatar,member.level as level from bethistory , member where ' \
                            ' member.memberid = bethistory.memberid ' \
                            ' and cast(floor(bethistory.total_win/bethistory.total_bet) as SIGNED) >= "{0}" ' \
                          'and (bethistory.bettime>="{1}" and bethistory.bettime<="{2}")'.format(rankminmultipilier,dotimedate.get('starttime'),dotimedate.get('endtime'))

                datalen , multipilierrankdata = await self.getdbdata('get_yesterday_bet_rank_multipilier',command,True)
                if datalen <0 :
                    raise Exception('db connection error')


                # get win bet history
                command = 'select bethistory.total_bet as total_bet ,"1" as ranktype,bethistory.total_win as amount , bethistory.memberid as memberid, ' \
                            'bethistory.gameid as gameid, member.nickname as nickname , member.avatar as avatar, ' \
                            ' member.level as level from bethistory , member where '    \
                            'bethistory.memberid = member.memberid and bethistory.total_win >="{0}" and (bethistory.bettime>="{1}"' \
                          ' and bethistory.bettime<="{2}")'.format(rankminwin,dotimedate.get('starttime'),dotimedate.get('endtime'))
                datalen , winrankdata = await self.getdbdata('get_yesterday_bet_win_total_win',command,True)
                if datalen <0:
                    raise Exception('db connection error')

                rankgameresultlist = []
                rankgameresult = {}
                for item_gameid in gameidlist:
                    rankgameresult = {
                        "gameid": item_gameid.get('gameid'),
                        "gamename": item_gameid.get('gamename'),
                        "rankminibet": item_gameid.get('rankminibet')
                    }
                    if multipilierrankdata is not None:
                        rankgameresult['gamerank_multipilier'] = [item for item in multipilierrankdata if (item.get('gameid') == item_gameid.get('gameid') and item.get('total_bet')>=item_gameid.get('rankminibet'))]
                    else:
                        rankgameresult['gamerank_multipilier'] = []

                    if winrankdata is not None:
                        rankgameresult['gamerank_win'] = [item for item in winrankdata if (item.get('gameid')==item_gameid.get('gameid') and item.get('total_bet')>=item_gameid.get('rankminibet'))]
                    else:
                        rankgameresult['gamerank_win'] = []
                    if len(rankgameresult['gamerank_multipilier']) > 0:
                        rankgameresult['gamerank_multipilier'] = sorted(rankgameresult['gamerank_multipilier'],
                                                            key=lambda k: k['amount'], reverse=True)

                        # 拿掉重複的
                        temprankmemberidlist = []
                        tempranklistnew = []
                        for _item in rankgameresult['gamerank_multipilier']:

                            if _item.get('memberid') not in temprankmemberidlist:
                                temprankmemberidlist.append(_item.get('memberid'))
                                tempranklistnew.append(_item)


                        # 只留下前面一百名
                        rankgameresult['gamerank_multipilier'] = tempranklistnew[:100]

                        rankindex = 1
                        for item in rankgameresult['gamerank_multipilier']:
                            item['rank'] = rankindex
                            item['gamename'] = item_gameid.get('gamename')
                            if len(multipilierrankaward) >= rankindex:
                                item['award'] = pg_general.converttype(multipilierrankaward[rankindex-1],int)
                                item['promotionid'] = pg_general.converttype(multipilierrankpromotionid[rankindex-1],int)
                            else:
                                item['award'] = 0
                                item['promotionid'] = None

                            rankindex += 1
                    if len(rankgameresult['gamerank_win'])>0:
                        rankgameresult['gamerank_win'] = sorted(rankgameresult['gamerank_win'],key=lambda k:k['amount'],reverse=True)

                        # 拿掉重複的
                        temprankmemberidlist = []
                        tempranklistnew = []
                        for _item in rankgameresult['gamerank_win']:
                            if _item.get('memberid') not in temprankmemberidlist:
                                temprankmemberidlist.append(_item.get('memberid'))
                                tempranklistnew.append(_item)


                        # 只留下前面一百名
                        rankgameresult['gamerank_win'] = tempranklistnew[:100]

                        rankindex = 1
                        for item in rankgameresult['gamerank_win']:
                            item['rank'] = rankindex
                            item['gamename'] = item_gameid.get('gamename')
                            if len(winrankaward)>= rankindex:
                                item['award'] = pg_general.converttype(winrankaward[rankindex-1],int)
                                item['promotionid'] = pg_general.converttype(winrankpromotionid[rankindex-1],int)
                            else:
                                item['award'] = 0
                                item['promotionid'] = None
                            rankindex += 1
                    rankgameresultlist.append(rankgameresult)

                # write to db gamedayranksettle
                command = 'insert into gamedayranksettle (gameid,ranktype,rank,memberid,award,rankdate ) values (%s,%s,%s,%s,%s,%s)'
                param = []
                for item in rankgameresultlist:
                    for j in item['gamerank_multipilier']:
                        if j.get('award') > 0:
                            param.append([
                                j.get('gameid'),
                                j.get('ranktype'),
                                j.get('rank'),
                                j.get('memberid'),
                                j.get('award'),
                                dotimedate.get('date')
                            ])
                    for j in item['gamerank_win']:
                        if j.get('award') > 0:
                            param.append([
                                j.get('gameid'),
                                j.get('ranktype'),
                                j.get('rank'),
                                j.get('memberid'),
                                j.get('award'),
                                dotimedate.get('date')
                            ])

                if len(param)> 0 and rankmode == 1:      # old mode
                    resultinsert,index = await self.insertdbdata('insert_gamedayrankdata',command,many=True,manydata=param)

                    if resultinsert == True:
                        gamedayranksettledate.append(dotimedate.get('date'))
                        gamedayranksettledate.sort()
                        # update to db setting.gamedayranksetupload_buckettledate
                        command = 'update setting set gamedayranksettledate="{0}"'.format(','.join([item.strftime('%Y-%m-%d') for item in gamedayranksettledate ]))
                        resultupdate = await self.updatedbdata('update_setting_gamedayranksettledate',command)

                        # 發 mail 給前三名得獎者
                        param = []
                        command = 'insert into memberinbox (memberid,inboxuri,mailtype,inboxtitle,inboxcontent,receivestate,dateline,promotionid) ' \
                                  'values(%s,%s,%s,%s,%s,%s,%s,%s)'
                        for item_rank_list in rankgameresultlist:
                            gamename = item_rank_list.get('gamename')

                            inboxuri = 'uri'
                            inboxtitle = rankdaymultipilierinboxtitle
                            inboxcontent = rankdaymultipilierinboxcontent
                            receivestate = 1
                            temp0 = pg_general.get_local_nowdatetime().strftime('%Y-%m-%d 23:59:59')
                            temp1 = datetime.strptime(temp0,'%Y-%m-%d %H:%M:%S')
                            dateline = temp1 + timedelta(minutes=rankdaybonuscountdown)
                            # local datetime to utc datetime
                            dateline = pg_general.local_datetime_to_utc_datetime(dateline)

                            for multipilieritem in item_rank_list.get('gamerank_multipilier'):

                                rank = multipilieritem.get('rank')
                                award = multipilieritem.get('award')
                                promotionid = multipilieritem.get('promotionid')
                                memberid = multipilieritem.get('memberid')
                                tempcontent = ''
                                if award >0:
                                    tempcontent = inboxcontent.format(rank,gamename,dotimedate.get('date'))
                                    param.append([memberid,inboxuri,avatar.AVATAR_TOP_HIT,inboxtitle,tempcontent,receivestate,str(dateline),promotionid])
                                    if str(memberid) not in notificationuserlist:
                                        notificationuserlist.append(str(memberid))

                            inboxtitle = rankdaywininboxtitle
                            inboxcontent = rankdaywininboxcontent

                            for winitem in item_rank_list.get('gamerank_win'):
                                rank = winitem.get('rank')
                                award = winitem.get('award')
                                promotionid = winitem.get('promotionid')
                                memberid = winitem.get('memberid')
                                tempcontent = ''
                                if award > 0:
                                    tempcontent = inboxcontent.format(rank,gamename,dotimedate.get('date'))
                                    param.append([memberid,inboxuri,avatar.AVATAR_TOP_WIN,inboxtitle,tempcontent,receivestate,str(dateline),promotionid])
                                    if str(memberid) not in notificationuserlist:
                                        notificationuserlist.append(str(memberid))


                        if len(param) > 0:
                            # 寫入 inbox
                            result_insert_mail , index = await self.insertdbdata('insert_mail',command,many=True,manydata=param)

                            # 發送推播 通知龍虎榜獎金
                            asyncio.ensure_future(self.senddailyrankrewardnotification(notificationuserlist))

                            # 做 member.totaltopmultiplier , member.totaltopwin + 1


                            param0 = ''
                            param1 = ''
                            param2 = []

                            param0_dict = {}
                            param1_dict = {}


                            for game_item in rankgameresultlist:
                                for m_item in game_item.get('gamerank_multipilier'):
                                    if m_item.get('rank') == 1:
                                        memberid = m_item.get('memberid')
                                        if param0_dict.get(memberid) is None:
                                            param0_dict[memberid] = {}
                                            param0_dict[memberid]['count'] = 1
                                        else:
                                            param0_dict[memberid]['count'] +=1
                                        # param0 = param0 + ' WHEN memberid="{0}" THEN (totaltopmultiplier+1)'.format(memberid)
                                        # if ('"'+ str(m_item.get('memberid'))+'"') not in param2:
                                        #     param2.append(('"'+str(m_item.get('memberid'))+'"'))
                                        #
                                for w_item in game_item.get('gamerank_win'):
                                    if w_item.get('rank') ==  1:
                                        memberid = w_item.get('memberid')
                                        if param1_dict.get(memberid) is None:
                                            param1_dict[memberid] = {}
                                            param1_dict[memberid]['count'] = 1
                                        else:
                                            param1_dict[memberid]['count'] += 1
                                        # param1 = param1 + ' WHEN memberid="{0}" THEN (totaltopwin+1)'.format(memberid)
                                        # if ('"'+str(w_item.get('memberid'))+'"') not in param2:
                                        #     param2.append(('"'+str(w_item.get('memberid'))+'"'))

                            for param0_key in param0_dict.keys():
                                param0 = param0 + ' WHEN memberid="{0}" THEN (totaltopmultiplier+{1})'.format(param0_key,param0_dict[param0_key]['count'])
                                param2.append(('"' + str(param0_key) + '"'))

                            param2 = ','.join(param2)
                            command = 'update member set totaltopmultiplier = CASE {0} END where memberid in ({1})'
                            command = command.format(param0,param2)
                            if len(param2)>0:
                                result_update = await self.updatedbdata('update member totaltopmultiplier',command)

                            param2 = []
                            for param1_key in param1_dict.keys():
                                param1 = param1 + ' WHEN memberid="{0}" THEN (totaltopwin+{1})'.format(param1_key,param1_dict[param1_key]['count'])
                                param2.append(('"' + str(param1_key) + '"'))
                            param2 = ','.join(param2)
                            command = 'update member set totaltopwin = CASE {0} END where memberid in ({1})'
                            command = command.format(param1, param2)
                            if len(param2) > 0:
                                result_update = await self.updatedbdata('update member totaltopwin', command)




                        result = pg_general.Apiresult.success

                else:
                    # 沒有可以上榜的資料 但是 update setting.gamedayranksettledate
                    gamedayranksettledate.append(dotimedate.get('date'))
                    gamedayranksettledate.sort()
                    # update to db setting.gamedayranksettledate
                    command = 'update setting set gamedayranksettledate="{0}"'.format(
                        ','.join([item.strftime('%Y-%m-%d') for item in gamedayranksettledate]))
                    resultupdate = await self.updatedbdata('update_setting_gamedayranksettledate', command)

                    if resultupdate == True:
                        result = pg_general.Apiresult.success

                # update setting.gamedayranksettletasktime
                if result == pg_general.Apiresult.success:
                    nowtime = pg_general.getutcnow_datetime()
                    command = 'update setting set gamedayranksettletasktime="{0}"'.format(str(nowtime))
                    resultupdate_gamedayranksettletasktime = await self.updatedbdata('update gamedayranksettletasktime',command)



        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.warn, 'pg_asqldb:makedayranksettle ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:makedayranksettle except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:makedayranksettle result:{0}'.format(result))
            return result

    async def makemonthlivedata(self,app):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:makemonthlivedata start')
        result = pg_general.Apiresult.connectdberror
        try:

            # 抓取 gamedayranksettletasktime
            command = 'select gamedayranksettletasktime from setting'
            datalen , data = await self.getdbdata('get_gamedayranksettletasktime',command)
            if datalen <0:
                raise Exception('connection db error')
            if datalen ==0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            gamedayranksettletasktime = data.get('gamedayranksettletasktime')
            if gamedayranksettletasktime == app['gamedayranksettletasktime']:  # 跟之前做的時間一樣不需要做
                result = pg_general.Apiresult.success
                raise ValueError('time is same,no need to do makemonthlivedata task')

            # get game list
            command = 'select gameid from game'
            datalen , data = await self.getdbdata('get_all_games_list',command,True)
            if datalen <0:
                raise Exception('connection db error')
            if datalen ==0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            gamelist = [{"gameid":item.get('gameid')} for item in data]

            # 取得 gamerankaward
            command = 'select ranktype,award,promotionid from gamerankaward where ranktime = 1'
            datalen , data = await self.getdbdata('get_gamerankaward',command,True)

            if datalen <0:
                raise Exception('connection db error')
            if datalen ==0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            multipilierrankaward = []
            winrankaward = []

            for item in data:
                if item.get('ranktype') ==0:
                    multipilierrankaward = item.get('award').split(',')
                    multipilierrankaward = [int(item) for item in multipilierrankaward]
                elif item.get('ranktype') == 1:
                    winrankaward = item.get('award').split(',')
                    winrankaward = [int(item) for item in winrankaward]

            nowtime = pg_general.getutcnow_datetime()

            # 做這個月的 month rank 次數統計
            command = 'select count(1) as amount,gamedayranksettle.gameid,gamedayranksettle.ranktype,gamedayranksettle.' \
                      'memberid,gamedayranksettle.rankdate,member.level,member.nickname,member.avatar,member.card ' \
                      ' from gamedayranksettle,member where gamedayranksettle.rank ="1" and' \
                      ' gamedayranksettle.memberid = member.memberid group by ranktype,memberid,gameid'

            datalen , data = await self.getdbdata('get_gamedayranksettle',command,True)
            if datalen <0:
                raise Exception('connection db error')
            if datalen ==0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            for gameitem in gamelist:
                gameitem['multipilierrank'] = [item for item in data if item['ranktype']==0 and item['gameid']==gameitem['gameid']]

                if len(gameitem['multipilierrank']) >0:  # 排序
                    gameitem['multipilierrank'] = sorted(gameitem['multipilierrank'], key=lambda k: k['amount'],reverse=True)
                    # 只留下前一百名
                    gameitem['multipilierrank'] = gameitem['multipilierrank'][:100]

                    rankindex = 1
                    for item in gameitem['multipilierrank']:
                        item['rank'] = rankindex
                        if len(multipilierrankaward) >= rankindex:
                            item['award'] = multipilierrankaward[rankindex-1]
                        else:
                            item['award'] = 0
                        rankindex+= 1

                gameitem['winrank'] = [item for item in data if item['ranktype']==1 and item['gameid']==gameitem['gameid']]
                if len(gameitem['winrank']) >0: # 排序
                    gameitem['winrank'] = sorted(gameitem['winrank'],key=lambda k:k['amount'],reverse=True)
                    # 只留下前一百名
                    gameitem['winrank'] = gameitem['winrank'][:100]

                    rankindex = 1
                    for item in gameitem['winrank']:
                        item['rank'] = rankindex
                        if len(winrankaward) >= rankindex:
                            item['award'] = winrankaward[rankindex-1]
                        else:
                            item['award'] =0
                        rankindex+= 1



            param = []
            for gameitem in gamelist:
                for item in gameitem['multipilierrank']:
                    param.append([
                        pg_general.converttype(item.get('gameid'),str),
                        pg_general.converttype(item.get('ranktype'),str),
                        pg_general.converttype(item.get('rank'),str),
                        pg_general.converttype(item.get('memberid'),str),
                        pg_general.converttype(item.get('avatar'),str),
                        pg_general.converttype(item.get('nickname'),str),
                        pg_general.converttype(item.get('level'),str),
                        pg_general.converttype(item.get('amount'),str),
                        pg_general.converttype(item.get('award'),str),
                        pg_general.converttype(item.get('card'),str)

                    ])

                for item in gameitem['winrank']:
                    param.append([
                        pg_general.converttype(item.get('gameid'),str),
                        pg_general.converttype(item.get('ranktype'),str),
                        pg_general.converttype(item.get('rank'),str),
                        pg_general.converttype(item.get('memberid'),str),
                        pg_general.converttype(item.get('avatar'),str),
                        pg_general.converttype(item.get('nickname'),str),
                        pg_general.converttype(item.get('level'),str),
                        pg_general.converttype(item.get('amount'),str),
                        pg_general.converttype(item.get('award'),str),
                        pg_general.converttype(item.get('card'),str)

                    ])

            if len(param) >0:
                # 清除 gamethismonthrank table
                command = 'delete from gamethismonthrank'
                resultdel = await self.updatedbdata('delete_gamethismonthrank',command)

                # 寫入 gamethismonthrank
                command = 'insert into gamethismonthrank (gameid,ranktype,rank,memberid,avatar,nickname,level,amount,award,card) ' \
                          'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                resultinsert , index = await self.insertdbdata('insert_gamethismonthrank',command,many=True,manydata=param)

                app['gamedayranksettletasktime'] = gamedayranksettletasktime

                result = pg_general.Apiresult.success
            else:
                app['gamedayranksettletasktime'] = gamedayranksettletasktime
                result = pg_general.Apiresult.success

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.warn, 'pg_asqldb:makemonthlivedata ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:makemonthlivedata except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:makemonthlivedata result:{0}'.format(result))
            return result





    async def makerankhistorydata(self,app):
        pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:makerankhistorydata start')
        result = pg_general.Apiresult.connectdberror

        rankmonthbonuscountdown = app["rankmonthbonuscountdown"]
        rankmonthmultipilierinboxcontent = app["rankmonthmultipilierinboxcontent"]
        rankmonthmultipilierinboxtitle = app["rankmonthmultipilierinboxtitle"]
        rankmonthwininboxcontent = app["rankmonthwininboxcontent"]
        rankmonthwininboxtitle = app["rankmonthwininboxtitle"]





        try:
            # 抓今天的時間與 setting.gamedayranksettledate 最後一筆資料 比對是否有跨月, 最後一筆資料必須為上個月的最後一天
            # 沒有跨月 則不做下去
            # 如果 setting.gamedayranksettledate 沒有資料也不做下去

            # get setting2.rankmode 是否是 old mode
            rankmode = await self.get_rank_mode()
            if rankmode == -1:
                raise Exception('get rankmode error')
            if rankmode != 1:
                return

            nowdate = pg_general.get_local_date()

            # 抓 排名的 award
            command = 'select ranktype,award, promotionid from gamerankaward where ranktime = 1'
            datalen , data = await self.getdbdata('get_all_award',command,True)

            if datalen <0 :
                raise Exception('db connection erorr')
            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            for item in data:
                if item.get('ranktype') == 0:
                    multipilierrankaward = item.get('award').split(',')
                    multipilierrankpromotionid = item.get('promotionid').split(',')
                elif item.get('ranktype') ==  1:
                    winrankaward = item.get('award').split(',')
                    winrankpromotionid = item.get('promotionid').split(',')


            # 抓 setting.gamedayranksettledate
            command = 'select gamedayranksettledate from setting'
            datalen , data = await self.getdbdata('get_setting_gamedayranksettledate',command)

            if datalen <0 :
                raise Exception('db connection erorr')
            if datalen == 0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            gamedayranksettledate = data.get('gamedayranksettledate')
            if gamedayranksettledate is None:
                raise ValueError('gamedayranksettledate is None')
            elif gamedayranksettledate.strip() == '':
                raise ValueError('gamedayranksettledate = ""')

            gamedayranksettledatelist = gamedayranksettledate.strip().split(',')
            if len(gamedayranksettledatelist) ==0:
                raise ValueError('gamedayranksettledate no data')

            lastdate = pg_general.strtodate(gamedayranksettledatelist[-1]).date()

            # test
            # nowdate=datetime(2019,8,1)
            # lastdate = datetime(2019,7,31)

            if nowdate.month == lastdate.month and nowdate.year == lastdate.year:
                result = pg_general.Apiresult.success
                raise ValueError('month is same, no need to do rank history')
            
            if lastdate.day != pg_general.monthlastday(lastdate):
                result = pg_general.Apiresult.success
                raise ValueError('lastdate is not the last day of month')


            # 抓所有 gamethismonthrank
            command = 'select gamethismonthrank.*,game.gamename as gamename from gamethismonthrank,game where gamethismonthrank.gameid = game.gameid'
            datalane , data = await self.getdbdata('get_gamethismonthrank', command , True)

            if datalen <0:
                raise Exception('connection db error')
            elif datalen ==0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            # 加入 monthdata
            param = []
            monthdata = lastdate.year*100 + lastdate.month
            for item in data:
                item['monthdata'] = monthdata
                param.append([
                    item.get('gameid'),
                    item.get('ranktype'),
                    item.get('rank'),
                    item.get('memberid'),
                    item.get('avatar'),
                    item.get('nickname'),
                    item.get('level'),
                    item.get('amount'),
                    item.get('monthdata'),
                    item.get('card')

                ])

            gamethismonthranklist = data.copy()


            # 寫入 gamehistoryrank
            command = 'insert into gamehistoryrank (gameid,ranktype,rank,memberid,avatar,nickname,level,amount,monthdata,card) ' \
                      'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'

            result , index = await self.insertdbdata('insert_gamehistoryrank',command,many=True,manydata=param)

            # delete all data from gamedayranksettle gamethismonthrank,setting.gamedayranksettledate,setting.gamedayranksettletasktime
            command = 'delete from gamedayranksettle'
            result_del_gamedayranksettle = await self.updatedbdata('delete gamedayranksettle',command)

            command = 'delete from gamethismonthrank'
            result_del_gamethismonthrank = await self.updatedbdata('delte gamethismonthrank',command)

            command = 'update setting set gamedayranksettledate="", gamedayranksettletasktime="1970-01-01"'
            result_update_setting = await self.updatedbdata('update setting',command)

            # 寫入 做過的月份資料 taskinfo.monthrankdone
            monthrankdone = str(lastdate.year)+'-'+ "{:0>2d}".format(lastdate.month)
            command = 'update taskinfo set monthrankdone="{0}"'.format(monthrankdone)
            result_update_taskinfo = await self.updatedbdata('update_taskinfo',command)

            # get all games
            command = 'select gameid from game'
            datalen , data = await self.getdbdata('get_all_games',command,True)

            gamelist = [{"gameid":item.get('gameid')} for item in data]

            # 找出所有 game's monthdata historyrankstart and historyrankend
            command = 'select gameid,min(monthdata) as historyrankstart , max(monthdata) as historyrankend from gamehistoryrank group by gameid'
            datalen , data = await self.getdbdata('get month data',command,True)

            if datalen <0:
                raise Exception('connect db error')
            elif datalen ==0:
                result = pg_general.Apiresult.dbnodata
                raise ValueError('db no data')

            gamehistorystartendlist = [{"gameid":item.get('gameid'),"historyrankstart":item.get('historyrankstart'),
                                        "historyrankend":item.get('historyrankend')} for item in data]

            command = 'update game set historyrankstart= CASE {0} END,historyrankend= CASE {1} END where gameid IN ({2})'
            param0 = ''
            param1 = ''
            param2 = []
            for item in gamehistorystartendlist:
                param0 = param0 + ' WHEN gameid= "{0}" THEN "{1}"'.format(item.get('gameid'),item.get('historyrankstart'))
                param1 = param1 + ' WHEN gameid= "{0}" THEN "{1}"'.format(item.get('gameid'),item.get('historyrankend'))
                #param2 = param2 + '"{0}",'.format(item.get('gameid'))
                if ('"' + str(item.get('gameid')) + '"') not in param2:
                    param2.append(('"' + str(item.get('gameid')) + '"'))


            param2 = ','.join(param2)
            command = command.format(param0,param1,param2)
            result = await self.updatedbdata('update game historyrankstartend',command)

            # 發送 bonus mail 給月冠
            param = []
            command = 'insert into memberinbox (memberid,inboxuri,mailtype,inboxtitle,inboxcontent,receivestate,dateline,promotionid) ' \
                      'values(%s,%s,%s,%s,%s,%s,%s,%s)'

            dateline = pg_general.strtodatetime((nowdate + timedelta(minutes=rankmonthbonuscountdown)).strftime('%Y-%m-%d 23:59:59'))
            # local datetime to utc datetime
            dateline = pg_general.local_datetime_to_utc_datetime(dateline)

            monthlyrankrewarduserlist = []
            for item in gamethismonthranklist:
                memberid = item.get('memberid')
                inboxuri = 'uri'
                receivestate = 1
                gamename = item.get('gamename')
                if item.get('ranktype')==0: # multipilier
                    inboxtitle = rankmonthmultipilierinboxtitle
                    inboxcontent = rankmonthmultipilierinboxcontent.format(item.get('rank'),item.get('gamename'),item.get('amount'))
                    if item.get('rank') <= len(multipilierrankpromotionid):
                        promotionid = multipilierrankpromotionid[item.get('rank')-1]
                        param.append([
                            memberid,
                            inboxuri,
                            avatar.AVATAR_MONTHLY_TOP_HIT,
                            inboxtitle,
                            inboxcontent,
                            receivestate,
                            dateline,
                            promotionid
                        ])
                        if str(memberid) not in monthlyrankrewarduserlist:
                            monthlyrankrewarduserlist.append(str(memberid))

                elif item.get('ranktype') == 1: # top win
                    inboxtitle = rankmonthwininboxtitle
                    inboxcontent = rankmonthwininboxcontent.format(item.get('rank'),item.get('gamename'),item.get('amount'))
                    if item.get('rank') <= len(winrankpromotionid):
                        promotionid = winrankpromotionid[item.get('rank')-1]
                        param.append([
                            memberid,
                            inboxuri,
                            avatar.AVATAR_MONTHLY_TOP_WIN,
                            inboxtitle,
                            inboxcontent,
                            receivestate,
                            dateline,
                            promotionid
                        ])
                        if str(memberid) not in monthlyrankrewarduserlist:
                            monthlyrankrewarduserlist.append(str(memberid))
            if len(param) >0 and rankmode ==1:      # old mode
                result , index = await self.insertdbdata('insert mail for monthly award',command,many=True,manydata=param)

                # 發送推播 通知龍虎榜獎金
                asyncio.ensure_future(self.sendmonthlyrankrewardnotification(monthlyrankrewarduserlist))


            result = pg_general.Apiresult.success


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.warn, 'pg_asqldb:makerankhistorydata ValueError except:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:makerankhistorydata except:{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.debug, 'pg_asqldb:makerankhistorydata result:{0}'.format(result))
            return result






    async def dellobbyserverip(self,ip):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:dellobbyserverip ip:{0}'.format(ip))

            command = 'delete from lobbyserversetting where ip ="{0}"'.format(ip)
            result = await self.updatedbdata('dellobbyserverip',command)
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:dellobbyserverip result:{0}'.format(result))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:dellobbyserverip except:{0}'.format(e))
        finally:
            return result

    async def getfeedback(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getfeedback')
            result = pg_general.Apiresult.connectdberror

            msg = []
            out_msg = ""
            index = ""
            command = 'select feedback.*,member.nickname from feedback,member where feedback.memberid =member.memberid and status is null'
            datalen , data = await self.getdbdata('getfeedback',command,True)
            if datalen>0:

                for  _item in data:
                    msg.append(str(_item.get('memberid'))+','+ _item.get('nickname') + ','+ str(_item.get('time'))+','+_item.get('content'))
                    if index =="":
                        index = str(_item.get('feedbackindex'))
                    else:
                        index = index + ',' + str(_item.get('feedbackindex'))
                if(len(index)>0):
                    command = 'update feedback set status = 0 where feedbackindex in ({})'.format(index)
                    result = await self.updatedbdata('updatefeedback',command)

                if len(msg)>0:
                    out_msg = '\n'.join(msg)


            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getfeedback except:{0}'.format(e))
        finally:
            return result,out_msg

    async def writeconcurrentuser(self,amount):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:writeconcurrentuser')
            result = pg_general.Apiresult.connectdberror

            logtime = pg_general.getutcnow_nof()
            command = 'insert into concurrentuserlog (logtime,users) values("{0}","{1}")'.format(logtime,amount)

            inert_result , index = await  self.insertdbdata("writeconcurrentuser",command)
            if inert_result == True:
                result = pg_general.Apiresult.success

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writeconcurrentuser except:{0}'.format(e))
        finally:
            return result

    async def get_bonus_index_exceed_date_line(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:get_bonus_index_exceed_date_line')
            result = False
            nowdatetime = datetime.utcnow()
            tomorrowdate = str((nowdatetime + timedelta(days=1)).date())

            command = 'select member.fcmtoken from memberinbox, member ' \
                    'where memberinbox.memberid = member.memberid and date(memberinbox.dateline) = "{0}" ' \
                    'and memberinbox.receivestate = 1 and member.fcmtoken != "" group by memberinbox.memberid'.format(tomorrowdate)

            datalen , data = await self.getdbdata('get_bonus_index_exceed_date_line',command,True)

            result = True
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_bonus_index_exceed_date_line ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_bonus_index_exceed_date_line except:{0}'.format(e))
        finally:
            return result , data

    async def del_announcement_task(self):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:del_announcement_task')
            result = False
            nowdatetime = datetime.utcnow()

            command = 'select * from announcement where dateline< "{0}"'.format(nowdatetime)
            datalen , data = await self.getdbdata('del_announcement_task',command,True)

            param = ''
            if datalen >0 :
                for item in data:
                    if param == '':
                        param = "{}".format(item.get('announceindex'))
                    else:
                        param = param + ',"{0}"'.format(item.get('announceindex'))


            if param != '':
                command = 'delete from announcement where announceindex in ({})'.format(param)
                result_del = await self.updatedbdata('del_announcement_task',command)


            result = True
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:del_announcement_task ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:del_announcement_task except:{0}'.format(e))
        finally:
            return result

    async def getchannellist(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getchannellist')
            result = False
            resultdata = {}

            command = 'select channelindex,channelname from channel where enable=1 order by posindex'
            datalen, data = await  self.getdbdata('getchannellist', command, True)

            channellist = []
            if datalen < 1:
                raise ValueError('get channel error')
            channellist = data.copy()

            for item in channellist:
                channelindex = item.get('channelindex')
                # get redis 資料
                redischannellist = await redis_obj.get_all_keys('channel_{0}_*'.format(channelindex))
                item['amount'] = len(redischannellist)

            result = True
            resultdata = {
                "commandid": 3000008,
                "channellist": channellist
            }



        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getchannellist ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getchannellist except:{0}'.format(e))
        finally:
            return result,resultdata

    async def updateofficialactiontoredis(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:updateofficialactiontoredis')
            result = False
            resultdata = {}

            command = 'select content from chatroom_promotion'
            datalen , data = await self.getdbdata('updateofficialactiontoredis',command,True)

            if datalen > 0:
                await redis_obj.set_json_value('chatroom_promotion', data.copy())
            elif datalen ==0:
                await redis_obj.del_key('chatroom_promotion')


            command = 'select content from chatroom_notice'
            datalen , data = await self.getdbdata('updateofficialactiontoredis',command,True)

            if datalen > 0:
                await redis_obj.set_json_value('chatroom_notice', data.copy())
            elif datalen == 0:
                await redis_obj.del_key('chatroom_notice')

            result = True

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateofficialactiontoredis ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:updateofficialactiontoredis except:{0}'.format(e))
        finally:
            return result

    async def makelivegamelist(self,app):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makelivegamelist')
            result = False
            upload_obj = app['uploadobj']

            # get chapterInfo gamelist
            command = 'select gameidlist from chapterInfo where chapterenable = 1 order by chapterid'
            datalen,data = await self.getdbdata('makelivegamelist',command,True)

            if datalen <1:
                raise ValueError('makelivegamelist error')

            gameindexliststr = ''
            for item in data:
                if gameindexliststr == '':
                    gameindexliststr = item.get('gameidlist')
                else:
                    gameindexliststr = gameindexliststr + ',' + item.get('gameidlist')


            command = 'select gameindex,gameid,gamename,resourceuri from game where enable="1" and gameindex in ({0})'.format(gameindexliststr)
            datalen , data = await self.getdbdata('get game list from game',command,True)

            if datalen < 1:
                raise ValueError('get game list error')

            gameitem = []
            gamelistarray = gameindexliststr.split(',')
            for item in gamelistarray:
                for dataitem in data:
                    if item == pg_general.converttype(dataitem.get('gameindex'),str):
                        gameitem.append({
                            "gameid": dataitem.get('gameid') ,
                            "gamename": dataitem.get('gamename'),
                            "gameicon": dataitem.get('resourceuri') + dataitem.get('gameid') + '.png',
                            "type": 1
                        })
                        break

            if len(gameitem)> 0:
                upload_obj.upload_bucket('setting/gameitemlist.json',{"gameitemlist": gameitem})

            result = True

        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makelivegamelist ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makelivegamelist except:{0}'.format(e))
        finally:
            return result


    async def upload_jinsong_rank_data_to_bucket(self,rankdata,upload_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:upload_jinsong_rank_data_to_bucket start')

            rankdatatemp = {"rankInfoList": rankdata}
            upload_obj.upload_bucket('rankdata/rank_jinsongprize_live.json', rankdatatemp)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:upload_jinsong_rank_data_to_bucket except:{}'.format(e))

    async def upload_rank_data_to_bucket(self,rankdata,upload_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:upload_rank_data_to_bucket start')
            result = False

            gamename = rankdata.get('gamename')
            topwin = rankdata.get('topwin')
            topmultipilier = rankdata.get('topmultipilier')

            topwinuploaddata = []
            topmultipilieruploaddata = []

            for gameid,gamename in gamename.items():
                temptopwin = topwin.get(gameid)
                if temptopwin is None:
                    temprankdata = []
                else:
                    temprankdata = temptopwin[:5]       # 只抓前五名
                topwinuploaddata.append({
                    "gameid": gameid,
                    "gamename": gamename,
                    "ranklist": temprankdata
                })
                temptopmultipilier = topmultipilier.get(gameid)
                if temptopmultipilier is None:
                    temprankdata = []
                else:
                    temprankdata = temptopmultipilier[:5]
                topmultipilieruploaddata.append({
                    "gameid": gameid,
                    "gamename": gamename,
                    "ranklist": temprankdata
                })


            rankdatatemp= {"rankInfoList": topwinuploaddata}
            upload_obj.upload_bucket('rankdata/rank_dragon_new_live.json', rankdatatemp)


            rankdatatemp = {"rankInfoList": topmultipilieruploaddata}
            upload_obj.upload_bucket('rankdata/rank_tiger_new_live.json', rankdatatemp)



            result = True
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:upload_rank_data_to_bucket ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:upload_rank_data_to_bucket except:{0}'.format(e))
        finally:
            return result

    async def makeserialtable(self,modeindex,amount):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makeserialtable start')
            result = pg_general.Apiresult.connectdberror

            randwords = ['a','b','c','d','e','f','g','h','i','j','k','m','n','p','q','r','s','t','u','v','w','x','y','z','2','3','4','5','6','7','8','9']

            seriallist = []
            for i in range(amount):
                tempwords = ''
                while(1):
                    for j in range(6):
                        tempwords = tempwords + random.choice(randwords)
                    if tempwords not in seriallist:
                        seriallist.append([modeindex,tempwords])
                        break
            command = 'insert into serialtable(modeindex,serialvalue) values(%s,%s)'
            resultinsert, index = await self.insertdbdata('insert makeserialtable', command, many=True, manydata=seriallist)


            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makeserialtable except:{0}'.format(e))
        finally:
            return result

    async def writeapilog(self,admin,pd,ip,apiname,content):
        try:
            logtime = pg_general.getutcnow_datetime()
            contentstr = json.dumps(content)

            command = 'insert into apilog (logtime,admin,ip,password,apiname,content) values(\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'.format(logtime,admin,ip,pd,apiname,contentstr)
            insertresult = await self.insertdbdata('writeapilog',command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:writeapilog except:{0}'.format(e))





    async def makepromotiontoinbox(self,telebotobj,param):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:makepromotiontoinbox param:{}'.format(param))
            ip = param.get('ip')
            admin = param.get('admin')
            pd = param.get('pd')
            userlist = param.get('userlist')
            title = param.get('title')
            content = param.get('content')
            type = param.get('type')
            amount = param.get('amount')


            if env_setting.PRODUCTION_MODE == False:
                if ip not in ['125.227.113.163','104.199.221.96','127.0.0.1','114.33.71.4']:
                    return {"result": -2}
            else:
                if ip not in ['104.199.221.96','114.33.71.4']:
                    return {"result": -2}
            if amount <=0 or type not in [0,1]:
                return {"result": -3}

            # check api flag if enable
            command = 'select apiflag from setting2'
            datalen , data = await self.getdbdata('get apiflag',command)
            if datalen !=1:
                return {"result": -5}

            apiflag = data.get('apiflag')
            if apiflag == 0:
                return {'result': -6}


            # confirm admin
            command = 'select * from apiadmin where admin="{0}" and pd = "{1}"'.format(admin,pd)
            datalen , data = await self.getdbdata('get apiadmin',command)
            if datalen <1:
                return {"result": -4}

            # get dateline
            todaydate = pg_general.getutcnow_datetime()
            datelinedatetime = todaydate + timedelta(days=5)
            datelinestr = datelinedatetime.date().__str__() + ' 15:59:59'
            if type == 0:
                promotionid = 30
            else:
                if env_setting.PRODUCTION_MODE == False:
                    promotionid = 49
                else:
                    promotionid = 67
            command = 'insert into memberinbox (memberid,mailtype,inboxtitle,inboxcontent,receivestate,dateline,promotionid,credit_award) ' \
                      'values(%s,%s,%s,%s,%s,%s,%s,%s)'
            args = []
            users = userlist.split(',')
            for item in users:
                memberid = pg_general.converttype(item,int)
                args.append([
                    memberid,
                    6,
                    title,
                    content,
                    1,
                    datelinestr,
                    promotionid,
                    amount
                ])

            if len(args)>0:
                resultinsert, index = await self.insertdbdata('insert inbox', command, many=True, manydata=args)

            result = {"result": 0}
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:makepromotiontoinbox param:{}'.format(param))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:makepromotiontoinbox except:{}'.format(e))

        return result

    async def make_bethistory_summary(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:make_bethistory_summary')
            result = False

            # get redis yesterday job
            yesterdaydatestr = (pg_general.get_tw_datetime() -timedelta(days=1)).date().__str__()

            startbettime = (pg_general.get_tw_datetime() -timedelta(days=2)).date().strftime('%Y-%m-%d 16:00:00')
            endbettime = (pg_general.get_tw_datetime() -timedelta(days=1)).date().strftime('%Y-%m-%d 15:59:59')


            # make gold bethistory summary
            command = 'select memberid,sum(bet) bet,sum(win) win,sumdate from (select memberid,sum(total_bet) as bet, ' \
                      'sum(total_win) as win,"{2}" as sumdate from bethistory where bettime between "{0}" and "{1}" group by memberid ' \
                      ' union all select memberid,sum(bet) bet,sum(win) win,"{2}" as sumdate from bethistory_fish_g where ' \
                      'resulttime between "{0}" and "{1}" group by memberid ) t1 group by memberid'.format(startbettime,endbettime,yesterdaydatestr)
            datalen , data = await self.getdbdata('make_bethistory_summary',command,True)


            if datalen >0:
                param = []
                for item in data:
                    param.append([
                        item.get('memberid'),
                        item.get('sumdate'),
                        item.get('bet'),
                        item.get('win')
                    ])
                if len(param)>0:
                    command = 'insert into betsum(memberid,sumdate,bet,win) values(%s,%s,%s,%s)'
                    insertresult = await self.insertdbdata('insert betsum',command,many=True,manydata=param)

            # make silver bethistory summary
            command = 'select memberid,sum(bet) bet,sum(win) win,sumdate from (select memberid,sum(total_bet) as bet, ' \
                      'sum(total_win) as win,"{2}" as sumdate from bethistory_s where bettime between "{0}" and "{1}" group by memberid ' \
                      ' union all select memberid,sum(bet) bet,sum(win) win,"{2}" as sumdate from bethistory_fish_s where ' \
                      'resulttime between "{0}" and "{1}" group by memberid ) t1 group by memberid'.format(startbettime, endbettime, yesterdaydatestr)
            datalen, data = await self.getdbdata('make_bethistory_summary', command, True)


            if datalen > 0:
                param = []
                for item in data:
                    param.append([
                        item.get('memberid'),
                        item.get('sumdate'),
                        item.get('bet'),
                        item.get('win')
                    ])
                if len(param) > 0:
                    command = 'insert into betsum_s(memberid,sumdate,bet,win) values(%s,%s,%s,%s)'
                    insertresult = await self.insertdbdata('insert betsum', command, many=True, manydata=param)

            result = True
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_bethistory_summary ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_bethistory_summary except:{0}'.format(e))
        finally:
            return result

    async def broadcastdowncardmember_future(self,param):
        for item in param:
            if env_setting.LOCAL_SERVER == False:
                lobbyserverip = item.get('lobbyserverip')
            else:
                lobbyserverip = '127.0.0.1'
            sendmsg = {
                "type": SendMsgType.server_to_client,
                "logintoken": item.get('logintoken'),
                "msg": {
                    "commandid": 3000015,
                    "data":{
                        "memberid": item.get('memberid'),
                        "card": item.get('card')
                    }
                }
            }


            try:
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                    'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
                realurl = 'http://{0}/broadcasttoall'.format(lobbyserverip)
                async with aiohttp.ClientSession() as session:
                    response = await session.get(realurl, json=sendmsg)
                    if response.status == 200:
                        data = await response.text()
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            'send_to_all_lobbyserver_future response:{0}'.format(data))
            except Exception as e:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'broadcastdowncardmember_future except:{0}'.format(e))




    async def writecardchangelog(self,param):
        try:
            command = 'insert into cardlevelchangelog (memberid,logtime,oldcard,newcard,memo) values(%s,%s,%s,%s,%s)'
            insertresult = await self.insertdbdata('write card level change log',command,True,param)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, 'pg_asqldb:writecardchangelog Exception : {}'.format(e))

    async def clear_bethistory_daily_data(self,redis_obj,cardinfo):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:clear_bethistory_daily_data')
            result = False

            nowutcdatetime = pg_general.getutcnow_datetime()

            # 調整降級
            # 先把 每個 card >=2 的玩家 memberid  抓出來 然後對這些玩家的 redis cardlevelupdays + 1
            command = 'select memberid,card from member where card >= 3'
            datalen, data = await self.getdbdata('get all member card>=3', command, True,True)

            allprocessmembers = []
            tempcardmember = []
            downcardmemberlist = []
            broadcastmemberlist = []

            insertcardlevelchangelog=[] # [memberid,logtime, oldcard,newcard]

            if datalen >= 1:
                allprocessmembers = [{"memberid":item.get('memberid'),"card": item.get('card')} for item in data]
                tempcardmember = [item.get('memberid') for item in data]
                # change to string
                tempcardmember = list(map(str,tempcardmember))
                for index,item in enumerate(tempcardmember):
                    tempdays = await redis_obj.incr('cardlevelupdays_{}'.format(item))
                    if tempdays >=60:
                        tempcard = allprocessmembers[index].get('card')
                        if tempcard in [3,4]:
                            totalblackbetlist = await redis_obj.hvals('bethistory_gold_{}'.format(item))
                            totalblackcardbuylist = await redis_obj.hvals('cardbuy_{}'.format(item))
                            totalblackbet = sum(list(map(int, totalblackbetlist)))
                            totalblackcardbuy = sum(list(map(int, totalblackcardbuylist)))

                            if totalblackbet < cardinfo[tempcard].get('twomonthaccbet') and totalblackcardbuy < cardinfo[tempcard].get('twomonthaccbuy'):
                                # 降級所以 clear all redis 相關 data
                                await redis_obj.del_key('bethistory_gold_{}'.format(item))
                                await redis_obj.del_key('bethistory_silver_{}'.format(item))
                                await redis_obj.del_key('cardbuy_{}'.format(item))
                                await redis_obj.del_key('cardlevelupdays_{}'.format(item))
                                downcardmemberlist.append(item)
                                insertcardlevelchangelog.append([item,nowutcdatetime,tempcard,tempcard-1,'carddown'])
                        elif tempcard == 5:
                            # 黑卡不會升級, 所以抓她的所有 bet and buy
                            totalblackbetlist = await redis_obj.hvals('bethistory_gold_{}'.format(item))
                            totalblackcardbuylist = await redis_obj.hvals('cardbuy_{}'.format(item))

                            totalblackbet = sum(list(map(int,totalblackbetlist)))
                            totalblackcardbuy = sum(list(map(int,totalblackcardbuylist)))
                            if totalblackbet < cardinfo[5].get('twomonthaccbet') and totalblackcardbuy < cardinfo[5].get('twomonthaccbuy'):
                                # 降級所以 clear all redis 相關 data
                                await redis_obj.del_key('bethistory_gold_{}'.format(item))
                                await redis_obj.del_key('bethistory_silver_{}'.format(item))
                                await redis_obj.del_key('cardbuy_{}'.format(item))
                                await redis_obj.del_key('cardlevelupdays_{}'.format(item))
                                downcardmemberlist.append(item)
                                insertcardlevelchangelog.append([item, nowutcdatetime, tempcard, tempcard - 1,'carddown'])

            if len(insertcardlevelchangelog)> 0:
                asyncio.ensure_future(self.writecardchangelog(insertcardlevelchangelog))

            if len(downcardmemberlist)> 0:
                # update db

                command = 'update member set card = card-1,cardlevelchangetime="{1}" where card>=3 and memberid in ({0})'.format(','.join(downcardmemberlist),nowutcdatetime)
                updateresult = await self.updatedbdata('update member card',command)

                # 抓降級會員是否有在線上 才抓資料 廣播
                checkonlineuserlist = ['online_'+item for item in downcardmemberlist]
                result_checkonlinelist = await redis_obj.mget(checkonlineuserlist)

                for item,boradcastmemberid in zip(result_checkonlinelist,downcardmemberlist):
                    if item is not None:
                        broadcastmemberlist.append(boradcastmemberid)

            # 做廣播
            if len(broadcastmemberlist)>0:
                # get new card level and call broadcast future
                command = 'select memberid,logintoken,card,lobbyserverip from member where memberid in ({0})'.format(','.join(broadcastmemberlist))
                datalen , data = await self.getdbdata('get new card',command,True,True)
                if datalen >0:
                    asyncio.ensure_future(self.broadcastdowncardmember_future(data.copy()))


            # clear bethistory_gold_{} & cardbuy_{} field = days mod 60
            twdatestr = pg_general.get_tw_datetime().date().__str__()
            twnowdate = pg_general.get_tw_datetime().date()
            firstdate = pg_general.get_tw_2020_first_date().date()
            datekey = str((twnowdate - firstdate).days % 60)

            # get all bethistory gold list from redis
            keystr = 'bethistory_gold_*'
            allkeys = await redis_obj.get_all_keys(keystr)
            if len(allkeys)>0:
                for item in allkeys:
                    await redis_obj.hdel(item,datekey)

            # get all bethistory_silver list from redis
            keystr = 'bethistory_silver_*'
            allkeys = await redis_obj.get_all_keys(keystr)
            if len(allkeys)> 0:
                for item in allkeys:
                    await redis_obj.hdel(item,datekey)

            # get all cardbuy_{} from redis
            keystr = 'cardbuy_*'
            allkeys = await redis_obj.get_all_keys(keystr)
            if len(allkeys)> 0:
                for item in allkeys:
                    await redis_obj.hdel(item,datekey)


        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:clear_bethistory_daily_data ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:clear_bethistory_daily_data except:{0}'.format(e))
        finally:
            return result

    async def makesuspenselist(self,upload_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:makesuspenselist')

            # 抓所有 enable =2 or 3 的玩家
            command = 'select nickname,suspensestarttime,suspenseendtime,suspensedesc from member where enable in(2,3)'
            datalen , data = await self.getdbdata('get all enable 2,3 user',command,True)

            if datalen > 0:
                memberlist = []
                for item in data:
                    nickname = item.get('nickname')
                    suspensestarttime = item.get('suspensestarttime')
                    suspenseendtime = item.get('suspenseendtime')
                    suspensedesc = item.get('suspensedesc')
                    if suspensestarttime is not None: # convert to tw time
                        suspensestarttime = suspensestarttime + timedelta(hours=8)
                    if suspenseendtime is not None: # convert to tw time
                        suspenseendtime = suspenseendtime + timedelta(hours=8)


                    memberlist.append({
                        "nickname": nickname,
                        "starttime": suspensestarttime.__str__(),
                        "endtime": None if suspenseendtime is None else suspenseendtime.__str__(),
                        "desc": suspensedesc
                    })
                if len(memberlist) >0:
                    twnowtime = pg_general.get_tw_datetime()
                    jsondata = {
                        "updatetime": twnowtime.__str__(),
                        "memberlist": memberlist
                    }
                    upload_obj.upload_suspenselist('setting/suspensionlist.json',jsondata)



        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makesuspenselist ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makesuspenselist except:{0}'.format(e))
        finally:
            pass

    async def makenewslist(self,upload_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,'pg_asqldb:makenewslist')

            command = 'select * from webnews'
            datalen , data = await self.getdbdata('makenewslist',command,True)

            if datalen > 0:
                newslist = sorted(data, key=lambda k: (k['newstime']), reverse=True)
                tempnewslist = []
                for item in newslist:
                    tempnewslist.append({
                        "newsindex": item.get('newsindex'),
                        "newstime": item.get('newstime').__str__(),
                        "type": item.get('type'),
                        "title": item.get('title'),
                        "content": item.get('content')
                    })



                twnowtime = pg_general.get_tw_datetime()
                jsondata = {
                    "updatetime": twnowtime.__str__(),
                    "newslist": tempnewslist
                }
                upload_obj.upload_newslist('setting/news_list.json',jsondata)



        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makenewslist ValueError:{0}'.format(e))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makenewslist except:{0}'.format(e))
        finally:
            pass

    async def noticeusercredit(self,redis_obj,memberid):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:noticeusercredit memberid:{0}'.format(
                                    memberid))

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
            datalen , data = await self.getdbdata("get credit",command,False,True)

            if datalen ==1:
                credit = data.get('credit')
                silvercredit = data.get('silvercredit')
                sendmsg = {
                    "type": SendMsgType.server_to_client,
                    "logintoken": tologintoken,
                    "msg": {"commandid": 3000016, "data": {"credit": credit,"silvercredit":silvercredit }}
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


    async def returngift(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:returngift')

            # get return gift over time minutes
            command = 'select giftovertimeminutes from setting2'
            datalen , data = await self.getdbdata('get giftovertimeminutes' , command, False)

            giftovertimeminutes = 7200
            if datalen ==1 :
                giftovertimeminutes = data.get('giftovertimeminutes')

            # for test
            temptime = pg_general.getutcnow_datetime() - timedelta(minutes=giftovertimeminutes)
            command = 'select * from gift where gifttime <="{0}" and status = 0'.format(temptime)


            datalen , data = await self.getdbdata('returngift',command,True,True)

            if datalen >0:
                for item in data:
                    ori_amount = item.get('ori_amount')
                    amount = item.get('amount')
                    frommemberid = item.get('frommemberid')
                    tomemberid = item.get('tomemberid')

                    giftindex = item.get('giftindex')
                    try:

                        # 先轉換 status of this gift
                        command = 'update gift set status =2 where giftindex="{0}"'.format(giftindex)
                        updateresutl = await self.updatedbdata('update status of gift',command)

                        # 將 frommembrerid credit 加回去
                        command = 'update member set credit = credit+"{0}" where memberid="{1}"'.format(ori_amount,frommemberid)
                        updateresult = await self.updatedbdata('update frommember credit',command)

                        param = {
                            "frommemberid": frommemberid,
                            "tomemberid": tomemberid,
                            "type": pg_general.transactiontype.overtimerejectgift,
                            "amount": amount,
                            "otherdata": None
                        }
                        asyncio.ensure_future(self.writetransactionlog('over time return gift', param))

                        # notice user
                        asyncio.ensure_future(self.noticeusercredit(redis_obj, frommemberid))

                    except Exception as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'pg_asqldb:returngift every member except:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:returngift except:{0}'.format(e))
        finally:
            pass


    async def makedailysummaryreport(self,redis_obj,telebotobj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:makedailysummaryreport')

            # 抓臺灣昨天起始與結束的 utc time str
            utcstarttime_str,utcendtime_str,yesterdaydate_tw_str = pg_general.get_tw_yesterday_startend_datetime_str()

            twdate = yesterdaydate_tw_str
            sumbet = 0                  #
            sum_totalwin = 0            #
            sumbet_s = 0                #
            sum_totalwin_s = 0          #
            sumdictinctusers = 0        #
            sumbetgoldusers = 0         #
            sumbetsilverusers = 0       #
            sumappbuyusers = 0
            sumappbuyusers_ios = 0
            sumappbuyusers_android = 0
            sumappbuypoints = 0
            sumappbuypoints_ios = 0
            sumappbuypoints_android = 0
            sumappbuycash = 0
            sumappbuycash_ios = 0
            sumappbuycash_android = 0
            sumgashbuypoints = 0
            sumgashbuypointscash = 0
            sumgashbuywallets = 0
            sumgashbuywalletscash = 0

            summycardbuyusers = 0    # 區間內mycard總購買人數
            summycardbuypoints = 0    # 區間內mycard總mapping的金爽點數
            summycardbuycash = 0    # 區間內mycard總消費的智冠面額

            spins = 0                   # 金幣場次數
            spins_s = 0                 # 銀幣場次數
            distinctuserlevelup = 0     #
            distinctusercardup = 0      #
            distinctusercarddown = 0    #
            newusers = 0                #
            newusers_ios = 0            #
            newusers_android = 0        #
            loginusers = 0              #
            apptotallogintimes = 0      #
            sumcreditcardbuypoints = 0     # 官網信用卡點數
            sumcreditcardbuycash = 0        # 官網信用卡現金
            gifttimes = 0               # 贈禮次數
            directloginuser = 0         # 直接玩人數
            fbloginuser = 0             # fb login 人數
            usernameloinguser = 0       # username login user
            piggycredit = 0              # 小豬總金額
            membercredit = 0            # 會員總金幣
            membersilvercredit = 0      # 會員總銀幣
            membersafe = 0              # 會員總保險箱
            memberinboxcredit = 0       # 會員未領信箱金幣
            memberinboxsilvercredit = 0 # 會員未另信箱銀幣
            membergift = 0              # 會員狀態中的贈禮
            maxconcurrentuser = 0       # 最高峰人數
            vipaveragebet = 0           # 白金卡以上玩家 平均下注
            pro_dailywheel = 0          # 每日轉輪贈金
            pro_freebox = 0             # 祝福保箱贈金
            pro_inbox = 0               # 領取贈金信件
            pro_bindphone = 0           # 綁定手機贈金
            pro_piggy = 0               # 小豬贈金
            pro_inboxwheel = 0          # 超級轉輪信件贈金
            pro_serial = 0              # 序號贈金
            buybox1silvercost = 0       # 買一個寶相花費銀幣
            getbox1goldamount = 0       # 買一個寶相得到金幣
            buybox10silvercost = 0      # 買十個寶相花費銀幣
            getbox10goldamount = 0      # 買十個寶相得到金幣


            # make summary bethistory gold
            command = 'select sum(total_bet) as sumbet,sum(total_win) as sum_totalwin, count( distinct(bethistory.memberid)) as dictinctusers,count(distinct(bethistory.txn_id)) as spins from bethistory,member ' \
                      'where bettime between "{0}" and "{1}" and member.memberid =bethistory.memberid and member.membertype =0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make summary bethistory',command)
            if datalen ==1:
                sumbet = data.get('sumbet')
                if sumbet is None:
                    sumbet = 0
                sum_totalwin = data.get('sum_totalwin')
                if sum_totalwin is None:
                    sum_totalwin = 0
                sumbetgoldusers = data.get('dictinctusers')
                if sumbetgoldusers is None:
                    sumbetgoldusers = 0
                spins = data.get('spins')
                if spins is None:
                    spins = 0
            # for fish
            command_fish = 'select sum(bet) as sumbet,sum(win) as sum_totalwin, count( distinct(bethistory_fish_g.memberid)) as dictinctusers,count(distinct(bethistory_fish_g.txn_id_auto)) as spins from bethistory_fish_g,member ' \
                      'where resulttime between "{0}" and "{1}" and member.memberid =bethistory_fish_g.memberid and member.membertype =0'.format(utcstarttime_str,utcendtime_str)
            datalen_fish , data_fish = await self.getdbdata('make summary bethistory_fish_g',command_fish)
            if datalen_fish ==1:
                if data_fish.get('sumbet') is not None:
                    sumbet = sumbet + data_fish.get('sumbet')
                if sumbet is None:
                    sumbet = 0
                if data_fish.get('sum_totalwin') is not None:
                    sum_totalwin = sum_totalwin + data_fish.get('sum_totalwin')
                if sum_totalwin is None:
                    sum_totalwin = 0

            # make summary bethistory silver
            command = 'select sum(total_bet) as sumbet,sum(total_win) as sum_totalwin, count( distinct(bethistory_s.memberid)) as dictinctusers,count(distinct(bethistory_s.txn_id)) as spins from bethistory_s,member ' \
                      'where bettime between "{0}" and "{1}" and member.memberid =bethistory_s.memberid and member.membertype =0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make summary bethistory_s',command)
            if datalen ==1:
                sumbet_s = data.get('sumbet')
                if sumbet_s is None:
                    sumbet_s = 0
                sum_totalwin_s = data.get('sum_totalwin')
                if sum_totalwin_s is None:
                    sum_totalwin_s = 0
                sumbetsilverusers = data.get('dictinctusers')
                if sumbetsilverusers is None:
                    sumbetsilverusers = 0
                spins_s = data.get('spins')
                if spins_s is None:
                    spins_s = 0
            # for fish
            command_fish_s = 'select sum(bet) as sumbet,sum(win) as sum_totalwin, count( distinct(bethistory_fish_s.memberid)) as dictinctusers,count(distinct(bethistory_fish_s.txn_id_auto)) as spins from bethistory_fish_s,member ' \
                      'where resulttime between "{0}" and "{1}" and member.memberid =bethistory_fish_s.memberid and member.membertype =0'.format(utcstarttime_str,utcendtime_str)
            datalen_fish_s , data_fish_s = await self.getdbdata('make summary bethistory_fish_g',command_fish_s)
            if datalen_fish_s ==1:
                if data_fish_s.get('sumbet') is not None:
                    sumbet_s = sumbet_s + data_fish_s.get('sumbet')
                if sumbet_s is None:
                    sumbet_s = 0
                if data_fish_s.get('sum_totalwin') is not None:
                    sum_totalwin_s = sum_totalwin_s + data_fish_s.get('sum_totalwin')
                if sum_totalwin_s is None:
                    sum_totalwin_s = 0

            # count total gold and silver distinct users
            command = 'select count(distinct t1.memberid) as distinctusers from  (select distinct(bethistory.memberid) from bethistory,member  ' \
                      'where bettime between "{0}" and "{1}" and bethistory.memberid = member.memberid and member.membertype = 0  union all ' \
                      'select distinct(bethistory_s.memberid) from bethistory_s,member where bettime between "{0}" and "{1}" and ' \
                      'bethistory_s.memberid = member.memberid and member.membertype =0) as t1'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('total gold and silver users',command)
            if datalen ==1:
                sumdictinctusers = data.get('distinctusers')
                if sumdictinctusers is None:
                    sumdictinctusers = 0
            # make registration users
            command = 'select count(distinct(memberid)) as distinctusers from member where ' \
                      ' registrationdatetime between "{0}" and "{1}" and membertype=0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make registration users',command)
            if datalen ==1:
                newusers = data.get('distinctusers')
                if newusers is None:
                    newusers = 0

            # make registration users-ios
            command = 'select count(distinct(memberid)) as distinctusers from member where ' \
                      ' registrationdatetime between "{0}" and "{1}" and membertype=0 and platform = 0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make registration users',command)
            if datalen ==1:
                newusers_ios = data.get('distinctusers')
                if newusers_ios is None:
                    newusers_ios = 0

            # make registration users
            command = 'select count(distinct(memberid)) as distinctusers from member where ' \
                      ' registrationdatetime between "{0}" and "{1}" and membertype=0 and platform = 1'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make registration users',command)
            if datalen ==1:
                newusers_android = data.get('distinctusers')
                if newusers_android is None:
                    newusers_android = 0

            # make logintimes and loginusers
            command = ' select count(1) as logintimes , count(distinct(memberloginlog.memberid)) as distinctusers from memberloginlog ,member ' \
                      ' where logintime between "{0}" and "{1}" and memberloginlog.memberid = member.memberid and member.membertype = 0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make login info',command)
            if datalen ==1 :
                loginusers = data.get('distinctusers')
                if loginusers is None:
                    loginusers = 0
                apptotallogintimes = data.get('logintimes')
                if apptotallogintimes is None:
                    apptotallogintimes = 0


            # make distinctuserlevelup
            command = 'select count(distinct(leveluplog.memberid)) as distinctuserlevelup from leveluplog,member where ' \
                      'leveluptime between "{0}" and "{1}" and leveluplog.memberid = member.memberid and member.membertype = 0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make distinctuserlevelup',command)
            if datalen ==1 :
                distinctuserlevelup = data.get('distinctuserlevelup')
                if distinctuserlevelup is None:
                    distinctuserlevelup = 0

            # make distinctusercardup
            command = 'select t1.cardupusers , t2.carddownusers from (select count(distinct(cardlevelchangelog.memberid)) ' \
                      'as cardupusers from cardlevelchangelog,member where newcard > oldcard and logtime between "{0}" and "{1}" ' \
                      'and cardlevelchangelog.memberid = member.memberid and member.membertype = 0) as t1, ' \
                      '(select count(distinct(cardlevelchangelog.memberid)) as carddownusers from cardlevelchangelog,member ' \
                      'where newcard < oldcard and logtime between "{0}" and "{1}" and cardlevelchangelog.memberid = member.memberid ' \
                      'and member.membertype =0) as t2'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('make distinctusercardup', command)
            if datalen ==1 :
                distinctusercardup = data.get('cardupusers')
                if distinctusercardup is None:
                    distinctusercardup = 0
                distinctusercarddown = data.get('carddownusers')
                if distinctusercarddown is None:
                    distinctusercarddown = 0

            # make  app sumappbuyusers , sumappbuypoints , sumappbuycash
            command = 'select count(distinct frommemberid) as sumappbuyusers , sum(amount) as sumappbuypoints ' \
                      'from transaction,member where transtime between "{0}" and "{1}" and type="0" and ' \
                      'transaction.frommemberid = member.memberid and member.membertype = 0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata("get sumofapppurchese",command)
            if datalen ==1:
                sumappbuyusers = data.get('sumappbuyusers')
                sumappbuypoints = data.get('sumappbuypoints')
            # ios
            command = 'select count(distinct frommemberid) as sumappbuyusers , sum(amount) as sumappbuypoints ' \
                      'from transaction,member where transtime between "{0}" and "{1}" and type="0" and ' \
                      'transaction.frommemberid = member.memberid and member.membertype = 0 and platform = 0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata("get sumofapppurchese",command)
            if datalen ==1:
                sumappbuyusers_ios = data.get('sumappbuyusers')
                sumappbuypoints_ios = data.get('sumappbuypoints')
            # android
            command = 'select count(distinct frommemberid) as sumappbuyusers , sum(amount) as sumappbuypoints ' \
                      'from transaction,member where transtime between "{0}" and "{1}" and type="0" and ' \
                      'transaction.frommemberid = member.memberid and member.membertype = 0 and platform = 1'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata("get sumofapppurchese",command)
            if datalen ==1:
                sumappbuyusers_android = data.get('sumappbuyusers')
                sumappbuypoints_android = data.get('sumappbuypoints')

            command = 'select sum(shopmapping.cost) as cash from mallhistory,shopmapping ' \
                      'where shopmapping.shopid = mallhistory.shopid and mallhistory.buytime between "{0}" and "{1}"'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get sumofappbuycash', command)
            if datalen == 1:
                sumappbuycash = pg_general.converttype(data.get('cash'),int)
            # ios
            command = 'select sum(shopmapping.cost) as cash from mallhistory,shopmapping,member ' \
                      'where shopmapping.shopid = mallhistory.shopid and mallhistory.buytime between "{0}" and "{1}" and member.memberid = mallhistory.memberid and member.platform = 0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get sumofappbuycash', command)
            if datalen == 1:
                sumappbuycash_ios = pg_general.converttype(data.get('cash'),int)
            # andriod
            command = 'select sum(shopmapping.cost) as cash from mallhistory,shopmapping,member ' \
                      'where shopmapping.shopid = mallhistory.shopid and mallhistory.buytime between "{0}" and "{1}" and member.memberid = mallhistory.memberid and member.platform = 1'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get sumofappbuycash', command)
            if datalen == 1:
                sumappbuycash_android = pg_general.converttype(data.get('cash'),int)

            if sumappbuycash is None:
                sumappbuycash = 0
            if sumappbuycash_ios is None:
                sumappbuycash_ios = 0
            if sumappbuycash_android is None:
                sumappbuycash_android = 0
            if sumappbuyusers is None:
                sumappbuyusers = 0
            if sumappbuyusers_ios is None:
                sumappbuyusers_ios = 0
            if sumappbuyusers_android is None:
                sumappbuyusers_android = 0
            if sumappbuypoints is None:
                sumappbuypoints = 0
            if sumappbuypoints_ios is None:
                sumappbuypoints_ios = 0
            if sumappbuypoints_android is None:
                sumappbuypoints_android = 0

            # make sumgashbuypoints
            command = 'select sum(gashpointinfo.cashamount) as cash, sum(gashpointinfo.pointamount) as point from gashwalletdeposite,gashpointinfo ' \
                      'where gashpointinfo.itemcode = gashwalletdeposite.itemcode and gashwalletdeposite.type = 1 and gashwalletdeposite.status = "3" ' \
                      'and gashwalletdeposite.pay_rcode = "0000" and gashwalletdeposite.pay_status = "S" and ' \
                      'gashwalletdeposite.endtime between "{0}" and "{1}"'.format(utcstarttime_str,utcendtime_str)

            datalen , data = await self.getdbdata('get sumgashbuypoints',command)
            if datalen ==1:
                sumgashbuypoints = data.get('point')
                sumgashbuypointscash = data.get('cash')

            if sumgashbuypoints is None:
                sumgashbuypoints = 0
            if sumgashbuypointscash is None:
                sumgashbuypointscash = 0


            # make sumgashbuywallets
            command = 'select sum(gashwalletinfo.cashamount) as cash, sum(gashwalletinfo.pointamount) as point from gashwalletdeposite,gashwalletinfo ' \
                      'where gashwalletinfo.itemcode = gashwalletdeposite.itemcode and gashwalletdeposite.type = 0 and ' \
                      'gashwalletdeposite.status = "3" and gashwalletdeposite.pay_rcode = "0000" and gashwalletdeposite.pay_status = "S" ' \
                      'and gashwalletdeposite.endtime between "{0}" and "{1}"'.format(utcstarttime_str,utcendtime_str)
            datalen, data = await self.getdbdata('get sumgashbuywallets',command)
            if datalen ==1:
                sumgashbuywallets = data.get('point')
                sumgashbuywalletscash = data.get('cash')

            if sumgashbuywallets is None:
                sumgashbuywallets = 0
            if sumgashbuywalletscash is None:
                sumgashbuywalletscash = 0

            # 搜索區間內mycard總購買人數、總消費智冠面額、總mapping的金爽點數
            command = 'select COUNT(*) as summycardbuyusers, sum(jinsongpoints) as summycardbuypoints, sum(amount) as summycardbuycash from mycardhistory where statusapi="37" and insertutcnowdate between "{0}" and "{1}"'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get mycard within count and points and cash', command)

            if datalen == 1:    # 如果有找到總數
                summycardbuyusers = data.get('summycardbuyusers')    # 區間內mycard總購買人數
                summycardbuypoints = data.get('summycardbuypoints')    # 區間內mycard總mapping的金爽點數
                summycardbuycash = data.get('summycardbuycash')    # 區間內mycard總消費的智冠面額

            if summycardbuyusers is None:
                summycardbuyusers = 0    # 沒有找到總數則給預設為0

            if summycardbuypoints is None:
                summycardbuypoints = 0    # 沒有找到總數則給預設為0

            if summycardbuycash is None:
                summycardbuycash = 0    # 沒有找到總數則給預設為0

            # make sumcreditcardbuypoints and cash
            command = 'select sum(cashamount)as cash,sum(pointamount) as point   from creditcarddeposite ,creditcardinfo ' \
                      'where status = "1" and creditcardinfo.itemcode = creditcarddeposite.ProductNum and starttime ' \
                                        'between "{0}" and "{1}"'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get sumcreditcardbuypoints', command)
            if datalen ==1 :
                sumcreditcardbuypoints = data.get('point')
                sumcreditcardbuycash = data.get('cash')

            if sumcreditcardbuypoints is None:
                sumcreditcardbuypoints = 0
            if sumcreditcardbuycash is None:
                sumcreditcardbuycash = 0

            # make gift times
            command = 'select count(1) as c1 from transaction where type = "{0}" and transtime between "{1}" and "{2}"'.format(pg_general.transactiontype.receivegift,utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get gift times',command)
            if datalen == 1:
                gifttimes = data.get('c1')

            if gifttimes is None:
                gifttimes = 0

            # find login method users
            command = 'select memberloginlog.memberid,loginmethod from memberloginlog,member where logintime ' \
                      'between "{0}" and "{1}" and memberloginlog.memberid = member.memberid and member.membertype= 0 ' \
                      ' group by memberloginlog.memberid'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get memberloginlog',command,True)
            if datalen >0:
                for item in data:
                    loginmethod = item.get('loginmethod')
                    if loginmethod is None or loginmethod == 3:
                        directloginuser += 1
                    elif loginmethod == 2:
                        fbloginuser += 1
                    else:
                        usernameloinguser += 1

            #make piggycredit summary
            command = 'select sum(piggycredit) as amount from memberpiggyinfo,member where memberpiggyinfo.memberid = member.memberid and member.membertype = 0'
            datalen , data = await self.getdbdata('get piggyinfo',command)
            if datalen ==1:
                piggycredit = data.get('amount')


            # make member credit,silvercredit,safe summary
            command = 'select sum(credit) as membercredit,sum(silvercredit) as membersilvercredit,sum(safe) as membersafe from member where member.membertype = 0'
            datalen , data = await self.getdbdata('make member credit summary',command)
            if datalen ==1:
                membercredit = data.get('membercredit')
                membersilvercredit = data.get('membersilvercredit')
                membersafe = data.get('membersafe')

            # make memberinbox 未領信件金額
            nowutcdatetime = pg_general.getutcnow_datetime()
            command = 'select memberinbox.promotionid,memberinbox.credit_award,promotion.promotiontype,promotion.content from memberinbox,promotion,member ' \
                      'where receivestate = 1 and promotion.promotionindex = memberinbox.promotionid and memberinbox.dateline >="{0}" ' \
                      'and memberinbox.memberid = member.memberid and member.membertype = 0'.format(nowutcdatetime)
            datalen , data = await self.getdbdata('get memberinbox',command,True)
            if datalen > 0:
                for item in data:
                    promotiontype = item.get('promotiontype')
                    content = item.get('content')
                    credit_award = item.get('credit_award')
                    if promotiontype == 0:
                        memberinboxcredit += pg_general.converttype(content,int)
                    elif promotiontype == 5:
                        memberinboxsilvercredit += pg_general.converttype(content,int)
                    elif promotiontype == 4:
                        memberinboxcredit += pg_general.converttype(credit_award,int)

            # make member gift 未完成的贈禮數據
            command = 'select sum(ori_amount) as amount from gift where status = 0'
            datalen , data = await self.getdbdata('get membergift',command)
            if datalen ==1:
                membergift = data.get('amount')
            if membergift is None:
                membergift = 0

            # get max concurrentuser of this day
            command = 'select max(users) as amount from concurrentuserlog where logtime between "{0}" and "{1}"'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get max concurrent user',command)
            if datalen ==1 :
                maxconcurrentuser = data.get('amount')
            if maxconcurrentuser is None:
                maxconcurrentuser = 0


            # make 白金以上會員每日 人均 壓分
            command = 'select count(distinct memberid), sum(total_bet) as sumtotalbet, (sum(total_bet) / count(distinct memberid)) as averagebet ' \
                      ' from (select bethistory.memberid, sum(total_bet) as total_bet, card from bethistory, member where member.memberid = bethistory.memberid ' \
                      ' and bethistory.bettime between "{0}" and "{1}" and membertype=0 group by bethistory.memberid having card >= 3) as t1 '.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get vipaveragebet',command)
            if datalen ==1:
                vipaveragebet = pg_general.converttype(data.get('averagebet'),int)

            if vipaveragebet is None:
                vipaveragebet = 0

            # make 贈金報表
            command = 'select type ,sum(amount) as amount,sum(amount_silver) as amount_silver from transaction,member where ' \
                      'transtime between "{0}" and "{1}" and type in (13,19,17,14,15,20)  and member.memberid = transaction.frommemberid ' \
                      'and member.membertype = 0  group by type'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get promotion data',command,True)
            amount = 0
            amount_g = 0
            amount_s = 0
            if datalen  >0:
                for item in data:
                    type = pg_general.converttype(item.get('type'),int)
                    amount = pg_general.converttype(item.get('amount'),int) + pg_general.converttype(item.get('amount_silver')/100,int)
                    if type == 13:
                        pro_dailywheel = amount
                    elif type == 19:
                        pro_freebox = amount
                    elif type == 17:
                        pro_inbox = amount
                        amount_g = pg_general.converttype(item.get('amount'), int)
                        amount_s = pg_general.converttype(item.get('amount_silver') / 100, int)
                    elif type == 14:
                        pro_bindphone = amount
                    elif type == 15:
                        pro_piggy = amount
                    elif type == 20:
                        pro_inboxwheel = amount

            if pro_dailywheel is None:
                pro_dailywheel = 0
            if pro_freebox is None:
                pro_freebox  = 0
            if pro_inbox is None:
                pro_inbox = 0
            if pro_bindphone is None:
                pro_bindphone = 0
            if pro_piggy is None:
                pro_piggy  = 0
            if pro_inboxwheel is None:
                pro_inboxwheel = 0


            # 序號贈金
            command = 'select sum(award) as award, sum(award_s) as award_s from seriallog,member  where usedtime between "{0}" and "{1}" ' \
                      ' and member.memberid = seriallog.memberid and member.membertype = 0'.format(utcstarttime_str,utcendtime_str)
            datalen , data = await self.getdbdata('get serial log',command)
            if datalen ==1:
                tmpaward = 0 if data.get('award') is None else pg_general.converttype(data.get('award'),int)
                tmpaward_s = 0 if data.get('award_s') is None else pg_general.converttype(data.get('award_s'),int)

                pro_serial = pg_general.converttype(tmpaward + (tmpaward_s/100) , int)

            if pro_serial is None:
                pro_serial = 0

            # 買寶相區
            command = 'select otherdata,sum(amount) amount, sum(amount_silver) amount_silver  from transaction where type in (21,22) ' \
                      ' and transtime between "{0}" and "{1}" group by otherdata '.format(utcstarttime_str,utcendtime_str)
            datalen, data = await self.getdbdata('get buy box info',command,True)
            if datalen > 0:
                for item in data:
                    tmpotherdata = item.get('otherdata')
                    amount = item.get('amount')
                    amount_silver = item.get('amount_silver')
                    if tmpotherdata == 'buyboxcost1':
                        buybox1silvercost = amount_silver
                    elif tmpotherdata == 'buyboxcost10':
                        buybox10silvercost = amount_silver
                    elif tmpotherdata == 'buyboxget1':
                        getbox1goldamount = amount
                    elif tmpotherdata == 'buyboxget10':
                        getbox10goldamount = amount


            param = []
            param.append([
                twdate,
                sumbet,
                sum_totalwin,
                sumbet_s,
                sum_totalwin_s,
                sumdictinctusers,
                sumbetgoldusers,
                sumbetsilverusers,
                sumappbuyusers,
                sumappbuypoints,
                sumgashbuypoints,
                sumgashbuywallets,
                distinctuserlevelup,
                distinctusercardup,
                distinctusercarddown,
                newusers,
                loginusers,
                apptotallogintimes,
                sumcreditcardbuypoints,
                gifttimes,
                directloginuser,
                fbloginuser,
                usernameloinguser,
                piggycredit,
                membercredit,
                membersilvercredit,
                membersafe,
                memberinboxcredit,
                memberinboxsilvercredit,
                membergift,
                maxconcurrentuser,
                vipaveragebet,
                sumappbuycash,
                sumgashbuypointscash,
                sumgashbuywalletscash,
                sumcreditcardbuycash,
                pro_dailywheel,
                pro_freebox,
                pro_inbox,
                pro_bindphone,
                pro_piggy,
                pro_inboxwheel,
                pro_serial,
                spins,
                spins_s,
                buybox1silvercost,
                getbox1goldamount,
                buybox10silvercost,
                getbox10goldamount,
                summycardbuyusers,    # 區間內mycard總購買人數
                summycardbuypoints,   # 區間內mycard總mapping的金爽點數
                summycardbuycash      # 區間內mycard總消費的智冠面額
            ])
            command = 'insert into dailysummary (twdate,sumbet,sum_totalwin,' \
                      'sumbet_s,sum_totalwin_s,sumdictinctusers,sumbetgoldusers,sumbetsilverusers,' \
                      'sumappbuyusers,sumappbuypoints,sumgashbuypoints,sumgashbuywallets,distinctuserlevelup,' \
                      'distinctusercardup,distinctusercarddown,newusers,loginusers,totallogintimes,sumcreditcardbuypoints,gifttimes,' \
                      'directloginuser,fbloginuser,usernameloinguser,piggycredit,membercredit,membersilvercredit,membersafe,memberinboxcredit,' \
                      'memberinboxsilvercredit,membergift,maxconcurrentuser,vipaveragebet,sumappbuycash,sumgashbuypointscash,sumgashbuywalletscash,sumcreditcardbuycash,' \
                      'pro_dailywheel,pro_freebox,pro_inbox,pro_bindphone,pro_piggy,pro_inboxwheel,pro_serial,spins,spins_s,buybox1silvercost,getbox1goldamount,buybox10silvercost,getbox10goldamount,summycardbuyusers,summycardbuypoints,summycardbuycash) ' \
                      'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,' \
                      '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            insertresult ,index = await self.insertdbdata('insert dailysummary',command,many=True,manydata=param)

            # get telebot dailysummary chatroomid from setting2
            command = 'select dailyreporttelegramroomid from setting2'
            datalen , data = await self.getdbdata('get telebot dailysummary chatroomid ',command)
            if datalen ==1 :
                chatroomid = data.get('dailyreporttelegramroomid')
                # make telebot data and send to chatroom
                if env_setting.PRODUCTION_MODE == False:
                    telebotmsg = '測試機\n'
                else:
                    telebotmsg = ''
                telebotmsg += '日期:{}\n'.format(twdate)
                telebotmsg += '新會:{:,}\n'.format(newusers)
                telebotmsg += '新會-ios:{:,}\n'.format(newusers_ios)
                telebotmsg += '新會-android:{:,}\n'.format(newusers_android)
                telebotmsg += '登入人數:{:,}\n'.format(loginusers)
                telebotmsg += '總押分-金:{:,}\n'.format(sumbet)
                telebotmsg += '總贏分-金:{:,}\n'.format(sum_totalwin)
                telebotmsg += '總場次-金:{:,}\n'.format(spins)
                telebotmsg += '總押分-銀:{:,}\n'.format(sumbet_s)
                telebotmsg += '總贏分-銀:{:,}\n'.format(sum_totalwin_s)
                telebotmsg += '總場次-銀:{:,}\n'.format(spins_s)
                telebotmsg += '總下注會員數-不分:{:,}\n'.format(sumdictinctusers)
                telebotmsg += '總下注會員數-金:{:,}\n'.format(sumbetgoldusers)
                telebotmsg += '總下注會員數-銀:{:,}\n'.format(sumbetsilverusers)
                telebotmsg += 'App內購人數:{}\n'.format(sumappbuyusers)
                telebotmsg += 'App內購點數:{:,}\n'.format(sumappbuypoints)
                telebotmsg += 'App內購現金:{:,}\n'.format(sumappbuycash)
                telebotmsg += 'App內購人數-ios:{}\n'.format(sumappbuyusers_ios)
                telebotmsg += 'App內購點數-ios:{:,}\n'.format(sumappbuypoints_ios)
                telebotmsg += 'App內購現金-ios:{:,}\n'.format(sumappbuycash_ios)
                telebotmsg += 'App內購人數-android:{}\n'.format(sumappbuyusers_android)
                telebotmsg += 'App內購點數-android:{:,}\n'.format(sumappbuypoints_android)
                telebotmsg += 'App內購現金-android:{:,}\n'.format(sumappbuycash_android)
                telebotmsg += 'GashPoint購點數:{:,}\n'.format(sumgashbuypoints)
                telebotmsg += 'GashPoint購現金:{:,}\n'.format(sumgashbuypointscash)
                telebotmsg += 'GashWallet購點數:{:,}\n'.format(sumgashbuywallets)
                telebotmsg += 'GashWallet購現金:{:,}\n'.format(sumgashbuywalletscash)

                telebotmsg += 'mycard購人數:{:,}\n'.format(summycardbuyusers)  # 區間內mycard總購買人數(同一玩家購買N次就算N次)
                telebotmsg += 'mycard購點數:{:,}\n'.format(summycardbuypoints)  # 區間內mycard總mapping的金爽點數
                telebotmsg += 'mycard購現金:{:,}\n'.format(summycardbuycash)  # 區間內mycard總消費的面額

                telebotmsg += '官網信用卡點數:{:,}\n'.format(sumcreditcardbuypoints)
                telebotmsg += '官網信用卡現金:{:,}\n'.format(sumcreditcardbuycash)
                telebotmsg += '贈禮次數:{:,}\n'.format(gifttimes)
                telebotmsg += 'Levelup人數:{:,}\n'.format(distinctuserlevelup)
                telebotmsg += 'CardUp人數:{:,}\n'.format(distinctusercardup)
                telebotmsg += 'CardDown人數:{:,}\n'.format(distinctusercarddown)
                telebotmsg += 'App總登入次數:{:,}\n'.format(apptotallogintimes)
                telebotmsg += '直接玩人數:{:,}\n'.format(directloginuser)
                telebotmsg += 'FB登入人數:{:,}\n'.format(fbloginuser)
                telebotmsg += '帳號登入人數:{:,}\n'.format(usernameloinguser)
                telebotmsg += '最高同時在線:{:,}\n'.format(maxconcurrentuser)
                telebotmsg += '白金以上日均押:{:,}\n'.format(vipaveragebet)
                telebotmsg += '-----------------\n'
                telebotmsg += '撲滿總金幣:{:,}\n'.format(int(piggycredit))
                telebotmsg += '總帳戶金幣:{:,}\n'.format(membercredit)
                telebotmsg += '總帳戶銀幣:{:,}\n'.format(membersilvercredit)
                telebotmsg += '總帳戶保險箱:{:,}\n'.format(membersafe)
                telebotmsg += '總未領信件金弊:{:,}\n'.format(memberinboxcredit)
                telebotmsg += '總未領信件銀幣:{:,}\n'.format(memberinboxsilvercredit)
                telebotmsg += '總未領贈禮金弊:{:,}\n'.format(membergift)
                telebotmsg += '-------贈金-------\n'
                telebotmsg += '日轉輪贈:{:,}\n'.format(pro_dailywheel)
                telebotmsg += '寶箱贈:{:,}\n'.format(pro_freebox)
                telebotmsg += '領取信件:{:,}\n'.format(pro_inbox)
                telebotmsg += '領取信件-金:{:,}\n'.format(amount_g)
                telebotmsg += '領取信件-銀:{:,}\n'.format(amount_s)
                telebotmsg += '綁手機贈:{:,}\n'.format(pro_bindphone)
                telebotmsg += '小豬贈:{:,}\n'.format(pro_piggy)
                telebotmsg += '超級轉輪信:{:,}\n'.format(pro_inboxwheel)
                telebotmsg += '序號贈金:{:,}\n'.format(pro_serial)
                telebotmsg += '總計以上:{:,}\n'.format(pro_dailywheel+pro_freebox+pro_inbox+pro_bindphone+pro_piggy+pro_inboxwheel+pro_serial)
                telebotmsg += '-----購買寶相--------\n'
                telebotmsg += '買一個花費銀:{:,}\n'.format(buybox1silvercost)
                telebotmsg += '買一個得到金:{:,}\n'.format(getbox1goldamount)
                telebotmsg += '買十個花費銀:{:,}\n'.format(buybox10silvercost)
                telebotmsg += '買十個得到金:{:,}\n'.format(getbox10goldamount)
                telebotmsg += '---------------------\n'
                telebotmsg += '總流通金幣:{:,}\n'.format(int(piggycredit)+ membercredit + membersafe,memberinboxcredit,membergift)
                telebotmsg += '-----------------\n'
                telebotobj.senddailyreport(chatroomid,telebotmsg)





        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makedailysummaryreport except:{0}'.format(e))
        finally:
            pass

    async def writetransactionlog(self,logintoken,param):
        # db.transaction
        # type 參考 pg_general transactiotype
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


    async def makelikerank(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:makelikerank start')

            # 抓 tw 今天的 starttime and endtime
            # 換算成 utctime starttime and endtime

            # delete like rank table
            command = 'delete from likerank'
            result = await self.updatedbdata('delete like rank table',command)

            localdate = pg_general.get_local_date()
            utcstarttimestr , utcendtimestr = pg_general.get_date_to_utc_start_end_time(localdate)

            command = 'select tomemberid,count(1) as c1,member.nickname,member.`level`,member.card,member.avatar from likelog,member where ' \
                      ' likelog.tomemberid = member.memberid and logtime between "{0}" and "{1}" ' \
                      ' group by tomemberid order by c1 desc limit 100'.format(utcstarttimestr,utcendtimestr)
            datalen , data = await self.getdbdata('get like log ', command , True)
            if datalen >0:
                param = []
                rank = 1
                for item in data:
                    param.append([
                        rank,
                        item.get('tomemberid'),
                        item.get('c1'),
                        item.get('nickname'),
                        item.get('avatar'),
                        item.get('card'),
                        item.get('level')
                    ])
                    rank = rank + 1


                command = 'insert into likerank (rank,memberid,likeamount,nickname,avatar,card,level) values(%s,%s,%s,%s,%s,%s,%s)'
                resultinsert, index = await self.insertdbdata('insert like rank', command, many=True, manydata=param)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makelikerank except:{0}'.format(e))

        pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:makelikerank end')

    async def jppool_broadcast(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, 'pg_asqldb:jppool_broadcast start')

            # get all jp data
            command = 'select * from jppool order by id desc'
            datalen , data = await self.getdbdata('get jppool data',command,True)

            pooldata = []
            totalpoolvalue = 0
            for item in data:
                enable = True if item.get('enable') == 1 else False

                id = item.get('id')
                current_centtemp = item.get('current_cent')
                totalpoolvalue += current_centtemp
                current_cent = {
                    "high": int(current_centtemp/pow(2,32)),
                    "low": int(current_centtemp % pow(2,32)),
                    "unsigned": True
                }
                min_cent = item.get('min_cent')
                max_centtemp = item.get('max_cent')
                max_cent = {
                    "high": int(max_centtemp / pow(2, 32)),
                    "low": int(max_centtemp % pow(2, 32)),
                    "unsigned": True
                }
                hitvalue = item.get('hitvalue')
                name = item.get('name')
                plusvalue_min = item.get('plusvalue_min')
                plusvalue_max = item.get('plusvalue_max')
                plusvalue = random.randrange(plusvalue_min,plusvalue_max)
                pooldata.append({
                    "current_cent": current_cent,
                    "enable": enable,
                    "id": id,
                    "max_cent": max_cent,
                    "name": name

                })

                # 判斷是否有超過　以及　累加　回寫
                current_centtemp += plusvalue
                if current_centtemp >= hitvalue:
                    current_centtemp = min_cent
                    hitvalue = random.randrange(min_cent,max_centtemp)

                command = 'update jppool set current_cent = "{0}" , hitvalue="{1}" where id="{2}"'.format(current_centtemp,hitvalue,id)
                updateresult = await self.updatedbdata('write jppool',command)


            # write to redis
            jppooldata = {"pooldata": pooldata,"totalpoolvalue": totalpoolvalue}
            await redis_obj.set_json_value("jppool",jppooldata)


            sendmsg = {"type": 0, "msg": {"commandid": 3000017, "data": {"pooldata": pooldata,"totalpoolvalue": totalpoolvalue}}}
            # get lobby server ips
            if env_setting.LOCAL_SERVER == False:
                command = 'select ip from lobbyserversetting'
                datalen, data = await self.getdbdata('get all lobby server ips', command, True)
                if datalen > 0:
                    try:
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
                        lobbyserverips = data
                        if lobbyserverips != []:
                            for item in lobbyserverips:
                                realurl = 'http://{0}/broadcasttoall'.format(item.get('ip'))
                                async with aiohttp.ClientSession() as session:
                                    response = await session.get(realurl, json=sendmsg)
                                    if response.status == 200:
                                        data = await response.text()
                                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                            'send_to_all_lobbyserver_future response:{0}'.format(data))
                                await asyncio.sleep(0)

                    except Exception as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'send_to_all_lobbyserver , except:{0}'.format(e))
                    finally:
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            'send_to_all_lobbyserver , done')






        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:jppool_broadcast except:{0}'.format(e))

    # 前端取得的交易面額選單供玩家選擇
    async def makepayconfig(self,upload_obj):
        try:

            gashwalletflag = 0
            gashpointflag = 0
            creditcardflag = 0
            bankflag = 0
            serialnumberflag = 0
            webpackageflag = 0
            gashwalletitems = []
            gashpointitems = []
            creditcarditems = []
            bankitems = []
            webpackageitems = []
            mycardtojinsongmapping = []
            command = 'select * from webserversetting'
            datalen, data = await self.getdbdata('get webserversetting',command)

            if datalen !=1:
                raise Exception('get webserversetting error')

            gashwalletflag = data.get('gashwalletflag')
            gashpointflag = data.get('gashpointflag')
            creditcardflag = data.get('creditcardflag')
            bankflag = data.get('bankflag')
            serialnumberflag = data.get('serialnumberflag')
            webpackageflag = data.get('webpackageflag')
            mycardflag = data.get('mycardflag')
            # gash wallet info
            command = 'select * from gashwalletinfo order by itemcode'
            datalen, data = await self.getdbdata('get gashwalletinfo ', command, True)

            if datalen >0:
                for item in data:
                    gashwalletitems.append({
                        "itemcode": item.get('itemcode'),
                        "cashamount": item.get('cashamount'),
                        "pointamount": item.get('pointamount')
                    })

            # gash point info
            command = 'select * from gashpointinfo order by itemcode'
            datalen, data = await self.getdbdata('get gashpointinfo', command, True)

            if datalen > 0:
                for item in data:
                    gashpointitems.append({
                        "itemcode": item.get('itemcode'),
                        "cashamount": item.get('cashamount'),
                        "pointamount": item.get('pointamount')

                    })

            # credit card info
            command = 'select * from creditcardinfo order by itemcode'
            datalen, data = await self.getdbdata('get creditcardinfo',command,True)

            if datalen > 0:
                for item in data:
                    creditcarditems.append({
                        "itemcode": item.get('itemcode'),
                        "cashamount": item.get('cashamount'),
                        "pointamount": item.get('pointamount'),
                        "productname": item.get('productname')
                    })

            # bank info
            command = 'select * from bankinfo order by itemcode'
            datalen, data = await self.getdbdata('get bankinfo',command,True)
            if datalen > 0:
                for item in data:
                    bankitems.append({
                        "itemcode": item.get('itemcode'),
                        "cashamount": item.get('cashamount'),
                        "pointamount": item.get('pointamount')
                    })

            # webpackage info
            command = 'select * from webpackageinfo order by itemcode'
            datalen, data = await self.getdbdata('get webpackageinfo',command,True)
            if datalen >0 :
                for item in data:
                    webpackageitems.append({
                        "itemcode": item.get('itemcode'),
                        "cashamount": item.get('cashamount'),
                        "pointamount": item.get('pointamount'),
                        "content": item.get('content'),
                        "type": item.get('type')
                    })

            # 取得MyCard點數與Jinsong點數的mapping
            command = 'select * from mycardpointmapping order by itemcode asc'
            datalen, data = await self.getdbdata('get mycardpointmapping', command, True)
            if datalen > 0:
                for i in data:
                    mycardtojinsongmapping.append({
                        "itemcode": i.get("itemcode"),     # 此itemcode為前端抓取flag的參數名稱，不是智冠品項名稱
                        "cashamount": i.get('mycardpoint'),   # 智冠面額
                        "pointamount": i.get('jinsongpoint')   # 金爽點數
                    })

            uploaddict = {
                "gashwallet":{
                    "enable": gashwalletflag,
                    "item": gashwalletitems
                },
                "gashpoint":{
                    "enable": gashpointflag,
                    "item": gashpointitems
                },
                "creditcard":{
                    "enable": creditcardflag,
                    "item": creditcarditems
                },
                "bank": {
                    "enable": bankflag,
                    "item": bankitems
                },
                "serialnumber":{
                    "enable": serialnumberflag
                },
                "webpackage":{
                    "enable": webpackageflag,
                    "item": webpackageitems
                },
                "mycardwallet":{
                    "enable": mycardflag,
                    "item": mycardtojinsongmapping    # 智冠面額mapping金爽點數的資料表
                }

            }

            upload_obj.upload_bucket('setting/payconfig.json',uploaddict)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makepayconfig except:{0}'.format(e))


    async def makewebad(self,upload_obj):
        try:
            command = 'select * from webadinfo order by posindex'
            datalen, data = await self.getdbdata('get web ad info', command, True)

            uploaddict = []

            if datalen >0:
                for item in data:
                    uploaddict.append({
                        "url": item.get('url'),
                        "linkurl": item.get('linkurl')
                    })


                upload_obj.upload_bucket('setting/webad.json', uploaddict)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makewebad except:{0}'.format(e))

    async def make_signal_action_redis(self,redis_obj):
        try:
            command = 'select * from signaldata'
            datalen , data = await self.getdbdata('get signal db',command)
            if datalen ==1:
                signaldict = {
                    "id": data.get('id'),
                    "ttltime": data.get('ttltime'),
                    "signal" : data.get('signal'),
                    "promotionid" : data.get('promotionid'),
                    "passcontent" : data.get('passcontent'),
                    "timefailcontent" : data.get('timefailcontent'),
                    "cardfailcontent": data.get('cardfailcontent'),
                    "dupphonefailcontent": data.get('dupphonefailcontent'),
                    "dupmemberfailcontent": data.get('dupmemberfailcontent'),
                    "bindphonefailcontent": data.get('bindphonefailcontent'),
                    "inboxtitle" : data.get('inboxtitle'),
                    "inboxcontent" : data.get('inboxcontent'),
                    "inboxdateline" : data.get('inboxdateline').__str__()

                }

                # set redis signal_action
                # tempstr = json.dumps(signaldict)
                await redis_obj.set_json_value('signal_action',signaldict,data.get('ttltime'))
                #
                # result = await redis_obj.get_json_value('signal_action')
                #
                # pass
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makewebad except:{0}'.format(e))
        pass

    async def service_to_user(self,memberid,content):
        try:
            try:
                sendmsg = content
                url = APISERVERURL + '?memberid={}&content={}'.format(memberid, sendmsg)
                returndata = 'error'
                async with aiohttp.ClientSession() as session:
                    response = await session.get(url)
                    if response.status == 200:
                        returndata = await response.text()
                    else:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'pg_asqldb:service_to_user 2 error not 200')
            except Exception as e:
                pass
            await asyncio.sleep(0.1)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:service_to_user except:{0}'.format(e))
        return returndata

    async def makeproreporttouser(self,redis_obj):
        try:
            # 抓設定值
            command = 'select * from proreporttouser where enable = 1'
            datalen , data = await self.getdbdata('makeproreporttouser',command,True)

            # 抓今天 local date
            todaydate = pg_general.get_tw_datetime().date()
            yesterdaydate = todaydate - timedelta(days=1)

            yesterday_utc_starttime_str, yesterday_utc_endtime_str,yesterday_date_str = pg_general.get_tw_yesterday_startend_datetime_str()

            newdata = []

            if datalen > 0:
                for tmpitem in data:

                    content = tmpitem.get('content')
                    startdate = tmpitem.get('startdate')
                    enddate = tmpitem.get('enddate')
                    type = tmpitem.get('type')
                    extra = tmpitem.get('extra')
                    mincard = tmpitem.get('mincard')
                    if None in [content,startdate,enddate,type,mincard]:
                        continue

                    if type ==2 and extra is None:
                        continue

                    # 超過時間不用做
                    if todaydate > (enddate + timedelta(days=1)):
                        continue

                    # 時間未到不用作
                    if todaydate <= startdate:
                        continue

                    if type ==1:        # 全部 金幣 押分
                        command = 'select betsum.memberid,sum(betsum.bet) as sumbet from  betsum,member where member.memberid = betsum.memberid ' \
                                  ' and betsum.sumdate between "{}" and "{}" and member.card >= "{}" and member.phonebindstatus = 2 ' \
                                  'group by betsum.memberid'.format(startdate.__str__(),yesterdaydate.__str__(),mincard)
                        datalen, data = await self.getdbdata('get betsum', command , True)
                        if datalen >0:
                            for item in data:
                                sumbet = item.get('sumbet')
                                memberid = item.get('memberid')
                                sendmsg = content.format(startdate.__str__(),yesterdaydate.__str__(),'{:,}'.format(sumbet))
                                url = APISERVERURL + '?memberid={}&content={}'.format(memberid,sendmsg)
                                try:
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(url)
                                        if response.status == 200:
                                            data = await response.text()
                                        else:
                                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                                'pg_asqldb:makeproreporttouser 1 error not 200')
                                except Exception as e:
                                    pass
                                await asyncio.sleep(0.1)
                    elif type ==2:      # 單 game 銀幣 押分

                        # 抓 start time and end time
                        utcstartimestr,utcendtimestr = pg_general.get_date_to_utc_start_end_time(startdate)

                        gameid = extra
                        command = 'select bethistory_s.memberid,sum(total_bet) as bet from bethistory_s,member where member.memberid = bethistory_s.memberid and member.card>="{3}" and bettime between "{0}" and "{1}" and gameid ="{2}" and member.phonebindstatus = 2 group by memberid'.format(utcstartimestr,yesterday_utc_endtime_str,gameid,mincard)
                        datalen , data = await self.getdbdata('get silver bethistory_s',command,True)

                        if datalen > 0:
                            for item in data:
                                sumbet = item.get('bet')
                                memberid = item.get('memberid')
                                sendmsg = content.format(startdate.__str__(),yesterdaydate.__str__(),'{:,}'.format(sumbet))
                                url = APISERVERURL + '?memberid={}&content={}'.format(memberid, sendmsg)
                                try:
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(url)
                                        if response.status == 200:
                                            data = await response.text()
                                        else:
                                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                                'pg_asqldb:makeproreporttouser 2 error not 200')
                                except Exception as e:
                                    pass
                                await asyncio.sleep(0.1)
                    elif type ==3: # 全部 金幣 贏分
                        command = 'select betsum.memberid,sum(betsum.win) as sumwin from  betsum,member where member.memberid = betsum.memberid ' \
                                  ' and betsum.sumdate between "{}" and "{}" and member.card >= "{}" ' \
                                  'group by betsum.memberid'.format(startdate.__str__(), yesterdaydate.__str__(),
                                                                    mincard)
                        datalen, data = await self.getdbdata('get betsum win', command, True)
                        if datalen > 0:
                            for item in data:
                                sumwin = item.get('sumwin')
                                memberid = item.get('memberid')
                                sendmsg = content.format(startdate.__str__(), yesterdaydate.__str__(),
                                                         '{:,}'.format(sumwin))
                                url = APISERVERURL + '?memberid={}&content={}'.format(memberid, sendmsg)
                                try:
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(url)
                                        if response.status == 200:
                                            data = await response.text()
                                        else:
                                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                                'pg_asqldb:makeproreporttouser 3 error not 200')
                                except Exception as e:
                                    pass
                                await asyncio.sleep(0.1)
                    elif type ==4 : # 龍虎榜領取獎金次數統計
                        command = 'select jinsonggamerankdaysettle.memberid, count(1) as c1 from jinsonggamerankdaysettle,member ' \
                                  'where member.memberid= jinsonggamerankdaysettle.memberid and extraaward >0 and rankdate ' \
                                  'between "{}" and "{}" and member.card>="{}" and member.phonebindstatus = 2 group by jinsonggamerankdaysettle.memberid ' \
                                  'order by c1 desc,jinsonggamerankdaysettle.memberid asc'.format(startdate.__str__(), yesterdaydate.__str__(),
                                                                    mincard)
                        datalen , data = await self.getdbdata('get jinsonggamerankdaysettle',command,True)
                        if datalen > 0:
                            newdata = data.copy()
                            for i in range(len(newdata)):
                                newdata[i]['rank'] = i+1

                            for item in newdata:
                                c1 = item.get('c1')
                                memberid = item.get('memberid')
                                rank = item.get('rank')
                                sendmsg = content.format(startdate.__str__(), yesterdaydate.__str__(),
                                                         '{:,}'.format(c1),rank)

                                url = APISERVERURL + '?memberid={}&content={}'.format(memberid, sendmsg)
                                try:
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(url)
                                        if response.status == 200:
                                            data = await response.text()
                                        else:
                                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                                'pg_asqldb:makeproreporttouser 4 error not 200')
                                except Exception as e:
                                    pass
                                await asyncio.sleep(0.1)
                    elif type == 5: # 5. 全部遊戲 累積 銀幣贏分 包含 暫時排名
                        command = 'select betsum_s.memberid,sum(win) as win from betsum_s ,member where ' \
                                  'member.memberid = betsum_s.memberid and member.card >= "{2}" and ' \
                                  'sumdate between "{0}" and "{1}" group by memberid having win >0 order by win desc '.format(startdate.__str__(), yesterdaydate.__str__(),
                                                                    mincard)
                        datalen, data = await self.getdbdata('get type5 proreport',command,True)
                        if datalen > 0:
                            newdata = data.copy()
                            for i in range(len(newdata)):
                                newdata[i]['rank'] = i + 1
                        for item in newdata:
                            win = item.get('win')
                            memberid = item.get('memberid')
                            rank = item.get('rank')
                            sendmsg = content.format(startdate.__str__(), yesterdaydate.__str__(),
                                                     '{:,}'.format(win), rank)

                            url = APISERVERURL + '?memberid={}&content={}'.format(memberid, sendmsg)
                            try:
                                async with aiohttp.ClientSession() as session:
                                    response = await session.get(url)
                                    if response.status == 200:
                                        data = await response.text()
                                    else:
                                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                            'pg_asqldb:makeproreporttouser 5 error not 200')
                            except Exception as e:
                                pass
                            await asyncio.sleep(0.1)
                    elif type ==6: # 金幣與銀幣 一起看單把 倍數排名
                        # 抓 start time and end time
                        utcstartimestr, utcendtimestr = pg_general.get_date_to_utc_start_end_time(startdate)
                        # yesterday_utc_endtime_str,yesterday_date_str
                        command = 'select t1.memberid, max(wintimes div 1) maxwintimes,card from ' \
                                  ' (select memberid, (total_win/total_bet) wintimes from bethistory where bettime between ' \
                                  ' "{0}" and "{1}" having wintimes >0 union all select memberid,(total_win/total_bet) ' \
                                  ' wintimes from bethistory_s where bettime between "{0}" and "{1}" having wintimes >0) ' \
                                  ' t1,member where member.memberid = t1.memberid and member.card >= "{2}" group by t1.memberid ' \
                                  ' order by maxwintimes desc,t1.memberid'.format(utcstartimestr,yesterday_utc_endtime_str,mincard)
                        datalen,data = await self.getdbdata('get type 6 proreport',command,True)
                        if datalen > 0:
                            newdata = data.copy()
                            for i in range(len(newdata)):
                                newdata[i]['rank'] = i + 1
                        for item in newdata:
                            maxwintimes = item.get('maxwintimes')
                            memberid = item.get('memberid')
                            rank = item.get('rank')
                            sendmsg = content.format(startdate.__str__(), yesterdaydate.__str__(),
                                                     '{:,}'.format(maxwintimes), rank)

                            url = APISERVERURL + '?memberid={}&content={}'.format(memberid, sendmsg)
                            try:
                                async with aiohttp.ClientSession() as session:
                                    response = await session.get(url)
                                    if response.status == 200:
                                        data = await response.text()
                                    else:
                                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                            'pg_asqldb:makeproreporttouser 6 error not 200')
                            except Exception as e:
                                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                    'pg_asqldb:makeproreporttouser 6 except:{}'.format(e))
                            await asyncio.sleep(0.1)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makeproreporttouser except:{0}'.format(e))
        pass


    async def force_delete_game(self,seatkey,tempgameid,tempseatnum):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:force_delete_game start,seatkey:{},tempgameid:{},tempseatnum:{}'.format(seatkey,tempgameid,tempseatnum))
            result = False
            clientdata = {"result": False}

            host_id = None
            seatname = None
            if seatkey[:4] == 'gold': # gold
                host_id = PS_HOST_ID
                seatname = 'gseat'
            elif seatkey[:4] == 'silv': # silver
                host_id = PS_HOST_ID_S
                seatname = 'sseat'
            elif seatkey[:4] == 'tuto': # tutorial
                host_id = PS_HOST_ID_T
                seatname = 'tseat'

            seatmemberid = '{}_{}_{}'.format(seatname, tempgameid, tempseatnum)
            url = PS_FORCE_DELETE_GAME.format(host_id,seatmemberid,tempgameid)

            errcount = 0
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response:
                            if response.status == 200:
                                data1 = await response.json()
                                result1 = pg_general.Apiresult.success
                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                    'pg_asqldb:force_delete_game return: {0},url:{1}'.format(
                                                        data1, url))
                                break
                            else:
                                errcount += 1
                                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                    'pg_asqldb:force_delete_game status: {0},url:{1}'.format(
                                                        response.status, url))
                                await asyncio.sleep(0)

                except Exception as e:
                    errcount += 1
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'pg_asqldb:force_delete_game exception 1: {0},errcount:{1}'.format(e, errcount))

            if errcount >= 3:
                result = False
                return result, clientdata
            if data1 != {}:  # 代表有位完成遊戲
                clientdata = {"result": True}

            result = True
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:force_delete_game exception : {0}'.format(e))

        return result, clientdata
    async def getuncompletedgame(self,seatid,tempseatid):
        try:
            result = False
            clientdata = {"result": False}
            # 抓取此玩家 還有的 未完成遊戲
            if tempseatid == 'gseat':
                url = PS_UNCOMPLETEGAME_URL.format(PS_HOST_ID, seatid)
            elif tempseatid == 'sseat':
                url = PS_UNCOMPLETEGAME_URL.format(PS_HOST_ID_S, seatid)
            elif tempseatid == 'tseat':
                url = PS_UNCOMPLETEGAME_URL.format(PS_HOST_ID_T, seatid)
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
                                        'pg_asqldb:getuncompletedgame exception 1: {0},errcount:{1}'.format(e, errcount))

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

    async def openfreewheelaction(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:openfreewheelaction start')

            # get now local date
            nowdate = pg_general.get_tw_datetime().date()
            command = 'select * from action_freewheel where localdate = "{0}"'.format(nowdate)
            datalen, data = await self.getdbdata('get free action wheel',command)
            if datalen ==1:
                await redis_obj.set_value('freewheelaction', 1, 14400)
                await redis_obj.set_value('freewheelaction', 1, 14400)
                await redis_obj.set_value('freewheelaction', 1, 14400)

                acttimes = data.get('act_times')
                await redis_obj.set_value('freewheelaction_acttimes', acttimes, 14400)
                await redis_obj.set_value('freewheelaction_acttimes', acttimes, 14400)
                await redis_obj.set_value('freewheelaction_acttimes', acttimes, 14400)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:openfreewheelaction except:{0}'.format(e))

    async def senddailybonus_notification(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:senddailybonus_notification start')

            # get_local_starttime_utc_str
            starttimestr = pg_general.get_local_starttime_utc_str()
            command = 'select distinct member.fcmtoken ' \
                      ' from memberdailybonus,member where lastspintime < "{0}" ' \
                      ' and member.memberid = memberdailybonus.memberid and fcmtoken not in(" ","0") ' \
                      ' and member.lastlogintime < "{0}" ' \
                      ' order by member.lastlogintime desc limit 5500 '.format(starttimestr)
            datalen , data = await self.getdbdata('get all notification ',command,True)
            list1 = [item.get('fcmtoken') for item in data[:2750]]
            list2 = [item.get('fcmtoken') for item in data[2750:]]

            list1.append('dHnTHNOrKU3uh-NT8DddJg:APA91bFNyW9eST_bvdbQt-hcbEOHZq3GfGMNu52g4oadafmEeUHdWNyDeIBhEc4NwGueHG7eqp_OhrIJ0n4g8o9ouEr-y7rEVoPeAEtg3iKDhn7IotCK8zCyWRQKGpXWtm3eyhSgT_yq')

            title = '金爽娛樂城'
            content = '👉🏻 點擊這裡,領取您的每日轉輪獎金 👈🏻'
            pg_fcm.send_notification_multiple_device(title, content, list1)
            pg_fcm.send_notification_multiple_device(title, content, list2)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:senddailybonus_notification except:{0}'.format(e))

    async def makeclearjobflagandcarddata(self,app):
        try:
            command = 'select clearseatflag from setting2'
            datalen, data = await self.getdbdata('get clearseatflag', command)
            if datalen == 1:
                app['clearseatflag'] = data.get('clearseatflag')


            # get card setting
            command = 'select keepseatseconds from cardinfo order by card'
            datalen, data = await self.getdbdata('get cardinfo', command, True)

            if datalen >0:
                app['keepseatsecondslist'] = data.copy()

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makeclearjobflagandcarddata except:{0}'.format(e))

    async def make_jinsongprize_live(self,redis_obj,app):  # 座金爽榜 及時榜單
        try:
            upload_obj = app['uploadobj']
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:make_jinsongprize_live start')
            twdate = pg_general.get_local_date()

            if twdate.day <= 15:
                betsumstartdate_str = datetime(twdate.year,twdate.month,1).__str__()
            else:
                betsumstartdate_str = datetime(twdate.year,twdate.month,16).__str__()




            # 從 betsum table 抓其他天, 從 bethistory 抓今天
            utcstarttimestr,utcendtimestr = pg_general.get_date_to_utc_start_end_time(pg_general.get_tw_datetime().date())


            betsumdict = {}
            betsumlist = []

            # 先抓 betsum 這個月分全部加總
            command = 'select betsum.memberid,sum(win) as win,card,avatar,nickname,level from betsum,member where member.memberid = betsum.memberid and sumdate >= "{0}"  group by betsum.memberid'.format(betsumstartdate_str)
            datalen, data = await self.getdbdata('get betsum summary',command,True)

            if datalen > 0:
                for item in data:
                    tempmemberidstr = pg_general.converttype(item.get('memberid'),str)
                    tempmemberdict = {
                        "sumwin": pg_general.converttype(item.get('win'),int),
                        "card": item.get('card'),
                        "level": item.get('level'),
                        "nickname": item.get('nickname'),
                        "avatar": item.get('avatar')

                    }
                    betsumdict[tempmemberidstr] = tempmemberdict.copy()


            # 抓 bethistory today
            command = 'select t1.memberid,sum(win) win, card,level,avatar,nickname from (select bethistory.memberid, ' \
                      'sum(total_win) as win from bethistory where bettime between "{0}" and "{1}" group by bethistory.memberid ' \
                      ' union all select bethistory_fish_g.memberid,sum(win) win from bethistory_fish_g where ' \
                      ' resulttime between "{0}" and "{1}" group by bethistory_fish_g.memberid) t1,member ' \
                      ' where member.memberid = t1.memberid group by t1.memberid '.format(utcstarttimestr,utcendtimestr)
            datalen , data = await self.getdbdata('get bethistory summary',command,True)
            if datalen >0:
                for item in data:
                    tempmemberidstr = pg_general.converttype(item.get('memberid'),str)
                    win = pg_general.converttype(item.get('win'),int)
                    if betsumdict.get(tempmemberidstr) is not None:
                        betsumdict[tempmemberidstr]['sumwin'] += win
                    else:
                        betsumdict[tempmemberidstr] = {}
                        betsumdict[tempmemberidstr]['sumwin'] = win
                        betsumdict[tempmemberidstr]['card'] = item.get('card')
                        betsumdict[tempmemberidstr]['level'] = item.get('level')
                        betsumdict[tempmemberidstr]['nickname'] = item.get('nickname')
                        betsumdict[tempmemberidstr]['avatar'] = item.get('avatar')


            for key, value in betsumdict.items():
                value.update({'memberid':pg_general.converttype(key,int)})
                if value.get('sumwin')>0:
                    betsumlist.append(value)

            betsumlist = sorted(betsumlist, key=lambda k: (k['sumwin']), reverse=True)

            # 只留下 100 名
            betsumlist = betsumlist[:100]


            # get redis jinsongprizesetting
            jinsongprizesetting = await redis_obj.get_json_value('jinsongprizesetting')
            jinsongprizesetting = jinsongprizesetting.get('jinsongprizesetting')


            if len(jinsongprizesetting)> 0:
                tempindex = 0
                for item in betsumlist:
                    item.update({"rank": tempindex+1})
                    if tempindex >= len(jinsongprizesetting):
                        item.update({"bonus":0})
                    else:
                        item.update({"bonus": jinsongprizesetting[tempindex].get('reward')})
                    tempindex +=1

            # 做及時差異畫右邊動畫推播
            diff_jinsong_live_dict = await redis_obj.get_json_value('jinsongranklive')
            diff_jinsong_live_memberid_list = []
            if diff_jinsong_live_dict is not None:
                diff_jinsong_live_memberid_list = [item.get('memberid') for item in diff_jinsong_live_dict]

            diff_jinsongprize_broadcast_list = []
            for idx,item in enumerate(betsumlist):
                if idx >=30:
                    break
                tempmemberid = item.get('memberid')
                if tempmemberid not in diff_jinsong_live_memberid_list[:idx+1]:
                    diff_jinsongprize_broadcast_list.append({
                        "memberid": tempmemberid,
                        "nickname": item.get('nickname'),
                        "avatar": item.get('avatar'),
                        "rank": item.get('rank'),
                        "sumwin": item.get('sumwin')
                    })


            # 抓昨天的來比較找出進步的差異
            yesterday_date_str = (pg_general.get_tw_datetime() - timedelta(days=1)).date().__str__()
            kk = 'jinsongranklive_{}'.format(yesterday_date_str)
            old_jinsong_rank_data = await redis_obj.get_json_value(kk)

            tempindex =0
            if old_jinsong_rank_data is None:
                templist = []
                tempsumwinlist = []
            else:
                templist = [item.get('memberid') for item in old_jinsong_rank_data]
                tempsumwinlist = [item.get('sumwin') for item in old_jinsong_rank_data]

            for tempitem in betsumlist:
                if tempitem.get('memberid') not in templist[0:tempindex+1]:
                    tempitem.update({'progressflag': 1,'winincressflag':1})
                else:
                    tempitem.update({'progressflag': 0})
                    # find old sumwin
                    oldindex = templist[0:tempindex+1].index(tempitem.get('memberid'))
                    oldsumwin = tempsumwinlist[oldindex]
                    newsumwin = tempitem.get('sumwin')
                    if newsumwin > oldsumwin:
                        tempitem.update({'winincressflag': 1})
                    else:
                        tempitem.update({'winincressflag': 0})
                tempindex += 1



            # set to redis
            await redis_obj.set_json_value("jinsongranklive",betsumlist)

            await redis_obj.set_json_value('jinsongranklive_{}'.format(twdate.__str__()),betsumlist,86400*2)        # 保留兩天

            asyncio.ensure_future(self.upload_jinsong_rank_data_to_bucket(betsumlist,upload_obj))


            # clear db jinsongprizelive
            command = 'delete from jinsongprizelive'
            upateresult = await self.updatedbdata('delete jinsongprizelive table',command)

            # insert new jinsongprizelive data
            command = 'insert into jinsongprizelive (rank,memberid,nickname,avatar,card,level,sumwin,bonus) values(%s,%s,%s,%s,%s,%s,%s,%s)'

            params = []
            for item in betsumlist:
                params.append([
                    item.get('rank'),
                    item.get('memberid'),
                    item.get('nickname'),
                    item.get('avatar'),
                    item.get('card'),
                    item.get('level'),
                    item.get('sumwin'),
                    item.get('bonus')
                ])

            resultinsert, insertindex = await self.insertdbdata('insert jinsongprizelive', command, many=True,
                                                                manydata=params)

            if len(diff_jinsongprize_broadcast_list)>0:
                sendmsg = {"type": 0, "msg": {"commandid": 3000026, "ranking": diff_jinsongprize_broadcast_list}}
                # get lobby server ips
                if env_setting.LOCAL_SERVER == False:
                    command = 'select ip from lobbyserversetting'
                    datalen, data = await self.getdbdata('get all lobby server ips', command, True)
                    if datalen > 0:
                        try:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
                            lobbyserverips = data
                            if lobbyserverips != []:
                                for item in lobbyserverips:
                                    realurl = 'http://{0}/broadcasttoall'.format(item.get('ip'))
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(realurl, json=sendmsg)
                                        if response.status == 200:
                                            data = await response.text()
                                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                'send_to_all_lobbyserver_future response:{0}'.format(
                                                                    data))
                                    await asyncio.sleep(0)

                        except Exception as e:
                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                'send_to_all_lobbyserver , except:{0}'.format(e))
                        finally:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , done')

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_jinsongprize_live except:{}'.format(e))

    async def make_rank_diff(self,redis_obj,jsoncontent,rankmode):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:make_rank_diff start:{}'.format(jsoncontent))

            oldtopwinrankdictlive = jsoncontent.get("oldtopwinrankdictlive")            # 舊龍榜
            oldtopmultipilierdictlive = jsoncontent.get("oldtopmultipilierdictlive")    # 舊虎榜
            topwinrankdict = jsoncontent.get("topwinrankdict")                          # 新龍榜
            topmultipilierrankdict = jsoncontent.get("topmultipilierrankdict")          # 新虎榜
            gameidnamemap = jsoncontent.get('gameidnamemap')                            # gameid gamename mapping
            chatrankdragoncontent = jsoncontent.get('chatrankdragoncontent')            # 龍榜 頻道丟的上榜訊息
            chatranktigercontent = jsoncontent.get('chatranktigercontent')              # 虎榜 頻道丟的上榜訊息

            difflist = []       # 有差異要廣播的榜單
            chatmsg = []        # 頻道要丟的龍虎榜上榜訊息

            # 比對龍榜
            for gameid,tempvalue in topwinrankdict.items():
                oldrankvalue = oldtopwinrankdictlive.get(gameid)
                if oldrankvalue is None:
                    oldrankvalue = []
                # 第一名 比對
                newrank = []
                oldrank = []
                for item in tempvalue:
                    if item.get('rank') in [1]:
                        newrank = [{"memberid":item.get('memberid')},{"nickname":item.get('nickname'),"avatar":item.get('avatar'),"rank":item.get('rank'),"amount":item.get('amount')}]
                oldrank = [{"memberid":item.get('memberid')} for item in oldrankvalue if item.get('rank') in [1]]

                if len(newrank) ==0:
                    continue
                if newrank[0] not in oldrank:
                    difflist.append({
                        "gameid": gameid,
                        "ranktype": 1,      # 龍榜
                        "amount": newrank[1].get('amount'),
                        "memberid": newrank[0].get('memberid'),
                        "nickname": newrank[1].get('nickname'),
                        "avatar": newrank[1].get('avatar'),
                        "rank": newrank[1].get('rank')

                    })
                    chatmsg.append({
                        'content':chatrankdragoncontent.format(newrank[1].get('nickname'),gameidnamemap[gameid],newrank[1].get('rank')),
                        'bubblememberid': newrank[0].get('memberid'),
                        'bubblenickname': newrank[1].get('nickname'),
                        'bubbleavatar': newrank[1].get('avatar')
                    })

                #第二名比對
                newrank = []
                oldrank = []
                for item in tempvalue:
                    if item.get('rank') in [2]:
                        newrank = [{"memberid": item.get('memberid')},{"nickname": item.get('nickname'), "avatar": item.get('avatar'), "rank": item.get('rank'),"amount": item.get('amount')}]
                oldrank = [{"memberid": item.get('memberid')} for item in oldrankvalue if item.get('rank') in [1,2]]
                if len(newrank) == 0:
                    continue
                if newrank[0] not in oldrank:
                    difflist.append({
                        "gameid": gameid,
                        "ranktype": 1,  # 龍榜
                        "amount": newrank[1].get('amount'),
                        "memberid": newrank[0].get('memberid'),
                        "nickname": newrank[1].get('nickname'),
                        "avatar": newrank[1].get('avatar'),
                        "rank": newrank[1].get('rank')

                    })
                    chatmsg.append({
                        'content':chatrankdragoncontent.format(newrank[1].get('nickname'), gameidnamemap[gameid],
                                                                newrank[1].get('rank')),
                        'bubblememberid': newrank[0].get('memberid'),
                        'bubblenickname': newrank[1].get('nickname'),
                        'bubbleavatar': newrank[1].get('avatar')

                    })

                # 第三名比對
                newrank = []
                oldrank = []
                for item in tempvalue:
                    if item.get('rank') in [3]:
                        newrank = [{"memberid": item.get('memberid')},{"nickname": item.get('nickname'), "avatar": item.get('avatar'), "rank": item.get('rank'), "amount": item.get('amount')}]
                oldrank = [{"memberid": item.get('memberid')} for item in oldrankvalue if item.get('rank') in [1, 2,3]]
                if len(newrank) == 0:
                    continue
                if newrank[0] not in oldrank:
                    difflist.append({
                        "gameid": gameid,
                        "ranktype": 1,  # 龍榜
                        "amount": newrank[1].get('amount'),
                        "memberid": newrank[0].get('memberid'),
                        "nickname": newrank[1].get('nickname'),
                        "avatar": newrank[1].get('avatar'),
                        "rank": newrank[1].get('rank')

                    })
                    chatmsg.append({
                        'content':chatrankdragoncontent.format(newrank[1].get('nickname'), gameidnamemap[gameid],
                                                                newrank[1].get('rank')),
                        'bubblememberid': newrank[0].get('memberid'),
                        'bubblenickname': newrank[1].get('nickname'),
                        'bubbleavatar': newrank[1].get('avatar')

                    })
            # 比對虎榜
            for gameid,tempvalue in topmultipilierrankdict.items():
                oldrankvalue = oldtopmultipilierdictlive.get(gameid)
                if oldrankvalue is None:
                    oldrankvalue = []
                # 第一名 比對
                newrank = []
                oldrank = []
                for item in tempvalue:
                    if item.get('rank') in [1]:
                        newrank = [{"memberid":item.get('memberid')},{"nickname":item.get('nickname'),"avatar":item.get('avatar'),"rank":item.get('rank'),"amount":item.get('amount')}]
                oldrank = [{"memberid":item.get('memberid')} for item in oldrankvalue if item.get('rank') in [1]]

                if len(newrank) ==0:
                    continue
                if newrank[0] not in oldrank:
                    difflist.append({
                        "gameid": gameid,
                        "ranktype": 0,      # 虎榜
                        "amount": newrank[1].get('amount'),
                        "memberid": newrank[0].get('memberid'),
                        "nickname": newrank[1].get('nickname'),
                        "avatar": newrank[1].get('avatar'),
                        "rank": newrank[1].get('rank')

                    })
                    chatmsg.append({
                        'content':chatranktigercontent.format(newrank[1].get('nickname'), gameidnamemap[gameid],
                                                                newrank[1].get('rank')),
                        'bubblememberid': newrank[0].get('memberid'),
                        'bubblenickname': newrank[1].get('nickname'),
                        'bubbleavatar': newrank[1].get('avatar')
                    })

                #第二名比對
                newrank = []
                oldrank = []
                for item in tempvalue:
                    if item.get('rank') in [2]:
                        newrank = [{"memberid": item.get('memberid')},{"nickname": item.get('nickname'), "avatar": item.get('avatar'), "rank": item.get('rank'), "amount": item.get('amount')}]
                oldrank = [{"memberid": item.get('memberid')} for item in oldrankvalue if item.get('rank') in [1,2]]
                if len(newrank) == 0:
                    continue
                if newrank[0] not in oldrank:
                    difflist.append({
                        "gameid": gameid,
                        "ranktype": 0,  # 虎榜
                        "amount": newrank[1].get('amount'),
                        "memberid": newrank[0].get('memberid'),
                        "nickname": newrank[1].get('nickname'),
                        "avatar": newrank[1].get('avatar'),
                        "rank": newrank[1].get('rank')

                    })
                    chatmsg.append({
                        'content':chatranktigercontent.format(newrank[1].get('nickname'), gameidnamemap[gameid],
                                                               newrank[1].get('rank')),
                        'bubblememberid': newrank[0].get('memberid'),
                        'bubblenickname': newrank[1].get('nickname'),
                        'bubbleavatar': newrank[1].get('avatar')
                    })

                # 第三名比對
                newrank = []
                oldrank = []
                for item in tempvalue:
                    if item.get('rank') in [3]:
                        newrank = [{"memberid": item.get('memberid')},{"nickname": item.get('nickname'), "avatar": item.get('avatar'), "rank": item.get('rank'), "amount": item.get('amount')}]
                oldrank = [{"memberid": item.get('memberid')} for item in oldrankvalue if item.get('rank') in [1, 2,3]]
                if len(newrank) == 0:
                    continue
                if newrank[0] not in oldrank:
                    difflist.append({
                        "gameid": gameid,
                        "ranktype": 0,  # 虎榜
                        "amount": newrank[1].get('amount'),
                        "memberid": newrank[0].get('memberid'),
                        "nickname": newrank[1].get('nickname'),
                        "avatar": newrank[1].get('avatar'),
                        "rank": newrank[1].get('rank')

                    })
                    chatmsg.append({
                        'content':chatranktigercontent.format(newrank[1].get('nickname'), gameidnamemap[gameid],
                                                               newrank[1].get('rank')),
                        'bubblememberid': newrank[0].get('memberid'),
                        'bubblenickname': newrank[1].get('nickname'),
                        'bubbleavatar': newrank[1].get('avatar')
                    })
            if len(difflist)>0 and rankmode==2:
                sendmsg = {"type": 0, "msg": {"commandid": 3000025, "ranking": difflist}}
                # get lobby server ips
                if env_setting.LOCAL_SERVER == False:
                    command = 'select ip from lobbyserversetting'
                    datalen, data = await self.getdbdata('get all lobby server ips', command, True)
                    if datalen > 0:
                        try:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
                            lobbyserverips = data
                            if lobbyserverips != []:
                                for item in lobbyserverips:
                                    realurl = 'http://{0}/broadcasttoall'.format(item.get('ip'))
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(realurl, json=sendmsg)
                                        if response.status == 200:
                                            data = await response.text()
                                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                'send_to_all_lobbyserver_future response:{0}'.format(data))
                                    await asyncio.sleep(0)

                        except Exception as e:
                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                'send_to_all_lobbyserver , except:{0}'.format(e))
                        finally:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , done')

            if len(chatmsg) > 0 and rankmode == 2:
                # call apiserver chat channel
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                    'sendtochannelbigprize')
                for item in chatmsg:
                    try:
                        content = item.get('content')
                        bubblememberid = item.get('bubblememberid')
                        bubblenickname = item.get('bubblenickname')
                        bubbleavatar = item.get('bubbleavatar')
                        sendmsg = content
                        url = APISERVER_CHANNEL_CHAT_URL.format(3, sendmsg,bubblememberid,bubblenickname,bubbleavatar)
                        returndata = 'error'

                        # 將龍虎榜前三名公告，從「打屁啦頻道」channelindex=3，移除不公告了。
                        # async with aiohttp.ClientSession() as session:
                        #     response = await session.get(url)
                        #     if response.status == 200:
                        #         returndata = await response.text()



                    except Exception as e:
                       pass
                    finally:
                        asyncio.sleep(0.1)



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_rank_diff except:{}'.format(e))


    async def make_new_dragon_tiger_rank_live(self,redis_obj,app,upload_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:make_new_dragon_tiger_rank_live start')

            gamesetting = []    # 遊戲設定值

            # get rankmode
            rankmode = await self.get_rank_mode()
            if rankmode == -1:
                raise Exception('get rank mode error')

            # 抓 setting.chatrankdragoncontent , setting.chatranktigercontent
            command = 'select chatrankdragoncontent,chatranktigercontent from setting'
            datalen , data = await self.getdbdata('get chatranktigercontent',command)
            if datalen != 1:
                raise Exception('get chatranktigercontent error')

            chatrankdragoncontent = data.get('chatrankdragoncontent')
            chatranktigercontent = data.get('chatranktigercontent')

            # 抓 龍虎榜上榜設定
            command ='select gameindex,gameid,gamename,rankminibet,rankminiwin,rankminimultipilier,rankdescription,rankprize,rankweekprize,ranktype from game where enable = 1'
            datalen , data = await self.getdbdata('get game setting',command,True)
            if datalen <= 0 :
                raise Exception('get get setting error')

            gamesetting = data.copy()
            gamerankprize = {}
            gamerankweekprize = {}
            gameidlist = []
            topwinrankdict = {}
            topmultipilierrankdict = {}
            dbjinsonggameranklivedata = []      # for write db jinsonggameranklivedata
            gameranktoponelive = {}             # for lobby to show top one on each game

            gameidnamemap = {}
            gameranktype = {}
            gameindexdict = {}
            for item in gamesetting:
                gameid = item.get('gameid')
                gameidnamemap[gameid]= item.get('gamename')
                rankprize = item.get('rankprize')
                rankweekprize = item.get('rankweekprize')
                gamerankprize.update({gameid:json.loads(rankprize)})
                gamerankweekprize.update({gameid:json.loads(rankweekprize)})
                tmpranktype = item.get('ranktype')
                gameranktype.update({gameid:tmpranktype})
                gameindexdict.update({gameid:item.get('gameindex')})
                gameidlist.append(gameid)

            # 抓今天 utc start and end time
            localdate = pg_general.get_local_date()
            utcstarttimestr , utcendtimestr = pg_general.get_date_to_utc_start_end_time(localdate)

            command_topwin  = ''
            command_topmultipilier = ''
            # make union command
            for item in data:

                rankminibet = item.get('rankminibet')
                rankminiwin = item.get('rankminiwin')
                rankminimultipilier = item.get('rankminimultipilier')
                tempgameid = item.get('gameid')
                ranktype = item.get('ranktype')
                if command_topwin != '':
                    command_topwin += ' union all '

                if ranktype ==0 : # 金幣榜
                    dbtype = 'bethistory'
                else:               # 銀幣榜
                    dbtype = 'bethistory_s'
                command_topwin += 'select t1.gameid,t1.memberid,t1.sumwin div 1 as amount,card,nickname,level,avatar from member,(select gameid,memberid,sum(total_win) as sumwin ' \
                          'from {5} where bettime between "{0}" and "{1}" and total_bet >= "{2}" and total_win >= "{3}" ' \
                          ' and gameid = "{4}" group by memberid) as t1 where member.memberid= t1.memberid'.format(utcstarttimestr,utcendtimestr,rankminibet,rankminiwin,tempgameid,dbtype)


                if command_topmultipilier != '':
                    command_topmultipilier += ' union all '
                command_topmultipilier += 'select t1.gameid,t1.memberid,t1.summultipilier div 1 as amount,card,nickname,level,avatar from member, (select gameid,memberid,sum(total_win/total_bet) as summultipilier ' \
                          'from {5} where bettime between "{0}" and "{1}" and total_bet >= "{2}" and (total_win/total_bet) >= "{3}" ' \
                          ' and gameid = "{4}" group by memberid) as t1 where member.memberid=t1.memberid'.format(utcstarttimestr,utcendtimestr,rankminibet,rankminimultipilier,tempgameid,dbtype)

            if command_topwin == '' or command_topmultipilier == '':
                raise Exception('command error')

            rankInfoList = []

            # 龍綁
            datalen , data = await self.getdbdata('get dragon rank',command_topwin,True)
            if datalen >0:
                # 整理 data
                for itemgameid in gameidlist:
                    templist = [item for item in data if item.get('gameid')==itemgameid]
                    templist = sorted(templist, key=lambda k: (k['amount']), reverse=True)  # sort rank
                    # 只留下前面一百名
                    templist = templist[:100]
                    topwinrankprizelist = gamerankprize.get(itemgameid).get('topwin')
                    for index in range(len(templist)):
                        templist[index].update({"rank":index+1})
                        templist[index].update({"ranktype": gameranktype[itemgameid]})
                        if index < len(topwinrankprizelist):
                            templist[index].update({"extraaward":topwinrankprizelist[index]})
                        else:
                            templist[index].update({"extraaward":0})
                        dbjinsonggameranklivedata.append([
                            1,  # type top win
                            templist[index].get('amount'),
                            templist[index].get('gameid'),
                            templist[index].get('memberid'),
                            templist[index].get('extraaward'),
                            templist[index].get('avatar'),
                            templist[index].get('nickname'),
                            templist[index].get('card'),
                            templist[index].get('level'),
                            templist[index].get('rank'),
                            gameranktype[templist[index].get('gameid')] # ranktype
                        ])
                    topwinrankdict.update({itemgameid: templist})
                    # 只抓第一名資料
                    if len(templist) > 0:
                        topwinavatar = "" if templist[0].get('avatar') is None else templist[0].get('avatar')
                        topwin = templist[0].get('amount')
                        topwinnickname = templist[0].get('nickname')
                        topwinmemberid = templist[0].get('memberid')
                    else:
                        topwinavatar = ""
                        topwin = -1
                        topwinnickname = ''
                        topwinmemberid = 0
                    gameranktoponelive.update({itemgameid: {
                        "topwinavatar": topwinavatar,
                        "topwin": topwin,
                        "topwinnickname": topwinnickname,
                        "topwinmemberid": topwinmemberid
                    }})


            # 虎綁
            datalen, data = await self.getdbdata('get tiger rank',command_topmultipilier,True)
            if datalen > 0:
                # 整理 data
                for itemgameid in gameidlist:
                    templist = [item for item in data if item.get('gameid')==itemgameid]
                    templist = sorted(templist, key=lambda  k:(k['amount']), reverse=True)

                    # 只留下前面一百名
                    templist = templist[:100]

                    topmultipilierprizelist = gamerankprize.get(itemgameid).get('topmultipilier')
                    for index in range(len(templist)):
                        templist[index].update({"rank":index+1})
                        templist[index].update({"ranktype": gameranktype[itemgameid]})
                        if index < len(topmultipilierprizelist):
                            templist[index].update({"extraaward":topmultipilierprizelist[index]})
                        else:
                            templist[index].update({"extraaward":0})

                        dbjinsonggameranklivedata.append([
                            0,  # type top multipilier
                            templist[index].get('amount'),
                            templist[index].get('gameid'),
                            templist[index].get('memberid'),
                            templist[index].get('extraaward'),
                            templist[index].get('avatar'),
                            templist[index].get('nickname'),
                            templist[index].get('card'),
                            templist[index].get('level'),
                            templist[index].get('rank'),
                            gameranktype[templist[index].get('gameid')]
                        ])

                    topmultipilierrankdict.update({itemgameid:templist})
                    # 只抓第一名資料
                    if len(templist)> 0:
                        topmultiplieravatar = "" if templist[0].get('avatar') is None else templist[0].get('avatar')
                        topmultiplier = templist[0].get('amount')
                        topmultipliernickname = templist[0].get('nickname')
                        topmultipliermemberid = templist[0].get('memberid')
                    else:
                        topmultiplieravatar = ""
                        topmultiplier = -1
                        topmultipliernickname = ''
                        topmultipliermemberid = 0
                    gameranktoponelive[itemgameid].update({
                        "topmultiplieravatar": topmultiplieravatar,
                        "topmultiplier": topmultiplier,
                        "topmultipliernickname": topmultipliernickname,
                        "topmultipliermemberid": topmultipliermemberid
                    })


            oldtopwinrankdictlive = await redis_obj.get_json_value('topwinrankdictlive')
            oldtopmultipilierdictlive = await redis_obj.get_json_value('topmultipilierdictlive')
            if oldtopwinrankdictlive is None:
                oldtopwinrankdictlive = {}
            if oldtopmultipilierdictlive is None:
                oldtopmultipilierdictlive = {}
            await redis_obj.set_json_value('topwinrankdictlive',topwinrankdict)
            await redis_obj.set_json_value('topmultipilierdictlive',topmultipilierrankdict)

            jsoncontent = {
                "oldtopwinrankdictlive":oldtopwinrankdictlive,
                "oldtopmultipilierdictlive":oldtopmultipilierdictlive,
                "topwinrankdict": topwinrankdict,
                "topmultipilierrankdict": topmultipilierrankdict,
                "gameidnamemap": gameidnamemap,
                "chatrankdragoncontent": chatrankdragoncontent,
                "chatranktigercontent": chatranktigercontent
            }
            # 先做 upload to bucket 的處理
            asyncio.ensure_future(self.upload_rank_data_to_bucket({"gamename": gameidnamemap,"topwin":topwinrankdict,"topmultipilier":topmultipilierrankdict},upload_obj))

            asyncio.ensure_future(self.make_rank_diff(redis_obj,jsoncontent,rankmode))       # 找出差異榜單前三名並廣播

            # 做搶榜推薦
            asyncio.ensure_future(self.makerankpush(topwinrankdict,topmultipilierrankdict,gameranktype,gameindexdict,gamerankprize))


            # clear db jinsonggameranklive
            command = 'delete from jinsonggameranklive'
            del_result = await self.updatedbdata('delete jinsonggameranklive',command)

            # write to db
            command = 'insert into jinsonggameranklive (type,amount,gameid,memberid,extraaward,avatar,nickname,card,level,rank,ranktype) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            updateresult, affectrows = await self.insertdbdata('insert jinsonggameranklive',command,many=True,manydata=dbjinsonggameranklivedata)

            # 做 周冠 live
            # 抓這周的起始以及結束的日期
            weekstartdate = localdate - timedelta(days=((localdate.weekday()+1)%7))
            weekenddate = localdate + timedelta(days=(6-((localdate.weekday()+1)%7)))

            command_week_rank = 'select t1.type,t1.gameid,t1.memberid,t1.amount,member.avatar,member.card,member.`level`,member.nickname from member, ' \
                                '(select type,gameid,memberid,sum(amount) div 1 as amount from jinsonggamerankdaysettle ' \
                                'where rankdate >= "2020-08-01" and rankdate between "{0}" and "{1}" group by type,gameid,memberid) as t1 ' \
                                'where member.memberid = t1.memberid '.format(weekstartdate.__str__(),weekenddate.__str__())
            datalen,data = await self.getdbdata('get week rank data',command_week_rank,True)


            weekranktopwindict = topwinrankdict.copy()      # 先將今天的值 放入
            weekranktopmultipilierdict = topmultipilierrankdict.copy() # 先將今天的值 放入

            # 拿掉 extraaward and rank
            for tempgameid,tempgamevalue in weekranktopwindict.items():
                tempvalue = []
                for tempitem in tempgamevalue:
                    if tempitem.get('extraaward') is not None:
                        tempitem.pop('extraaward')
                    if tempitem.get('rank') is not None:
                        tempitem.pop('rank')
                    tempvalue.append(tempitem)
            for tempgameid,tempgamevalue in weekranktopmultipilierdict.items():
                tempvalue = []
                for tempitem in tempgamevalue:
                    if tempitem.get('extraaward') is not None:
                        tempitem.pop('extraaward')
                    if tempitem.get('rank') is not None:
                        tempitem.pop('rank')
                    tempvalue.append(tempitem)





            weekranktopwinlist = []
            weekranktopmultipilierlist = []
            if datalen > 0:
                weekranktopwinlist = [item for item in data if item.get('type')==1]
                weekranktopmultipilierlist = [item for item in data if item.get('type') == 0]

            # 龍綁
            for item in weekranktopwinlist:
                tempgameid = item.get('gameid')
                tempamount = item.get('amount')
                tempavatar = item.get('avatar')
                tempcard = item.get('card')
                templevel = item.get('level')
                tempmemberid = item.get('memberid')
                tempnickname = item.get('nickname')
                temptype = item.get('type')


                temptodaygamerank = weekranktopwindict.get(tempgameid)
                if temptodaygamerank is None:
                    temptodaygamerank = []
                findflag = False
                tempindex = 0
                for tempitem in temptodaygamerank:
                    if tempitem.get('memberid') == tempmemberid:
                        findflag = True
                        break
                    tempindex += 1
                if findflag == True:
                    temptodaygamerank[tempindex]['amount'] += tempamount
                else:
                    temptodaygamerank.append({
                        "amount": tempamount,
                        "avatar": tempavatar,
                        "card": tempcard,
                        "gameid": tempgameid,
                        "level": templevel,
                        "memberid": tempmemberid,
                        "nickname": tempnickname
                    })
                weekranktopwindict.update({tempgameid:temptodaygamerank})
            # 虎綁
            for item in weekranktopmultipilierlist:
                tempgameid = item.get('gameid')
                tempamount = item.get('amount')
                tempavatar = item.get('avatar')
                tempcard = item.get('card')
                templevel = item.get('level')
                tempmemberid = item.get('memberid')
                tempnickname = item.get('nickname')
                temptype = item.get('type')


                temptodaygamerank = weekranktopmultipilierdict.get(tempgameid)
                if temptodaygamerank is None:
                    temptodaygamerank = []
                findflag = False
                tempindex = 0
                for tempitem in temptodaygamerank:
                    if tempitem.get('memberid') == tempmemberid:
                        findflag = True
                        break
                    tempindex += 1
                if findflag == True:
                    temptodaygamerank[tempindex]['amount'] += tempamount
                else:
                    temptodaygamerank.append({
                        "amount": tempamount,
                        "avatar": tempavatar,
                        "card": tempcard,
                        "gameid": tempgameid,
                        "level": templevel,
                        "memberid": tempmemberid,
                        "nickname": tempnickname
                    })
                weekranktopmultipilierdict.update({tempgameid:temptodaygamerank})

            # 排序
            for tempgameid,tempgamevalue in weekranktopwindict.items():
                tempgamevalue = sorted(tempgamevalue, key=lambda k: (k['amount']),reverse=True)
                # 留下 100 名
                tempgamevalue = tempgamevalue[:100]

                # get weekly reward
                weektopwinprize = gamerankweekprize[tempgameid].get('topwin')

                for rankindex in range(len(tempgamevalue)):
                    if rankindex < len(weektopwinprize):
                        tempprize = weektopwinprize[rankindex]
                    else:
                        tempprize = 0
                    tempgamevalue[rankindex].update({"rank":rankindex+1,"extraaward":tempprize})

                weekranktopwindict.update({tempgameid: tempgamevalue})


            for tempgameid,tempgamevalue in weekranktopmultipilierdict.items():
                tempgamevalue = sorted(tempgamevalue , key=lambda  k: (k['amount']),reverse=True)
                # 留下 100 名
                tempgamevalue = tempgamevalue[:100]

                # get weekly reward
                weektopmultipilierprize = gamerankweekprize[tempgameid].get('topmultipilier')

                for rankindex in range(len(tempgamevalue)):
                    if rankindex < len(weektopmultipilierprize):
                        tempprize = weektopmultipilierprize[rankindex]
                    else:
                        tempprize = 0
                    tempgamevalue[rankindex].update({"rank":rankindex+1,"extraaward":tempprize})

                weekranktopmultipilierdict.update({tempgameid: tempgamevalue})

            await redis_obj.set_json_value('topweekwinrankdictlive', weekranktopwindict)
            await redis_obj.set_json_value('topweekmultipilierdictlive', weekranktopmultipilierdict)

            # prepare db data
            db_weekranklivedata = []

            for tempgameid,tempgamevalue in weekranktopwindict.items():
                for itemtemp in tempgamevalue:
                    db_weekranklivedata.append([
                        1,          # type
                        itemtemp.get('gameid'),     # gameid
                        itemtemp.get('memberid'),   # memberid
                        itemtemp.get('amount'),     # amount
                        itemtemp.get('extraaward'), # extraaward
                        itemtemp.get('nickname'),   # nickname
                        itemtemp.get('card'),       # card
                        itemtemp.get('level'),      # level
                        itemtemp.get('avatar'),      # avatar
                        itemtemp.get('rank'),         # rank
                        gameranktype[itemtemp.get('gameid')]    # ranktype
                    ])

            for tempgameid , tempgamevalue in weekranktopmultipilierdict.items():
                for itemtemp in tempgamevalue:
                    db_weekranklivedata.append([
                        0,          # type
                        itemtemp.get('gameid'),     # gameid
                        itemtemp.get('memberid'),   # memberid
                        itemtemp.get('amount'),     # amount
                        itemtemp.get('extraaward'), # extraaward
                        itemtemp.get('nickname'),   # nickname
                        itemtemp.get('card'),       # card
                        itemtemp.get('level'),      # level
                        itemtemp.get('avatar'),      # avatar
                        itemtemp.get('rank'),        # rank
                        gameranktype[itemtemp.get('gameid')]    # ranktype

                    ])


            # clear db table jinsonggamerankweeklive
            command = 'delete from jinsonggamerankweeklive'
            del_result = await self.updatedbdata('del table jinsonggamerankweeklive',command)

            command = 'insert into jinsonggamerankweeklive (type,gameid,memberid,amount,extraaward,nickname,card,level,avatar,rank,ranktype) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            insertresult, affectrows = await self.insertdbdata('insert into jinsonggamerankweeklive',command, many=True,manydata=db_weekranklivedata)


            # send broadcast gameranktoponelive
            if gameranktoponelive != {} and rankmode==2:
                sendmsg = {"type": 0, "msg": {"commandid": 3000024, "gamelist": gameranktoponelive}}
                # get lobby server ips
                if env_setting.LOCAL_SERVER == False:
                    command = 'select ip from lobbyserversetting'
                    datalen, data = await self.getdbdata('get all lobby server ips', command, True)
                    if datalen > 0:
                        try:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
                            lobbyserverips = data
                            if lobbyserverips != []:
                                for item in lobbyserverips:
                                    realurl = 'http://{0}/broadcasttoall'.format(item.get('ip'))
                                    async with aiohttp.ClientSession() as session:
                                        response = await session.get(realurl, json=sendmsg)
                                        if response.status == 200:
                                            data = await response.text()
                                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                                'send_to_all_lobbyserver_future response:{0}'.format(data))
                                    await asyncio.sleep(0)

                        except Exception as e:
                            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                                'send_to_all_lobbyserver , except:{0}'.format(e))
                        finally:
                            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                'send_to_all_lobbyserver , done')

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:make_new_dragon_tiger_rank_live except:{}'.format(e))

    async def makerankpush(self,topwindict,topmultipilierdict,gameranktype,gameindexdict,gamerankprize):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makerankpush start')

            rankpushlist = []
            for tempgameid,tempvalue in gamerankprize.items():
                topwinprizelist = tempvalue.get('topwin')
                topmultipilierprizelist =tempvalue.get('topmultipilier')
                tempranktype = gameranktype[tempgameid]
                tempgameindex = gameindexdict[tempgameid]
                tempnumber = 0
                for idx, tempprize in enumerate(topwinprizelist):
                    if topwindict.get(tempgameid) is None:
                        tempamount = None
                    elif idx +1 > len(topwindict[tempgameid]):
                        tempamount = None
                    else:
                        tempamount = topwindict[tempgameid][idx].get('amount')
                    if tempamount is None:
                        tempnumber += tempprize
                    elif tempamount <= 10000:
                        tempnumber += tempprize
                for idx,tempprize in enumerate(topmultipilierprizelist):
                    if topmultipilierdict.get(tempgameid) is None:
                        tempamount = None
                    elif idx + 1> len(topmultipilierdict[tempgameid]):
                        tempamount = None
                    else:
                        tempamount = topmultipilierdict[tempgameid][idx].get('amount')
                    if tempamount is None:
                        tempnumber += tempprize
                    elif tempamount <= 100:
                        tempnumber += tempprize
                rankpushlist.append({
                    "gameid": tempgameid,
                    "ranktype": tempranktype,
                    "number": tempnumber,
                    "gameindex": tempgameindex
                })
            newranklist = sorted(rankpushlist ,key = lambda k:(k['ranktype'], -k['number']))

            # 抽取變成 gameindex
            writerankpushlist = [pg_general.converttype(item.get('gameindex'),str) for item in newranklist]
            writerankpushstr = ','.join(writerankpushlist)

            command = 'update chapterInfo set goodranklist = "{0}" where chapterInfoindex = 1'.format(writerankpushstr)
            updateresult = await self.updatedbdata("update goodranklist",command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makerankpush except:{}'.format(e))


    async def makejinsonggamedayranksettle(self,redis_obj,app,date=None): # 新的 金爽龍虎榜 日冠結算
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:makejinsonggamedayranksettle start')

            # 抓榜單模式　是否是舊版本　或是新版本
            command = 'select rankmode from setting2'
            datalen, data = await self.getdbdata('get rankmode from setting2',command)
            if datalen != 1:
                raise Exception('get rankmode error')

            if data.get('rankmode') ==1:        # 舊模式不做處理
                return
            twtodaydate = pg_general.get_local_date()
            if date is not None:
                twtodaydate = date
            # 抓昨天的 utc start , end time str
            twyesterdaydate = twtodaydate - timedelta(days=1)
            yesterday_utc_starttime_str, yesterday_utc_endtime_str = pg_general.get_date_to_utc_start_end_time(twyesterdaydate)

            gamesetting = []  # 遊戲設定值

            # 抓 龍虎榜上榜設定
            command = 'select gameid,gamename,rankminibet,rankminiwin,rankminimultipilier,rankdescription,rankprize,ranktype from game where enable = 1'
            datalen, data = await self.getdbdata('get game setting', command, True)
            if datalen <= 0:
                raise Exception('get get setting error')

            gamesetting = data.copy()
            gamerankprize = {}
            gameidlist = []
            gamenamedict = {}
            topwinrankdict = {}
            topmultipilierrankdict = {}
            dbjinsonggamerankdaysettledata = []
            gameranktype = {}


            for item in gamesetting:
                gameid = item.get('gameid')
                rankprize = item.get('rankprize')
                gamerankprize.update({gameid: json.loads(rankprize)})
                gameidlist.append(gameid)
                gamenamedict.update({gameid:item.get('gamename')})
                gameranktype.update({gameid:item.get('ranktype')})

            command_topwin = ''
            command_topmultipilier = ''
            # make union command
            for item in data:
                rankminibet = item.get('rankminibet')
                rankminiwin = item.get('rankminiwin')
                rankminimultipilier = item.get('rankminimultipilier')
                tempgameid = item.get('gameid')
                tempranktype = item.get('ranktype')
                if tempranktype == 0 :
                    dbtype = 'bethistory'
                else:
                    dbtype = 'bethistory_s'
                if command_topwin != '':
                    command_topwin += ' union all '

                command_topwin += 'select t1.gameid,t1.memberid,t1.sumwin div 1 as amount,card,nickname,level,avatar from member,(select gameid,memberid,sum(total_win) as sumwin ' \
                                  'from {5} where bettime between "{0}" and "{1}" and total_bet >= "{2}" and total_win >= "{3}" ' \
                                  ' and gameid = "{4}" group by memberid) as t1 where member.memberid= t1.memberid'.format(
                    yesterday_utc_starttime_str, yesterday_utc_endtime_str, rankminibet, rankminiwin, tempgameid,dbtype)

                if command_topmultipilier != '':
                    command_topmultipilier += ' union all '
                command_topmultipilier += 'select t1.gameid,t1.memberid,t1.summultipilier div 1 as amount,card,nickname,level,avatar from member, (select gameid,memberid,sum(total_win/total_bet) as summultipilier ' \
                                          'from {5} where bettime between "{0}" and "{1}" and total_bet >= "{2}" and (total_win/total_bet) >= "{3}" ' \
                                          ' and gameid = "{4}" group by memberid) as t1 where member.memberid=t1.memberid'.format(
                    yesterday_utc_starttime_str, yesterday_utc_endtime_str, rankminibet, rankminimultipilier, tempgameid,dbtype)

            if command_topwin == '' or command_topmultipilier == '':
                raise Exception('command error')

            totaltopwinlist = []
            totaltopmultiplierlist = []


            # 龍綁
            datalen, data = await self.getdbdata('get dragon rank', command_topwin, True)
            if datalen > 0:
                # 整理 data
                for itemgameid in gameidlist:
                    templist = [item for item in data if item.get('gameid') == itemgameid]
                    templist = sorted(templist, key=lambda k: (k['amount']), reverse=True)  # sort rank
                    topwinrankprizelist = gamerankprize.get(itemgameid).get('topwin')
                    tmpranktype = gameranktype.get(itemgameid)
                    for index in range(len(templist)):
                        templist[index].update({"rank": index + 1})
                        if index < len(topwinrankprizelist):
                            templist[index].update({"extraaward": topwinrankprizelist[index]})
                        else:
                            templist[index].update({"extraaward": 0})
                        dbjinsonggamerankdaysettledata.append([
                            twyesterdaydate,
                            1,  # type top win
                            templist[index].get('gameid'),
                            templist[index].get('memberid'),
                            templist[index].get('amount'),
                            templist[index].get('extraaward'),
                            templist[index].get('rank'),
                            tmpranktype

                        ])
                        if templist[index].get('rank') == 1:
                            totaltopwinlist.append((templist[index].get('memberid'),1,0))
                    topwinrankdict.update({itemgameid: templist})

            # 虎綁
            datalen, data = await self.getdbdata('get tiger rank', command_topmultipilier, True)
            if datalen > 0:
                # 整理 data
                for itemgameid in gameidlist:
                    templist = [item for item in data if item.get('gameid') == itemgameid]
                    templist = sorted(templist, key=lambda k: (k['amount']), reverse=True)
                    topmultipilierprizelist = gamerankprize.get(itemgameid).get('topmultipilier')
                    tmpranktype = gameranktype.get(itemgameid)
                    for index in range(len(templist)):
                        templist[index].update({"rank": index + 1})
                        if index < len(topmultipilierprizelist):
                            templist[index].update({"extraaward": topmultipilierprizelist[index]})
                        else:
                            templist[index].update({"extraaward": 0})

                        dbjinsonggamerankdaysettledata.append([
                            twyesterdaydate,
                            0,  # type top multipilier
                            templist[index].get('gameid'),
                            templist[index].get('memberid'),
                            templist[index].get('amount'),
                            templist[index].get('extraaward'),
                            templist[index].get('rank'),
                            tmpranktype
                        ])
                        if templist[index].get('rank') == 1:
                            totaltopmultiplierlist.append((templist[index].get('memberid'),0,1))
                    topmultipilierrankdict.update({itemgameid: templist})



            # write to db
            command = 'insert into jinsonggamerankdaysettle (rankdate,type,gameid,memberid,amount,extraaward,rank,ranktype) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            insertresult,affectrows = await self.insertdbdata('insert into jinsonggamerankdaysettle',command,many=True,manydata=dbjinsonggamerankdaysettledata)

            # set setting 信件 標題與內文
            command = 'select rankdaymultipilierinboxcontent,rankdaywininboxcontent,rankdaymultipilierinboxtitle,rankdaywininboxtitle from setting'
            datalen, data = await self.getdbdata('get setting data',command)

            if datalen <1:
                raise Exception('get setting data error')

            rankdaymultipilierinboxcontent = data.get('rankdaymultipilierinboxcontent')
            rankdaywininboxcontent = data.get('rankdaywininboxcontent')
            rankdaymultipilierinboxtitle = data.get('rankdaymultipilierinboxtitle')
            rankdaywininboxtitle = data.get('rankdaywininboxtitle')


            inboxmaildatalist = []
            inboxdateline = twtodaydate + timedelta(days=5)
            inboxdatelinestr = inboxdateline.strftime('%Y-%m-%d 15:59:59')
            notificationuserlist = []       # fcm notification list

            # 龍榜獎勵信件
            for tempgameid in topwinrankdict.keys():
                tempranklist = topwinrankdict.get(tempgameid)
                tempgamename = gamenamedict.get(tempgameid)
                tmpranktype = gameranktype.get(tempgameid)
                for temprankdata in tempranklist:
                    tempmemberid = temprankdata.get('memberid')
                    temprank = temprankdata.get('rank')
                    extraaward = temprankdata.get("extraaward")
                    if extraaward <=0:
                        continue
                    if tmpranktype ==0:
                        promotionid = 30
                    else:
                        promotionid = 67
                    inboxmaildatalist.append([
                        tempmemberid,       # memberid
                        0,                  # mailtype
                        rankdaywininboxtitle,   # inboxtitle
                        rankdaywininboxcontent.format(temprank,tempgamename,twyesterdaydate.__str__()),     # inboxcontent
                        inboxdatelinestr,       #dateline
                        promotionid,                     # promotionid
                        extraaward              # credit_award
                    ])
                    if str(tempmemberid) not in notificationuserlist:       # 加入推播 list
                        notificationuserlist.append(str(tempmemberid))
            # 虎榜獎勵信件
            for tempgameid in topmultipilierrankdict.keys():
                tempranklist = topmultipilierrankdict.get(tempgameid)
                tempgamename = gamenamedict.get(tempgameid)
                tmpranktype = gameranktype.get(tempgameid)
                for temprankdata in tempranklist:
                    tempmemberid = temprankdata.get('memberid')
                    temprank = temprankdata.get('rank')
                    extraaward = temprankdata.get('extraaward')
                    if extraaward <= 0:
                        continue
                    if tmpranktype ==0:
                        promotionid = 30
                    else:
                        promotionid = 67

                    inboxmaildatalist.append([
                        tempmemberid,       # memberid
                        1,                  # mailtype
                        rankdaymultipilierinboxtitle,   # inboxtitle
                        rankdaymultipilierinboxcontent.format(temprank,tempgamename,twyesterdaydate.__str__()),     #inboxcontent
                        inboxdatelinestr,       # dateline
                        promotionid,                     # promotionid
                        extraaward              # credit_award
                    ])
                    if str(tempmemberid) not in notificationuserlist:       # 加入推播 list
                        notificationuserlist.append(str(tempmemberid))

            if len(inboxmaildatalist)>0:
                command = 'insert into memberinbox (memberid,mailtype,inboxtitle,inboxcontent,dateline,promotionid,credit_award) ' \
                          'values(%s,%s,%s,%s,%s,%s,%s)'
                insertresult, affectrows = await self.insertdbdata('insert into mailbox',command,many=True,manydata=inboxmaildatalist)

            # 發送推播 通知龍虎榜獎金
            if notificationuserlist != []:
                asyncio.ensure_future(self.senddailyrankrewardnotification(notificationuserlist))

            # make member's totaltopwin & totaltopmultiplier record
            updaterecordstrlist = []
            for tempitem in totaltopwinlist:
                updaterecordstrlist.append('({0},{1},0)'.format(tempitem[0],tempitem[1]))
            for tempitem in totaltopmultiplierlist:
                updaterecordstrlist.append('({0},0,{1})'.format(tempitem[0],tempitem[2]))

            if len(updaterecordstrlist) > 0:
                updaterecordstr = ','.join(updaterecordstrlist)

                command = 'insert into member (memberid,totaltopwin,totaltopmultiplier) values {0}' \
                          ' on duplicate key update totaltopwin = totaltopwin + values(totaltopwin), ' \
                          ' totaltopmultiplier = totaltopmultiplier + values(totaltopmultiplier) '.format(updaterecordstr)
                updateresult = await self.updatedbdata('update member totaltopwin',command)



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makejinsonggamedayranksettle except:{}'.format(e))

    async def makejinsonggameweekranksettle(self,redis_obj,app): # 新版周冠結算
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makejinsonggameweekranksettle start')
            result = False

            # get setting2.rankmode
            command = 'select rankmode from setting2'
            datalen,data = await self.getdbdata('get rankmode from setting2',command)
            if datalen != 1:
                raise Exception('get rankmode error')

            if data.get('rankmode') ==1:
                return      # old mode return


            localdate = pg_general.get_local_date()
            enddate = localdate - timedelta(days=1)
            startdate = localdate - timedelta(days=7)

            command = 'select type,jinsonggamerankdaysettle.gameid,memberid,sum(amount) div 1 as amount,gamename,game.rankweekprize,game.ranktype from jinsonggamerankdaysettle,game where rankdate>="2020-08-01" and game.gameid = jinsonggamerankdaysettle.gameid and rankdate between "{0}" and "{1}"  group by type,gameid,memberid'.format(startdate.__str__(),enddate.__str__())
            datalen, data = await self.getdbdata('get week rank from jinsonggamerankdaysettlt',command,True)
            if datalen <1:
                return result

            weektopwinlist = []
            weektopwindict = {}
            weektopmultipilierlist = []
            weektopmultipilierdict = {}

            for item in data:
                gameid = item.get('gameid')
                type = item.get('type')
                memberid = item.get('memberid')
                amount = item.get('amount')
                gamename = item.get('gamename')
                rankweekprize = json.loads(item.get('rankweekprize'))
                ranktype = item.get('ranktype')
                if type == 0:   # multipilier
                    if weektopmultipilierdict.get(gameid) is None:
                        weektopmultipilierdict[gameid] = {"gamename": gamename,"rank":[],"rankweekprize":rankweekprize.get('topmultipilier'),"ranktype":ranktype}
                    weektopmultipilierdict[gameid]['rank'].append({
                        "memberid": memberid,
                        "amount": amount
                    })
                elif type ==1:  # win
                    if weektopwindict.get(gameid) is None:
                        weektopwindict[gameid] = {"gamename":gamename,"rank":[],"rankweekprize": rankweekprize.get('topwin'),"ranktype": ranktype}
                    weektopwindict[gameid]['rank'].append({
                        "memberid":memberid,
                        "amount": amount
                    })

            # 周龍榜
            for tempgameid,tempvalue in weektopwindict.items():
                if tempvalue is None:
                    continue

                gamename = tempvalue.get('gamename')
                rankweekprize = tempvalue.get('rankweekprize')
                rank = tempvalue.get('rank')
                ranktype = tempvalue.get('ranktype')
                if None in [gamename,rankweekprize,rank,ranktype]:
                    continue
                if len(rank) <1:
                    continue

                # rank 排序
                rank = sorted(rank, key=lambda k: (k['amount']),reverse=True)
                rank = rank[:len(rankweekprize)]
                tempvalue['rank'] = rank
                for tempindex,item in enumerate(rank):
                    # 補上 rank
                    item.update({"rank":tempindex+1})
                    # 補上 rankweekprize
                    if len(rankweekprize)>tempindex:
                        item.update({"rankweekprize": rankweekprize[tempindex]})
                    else:
                        item.update({"rankweekprize": 0})

            # 周虎榜
            for tempgameid, tempvalue in weektopmultipilierdict.items():
                if tempvalue is None:
                    continue
                gamename = tempvalue.get('gamename')
                rankweekprize = tempvalue.get('rankweekprize')
                rank = tempvalue.get('rank')
                ranktype = tempvalue.get('ranktype')
                if None in [gamename,rankweekprize,rank,ranktype]:
                    continue
                if len(rank)<1:
                    continue

                # rank 排序
                rank = sorted(rank , key=lambda k:(k['amount']),reverse=True)
                rank = rank[:len(rankweekprize)]
                tempvalue['rank'] = rank
                for tempindex,item in enumerate(rank):
                    # 補上 rank
                    item.update({"rank":tempindex+1})
                    # 補上 rankweekprize
                    if len(rankweekprize)>tempindex:
                        item.update({"rankweekprize":rankweekprize[tempindex]})
                    else:
                        item.update({"rankweekprize":0})

            # 派發 inbox
            # 整理要派發的名單
            params = []
            notificationuserlist = []   # fcm notification memberid list
            dbweeksettle = []           # jinsonggamerankweeksettle list
            inboxdateline = (localdate + timedelta(days=5)).strftime('%Y-%m-%d 15:59:59')
            # get inbox title and content
            command = 'select rankweekwininboxtitle,rankweekmultipilierinboxtitle,rankweekwininboxcontent,rankweekmultipilierinboxcontent from setting'
            datalen, data = await self.getdbdata('get week rank prize inbox title and content',command)
            if datalen !=1:
                raise Exception('get inbox title and content error')

            rankweekwininboxtitle = data.get('rankweekwininboxtitle')
            rankweekmultipilierinboxtitle = data.get('rankweekmultipilierinboxtitle')
            rankweekwininboxcontent = data.get('rankweekwininboxcontent')
            rankweekmultipilierinboxcontent = data.get('rankweekmultipilierinboxcontent')

            if None in [rankweekwininboxtitle,rankweekmultipilierinboxtitle,rankweekwininboxcontent,rankweekmultipilierinboxcontent]:
                raise Exception('get inbox title content error 2')

            # 虎綁
            for tempgameid , tempvalue in weektopmultipilierdict.items():
                gamename = tempvalue.get('gamename')
                rank = tempvalue.get('rank')
                ranktype = tempvalue.get('ranktype')
                if None in [gamename,rank]:
                    continue
                if len(rank) < 1:
                    continue
                for tempitem in rank:
                    rankindex = tempitem.get('rank')
                    rankweekprize = tempitem.get('rankweekprize')
                    amount = tempitem.get('amount')
                    if rankweekprize <=0:
                        continue

                    if ranktype ==0:
                        promotionid = 30
                    else:
                        promotionid = 67
                    memberid = tempitem.get('memberid')
                    params.append([
                        memberid,
                        1,          # mailtype
                        rankweekmultipilierinboxtitle, # inbox title
                        rankweekmultipilierinboxcontent.format(rankindex,gamename,'{}~{}'.format(startdate.__str__(),enddate.__str__())),
                        inboxdateline,
                        promotionid,
                        rankweekprize
                    ])
                    if str(memberid) not in notificationuserlist:
                        notificationuserlist.append(str(memberid))

                    dbweeksettle.append([
                        startdate.__str__(),
                        enddate.__str__(),
                        0,                          # type
                        tempgameid,                 # gameid
                        memberid,                   #memberid
                        amount,
                        rankweekprize,              # extraaward
                        rankindex,
                        ranktype
                    ])


            # 龍綁
            for tempgameid , tempvalue in weektopwindict.items():
                gamename = tempvalue.get('gamename')
                rank = tempvalue.get('rank')
                ranktype = tempvalue.get('ranktype')
                if None in [gamename,rank]:
                    continue
                if len(rank) < 1:
                    continue
                for tempitem in rank:
                    rankindex = tempitem.get('rank')
                    rankweekprize = tempitem.get('rankweekprize')
                    amount = tempitem.get('amount')
                    if rankweekprize <=0:
                        continue
                    memberid = tempitem.get('memberid')

                    if ranktype == 0:
                        promotionid = 30
                    else:
                        promotionid = 67
                    params.append([
                        memberid,
                        0,          # mailtype
                        rankweekwininboxtitle, # inbox title
                        rankweekwininboxcontent.format(rankindex,gamename,'{}~{}'.format(startdate.__str__(),enddate.__str__())),
                        inboxdateline,
                        promotionid,
                        rankweekprize
                    ])
                    if str(memberid) not in notificationuserlist:
                        notificationuserlist.append(str(memberid))
                    dbweeksettle.append([
                        startdate.__str__(),
                        enddate.__str__(),
                        1,  # type
                        tempgameid,  # gameid
                        memberid,  # memberid
                        amount,
                        rankweekprize,  # extraaward
                        rankindex,
                        ranktype
                    ])
            # insert into db
            command = 'insert into memberinbox (memberid,mailtype,inboxtitle,inboxcontent,dateline,promotionid,credit_award) values ' \
                      '(%s,%s,%s,%s,%s,%s,%s)'
            insertresult,affectrows = await self.insertdbdata('insert into inbox',command,many=True,manydata=params)

            # 發送推播 通知龍虎榜獎金
            if notificationuserlist != []:
                asyncio.ensure_future(self.sendweeklyrankrewardnotification(notificationuserlist))

            # insert into db.jinsonggamerankweeksettle
            command = 'insert into jinsonggamerankweeksettle(rankdatestart,rankdateend,type,gameid,memberid,amount,extraaward,rank,ranktype) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            insertresult,affectrows = await self.insertdbdata('insert into jinsonggamerankweeksettle',command,many=True,manydata=dbweeksettle)



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makejinsonggameweekranksettle except:{}'.format(e))

        return result

    async def makejinsongmonthprizesettle(self,redis_obj,app,daynumber,date=None): # 金爽榜結算
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makejinsongmonthprizesettle start')
            result = False

            # get rankmode from setting2
            command = 'select rankmode from setting2'
            datalen,data = await self.getdbdata('get rankmode from setting2',command)
            if datalen !=1:
                raise Exception('get rankmode error')

            if data.get('rankmode') == 1:
                return          # old mode

            # get rankmonthjinsongprizeinboxtitle, rankmonthjinsongprizeinboxcontent from setting
            command = 'select rankmonthjinsongprizeinboxtitle,rankmonthjinsongprizeinboxcontent from setting'
            datalen, data = await self.getdbdata('get jinsongprize inbox',command)
            if datalen !=1:
                raise Exception("get inbox title and content error")
            rankmonthjinsongprizeinboxtitle = data.get('rankmonthjinsongprizeinboxtitle')
            rankmonthjinsongprizeinboxcontent = data.get('rankmonthjinsongprizeinboxcontent')


            # get jinsongprizesetting
            command = 'select * from jinsongprizesetting order by poolindex'
            datalen, data = await self.getdbdata('get jinsongprizesetting',command,True)
            if datalen <1:
                raise Exception('get jinsongprizesetting error')

            jinsongprizesettinglist = data.copy()



            todaylocaldate = pg_general.get_local_date()
            if date is not None:
                todaylocaldate = date
            yesterdaydate = todaylocaldate - timedelta(days=1)
            lastmonthstartdate = datetime(yesterdaydate.year,yesterdaydate.month,16).date()
            thismonthstartdate = datetime(todaylocaldate.year,todaylocaldate.month,1).date()

            if daynumber ==1:
                startdate = lastmonthstartdate
                enddate = yesterdaydate
            elif daynumber == 16:
                startdate = thismonthstartdate
                enddate = yesterdaydate

            # prepare inbox dateline
            inboxdateline = pg_general.get_local_date() + timedelta(days=5)
            inboxdatelinestr = '{}-{}-{} 15:59:59'.format(inboxdateline.year,inboxdateline.month,inboxdateline.day)


            # get member rank
            command = 'select memberid,sum(win) div 1 as win from betsum where sumdate between "{0}" and "{1}" group by memberid having win >0'.format(startdate.__str__(),enddate.__str__())
            datalen, data = await self.getdbdata('get monthly rank from betsum',command,True)

            if datalen <1:
                raise Exception('get monthly betsum error')

            monthlyranklist = data.copy()
            monthlyranklist = sorted(monthlyranklist, key=lambda k: (k['win']),reverse=True)
            notificationuserlist = []  # fcmtoken list

            # get total monthly bet
            command = 'select sum(bet) div 1 as totalbet from betsum where sumdate between "{0}" and "{1}"'.format(startdate.__str__(),enddate.__str__())
            datalen,data = await self.getdbdata('get monthly total bet ',command)

            if datalen !=1 :
                raise Exception('get monthyly total bet error')

            monthlytotalbet = data.get('totalbet')
            if monthlytotalbet <=0:
                raise Exception('monthly totalbet data is error')

            # dbmonthdatalist for jinsonggamerankmonthsettle
            dbmonthdatalist = []
            inboxdatalist = []

            for index,item in enumerate(monthlyranklist):
                if index >= len(jinsongprizesettinglist):
                    item.update({'reward': 0})
                    getreward = 0
                else:
                    initial = jinsongprizesettinglist[index].get('initial')
                    percent = jinsongprizesettinglist[index].get('percent')
                    cap = jinsongprizesettinglist[index].get('cap')
                    reward = monthlytotalbet*percent
                    getreward = 0
                    if (reward+initial) >= cap:
                        getreward = cap
                    else:
                        getreward = reward + initial

                    item.update({'reward': pg_general.converttype(getreward,int)})
                item.update({'rank':index+1})
                memberid = item.get('memberid')
                if str(memberid) not in notificationuserlist:
                    notificationuserlist.append(str(memberid))

                if item.get('reward')>0:
                    dbmonthdatalist.append([
                        startdate.__str__(),
                        enddate.__str__(),
                        memberid,
                        item.get('win'),
                        item.get('reward'),
                        item.get('rank')
                    ])
                    inboxdatalist.append([
                        memberid,
                        6,                                          # mail type
                        rankmonthjinsongprizeinboxtitle,            # inbox title
                        rankmonthjinsongprizeinboxcontent.format(item.get('rank'),startdate.__str__(),enddate.__str__()),
                        inboxdatelinestr,                           #dateline
                        30,                                         # promotionid
                        item.get('reward')                          #credit_award

                    ])

            if notificationuserlist != []:
                # 發送推播 通知龍虎榜獎金
                asyncio.ensure_future(self.sendmonthlyjinsongrewardnotification(notificationuserlist))

            if len(dbmonthdatalist)>0:
                command = 'insert into jinsonggamerankmonthsettle(rankdatestart,rankdateend,memberid,amount,extraaward,rank)values(%s,%s,%s,%s,%s,%s)'
                insertresult,affectrows = await self.insertdbdata('insert into jinsonggamerankmonthsettlt',command,many=True,manydata=dbmonthdatalist)

            if len(inboxdatalist)> 0:
                command = 'insert into memberinbox(memberid,mailtype,inboxtitle,inboxcontent,dateline,promotionid,credit_award)values(%s,%s,%s,%s,%s,%s,%s)'
                insertresult, affectrows = await self.insertdbdata('insert into memberinbox', command,
                                                                   many=True, manydata=inboxdatalist)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makejinsongmonthprizesettle except:{}'.format(e))
        return result


    async def broadcast_jinsongprize(self,redis_obj,app):      # 廣播 金爽綁 pool
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:broadcast_jinsongprize start')
            twdatetimestr = pg_general.get_tw_date_str()
            twdatetimemonthstr = pg_general.get_tw_date_month_str()

            twdate = pg_general.get_tw_datetime().date()

            # get this month totalbet
            if twdate.day >= 1 and twdate.day <= 15:
                totalbetmonthamount = await redis_obj.get_value('totalmonthbet_' + twdatetimemonthstr)
            else:
                totalbetmonthamount = await redis_obj.get_value('totalmonthbet2_' + twdatetimemonthstr)

            if totalbetmonthamount is None:
                totalbetmonthamount = 0
            totalbetmonthamount = pg_general.converttype(totalbetmonthamount,int)

            # get db jinsongprizesetting
            command = 'select * from jinsongprizesetting order by poolindex'
            datalen,data = await self.getdbdata('get all jinsongprizesetting',command,True)
            if datalen <1:
                raise Exception('get jinsongprizesetting error')

            jinsongprizesetting = []
            totaljinsongprize = 0
            for item in data:
                rewardtmp = pg_general.converttype(totalbetmonthamount*item.get('percent'),int)
                cap = item.get('cap')
                initial = item.get('initial')
                percent = item.get('percent')
                poolindex = item.get('poolindex')
                if (rewardtmp+initial) >= cap:
                    rewardtmp = cap
                else:
                    rewardtmp = initial + rewardtmp
                jinsongprizesetting.append({
                    "poolindex": poolindex,
                    "percent": percent,
                    "cap": cap,
                    "initial": initial,
                    "reward": rewardtmp
                })
                totaljinsongprize += rewardtmp


            await redis_obj.set_json_value('jinsongprizesetting',{"totaljinsongprize":totaljinsongprize,"jinsongprizesetting":jinsongprizesetting})

            sendmsg = {"type": 0, "msg": {"commandid": 3000023, "data": {"jinsongprize":totaljinsongprize}}}
            # get lobby server ips
            if env_setting.LOCAL_SERVER == False:
                command = 'select ip from lobbyserversetting'
                datalen, data = await self.getdbdata('get all lobby server ips', command, True)
                if datalen > 0:
                    try:
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            'send_to_all_lobbyserver , sendmsg:{0}'.format(sendmsg))
                        lobbyserverips = data
                        if lobbyserverips != []:
                            for item in lobbyserverips:
                                realurl = 'http://{0}/broadcasttoall'.format(item.get('ip'))
                                async with aiohttp.ClientSession() as session:
                                    response = await session.get(realurl, json=sendmsg)
                                    if response.status == 200:
                                        data = await response.text()
                                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                            'send_to_all_lobbyserver_future response:{0}'.format(data))
                                await asyncio.sleep(0)

                    except Exception as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,
                                            'send_to_all_lobbyserver , except:{0}'.format(e))
                    finally:
                        pg_general.writelog(pg_general.PG_LogerLevel.info,
                                            'send_to_all_lobbyserver , done')


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:broadcast_jinsongprize except:{0}'.format(e))



    async def clearseats_job(self,redis_obj,app):
        try:
            clearseatflag = app['clearseatflag']
            if clearseatflag != 1:
                return
            keepseatsecondslist = app['keepseatsecondslist']

            dirtyseatlist = await redis_obj.hkeys('dirtyseat')
            if dirtyseatlist is not None:
                for item in dirtyseatlist:
                    try:
                        valuelist = item.split('_')
                        tempgametype = valuelist[0]
                        if tempgametype == 'g':
                            tempgametype = 'goldseats'
                            tempgametype2 = 'seatsgold'
                            tempseatid = 'gseat'
                        elif tempgametype == 's':
                            tempgametype = 'silverseats'
                            tempgametype2 = 'seatssilver'
                            tempseatid = 'sseat'
                        elif tempgametype == 't':
                            tempgametype = 'tutorialseats'
                            tempgametype2 = 'seatstutorial'
                            tempseatid = 'tseat'
                        tempgameid = valuelist[1]
                        tempseatnum = valuelist[2]
                        seatkey = tempgametype + '_' + tempgameid + '@' + tempseatnum
                        valuelist2 = await redis_obj.hmget(seatkey,['memberid','status','dateline','card'])
                        tempmemberid = pg_general.converttype(valuelist2[0],int)
                        tempstatus = pg_general.converttype(valuelist2[1],int)
                        tempdateline = pg_general.strtodatetime(valuelist2[2])
                        tempcard = pg_general.converttype(valuelist2[3],int)
                        tempkeepseconds = keepseatsecondslist[tempcard].get('keepseatseconds')
                        tempnowutcdatetime = pg_general.getutcnow_datetime()
                        tempuserseatkey = '{}_{}@{}_{}'.format(tempgametype2,tempgameid,tempseatnum,tempmemberid)
                        valuelist3 = await redis_obj.get_all_keys(tempuserseatkey)
                        if (valuelist3 is None or valuelist3 == []) and tempstatus== 1:      # 原本狀態 : playing , 已經沒使用此機台, 判斷是否要 保留 或是回收
                            if tempkeepseconds > 0 and tempseatid != 'tseat':         # 要保留, turtorial 強制不保留
                                newdateline_str = pg_general.datetime_to_str(tempnowutcdatetime + timedelta(seconds=tempkeepseconds))
                                await redis_obj.hmset(seatkey,{"dateline": newdateline_str,"status": 2 })
                                await redis_obj.set_value(tempuserseatkey,2,tempkeepseconds)
                            else:           # 不保留 確認是否有 未完成的遊戲
                                seatid = '{}_{}_{}'.format(tempseatid,tempgameid,tempseatnum)
                                uncompletedresult, uncomplietedclientdata = await self.getuncompletedgame(seatid,tempseatid)
                                if uncompletedresult == True and uncomplietedclientdata.get('result') == True: # 有未完成的遊戲 設定 status = 3 , dateline + 30 天
                                    newdateline_str = pg_general.datetime_to_str(tempnowutcdatetime+timedelta(days=30))
                                    await redis_obj.hmset(seatkey, {"dateline": newdateline_str, "status": 3})
                                    # set uncompletegame
                                    await redis_obj.hset('uncompletedgame',seatkey,1)
                                    await redis_obj.set_value(tempuserseatkey, 3, 2592000) # 位完成遊戲 保留 30 天
                                else:   # 沒有未完成遊戲 回收此機台
                                    # 清除 dirtyseat
                                    await redis_obj.hdel('dirtyseat',item)
                                    # 設定為空機台
                                    if tempgametype == 'goldseats':
                                        await redis_obj.hset('gemptyseats_{}'.format(tempgameid),str(tempseatnum),1)
                                    elif tempgametype == 'silverseats':
                                        await redis_obj.hset('semptyseats_{}'.format(tempgameid),str(tempseatnum),1)
                                    elif tempgametype == 'tutorialseats':
                                        await redis_obj.hset('temptyseats_{}'.format(tempgameid),str(tempseatnum),1)
                                    # 刪除未完成遊戲紀錄
                                    await redis_obj.hdel('uncompletedgame',seatkey)
                                    # 設定座位狀態為 空台 : status = 0
                                    await redis_obj.hmset(seatkey, {'status': 0})

                        elif (valuelist3 is None or valuelist3 == []) and tempstatus== 2:       # 原本保留中 判斷 是否過保留時間 要取消保留
                            if tempnowutcdatetime > tempdateline:       # 時間 超過要回復 狀態 , 先 抓 是否有未完成遊戲
                                seatid = '{}_{}_{}'.format(tempseatid, tempgameid, tempseatnum)
                                uncompletedresult, uncomplietedclientdata = await self.getuncompletedgame(seatid,tempseatid)
                                if uncompletedresult == True and uncomplietedclientdata.get('result') == True:  # 有未完成的遊戲 設定 status = 3 , dateline + 30 天
                                    newdateline_str = pg_general.datetime_to_str(tempnowutcdatetime + timedelta(days=30))
                                    await redis_obj.hmset(seatkey, {"dateline": newdateline_str, "status": 3})
                                    # set uncompletegame
                                    await redis_obj.hset('uncompletedgame', seatkey, 1)
                                    await redis_obj.set_value(tempuserseatkey, 3, 2592000)  # 位完成遊戲 保留 30 天
                                elif uncompletedresult == True and uncomplietedclientdata.get('result') == False: # 沒有未完成的遊戲 改為 空機台狀態
                                    await redis_obj.hmset(seatkey,{"status":0})
                                    await redis_obj.hdel('uncompletedgame',seatkey)
                                    if tempgametype =='goldseats':
                                        await redis_obj.hset('gemptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                                    elif tempgametype == 'silverseats':
                                        await redis_obj.hset('semptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                                    elif tempgametype == 'tutorialseats':
                                        await redis_obj.hset('temptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                                    await redis_obj.hdel('dirtyseat', item)
                        elif (valuelist3 is None or valuelist3 == []) and tempstatus ==3:       # 原本 有未完成遊戲 確定時間 結束 call delete game
                            if tempnowutcdatetime > tempdateline:
                                result , clientdata = await self.force_delete_game(seatkey,tempgameid,tempseatnum)
                                # 清除 dirtyseat
                                await redis_obj.hdel('dirtyseat', item)
                                # 設定為空機台
                                if tempgametype == 'goldseats':
                                    await redis_obj.hset('gemptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                                elif tempgametype == 'silverseats':
                                    await redis_obj.hset('semptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                                elif tempgametype == 'tutorialseats':
                                    await redis_obj.hset('temptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                                # 刪除未完成遊戲紀錄
                                await redis_obj.hdel('uncompletedgame', seatkey)
                                # 設定座位狀態為 空台 : status = 0
                                await redis_obj.hmset(seatkey, {'status': 0})
                        elif tempseatid == 'tseat' and tempstatus ==3:     # 遇到教學模式未完成遊戲直接刪除 並且RNG結算
                                result, clientdata = await self.force_delete_game(seatkey, tempgameid, tempseatnum)
                                # 清除 dirtyseat
                                await redis_obj.hdel('dirtyseat', item)
                                # 設定為空機台

                                await redis_obj.hset('temptyseats_{}'.format(tempgameid), str(tempseatnum), 1)
                                # 刪除未完成遊戲紀錄
                                await redis_obj.hdel('uncompletedgame', seatkey)
                                # 設定座位狀態為 空台 : status = 0
                                await redis_obj.hmset(seatkey, {'status': 0})

                                # 直接算分給他
                                # get setting2 data
                                command = 'select delnewbiegamereturncreditsetting from setting2'
                                datalen , data = await self.getdbdata('get delnewbiegamereturncreditsetting from setting2',command)
                                if datalen > 0:
                                    delgameconfig = json.loads(data.get('delnewbiegamereturncreditsetting'))
                                    multiple = delgameconfig.get('multiple')
                                    winlist = delgameconfig.get('data')['winlist']
                                    weightlist = delgameconfig.get('data')['weightlist']
                                    totalweight = sum(weightlist)
                                    rngdata = random.randint(1,totalweight)
                                    getwinamount = 0
                                    for idx,tmpitem in enumerate(weightlist):
                                        if tmpitem>= rngdata:
                                            getwinamount = winlist[idx] * multiple
                                            break
                                        else:
                                            rngdata -= tmpitem
                                    if getwinamount ==0:
                                        raise Exception('get random winamount error')

                                    # update member silvercredit
                                    command = 'update member set silvercredit = silvercredit +"{0}" where memberid="{1}"'.format(getwinamount,tempmemberid)
                                    updateresult = await self.updatedbdata('update tutorial win amount',command)

                                    # update member transaction
                                    param = {
                                        "frommemberid": tempmemberid,
                                        "tomemberid": tempmemberid,
                                        "type": pg_general.transactiontype.tutorialwin,
                                        "amount": 0,
                                        "amount_silver": getwinamount,
                                        "otherdata": 'tutorialwin'
                                    }
                                    asyncio.ensure_future(self.writetransactionlog('over time return gift', param))



                        await asyncio.sleep(0)
                    except Exception as e:
                        pg_general.writelog(pg_general.PG_LogerLevel.error,'pg_asqldb:clearseats_job 1 except:{0}'.format(e))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:clearseats_job except:{0}'.format(e))
        pass



    async def allmallhistory(self):
        try:
            result = False
            resultdata = ''

            command = 'select mallhistoryindex,shopid,buytime,cost,transactionid,malltype,memberid from mallhistory order by buytime desc limit 5'
            datalen, data = await self.getdbdata('get allmallhistory',command,True)

            if datalen >0:
                result = True
                resultdata = 'mallhistoy\n'
                for item in data:
                    mallhistoryindex = item.get('mallhistoryindex')
                    shopid = item.get('shopid')
                    buytime = item.get('buytime')
                    cost = item.get('cost')
                    transactionid = item.get('transactionid')
                    malltype = item.get('malltype')
                    memberid = item.get('memberid')
                    resultdata = resultdata + 'index:{0},shopid:{1},buytime:{2},cost:{3},transactionid:{4},malltype:{5},memberid:{6}\n'.format(mallhistoryindex,shopid,buytime,cost,transactionid,malltype,memberid)

            command = 'select transid,type, memberid,amount,starttime,status,pay_rcode,pay_status from gashwalletdeposite order by transid desc limit 5'
            datalen , data = await self.getdbdata('get gashwalletdeposite',command,True)
            if datalen > 0:
                result = True
                resultdata += 'gashwalletdeposite\n'
                for item in data:
                    transid = item.get('transid')
                    type = item.get('type')
                    memberid = item.get('memberid')
                    amount = item.get('amount')
                    starttime = item.get('starttime')
                    status = item.get('status')
                    pay_rcode = item.get('pay_rcode')
                    pay_status = item.get('pay_status')
                    resultdata = resultdata + 'transid:{0},type:{1},memberid:{2},amount:{3},starttime:{4},status:{5},pay_rcode:{6},pay_status:{7}\n'.format(transid,type,memberid,amount,starttime,status,pay_rcode,pay_status)
            command = 'select transid,memberid,status,starttime,Amount from creditcarddeposite order by transid desc limit 5'
            datalen , data = await self.getdbdata('get creditcarddeposite', command , True)
            if datalen > 0:
                result = True
                resultdata += 'creditcarddeposite\n'
                for item in data:
                    transid = item.get('transid')
                    memberid = item.get('memberid')
                    status = item.get('status')
                    starttime = item.get('starttime')
                    Amount = item.get('Amount')
                    resultdata = resultdata + 'transid:{0},memberid:{1},status:{2},starttime:{3},Amount:{4}\n'.format(transid,memberid,status,starttime,Amount)



        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:allmallhistory except:{0}'.format(e))

        return result,resultdata


    async def createseats(self,redis_obj):
        try:
            result = pg_general.Apiresult.connectdberror
            resultdata = {}

            # 先抓 game 座位數量
            command = 'select gameid,seatsamount,seatsamount_s,seatsamount_t from game'
            datalen, data = await self.getdbdata('createseats',command,True)
            gameseatslist = []
            if datalen >0:
                for item in data:
                    gameid = item.get('gameid')
                    seatsamount = item.get('seatsamount')
                    seatsamount_s = item.get('seatsamount_s')
                    seatsamount_t = item.get('seatsamount_t')
                    gemptyseatsdict = {}
                    semptyseatsdict = {}
                    for i in range(seatsamount):
                        seatkey = 'goldseats_{}@{}'.format(gameid,str(i+1))
                        tempseatsfields = await redis_obj.hkeys(seatkey)
                        addstr = {}
                        if 'gameid' not in tempseatsfields:
                            addstr['gameid'] = gameid
                        if 'unopenturn' not in tempseatsfields:
                            addstr['unopenturn'] = 0
                        if 'avgturn' not in tempseatsfields:
                            addstr['avgturn'] = 0
                        if 'his1turn' not in tempseatsfields:
                            addstr['his1turn'] = 0
                        if 'his2turn' not in tempseatsfields:
                            addstr['his2turn'] = 0
                        if 'his3turn' not in tempseatsfields:
                            addstr['his3turn'] = 0
                        if 'his1multi' not in tempseatsfields:
                            addstr['his1multi'] = 0
                        if 'his2multi' not in tempseatsfields:
                            addstr['his2multi'] = 0
                        if 'his3multi' not in tempseatsfields:
                            addstr['his3multi'] = 0
                        if 'memberid' not in tempseatsfields:
                            addstr['memberid'] = 0
                        if 'status' not in tempseatsfields:
                            addstr['status'] = 0
                        if 'avatar' not in tempseatsfields:
                            addstr['avatar'] = ''
                        if 'card' not in tempseatsfields:
                            addstr['card'] = 0
                        if 'dateline' not in tempseatsfields:
                            addstr['dateline'] = '2020-05-01 00:00:00'
                        if addstr != {}:
                            await redis_obj.hmset(seatkey,addstr)
                        gemptyseatsdict[str(i+1)] = 1
                    # set gemptyseats_gameid
                    await redis_obj.hmset('gemptyseats_{}'.format(gameid),gemptyseatsdict)

                    for i in range(seatsamount_s):
                        seatkey = 'silverseats_{}@{}'.format(gameid, str(i + 1))
                        tempseatsfields = await redis_obj.hkeys(seatkey)
                        addstr = {}
                        if 'gameid' not in tempseatsfields:
                            addstr['gameid'] = gameid
                        if 'unopenturn' not in tempseatsfields:
                            addstr['unopenturn'] = 0
                        if 'avgturn' not in tempseatsfields:
                            addstr['avgturn'] = 0
                        if 'his1turn' not in tempseatsfields:
                            addstr['his1turn'] = 0
                        if 'his2turn' not in tempseatsfields:
                            addstr['his2turn'] = 0
                        if 'his3turn' not in tempseatsfields:
                            addstr['his3turn'] = 0
                        if 'his1multi' not in tempseatsfields:
                            addstr['his1multi'] = 0
                        if 'his2multi' not in tempseatsfields:
                            addstr['his2multi'] = 0
                        if 'his3multi' not in tempseatsfields:
                            addstr['his3multi'] = 0
                        if 'memberid' not in tempseatsfields:
                            addstr['memberid'] = 0
                        if 'status' not in tempseatsfields:
                            addstr['status'] = 0
                        if 'avatar' not in tempseatsfields:
                            addstr['avatar'] = ''
                        if 'card' not in tempseatsfields:
                            addstr['card'] = 0
                        if 'dateline' not in tempseatsfields:
                            addstr['dateline'] = '2020-05-01 00:00:00'
                        if addstr != {}:
                            await redis_obj.hmset(seatkey,addstr)
                        semptyseatsdict[str(i + 1)] = 1
                    # set semptyseats_gameid
                    await redis_obj.hmset('semptyseats_{}'.format(gameid), semptyseatsdict)

                    for i in range(seatsamount_t):
                        seatkey = 'tutorialseats_{}@{}'.format(gameid, str(i + 1))
                        tempseatsfields = await redis_obj.hkeys(seatkey)
                        addstr = {}
                        if 'gameid' not in tempseatsfields:
                            addstr['gameid'] = gameid
                        if 'unopenturn' not in tempseatsfields:
                            addstr['unopenturn'] = 0
                        if 'avgturn' not in tempseatsfields:
                            addstr['avgturn'] = 0
                        if 'his1turn' not in tempseatsfields:
                            addstr['his1turn'] = 0
                        if 'his2turn' not in tempseatsfields:
                            addstr['his2turn'] = 0
                        if 'his3turn' not in tempseatsfields:
                            addstr['his3turn'] = 0
                        if 'his1multi' not in tempseatsfields:
                            addstr['his1multi'] = 0
                        if 'his2multi' not in tempseatsfields:
                            addstr['his2multi'] = 0
                        if 'his3multi' not in tempseatsfields:
                            addstr['his3multi'] = 0
                        if 'memberid' not in tempseatsfields:
                            addstr['memberid'] = 0
                        if 'status' not in tempseatsfields:
                            addstr['status'] = 0
                        if 'avatar' not in tempseatsfields:
                            addstr['avatar'] = ''
                        if 'card' not in tempseatsfields:
                            addstr['card'] = 0
                        if 'dateline' not in tempseatsfields:
                            addstr['dateline'] = '2020-05-01 00:00:00'
                        if addstr != {}:
                            await redis_obj.hmset(seatkey,addstr)
                        semptyseatsdict[str(i + 1)] = 1
                    # set semptyseats_gameid
                    await redis_obj.hmset('temptyseats_{}'.format(gameid), semptyseatsdict)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:createseats except:{0}'.format(e))

        return result, resultdata



    async def noticeuserinboxdateline(self,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:noticeuserinboxdateline start')

            # find today utc date time
            nowdatestart_str , nowdateend_str = pg_general.get_date_to_utc_start_end_time(pg_general.getutcnow_datetime().date())

            command = 'select distinct memberinbox.memberid,member.fcmtoken from memberinbox,member where receivestate = 1 ' \
                      'and dateline = "{0}" and member.fcmtoken != "0" and member.memberid = memberinbox.memberid'.format(nowdateend_str)
            datalen, data = await self.getdbdata('get inbox dateline fcmtoken',command,True)

            if datalen > 0:
                fcmtokenlist = [item.get('fcmtoken') for item in data]
                if len(fcmtokenlist)> 0:
                    title = "您有即將到期的優惠信件"
                    msg = "👉🏻 快點擊領取優惠信件 👈🏻"
                    pg_fcm.send_notification_multiple_device(title, msg, fcmtokenlist)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:noticeuserinboxdateline except:{0}'.format(e))

    async def makeactivenumbersettle(self,redis_obj,app):
        try:
            # 抓最近七天日期範圍
            enddate_str = (pg_general.get_tw_datetime() - timedelta(days=1)).date().__str__()
            startdate_str = (pg_general.get_tw_datetime()-timedelta(days=7)).date().__str__()

            # get activenumber setting
            command = 'select activenumbersetting from setting'
            datalen, data = await self.getdbdata('get activenumbersetting',command)
            if datalen !=1:
                raise Exception('get activenumber setting error')
            activenumbersetting = data.get('activenumbersetting')
            if activenumbersetting is None:
                raise Exception('get activenumber setting error 2')
            activenumbersetting = json.loads(activenumbersetting)
            activenumbersetting = activenumbersetting.get('setting')
            if activenumbersetting is None:
                raise Exception('get activenumber setting error 3')

            cardsetting = activenumbersetting.get('card')
            betmaxsetting = activenumbersetting.get('betmax')
            betvaluesetting = activenumbersetting.get('betvalue')
            goldmaxsetting = activenumbersetting.get('goldmax')
            goldvaluesetting = activenumbersetting.get('goldvalue')

            if None in [cardsetting,betmaxsetting,betvaluesetting,goldmaxsetting,goldvaluesetting]:
                raise Exception('get activenumber setting error 4')

            command = 'select t1.*,t2.totalbet from (select member.memberid,(credit+safe) goldamount,card,activenumber from member ' \
                      ' where memberid >10 group by member.memberid) t1 left join (select memberid,sum(bet) as totalbet from betsum ' \
                      ' where sumdate between "{0}" and "{1}" group by memberid) t2 ' \
                      ' on t1.memberid = t2.memberid'.format(startdate_str,enddate_str)
            datalen, data = await self.getdbdata('get member detail',command,True)

            if datalen <= 0:
                raise('makeactivenumbersettle error')

            writelist = ''      # for update membrer activenumber
            for item in data:
                memberid = item.get('memberid')
                goldamount = item.get('goldamount')
                card = item.get('card')
                oldactivenumber = item.get('activenumber')
                totalbet = item.get('totalbet')

                if totalbet is None:        # 有可能為空
                    totalbet = 0
                activenumber = cardsetting[card]
                if goldamount >= goldmaxsetting:
                    activenumber += goldvaluesetting
                else:
                    activenumber += int((goldamount/goldmaxsetting)*goldvaluesetting)

                if totalbet >= betmaxsetting:
                    activenumber += betvaluesetting
                else:
                    activenumber += int((totalbet/betmaxsetting)*betvaluesetting)

                activenumber = int(activenumber/2)
                activenumber += 50

                if oldactivenumber != activenumber:
                    if writelist != '':
                        writelist += ',({},{})'.format(memberid,activenumber)
                    else:
                        writelist = '({},{})'.format(memberid,activenumber)
            if len(writelist) > 0:
                command = 'insert into member (memberid,activenumber) values {0} ' \
                          ' ON DUPLICATE KEY UPDATE activenumber=VALUES(activenumber) '.format(writelist)
                updateresult = await self.updatedbdata('update activenumber',command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:makeactivenumbersettle except:{0}'.format(e))

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

            url = PS_API_SERVER_URL + 'funds/withdrawall/?host_id={}&member_id=fish_{}&txn_id={}&purpose=1'.format(host_id,memberid,txn_id,)
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
                    updateresult = await self.updatedbdata(logintoken,command)

                    # update member credit and silvercredit
                    command = 'update member set credit= credit+"{0}" ,silvercredit = silvercredit+"{1}" where memberid = "{2}"'.format(amount,amount_silver,memberid)
                    updateresult = await self.updatedbdata(logintoken,command)
                else:
                    result = False
                    raise Exception('response not 200:{}'.format(json.dumps(data)))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_transferAllCreditToHost except:{0}'.format(e))

    async def clear_fish_game_credit_account(self,redis_obj, app):
        try:
            # get all fish dirty key
            dirtykeylist = await redis_obj.hkeys('dirtyfish')
            if dirtykeylist is None:
                return True
            if len(dirtykeylist)<= 0:
                return True
            for item in dirtykeylist:
                valuelist = item.split('_')
                if len(valuelist) != 3:
                    raise Exception('valuelist lens is not 3')

                halltype = valuelist[0]
                gameid = valuelist[1]
                memberid = valuelist[2]

                keyisexist = await redis_obj.get_value('fish_{}'.format(item))
                if keyisexist is not None:  # 如果存在表示在遊戲中
                    continue

                # 不存在的話 將所有錢包轉回 , 並刪除 相關 redis key
                if halltype == 'g':
                    hostid = PS_HOST_ID
                    hallid = 0
                elif halltype == 's':
                    hostid = PS_HOST_ID_S
                    hallid = 1

                await self.call_gameapi_transferAllCreditToHost('transfer all credittohost', memberid, hostid, hallid)
                # del member fish game key
                await redis_obj.del_key('fish_{}'.format(item))
                # del dirtyfish hkey
                await redis_obj.hdel('dirtyfish',item)
                # notice user
                asyncio.ensure_future(self.noticeusercredit(redis_obj, memberid))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:clear_fish_game_credit_account except:{0}'.format(e))

    async def call_gameapi_get_fish_game_history(self,host_id,gameid,starttime,endtime):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:call_gameapi_get_fish_game_history host_id:{},gameid:{},starttime:{},endtime:{}'.format(host_id,gameid,starttime,endtime))
            resultdata = {}
            url = PS_API_SERVER_URL + 'feed/minutelysummary/?host_id={}&start_dt={}&end_dt={}&game_id={}'.format(
                host_id, starttime, endtime, gameid )
            errcount = 0
            data = {}
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response:
                            if response.status == 200:
                                data = await response.json()
                                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                                    'call_gameapi_get_fish_game_history response:{},url:{}'.format(
                                                        data, url))

                                break
                            else:

                                errcount += 1
                                await asyncio.sleep(0)
                except Exception as e:
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'pg_asqldb:call_gameapi_get_fish_game_history transfer error e:{0}'.format(e))
                    await asyncio.sleep(0.1)
            if errcount >= 3:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:call_gameapi_get_fish_game_history error errcount:{0}'.format(
                                        errcount))
            else:
                if data is None:
                    raise Exception('get fish game history error')

                resultdata = data.copy()

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:call_gameapi_get_fish_game_history except:{0}'.format(e))

        return resultdata


    async def get_fish_game_bethistory(self,app,redis_obj):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info, "pg_asqldb:get_fish_game_bethistory start")
            gameidlist = []
            historydata_g = {}
            historydata_s = {}
            starttime = pg_general.get_tw_datetime()-timedelta(minutes=12)
            endtime = pg_general.get_tw_datetime()-timedelta(minutes=12)

            host_id_g = PS_HOST_ID
            host_id_s = PS_HOST_ID_S

            # get last task time
            command = 'select fish_bethistory_task_last_time from taskinfo'
            datalen, data = await self.getdbdata('get last fish bethistory taskinfo',command)
            if datalen !=1 :
                return False
            fish_bethistory_task_last_time = data.get('fish_bethistory_task_last_time')

            if fish_bethistory_task_last_time >= starttime:
                return False

            if (fish_bethistory_task_last_time + timedelta(minutes=1)) < starttime:
                starttime = fish_bethistory_task_last_time + timedelta(minutes=1)

            starttime = starttime.strftime('%Y-%m-%dT%H:%M:00')
            endtime = endtime.strftime('%Y-%m-%dT%H:%M:00')

            # get fish gameid list
            command = 'select gameid from gamefish'
            datalen, data = await self.getdbdata('get_fish_game_bethistory',command,True)
            if datalen <= 0:
                return True

            for item in data:
                gameidlist.append(item.get('gameid'))

            # gold
            for gameid in gameidlist:
                historydata_g = await self.call_gameapi_get_fish_game_history(host_id_g,gameid,starttime,endtime)
                historydata_s = await self.call_gameapi_get_fish_game_history(host_id_s,gameid,starttime,endtime)

            write_historydata_list_g = []
            write_historydata_list_s = []
            total_bet = 0
            if historydata_g is not None and historydata_g != {}:
                for key1 in historydata_g:
                    value1 = historydata_g[key1]  # value1 is dict
                    resulttime = key1.replace('T'," ")
                    resulttime = datetime.strptime(resulttime, '%Y-%m-%d %H:%M:%S')
                    resulttime = resulttime - timedelta(hours= 8)
                    resulttime = resulttime.strftime('%Y-%m-%d %H:%M:%S')
                    for key2 in value1:             # key2 is fish_{memberid}
                        memberid = key2.split('_')[1]
                        value2 = value1[key2]  # value2 is list

                        for round_data in value2:   # round_data is dict
                            gid = round_data.get('gid')
                            rnd = round_data.get('rnd')
                            bet = round_data.get('bet')
                            total_bet += pg_general.converttype(bet,int)
                            win = round_data.get('win')
                            write_historydata_list_g.append([gid,memberid,resulttime,bet,win,rnd])
                if len(write_historydata_list_g) > 0:
                    command = 'insert into bethistory_fish_g(gameid,memberid,resulttime,bet,win,rnd)values(%s,%s,%s,%s,%s,%s)'
                    insertresult = await self.insertdbdata('insert betshitory fish g',command,True,write_historydata_list_g)

                    # 做金爽榜及時榜單 total bet 累積
                    twdatetimestr = pg_general.get_tw_date_str()
                    twdatetimemonthstr = pg_general.get_tw_date_month_str()
                    twtodaydate = pg_general.get_tw_datetime().date()
                    if twtodaydate.day >= 1 and twtodaydate.day <= 15:
                        await redis_obj.incrby('totalmonthbet_{}'.format(twdatetimemonthstr), total_bet)
                    else:
                        await redis_obj.incrby('totalmonthbet2_{}'.format(twdatetimemonthstr), total_bet)



            if historydata_s is not None and historydata_s != {}:
                for key1 in historydata_s:
                    value1 = historydata_s[key1]  # value1 is dict
                    resulttime = key1.replace('T'," ")
                    resulttime = datetime.strptime(resulttime, '%Y-%m-%d %H:%M:%S')
                    resulttime = resulttime - timedelta(hours=8)
                    resulttime = resulttime.strftime('%Y-%m-%d %H:%M:%S')
                    for key2 in value1:             # key2 is fish_{memberid}
                        memberid = key2.split('_')[1]
                        value2 = value1[key2]  # value2 is list

                        for round_data in value2:   # round_data is dict
                            gid = round_data.get('gid')
                            rnd = round_data.get('rnd')
                            bet = round_data.get('bet')
                            total_bet += pg_general.converttype(bet,int)
                            win = round_data.get('win')
                            write_historydata_list_s.append([gid,memberid,resulttime,bet,win,rnd])
                if len(write_historydata_list_s) > 0:
                    command = 'insert into bethistory_fish_s(gameid,memberid,resulttime,bet,win,rnd)values(%s,%s,%s,%s,%s,%s)'
                    insertresult = await self.insertdbdata('insert betshitory fish g',command,True,write_historydata_list_s)

                    # 做金爽榜及時榜單 total bet 累積
                    twdatetimestr = pg_general.get_tw_date_str()
                    twdatetimemonthstr = pg_general.get_tw_date_month_str()
                    twtodaydate = pg_general.get_tw_datetime().date()
                    await redis_obj.incrby('totaldaybets_{}'.format(twdatetimestr), total_bet)
                    await redis_obj.incrby('totalmonthbets_{}'.format(twdatetimemonthstr), total_bet)


            # 都做完 寫入 taskinfo
            command = 'update taskinfo set fish_bethistory_task_last_time = "{0}" where taskinfo.index=1'.format(endtime)
            updateresult = await self.updatedbdata('update taskinfo.fish_bethistory_task_last_time',command)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:get_fish_game_bethistory except:{0}'.format(e))
        return True

    async def getmemberinfo(self,memberid):
        try:
            result = False
            clientdata = {}

            command = 'select nickname,username,phone,card,level,credit,silvercredit,point,safe,auserid,fbid from member where memberid = "{0}"'.format(memberid)
            datalen, data = await self.getdbdata('getmemberinfo',command)

            if datalen ==1:
                clientdata = {
                    "nickname": data.get('nickname'),
                    "username": data.get('username'),
                    "phone": data.get('phone'),
                    "card": data.get('card'),
                    "level": data.get('level'),
                    "credit": data.get('credit'),
                    "silvercredit": data.get('silvercredit'),
                    "point": data.get('point'),
                    "safe": data.get('safe'),
                    "auserid": data.get('auserid'),
                    "fbid": data.get('fbid')
                }
                result = True

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getmemberinfo except:{0}'.format(e))
        return result, clientdata

    async def getmemberfromphone(self,phone):
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'pg_asqldb:getmemberfromphone start')
            result = False
            clientdata = {"phonelist":[]}

            command = 'select memberid from member where phone = "{0}"'.format(phone)
            datalen, data = await self.getdbdata('getmemberfromphone',command,True)

            phonelist = []
            if datalen >0:
                for item in data:
                    phonelist.append(item.get('memberid'))
                clientdata = {
                    "phonelist": phonelist
                }

            result = True
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_asqldb:getmemberfromphone except:{0}'.format(e))
        return result, clientdata