from urllib import request, parse
from urllib.parse import urlparse
from utils import *
from tornado.httpclient import *
import json

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

            d = json.dumps(params).encode(encoding='utf-8')
            hd = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko', 'Content-Type': 'application/json;charset=utf-8'}
            req = request.Request(url=url, data=d, headers=hd)
            res = request.urlopen(req, timeout=60).read()
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
    def ReqGetDeck(cls, url, count):
        count = int(count)
        count = count if (count >= 1 and count <= 1000) else 100
        return cls.DoGet(url, { "deck_count": count })

    @classmethod
    def ReqGetTrans(cls, url, action, uuid, op, number, token):
        return cls.DoGet(url, {
            "action": action,
            "uuid": uuid,
            "op": op,
            "money": number,
            "token": token
        })

    # @classmethod
    # def ReqGetTransMultiHost(cls, url, action, uuid, op, number, token, txn_id):
    #     return cls.DoGet(url, {
    #         "action": action,
    #         "uuid": uuid,
    #         "op": op,
    #         "money": number,
    #         "token": token,
    #         "txn_id": txn_id
    #     })