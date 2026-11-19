package lottery

import (
	"fish-shrimp-crab-game-server/application/gamesettingFS"
	"fish-shrimp-crab-game-server/application/lobbysettingFS"
	lottery_proto "fish-shrimp-crab-game-server/application/lottery/proto"
	"fish-shrimp-crab-game-server/application/playerdata"
	bet_proto "fish-shrimp-crab-game-server/domain/bet/proto"
	commonFS_proto "fish-shrimp-crab-game-server/models/proto"
	"fmt" //--
	"math"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	EMSGID_eLotteryResult          = "EMSGID_eResult"
	EMSGID_eBroadcastLotteryResult = "EMSGID_eBroadcastLotteryResult"
)

var Service = &service{
	Id: "LotteryService",
}

type service struct {
	Id string
}

func (s *service) Result(bets map[string][]bet_proto.BetCall, result [3]int32, gameRoomUuid string) {
	//[雞，葫蘆，蝦，虎，魚，蟹]

	betIndex := s.calculateBetIndex(result)

	fmt.Printf("QA LOG ---> : ----------not in vip----------Dices = %v----------\n", result)//--

	broadcastResult := &lottery_proto.BroadcastResult{
		Msgid:      commonFS_proto.EMSGID_eBroadcastLotteryResult,
		WinIndexes: betIndex[:],
	}

	for playerUuid, betCalls := range bets {
		fee := lobbysettingFS.Service.Fee(playerUuid)

		totalCost := 0
		totalWin := 0 //含本金的贏分
		for _, betCall := range betCalls {
			betAreaRate := betIndex[int(betCall.BetType)]                      //賠率
			betCost := gamesettingFS.Service.Bet(playerUuid, betCall.BetIndex) //押注面額
			gameRate := gamesettingFS.Service.Rate(playerUuid)                 //房間的比例
			bet := int(betCost * gameRate)                                     //押注面額*比例 = 真正的押注金

			totalCost += bet
			// 賠分不含本金在內
			if betAreaRate >= 1 {
				totalWin += int(betAreaRate)*bet + bet
			}
		}

		//分數加回錢包
		profit := totalWin - totalCost //尚未抽水的利潤
		feeProfit := 0
		if profit > 0 { //整體是贏的，贏分會扣抽水
			feePercent := float64(100-fee) / math.Floor(100)
			feeProfit = int(math.Round(float64(profit) * feePercent)) //抽水後的利潤
			feeTotalWin := totalCost + feeProfit                      //已抽水後的贏分
			wallet.Service.IncreaseBalance(playerUuid, "", uint64(feeTotalWin))
		} else { //整體不輸不贏或輸分，就不扣抽水了
			wallet.Service.IncreaseBalance(playerUuid, "", uint64(totalWin))
		}

		if betCalls != nil {
			result := s.eResult(playerUuid, betCalls, totalWin, totalCost, feeProfit)
			broadcastResult.Results = append(broadcastResult.Results, result)
		}
	}
	bytes, _ := proto.Marshal(broadcastResult)

	flux.Send(EMSGID_eBroadcastLotteryResult, s.Id, gameRoomUuid, bytes, bets, result)
}

