
import json
from utils import *
import uuid
import hashlib

#桌椅信息
INVALID_CHAIR = 65535
INVALID_TABLE = 65535

#扩展人数
RESERVE_USER_COUNT = 40

#游戏类型
GAME_MODULE_GOLD = 0x0001   #金币类型
GAME_MODULE_EDUCATE = 0x0008    #训练类型，试玩场

#匹配规则
MATE_ALLOW = 0x0001
MATE_SAME_ADDRESS = 0x0002       #同地址过滤
MATE_LAST_TABLE = 0x0003         #同桌过滤

def GenServerUUID():
    return hashlib.md5(str(uuid.uuid1()).encode()).hexdigest()

#用户状态
class eUS(object):
    US_NULL = 0x00      #没有状态
    US_FREE = 0x01      #自由状态
    US_SIT = 0x02       #坐下状态
    US_READY = 0x03     #准备状态
    US_PLAYING = 0x05   #游戏状态
    US_OFFLINE = 0x06   #断线状态
    US_EXIT = 0x07      #准备退出游戏状态

#游戏状态
class eGS(object):
    GS_FREE = 0         #空闲状态
    GS_PLAY = 100       #游戏状态
    GS_WAIT = 200       #等待状态

#游戏开始模式
class eGSM(object):
    SM_CONTROL          = 0         #手动开始
    SM_FULL_READY       = 1         #满人且所有准备
    SM_ATLEAST_2_READY  = 10        #至少2人准备
    SM_ATLEAST_3_READY  = 11        #至少3人准备
    SM_ATLEAST_4_READY  = 12        #至少4人准备

'''
//8档血池等级
//<Status Val = "1" Name = "系统必赢" />
//<Status Val = "2" Name = "系统大赢" />
//<Status Val = "3" Name = "系统中赢" />
//<Status Val = "4" Name = "系统小赢" />
//<Status Val = "5" Name = "系统小输" />
//<Status Val = "6" Name = "系统中输" />
//<Status Val = "7" Name = "系统大输" />
//<Status Val = "8" Name = "系统必输" />
'''
class eGMToolCtrlLevel(object):
    GM_INVALIDATE = -1  #非法状态
    GM_NORMAL = 0       #系统正常
    GM_BIYING = 1       #系统必赢
    GM_DAYING = 2       #系统大赢
    GM_ZHONGYING = 3    #系统中赢
    GM_XIAOYING = 4     #系统小赢
    GM_XIAOSHU = 5      #系统小输
    GM_ZHONGSHU = 6     #系统中输
    GM_DASHU = 7        #系统大输
    GM_BISHU = 8        #系统必输

class eST(object):
    ST_NULL = 0x00,     #无效积分
    ST_WIN = 0x01,      #胜局积分
    ST_LOSE = 0x02,     #输局积分
    ST_DRAW = 0x03,     #和局积分
    ST_FLEE = 0x04,     #逃局积分

class stScoreInfo(object):
    def __init__(self):
        self.mScoreType = eST.ST_NULL
        self.mScore = 0
        self.mRevenue = 0   #税收
        self.mCost = 0
        self.mModScore = 0

