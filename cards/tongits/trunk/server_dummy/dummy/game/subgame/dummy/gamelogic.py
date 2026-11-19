
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(('%s/../..' % (os.getcwd())))
    sys.path.append(('%s/../../../../utils'%(os.getcwd())))

from copy import deepcopy
from utils import *
import time
import android
from itertools import permutations
from random import choice
from definations import *
import shelve
import math

class EnumPokerType(object):
    nClubs = 0
    nDiamonds = 1
    nHearts = 2
    nSpade = 3
    nJoker = 4
    nCount = 5

class EnumPokerPoint(object):
    nAce = 1
    nJack = 11
    nQueen = 12
    nKing = 13
    nSpecAce = 14

class EnumScoreBaseType(object):
    nNormal = 0
    nSpecial = 1
    nFinish = 2
    nOther = 3

class EnumFinishType(object):  # 遊戲結束時mt=2的st次分類項目
    nInHandRemain = 0  # 手牌剩餘
    nGroupRemain = 1  # 組牌剩餘
    nMessRemain = 2  # 雜牌剩餘

class EnumGameOperation(object):
    nAnnounce = 0x01
    nDraw = 0x02
    nPick = 0x04
    nCombine = 0x08
    nInsert = 0x10
    nDrop = 0x20
    # nNotOpenCanDummy = 0x40
    Group = 0x80
    UnGroup = 0x100
    Fight = 0x200
    Challenge = 0x400
    Fold = 0x800
    GroupReorganize = 0x2000

class EnumSpecEvent(object):
    nNormalWin1 = 0  # 自己得到基礎贏分
    nNormalWin2 = 1  # 別人得到基礎贏分
    nTongits1 = 2  # 自己胡牌
    nTongits2 = 3  # 別人胡牌了
    nSecretMelds1 = 4  # 自己有特殊組合
    nSecretMelds2 = 5  # 別人有特殊組合
    nSpecialCards1 = 6  # 自己有加分牌
    nSpecialCards2 = 7  # 別人有加分牌
    nBurned1 = 8  # 自己未開張
    nBurned2 = 9  # 別人未開張
    nFight1 = 10  # 自己發起比牌獲勝
    nFight2 = 11  # 自己發起比牌，但別人獲勝
    nChallenge1 = 12  # 自己接受比牌獲勝
    nChallenge2 = 13  # 自己接受比牌，但別人獲勝
    nFord1 = 14  # 自己放棄比牌
    nFord2 = 15  # 別人放棄比牌，但自己獲勝

class Poker(object):

    @classmethod
    def Index2TypePoint(cls, card_index):
        return (card_index >> 4) & 0x0f, card_index & 0x0f

    @classmethod
    def TypePoint2Index(cls, poker_type, poker_point):
        if poker_point == EnumPokerPoint.nSpecAce:
            poker_point = EnumPokerPoint.nAce
        return ((poker_type & 0x0f) << 4) | (poker_point & 0x0f)

    @classmethod
    def CheckRelatedTo(cls, card_index1, card_index2):
        if card_index1 == card_index2:
            return False
        poker_type1, poker_point1 = cls.Index2TypePoint(card_index1)
        poker_type2, poker_point2 = cls.Index2TypePoint(card_index2)
        if poker_point1 == EnumPokerPoint.nAce:
            poker_point1 = EnumPokerPoint.nSpecAce
        if poker_point2 == EnumPokerPoint.nAce:
            poker_point2 = EnumPokerPoint.nSpecAce
        if poker_point1 == poker_point2:
            return True
        if poker_type1 == poker_type2:
            if poker_point2 > poker_point1:
                if poker_point2 - poker_point1 < 3:
                    return True
                else:
                    return False
            else:
                if poker_point1 - poker_point2 < 3:
                    return True
                else:
                    return False
        return False

    def __init__(self, poker_type, poker_point):
        poker_type = int(poker_type)
        poker_point = int(poker_point)
        self.nType = poker_type
        self.nPoint = poker_point
        self.nIndex = Poker.TypePoint2Index(poker_type, poker_point)

    def __repr__(self):
        return str(self.__dict__)

    @property
    def Type(self):
        return self.nType

    @property
    def Point(self):
        return self.nPoint

    @property
    def Index(self):
        return self.nIndex

class LogicConfig(object):
    nTotalSeats = 3  # 3人局
    nMinPlayers2Start = 3
    mStartCardsNumConfig = {}
    mPokers = {}
    vPokerOrder = []
    mPokerIndex2Score = {}
    mEventID2Score = {}
    nMinContinuity = 3
    nMaxContinuity = 5

    @classmethod
    def Preview(cls):
        Info("Configs>>>>")
        Info("nTotalSeats", cls.nTotalSeats)
        Info("nMinPlayers2Start", cls.nMinPlayers2Start)
        Info("mStartCardsNumConfig", cls.mStartCardsNumConfig)
        Info("mPokers", cls.mPokers)
        Info("vPokerOrder", cls.vPokerOrder)
        Info("mPokerIndex2Score", cls.mPokerIndex2Score)
        Info("mEventID2Score", cls.mEventID2Score)
        Info("nMinContinuity", cls.nMinContinuity)
        Info("nMaxContinuity", cls.nMaxContinuity)
        Info("<<<<")

    @classmethod
    def Reset2Default(cls):
        cls.nTotalSeats = 3  # 3人局
        cls.nMinPlayers2Start = 3
        cls.mStartCardsNumConfig = {
            3: 12
        }  # 起始3人: 起手12張牌
        cls.mPokers = {}
        cls.vPokerOrder = []
        cls.mPokerIndex2Score = {}

        for i in range(4):  # 4個花色
            for j in range(13):  # 每個花色13張牌
                poker = Poker(i, j + 1)
                cls.mPokers[poker.Index] = poker
                cls.vPokerOrder.append(poker.Index)
                if poker.Index != 0x02 and poker.Index != 0x3c:
                    if poker.Point == 1:
                        cls.mPokerIndex2Score[poker.Index] = [0, 0]
                    elif poker.Point < 10:
                        cls.mPokerIndex2Score[poker.Index] = [0, 0]
                    else:
                        cls.mPokerIndex2Score[poker.Index] = [0, 0]
                else:
                    cls.mPokerIndex2Score[poker.Index] = [0, 0]

        cls.mEventID2Score = {
            EnumSpecEvent.nNormalWin1: 2,
            EnumSpecEvent.nNormalWin2: -1,
            EnumSpecEvent.nTongits1: 2,
            EnumSpecEvent.nTongits2: -1,
            EnumSpecEvent.nSecretMelds1: 2,
            EnumSpecEvent.nSecretMelds2: -1,
            EnumSpecEvent.nSpecialCards1: 2,
            EnumSpecEvent.nSpecialCards2: -1,
            EnumSpecEvent.nBurned1: -1,
            EnumSpecEvent.nBurned2: 1,
            EnumSpecEvent.nFight1: 2,
            EnumSpecEvent.nFight2: -2,
            EnumSpecEvent.nChallenge1: 2,
            EnumSpecEvent.nChallenge2: -2,
            EnumSpecEvent.nFord1: -1,
            EnumSpecEvent.nFord2: 1,
        }

        cls.nMinContinuity = 3
        cls.nMaxContinuity = 5

    @classmethod
    def CardSymbolCovertor(cls, data):
        try:
            tmp = {}
            for card_index in data:
                card_index = int(card_index)
                if card_index == 0 or card_index == 16:
                    continue
                #--------------------
                tmp[card_index] = 1
                # 牌值转换
                #t, p = Poker.Index2TypePoint(card_index)
                #if t == 0:
                #    t = 1
                #elif t == 1:
                #    t = 0
                #new_card_index = Poker.TypePoint2Index(t, p)
                #if new_card_index not in cls.mPokers:
                #    Err("Invalid card index:", new_card_index, card_index, data)
                #    return None
                #tmp[new_card_index] = 1

            if len(tmp) != len(cls.mPokers):
                Err("Count of cards not matched!", tmp)
                return None

            return list(tmp.keys())
        except:
            PrintEXC()
            return None

class CardInfo(object):
    def __init__(self, poker_obj, owner = None):
        self.xPoker = poker_obj
        self.xOwner = owner
        self.vDropOrder = []
        self.xFinalOwner = None
        score_cfg = LogicConfig.mPokerIndex2Score[poker_obj.Index]
        self.nScore4Gain = score_cfg[0]
        self.nScore4Lose = -score_cfg[1]

    def __repr__(self):
        return str(self.__dict__)

    @property
    def Poker(self):
        return self.xPoker

    @property
    def Owner(self):
        return self.xOwner

    @property
    def DropOrder(self):
        return self.vDropOrder

    @property
    def FinalOwner(self):
        return self.xFinalOwner

    @property
    def Score4Gain(self):
        return self.nScore4Gain

    @property
    def Score4Lose(self):
        return self.nScore4Lose

    def SetOwner(self, owner):
        self.xOwner = owner

    def SetFinalOwner(self, owner):
        self.xFinalOwner = owner

    def Dropped(self, who, is_opened):
        self.vDropOrder.append((who, is_opened))

