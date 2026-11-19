
import sys
import os
import random

sys.path.append(('%s/../..' % (os.getcwd())))
sys.path.append(('%s/../../utils' % (os.getcwd())))

from utils import *
#from aes128 import *
from urllib import request, parse
import json
from tornado.httpclient import *

def DoRequest(url, params):
    d = json.dumps(params).encode()
    header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko', 'Content-Type' : 'application/json'}
    req = request.Request(url = url, data = d, headers = header_dict)
    res = request.urlopen(req)
    res = res.read()
    jdata = json.loads(res.decode(encoding='utf-8'))
    return jdata

def DoRequest2(url, params):
    http_client = HTTPClient()
    try:
        header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}
        response = http_client.fetch(HTTPRequest(url = url, method = "POST", headers = header_dict, body = json.dumps(params)))
        return response.body
    except HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        print("Error: " + str(e))
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("Error: " + str(e))
    http_client.close()

def DoGet(url, params):
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
        Log(request_url)
        response = request.urlopen(request_url, timeout=5)
        response = response.read()
        Log(response)
        jdata = json.loads(response.decode(encoding='utf-8'))
        return jdata
    except:
        PrintEXC()
        return None

if __name__ == "__main__":
    '''
    key = "0ct8p1ghs9olxujzkmdf"
    channel = "test2"

    datajson = {
        "action" : "login",
        "uuid" : "21212121211",
        "gameid" : "111",
        "money" : "10000",
        "order" : "sjdadkpaodiqmkajd",
        "nickname" : "test_001"
    }

    test = json.dumps(datajson)
    Info(len(test))

    test2 = json.loads(test)
    Info(test2)

    data = AES128Encrypt(key, datajson)
    Info("data", data)
    timestamp = str(GetServerTimeMS())

    signsrc = channel + timestamp + key
    md5 = hashlib.md5()
    md5.update(signsrc.encode(encoding='UTF-8'))
    sign = md5.hexdigest()

    request_url = "http://192.168.1.106:9180/v1/?_input_charset=utf-8"
    request_url += ("&channel=" + channel)
    request_url += ("&timestamp=" + timestamp)
    request_url += ("&data=" + data)
    request_url += ("&sign=" + sign)
    Info(request_url)

    response = request.urlopen(request_url, timeout=5)
    Info(response)
    '''

    '''
    url = 'http://192.168.3.4:9400/newchl'
    params = {
        "host_id" : "test_001",
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "data" : {
            "api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
            "timezone" : "-",
            "currency" : "-",
            "gs_url" : "-",
            "dl_url" : "-"
        }
    }
    print(DoRequest(url, params))
    '''


    '''
    url = 'http://192.168.3.4:9400/newsvrcfg'
    params = {
        "game_id" : "Demo",
        "data" : {
            "game_id" : "Demo",
            "game_type" : "-",
            "eng_name" : "-",
            "chs_name" : "-",
            "cht_name" : "-",
            "enable" : True
        }
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/modchl'
    params = {
        "host_api_key" : "TEST3",
        "data" : {
            "timezone" : "mod",
            "dl_url" : "mod--"
        }
    }
    print(DoRequest(url, params))
    '''
    '''
    url = 'http://192.168.1.106:9400/modsvrcfg'
    params = {
        "game_id" : "Demo3",
        "data" : {
            "cht_name" : "1234",
            "enable" : False
        }
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/traderecords'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "member_id" : "ca71b35c357e397d342513b86678b1eb",
        "type" : 0,
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/onlineinfo'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/loginrecords'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "start_dtm" : "2020-1-1 00:00:00",
        "end_dtm" : "2020-6-1 00:00:00",
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/forcelogout'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        #"subgame_id" : 2,
        #"member_id" : "32d24adf081563b1a6ba5d43f303982b",
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/tablerecords'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "start_dtm" : "2020-1-1 00:00:00",
        "end_dtm" : "2020-10-1 00:00:00",
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/playrecords'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        #"round_id" : "15888348390000002003",
        #"member_id" : "32d24adf081563b1a6ba5d43f303982b",
        "subgame_id" : 2,
        "start_dtm" : "2020-1-1 00:00:00",
        "end_dtm" : "2020-6-1 00:00:00",
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/hourrecords'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "start_dtm" : "2020-1-1 00:00:00",
        "end_dtm" : "2020-6-1 00:00:00",
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/dayrecords'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "start_dt" : "2020-1-1",
        "end_dt" : "2020-10-1",
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.1.106:9400/getchl'
    params = {
        "host_api_key" : "TEST2",
    }
    print(DoRequest(url, params))
    '''
    '''
    url = 'http://192.168.1.106:9400/delchl'
    params = {
        "host_api_key" : "TEST2",
    }
    print(DoRequest(url, params))
    '''
    '''
    url = 'http://192.168.1.106:9400/getsvrcfg'
    params = {
        "game_id" : "Demo2",
    }
    print(DoRequest(url, params))
    '''
    '''
    url = 'http://192.168.1.106:9400/delsvrcfg'
    params = {
        "game_id" : "Demo2",
    }
    print(DoRequest(url, params))
    '''
    '''
    url = 'http://192.168.3.4:9400/newsvropt'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "game_id" : "Demo",
        "subgame_id" : 1,
        "data" : {
            "srvtype" : 1,          #体验场
            "tablecount" : 100,   # 桌子数
            "cellscore" : 100,    # 底注(cent)
            "accessscore" : 5000,  # 准入(cent)
            "maxenterscore" : 0, # 进入分数上限(cent)
            "thinktime" : 30,    # 思考时间(s)
            "ledmul" : 180,       # 跑马灯倍数
            "allowrobot" : 1,   # 是否允许匹配机器人(0:不允许)
            "ipfilter" : 0,     # 匹配时是否过滤桶IP段玩家(0:不过滤)
            "robot_draw_rate" : 80,
        }
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.3.4:9400/getsvropt'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "game_id" : "Demo",
        "subgame_id" : 1,
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.3.4:9400/modsvropt'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "game_id" : "Demo",
        "subgame_id" : 1,
        "data" : {
            "cellscore" : 10000,    # 底注(cent)
        }
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.3.4:9400/newsvropt'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "game_id" : "Demo",
        "subgame_id" : 1,
        "data" : {
            "srvtype" : 1,          #体验场
            "tablecount" : 100,   # 桌子数
            "cellscore" : 100,    # 底注(cent)
            "accessscore" : 5000,  # 准入(cent)
            "thinktime" : 20,    # 思考时间(s)
            "ledmul" : 180,       # 跑马灯倍数
            "allowrobot" : 1,   # 是否允许匹配机器人(0:不允许)
            "ipfilter" : 0,     # 匹配时是否过滤桶IP段玩家(0:不过滤)
            "robot_draw_rate" : 80,
        }
    }
    print(DoRequest(url, params))
    '''

    '''
    url = 'http://192.168.3.4:9400/delsvropt'
    params = {
        "host_api_key" : "kmxnhsy5df4dw5sd5f4sdf54fsd",
        "game_id" : "Demo",
        "subgame_id" : 1,
    }
    print(DoRequest(url, params))
    '''


    '''
    url = 'http://192.168.1.106:9400/'
    params = {
        "action" : "gamerecord",
        "uuid" : 93,
        "token" : 0,
        "page" : 0,
        "count" : 5,
        "time" : "2020-04-09"
    }
    print(DoGet(url, params))
    '''


