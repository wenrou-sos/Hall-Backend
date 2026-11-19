import asyncio
import aiomysql
import os
import env_setting
import pg_general
from traceback import format_exc
import importlib.util

if env_setting.LOCAL_SERVER == True:
    ECPAY_SDK_PATH = "ecpay_payment_sdk.py"
else:
    ECPAY_SDK_PATH = os.path.dirname(os.path.abspath(__file__)) + "//ecpay_payment_sdk.py"

if env_setting.LOCAL_SERVER == True:
    DB_HOST = '35.234.13.198'
    DB_HOST_READ = '35.234.13.198'
else:
    if env_setting.PRODUCTION_MODE == False:
        DB_HOST = '35.234.13.198'
        DB_HOST_READ = '35.234.13.198'
    else:
        DB_HOST = '35.234.13.198'
        DB_HOST_READ = '35.234.13.198'

DB_USER = 'gm-server'
DB_NAME = 'slot-game'
if env_setting.PRODUCTION_MODE == False:
    DB_PASSWORD = 'MBpBy7RCNyH2HjUW'
else:
    DB_PASSWORD = 'MBpBy7RCNyH2HjUW'

class PG_SLOTGAME_ASQLDB:
    async def createpool(self):
        try:
            if not env_setting.LOCAL_SERVER:
                self.pool = await aiomysql.create_pool(host=DB_HOST, port=3306, user=DB_USER,
                                                       password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

                pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                    "pg_slotgame_asqldb:createpool: slot-game db create pool done")

                self.pool_read = await aiomysql.create_pool(host=DB_HOST_READ, port=3306, user=DB_USER,
                                                            password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
                pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                    "pg_slotgame_asqldb:createpool: repplication slot-game db create pool done")
            else:
                self.pool = await aiomysql.create_pool(host=DB_HOST, port=3306, user=DB_USER,
                                                       password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)

                self.pool_read = await aiomysql.create_pool(host=DB_HOST_READ, port=3306, user=DB_USER,
                                                       password=DB_PASSWORD, db=DB_NAME, maxsize=1024, autocommit=True)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                "pg_slotgame_asqldb:createpool except: {0}".format(e))

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
                                "pg_slotgame_asqldb:getdbdata:command=None logintoken:{0}".format(logintoken))
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
                                            "pg_slotgame_asqldb:getdbdata:execute command:{0}, logintoken:{1}".format(command,
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
                                    'pg_slotgame_asqldb:getdbdata exception:{0}, command:{1}, logintoken:{2},errcount:{3}'.format(e, command,
                                                                                                            logintoken,errcount))
                await asyncio.sleep(0)
        try:

            if datalen >= 10000:
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                             "pg_slotgame_asqldb:getdbdata:finally datalen:{0}, logintoken:{1}".format(datalen, logintoken))
            else:
                pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_slotgame_asqldb:getdbdata:finally datalen:{0}, data:{1}, logintoken:{2}".format(datalen,data,logintoken))
        except ValueError as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_slotgame_asqldb:getdbdata ValueError:{0}, logintoken:{1}'.format(format_exc(), logintoken))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_slotgame_asqldb:getdbdata except:{0}, logintoken:{1}'.format(format_exc(), logintoken))

        return datalen, data

    async def insertdbdata(self, logintoken, command=None,many=False,manydata=[]):
        result = False
        index = 0
        if command is None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_slotgame_asqldb:insertdbdata:command=None logintoken:{0}".format(logintoken))
            return result, index
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        "pg_slotgame_asqldb:insertdbdata:execute command:{0}, logintoken:{1}".format(command,
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
                                'pg_slotgame_asqldb:insertdbdata exception:{0}, command:{1}, logintoken:{2}'.format(e, command,
                                                                                                           logintoken))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_slotgame_asqldb:insertdbdata:finally result:{0}, index:{1}, logintoken:{2}".format(result,
                                                                                                              index,
                                                                                                              logintoken))
            return result, index

    async def updatedbdata(self, logintoken, command=None):
        result = False
        if command is None:
            pg_general.writelog(pg_general.PG_LogerLevel.warn,
                                "pg_slotgame_asqldb:updatedbdata:command=None logintoken:{0}".format(logintoken))
            return result
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    pg_general.writelog(pg_general.PG_LogerLevel.info,
                                        "pg_slotgame_asqldb:updatedbdata:execute command:{0}, logintoken:{1}".format(command,
                                                                                                            logintoken))
                    datarows = await cur.execute(command)
                    await conn.commit()
                    result = True
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'pg_slotgame_asqldb:updatedbdata exception:{0}, command:{1}, logintoken:{2}'.format(e, command,
                                                                                                           logintoken))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                "pg_slotgame_asqldb:updatedbdata:finally result:{0}, logintoken:{1}".format(result, logintoken))
            return result
