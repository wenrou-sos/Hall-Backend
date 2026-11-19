import env_setting
import asyncio
import aredis
import pg_general
import json

if env_setting.LOCAL_SERVER:
    REDIS_HOST = '34.80.168.83'
else:
    if env_setting.PRODUCTION_MODE ==True:
        REDIS_HOST = 'production-jinsong-redisserver.playgems.net'
    else:
        REDIS_HOST = '10.148.0.14'


REDIS_PORT = '6379'
DEFAULT_EXPIRE_SECONDS = 86400

class PGRedis(object):

    def __init__(self):
        try:
            self.initialflag = False
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:__init__ start")
            self.host = REDIS_HOST
            self.port = REDIS_PORT
            self.pool = aredis.ConnectionPool(host=self.host, port=self.port)
            self.r = aredis.StrictRedis(connection_pool=self.pool)
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:__init__ end")
            self.initialflag = True
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:__init__ except:{0}".format(e))

    async def info(self):
        try:
            value = await self.r.info()
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:info except:{0}".format(e))
        finally:
            return value


    async def get_all_keys(self,keystr=None):
        try:
            keys = None
            if keystr is None:
                keys = await self.r.keys()
            else:
                keys = await self.r.keys(keystr)
                keys = [item.decode('utf-8') for item in keys ]

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_all_keys except:{0}".format(e))
        finally:
            return keys

    async def get_json_value(self,key):
        try:
            value = None
            json_value = None
            value = await self.r.get(key)
            if value is not None:
                json_value = json.loads(value.decode('utf-8'))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "get_json_value exception : {0}".format(e))
        finally:
            return json_value

    async def get_value(self, key):
        try:
            value = None
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:get_value start")
            value = await self.r.get(key)
            if  value is not None:
                value = str(value, encoding = "utf-8")

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_value except:{0}".format(e))
        finally:
            return value

    async def llen(self,key):
        try:
            value = None
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:llen start")
            value = await self.r.llen(key)
            if value is not None:
                value = str(value)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:llen except:{0}".format(e))
        finally:
            return value

    async def set_json_value(self,key,json_value,time=DEFAULT_EXPIRE_SECONDS):
        try:
            result = False
            value = json.dumps(json_value)
            result = await self.r.setex(key, time, value)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "set_json_value except:{0}".format(e))
        finally:
            return result

    async def set_value(self,key,value,time=DEFAULT_EXPIRE_SECONDS):
        try:
            result = False

            result = await self.r.setex(key,time,value)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:set_value except:{0}".format(e))
        finally:
            return result
    async def lpush(self,key,content):
        try:
            data = 0
            data = await self.r.lpush(key,content)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:lpush except:{0}".format(e))
        return data
    async def get_db_size(self):
        try:
            dbsize = None
            dbsize = await self.r.dbsize()

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_db_size except:{0}".format(e))
        finally:
            return dbsize

    async def del_key(self,key):
        try:
            result = False
            result = await self.r.delete(key)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:del_key except:{0}".format(e))
        finally:
            return result
    async def flushdb(self):
        await self.r.flushdb()

    async def expire(self,key,seconds=None):
        try:
            result = True
            if seconds is not None:
                result = await self.r.expire(key,seconds)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:expire except:{0}".format(e))
        finally:
            return result
    async def ttl(self,key):
        try:
            value = await self.r.ttl(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:ttl except:{0}".format(e))
        finally:
            return value
    async def hmset(self,key,mapping,ttlseconds=None):
        try:
            result = await self.r.hmset(key,mapping)
            if ttlseconds is not None:
                await self.expire(key,ttlseconds)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hmset except:{0}".format(e))
        finally:
            return result

    async def hmget(self,key,fieldlist):
        try:
            result = await self.r.hmget(key,fieldlist)
            result = [item.decode('utf-8') for item in result]
        except:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:hmget except:{}".format(e))
        finally:
            return result

    async def hset(self,key,field,value,ttlseconds=None):
        try:
            result = await self.r.hset(key,field,value)
            if ttlseconds is not None:
                await self.expire(key,ttlseconds)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hset except:{0}".format(e))
        finally:
            return result

    async def hget(self,key,field):
        try:
            value = None
            value = await self.r.hget(key,field)
            value = value.decode('utf-8')

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hget except:{0}".format(e))
        finally:
            return value

    async def convert(self,data):
        new_data = {key.decode(): val.decode() for key, val in data.items()}
        return new_data

    async def hgetall(self,key):
        try:
            value = None
            value = await self.r.hgetall(key)
            value = await self.convert(value)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hgetall except:{0}".format(e))
        finally:
            return value


    async def hkeys(self,key):
        try:
            keys = []
            keys = await self.r.hkeys(key)
            keys = [item.decode('utf-8') for item in keys]

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hkeys except:{0}".format(e))
        finally:
            return keys
    async def smembers(self,key):
        try:
            keys=[]
            keys = await self.r.smembers(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:smembers except:{0}".format(e))
        finally:
            return keys

    async def hdel(self,key,field):
        try:
            await self.r.hdel(key,field)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hdel except:{0}".format(e))
        finally:
            return
    async def incrby(self,key,value):
        try:
            data = await self.r.incrby(key,value)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:incrby except:{0}".format(e))
        return data
    async def hvals(self,key):
        try:
            data = await self.r.hvals(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hvals except:{0}".format(e))
        finally:
            return data
    async def mget(self,keylist):
        try:
            data = await self.r.mget(keylist)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:mget except:{0}".format(e))
        finally:
            return data
    async def incr(self,key):
        try:
            data = await self.r.incr(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:incr except:{0}".format(e))
        finally:
            return data
    async def lrange(self,args):
        try:
            key = args.split(',')[0]
            start = args.split(',')[1]
            end = args.split(',')[2]
            data = await self.r.lrange(key,start,end)
            valuelist = [item.decode('utf-8') for item in data]
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:incr except:{0}".format(e))
        finally:
            return valuelist

async def testmain():
    s = PGRedis()

    # result = await s.lrange('chatroom_channel_3,0,20')

    # result = await s.hmget("tutorialseats_PSS-APP-00019@6",["his1turn","his1multi"])

    keys = await s.get_all_keys('tempty*')
    print(1)
    # keys = await s.hmset('goldseats_PSS-APP-00019@1',{'memberid': 2600,'status': 2,'dateline':"2020-06-02 00:00:00"})
    # for item in keys:
    #     await s.del_key(item)
    #
    #
    # data = await s.mget(['online_2144'])
    print(1)
if __name__ == '__main__':
    pg_general.loggerinit()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(testmain())
