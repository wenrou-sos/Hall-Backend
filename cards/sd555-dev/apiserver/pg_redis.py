import sys
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



    async def get_all_keys(self,keystr=None):
        try:
            keys = None
            if keystr is None:
                keys = await self.r.keys()
            else:
                keys = await self.r.keys(keystr)
                keys = [item.decode('utf-8') for item in keys ]


            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:get_all_keys keys:{0}".format(keys))
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
            if value is not None:
                value = str(value, encoding = "utf-8")
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:get_value value:{0} ".format(value))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:get_value except:{0}".format(e))
        finally:
            return value

    async def mget_json_value(self,key):
        try:
            value = None
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:mget_json_value start")
            value = await self.r.mget(key)

            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:mget_json_value value:{0} ".format(value))
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:mget_json_value except:{0}".format(e))
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
            pg_general.writelog(pg_general.PG_LogerLevel.info, "PGRedis:set_value start")
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

    async def sadd(self,set,value):
        try:
            data = await self.r.sadd(set,value)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:sadd except:{0}".format(e))
        return data
    async def incr(self,key):
        try:
            data = await self.r.incr(key)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:incr except:{0}".format(e))
        return data
    async def incrby(self,key,value):
        try:
            data = await self.r.incrby(key,value)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:incrby except:{0}".format(e))
        return data
    async def hincrby(self,key,field,value):
        try:
            data = await self.r.hincrby(key,field,value)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hincrby except:{0}".format(e))
        return data
    async def mget(self,keystr):
        try:
            data = await self.r.mget(keystr)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:mget except:{0}".format(e))
        return data
    async def hvals(self,key):
        try:
            datalist = []
            datalist = await self.r.hvals(key)
            datalist = [item.decode('utf-8') for item in datalist]


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hvals except:{0}".format(e))
        return datalist

    async def hget(self,key,field):
        try:
            value = None
            value = await self.r.hget(key,field)
            if value is not None:
                value = value.decode('utf-8')

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hget except:{0}".format(e))
        finally:
            return value

    async def convert(self,data):
        new_data = {key.decode(): val.decode() for key, val in data.items()}
        return new_data

    async def hgetall(self, key):
        try:
            value = None
            value = await self.r.hgetall(key)
            value = await self.convert(value)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hgetall except:{0}".format(e))
        finally:
            return value

    async def hset(self,key,field,value,ttlseconds=None):
        try:
            result = await self.r.hset(key,field,value)
            if ttlseconds is not None:
                await self.expire(key,ttlseconds)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hset except:{0}".format(e))
        finally:
            return result

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

    async def hmget(self,key,fieldlist):
        try:
            result = await self.r.hmget(key,fieldlist)
            result = [(item.decode('utf-8') if item is not None else '' ) for item in result]
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,"PGRedis:hmget except:{}".format(e))
        finally:
            return result

    async def hmset(self,key,mapping,ttlseconds=None):
        try:
            result = await self.r.hmset(key,mapping)
            if ttlseconds is not None:
                await self.expire(key,ttlseconds)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hmset except:{0}".format(e))
        finally:
            return result

    async def hkeys(self,key):
        try:
            result = await self.r.hkeys(key)
            result = [item.decode('utf-8') for item in result]
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hkeys except:{0}".format(e))
        finally:
            return result

    async def hdel(self,key,field):
        try:
            result = await self.r.hdel(key,field)
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:hdel except:{0}".format(e))
        finally:
            return result

    async def validatelogintoken(self, memberid, logintoken, mode=0):
        """

        Args:
            mode (bool): 是否繞過 redis 驗證
        """
        try:
            # get if memberid is online, 本機不檢查
            if env_setting.LOCAL_SERVER == True or mode == pg_general.PASS_REDIS_VALIDATION_CODE:
                result = True
                return result

            # memberid <= 10 不檢查
            if int(memberid) <= 10:
                result = True
                return result

            result = True
            # onlineresult = await self.get_value('online_{}'.format(memberid))
            membertoken = await self.get_value('{}'.format(memberid))
            if None in [membertoken] or membertoken != logintoken:
                callerfunction = sys._getframe().f_back.f_code.co_name
                if callerfunction != "logout_handle":
                    raise Exception('validatelogintoken error 1,membertoken:{},logintoken:{},caller:{}'.format(membertoken,logintoken,callerfunction))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error, "PGRedis:validatelogintoken except:{0}".format(e))
            result = False
        return result

    def str_to_dict(self, value):
        return json.loads(value.replace('\'', '\"'))

async def testmain():
    s = PGRedis()
    await s.del_key('testkey')
    # result = await s.hdel('gorden','k1')
    # data = await s.lrange("gordenlist",0,100)
    # print(data)
    # result = await s.ltrim('gordenlist',0,3)
    # data = await s.lrange('gordenlist',0,100)
    # print(data)
    result = await s.incrby('testkey',10)
    data = await s.get_value('testkey')
    print(data)

    pass
    pass


    # await s.flushdb()
    # # keys = await s.get_all_keys()
    # # await s.set_value('gorden','1234',20)
    # # result = await s.get_value('kkk')
    # # print(await s.get_value('gorden'))
    # gorden = {
    #       "packageUrl": "https://production-resource-download.playgems.net/public_release/hotupdate/v1.3/root/ios/",
    #       "remoteManifestUrl": "https://production-resource-download.playgems.net/public_release/hotupdate/v1.3/root/ios/project_ios.manifest",
    #       "remoteVersionUrl": "https://production-resource-download.playgems.net/public_release/hotupdate/v1.3/root/ios/version_ios.manifest",
    #       "version": "1.1.3",
    #       "engineVersion": "3.17",
    #       "groupVersions": {},
    #       "assets": {
    #         "myTestUpgrade1": {
    #           "path": "lobby_1.1.3.zip",
    #           "compressed": True,
    #           "md5": "20190920_1850"
    #         }
    #       },
    #       "searchPaths": []
    #     }
    # json_gorden = json.dumps(gorden)
    # await s.set_value('gorden',json_gorden)
    # print(json.loads(await s.get_value('gorden')))

    # data = await s.hvals('bethistory_gold_24001')
    # data = await s.mget(['test1','kk','test2'])
    # data = await s.get_value('online_25371')
if __name__ == '__main__':
    pg_general.loggerinit()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(testmain())
