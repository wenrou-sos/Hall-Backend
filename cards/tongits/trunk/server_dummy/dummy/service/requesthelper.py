
import json
from urllib import request, parse
from urllib.parse import urlparse
from utils import *

'''
sPsUrls = {
    "login" : "https://stage-api.iplaystar.net/proxy/psx1/login",
    "logout": "https://stage-api.iplaystar.net/proxy/psx1/logout",
    "getbalance" : "https://stage-api.iplaystar.net/proxy/psx1/getbalance",
    "rollin": "https://stage-api.iplaystar.net/proxy/psx1/rollin",
    "rollout" : "https://stage-api.iplaystar.net/proxy/psx1/rollout"
}
'''

class RequestHelper(object):
    @classmethod
    def DoPost(cls, url, params):
        reqtime = GetServerTime()
        suuid = GenShortUUID()

        try:
            if url is None or len(url) == 0:
                Warn(f'RH POST [Fail], suuid: {suuid}, fail url')
                return None

            p = urlparse(url)
            # url 參考 "http://www.programiz.com"
            # p參考結果 ParseResult(scheme='https', netloc='www.programiz.com', path='/python-programming', params='', query='', fragment='')
            if len(p.scheme) == 0 or len(p.netloc) == 0:
                Warn(f'RH POST [Fail], suuid: {suuid}, fail url: {url}')
                return None

            Log(f'RH POST [BEGIN], suuid: {suuid}, url: {url}, params: {params}')

            d = json.dumps(params).encode()
            h = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko', 'Content-Type' : 'application/json;charset=utf-8'}
            Log("DoPost:", url)
            req = request.Request(url = url, data = d, headers = h)
            res = request.urlopen(req, timeout=60)
            res = res.read()
            jdata = json.loads(res.decode(encoding='utf-8'))

            restime = GetServerTime()
            Log(f'RH POST [END], suuid: {suuid}, response: {jdata}, t: {restime - reqtime}ms')
            return jdata
        except:
            restime = GetServerTime()
            Warn(f'RH POST [END], suuid: {suuid}, except, t: {restime - reqtime}ms')
            PrintEXC()
            return None

    @classmethod
    def DoGet(cls, url, params):
        reqtime = GetServerTime()
        suuid = GenShortUUID()

        try:
            if url is None or len(url) == 0:
                Warn(f'RH GET [Fail], suuid: {suuid}, fail url')
                return None

            p = urlparse(url)
            # url 參考 "http://www.programiz.com"
            # p參考結果 ParseResult(scheme='https', netloc='www.programiz.com', path='/python-programming', params='', query='', fragment='')
            if len(p.scheme) == 0 or len(p.netloc) == 0:
                Warn(f'RH GET [Fail], suuid: {suuid}, fail url: {url}')
                return None

            request_url = url + "?"
            b = False
            for k, v in params.items():
                if b:
                    request_url += ("&" + k + "=")
                else:
                    request_url += (k + "=")
                    b = True
                request_url += str(v)
            h = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
                 'Content-Type': 'application/json;charset=utf-8'}

            Log(f'RH GET [BEGIN], suuid: {suuid}, url: {request_url}')

            req = request.Request(url=request_url, headers=h)
            response = request.urlopen(req, timeout=60)
            response = response.read()
            jdata = json.loads(response.decode(encoding='utf-8'))

            restime = GetServerTime()
            Log(f'RH GET [END], suuid: {suuid}, response: {jdata}, t: {restime - reqtime}ms')
            return jdata
        except:
            restime = GetServerTime()
            Warn(f'RH GET [END], suuid: {suuid}, except, t: {restime - reqtime}ms')
            PrintEXC()
            return None

    @classmethod
    def ReqLoginVerify(cls, url, host_api_key, access_token):
        return cls.DoPost(url, {
            "host_api_key" : host_api_key,
            "access_token" : access_token
        })

    @classmethod
    def ReqQueryBalance(cls, url, host_api_key, member_id):
        return cls.DoPost(url, {
            "host_api_key" : host_api_key,
            "member_id" : member_id
        })

    @classmethod
    def ReqRollIn(cls, url, host_api_key, member_id, txn_id, amount):
        return cls.DoPost(url, {
            "host_api_key" : host_api_key,
            "member_id" : member_id,
            "txn_id" : txn_id,
            "amount" : int(amount)
        })

    @classmethod
    def ReqRollOut(cls, url, host_api_key, member_id, txn_id, amount):
        return cls.DoPost(url, {
            "host_api_key" : host_api_key,
            "member_id" : member_id,
            "txn_id" : txn_id,
            "amount" : int(amount)
        })

    @classmethod
    def ReqLogout(cls, url, host_api_key, access_token):
        return cls.DoPost(url, {
            "host_api_key" : host_api_key,
            "access_token" : access_token
        })

    @classmethod
    def ReqGetGameList(cls, url, host_api_key, user_type):  # 新增user_type導入HDRGameServerList
        return cls.DoPost(url, {
            "host_api_key": host_api_key,
            "user_type": user_type
        })

    @classmethod
    def ReqMultiHostBanned(cls, url, host_api_key, type_id, game_id, player_list):
        return cls.DoPost(url, {
            "host_api_key": host_api_key,
            "type": type_id,
            "game_id": game_id,
            "player_list": player_list,
        })

    @classmethod
    def ReqMultiHostVip(cls, url, host_api_key, type_id, game_id, player_list):
        return cls.DoPost(url, {
            "host_api_key": host_api_key,
            "type": type_id,
            "game_id": game_id,
            "player_list": player_list,
        })

    @classmethod
    def ReqMultiHostSvropt(cls, url, host_api_key, game_id, subgame_id):
        return cls.DoPost(url, {
            "host_api_key": host_api_key,
            "game_id": game_id,
            "subgame_id": subgame_id,
        })

    @classmethod
    def ReqMultiServerList(cls, url, uuid):
        return cls.DoPost(url, {
            "uuid": uuid
        })

    @classmethod
    def ReqMultiOnLogout(cls, url, hostuuid):
        return cls.DoPost(url, {
            "hostuuid": hostuuid
        })

    @classmethod
    def ReqSyncToken(cls, url, hostuuid, new_token):
        return cls.DoPost(url, {
            "hostuuid": hostuuid,
            "new_token": new_token
        })

    @classmethod
    def ReqNumOfSingleInMulti(cls, url, multi_host_api_key, host_api_key):
        return cls.DoPost(url, {
            "multi_host_api_key": multi_host_api_key,
            "host_api_key": host_api_key
        })

    @classmethod
    def ReqHostMaintain(cls, url, host_api_key, is_maintain, multi_host_api_key):
        return cls.DoPost(url, {
            "host_api_key": host_api_key,
            "is_maintain": is_maintain,
            "multi_host_api_key": multi_host_api_key
        })

    @classmethod
    def ReqSyncBase(cls, url, hostuuid, faceid, frame, designation, card_style, clean_score):
        """將 base 資料同步至多代理商 redis
        """
        return cls.DoPost(url, {
            "hostuuid": hostuuid,
            "faceid": faceid,
            "frame": frame,
            "designation": designation,
            "card_style": card_style,
            "clean_score": clean_score
        })

    @classmethod
    def ReqSyncEvent(cls, url, hostuuid, data):
        """將 event 資料同步至多代理商 redis

        event 要同步的資料有 login_time、login_day、has_award、bonus

        Args:
            url:
            hostuuid:
            data (dict): 根據情況傳入不同的值
                Examples:
                    同步登入獎勵會帶入 login_time、login_day、has_award
                    同步每日點數會帶入 daily_point
                    同步剩餘點數會帶入 remain_point
        Returns:

        """

        data['hostuuid'] = hostuuid

        return cls.DoPost(url, data)

    @classmethod
    def ReqMultiReuestSingleEvent(cls, url, uuid):
        """多代理向單代理請求redis event
        """
        return cls.DoPost(url, {
            "uuid": uuid
        })