class CardSerializer(object):
    def __init__(self):
        self.vSerials = [0 for i in range(EnumPokerType.nJoker)]

    def Clear(self):
        self.vSerials = [0 for i in range(EnumPokerType.nJoker)]

    def Copy(self):
        card_serial = CardSerializer()
        card_serial.vSerials = deepcopy(self.vSerials)
        return card_serial

    def Add(self, card_index):
        poker_type, poker_point = Poker.Index2TypePoint(card_index)
        self.vSerials[poker_type] |= 1 << poker_point

    def AddBatch(self, card_index_list):
        for card_index in card_index_list:
            poker_type, poker_point = Poker.Index2TypePoint(card_index)
            self.vSerials[poker_type] |= 1 << poker_point

    def CheckCondition(self, combo, include_card = None, match_one = None, remain_one = None): # include_card -> card_index, match_one -> { card_index : CardInfo }, remain_one -> { card_index : CardInfo }
        if include_card is not None:
            if include_card not in combo:
                return False

        if match_one is not None:
            matched = False
            for card_index in combo:
                if card_index in match_one:
                    matched = True
                    break
            if not matched:
                return False

        if remain_one is not None:
            match_cnt = 0
            for card_index in combo:
                if card_index in remain_one:
                    match_cnt += 1
            if match_cnt == len(remain_one):
                for card_index in combo:
                    if not card_index in remain_one:
                        return False

        return True

    def GetAllCombo(self, include_card = None, match_one = None, remain_one = None): # include_card -> card_index, match_one -> { card_index : CardInfo }, remain_one -> { card_index : CardInfo }

        # A' K Q J 10 9 8 7 6 5 4 3 2 A ?
        # ex: 24572
        # 1  0 1 1  1 1 1 1 1 1 1 1 1 1 0
        # ex: 32764
        # 1  1 1 1  1 1 1 1 1 1 1 1 1 0 0

        combos = []
        dia_serial = self.vSerials[EnumPokerType.nDiamonds]
        clu_serial = self.vSerials[EnumPokerType.nClubs]
        hea_serial = self.vSerials[EnumPokerType.nHearts]
        spa_serial = self.vSerials[EnumPokerType.nSpade]

        # check [3] same point
        mix_serial = (dia_serial ^ clu_serial) & (hea_serial & spa_serial)
        if mix_serial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                tmp_serial = mix_serial >> point
                if (tmp_serial & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                    point_bit_pos = 1 << point
                    if (dia_serial & point_bit_pos) != 0:
                        combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    else:
                        combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1

                    if self.CheckCondition(combo, include_card, match_one, remain_one):
                        combos.append(combo)
                point += 1

        mix_serial = (dia_serial & clu_serial) & (hea_serial ^ spa_serial)
        if mix_serial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                tmp_serial = mix_serial >> point
                if (tmp_serial & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    point_bit_pos = 1 << point
                    if (hea_serial & point_bit_pos) != 0:
                        combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    else:
                        combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1

                    if self.CheckCondition(combo, include_card, match_one, remain_one):
                        combos.append(combo)
                point += 1

        # check [4] same point
        mix_serial = (dia_serial & clu_serial) & (hea_serial & spa_serial)
        if mix_serial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                tmp_serial = mix_serial >> point
                if (tmp_serial & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1

                    if self.CheckCondition(combo, include_card, match_one, remain_one):
                        combos.append(combo)
                point += 1

        if dia_serial != 0:
            point = 1
            combo = {}
            for i in range(EnumPokerPoint.nKing):
                tmp_serial = dia_serial >> point
                if (tmp_serial & 0x0001) == 1:
                    combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                else:
                    if len(combo) >= LogicConfig.nMinContinuity:
                        if self.CheckCondition(combo, include_card, match_one, remain_one):
                            combos.append(combo)
                    combo = {}
                point += 1
            if len(combo) >= LogicConfig.nMinContinuity:
                if self.CheckCondition(combo, include_card, match_one, remain_one):
                    combos.append(combo)

        if clu_serial != 0:
            point = 1
            combo = {}
            for i in range(EnumPokerPoint.nKing):
                tmp_serial = clu_serial >> point
                if (tmp_serial & 0x0001) == 1:
                    combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                else:
                    if len(combo) >= LogicConfig.nMinContinuity:
                        if self.CheckCondition(combo, include_card, match_one, remain_one):
                            combos.append(combo)
                    combo = {}
                point += 1
            if len(combo) >= LogicConfig.nMinContinuity:
                if self.CheckCondition(combo, include_card, match_one, remain_one):
                    combos.append(combo)

        if hea_serial != 0:
            point = 1
            combo = {}
            for i in range(EnumPokerPoint.nKing):
                tmp_serial = hea_serial >> point
                if (tmp_serial & 0x0001) == 1:
                    combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                else:
                    if len(combo) >= LogicConfig.nMinContinuity:
                        if self.CheckCondition(combo, include_card, match_one, remain_one):
                            combos.append(combo)
                    combo = {}
                point += 1
            if len(combo) >= LogicConfig.nMinContinuity:
                if self.CheckCondition(combo, include_card, match_one, remain_one):
                    combos.append(combo)

        if spa_serial != 0:
            point = 1
            combo = {}
            for i in range(EnumPokerPoint.nKing):
                tmp_serial = spa_serial >> point
                if (tmp_serial & 0x0001) == 1:
                    combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                else:
                    if len(combo) >= LogicConfig.nMinContinuity:
                        if self.CheckCondition(combo, include_card, match_one, remain_one):
                            combos.append(combo)
                    combo = {}
                point += 1
            if len(combo) >= LogicConfig.nMinContinuity:
                if self.CheckCondition(combo, include_card, match_one, remain_one):
                    combos.append(combo)
        return combos

    def HasFullMatch(self, combine):
        combos = self.GetAllCombo()
        for combo in combos:
            if len(combo) == len(combine):
                all_matched = True
                for cb_card_index in combine:
                    if cb_card_index not in combo:
                        all_matched = False
                        break
                if all_matched:
                    return True
        return False

    def GetAllComboByFixOne(self, fix_one):
        poker_type, poker_point = Poker.Index2TypePoint(fix_one)
        self.vSerials[poker_type] |= 1 << poker_point
        combos = self.GetAllCombo(fix_one)
        self.vSerials[poker_type] ^= 1 << poker_point
        return combos

    #无影响的牌:无法组搭&听搭
    def GetNotEffect(self):
        for st in range(EnumPokerType.nJoker):
            serial = self.vSerials[st]
            ace_bit_pos = 1 << EnumPokerPoint.nAce
            if (serial & ace_bit_pos) != 0:
                self.vSerials[st] = serial ^ ace_bit_pos | (1 << EnumPokerPoint.nSpecAce)

        mNoEffIdxs = {}
        point = 2
        for sp in range(EnumPokerPoint.nKing):
            ok = True
            for st in range(EnumPokerType.nJoker):
                serial = self.vSerials[st]
                tmp_serial = serial >> point
                if (tmp_serial & 0x0001) == 1:
                    ok = False
                    break
            if ok:
                for st in range(EnumPokerType.nJoker):
                    serial = self.vSerials[st]
                    if ((serial >> (point-1)) & 0x0001 == 0) and ((serial >> (point-2)) & 0x0001 == 0) \
                            and ((serial >> (point+1)) & 0x0001 == 0) and ((serial >> (point+2)) & 0x0001 == 0):
                        mNoEffIdxs[Poker.TypePoint2Index(st, point)] = 1
            point += 1
        return mNoEffIdxs

    def Remove(self, idx):
        if isinstance(idx, int):
            st, p = Poker.Index2TypePoint(idx)
            self.vSerials[st] ^= 1 << p
        elif isinstance(idx, dict):
            for i in list(idx.keys()):
                st, p = Poker.Index2TypePoint(i)
                self.vSerials[st] ^= 1 << p
        elif isinstance(idx, list):
            for i in idx:
                st, p = Poker.Index2TypePoint(i)
                self.vSerials[st] ^= 1 << p

    #获取组合(先顺后条),返回组合 以及 剩下的牌
    def GetCombosPriorityShunZi(self):
        combos = []
        acebitpos = 1 << EnumPokerPoint.nAce
        spec_acebitpos = 1 << EnumPokerPoint.nSpecAce
        #扫描顺子
        for st in range(EnumPokerType.nJoker):
            serial = self.vSerials[st]
            if serial != 0:
                if (serial & acebitpos) != 0:
                    serial = serial ^ acebitpos | spec_acebitpos
                point = 2
                combo = {}
                for i in range(EnumPokerPoint.nKing):
                    if ((serial >> point) & 0x0001) == 1:
                        combo[Poker.TypePoint2Index(st, point)] = 1
                    else:
                        if len(combo) >= LogicConfig.nMinContinuity:
                            combos.append(combo)
                            self.Remove(combo)
                        combo = {}
                    point += 1
                if len(combo) >= LogicConfig.nMinContinuity:
                    combos.append(combo)
                    self.Remove(combo)

        mixserial = (self.vSerials[EnumPokerType.nDiamonds] ^ self.vSerials[EnumPokerType.nClubs]) \
                     & (self.vSerials[EnumPokerType.nHearts] & self.vSerials[EnumPokerType.nSpade])
        if mixserial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                if ((mixserial >> point) & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                    bit_pos = 1 << point
                    if (self.vSerials[EnumPokerType.nDiamonds] & bit_pos) != 0:
                        combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    else:
                        combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    combos.append(combo)
                    self.Remove(combo)
                point += 1

        mixserial = (self.vSerials[EnumPokerType.nDiamonds] & self.vSerials[EnumPokerType.nClubs]) \
                     & (self.vSerials[EnumPokerType.nHearts] ^ self.vSerials[EnumPokerType.nSpade])
        if mixserial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                if ((mixserial >> point) & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    bit_pos = 1 << point
                    if (self.vSerials[EnumPokerType.nHearts] & bit_pos) != 0:
                        combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    else:
                        combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                    combos.append(combo)
                    self.Remove(combo)
                point += 1

        mixserial = (self.vSerials[EnumPokerType.nDiamonds] & self.vSerials[EnumPokerType.nClubs]) \
                     & (self.vSerials[EnumPokerType.nHearts] & self.vSerials[EnumPokerType.nSpade])
        if mixserial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                if ((mixserial >> point) & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                    combos.append(combo)
                    self.Remove(combo)
                point += 1

        #剩下的牌
        nocombo = {}
        for st in range(EnumPokerType.nJoker):
            serial = self.vSerials[st]
            if serial > 0:
                point = 1
                for i in range(EnumPokerPoint.nKing):
                    if ((serial >> point) & 0x0001) == 1:
                        nocombo[Poker.TypePoint2Index(st, point)] = 1
                    point += 1
        return combos, nocombo

    #获取组合(先条后顺),返回组合 以及 剩下的牌
    def GetCombosPriorityTiaoZi(self):
        combos = []

        mixserial = (self.vSerials[EnumPokerType.nDiamonds] ^ self.vSerials[EnumPokerType.nClubs]) \
                     & (self.vSerials[EnumPokerType.nHearts] & self.vSerials[EnumPokerType.nSpade])
        if mixserial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                if ((mixserial >> point) & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                    bit_pos = 1 << point
                    if (self.vSerials[EnumPokerType.nDiamonds] & bit_pos) != 0:
                        combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    else:
                        combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    combos.append(combo)
                    self.Remove(combo)
                point += 1

        mixserial = (self.vSerials[EnumPokerType.nDiamonds] & self.vSerials[EnumPokerType.nClubs]) \
                     & (self.vSerials[EnumPokerType.nHearts] ^ self.vSerials[EnumPokerType.nSpade])
        if mixserial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                if ((mixserial >> point) & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    bit_pos = 1 << point
                    if (self.vSerials[EnumPokerType.nHearts] & bit_pos) != 0:
                        combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    else:
                        combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                    combos.append(combo)
                    self.Remove(combo)
                point += 1

        mixserial = (self.vSerials[EnumPokerType.nDiamonds] & self.vSerials[EnumPokerType.nClubs]) \
                     & (self.vSerials[EnumPokerType.nHearts] & self.vSerials[EnumPokerType.nSpade])
        if mixserial != 0:
            point = 1
            for i in range(EnumPokerPoint.nKing):
                if ((mixserial >> point) & 0x0001) == 1:
                    combo = {}
                    combo[Poker.TypePoint2Index(EnumPokerType.nDiamonds, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nClubs, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nHearts, point)] = 1
                    combo[Poker.TypePoint2Index(EnumPokerType.nSpade, point)] = 1
                    combos.append(combo)
                    self.Remove(combo)
                point += 1

        acebitpos = 1 << EnumPokerPoint.nAce
        spec_acebitpos = 1 << EnumPokerPoint.nSpecAce
        #扫描顺子
        for st in range(EnumPokerType.nJoker):
            serial = self.vSerials[st]
            if serial != 0:
                if (serial & acebitpos) != 0:
                    serial = serial ^ acebitpos | spec_acebitpos
                point = 2
                combo = {}
                for i in range(EnumPokerPoint.nKing):
                    if ((serial >> point) & 0x0001) == 1:
                        combo[Poker.TypePoint2Index(st, point)] = 1
                    else:
                        if len(combo) >= LogicConfig.nMinContinuity:
                            combos.append(combo)
                            self.Remove(combo)
                        combo = {}
                    point += 1
                if len(combo) >= LogicConfig.nMinContinuity:
                    combos.append(combo)
                    self.Remove(combo)

        #剩下的牌
        nocombo = {}
        for st in range(EnumPokerType.nJoker):
            serial = self.vSerials[st]
            if serial > 0:
                point = 1
                for i in range(EnumPokerPoint.nKing):
                    if ((serial >> point) & 0x0001) == 1:
                        nocombo[Poker.TypePoint2Index(st, point)] = 1
                    point += 1
        return combos, nocombo

class PlayerInfo(object):
    def __init__(self, seat_index):
        self.nSeatIndex = seat_index
        self.bIsJoined = False
        self.mInHand = {}  # card_index : CardInfo
        self.mCombos = {}  # combo_index : { card_index : CardInfo }
        self.group_combination = []  # [{card_index : CardInfo, ..., ...}, ...]
        self.vScoreRecords = []  # [(main_type, sub_type, score)...]
        self.nNewRecordCursor = -1
        self.xPickedFinal = None
        self.nPickedFirstType = -1
        self.nComboCount = 0  # 出牌+撿牌次數累積
        self.nComboSheetsAmounts = 0  # 出牌+插牌+撿牌張數累積
        self.nTurnCount = 0
        self.nTurnWhenOpen = 0
        self.nGainedScore = 0
        self.nLostScore = 0
        self.nOpAllow = 0
        self.open_time = 2000000000  # 開張的時間
        self.nTurnFirstOp = 0
        self.bIsAnnounced = False
        self.bIsOpened = False
        self.bAllSameType = False
        # self.nNotOpenCanDummy = None  # 未開張一次清空內容[[],[],[],[]]
        # self.continueNotOpenCanDummy = True  # 是否持續操作未開張一次清空
        self.gamelogic_android_round = False  # 是否為機器人的回合
        # self.detain_could_be_inserted = True  # 機器人扣留可能被接金牌的牌
        # self.android_pick_combine_insert_drop = None  # 機器人未開張一次清空組合
        # self.event_accumulation = 0  # 單人單局「棄牌組搭」「協助金牌」「棄掉可插」的累積次數
        self.auto_operate = 0  # 上次操作是否由系統自動操作，預設 0
        self.water_balloon = 0  # 每局獲得的水球數
        self.odd_turn_inserted_mark = 0  # 單雙數回合是否被插牌
        self.even_turn_inserted_mark = 0  # 單雙數回合是否被插牌
        self.fight_status = 0  # 比牌中的狀態，用 EnumGameOperation 的值表示
        self.add_point_event = 0  # 「加分牌」事件累計
        self.compare_point = 0  # 比牌點數
        self.consume_point = 0  # 消耗比牌點數
        self.drop_first_min_card = 13  # 棄掉最小牌的比牌點數
        self.drop_second_min_card = 13  # 棄掉最2小的牌的比牌點數
        self.op_allow_fight = 2  # 用來告示前端目前這位玩家是否允許發起比牌: 0不允許1允許2不允許但不被插刀子
        self.has_drawed_or_picked = False  # 輪到自己回合時，抽過或撿過牌了嗎？

    def __repr__(self):
        return str(self.__dict__)

    def __lt__(self, other):
        return self.GetTotalScore() < other.GetTotalScore()

    @property
    def SeatIndex(self):
        return self.nSeatIndex

    @property
    def IsJoined(self):
        return self.bIsJoined

    @property
    def InHand(self):
        return self.mInHand

    @property
    def Combos(self):
        return self.mCombos

    @property
    def ScoreRecords(self):
        return self.vScoreRecords

    @property
    def PickedFinal(self):
        return self.xPickedFinal

    @property
    def ComboCount(self):
        return self.nComboCount

    @property
    def TurnCount(self):
        return self.nTurnCount

    @property
    def TurnWhenOpen(self):
        return self.nTurnWhenOpen

    @property
    def GainedScore(self):
        return self.nGainedScore

    @property
    def LostScore(self):
        return self.nLostScore

    @property
    def OpAllow(self):
        return self.nOpAllow

    @property
    def TurnFirstOp(self):
        return self.nTurnFirstOp

    @property
    def IsAnnounced(self):
        return self.bIsAnnounced

    @property
    def IsOpened(self):
        return self.bIsOpened

    @property
    def AllSameType(self):
        return self.bAllSameType

    # @property
    # def NotOpenCanDummy(self):
    #     return self.nNotOpenCanDummy

    # @property
    # def EventAccumulation(self):
    #     return self.event_accumulation

    @property
    def WaterBalloon(self):
        return self.water_balloon

    def JoinIn(self):
        self.bIsJoined = True

    def Leave(self):
        self.bIsJoined = False

    def ProcNormalScore(self, op_type, card_info_list):
        total_gained = 0
        tmp = []
        for card_info in card_info_list:
            # self.nGainedScore += card_info.nScore4Gain
            # total_gained += card_info.nScore4Gain
            tmp.append(card_info.Poker.Index)
        # if total_gained == 0:
        #     return

        # 普通加減+0沒分，只是雲端拿來記錄撿牌出牌狀況
        self.vScoreRecords.append((EnumScoreBaseType.nNormal, op_type, tmp, 0))
        if self.nNewRecordCursor == -1:
            self.nNewRecordCursor = len(self.vScoreRecords) - 1

    def ProcEventScore(self, event_id):
        sc = LogicConfig.mEventID2Score[event_id]
        if sc > 0:
            self.nGainedScore += sc
        else:
            self.nLostScore -= sc
        self.vScoreRecords.append((EnumScoreBaseType.nSpecial, event_id, sc))
        if self.nNewRecordCursor == -1:
            self.nNewRecordCursor = len(self.vScoreRecords) - 1

    def ProcEndScore(self):
        total_lost = 0
        # for card_info in self.mInHand.values():
        #     self.nLostScore += card_info.nScore4Lose
        #     total_lost -= card_info.nScore4Lose
        # if total_lost == 0:
        #     return

        # 結束加減+0沒分，只是雲端拿來記錄手牌剩餘，mt=2；st=0
        self.vScoreRecords.append((EnumScoreBaseType.nFinish, list(self.mInHand.keys()), 0,
                                   EnumFinishType.nInHandRemain))
        # 承上，記錄組牌剩餘，mt=2；st=1
        group_index_list = []
        for group in self.group_combination:
            for card_index in group:
                group_index_list.append(card_index)
        self.vScoreRecords.append((EnumScoreBaseType.nFinish, group_index_list, 0, EnumFinishType.nGroupRemain))
        # 承上，記錄雜牌剩餘，雜牌 = 手牌 - 組牌，mt=2；st=2
        mess_index_list = []
        for i in list(self.mInHand.keys()):
            if i not in group_index_list:
                mess_index_list.append(i)
        self.vScoreRecords.append((EnumScoreBaseType.nFinish, mess_index_list, 0, EnumFinishType.nMessRemain))

        if self.nNewRecordCursor == -1:
            self.nNewRecordCursor = len(self.vScoreRecords) - 1

    def GetScoreRecordsAndFlush(self):
        if self.nNewRecordCursor != -1:
            tmp = self.vScoreRecords[self.nNewRecordCursor:]
            self.nNewRecordCursor = -1
            return tmp
        else:
            return None

    def NewRound(self):
        if self.bIsJoined:
            self.mInHand = {}
            self.mCombos = {}
            self.group_combination = []  # 組牌區
            self.vScoreRecords = []
            self.nNewRecordCursor = -1
            self.xPickedFinal = None
            self.nPickedFirstType = -1
            self.nComboCount = 0  # 出牌+撿牌次數累積
            self.nComboSheetsAmounts = 0  # 出牌+插牌+撿牌張數累積
            self.nTurnCount = 0
            self.nTurnWhenOpen = 0
            self.nGainedScore = 0
            self.nLostScore = 0
            self.nOpAllow = 0
            self.open_time = 2000000000  # 開張的時間
            self.nTurnFirstOp = 0
            self.bIsAnnounced = False
            self.bIsOpened = False
            self.bAllSameType = True
            # self.nNotOpenCanDummy = None  # 未開張一次清空內容[[],[],[],[]]
            # self.continueNotOpenCanDummy = True  # 是否持續操作未開張一次清空
            self.gamelogic_android_round = False  # 是否為機器人的回合
            # self.detain_could_be_inserted = True  # 機器人扣留可能被接金牌的牌
            # self.android_pick_combine_insert_drop = None  # 機器人未開張一次清空組合
            # self.event_accumulation = 0  # 單人單局「棄牌組搭」「協助金牌」「棄掉可插」的累積次數
            self.auto_operate = 0  # 上次操作是否由系統自動操作，預設0
            self.water_balloon = 0  # 每局獲得的水球數
            self.odd_turn_inserted_mark = 0  # 單雙數回合是否被插牌
            self.even_turn_inserted_mark = 0  # 單雙數回合是否被插牌
            self.fight_status = 0  # 比牌中的狀態，用 EnumGameOperation 的值表示
            self.add_point_event = 0  # 「加分牌」事件累計
            self.compare_point = 0  # 比牌點數
            self.consume_point = 0  # 消耗比牌點數
            self.drop_first_min_card = 13  # 棄掉最小牌的比牌點數
            self.drop_second_min_card = 13  # 棄掉最2小的牌的比牌點數
            self.op_allow_fight = 2  # 用來告示前端目前這位玩家是否允許發起比牌: 0不允許1允許2不允許但不被插刀子
            self.has_drawed_or_picked = False  # 輪到自己回合時，抽過或撿過牌了嗎？

            return True
        return False

    def RoundEnd(self, tmp_other_1, tmp_other_2, winner_info, finish_cond):
        self.ProcEndScore()  # 就算結算沒分，也要記錄手牌狀況供雲端查詢
        if winner_info == self:
            self.ProcEventScore(EnumSpecEvent.nNormalWin1)  # 基礎贏分
            tmp_other_1.ProcEventScore(EnumSpecEvent.nNormalWin2)
            tmp_other_2.ProcEventScore(EnumSpecEvent.nNormalWin2)

            for i in range(self.add_point_event):  # 贏的人是否有加分事件
                self.ProcEventScore(EnumSpecEvent.nSpecialCards1)
                tmp_other_1.ProcEventScore(EnumSpecEvent.nSpecialCards2)
                tmp_other_2.ProcEventScore(EnumSpecEvent.nSpecialCards2)

            if finish_cond == 1 or finish_cond == 4:
                # 遊戲達成tongits(手牌清空或雜牌清空)
                self.ProcEventScore(EnumSpecEvent.nTongits1)
                tmp_other_1.ProcEventScore(EnumSpecEvent.nTongits2)
                tmp_other_2.ProcEventScore(EnumSpecEvent.nTongits2)

        if self.has_special_combine() and self.has_special_combine() > 0:  # 計算是否有特殊組合
            for _ in range(self.has_special_combine()):  # 走訪有多少種特殊組合的牌
                self.ProcEventScore(EnumSpecEvent.nSecretMelds1)  # 手牌特殊組合加分
                tmp_other_1.ProcEventScore(EnumSpecEvent.nSecretMelds2)  # 其他人發現別人有特殊組合扣分
                tmp_other_2.ProcEventScore(EnumSpecEvent.nSecretMelds2)  # 其他人發現別人有特殊組合扣分

        if not self.bIsOpened:  # 是否有開張
            self.ProcEventScore(EnumSpecEvent.nBurned1)  # 未開張要付給贏家
            winner_info.ProcEventScore(EnumSpecEvent.nBurned2)

    def GetTotalScore(self):
        return self.nGainedScore - self.nLostScore

    def CombineAllowed(self):
        if len(self.mInHand) > 1:
            card_serial = CardSerializer()
            card_serial.AddBatch(list(self.mInHand.keys()))
            combos = card_serial.GetAllCombo(remain_one=self.mInHand)

            if len(combos) > 0 and len(self.mInHand) >= LogicConfig.nMinContinuity:
                self.nOpAllow |= EnumGameOperation.nCombine

    def IsOpAllowed(self, op_type):
        if op_type == EnumGameOperation.nCombine:
            self.CombineAllowed()
        elif op_type == EnumGameOperation.Group:  # 允許組牌
            self.nOpAllow |= EnumGameOperation.Group
        elif op_type == EnumGameOperation.UnGroup:  # 允許解散組牌
            self.nOpAllow |= EnumGameOperation.UnGroup
        elif op_type == EnumGameOperation.GroupReorganize:  # 整牌鍵自動組牌非自己回合也要能組
            self.nOpAllow |= EnumGameOperation.GroupReorganize
        return (self.nOpAllow & op_type) != 0

    # # 是否扣留可能被接金牌的組合
    # def detain_could_be_inserted(self):
    #     return self.detain_could_be_inserted

    def _get_all_possible_combo_list(self, combos):
        new_combos = []

        for combo in combos:
            new_combos.append([k for k in combo.keys()])

        # 將所有排列組合列出，並將 [{...}, ...] 轉換成 [[...], ...]
        all_new_combos = [list(deepcopy(p)) for p in
                          permutations(new_combos, len(new_combos))]

        return all_new_combos

    def _remove_duplicate_card(self, all_new_combos):
        """刪除重複的牌

        一副牌多種組合，但一張牌不能重複使用，所以刪除掉

        Args:
            all_new_combos: 所有可能的組合
                examples: [
                        [[1, 2, 3], [4, 5, 6]],
                        [[1, 2, 3], [3, 19, 35]],
                        ...
                    ]
        """
        for combos in all_new_combos:
            cal_repeat = []  # 計數重複用

            for combo in combos:
                for card in reversed(combo):  # 用 reversed 避免影響 index
                    if card not in cal_repeat:
                        cal_repeat.append(card)
                    else:
                        combo.remove(card)

    # def _remove_not_combo_card(self, all_new_combos):
    #     """刪除不符合組合的牌
    #
    #     因為上一個步驟是刪除掉重複的牌，所以可能會導致原本可以是組合的牌變成不是組合
    #
    #     Args:
    #         all_new_combos: 所有可能的組合
    #             examples: [
    #                     [[1, 2, 3], [4, 5, 6]],
    #                     [[1, 2, 3], [3, 19, 35]],
    #                     ...
    #                 ]
    #     """
    #     for combos in all_new_combos:
    #         # 刪除 4 張以上不符合組合的牌
    #         for combo in combos:
    #             is_4_of_a_kind = abs(combo[0] - combo[1]) % 16 == 0
    #             if len(combo) <= 3 or is_4_of_a_kind:
    #                 continue
    #
    #             combines = []  # 新增臨時判斷是組合的所有牌
    #             for count in range(1, len(combo) - 1):  # 走訪每一張牌
    #                 # 如果自己張與前一張與後一張可成為組合
    #                 curr_num = combo[count]
    #                 next_num = combo[count + 1]
    #                 pre_num = combo[count - 1]
    #                 is_next = abs(next_num - curr_num) == 1
    #                 is_previous = abs(curr_num - pre_num) == 1
    #                 if not is_next or not is_previous:
    #                     continue
    #                 for temp in [pre_num, curr_num, next_num]:
    #                     if temp not in combines:
    #                         combines.append((temp))
    #             for card in reversed(combo):
    #                 if card not in combines:  # 查詢不是組合的牌
    #                     combo.remove(card)  # 不是組合的牌刪除
    #         # 刪除 3 張以下不符合組合的牌
    #         for combo in reversed(combos):
    #             if len(combo) < 3:
    #                 combos.remove(combo)
    #             # 組合張數剛好 3 張(上一個迴圈功能已經把不合理的 4 張以上組合淘汰了)
    #             elif len(combo) == 3:
    #                 for count in range(len(combo) - 1):  # 走訪這3張的組合
    #                     if (combo[count + 1] - combo[count]) in (2, 3, 10, 11):
    #                         combos.remove(combo)  # 刪除不合理的組合
    #                         break

    # def _get_pairs_card_list(self, from_combine_to_drop_s):
    #     pairscard = []  # 2張連續順子聽搭
    #
    #     for j in range(len(from_combine_to_drop_s)):
    #         # 避免index out of range
    #         if j + 1 == len(from_combine_to_drop_s):
    #             continue
    #
    #         tmp_card_index = from_combine_to_drop_s[j]
    #         tmp_ndex_card_index = from_combine_to_drop_s[j + 1]
    #
    #         if tmp_card_index + 1 == tmp_ndex_card_index:
    #             # 將後面一張牌加入為連續順子聽搭
    #             pairscard.append([tmp_card_index, tmp_ndex_card_index])
    #
    #     return pairscard

    # def CheckNotOpenCanDummy(self, all_insert_combos):  # 未開張一次清空
    #     card_serial = CardSerializer()
    #     card_serial.AddBatch(list(self.mInHand.keys()))
    #
    #     all_new_combos = []  # 新增用來加入所有排列組合的牌型
    #     combos = card_serial.GetAllCombo(remain_one=self.mInHand)
    #
    #     if len(combos) > 0:
    #         all_new_combos = self._get_all_possible_combo_list(combos)
    #
    #         self._remove_duplicate_card(all_new_combos)
    #         self._remove_not_combo_card(all_new_combos)
    #
    #     if all_new_combos != []:
    #         from_combine_to_combine = []  # 3維：預知出牌階段結束後，所有出牌組合牌型
    #         from_combine_to_drop = []  # 2維：預知出牌階段結束後，所有組合牌型剩餘的牌
    #
    #         # 走訪所有組合牌型的第N個組合牌型
    #         for combos in all_new_combos:
    #             # 建立並複製一個手牌index的清單，作為「預知手牌」
    #             mInHand_copy = [i for i in self.mInHand.keys()]
    #
    #             # [[], [[出牌組合1, 出牌組合2]], [], []]
    #             pick_combine_insert_drop = [[], [], [], []]
    #
    #             # 檢查手中的牌組組合，放到出牌組合中，從手牌中移除
    #             for combo in combos:  # 開始走訪每一種組合
    #                 for _card_index in combo:
    #                     mInHand_copy.remove(_card_index)
    #
    #                 if len(combo) in (3, 4, 5):
    #                     pick_combine_insert_drop[1].append(combo)
    #
    #                 elif len(combo) in (6, 7, 8, 9, 10):
    #                     combo_index = len(combo) // 2
    #                     pick_combine_insert_drop[1].append(combo[:combo_index])
    #                     pick_combine_insert_drop[1].append(combo[combo_index:])
    #
    #                 elif len(combo) in (11, 12, 13):
    #                     pick_combine_insert_drop[1].append(combo[:4])
    #                     pick_combine_insert_drop[1].append(combo[4:8])
    #                     pick_combine_insert_drop[1].append(combo[8:])
    #
    #             if len(mInHand_copy) == 1:  # 手牌剩下一張，就當作棄牌
    #                 pick_combine_insert_drop[3].append(mInHand_copy[0])
    #                 mInHand_copy = []
    #
    #             # 如果在預知出牌階段就已經全出完
    #             if len(mInHand_copy) == 0:
    #                 Log("未開張一次清空={}".format(pick_combine_insert_drop))
    #                 self.android_pick_combine_insert_drop = pick_combine_insert_drop
    #                 return pick_combine_insert_drop
    #
    #             mInHand_copy = sorted(mInHand_copy)
    #             # 如果預知手牌曾在上一次迴圈留下一樣的棄牌結果，就不用讓插牌階段再跑一次
    #             if mInHand_copy not in from_combine_to_drop:
    #                 from_combine_to_drop.append(mInHand_copy)
    #                 # 本次出牌結果pick_combine_insert_drop[1]加入之
    #                 from_combine_to_combine.append(pick_combine_insert_drop[1])
    #
    #         for i, from_combine_to_drop_s in enumerate(from_combine_to_drop):
    #             # 走訪所有場上組合，準備預知插牌狀況
    #             pairscard = self._get_pairs_card_list(from_combine_to_drop_s)
    #             caninsertcard = []  # 臨時放入可插的牌
    #             candropcard = []  # 臨時放入可棄的牌
    #
    #             for combo in all_insert_combos.values():
    #                 card_index_list = list(combo.keys())
    #
    #                 for pairs_index in reversed(pairscard):
    #                     card_combo = card_index_list + pairs_index
    #                     card_serial.Clear()
    #                     card_serial.AddBatch(card_combo)
    #                     can_insert = card_serial.HasFullMatch(card_combo)
    #
    #                     if not can_insert:
    #                         continue
    #
    #                     if pairs_index not in caninsertcard:
    #                         caninsertcard = caninsertcard + pairs_index  # 丟入視為可插
    #                         # 將可插牌從手牌當中移除
    #                         from_combine_to_drop_s = list(set(from_combine_to_drop_s) - set(pairs_index))
    #                     pairscard.remove(pairs_index)
    #
    #                     # 接下來把連續2張個別拆開來看
    #                     card_combo = card_index_list + [pairs_index[0]]
    #                     card_serial.Clear()
    #                     card_serial.AddBatch(card_combo)
    #
    #                     if not card_serial.HasFullMatch(card_combo):  # 如果個別不可插牌
    #                         if pairs_index[0] not in candropcard:
    #                             candropcard.append(pairs_index[0])  # 這1張丟入視為可棄
    #
    #                     else:  # 如果連續插牌的第1張可插，那就換連續插牌的第2張判斷
    #                         card_combo = card_index_list + [pairs_index[1]]
    #                         card_serial.Clear()
    #                         card_serial.AddBatch(card_combo)
    #
    #                         if not card_serial.HasFullMatch(card_combo):  # 如果個別不可插牌
    #                             if pairs_index[1] not in candropcard:
    #                                 candropcard.append(pairs_index[1])  # 這1張丟入視為可棄
    #
    #             if pairscard != []:  # 上面的連續插牌判斷完成了，還有剩下來的牌
    #                 for pair in pairscard:
    #                     if pair not in from_combine_to_drop_s:
    #                         from_combine_to_drop_s = from_combine_to_drop_s + pair  # 剩下的加入手牌
    #
    #             # 接下來判斷「單一無關插牌」的部分
    #             for combo in all_insert_combos.values():
    #                 card_index_list = list(combo.keys())
    #
    #                 for card_index in from_combine_to_drop_s:
    #                     card_combo = card_index_list + [card_index]
    #                     card_serial.Clear()
    #                     card_serial.AddBatch(card_combo)
    #                     if card_serial.HasFullMatch(card_combo):  # 如果可插牌
    #                         if card_index not in caninsertcard:
    #                             caninsertcard = caninsertcard + [card_index]  # 丟入插牌陣列
    #                             # 將可插牌從手牌當中移除
    #                             from_combine_to_drop_s = list(set(from_combine_to_drop_s) - set([card_index]))
    #                         # 為避免無牌可棄，把不是連續插牌的都丟入
    #                         if card_index not in candropcard:
    #                             candropcard.append(card_index)
    #
    #             # 再建一個[[], [[出牌組合1, 出牌組合2]], [], []]
    #             pick_combine_insert_drop = [[], [], [], []]
    #             # 上一出牌階段被加入臨時出牌區的牌，加入至正式出牌區
    #             pick_combine_insert_drop[1] = pick_combine_insert_drop[1] + from_combine_to_combine[i]
    #             # 留下來的臨時插牌區的牌，加入至正式插牌區
    #             pick_combine_insert_drop[2] = pick_combine_insert_drop[2] + caninsertcard
    #
    #             for i in from_combine_to_drop_s:  # 走訪手牌並逐一棄置
    #                 if i not in pick_combine_insert_drop[3]:
    #                     pick_combine_insert_drop[3].append(i)  # 全數丟入棄牌陣列
    #
    #             # 判斷[2]插牌區與[3]棄牌區有沒有重複
    #             for drop_a_card in reversed(pick_combine_insert_drop[3]):
    #                 if drop_a_card in pick_combine_insert_drop[2]:
    #                     # 重複的從[3]棄牌區移除
    #                     pick_combine_insert_drop[3].remove(drop_a_card)
    #
    #             # 如果棄牌陣列只剩一張
    #             if len(pick_combine_insert_drop[3]) in (0, 1):
    #                 Log("未開張一次清空={}".format(pick_combine_insert_drop))
    #                 # 一旦一個組合牌型達成未開張一次清空，那就沒必要再找下一種了
    #                 self.android_pick_combine_insert_drop = pick_combine_insert_drop
    #                 return pick_combine_insert_drop
    #
    #     else:
    #         # 建立並複製一個手牌index的清單，作為「預知手牌」
    #         mInHand_copy = [i for i in self.mInHand.keys()]
    #         mInHand_copy = sorted(mInHand_copy)
    #
    #         # [[], [[出牌組合1, 出牌組合2]], [], []]
    #         pick_combine_insert_drop = [[], [], [], []]
    #
    #         # 走訪所有場上組合，準備預知插牌狀況
    #         pairscard = self._get_pairs_card_list(mInHand_copy)  # 2張連續順子聽搭
    #         caninsertcard = []  # 臨時放入可插的牌
    #         candropcard = []  # 臨時放入可棄的牌
    #
    #         for combo in all_insert_combos.values():
    #             card_index_list = list(combo.keys())
    #
    #             for pairs_index in reversed(pairscard):
    #                 card_combo = card_index_list + pairs_index
    #                 card_serial.Clear()
    #                 card_serial.AddBatch(card_combo)
    #                 can_insert = card_serial.HasFullMatch(card_combo)
    #
    #                 if not can_insert:
    #                     continue
    #
    #                 if pairs_index not in caninsertcard:
    #                     caninsertcard = caninsertcard + pairs_index  # 丟入插牌陣列
    #                     # 將可插牌從手牌當中移除
    #                     mInHand_copy = list(set(mInHand_copy) - set(pairs_index))
    #
    #                 pairscard.remove(pairs_index)
    #
    #                 # 接下來把連續2張個別拆開來看
    #                 card_combo = card_index_list + [pairs_index[0]]
    #                 card_serial.Clear()
    #                 card_serial.AddBatch(card_combo)
    #
    #                 if not card_serial.HasFullMatch(card_combo):  # 如果個別不可插牌
    #                     if pairs_index[0] not in candropcard:
    #                         candropcard.append(pairs_index[0])  # 這1張丟入視為可棄
    #
    #                 else:  # 如果連續插牌的第1張可插，那就換連續插牌的第2張判斷
    #                     card_combo = card_index_list + [pairs_index[1]]
    #                     card_serial.Clear()
    #                     card_serial.AddBatch(card_combo)
    #
    #                     if not card_serial.HasFullMatch(card_combo):  # 如果個別不可插牌
    #                         if pairs_index[1] not in candropcard:
    #                             candropcard.append(pairs_index[1])  # 這1張丟入視為可棄
    #
    #         if pairscard != []:  # 上面的連續插牌判斷完成了，還有剩下來的牌
    #             for pair in pairscard:
    #                 mInHand_copy = mInHand_copy + pair  # 剩下的加入手牌
    #
    #         # 接下來判斷「單一無關插牌」的部分
    #         for combo in all_insert_combos.values():
    #             card_index_list = list(combo.keys())
    #
    #             for card_index in mInHand_copy:
    #                 card_combo = card_index_list + [card_index]
    #                 card_serial.Clear()
    #                 card_serial.AddBatch(card_combo)
    #
    #                 if card_serial.HasFullMatch(card_combo):  # 如果可插牌
    #                     if card_index not in caninsertcard:
    #                         caninsertcard = caninsertcard + [card_index]  # 丟入插牌陣列
    #                         # 將可插牌從手牌當中移除
    #                         mInHand_copy = list(set(mInHand_copy) - set([card_index]))
    #
    #                     # 為避免無牌可棄，把不是連續插牌的都丟入
    #                     if card_index not in candropcard:
    #                         candropcard.append(card_index)
    #
    #         # 留下來的臨時插牌區的牌，加入至正式插牌區
    #         pick_combine_insert_drop[2] = pick_combine_insert_drop[2] + caninsertcard
    #         for i in mInHand_copy:  # 走訪手牌並逐一棄置
    #             pick_combine_insert_drop[3].append(i)  # 全數丟入棄牌陣列
    #
    #         if len(pick_combine_insert_drop[3]) in (0, 1):
    #             Log("未開張一次清空={}".format(pick_combine_insert_drop))
    #             # 一旦一個組合牌型達成未開張一次清空，那就沒必要再找下一種了
    #             self.android_pick_combine_insert_drop = pick_combine_insert_drop
    #             return pick_combine_insert_drop
    #     return None

    def has_special_combine(self):
        """確認玩家的組合中是否有特殊組合

        檢查組合之中有無鐵支、五張順子
        """
        special_count = 0  # 特殊組合有幾組
        for group in self.group_combination:
            if len(group) == 4:  # 是否為鐵支
                card_index_ls = [card_index for card_index in group]
                is_4_of_a_kind = True  # 先預設True
                for i in range(3):
                    is_4_of_a_kind = abs(card_index_ls[i] - card_index_ls[i + 1]) % 16 == 0

                    if not is_4_of_a_kind:
                        break
                if is_4_of_a_kind:  # 若 break 出來回傳 False，跑完 for 出來回傳 True
                    special_count += 1

            elif len(group) == 5:  # 一定是順子
                special_count += 1

        return special_count  # 最後特殊組合有幾組

    def CheckAnyAction(self, all_combos, is_fight=False, SeaBottomOrder=None):
        if is_fight:
            self.nOpAllow = 0  # 清空所有選項
            if self.bIsOpened:  # 玩家開張才有選擇
                self.nOpAllow |= EnumGameOperation.Challenge
                self.nOpAllow |= EnumGameOperation.Fold
            else:  # 直接設定為放棄
                self.nOpAllow |= EnumGameOperation.Fold
            return

        if SeaBottomOrder and not self.has_drawed_or_picked:  # 組牌後沒抽過牌或撿過牌
            is_even_turn_fight = self.nTurnCount % 2 == 0 and self.odd_turn_inserted_mark != 1
            is_odd_turn_fight = self.nTurnCount % 2 == 1 and self.even_turn_inserted_mark != 1
            # 若已開張，且上回合自己的牌面牌沒被人插牌
            if self.bIsOpened and (is_even_turn_fight or is_odd_turn_fight):
                self.nOpAllow |= EnumGameOperation.Fight  # 允許發起比牌
                self.op_allow_fight = 1  # 用來告示前端目前這位玩家允許發起比牌

            self.nOpAllow |= EnumGameOperation.nDraw  # 要能允許抽牌
            self._check_pick_action(SeaBottomOrder[-1], list(self.mInHand.keys()))  # 要能驗證是否允許撿牌

        if len(self.mInHand) > 1:
            card_serial = CardSerializer()
            card_serial.AddBatch(list(self.mInHand.keys()))
            combos = card_serial.GetAllCombo(remain_one=self.mInHand)

            self.nOpAllow |= EnumGameOperation.GroupReorganize
            if len(combos) > 0 and len(self.mInHand) > LogicConfig.nMinContinuity:
                if self.has_drawed_or_picked:  # 本輪抽過或撿過牌
                    self.nOpAllow |= EnumGameOperation.nCombine  # 才能允許出牌

                if len(self.group_combination) != 0:
                    self.nOpAllow |= EnumGameOperation.UnGroup

                if combos not in self.group_combination:
                    self.nOpAllow |= EnumGameOperation.Group

            # 不清楚是否是因為前端流程關係，所以才沒把這個值消除掉
            # 目前先手動消除，若沒有 combo 又有組牌選項時要消除
            elif (self.OpAllow & EnumGameOperation.Group) != 0:
                self.nOpAllow ^= EnumGameOperation.Group

            # 檢查手中的牌是否可以插到已經打出的組合中
            if self.has_drawed_or_picked:  # 本輪抽過或撿過牌
                for combo in all_combos.values():
                    matched = False
                    for card_index in self.mInHand:
                        card_index_list = list(combo.keys())
                        card_index_list.append(card_index)
                        card_serial.Clear()
                        card_serial.AddBatch(card_index_list)
                        if card_serial.HasFullMatch(card_index_list):
                            matched = True
                            break
                    if matched:
                        self.nOpAllow |= EnumGameOperation.nInsert  # 才能允許插牌
                        break

    def AddCard(self, card_info):
        if not self.bIsJoined:
            return False
        self.mInHand[card_info.Poker.Index] = card_info
        card_info.SetOwner(self)

    def Announce(self):
        if (self.nOpAllow & EnumGameOperation.nAnnounce) == 0:
            return False

        self.bIsAnnounced = True
        self.nOpAllow &= 0xff ^ EnumGameOperation.nAnnounce
        return True

    def DrawCard(self, card_info):
        if (self.nOpAllow & EnumGameOperation.nDraw) == 0:
            return False
        self.mInHand[card_info.Poker.Index] = card_info
        card_info.SetOwner(self)
        self.nOpAllow = EnumGameOperation.nDrop
        self.nTurnFirstOp = EnumGameOperation.nDraw
        return True

    def Pick(self, card_index, picked_card_info, combine):
        if (self.nOpAllow & EnumGameOperation.nPick) == 0:
            return False

        if len(combine) < LogicConfig.nMinContinuity:
            return False

        if len(combine) > LogicConfig.nMaxContinuity:
            return False

        card_serial = CardSerializer()
        card_serial.AddBatch(combine)
        if not card_serial.HasFullMatch(combine):
            return False

        in_hand_list = list(self.mInHand.keys())
        card_serial.Clear()
        card_serial.AddBatch(in_hand_list)
        card_serial.AddBatch(list(picked_card_info.keys()))
        combos = card_serial.GetAllCombo(card_index, in_hand_list)
        if len(combos) == 0:
            return False

        matched = False
        for combo in combos:
            all_matched = True
            for cb_card_index in combine:
                if cb_card_index not in combo:
                    all_matched = False
                    break

                self._ungroup_process(cb_card_index)  # 確認撿牌是否有卡組牌區需要解散組牌

            if all_matched:
                matched = True
                break
        if not matched:
            return False

        if self.nPickedFirstType == -1:
            poker_type, poker_point = Poker.Index2TypePoint(card_index)
            self.nPickedFirstType = poker_type

        for picked_index in picked_card_info:
            card_info = picked_card_info[picked_index]
            self.mInHand[picked_index] = card_info

        new_combo = {}
        for cb_card_index in combine:
            card_info = self.mInHand.pop(cb_card_index, None)

            # 累計消耗比牌點數計算
            _, card_point = Poker.Index2TypePoint(cb_card_index)
            self.consume_point += card_point if card_point <= 10 else 10

            self.check_add_point_event(cb_card_index)  # 加分牌累計計算
            self.nComboSheetsAmounts += 1  # 每出掉一張就加一次
            card_info.SetFinalOwner(self)
            new_combo[cb_card_index] = card_info
            if card_info.Poker.Type != self.nPickedFirstType:
                self.bAllSameType = False
        self.mCombos[self.nComboCount] = new_combo
        self.nComboCount += 1

        # 普通加減+0沒分，只是雲端拿來記錄撿牌出牌狀況
        self.ProcNormalScore(EnumGameOperation.nPick, new_combo.values())

        if len(picked_card_info) == 1:
            picked_target = picked_card_info[card_index]
            if len(picked_target.DropOrder) > 0:
                self.xPickedFinal = picked_target

        if not self.bIsOpened:  # 如果還沒開張
            self.nTurnWhenOpen = self.nTurnCount
            self.bIsOpened = True  # 撿牌為開張
            self.open_time = int(time.time())  # 紀錄開張瞬間

        self.nOpAllow = EnumGameOperation.nDrop
        self.nTurnFirstOp = EnumGameOperation.nPick
        return True

    def _ungroup_process(self, cb_card_index):
        """若牌在組牌組合中，解散該組合

        Args:
            cb_card_index (int): 撲克牌編號

        為什麼一樣的步驟要跑3次？出牌強制解散組牌區的組合，有可能出現2組以上的組合需要被解散。
        因此走訪3次，因為組牌區最多4組，而擁有4組等於tongits，意味出牌行為最多3組被解散remove。
        """
        for _ in range(3):
            for group_dc in self.group_combination:
                for group_index in group_dc:  # 走訪組牌區的keys(index)
                    if cb_card_index == group_index:
                        self.group_combination.remove(group_dc)
                        break

    def check_add_point_event(self, card_index):
        is_A = card_index % 16 == 1
        is_K = card_index % 16 == 13

        if is_A or is_K:
            self.add_point_event += 1

    def Combine(self, combine):
        if (self.nOpAllow & EnumGameOperation.nCombine) == 0:
            return False

        if len(combine) < LogicConfig.nMinContinuity:
            return False

        if len(combine) > LogicConfig.nMaxContinuity:
            return False

        for cb_card_index in combine:
            if cb_card_index not in self.mInHand:
                return False

        card_serial = CardSerializer()
        card_serial.AddBatch(combine)
        if not card_serial.HasFullMatch(combine):
            return False

        new_combo = {}
        for cb_card_index in combine:

            self._ungroup_process(cb_card_index)  # 確認出牌是否有卡組牌區需要解散組牌

            # 累計消耗比牌點數計算
            _, card_point = Poker.Index2TypePoint(cb_card_index)
            self.consume_point += card_point if card_point <= 10 else 10

            card_info = self.mInHand.pop(cb_card_index, None)
            self.check_add_point_event(cb_card_index)  # 加分牌累計計算

            self.nComboSheetsAmounts += 1  # 每出掉一張就加一次
            card_info.SetFinalOwner(self)
            new_combo[cb_card_index] = card_info
            if card_info.Poker.Type != self.nPickedFirstType:
                self.bAllSameType = False

        self.mCombos[self.nComboCount] = new_combo

        if not self.bIsOpened:  # 如果還沒開張
            self.nTurnWhenOpen = self.nTurnCount
            self.bIsOpened = True  # 出牌視為開張
            self.open_time = int(time.time())  # 紀錄開張瞬間

        self.nComboCount += 1
        # 普通加減+0沒分，只是雲端拿來記錄撿牌出牌狀況
        self.ProcNormalScore(EnumGameOperation.nCombine, new_combo.values())
        self.nOpAllow = EnumGameOperation.nDrop
        return True

    def Insert(self, card_index, target_player_info, target_combo_index):
        if (self.nOpAllow & EnumGameOperation.nInsert) == 0:
            return False
        if card_index not in self.mInHand:
            return False
        if target_combo_index not in target_player_info.Combos:
            return False

        target_combo = target_player_info.Combos[target_combo_index]
        card_serial = CardSerializer()
        card_index_list = list(target_combo.keys())
        card_index_list.append(card_index)
        card_serial.AddBatch(card_index_list)
        if not card_serial.HasFullMatch(card_index_list):
            return False

        self._ungroup_process(card_index)  # 確認插牌是否有卡組牌區需要解散組牌

        # 累計消耗比牌點數計算
        _, card_point = Poker.Index2TypePoint(card_index)
        self.consume_point += card_point if card_point <= 10 else 10

        card_info = self.mInHand.pop(card_index, None)
        self.nComboSheetsAmounts += 1  # 每出掉一張就加一次
        self.check_add_point_event(card_index)  # 加分牌累計計算
        self.water_balloon += 10  # 每次進行插牌+10水球

        card_info.SetFinalOwner(self)
        target_combo[card_index] = card_info
        if card_info.Poker.Type != self.nPickedFirstType:
            self.bAllSameType = False

        # 普通加減+0沒分，只是雲端拿來記錄撿牌出牌狀況
        self.ProcNormalScore(EnumGameOperation.nInsert, (card_info,))

        self.nOpAllow = EnumGameOperation.nDrop
        return True

    def Drop(self, card_index):
        if (self.nOpAllow & EnumGameOperation.nDrop) == 0:
            return None

        # 不小心棄掉組牌區的牌
        self._ungroup_process(card_index)  # 確認棄牌是否有卡組牌區需要解散組牌

        # 計算牌面比牌點數
        _, card_point = Poker.Index2TypePoint(card_index)
        if card_point < self.drop_first_min_card:  # 牌面比自己歷程最小棄牌還小
            self.drop_second_min_card = self.drop_first_min_card  # 原本最小棄牌取代為第2小棄牌
            self.drop_first_min_card = card_point  # 最小棄牌被本次棄牌取代
        elif card_point < self.drop_second_min_card:  # 牌面比自己歷程第2小棄牌還小
            self.drop_second_min_card = card_point

        card_info = self.mInHand.pop(card_index, None)
        if card_info is None:
            return None

        card_info.Dropped(self, self.bIsOpened)
        self.nOpAllow = 0
        return card_info

    def Group(self, combination):
        if (len(combination) < LogicConfig.nMinContinuity or
            len(combination) > LogicConfig.nMaxContinuity):
            return False

        for card_index in combination:
            if card_index not in self.mInHand:
                return False

        card_serial = CardSerializer()
        card_serial.AddBatch(combination)
        if not card_serial.HasFullMatch(combination):
            return False

        # 驗證組牌加牌時，牌是否在裡面
        is_break = False
        for old_group in self.group_combination:  # 走訪玩家組牌區
            for group_index in old_group:  # 走訪組牌區的keys(index)
                if group_index in combination:  # 如果其中一張早就被組過了
                    self.group_combination.remove(old_group)  # 組牌區移除舊組合
                    is_break = True
                    break  # 若組牌區有更新組合則沒必要繼續走訪
            if is_break:
                break  # 若組牌區有更新組合則沒必要繼續走訪

        new_group = {}
        for card_index in combination:
            new_group[card_index] = self.mInHand[card_index]

        self.group_combination.append(new_group)
        self.nOpAllow = EnumGameOperation.nDrop
        return True

    def UnGroup(self, card_index_list):
        for card_index in card_index_list:
            self._ungroup_process(card_index)
        return True

    def GroupReorganize(self, combinations):
        # 走訪所有新增組合
        for combination in combinations:
            if (len(combination) < LogicConfig.nMinContinuity or
                    len(combination) > LogicConfig.nMaxContinuity):
                return False  # 執行的組合超過張數限制

            for card_index in combination:
                if card_index not in self.mInHand:
                    return False  # 執行的牌不在手牌內

            card_serial = CardSerializer()
            card_serial.AddBatch(combination)
            if not card_serial.HasFullMatch(combination):
                return False  # 執行的組合不是組合

            new_group = {}
            for card_index in combination:
                new_group[card_index] = self.mInHand[card_index]

            self.group_combination.append(new_group)
        return True

    def Fight(self):
        if (self.nOpAllow & EnumGameOperation.Fight) == 0:
            return False

        self.nOpAllow = 0  # 清空所有選項
        self.fight_status = EnumGameOperation.Fight
        return True

    def Challenge(self):
        if (self.nOpAllow & EnumGameOperation.Challenge) == 0:
            return False

        self.nOpAllow = 0  # 清空所有選項
        self.nOpAllow |= EnumGameOperation.Challenge
        self.fight_status = EnumGameOperation.Challenge
        return True

    def Fold(self):
        if (self.nOpAllow & EnumGameOperation.Fold) == 0:
            return False

        self.nOpAllow = 0  # 清空所有選項
        self.nOpAllow |= EnumGameOperation.Fold
        self.fight_status = EnumGameOperation.Fold
        return True

    def _check_pick_action(self, new_picked_order, in_hand):
        """判斷玩家是否可以撿牌，並給予動作選項

        Args:
            new_picked_order (int): 玩家可以撿的牌
            in_hand (list): 手中有的牌
        """
        card_serial = CardSerializer()

        card_serial.Clear()
        card_serial.AddBatch(in_hand)
        card_serial.Add(new_picked_order)

        all_dict = {new_picked_order: 0}
        all_dict.update(self.mInHand)
        combos = card_serial.GetAllCombo(new_picked_order, self.mInHand, all_dict)

        if len(combos) > 0:
            self.nOpAllow |= EnumGameOperation.nPick

    def _check_group_action(self, in_hand):
        """判斷玩家是否可以組牌，並給予動作選項

        Args:
            in_hand (list): 手中有的牌
        """
        card_serial = CardSerializer()

        card_serial.Clear()
        card_serial.AddBatch(in_hand)

        all_dict = {}
        all_dict.update(self.mInHand)
        combos = card_serial.GetAllCombo(match_one=self.mInHand, remain_one=all_dict)

        if len(combos) > 0:
            self.nOpAllow |= EnumGameOperation.Group
            self.nOpAllow |= EnumGameOperation.GroupReorganize

    def NewTurn(self, sea_bottom_order, is_opening_player):
        """

        Args:
            sea_bottom_order (list): 海底的牌
            is_opening_player (bool): 是否為開局玩家，因為開局玩家不能抽牌
        """
        if not self.bIsJoined:
            return False
        self.nOpAllow = 0
        self.nTurnFirstOp = 0

        in_hand = list(self.mInHand.keys())

        self._check_group_action(in_hand)
        if not is_opening_player:
            self.nOpAllow |= EnumGameOperation.nDraw
        else:  # 開局玩家流程
            self.nOpAllow |= EnumGameOperation.nDrop

        if len(sea_bottom_order) != 0:
            self._check_pick_action(sea_bottom_order[-1], in_hand)  # 海底只有最後一張牌

        self.xPickedFinal = None
        self.nTurnCount += 1

        if self.nTurnCount % 2 == 0:  # 將本回合標籤回復為預設值
            self.even_turn_inserted_mark = 0
        else:
            self.odd_turn_inserted_mark = 0

        is_even_turn_fight = self.nTurnCount % 2 == 0 and self.odd_turn_inserted_mark != 1
        is_odd_turn_fight = self.nTurnCount % 2 == 1 and self.even_turn_inserted_mark != 1
        # 若已開張，且上回合自己的牌面牌沒被人插牌
        if self.bIsOpened and (is_even_turn_fight or is_odd_turn_fight):
            self.nOpAllow |= EnumGameOperation.Fight  # 允許發起比牌
            self.op_allow_fight = 1  # 用來告示前端目前這位玩家允許發起比牌
        if not is_even_turn_fight and not is_odd_turn_fight:  # 上一回合自己的檯面牌被人插牌
            self.op_allow_fight = 0  # 用來告示前端目前這位玩家不允許發起比牌，而且畫面必須被插刀子

        return True

    def set_auto_operate(self, is_auto):
        """記錄該玩家最後一次操作是否為系統自動操作

        Args:
            is_auto (bool): True 代表是
        """
        self.auto_operate = 1 if is_auto else 0

    def get_current_point(self):
        total_point = 0
        all_group_card_index_ls = []

        # 如果自己是放棄比牌方，那也不用比了，直接視為點數999
        if self.fight_status == EnumGameOperation.Fold:
            return 999

        # 將所有 card_index 從 group_combination 拆解出來，方便後續比對
        for group in self.group_combination:
            for card_index in group:
                all_group_card_index_ls.append(card_index)

        for card_index in self.mInHand:
            _, card_point = Poker.Index2TypePoint(card_index)

            if card_index in all_group_card_index_ls:
                continue

            total_point += card_point if card_point <= 10 else 10

        self.compare_point = total_point
        return total_point

    def get_in_hand_without_group(self):
        """取得組合之外的牌

        Returns:
            output (dict): 跟 self.mInHand 一樣，只是去除掉是組合的牌
        """
        all_group_card_index_ls = []
        output = {}

        # 將所有 card_index 從 group_combination 拆解出來，方便後續比對
        for group in self.group_combination:
            for card_index in group:
                all_group_card_index_ls.append(card_index)

        for card_index, card_info in self.mInHand.items():
            _, card_point = Poker.Index2TypePoint(card_index)

            if card_index in all_group_card_index_ls:
                continue

            output[card_index] = card_info

        return output

class GameLogic(object):
    def __init__(self):
        self.mUsers = {}
        self.StrRoundSign = 0
        self.mPlayers = {} # seat_index : PlayerInfo
        self.vPlayersOrder = [] # seat_index
        self.nTurnCursor = 0
        self.mDeck = {} # card_index : CardInfo
        self.vDeckOrder = [] # card_index ...
        self.nDeckCursor = 0
        self.mSeaBottom = {} # card_index : CardInfo
        self.vSeaBottomOrder = [] # card_index ...
        self.mAllCombos = {} # unq_index : { card_index : CardInfo }
        self.vLevel = []
        self.nJoinedCount = 0
        self.bIsGaming = False
        self.bIsFinished = False
        self.bHasAndroid = False
        self.is_fight = False

        self.mOperationProc = {
            EnumGameOperation.nAnnounce: self.Announce,
            EnumGameOperation.nDraw: self.Draw,
            EnumGameOperation.nPick: self.Pick,
            EnumGameOperation.nCombine: self.Combine,
            EnumGameOperation.nInsert: self.Insert,
            EnumGameOperation.nDrop: self.Drop,
            EnumGameOperation.Group: self.Group,
            EnumGameOperation.UnGroup: self.UnGroup,
            EnumGameOperation.GroupReorganize: self.GroupReorganize,
            EnumGameOperation.Fight: self.Fight,
            EnumGameOperation.Challenge: self.Challenge,
            EnumGameOperation.Fold: self.Fold,
        }

    def __repr__(self):
        return str(self.__dict__)

    @property
    def Players(self):
        return self.mPlayers

    @property
    def Deck(self):
        return self.mDeck

    @property
    def SeaBottom(self):
        return self.mSeaBottom

    @property
    def AllCombos(self):
        return self.mAllCombos

    @property
    def Level(self):
        return self.vLevel

    @property
    def IsGaming(self):
        return self.bIsGaming

    @property
    def IsFinished(self):
        return self.bIsFinished

    @property
    def HasAndroid(self):
        return self.bHasAndroid

    @property
    def CurrentTurn(self):
        return self.vPlayersOrder[self.nTurnCursor]

    def UpdateStrRoundSign(self, NewStrRoundSign):
        self.StrRoundSign = NewStrRoundSign

    def UpdatemUsers(self, mUsers):
        self.mUsers = mUsers

    def GetComboUniqueIndex(self, seat_index, combo_index):
        return ((seat_index & 0xffff) << 16) | (combo_index & 0xffff)

    def SplitComboUniqueIndex(self, unique_index):
        return (unique_index >> 16) & 0xffff, unique_index & 0xffff

    def GetRecords(self):
        rec = {}
        for player_info in self.mPlayers.values():
            rec_per_player = player_info.GetScoreRecordsAndFlush()
            if rec_per_player is not None:
                rec[player_info.SeatIndex] = rec_per_player
        return rec

    def ResetDeck(self, from_3rd_data = None):
        if self.bIsGaming:
            return False

        poker_set = LogicConfig.mPokers
        poker_count = len(poker_set)
        poker_order = LogicConfig.vPokerOrder
        if from_3rd_data is None: # local rand
            for i in range(poker_count):
                first_range = GetRndInt(1, poker_count - 1)
                second_range = poker_count - first_range
                first_index = GetRndInt(0, first_range - 1)
                second_index = GetRndInt(0, second_range - 1) + first_range
                tmp = poker_order[first_index]
                poker_order[first_index] = poker_order[second_index]
                poker_order[second_index] = tmp

        else: # use 3rd data
            poker_order = LogicConfig.CardSymbolCovertor(from_3rd_data)
            if poker_order is None:
                Err("Third data is invalid!")
                return False
            else:
                LogicConfig.vPokerOrder = poker_order
        internal_data = deepcopy(poker_order)
        
        new_deck = {}
        for card_index in internal_data:
            poker = poker_set[card_index]
            new_deck[card_index] = CardInfo(poker)

        self.mDeck = new_deck
        self.vDeckOrder = internal_data
        self.nDeckCursor = 0
        self.mSeaBottom.clear()
        self.vSeaBottomOrder.clear()
        self.mAllCombos.clear()
        return True

    def PlayerJoinIn(self, seat_index, android = False):
        if self.bIsGaming:
            return False

        if self.nJoinedCount >= LogicConfig.nTotalSeats:
            Warn("No idle seat!")
            return False

        seat_index = int(seat_index)
        if seat_index < 0 or seat_index >= LogicConfig.nTotalSeats:
            Warn("Invalid seat index!")
            return False

        player_info = None
        if seat_index not in self.mPlayers:
            player_info = PlayerInfo(seat_index)
            self.mPlayers[seat_index] = player_info
        else:
            player_info = self.mPlayers[seat_index]

        if player_info.IsJoined:
            Warn("Seat [%d] has been occupied!")
            return False

        player_info.JoinIn()
        self.nJoinedCount += 1
        if android:
            self.bHasAndroid = android
        return True

    def PlayerLeave(self, seat_index):
        if self.bIsGaming:
            Warn("No PlayerLeave Because self.bIsGaming")
            return False

        if self.nJoinedCount <= 0:
            Warn("No player joined in!")
            return False

        seat_index = int(seat_index)
        if seat_index < 0 or seat_index >= LogicConfig.nTotalSeats:
            Warn("Invalid seat index!")
            return False

        if seat_index in self.mPlayers:
            player_info = self.mPlayers[seat_index]
            if player_info.IsJoined:
                player_info.Leave()
                self.nJoinedCount -= 1

        return True

    def GameStart(self, from_3rd_data = None):
        if self.bIsGaming:
            Warn("玩家異常在遊戲中")
            return False

        if self.nJoinedCount < LogicConfig.nMinPlayers2Start:
            Warn("加入的真人與機器人數量加總未達最低開局人數")
            return False

        players_order = self.vPlayersOrder
        players_order.clear()
        for seat_index in self.mPlayers:
            player_info = self.mPlayers[seat_index]
            if player_info.NewRound():
                players_order.append(seat_index)

        real_joined = len(players_order)
        if real_joined < LogicConfig.nMinPlayers2Start:
            Warn("Game start failed!", players_order, self.mPlayers)
            return False
        players_order.sort()

        if real_joined not in LogicConfig.mStartCardsNumConfig:
            return False

        if not self.ResetDeck(from_3rd_data):
            return False

        game_start_seat_index = self.CalcNextTurnCursor(True)  # 誰先第1回合起手
        cards_per_player = LogicConfig.mStartCardsNumConfig[real_joined]  # 發12張

        # 先發12張牌給3個人
        for i in range(cards_per_player):
            for j in range(real_joined):
                seat_index = players_order[j]
                player_info = self.mPlayers[seat_index]
                card_index = self.vDeckOrder[self.nDeckCursor]
                self.nDeckCursor += 1
                card_info = self.mDeck.pop(card_index, None)
                if card_info is None:
                    Warn("Lose card info in deck!")
                    return False
                player_info.AddCard(card_info)  # 加牌

        # 拿到起手優先的玩家再多發1張牌，為13張牌
        player_info = self.mPlayers[game_start_seat_index]
        card_index = self.vDeckOrder[self.nDeckCursor]
        self.nDeckCursor += 1
        card_info = self.mDeck.pop(card_index, None)
        if card_info is None:
            Warn("Lose card info in deck!")
            return False
        player_info.AddCard(card_info)  # 加牌
        player_info.has_drawed_or_picked = True  # 先手回合的人就當作抽完牌了

        self.vLevel.clear()
        self.bIsGaming = True
        self.bIsFinished = False
        return True

    def GameEnd(self):
        if self.bIsGaming and self.bIsFinished:
            self.bIsGaming = False
            self.bIsFinished = False
            self.bHasAndroid = False
            self.is_fight = False

    def CalcNextTurnCursor(self, rand=False):
        """輪到下一位玩家動作

        Args:
            rand (bool):
                True 代表牌局剛開始，隨機抽一個人開始，並多給他一張牌

        """
        is_opening_player = rand

        if rand:
            # 定義起始回合座號操作順序
            self.nTurnCursor = GetRndInt(0, len(self.vPlayersOrder) - 1)

            seat_index = self.vPlayersOrder[self.nTurnCursor]

        else:
            self.nTurnCursor += 1
            if self.nTurnCursor >= len(self.vPlayersOrder):
                self.nTurnCursor = 0

            seat_index = self.vPlayersOrder[self.nTurnCursor]

        self.mPlayers[seat_index].NewTurn(self.vSeaBottomOrder, is_opening_player)
        return self.nTurnCursor

    def _choose_drop_card(self, player_info):  # 玩家時間到被強迫棄牌時，要選擇哪張牌？
        all_group_card_index_ls = []
        # 將所有 card_index 從 group_combination 拆解出來，方便後續比對
        for group in player_info.group_combination:
            for card_index in group:
                all_group_card_index_ls.append(card_index)

        max_card = [0, 0, 0]  # 設置最大雜牌[牌面序號, 牌面數字, 牌面花色]
        for card_index in player_info.mInHand:
            if card_index in all_group_card_index_ls:  # 如果是組牌區的牌
                continue  # 跳過不計算

            drop_card_number = int(card_index % 16)  # 牌面數字
            drop_card_flower = int(math.floor(card_index / 16))  # 牌面花色，0梅花1方塊2愛心3黑桃

            if drop_card_number > max_card[1]:  # 若牌面數字比原來的大
                max_card = [card_index, drop_card_number, drop_card_flower]  # 取代成為最大雜牌
            elif drop_card_number == max_card[1]:  # 若牌面數字比原來的相等
                if drop_card_flower > max_card[2]:  # 若牌面花色比原來的大
                    max_card = [card_index, drop_card_number, drop_card_flower]  # 取代成為最大雜牌

        return max_card[0]  # 選擇最大雜牌的序號丟棄之

    def who_has_the_smallest_card(self, p_one_index, p_two_index, p_one_inhand_keys, p_two_inhand_keys):
        # 平手第一階段：誰雜牌少
        if len(p_one_inhand_keys) < len(p_two_inhand_keys):
            return p_one_index
        elif len(p_one_inhand_keys) > len(p_two_inhand_keys):
            return p_two_index

        # 平手第二階段：找出最大雜牌持有者敗
        max_card = [0, 0, 0]  # 設置最大雜牌[牌面序號, 牌面點數非數字, 牌面花色]
        for card_index in p_one_inhand_keys + p_two_inhand_keys:
            drop_card_point = int(card_index % 16)  # 牌面點數
            drop_card_flower = int(math.floor(card_index / 16))  # 牌面花色，0梅花1方塊2愛心3黑桃

            if drop_card_point > max_card[1]:  # 若牌面點數比原來的大
                max_card = [card_index, drop_card_point, drop_card_flower]  # 取代成為最大雜牌
            elif drop_card_point == max_card[1]:  # 若牌面點數比原來的相等
                if drop_card_flower > max_card[2]:  # 若牌面花色比原來的大
                    max_card = [card_index, drop_card_point, drop_card_flower]  # 取代成為最大雜牌

        if max_card[0] in p_one_inhand_keys:  # 最大雜牌在1號選手身上
            return p_two_index  # 2號選手的座號獲勝
        else:  # 最大雜牌在2號選手身上
            return p_one_index  # 1號選手的座號獲勝

    def GetPlayerForceOp(self):
        if not self.bIsGaming:
            return None, None, None

        if self.bIsFinished:
            return None, None, None

        seat_index = self.vPlayersOrder[self.nTurnCursor]
        player_info = self.mPlayers[seat_index]
        Log("局號[%s]玩家[%s]座位[%.2d]超過思考時間，系統自動操作" % (self.StrRoundSign, self.mUsers[seat_index].UUID, seat_index))
        # # 如果玩家按下了未開張一次清空的dummy，或同意持續操作未開張一次清空事件
        # if real_player_can_not_open_can_dummy == True and player_info.continueNotOpenCanDummy == True:
        #     player_info.nTurnWhenOpen = player_info.nTurnCount  # 同時達成原本一次清空的條件
        #     player_info.bIsOpened = True  # 開張了
        #     player_info.open_time = int(time.time())  # 紀錄開張瞬間
        #     # 如果出牌陣列有東西
        #     if player_info.nNotOpenCanDummy != None and len(player_info.nNotOpenCanDummy[1]) > 0:
        #         for i in player_info.nNotOpenCanDummy[1]:
        #             # 做完出牌操作還要再進來一次
        #             player_info.continueNotOpenCanDummy = True
        #             # 準備出牌了，將i從a[1]刪除，避免下次進來重複出同一組牌
        #             player_info.nNotOpenCanDummy[1].remove(i)
        #             # 允許出牌
        #             player_info.nOpAllow |= EnumGameOperation.nCombine
        #             # 進行強制出牌
        #             return seat_index, EnumGameOperation.nCombine, i
        #     # 如果插牌陣列有東西
        #     if player_info.nNotOpenCanDummy != None and len(player_info.nNotOpenCanDummy[2]) > 0:
        #         Four_of_a_kind = 999
        #         Full_house = 999
        #         card_serial = CardSerializer()
        #         for card_index in player_info.nNotOpenCanDummy[2]:  # 走訪插牌區的每張牌
        #             for beinsert_index, combo in self.mAllCombos.items():  # 走訪每種檯面組合
        #                 card_index_list = list(combo.keys())
        #                 card_index_list.append(card_index)
        #                 card_serial.Clear()
        #                 card_serial.AddBatch(card_index_list)
        #                 if card_serial.HasFullMatch(card_index_list):  # 如果可插牌
        #                     # 判斷可插組合為鐵支
        #                     if len(card_index_list) == 4 and card_index_list[0] % 16 == card_index_list[1] % 16:
        #                         Four_of_a_kind = beinsert_index  # 將65536檯面index取代Four_of_a_kind
        #                     # 判斷可插組合為順子
        #                     else:
        #                         Full_house = beinsert_index  # 將65536檯面index取代Full_house
        #             if Full_house != 999:  # 優先判斷檯面組合為順子時，先插進去
        #                 # 做完插牌操作還要再進來一次
        #                 player_info.continueNotOpenCanDummy = True
        #                 # 準備插牌了，將card_index從a[2]刪除，避免下次進來重複插同一張牌
        #                 player_info.nNotOpenCanDummy[2].remove(card_index)
        #                 # 允許插牌
        #                 player_info.nOpAllow |= EnumGameOperation.nInsert
        #                 return seat_index, EnumGameOperation.nInsert, [card_index, Full_house]
        #             elif Four_of_a_kind != 999:  # 檯面牌沒有順子，不能插時，才插鐵支檯面組合
        #                 # 做完插牌操作還要再進來一次
        #                 player_info.continueNotOpenCanDummy = True
        #                 # 準備插牌了，將card_index從a[2]刪除，避免下次進來重複插同一張牌
        #                 player_info.nNotOpenCanDummy[2].remove(card_index)
        #                 # 允許插牌
        #                 player_info.nOpAllow |= EnumGameOperation.nInsert
        #                 return seat_index, EnumGameOperation.nInsert, [card_index, Four_of_a_kind]
        #     # 如果棄牌陣列只有1張
        #     if player_info.nNotOpenCanDummy != None and len(player_info.nNotOpenCanDummy[3]) == 1:
        #         in_hand = list(player_info.InHand.keys())
        #         drop_card_index = 0
        #         if len(in_hand) > 0:
        #             drop_card_index = in_hand[len(in_hand) - 1]
        #         # 做完一次棄牌操作就不用再進來了
        #         player_info.continueNotOpenCanDummy = False
        #         player_info.nNotOpenCanDummy = None
        #         # 允許棄牌
        #         player_info.nOpAllow = EnumGameOperation.nDrop
        #         # 進行強制棄牌
        #         return seat_index, EnumGameOperation.nDrop, [drop_card_index]
        # 如果允許棄牌操作，強制棄牌
        if (player_info.OpAllow & EnumGameOperation.nDrop) != 0:
            in_hand = list(player_info.InHand.keys())
            drop_card_index = 0

            if len(in_hand) > 0:
                drop_card_index = self._choose_drop_card(player_info)  # 計算最大雜牌要自動丟棄
            return seat_index, EnumGameOperation.nDrop, [drop_card_index]
        # 如果允許抽牌操作，強制抽牌
        else:
            return seat_index, EnumGameOperation.nDraw, []

    def GetPlayerForceFold(self, seat_index):
        turn_cursor_seat_index = self.vPlayersOrder[self.nTurnCursor]
        if seat_index == turn_cursor_seat_index:  # 目前輪到誰，不可能發起比牌又要思考接受比牌
            return None, None, None
        else:
            return seat_index, EnumGameOperation.Fold, []

    def who_has_these_cards(self, params):  # 確認誰有這些牌
        # 先確定誰有這些牌-----
        seat_index = None
        for i in self.vPlayersOrder:  # 走訪所有玩家
            player_info = self.mPlayers[i]  # 每個玩家的info
            for j in params:
                if j in list(player_info.mInHand.keys()):  # 自動組牌的牌在這人的手牌內
                    seat_index = i  # 就是這位玩家操作整牌鍵
                    break

        # 再重組params從一維變成二維-----
        two_dimension = []
        one_dimension = []
        # [1, 2, 3, 99, 49, 50, 51, 99, 25, 26, 27, 99] to [[1, 2, 3], [49, 50, 51], [25, 26, 27]]
        for i in params:
            if i > 0 and i < 99:  # 正常牌面序號
                one_dimension.append(i)
            else:  # 異常牌面序號，作為分隔組合之使用
                two_dimension.append(one_dimension)
                one_dimension = []

        return seat_index, two_dimension

    def PlayerOperate(self, seat_index, op_type, op_data, android_round=False, auto_operate=False):
        """

        Args:
            android_round (bool): 判斷是否為機器人回合
            auto_operate (bool): 判斷是否為系統自動操作
        """

        uuid = self.mUsers[seat_index].UUID
        Log("Player operating:", seat_index, op_type, op_data)
        Log("Player:[%s] seat_index:[%d] op_type:[%d] op_data:" % (uuid, seat_index, op_type), op_data)
        if not self.bIsGaming:
            Warn("玩家[%s] 不在遊戲中" % (uuid))
            return False

        if self.bIsFinished:
            Warn("玩家[%s] 此局已結束" % (uuid))
            return False

        seat_index = int(seat_index)
        if seat_index < 0 or seat_index >= LogicConfig.nTotalSeats:
            Warn("玩家[%s] Invalid seat index!" % (uuid))
            return False

        # 不是接受比牌、也不是放棄比牌、也不是整牌鍵(自動組牌)
        fight_op_type_tp = (EnumGameOperation.Challenge, EnumGameOperation.Fold, EnumGameOperation.GroupReorganize)
        cur_turn_seat_index = self.vPlayersOrder[self.nTurnCursor]
        if seat_index != cur_turn_seat_index and op_type not in fight_op_type_tp:
            Warn("玩家[%s] Turn error, now it's [%d], isn't [%d]!" % (uuid, cur_turn_seat_index, seat_index))
            return False

        if op_type not in self.mOperationProc:
            Warn("玩家[%s] Invalid operation type!" % (uuid))
            return False

        player_info = self.mPlayers[seat_index]
        if not player_info.IsOpAllowed(op_type):
            Warn("玩家[%s] Operation not allowed!" % (uuid))
            return False
        # 是否為機器人回合
        if android_round == True:
            player_info.gamelogic_android_round = True

        player_info.set_auto_operate(auto_operate)

        fun = self.mOperationProc[op_type]
        return fun(player_info, op_data)

    def Announce(self, player_info, op_data): # op_data -> unused
        return player_info.Announce()

    # 交換牌組牌
    def MoveToNextDraw(self, nSrcIdx):
        nPos = -1
        for idx in range(self.nDeckCursor, len(self.vDeckOrder)):
            if self.vDeckOrder[idx] == nSrcIdx:
                nPos = idx
        if nPos > 0:
            self.vDeckOrder[nPos], self.vDeckOrder[self.nDeckCursor] \
                = self.vDeckOrder[self.nDeckCursor], self.vDeckOrder[nPos]

    def Draw(self, player_info, op_data): # op_data -> unused
        if op_data is not None and len(op_data) > 0:
            self.MoveToNextDraw(op_data[0])
        # 如果是真人玩家的回合，而且抽中壞牌率
        # 如果是真人玩家的回合，而且為vip玩家，而且在vip房內抽中vip壞牌率

        if (player_info.gamelogic_android_round == False and GetRndInt(1, 100) <= ServiceOpt.sBadDrawRate) \
            or (player_info.gamelogic_android_round == False and android.android_vip == True
                and GetRndInt(1, 100) <= ServiceOpt.sBadDrawRateVip):
            # 開啟反作弊抽牌規則
            vRelates = self.draw_cheating(player_info)
            if len(vRelates) > 0:  # 如果有許多無關的抽牌可選擇
                # 抽籤決定抽哪一張牌
                one_of_vRelates = vRelates[GetRndInt(0, len(vRelates) - 1)]
                # 抽到的牌與原本的牌組最上張交換
                self.MoveToNextDraw(one_of_vRelates)
        elif player_info.gamelogic_android_round == False and (50 < ServiceOpt.sBadDrawRate) or (android.android_vip == True and 50 < ServiceOpt.sBadDrawRateVip):
            vRelates = self.draw_cheating_A(player_info)
            if len(vRelates) > 0:  # 如果有許多無關的抽牌可選擇
                # 抽籤決定抽哪一張牌
                one_of_vRelates = vRelates[GetRndInt(0, len(vRelates) - 1)]
                # 抽到的牌與原本的牌組最上張交換
                self.MoveToNextDraw(one_of_vRelates)



        card_index = self.vDeckOrder[self.nDeckCursor]
        card_info = self.mDeck[card_index]
        is_ok = player_info.DrawCard(card_info)
        if not is_ok:
            return False
        self.nDeckCursor += 1
        self.mDeck.pop(card_index, None)
        # # 如果玩家未開張
        # if player_info.bIsOpened == False:
        #     # 預知是否未開張一次清空
        #     response_not_open_can_dummy = player_info.CheckNotOpenCanDummy(self.mAllCombos)
        #     # 如果預知能達成未開張一次清空
        #     if response_not_open_can_dummy != None:
        #         player_info.nNotOpenCanDummy = response_not_open_can_dummy
        #         # 允許操作：未開張一次清空
        #         player_info.nOpAllow |= EnumGameOperation.nNotOpenCanDummy
        #         # 如果機器人能達成未開張一次清空
        #         if player_info.gamelogic_android_round == True:
        #             player_info.bIsOpened = True
        #             player_info.open_time = int(time.time())  # 紀錄開張瞬間
        #             player_info.nOpAllow |= EnumGameOperation.nCombine
        #             player_info.nTurnWhenOpen = player_info.nTurnCount
        #             # 機器人不扣留任何一張可能被接金牌的牌
        #             player_info.detain_could_be_inserted = False
        # # 如果玩家已開張
        # else:
        player_info.has_drawed_or_picked = True  # 玩家本回合抽過牌了
        player_info.CheckAnyAction(self.mAllCombos)
        return True

    # 反作弊抽牌：先檢驗牌組與手牌或海底的「非」關聯性
    def draw_cheating(self, player_info):
        vMeIndexs = list(player_info.mInHand.keys())  # 手牌
        SeaBottomOrder = self.vSeaBottomOrder  # 海底牌
        vDeckRemain = self.vDeckOrder[self.nDeckCursor:]  # 剩餘的牌組
        Log("draw_cheating 剩餘的牌組:{}".format(vDeckRemain))
        # 準備一個作弊抽牌區
        mRelates = []
        Log("壞牌機率{}, vip壞牌機率{} 如果壞牌率>50 排除A".format(ServiceOpt.sBadDrawRate, ServiceOpt.sBadDrawRateVip))
        for nTryIdx in vDeckRemain:  # 走訪剩餘牌組
            if (50 < ServiceOpt.sBadDrawRate) or (android.android_vip == True and 50 < ServiceOpt.sBadDrawRateVip):
                if nTryIdx & 0x0f > 1 :
                    for _ in range(6):  # 走訪加入6次至作弊抽牌區，先以權重6倍作為基礎
                        mRelates.append(nTryIdx)
                else:
                    Log("draw_cheating 排除A:{}".format(nTryIdx))
            else:
                for _ in range(6):  # 走訪加入6次至作弊抽牌區，先以權重6倍作為基礎
                    mRelates.append(nTryIdx)

        if(len(mRelates) == 0):# 如果壞牌率>50 牌組全是A
            for _ in range(6):
                    mRelates.append(nTryIdx)

        Log("draw_cheating 作弊抽牌區:{}".format(mRelates))
        # 手牌聽搭或海底關聯
        for nTryIdx in vDeckRemain:  # 走訪剩餘牌組
            for idx in (vMeIndexs + [SeaBottomOrder[-1]]):  # 走訪手牌+海底牌末張
                # 牌組與手牌+海底牌是否關聯
                if self.TryRelateCombo(nTryIdx, idx):
                    if nTryIdx in mRelates:  # 如果作弊抽牌區有這張牌
                        # 關聯1次，刪除權重1倍，關聯6次以上，權重消失
                        mRelates.remove(nTryIdx)
        # 可插
        serial = CardSerializer()
        for unq_index, combo in self.mAllCombos.items():
            for nTryIdx in vDeckRemain:
                cindexlist = list(combo.keys())
                cindexlist.append(nTryIdx)
                serial.Clear()
                serial.AddBatch(cindexlist)
                # 牌組與插牌是否關聯
                if serial.HasFullMatch(cindexlist):
                    if nTryIdx in mRelates:  # 如果作弊抽牌區有這張牌
                        # 關聯1次，刪除權重1倍，關聯6次以上，權重消失
                        mRelates.remove(nTryIdx)
        return mRelates

    def draw_cheating_A(self, player_info):
        vDeckRemain = self.vDeckOrder[self.nDeckCursor:]  # 剩餘的牌組
        Log("draw_cheating_A 剩餘的牌組:{}".format(vDeckRemain))
        # 準備一個作弊抽牌區
        mRelates = []
        Log("壞牌機率{}, vip壞牌機率{} 如果壞牌率>50 排除A".format(ServiceOpt.sBadDrawRate, ServiceOpt.sBadDrawRateVip))
        for nTryIdx in vDeckRemain:  # 走訪剩餘牌組
            if (50 < ServiceOpt.sBadDrawRate) or (android.android_vip == True and 50 < ServiceOpt.sBadDrawRateVip):
                if nTryIdx & 0x0f > 1 :
                        mRelates.append(nTryIdx)
                else:
                    Log("draw_cheating_A 排除A:{}".format(nTryIdx))
            else:
                mRelates.append(nTryIdx)

        if(len(mRelates) == 0):# 如果壞牌率>50 牌組全是A
            mRelates.append(nTryIdx)

        return mRelates

    # 判斷兩張牌是否有關聯
    def TryRelateCombo(self, idx1, idx2):
        color1, value1 = Poker.Index2TypePoint(idx1)
        color2, value2 = Poker.Index2TypePoint(idx2)
        if value1 == value2:
            return True
        if color1 != color2:
            return False
        value1 = value1 if value1 != EnumPokerPoint.nAce else EnumPokerPoint.nSpecAce
        value2 = value2 if value2 != EnumPokerPoint.nAce else EnumPokerPoint.nSpecAce
        if abs(value1 - value2) <= 2:
            return True
        return False

    def Pick(self, player_info, op_data):  # op_data -> [sea_bottom_cursor, card_index...]
        """
        Args:
            op_data (list) : 本次操作所帶的資料
                index 0 的值代表海底的哪張牌（位址）
                其他代表要丟出的組合
        """
        sea_bottom_cursor = int(op_data[0])
        combine = op_data[1:]
        sea_bottom_count = len(self.vSeaBottomOrder)
        if sea_bottom_cursor < 0 or sea_bottom_cursor >= sea_bottom_count:
            return False
        need_picked = self.vSeaBottomOrder[sea_bottom_cursor:]
        picked_card_info = {}
        for card_index in need_picked:
            card_info = self.mSeaBottom[card_index]
            picked_card_info[card_index] = card_info

        is_ok = player_info.Pick(need_picked[0], picked_card_info, combine)
        if not is_ok:
            return False
        for card_index in need_picked:
            self.mSeaBottom.pop(card_index, None)
        self.vSeaBottomOrder = self.vSeaBottomOrder[:sea_bottom_cursor]
        last_new_combo_index = player_info.ComboCount - 1
        last_new_combo = player_info.Combos[last_new_combo_index]
        self.mAllCombos[self.GetComboUniqueIndex(player_info.SeatIndex, last_new_combo_index)] = last_new_combo

        self.CheckGameEnd(player_info)
        player_info.has_drawed_or_picked = True  # 玩家本回合撿過牌了
        player_info.CheckAnyAction(self.mAllCombos)
        return True

    def Combine(self, player_info, op_data):  # op_data -> [card_index...]
        # BOT 最後一組出牌不會留一張棄牌
        # inhadlst = list(player_info.InHand.keys())
        # if len(inhadlst) == len(op_data):
        #     while True:
        #         for i in range(len(inhadlst)):
        #             if inhadlst[i] not in op_data:
        #                 break
        #         if len(op_data) > LogicConfig.nMinContinuity:
        #             op_data.pop(0)
        #         else:
        #             return False
        #         break

        is_ok = player_info.Combine(op_data)
        if not is_ok:
            return False
        last_new_combo_index = player_info.ComboCount - 1
        last_new_combo = player_info.Combos[last_new_combo_index]
        self.mAllCombos[self.GetComboUniqueIndex(player_info.SeatIndex, last_new_combo_index)] = last_new_combo

        self.CheckGameEnd(player_info)
        player_info.CheckAnyAction(self.mAllCombos)
        return True

    def Insert(self, player_info, op_data):  # op_data -> [card_index, combo_unq_index]
        card_index = int(op_data[0])
        combo_unq_index = int(op_data[1])
        if combo_unq_index not in self.mAllCombos:
            return False
        target_seat_index, target_combo_index = self.SplitComboUniqueIndex(combo_unq_index)
        target_player_info = self.mPlayers[target_seat_index]
        is_ok = player_info.Insert(card_index, target_player_info, target_combo_index)
        if not is_ok:
            return False

        if target_player_info.nTurnCount % 2 == 0:
            target_player_info.even_turn_inserted_mark = 1  # 目標玩家的檯面牌被插上了牌
        else:
            target_player_info.odd_turn_inserted_mark = 1  # 目標玩家的檯面牌被插上了牌
        target_player_info.op_allow_fight = 0  # 被插牌且必須插上刀子

        self.CheckGameEnd(player_info)
        player_info.CheckAnyAction(self.mAllCombos)
        return True

    def Drop(self, player_info, op_data):  # op_data -> [drop_card_index]
        drop_card_index = int(op_data[0])
        card_info = player_info.Drop(drop_card_index)
        if card_info is None:
            Err("Drop, card_info is None")
            return False
        self.mSeaBottom[drop_card_index] = card_info
        self.vSeaBottomOrder.append(drop_card_index)
        # if len(player_info.InHand) > 0:
            # card_serial = CardSerializer()
            # for combo in self.mAllCombos.values():
            #     card_serial.Clear()
            #     card_index_list = list(combo.keys())
            #     card_index_list.append(drop_card_index)
            #     card_serial.AddBatch(card_index_list)
            #     if card_serial.HasFullMatch(card_index_list):
            #         player_info.event_accumulation += 1  # 個人累積事件+1
            #         break

            # card_serial.Clear()
            # card_serial.AddBatch(self.vSeaBottomOrder)
            # combos = card_serial.GetAllCombo(drop_card_index)
            # if len(combos) > 0:
            #     player_info.event_accumulation += 1  # 個人累積事件+1

        player_info.has_drawed_or_picked = False  # 玩家本回合結束，下一輪當然還沒抽牌或撿牌
        if not self.CheckGameEnd(player_info):  # 棄牌後，遊戲還沒結束時
            self.CalcNextTurnCursor(False)  # 輪到下一位
        return True

    def Group(self, player_info, op_data):
        if self.is_fight:  # 比牌時不能組牌
            return False

        is_ok = player_info.Group(op_data)
        if not is_ok:
            return False

        if player_info.has_drawed_or_picked:  # 組牌前已經抽過或撿過牌
            self.CheckGameEnd(player_info)  # 才去驗證遊戲是否結束

        player_info.CheckAnyAction(self.mAllCombos, SeaBottomOrder=self.vSeaBottomOrder)
        return True

    def UnGroup(self, player_info, op_data):
        if self.is_fight:  # 比牌時不能解散組牌
            return False

        is_ok = player_info.UnGroup(op_data)
        if not is_ok:
            return False

        player_info.CheckAnyAction(self.mAllCombos)
        return True

    def GroupReorganize(self, player_info, op_data):
        if self.is_fight:  # 比牌時整牌鍵自動重組失效
            return False

        is_ok = player_info.GroupReorganize(op_data)
        if not is_ok:
            return False

        if player_info.has_drawed_or_picked:  # 組牌前已經抽過或撿過牌
            self.CheckGameEnd(player_info)  # 才去驗證遊戲是否結束
        player_info.CheckAnyAction(self.mAllCombos)
        return True

    def Fight(self, player_info, op_data):
        is_ok = player_info.Fight()
        if not is_ok:
            return False

        self.is_fight = True

        for seat_index in self.vPlayersOrder:  # 走訪所有玩家
            if seat_index == self.nTurnCursor:  # 發起比牌的人不用處理
                continue

            player = self.mPlayers[seat_index]  # 每個玩家的info
            player.CheckAnyAction({}, self.is_fight)

        self.CheckGameEnd(player_info)
        return True

    def Challenge(self, player_info, op_data):
        is_ok = player_info.Challenge()
        if not is_ok:
            return False

        self.CheckGameEnd(player_info)
        return True

    def Fold(self, player_info, op_data):
        is_ok = player_info.Fold()
        if not is_ok:
            return False

        self.CheckGameEnd(player_info)
        return True

    def fight_end_check(self):
        """檢查是否結束比牌環節

        若不是比牌狀況下直接回傳 False
        若有玩家的比牌狀況為 0 （代表還沒回傳執行結果）回傳 False
        """
        if not self.is_fight:
            return False

        for seat_index in self.vPlayersOrder:
            player_info = self.mPlayers[seat_index]
            if player_info.fight_status == 0:
                return False

        return True

    def _get_winner_index(self, point_ls, fighter_index):
        """取得贏家座位 index

        找出點數最小者
        只有一名，則直接勝出
        有兩名，若有發起者，發起者輸，若無則進入比對
        有三名，發起者輸，剩餘兩名進入比對
        若沒有發起者（流局），有數名點數相同者直接進行比牌

        比對方式：
            雜牌張數小的贏
            依照順序比對卡牌點數較小者贏
            依照順序比對卡牌花色較小者贏

        Args:
            point_ls (list): 玩家點數，依照座位排序
            fighter_index (int): 發起者座位

        Returns:
            index (int): 贏家座位
        """
        min_point = min(point_ls)
        min_point_player_index_ls = []

        for seat_index, point in enumerate(point_ls):
            if min_point == point:
                min_point_player_index_ls.append(seat_index)

        min_point_player_count = len(min_point_player_index_ls)

        if min_point_player_count == 1:  # 沒平手，最小者獲勝
            return min_point_player_index_ls[0]

        elif fighter_index == -1 and min_point_player_count == 3:  # 流局且三人平手
            p_one_index = min_point_player_index_ls[0]
            p_two_index = min_point_player_index_ls[1]
            p_three_index = min_point_player_index_ls[2]

            p_one = self.mPlayers[p_one_index]
            p_two = self.mPlayers[p_two_index]
            p_three = self.mPlayers[p_three_index]

            p_one_card_index_ls = [index for index in p_one.get_in_hand_without_group()]
            p_two_card_index_ls = [index for index in p_two.get_in_hand_without_group()]
            p_three_card_index_ls = [index for index in p_three.get_in_hand_without_group()]

            compare_data_dc = {
                p_one_index: p_one_card_index_ls,
                p_two_index: p_two_card_index_ls,
                p_three_index: p_three_card_index_ls,
            }

            # 兩兩互相比較
            tmp_winner = self.who_has_the_smallest_card(p_one_index, p_two_index,
                                                      p_one_card_index_ls,
                                                      p_two_card_index_ls)
            
            winner = self.who_has_the_smallest_card(tmp_winner, p_three_index,
                                                    compare_data_dc[tmp_winner],
                                                    p_three_card_index_ls)
            return winner

        else:  # 2 人、3 人平手的情況
            if min_point_player_count == 3: # 3 人平手，發起者輸
                min_point_player_index_ls.remove(fighter_index)

            # 兩個平手且含發起者，發起者輸
            elif min_point_player_count == 2 and fighter_index in min_point_player_index_ls:
                if min_point_player_index_ls[0] == fighter_index:
                    return min_point_player_index_ls[1]
                else:
                    return min_point_player_index_ls[0]

            p_one_index = min_point_player_index_ls[0]
            p_two_index = min_point_player_index_ls[1]

            p_one = self.mPlayers[p_one_index]
            p_two = self.mPlayers[p_two_index]

            p_one_card_index_ls = [index for index in p_one.get_in_hand_without_group()]
            p_two_card_index_ls = [index for index in p_two.get_in_hand_without_group()]

            return self.who_has_the_smallest_card(p_one_index, p_two_index, p_one_card_index_ls, p_two_card_index_ls)

    def win_judgment_and_get_winner_seat(self, mode):
        """計算獲勝賠付點數，取得贏家座位

        根據獲勝的方式不同的計算方式

        Args:
            mode (str): 獲勝的方式

        Returns:
            winner_index (int): 贏家座位 index
        """
        winner_index = -1  # 贏家座號
        if mode == "tongits":
            for seat_index in self.vPlayersOrder:  # 走訪所有玩家
                player_info = self.mPlayers[seat_index]  # 每個玩家的info
                # 計算組牌區有幾張牌
                group_cards_amonuts = 0
                for i in player_info.group_combination:  # 走訪組牌區取得每一組合
                    for _ in i:  # 走訪組合取得每一張
                        group_cards_amonuts += 1

                # 手牌清零的贏家
                is_hand_winner = len(player_info.InHand) == 0
                # 雜牌清零的贏家
                is_messy_winner = len(player_info.InHand) - group_cards_amonuts == 0

                if is_hand_winner or is_messy_winner:
                    winner_index = seat_index
                    break

        elif mode == "fight":
            point_ls = []
            fighter_index = -1  # 發起者座位

            # 計算結算所需資料
            for seat_index in self.vPlayersOrder:  # 走訪所有玩家
                player_info = self.mPlayers[seat_index]  # 每個玩家的info
                point = player_info.get_current_point()
                point_ls.append(point)

                if player_info.fight_status == EnumGameOperation.Fight:
                    fighter_index = seat_index

            winner_index = self._get_winner_index(point_ls, fighter_index)
            winner_info = self.mPlayers[winner_index]  # 比牌贏家資訊

            for seat_index in self.vPlayersOrder:  # 走訪所有玩家
                player_info = self.mPlayers[seat_index]  # 每個玩家的info
                # 如果玩家還沒開張且手上有特殊組合
                if player_info.has_special_combine() and not player_info.bIsOpened:
                    player_info.nTurnWhenOpen = player_info.nTurnCount
                    player_info.bIsOpened = True  # 有特殊組合為開張
                    player_info.open_time = int(time.time())  # 紀錄開張瞬間

                is_winner = seat_index == winner_index

                # 發起比牌會進此判斷式
                if player_info.fight_status == EnumGameOperation.Fight:
                    if not is_winner:
                        player_info.ProcEventScore(EnumSpecEvent.nFight2)  # 發起比牌，輸了
                        winner_info.ProcEventScore(EnumSpecEvent.nChallenge1)  # 對方接受比牌，贏了

                # 放棄比牌會進此判斷式
                elif player_info.fight_status == EnumGameOperation.Fold:
                    if player_info.bIsOpened:  # 已開張，才是放棄比牌事件；未開張，就只有未開張事件
                        player_info.ProcEventScore(EnumSpecEvent.nFord1)  # 放棄比牌，輸了
                        winner_info.ProcEventScore(EnumSpecEvent.nFord2)  # 有人放棄比牌，則獲勝方得分

                # 接受比牌會進此判斷式
                elif player_info.fight_status == EnumGameOperation.Challenge:
                    if not is_winner:
                        player_info.ProcEventScore(EnumSpecEvent.nChallenge2)  # 接受比牌，輸了
                        if winner_info.fight_status == EnumGameOperation.Fight:
                            winner_info.ProcEventScore(EnumSpecEvent.nFight1)  # 對方發起比牌，贏了
                        else:
                            winner_info.ProcEventScore(EnumSpecEvent.nChallenge1)  # 對方接受比牌，贏了

        return winner_index

    def CheckGameEnd(self, player_info):
        # 計算組牌區有幾張牌
        group_cards_amonuts = 0
        for i in player_info.group_combination:  # 走訪組牌區取得每一組合
            for _ in i:  # 走訪組合取得每一張
                group_cards_amonuts += 1

        finish_cond = 0
        if len(player_info.InHand) == 0:  # 手牌清零：tongits
            finish_cond += 1
            if not player_info.bIsOpened:  # 如果還沒開張
                player_info.nTurnWhenOpen = player_info.nTurnCount
                player_info.bIsOpened = True  # 插牌視為開張
                player_info.open_time = int(time.time())  # 紀錄開張瞬間
        elif len(self.mDeck) == 0:  # 海底牌組清零：流局
            finish_cond += 2
        elif self.fight_end_check():  # 比牌
            finish_cond += 3
        elif len(player_info.InHand) - group_cards_amonuts == 0:  # 雜牌清零：tongits
            finish_cond += 4
            if not player_info.bIsOpened:  # 如果還沒開張
                player_info.nTurnWhenOpen = player_info.nTurnCount
                player_info.bIsOpened = True  # 插牌視為開張
                player_info.open_time = int(time.time())  # 紀錄開張瞬間

        winner_info = None  # 獲勝者的play_info
        if finish_cond > 0:
            self.bIsFinished = True

            # 計算基礎賠付 & 比牌賠付
            if finish_cond == 1:  # 胡牌時
                winner_seat_index = self.win_judgment_and_get_winner_seat("tongits")
            elif finish_cond == 2:  # 流局時
                winner_seat_index = self.win_judgment_and_get_winner_seat("fight")
            elif finish_cond == 3:  # 有人發起比牌時
                winner_seat_index = self.win_judgment_and_get_winner_seat("fight")
            else:  # 雜牌清零時
                winner_seat_index = self.win_judgment_and_get_winner_seat("tongits")

            if winner_seat_index >= 0 and winner_seat_index < 3:
                winner_info = self.mPlayers[winner_seat_index]

            for seat_index in self.vPlayersOrder:  # 走訪所有玩家
                tmp_player_info = self.mPlayers[seat_index]  # 每個玩家的info
                tmp_other_1 = None
                tmp_other_2 = None

                for i in range(len(self.vPlayersOrder)):
                    if i != seat_index:  # 如果座號不是發生事件的那一個人，就另外給他互補事件
                        if tmp_other_1 == None:
                            tmp_other_1 = self.mPlayers[i]
                        elif tmp_other_2 == None:
                            tmp_other_2 = self.mPlayers[i]

                tmp_player_info.RoundEnd(tmp_other_1, tmp_other_2, winner_info, finish_cond)
            # 全部都計算完成，下面開始排序==================
            dict_list = []  # 新增list裡面包dict型別
            oop_list = []   # 新增list裡面包oop型別
            for seat_index in self.vPlayersOrder:
                each_player = self.mPlayers[seat_index]
                each_player_dict = eval(str(each_player))  # 將oop型別強制轉換成dict
                dict_list.append(each_player_dict)   # 加入用來排序的列表
                oop_list.append(each_player)         # 加入最後依座號來取得原本oop資料的列表
            # 排序方式：分數高 → 出插撿牌的張數多 → 手牌剩餘少 → 開張順序 → 座號大
            rank_list = sorted(dict_list, key=lambda x:(x['nGainedScore']-x['nLostScore'], x['nComboSheetsAmounts'], -len(x['mInHand']), -x['open_time'], x['nSeatIndex']))
            # 走訪已排序的玩家資訊
            for i in rank_list:
                # 走訪未排序的玩家資訊
                for j in oop_list:
                    # 用相同座號取出排序為第N名的玩家
                    if i['nSeatIndex'] == j.SeatIndex:
                        self.vLevel.append(j)
            return True
        return False

# ================================================================================================================ #
# ================================================================================================================ #
# ================================================================================================================ #
def GetOpenedString(player_info):
    if player_info.IsOpened:
        return "已开张"
    else:
        return "未开张"

def GetOpAllowString(player_info):
    op_str = ""
    if (player_info.OpAllow & EnumGameOperation.nAnnounce) != 0:
        op_str += "-宣告 "
    if (player_info.OpAllow & EnumGameOperation.nDraw) != 0:
        op_str += "-可抽 "
    if (player_info.OpAllow & EnumGameOperation.nPick) != 0:
        op_str += "-可捡 "
    if (player_info.OpAllow & EnumGameOperation.nCombine) != 0:
        op_str += "-可搭 "
    if (player_info.OpAllow & EnumGameOperation.nInsert) != 0:
        op_str += "-可插 "
    if (player_info.OpAllow & EnumGameOperation.nDrop) != 0:
        op_str += "-可弃 "
    # if (player_info.OpAllow & EnumGameOperation.nNotOpenCanDummy) != 0:
    #     op_str += "-可未開張一次清空 "
    if (player_info.OpAllow & EnumGameOperation.Group) != 0:
        op_str += "-可組 "
    if (player_info.OpAllow & EnumGameOperation.UnGroup) != 0:
        op_str += "-可拆組 "
    if (player_info.OpAllow & EnumGameOperation.Fight) != 0:
        op_str += "-可比牌 "
    if (player_info.OpAllow & EnumGameOperation.Challenge) != 0:
        op_str += "-可接受比牌 "
    if (player_info.OpAllow & EnumGameOperation.Fold) != 0:
        op_str += "-可放棄比牌 "
    return op_str

def GetCardGraph(t, p):
    point_graph = [
    "",
    "Ａ",
    "２",
    "３",
    "４",
    "５",
    "６",
    "７",
    "８",
    "９",
    "10",
    "Ｊ",
    "Ｑ",
    "Ｋ",
    ]
    tmp = ""
    if t == EnumPokerType.nDiamonds:
        tmp += "\033[1;31;47m♦"
    elif t == EnumPokerType.nClubs:
        tmp += "\033[1;30;47m♣"
    elif t == EnumPokerType.nHearts:
        tmp += "\033[1;31;47m♥"
    elif t == EnumPokerType.nSpade:
        tmp += "\033[1;30;47m♠"
    elif t == EnumPokerType.nJoker:
        if p == 1:
            return "\033[1;30;47mJOKER\033[0m "
        else:
            return "\033[1;31;47mJOKER\033[0m "

    return tmp + point_graph[p] + "\033[0m "

def CvtCardIndexToGraph(card_index_list):
    tmp = ""
    for card_index in card_index_list:
        t, p = Poker.Index2TypePoint(card_index)
        tmp += GetCardGraph(t, p)
    return "[ " + tmp + "]"

def ShowStatus(logic, StrRoundSign=-1, mUsers=None):
    Log("")
    if StrRoundSign != -1:
        logic.UpdateStrRoundSign(StrRoundSign)
    if mUsers != None:
        logic.UpdatemUsers(mUsers)
    Log(">>>>>>>>>>>>>>" + str(logic.StrRoundSign) + ">>>>>>>>>>>>>>")
    Log("海底:", CvtCardIndexToGraph(logic.vSeaBottomOrder))
    deck_remain = logic.vDeckOrder[logic.nDeckCursor:]
    Log("牌库:", CvtCardIndexToGraph(deck_remain))
    Log("")
    for seat_index in logic.vPlayersOrder:
        player_info = logic.mPlayers[seat_index]
        Log("玩家[%s]座位[%.2d][%s][Gained:%d][Lost:%d]" % (logic.mUsers[seat_index].UUID, seat_index, GetOpenedString(player_info), player_info.GainedScore, player_info.LostScore))
        in_hand = list(player_info.InHand.keys())
        in_hand.sort()
        Log("    手牌:", CvtCardIndexToGraph(in_hand))
        for combo_index in player_info.Combos:
            combo = list(player_info.Combos[combo_index].keys())
            combo.sort()
            Log("    搭%.2d:" % combo_index, CvtCardIndexToGraph(combo))

        for group_dc in player_info.group_combination:
            group_ls = sorted(list(group_dc))

            Log("    組合:", CvtCardIndexToGraph(group_ls))
        Log("    目前點數:", player_info.get_current_point())

        card_serial = CardSerializer()
        card_serial.AddBatch(in_hand)
        combos = card_serial.GetAllCombo()
        for combo in combos:
            combo_list = list(combo.keys())
            combo_list.sort()
            Log("      --手牌可搭:", CvtCardIndexToGraph(combo_list))
        Log("")
    turn_seat_index = logic.CurrentTurn
    Log("回合玩家[%.2d]可操作项:" % turn_seat_index, GetOpAllowString(logic.mPlayers[turn_seat_index]))
    Log("<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    Log("")

if __name__ == "__main__":
    import time
    def LocalTest():
        LogicConfig.Reset2Default()
        # LogicConfig.Preview()

        logic = GameLogic()
        rand_player = [
            0x01 | 0x02,
            0x01 | 0x04,
            0x01 | 0x08,
            0x02 | 0x04,
            0x02 | 0x08,
            0x04 | 0x08,
            0x01 | 0x02 | 0x04,
            0x01 | 0x02 | 0x04,
            0x01 | 0x02 | 0x08,
            0x01 | 0x02 | 0x08,
            0x02 | 0x04 | 0x08,
            0x02 | 0x04 | 0x08,
            0x01 | 0x02 | 0x04 | 0x08,
            0x01 | 0x02 | 0x04 | 0x08,
            0x01 | 0x02 | 0x04 | 0x08,
            0x01 | 0x02 | 0x04 | 0x08,
            0x01 | 0x02 | 0x04 | 0x08,
            0x01 | 0x02 | 0x04 | 0x08,
        ]
        rand_group_index = GetRndInt(0, len(rand_player) - 1)
        rand_group = rand_player[rand_group_index]

        seat_index = 0
        for i in range(LogicConfig.nTotalSeats):  # 總共可坐多少座位
            bit_pos = 1 << seat_index
            if (rand_group & bit_pos) != 0:
                logic.PlayerJoinIn(seat_index)
            seat_index += 1
        start_time = time.time()
        logic.GameStart()
        elapse = time.time() - start_time
        Log("初始化用时:%fus" % (elapse * 1000000))
        Log("游戏开始...")
        Log("参与者数量:", logic.nJoinedCount)
        ShowStatus(logic)

    LocalTest()
else:
    pass