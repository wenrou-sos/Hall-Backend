
from definations import *
import random
from utils import *
from collections import OrderedDict
from difflib import SequenceMatcher

class stMatchInfo(object):
    def __init__(self):
        self.nScore = 0             #参与匹配时的分数
        self.sIPAddr = "127.0.0.1"  #客户端地址
        self.pSvrUserItem = None
        self.nMateTime = 0       #可以开始参与匹配时间
        self.nMaxMateTime = 0       #最长匹配时间

    def __eq__(self, other):
        return self.pSvrUserItem.UUID == other.pSvrUserItem.UUID

    def __lt__(self, other):
        if (self.nScore == other.nScore):
            return int(self.nMateTime < other.nMateTime)
        return int(self.nScore < other.nScore)

#匹配管理
class Matcher(object):
    def __init__(self, nMatchRule = MATE_SAME_ADDRESS|MATE_LAST_TABLE):
        self.mMatchRule = nMatchRule  #匹配规则
        self.nCount = 0
        self.mMatchUsers = OrderedDict()
        self.match_users_group = []  # 預防玩家重複進入匹配列隊中的暫存

    def GetCount(self):
        return self.nCount

    def AddMatch(self, rMateInfo):
        if rMateInfo.nMateTime not in self.mMatchUsers:
            self.mMatchUsers[rMateInfo.nMateTime] = []
        self.mMatchUsers[rMateInfo.nMateTime].append(rMateInfo)
        self.match_users_group.append(rMateInfo.pSvrUserItem.UUID)
        # 建立暫時存取self.mMatchUsers.values()的清單
        values = []
        # 走訪取出所有self.mMatchUsers.keys()
        for key in list(self.mMatchUsers.keys()):
            val = self.mMatchUsers[key]
            # 如果玩家帳號values()早已存在
            if val in values:
                # 刪除這一個玩家的items()
                del self.mMatchUsers[key]
            else:
                # 否則加入至暫時存取區，表示新加入玩家，未重複匹配
                values.append(val)
        self.nCount += 1
        return True

    def DelMatchInfo(self, rMateInfo):
        if rMateInfo is None:
            return
        if rMateInfo.nMateTime not in self.mMatchUsers:
            return
        vMatcher = self.mMatchUsers[rMateInfo.nMateTime]
        nIdx = 0
        for r in vMatcher:
            if r == rMateInfo:
                break
            nIdx += 1
        if nIdx >= 0 and nIdx < len(vMatcher):
            self.nCount -= 1
            del vMatcher[nIdx]
        if len(vMatcher) == 0:
            del self.mMatchUsers[rMateInfo.nMateTime]

        try:
            self.match_users_group.remove(rMateInfo.pSvrUserItem.UUID)
        except:
            pass

    def DelMatchItem(self, pSvrUserItem):
        self.DelMatchInfo(self.FindMatchInfo(pSvrUserItem))

    def DelAll(self):
        self.mMatchUsers.clear()
        self.nCount = 0

    def FindMatchInfo(self, pSvrUserItem):
        if pSvrUserItem is not None:
            for _, vMatcher in self.mMatchUsers.items():
                for r in vMatcher:
                    if pSvrUserItem.UUID == r.pSvrUserItem.UUID:
                        return r
        return None

    def OnMatchGroups(self, nTick, nCount, vMateUsers):
        ipcheck = True
        vAllUsers = []
        for nTime, vMatcher in self.mMatchUsers.items():
            if nTime <= nTick:
                vAllUsers += vMatcher
        vAllUsers = sorted(vAllUsers, reverse=True)
        if len(vAllUsers) < ServiceAttr.sMinPlayer:
            for info in vAllUsers:
                if nTick >= info.nMaxMateTime:
                    vMateUsers.append(info)
        else:
            for info in vAllUsers:
                if len(vMateUsers) >= nCount:
                    break
                #IP条件过滤(IPV4)
                if ServiceOpt.sMatchIPFilter:
                    if len(vMateUsers) > 0:
                        nFindIdx = info.sIPAddr.rfind(".")
                        if nFindIdx >= 0:
                            bOK = True
                            if ipcheck:
                                sStr = info.sIPAddr[0:nFindIdx]
                                for sMateUsr in vMateUsers:
                                    nIdx = sMateUsr.sIPAddr.rfind(".")
                                    if nIdx >= 0:
                                        if sStr == sMateUsr.sIPAddr[0:nIdx]:
                                            bOK = False
                            if not bOK:
                                continue
                vMateUsers.append(info)
            # 如果「配對率」> 0%，且匹配2~3人
            if ServiceOpt.sRobotRate > 0 and len(vMateUsers) >= 2:
                # 抽籤：「2~4位真人玩家成局」或「踢人，剩下1位真人玩家成局」
                draw_result = random.choices(population=['a','b'], weights=[100-int(ServiceOpt.sRobotRate), int(ServiceOpt.sRobotRate)], k=1)
                # 如果是2人
                if draw_result == ['b'] and len(vMateUsers) == 2:
                    del vMateUsers[-1]  # 把最後1個加入至暫時匹配區的玩家踢掉，剩1人留下
                # 如果是3人
                elif draw_result == ['b'] and len(vMateUsers) == 3:
                    del vMateUsers[-1]  # 把最後2個加入至暫時匹配區的玩家踢掉，剩1人留下
                    del vMateUsers[-1]  # 把最後2個加入至暫時匹配區的玩家踢掉，剩1人留下

        # 防止套利機制是否啟動
        if ServiceOpt.sPreventArbitrage == 1:
            # 分析彼此nickname是否過度相似
            if len(vMateUsers) >= 2:  # 至少有2位真人以上，才有比較意義
                for i in reversed(vMateUsers):
                    ans1 = i.pSvrUserItem.mUserInfo.mNickName  # 設定第一位比較的玩家
                    for j in reversed(vMateUsers):
                        if i != j:
                            ans2 = j.pSvrUserItem.mUserInfo.mNickName  # 設定第二位比較的玩家
                            # 比較兩位玩家名稱相似度超過82%
                            if SequenceMatcher(None, ans1, ans2).quick_ratio() >= 0.82:
                                vMateUsers.remove(j)  # 踢掉其中一位玩家至下一輪匹配
            # 分析是否有資歷0天內的玩家
            if len(vMateUsers) >= 2:  # 至少有2位真人以上，才有比較意義
                for k in reversed(vMateUsers):
                    # 如果資歷為0天不到的新玩家
                    if k.pSvrUserItem.mUserInfo.mCanMatchPlayer == 0:
                        vMateUsers.remove(k)  # 踢掉玩家至下一輪匹配
        return vMateUsers