class ServiceOpt(object):
    sSvrUUID = ""
    sIndex = 0
    sHashKey = ""
    sHostApiKey = ""
    sSubGameId = 0
    sSvrName = "-"
    sMaxPlayer = 5000
    sTableCount = 1000
    sSvrPort = 0
    sSvrType = 0
    sModuleName = "dummy"
    sJsonData = {}
    sJOptions = {}
    #游戏设定(可修改)
    sCellScore = 100
    sAllowAndroid = True        # 是否允许匹配机器人
    sMatchIPFilter = False      # 是否过滤同IP网段玩家
    sMatchWaitTime = [1,3,3,5]  # 匹配等待时间[隨機方式：權重種子取出不放回；所有  權重種子用完後重置]
    sThinkTime = 20             # 回合操作時間
    # sChallengeTime = 20       # 接受比牌的思考時間
    # sRobotFightRate = 0       # 機器人目前比牌點數最小，發起比牌的機率
    sNoticeScore = 0            # 跑马灯记录条件分数
    sRobotDrawRate = 20         # 機器人摸到好牌的機率
    sRobotDrawRateVip = 80      # vip房內，機器人摸到好牌的機率
    sBadDrawRate = 0            # 真人玩家啟用壞牌抽牌機制的機率
    sBadDrawRateVip = 80        # vip房內，真人玩家啟用壞牌抽牌機制的機率
    sAllowLeverage = 1          # 是否允許啟用以小博大機制結算分數，預設為1開啟
    sPreventArbitrage = 0       # 防止玩家套利機制0關閉1啟動
    sMaxConnected = 2000        # 房間最大容留連線人數
    sWinTimes = 20              # 玩家贏分超過底注N倍
    sMinEnterScore = 0
    sMaxEnterScore = 0
    sRobotRate = 0
    sMultiHost = 0  # 多代理與單代理商模式，預設為單代理商模式

    @classmethod
    def IsEducateSvr(cls):
        return cls.sSvrType == 1

    @classmethod
    def InitOptions(cls, data):
        cls.sIndex = data["id"]
        cls.sHashKey = data["hash_key"]
        cls.sHostApiKey = data["host_api_key"]
        cls.sSubGameId = data["subgame_id"]
        cls.sSvrName = "dummy"
        cls.sModuleName = "dummy"

        ''' Option = {
            "srvtype" : 1,                  #服务类型(1：体验场 2：正式场)
            "tablecount" : 100,             #桌子数
            "cellscore" : 1000,             #底注(cent)
            "accessscore" : 100000,         #准入(cent)，0:不限制
            "thinktime" : 20,               #思考时间(s)
            "ledmul" : 180,                 #跑马灯倍数
            "allowrobot" : 1,               #是否允许匹配机器人(0:不允许)
            "ipfilter" : 1,                 #匹配时是否过滤同IP段玩家(0:不过滤)
            "random_robot_rate" : 50,       #3~4位真人玩家進桌拆分機率
            # 非newsvropt設定，由newchl設定，從newsvropt與getsvropt帶入
            "allow_leverage" : 1,           #是否允許啟用以小博大機制結算分數(1:允許)
            "pre_arbitrage" : 0,            #防止玩家套利機制0關閉1啟動
            "max_connected" : 2000,         #房間最大容留連線人數
            "win_times" : 20,               #贏分底注倍率上限，超過則下一場開始vip
            "robot_draw_rate" : 20          #機器人摸到好牌的機率
            "robot_draw_rate_vip" : 80      #vip房內，機器人摸到好牌的機率
            "bad_draw_rate" : 0,            #真人玩家啟用壞牌抽牌機制的機率
            "bad_draw_rate_vip" : 80,       #vip房內，真人玩家啟用壞牌抽牌機制的機率
        }'''
        cls.sJOptions = {} if len(data["json_options"]) == 0 else json.loads(data["json_options"])
        if "random_robot_rate" in cls.sJOptions:
            if cls.sJOptions["random_robot_rate"] is None:
                cls.sRobotRate = 0
            else:
                cls.sRobotRate = cls.sJOptions["random_robot_rate"]
        else:
            cls.sRobotRate = 0
        if "max_score" in cls.sJOptions: cls.sMaxScore = cls.sJOptions["max_score"]
        if "MultiHost" in cls.sJOptions: cls.sMultiHost = cls.sJOptions["MultiHost"]
        if "cellscore" in cls.sJOptions: cls.sCellScore = cls.sJOptions["cellscore"]
        if "accessscore" in cls.sJOptions: cls.sMinEnterScore = cls.sJOptions["accessscore"]
        if "thinktime" in cls.sJOptions: cls.sThinkTime = cls.sJOptions["thinktime"]
        # if "challengetime" in cls.sChallengeTime: cls.sChallengeTime = cls.sJOptions["challengetime"]
        # if "robot_fight_rate" in cls.sRobotFightRate: cls.sRobotFightRate = cls.sJOptions["robot_fight_rate"]
        if "ledmul" in cls.sJOptions: cls.sNoticeScore = cls.sCellScore * cls.sJOptions["ledmul"]
        if "allowrobot" in cls.sJOptions: cls.sAllowAndroid = False if cls.sJOptions["allowrobot"] == 0 else True
        if "ipfilter" in cls.sJOptions: cls.sMatchIPFilter = False if cls.sJOptions["ipfilter"] == 0 else True
        if "allow_leverage" in cls.sJOptions: cls.sAllowLeverage = 0 if cls.sJOptions["allow_leverage"] == 0 else 1
        if "pre_arbitrage" in cls.sJOptions: cls.sPreventArbitrage = 1 if cls.sJOptions["pre_arbitrage"] == 1 else 0
        if "max_connected" in cls.sJOptions: cls.sMaxConnected = cls.sJOptions["max_connected"]
        if "srvtype" in cls.sJOptions: cls.sSvrType = cls.sJOptions["srvtype"]
        if "win_times" in cls.sJOptions: cls.sWinTimes = cls.sJOptions["win_times"]
        if "robot_draw_rate" in cls.sJOptions: cls.sRobotDrawRate = cls.sJOptions["robot_draw_rate"]
        if "robot_draw_rate_vip" in cls.sJOptions: cls.sRobotDrawRateVip = cls.sJOptions["robot_draw_rate_vip"]
        if "bad_draw_rate" in cls.sJOptions: cls.sBadDrawRate = cls.sJOptions["bad_draw_rate"]
        if "bad_draw_rate_vip" in cls.sJOptions: cls.sBadDrawRateVip = cls.sJOptions["bad_draw_rate_vip"]
        cls.sThinkTime = cls.sThinkTime if cls.sThinkTime > 0 else 20
        # cls.sChallengeTime = cls.sChallengeTime if cls.sChallengeTime > 0 else 8
        # cls.robot_fight_rate = cls.sRobotFightRate if cls.sRobotFightRate > 0 else 0
        cls.sMaxConnected = cls.sMaxConnected if cls.sMaxConnected > 0 else 2000
        cls.sWinTimes = cls.sWinTimes if cls.sWinTimes >= 1 else 20
        cls.sRobotDrawRate = cls.sRobotDrawRate if cls.sRobotDrawRate >= 0 else 20
        cls.sRobotDrawRateVip = cls.sRobotDrawRateVip if cls.sRobotDrawRateVip >= 0 else 80
        cls.sBadDrawRate = cls.sBadDrawRate if cls.sBadDrawRate >= 0 else 0
        cls.sBadDrawRateVip = cls.sBadDrawRateVip if cls.sBadDrawRateVip >= 0 else 80
        cls.sRobotRate = cls.sRobotRate if cls.sRobotRate > 0 and cls.sRobotRate <= 100 else 0

    @classmethod
    def HotUpdate(cls, data):
        cls.sJOptions = {} if len(data["json_options"]) == 0 else json.loads(
            data["json_options"])
        if cls.sJOptions.get('random_robot_rate'):
            cls.sRobotRate = cls.sJOptions["random_robot_rate"]
        else:
            cls.sRobotRate = 0
        if "allowrobot" in cls.sJOptions: cls.sAllowAndroid = False if \
        cls.sJOptions["allowrobot"] == 0 else True
        if "thinktime" in cls.sJOptions: cls.sThinkTime = cls.sJOptions["thinktime"]
        # if "challengetime" in cls.sChallengeTime: cls.sChallengeTime = cls.sJOptions["challengetime"]
        # if "robot_fight_rate" in cls.sRobotFightRate: cls.sRobotFightRate = cls.sJOptions["robot_fight_rate"]
        if "pre_arbitrage" in cls.sJOptions: cls.sPreventArbitrage = 1 if \
        cls.sJOptions["pre_arbitrage"] == 1 else 0
        if "win_times" in cls.sJOptions: cls.sWinTimes = cls.sJOptions[
            "win_times"]
        if "robot_draw_rate" in cls.sJOptions: cls.sRobotDrawRate = \
        cls.sJOptions["robot_draw_rate"]
        if "robot_draw_rate_vip" in cls.sJOptions: cls.sRobotDrawRateVip = \
        cls.sJOptions["robot_draw_rate_vip"]
        if "bad_draw_rate" in cls.sJOptions: cls.sBadDrawRate = cls.sJOptions[
            "bad_draw_rate"]
        if "bad_draw_rate_vip" in cls.sJOptions: cls.sBadDrawRateVip = \
        cls.sJOptions["bad_draw_rate_vip"]
        cls.sThinkTime = cls.sThinkTime if cls.sThinkTime > 0 else 20
        # cls.sChallengeTime = cls.sChallengeTime if cls.sChallengeTime > 0 else 8
        # cls.sRobotFightRate = cls.sRobotFightRate if cls.sRobotFightRate > 0 else 0
        cls.sWinTimes = cls.sWinTimes if cls.sWinTimes >= 1 else 20
        cls.sRobotDrawRate = cls.sRobotDrawRate if cls.sRobotDrawRate >= 0 else 20
        cls.sRobotDrawRateVip = cls.sRobotDrawRateVip if cls.sRobotDrawRateVip >= 0 else 80
        cls.sBadDrawRate = cls.sBadDrawRate if cls.sBadDrawRate >= 0 else 0
        cls.sBadDrawRateVip = cls.sBadDrawRateVip if cls.sBadDrawRateVip >= 0 else 80
        cls.sRobotRate = cls.sRobotRate if cls.sRobotRate > 0 and cls.sRobotRate <= 100 else 0