func (s *service) VipResult(bets map[string][]bet_proto.BetCall, result [][3]int32, gameRoomUuid, vipPlayerUuid string, reRollTimes int) (minTotalWinIndex int) {
	//[雞，葫蘆，蝦，虎，魚，蟹]

	var allBetIndex [][24]int32
	minTotalWin := int(^uint(0) >> 1) //最大int值

	fmt.Printf("QA LOG ---> : -----------------------------reRollTimes = %d-----------------------------------------------------------------------------------------------\n", reRollTimes) //--
	for i := 0; i < reRollTimes; i++ {
		betIndex := s.calculateBetIndex(result[i])
		allBetIndex = append(allBetIndex, betIndex)

		betCalls := bets[vipPlayerUuid]

		totalWin := 0 //含本金的贏分
		for _, betCall := range betCalls {
			betAreaRate := betIndex[int(betCall.BetType)]                         //賠率
			betCost := gamesettingFS.Service.Bet(vipPlayerUuid, betCall.BetIndex) //押注面額
			gameRate := gamesettingFS.Service.Rate(vipPlayerUuid)                 //房間的比例
			bet := int(betCost * gameRate)                                        //押注面額*比例 = 真正的押注金

			// 賠分不含本金在內
			if betAreaRate >= 1 {
				totalWin += int(betAreaRate)*bet + bet
			}
		}
		//取最小贏分索引
		if totalWin < minTotalWin {
			minTotalWin = totalWin
			minTotalWinIndex = i
		}
		fmt.Printf("QA LOG ---> Times : %2d   Dices = %v   betIndex = %v   totalWin = %d \n", i+1, result[i], betIndex, totalWin) //QA test LOG

	}
	fmt.Printf("QA LOG ---> : -----------------------------Times = %2d   Dices = %v   totalWin = %d------------------------------------------------------------------\n", minTotalWinIndex+1, result[minTotalWinIndex], minTotalWin)//--

	broadcastResult := &lottery_proto.BroadcastResult{
		Msgid:      commonFS_proto.EMSGID_eBroadcastLotteryResult,
		WinIndexes: allBetIndex[minTotalWinIndex][:],
	}

	for playerUuid, betCalls := range bets {
		fee := lobbysettingFS.Service.Fee(playerUuid)

		totalCost := 0
		totalWin := 0 //含本金的贏分
		for _, betCall := range betCalls {
			betAreaRate := allBetIndex[minTotalWinIndex][int(betCall.BetType)] //賠率
			betCost := gamesettingFS.Service.Bet(playerUuid, betCall.BetIndex) //押注面額
			gameRate := gamesettingFS.Service.Rate(playerUuid)                 //房間的比例
			bet := int(betCost * gameRate)                                     //押注面額*比例 = 真正的押注金

			totalCost += bet
			// 賠分不含本金在內
			if betAreaRate >= 1 {
				totalWin += int(betAreaRate)*bet + bet
			}
		}

		//分數加回錢包
		profit := totalWin - totalCost //尚未抽水的利潤
		feeProfit := 0
		if profit > 0 { //整體是贏的，贏分會扣抽水
			feePercent := float64(100-fee) / math.Floor(100)
			feeProfit = int(math.Round(float64(profit) * feePercent)) //抽水後的利潤
			feeTotalWin := totalCost + feeProfit                      //已抽水後的贏分
			wallet.Service.IncreaseBalance(playerUuid, "", uint64(feeTotalWin))
		} else { //整體不輸不贏或輸分，就不扣抽水了
			wallet.Service.IncreaseBalance(playerUuid, "", uint64(totalWin))
		}

		if betCalls != nil {
			result := s.eResult(playerUuid, betCalls, totalWin, totalCost, feeProfit)
			broadcastResult.Results = append(broadcastResult.Results, result)
		}
	}
	bytes, _ := proto.Marshal(broadcastResult)

	flux.Send(EMSGID_eBroadcastLotteryResult, s.Id, gameRoomUuid, bytes, bets, result[minTotalWinIndex])

	return minTotalWinIndex
}

func (s *service) eResult(playerUuid string, calls []bet_proto.BetCall, win int, cost int, feeProfit int) *lottery_proto.Result {
	gameDataResult := s.createResult(playerUuid, calls, win, cost)
	playerdata.Service.SaveUserGameData(playerUuid, calls, win, cost, gameDataResult)

	//發送結果至前端
	frontEndResult := s.createResult(playerUuid, calls, win, cost)
	if win > cost {
		frontEndResult.Pay = uint64(feeProfit)
	}
	bytes, _ := proto.Marshal(frontEndResult)
	// logger.Service.Zap.Infow("EMSGID_eLotteryResult",
	// 	"player:", playerUuid,
	// 	"balance:", balance,
	// )
	playerResult := make(map[string]uint64)
	playerResult["total_Bet"] = uint64(cost)
	if (win - cost) > 0 {
		playerResult["total_Win"] = uint64(cost) + frontEndResult.Pay
	} else {
		playerResult["total_Win"] = uint64(win)
	}

	flux.Send(EMSGID_eLotteryResult, s.Id, playerUuid, bytes, playerResult)

	return gameDataResult
}

//建立遊戲紀錄
func (s *service) createResult(playerUuid string, calls []bet_proto.BetCall, win int, cost int) *lottery_proto.Result {
	r := &lottery_proto.Result{
		Msgid:         commonFS_proto.EMSGID_eLotteryResult,
		Seat:          calls[0].Seat,
		Pay:           0,
		Status:        0,
		PlayerBalance: 0,
	}
	if win > cost {
		r.Pay = uint64(win - cost)
		r.Status = int32(lottery_proto.Result_WIN)
	}
	if cost > win {
		r.Pay = uint64(cost - win)
		r.Status = int32(lottery_proto.Result_LOSE)
	}
	if win == cost {
		r.Status = int32(lottery_proto.Result_TIE)
	}
	balance, _ := wallet.Service.Balance(playerUuid)
	r.PlayerBalance = balance
	//bytes, _ := proto.Marshal(r)
	//flux.Send(EMSGID_eLotteryResult, s.Id, playerUuid, bytes)
	//playerdata.Service.SaveUserGameData(playerUuid, calls, win, cost, r)
	return r
}

