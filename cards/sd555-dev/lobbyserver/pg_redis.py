import env_setting
import asyncio
import aredis
from datetime import datetime
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

    async def get_json_value(self,key):
        try:
            value = None
            json_value = None
            value = await self.r.get(key)
            if value is not None:
                json_value = json.loads(value.decode('utf-8'))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_json_value exception : {0}".format(e))
        finally:
            return json_value

    async def get_all_keys(self,keystr=None):
        try:
            keys = None
            if keystr is None:
                keys = await self.r.keys()
            else:
                keys = await self.r.keys(keystr)
                if keys is not None:
                    keys = [item.decode('utf-8') for item in keys]

            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:get_all_keys keys:{0}".format(keys))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_all_keys except:{0}".format(e))
        finally:
            return keys

    async def get_value(self, key):
        try:
            value = None
            # pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:get_value start,key:{}".format(key))
            value = await self.r.get(key)
            if  value is not None:
                value = str(value, encoding = "utf-8")
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:get_value value:{0} ".format(value))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_value except:{0}".format(e))
        finally:
            return value

    async def set_value(self,key,value,time=DEFAULT_EXPIRE_SECONDS):
        try:
            result = False
            # pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:set_value start")
            result = await self.r.setex(key,time,value)
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:set_value result:{0} ".format(result))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:set_value except:{0}".format(e))
        finally:
            return result

    async def get_db_size(self):
        try:
            dbsize = None
            dbsize = await self.r.dbsize()
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:get_db_size dbsize:{0} ".format(dbsize))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_db_size except:{0}".format(e))
        finally:
            return dbsize

    async def del_key(self,key):
        try:
            result = False
            result = await self.r.delete(key)
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:del_key result:{0} ".format(result))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:del_key except:{0}".format(e))
        finally:
            return result
    async def flushdb(self):
        await self.r.flushdb()

    async def ttl(self,key):
        try:
            data = -2
            data = await self.r.ttl(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:ttl except:{0}".format(e))
        return data
    async def expire(self,key,expiretime):
        try:
            data = False
            data = await self.r.expire(key,expiretime)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:expire except:{0}".format(e))
        return data
    async def lpush(self,key,content):
        try:
            data = 0
            data = await self.r.lpush(key,content)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:lpush except:{0}".format(e))
        return data
    async def rpop(self,key):
        try:
            data = ''
            data = await self.r.rpop(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:rpop except:{0}".format(e))
        return data
    async def llen(self,key):
        try:
            data = 0
            data = await self.r.llen(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:llen except:{0}".format(e))
        return data

    async def lrange(self,key,startindex,endindex):
        try:
            result = await self.r.lrange(key,startindex,endindex)
        except:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:lrange except:{}".format(e))
        finally:
            return result

    async def lpush(self,key,value):
        try:
            result = await self.r.lpush(key,value)
        except:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:lpush except:{}".format(e))
        finally:
            return result
    async def ltrim(self,key,startindex,endindex):
        try:
            result = await self.r.ltrim(key,startindex,endindex)
        except:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:ltrim except:{}".format(e))
        finally:
            return result

async def testmain():
    s = PGRedis()
    await s.flushdb()
    # keys = await s.get_all_keys()
    # await s.set_value('gorden','1234',20)
    # result = await s.get_value('kkk')
    # print(await s.get_value('gorden'))
    gorden = {
          "packageUrl": "https://production-resource-download.playgems.net/public_release/hotupdate/v1.3/root/ios/",
          "remoteManifestUrl": "https://production-resource-download.playgems.net/public_release/hotupdate/v1.3/root/ios/project_ios.manifest",
          "remoteVersionUrl": "https://production-resource-download.playgems.net/public_release/hotupdate/v1.3/root/ios/version_ios.manifest",
          "version": "1.1.3",
          "engineVersion": "3.17",
          "groupVersions": {},
          "assets": {
            "myTestUpgrade1": {
              "path": "lobby_1.1.3.zip",
              "compressed": True,
              "md5": "20190920_1850"
            }
          },
          "searchPaths": []
        }
    json_gorden = json.dumps(gorden)
    await s.set_value('gorden',json_gorden)
    print(json.loads(await s.get_value('gorden')))

if __name__ == '__main__':
    pg_general.loggerinit()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(testmain())
