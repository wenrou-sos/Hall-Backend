from urllib import request, parse
from utils import *
from tornado.httpclient import *
import json

class RequestHelper(object):
    @classmethod
    def DoPost(cls, url, params):
        try:
            d = json.dumps(params).encode(encoding='utf-8')
            hd = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko', 'Content-Type': 'application/json;charset=utf-8'}
            req = request.Request(url=url, data=d, headers=hd)
            res = request.urlopen(req).read()
            jdata = json.loads(res.decode(encoding='utf-8'))
            return jdata
        except:
            PrintEXC()
            return None

    @classmethod
    def DoGet(cls, url, params):
        try:
            request_url = url + "?"
            b = False
            for k, v in params.items():
                if b:
                    request_url += ("&" + k + "=")
                else:
                    request_url += (k + "=")
                    b = True
                request_url += str(v)
            response = request.urlopen(request_url, timeout=10)
            response = response.read()
            Info(response)
            jdata = json.loads(response.decode(encoding='utf-8'))
            return jdata
        except:
            PrintEXC()
            return None