func (s *service) calculateBetIndex(result [3]int32) (betIndex[24]int32) {
	// 各個骰面出現的次數
	count := [6]int{0, 0, 0, 0, 0, 0}

	for i := range result {
		count[result[i]]++
	}

	// 單個圖案(注區18 ~ 23)
	for i := range count {
		if count[i] != 0 {
			betIndex[i+18] = int32(count[i])
		}
	}

	// 三個圖案(注區1 ~ 3)
	// 注區一：虎+雞+魚
	betArea1 := []int{0, 3, 4}
	betArea1Count := 0
	for _, i := range betArea1 {
		if count[i] != 0 {
			betArea1Count++
		}
	}
	if betArea1Count == 2 {
		betIndex[0] = 1
	}
	if betArea1Count == 3 {
		betIndex[0] = 5
	}

	// 注區二：虎+葫蘆+蟹
	betArea2 := []int{1, 3, 5}
	betArea2Count := 0
	for _, i := range betArea2 {
		if count[i] != 0 {
			betArea2Count++
		}
	}
	if betArea2Count == 2 {
		betIndex[1] = 1
	}
	if betArea2Count == 3 {
		betIndex[1] = 5
	}

	// 注區三：魚+蝦+蟹
	betArea3 := []int{2, 4, 5}
	betArea3Count := 0
	for _, i := range betArea3 {
		if count[i] != 0 {
			betArea3Count++
		}
	}
	if betArea3Count == 2 {
		betIndex[2] = 1
	}
	if betArea3Count == 3 {
		betIndex[2] = 5
	}

	// 雙圖案
	// 注區四：雞+蝦
	betArea4 := []int{0, 2}
	betArea4Count := 0
	if count[betArea4[0]] > 0 && count[betArea4[1]] > 0 {
		for _, i := range betArea4 {
			if count[i] > 0 {
				betArea4Count += count[i]
			}
		}
		if betArea4Count == 2 {
			betIndex[3] = 5
		}
		if betArea4Count == 3 {
			betIndex[3] = 7
		}
	}

	// 注區五：虎+蝦
	betArea5 := []int{2, 3}
	betArea5Count := 0
	if count[betArea5[0]] > 0 && count[betArea5[1]] > 0 {
		for _, i := range betArea5 {
			if count[i] > 0 {
				betArea5Count += count[i]
			}
		}
		if betArea5Count == 2 {
			betIndex[4] = 5
		}
		if betArea5Count == 3 {
			betIndex[4] = 7
		}
	}

	// 注區六：虎+葫蘆
	betArea6 := []int{1, 3}
	betArea6Count := 0
	if count[betArea6[0]] > 0 && count[betArea6[1]] > 0 {
		for _, i := range betArea6 {
			if count[i] > 0 {
				betArea6Count += count[i]
			}
		}
		if betArea6Count == 2 {
			betIndex[5] = 5
		}
		if betArea6Count == 3 {
			betIndex[5] = 7
		}
	}

	// 注區七：葫蘆+蟹
	betArea7 := []int{1, 5}
	betArea7Count := 0
	if count[betArea7[0]] > 0 && count[betArea7[1]] > 0 {
		for _, i := range betArea7 {
			if count[i] > 0 {
				betArea7Count += count[i]
			}
		}
		if betArea7Count == 2 {
			betIndex[6] = 5
		}
		if betArea7Count == 3 {
			betIndex[6] = 7
		}
	}

	// 注區八：魚+蝦
	betArea8 := []int{2, 4}
	betArea8Count := 0
	if count[betArea8[0]] > 0 && count[betArea8[1]] > 0 {
		for _, i := range betArea8 {
			if count[i] > 0 {
				betArea8Count += count[i]
			}
		}
		if betArea8Count == 2 {
			betIndex[7] = 5
		}
		if betArea8Count == 3 {
			betIndex[7] = 7
		}
	}

	// 注區九：魚+雞
	betArea9 := []int{0, 4}
	betArea9Count := 0
	if count[betArea9[0]] > 0 && count[betArea9[1]] > 0 {
		for _, i := range betArea9 {
			if count[i] > 0 {
				betArea9Count += count[i]
			}
		}
		if betArea9Count == 2 {
			betIndex[8] = 5
		}
		if betArea9Count == 3 {
			betIndex[8] = 7
		}
	}

	// 注區十：虎+蟹
	betArea10 := []int{3, 5}
	betArea10Count := 0
	if count[betArea10[0]] > 0 && count[betArea10[1]] > 0 {
		for _, i := range betArea10 {
			if count[i] > 0 {
				betArea10Count += count[i]
			}
		}
		if betArea10Count == 2 {
			betIndex[9] = 5
		}
		if betArea10Count == 3 {
			betIndex[9] = 7
		}
	}

	// 注區十一：雞+蟹
	betArea11 := []int{0, 5}
	betArea11Count := 0
	if count[betArea11[0]] > 0 && count[betArea11[1]] > 0 {
		for _, i := range betArea11 {
			if count[i] > 0 {
				betArea11Count += count[i]
			}
		}
		if betArea11Count == 2 {
			betIndex[10] = 5
		}
		if betArea11Count == 3 {
			betIndex[10] = 7
		}
	}

	// 注區十二：雞+虎
	betArea12 := []int{0, 3}
	betArea12Count := 0
	if count[betArea12[0]] > 0 && count[betArea12[1]] > 0 {
		for _, i := range betArea12 {
			if count[i] > 0 {
				betArea12Count += count[i]
			}
		}
		if betArea12Count == 2 {
			betIndex[11] = 5
		}
		if betArea12Count == 3 {
			betIndex[11] = 7
		}
	}

	// 注區十三：雞+葫蘆
	betArea13 := []int{0, 1}
	betArea13Count := 0
	if count[betArea13[0]] > 0 && count[betArea13[1]] > 0 {
		for _, i := range betArea13 {
			if count[i] > 0 {
				betArea13Count += count[i]
			}
		}
		if betArea13Count == 2 {
			betIndex[12] = 5
		}
		if betArea13Count == 3 {
			betIndex[12] = 7
		}
	}

	// 注區十四：虎+魚
	betArea14 := []int{3, 4}
	betArea14Count := 0
	if count[betArea14[0]] > 0 && count[betArea14[1]] > 0 {
		for _, i := range betArea14 {
			if count[i] > 0 {
				betArea14Count += count[i]
			}
		}
		if betArea14Count == 2 {
			betIndex[13] = 5
		}
		if betArea14Count == 3 {
			betIndex[13] = 7
		}
	}

	// 注區十五：葫蘆+魚
	betArea15 := []int{1, 4}
	betArea15Count := 0
	if count[betArea15[0]] > 0 && count[betArea15[1]] > 0 {
		for _, i := range betArea15 {
			if count[i] > 0 {
				betArea15Count += count[i]
			}
		}
		if betArea15Count == 2 {
			betIndex[14] = 5
		}
		if betArea15Count == 3 {
			betIndex[14] = 7
		}
	}

	// 注區十六：葫蘆+蝦
	betArea16 := []int{1, 2}
	betArea16Count := 0
	if count[betArea16[0]] > 0 && count[betArea16[1]] > 0 {
		for _, i := range betArea16 {
			if count[i] > 0 {
				betArea16Count += count[i]
			}
		}
		if betArea16Count == 2 {
			betIndex[15] = 5
		}
		if betArea16Count == 3 {
			betIndex[15] = 7
		}
	}

	// 注區十七：魚+蟹
	betArea17 := []int{4, 5}
	betArea17Count := 0
	if count[betArea17[0]] > 0 && count[betArea17[1]] > 0 {
		for _, i := range betArea17 {
			if count[i] > 0 {
				betArea17Count += count[i]
			}
		}
		if betArea17Count == 2 {
			betIndex[16] = 5
		}
		if betArea17Count == 3 {
			betIndex[16] = 7
		}
	}

	// 注區十八：蝦+蟹
	betArea18 := []int{2, 5}
	betArea18Count := 0
	if count[betArea18[0]] > 0 && count[betArea18[1]] > 0 {
		for _, i := range betArea18 {
			if count[i] > 0 {
				betArea18Count += count[i]
			}
		}
		if betArea18Count == 2 {
			betIndex[17] = 5
		}
		if betArea18Count == 3 {
			betIndex[17] = 7
		}
	}
	return betIndex
}
