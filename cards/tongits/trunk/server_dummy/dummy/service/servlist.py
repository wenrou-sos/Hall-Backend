import json
import random
from utils import *

class ServListInitError(Exception):
    pass

'''
    -------------------服务器结构图--------------------
    {
        classid1 = {
            levelid1 = {
                "index" = 0,
                "serverids" = [serverid1,serverid2,serverid3],
            }
        }
    }
    -------------------服务器列表--------------------
    {
        host_api_key = {
            subgame_id1 : [server_uuid, server_uuid......],
            subgame_id2 : [server_uuid, server_uuid......],
            ......
        }
    }
    -------------------游戏人数--------------------
    {
        host_api_key = {
            subgame_id1 : [max, cur],
            subgame_id2 : [max, cur],
            ......
        }
    }
'''

class ServListMgr(object):
    sHostApiKeySvrs = {}        #服务器列表
    mSvrLists = {}              #serveruuid->server_data
    mCounts = {}                #游戏人数：

    def __init__(self):
        raise ServListInitError("ServListMgr无法被初始化")

    # ----------------------服务器列表-----------------------------------
    @classmethod
    def GetHostApiKeySvrs(cls):
        return cls.sHostApiKeySvrs

    @classmethod
    def GetServsByHostApiKey(cls, sHostApiKey):
        if sHostApiKey in cls.sHostApiKeySvrs:
            return cls.sHostApiKeySvrs[sHostApiKey]
        return None

    @classmethod
    def AddServ(cls, server_data):
        if server_data is None:
            return
        mHostApiKeys = {}
        if server_data.host_api_key in cls.sHostApiKeySvrs:
            mHostApiKeys = cls.sHostApiKeySvrs[server_data.host_api_key]
        servers = []
        if server_data.subgame_id in mHostApiKeys:
            servers = mHostApiKeys[server_data.subgame_id]
        newserver = True
        for svr in servers:
            if server_data.server_uuid == svr.server_uuid:
                svr.CopyFrom(server_data)
                newserver = False
                break
        if newserver:
            servers.append(server_data)
        mHostApiKeys[server_data.subgame_id] = servers
        cls.sHostApiKeySvrs[server_data.host_api_key] = mHostApiKeys
        Log(cls.sHostApiKeySvrs)
        cls.mSvrLists[server_data.server_uuid] = server_data

    @classmethod
    def DelServ(cls, server_data):
        if server_data is None:
            return
        if server_data.host_api_key in cls.sHostApiKeySvrs:
            mHostApiKeys = cls.sHostApiKeySvrs[server_data.host_api_key]
            if server_data.subgame_id in mHostApiKeys:
                servers = mHostApiKeys[server_data.subgame_id]
                rmidx = -1
                for idx in range(len(servers)):
                    if server_data.server_uuid == servers[idx].server_uuid:
                        rmidx = idx
                        break
                if rmidx > 0:
                    servers.pop(rmidx)
        if server_data.server_uuid in cls.mSvrLists:
            del cls.mSvrLists[server_data.server_uuid]

    @classmethod
    def GetOptimalSvrByHostApiKey(cls, sHostApiKey):
        vRstSvrs = []
        if isinstance(sHostApiKey, str):
            sHostApiKey = sHostApiKey.encode()
        if sHostApiKey in cls.sHostApiKeySvrs:
            mHostApiKeys = cls.sHostApiKeySvrs[sHostApiKey]
            Log("负载均衡-从中找出最优的服务器", mHostApiKeys)
            for subgameid, servers in mHostApiKeys.items():
                optimal_level = 0
                optimal_score = 0
                optimal_server = None
                for server_data in servers:
                    level, score = cls.GetGradeOfServer(server_data)
                    if level >= optimal_level:
                            optimal_score = score
                            optimal_server = server_data
                vRstSvrs.append(optimal_server)
        return vRstSvrs

    @classmethod
    def GetSvrByHostApiKey(cls, sHostApiKey, sSvrUUID):
        if isinstance(sHostApiKey, str):
            sHostApiKey = sHostApiKey.encode()
        if isinstance(sSvrUUID, str):
            sSvrUUID = sSvrUUID.encode()
        if sHostApiKey in cls.sHostApiKeySvrs:
            mHostApiKeys = cls.sHostApiKeySvrs[sHostApiKey]
            for nSubGameId in mHostApiKeys.keys():
                servers = mHostApiKeys[nSubGameId]
                for server_data in servers:
                    if server_data.server_uuid == sSvrUUID:
                        return server_data
        return None

    @classmethod
    def GetSvrData(cls, sSvrUUID):
        if sSvrUUID not in cls.mSvrLists:
            return None
        return cls.mSvrLists[sSvrUUID]

    @classmethod
    def GetGradeOfServer(cls, server_data)->(int, int):
        nMaxPlayer = server_data.max_player if server_data.max_player > 0 else 500
        nCurPlayer = server_data.cur_player if server_data.cur_player >= 0 else 0
        score = int((nCurPlayer / nMaxPlayer) * 100)
        if score >= 0 and score <= 33:
            return 2, score
        if score > 33 and score <= 66:
            return 3, score
        return 1, score

    @classmethod
    def OnUpdate(cls, mOnlineInfos):
        #Log("在线玩家列表", mOnlineInfos)
        for sSvrUUID, count in mOnlineInfos.items():
            if sSvrUUID in cls.mSvrLists:
                server_data = cls.mSvrLists[sSvrUUID]
                server_data.cur_player = int(count)
                break