class ServiceAttr(object):
    sChairCnt = 0           # 椅子数量
    sMinPlayer = 3          # 最低玩家数
    sStartMode = 0          # 游戏开始模式
    sAllowMatch = True      # 匹配游戏
    sWaitStartTime = 15     # 等待下一对局开始时间

class AndroidOptions(object):
    sActionTime = 1         # 响应时间
    sCheckOpTime = 3        # 检测操作时间
    sCheckStTime = 3        # 检查状态时间
    sMinWaitTime = 3        # 最小等待时间
    sMaxWaitTime = 5        # 最大等待时间

    @classmethod
    def InitOptions(cls, data):
        cls.sActionTime = data["action_interval"]
        cls.sCheckOpTime = data["check_action"]
        cls.sCheckStTime = data["check_status"]
        cls.sMinWaitTime = data["min_wait"]
        cls.sMaxWaitTime = data["max_wait"]

#桌子日志类
class stTableLog(object):
    def __init__(self):
        self.nTableID = 0       #桌子号
        self.sRoundID = ""      #游戏局号
        self.sTime = ""         #游戏时间
        self.sDetailInfo = ""   #游戏详细信息

#玩家日志类
class stPlayerLog(object):
    def __init__(self):
        self.nUUID = 0          #游戏UUID
        self.sMemberID = ""     #平台玩家ID
        self.sChannel = ""      #渠道
        self.mNickName = ""     #昵称
        self.nCalScore = 0      #投注
        self.nTax = 0           #税收
        self.nCurrentScore = 0  #当前分数
        self.sTime = ""         #游戏时间
        self.sRoundID = ""      #游戏局号
        self.nTableID = 0       #桌子号
        self.nChairID = 0       #座位号
