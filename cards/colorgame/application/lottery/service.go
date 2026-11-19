package lottery

import (
	"colorgame-game-server/application/gamesettingFS"
	lottery_proto "colorgame-game-server/application/lottery/proto"
	"colorgame-game-server/application/playerdata"
	bet_proto "colorgame-game-server/domain/bet/proto"
	"colorgame-game-server/domain/probability"
	commonFS_proto "colorgame-game-server/models/proto"
	"fmt" //--
	"math/rand"
	"sort"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"

	rand1 "crypto/rand"
	"math/big"

	"gitlab.iplaystar.net/game-server/rng"
)

const (
	EMSGID_eLotteryResult          = "EMSGID_eLotteryResult"
	EMSGID_eBroadcastLotteryResult = "EMSGID_eBroadcastLotteryResult"
	MAX_BET_TYPE                   = 6 //最大押注區的號碼
)

var Service = &service{
	Id: "LotteryService",
}

type service struct {
	Id string
}

var Win_list map[int]int
var Lose_list map[int]int
var Win_Count map[int]int
var Lose_Count map[int]int
var BetAreaRate map[int]int

func (s *service) Result(bets map[string][]bet_proto.BetCall, result [3]int32, chosenColor probability.ColorWeight, gameRoomUuid, fakeRoomId string, isSimulation bool, simulation_block, simulation_bet int, jsonPath string) (chosenMultiple int) {
	//[黃0，白1，粉2，藍3，紅4，綠5]()

	//計算顏色出現的次數
	colorNumResult := [6]int{}
	for diceResultIndex := 0; diceResultIndex < len(result); diceResultIndex++ { //分析三次開骰的結果
		for colorIndex := 0; colorIndex < 6; colorIndex++ {
			if result[diceResultIndex] == int32(colorIndex) {
				colorNumResult[colorIndex]++
				break
			}
		}
	}

	//取得賠率物件
	combControl := probability.CombServie.GetCombControl(jsonPath)

	//選定倍率
	var multipleWeightValue []int //倍率權重植
	for _, multipleWeight := range chosenColor.Multiples {
		multipleWeightValue = append(multipleWeightValue, multipleWeight.Weight)
	}

	randomMultipleIndex := getRandomIndexByWeight(multipleWeightValue)
	chosenMultiple = chosenColor.Multiples[randomMultipleIndex].Multiple

	// 各個注區的賠率
	betIndex := [6]int32{0, 0, 0, 0, 0, 0}

	//計算賠率
	for colorI, times := range colorNumResult {
		if times == 1 {
			betIndex[colorI] = int32(combControl.HITX1)
		} else if times == 2 {
			betIndex[colorI] = int32(combControl.HITX2)
		} else if times == 3 {
			//結果
			betIndex[colorI] = int32(chosenMultiple)

		}

		//需扣掉本金
		if betIndex[colorI] != 0 {
			betIndex[colorI] -= 1
		}
	}
	fmt.Printf("QA LOG ---> : ----------not in vip----------Dices = %v----------\n", result) //--

	//印賠率結果
	logger.Service.Zap.Infow("gameRoomBetIndex", "gameRoomUuid", gameRoomUuid, "betIndex", betIndex)

	if !isSimulation {

		//分析所有的押注贏分
		broadcastResult := &lottery_proto.BroadcastResult{
			Msgid:      commonFS_proto.EMSGID_eBroadcastLotteryResult,
			WinIndexes: betIndex[:],
		}

		for playerUuid, betCalls := range bets {
			var totalCost uint64 = 0
			var totalWin uint64 = 0 //含本金的贏分
			for _, betCall := range betCalls {
				betAreaRate := betIndex[int(betCall.BetType)]                      //賠率
				betCost := gamesettingFS.Service.Bet(playerUuid, betCall.BetIndex) //押注面額
				gameRate := gamesettingFS.Service.Rate(playerUuid)                 //房間的比例
				bet := uint64(betCost * gameRate)                                  //押注面額*比例 = 真正的押注金

				totalCost += bet
				// 賠分不含本金在內
				if betAreaRate >= 1 {
					totalWin += uint64(betAreaRate)*bet + bet
				}
			}

			//分數加回錢包
			if wallet.Service.WalletCategory(playerUuid) == wallet.CategoryHost {
				wallet.Service.IncreaseCent(playerUuid, "", totalWin)
				cent, _ := wallet.Service.Cent(playerUuid)
				wallet.Service.Withdraw(playerUuid, 0, cent, totalCost, totalWin)
			} else {
				wallet.Service.IncreaseBalance(playerUuid, "", totalWin, 0, 0)
			}

			if betCalls != nil {
				result := s.eResult(playerUuid, betCalls, totalWin, totalCost)
				broadcastResult.Results = append(broadcastResult.Results, result)
			}
		}
		bytes, _ := proto.Marshal(broadcastResult)

		flux.Send(EMSGID_eBroadcastLotteryResult, s.Id, gameRoomUuid, bytes, bets, result, fakeRoomId)

	} else {
		num_list := make(map[int]int)

		for i := 0; i < 6; i++ {
			num_list[i] = i
		}

		if simulation_block == 0 {
			randNum, _ := rand1.Int(rand1.Reader, big.NewInt(int64(6)))
			simulation_block = int(randNum.Int64()) + 1
		}

		for i := 0; i < 6-simulation_block; i++ {
			if len(num_list) > 0 {
				options := make([]rng.Option, 0)

				for k := range num_list {
					options = append(options, rng.Option{Weight: 10, Item: k})
				}

				deleted_num := rng.New(options).Item.(int)
				delete(num_list, deleted_num)
			}

		}

		if simulation_bet == 0 {
			options := make([]rng.Option, 0)
			options = append(options, rng.Option{Weight: 10, Item: 1})
			options = append(options, rng.Option{Weight: 10, Item: 10})
			options = append(options, rng.Option{Weight: 10, Item: 100})

			simulation_bet = rng.New(options).Item.(int)
		}

		totalCost := 0
		totalWin := 0 //含本金的贏分
		for k := range num_list {
			betAreaRate := betIndex[k] //各區賠率
			bet := simulation_bet      //押注

			totalCost += bet
			// 賠分不含本金在內
			if betAreaRate >= 1 {
				totalWin += int(betAreaRate)*bet + bet
				BetAreaRate[int(betAreaRate)]++
			}
		}

		//分數加回錢包
		profit := totalWin - totalCost

		if profit > 0 { //整體是贏的
			feeTotalWin := totalCost + profit //贏分
			logger.Service.Zap.Infow("贏", "押注區域", simulation_block, "各區押注", simulation_bet, "獲得", feeTotalWin)
			Win_list[simulation_block*simulation_bet] += feeTotalWin
			Win_Count[simulation_block*simulation_bet]++
		} else { //整體不輸不贏或輸分，就不扣抽水了
			logger.Service.Zap.Infow("輸或平", "押注區域", simulation_block, "各區押注", simulation_bet, "獲得", totalWin)
			Lose_list[simulation_block*simulation_bet] += totalWin
			Lose_Count[simulation_block*simulation_bet]++
		}

		for k := range num_list {
			delete(num_list, k)
		}
	}

	return chosenMultiple
}

func (s *service) VipResult(bets map[string][]bet_proto.BetCall, result [][3]int32, chosenColor []probability.ColorWeight, allFireColorType []int, gameRoomUuid, fakeRoomId, jsonPath, vipPlayerUuid string, reRollTimes int) (chosenMultiple, minTotalWinIndex int) {
	//[黃0，白1，粉2，藍3，紅4，綠5]()

	var allBetIndex [][6]int32
	var allChosenMultiple []int
	minTotalWin := int(^uint(0) >> 1) //最大int值

	//取得賠率物件
	combControl := probability.CombServie.GetCombControl(jsonPath)
	fmt.Printf("QA LOG ---> : -----------------------------reRollTimes = %d-----------------------------------------------------------------------------------------------------------------\n", reRollTimes) //--
	for i := 0; i < reRollTimes; i++ {
		//計算顏色出現的次數
		colorNumResult := [6]int{}
		for diceResultIndex := 0; diceResultIndex < len(result[i]); diceResultIndex++ { //分析三次開骰的結果
			for colorIndex := 0; colorIndex < 6; colorIndex++ {
				if result[i][diceResultIndex] == int32(colorIndex) {
					colorNumResult[colorIndex]++
					break
				}
			}
		}

		//選定倍率
		var multipleWeightValue []int //倍率權重植
		for _, multipleWeight := range chosenColor[i].Multiples {
			multipleWeightValue = append(multipleWeightValue, multipleWeight.Weight)
		}

		randomMultipleIndex := getRandomIndexByWeight(multipleWeightValue)
		chosenMultiple = chosenColor[i].Multiples[randomMultipleIndex].Multiple
		allChosenMultiple = append(allChosenMultiple, chosenMultiple)

		// 各個注區的賠率
		betIndex := [6]int32{0, 0, 0, 0, 0, 0}

		//計算賠率
		for colorI, times := range colorNumResult {
			if times == 1 {
				betIndex[colorI] = int32(combControl.HITX1)
			} else if times == 2 {
				betIndex[colorI] = int32(combControl.HITX2)
			} else if times == 3 {
				//結果
				betIndex[colorI] = int32(chosenMultiple)

			}

			//需扣掉本金
			if betIndex[colorI] != 0 {
				betIndex[colorI] -= 1
			}
		}

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
	fmt.Printf("QA LOG ---> : -----------------------------Times = %2d   Dices = %v   fireColorType = %d   totalWin = %d------------------------------------------------------------------\n", minTotalWinIndex+1, result[minTotalWinIndex], allFireColorType[minTotalWinIndex], minTotalWin) //--
	//印賠率結果
	logger.Service.Zap.Infow("gameRoomBetIndex", "gameRoomUuid", gameRoomUuid, "betIndex", allBetIndex[minTotalWinIndex])

	//分析所有的押注贏分
	broadcastResult := &lottery_proto.BroadcastResult{
		Msgid:      commonFS_proto.EMSGID_eBroadcastLotteryResult,
		WinIndexes: allBetIndex[minTotalWinIndex][:],
	}

	for playerUuid, betCalls := range bets {
		var totalCost uint64 = 0
		var totalWin uint64 = 0 //含本金的贏分
		for _, betCall := range betCalls {
			betAreaRate := allBetIndex[minTotalWinIndex][int(betCall.BetType)] //賠率
			betCost := gamesettingFS.Service.Bet(playerUuid, betCall.BetIndex) //押注面額
			gameRate := gamesettingFS.Service.Rate(playerUuid)                 //房間的比例
			bet := uint64(betCost * gameRate)                                  //押注面額*比例 = 真正的押注金

			totalCost += bet
			// 賠分不含本金在內
			if betAreaRate >= 1 {
				totalWin += uint64(betAreaRate)*bet + bet
			}
		}

		//分數加回錢包
		if wallet.Service.WalletCategory(playerUuid) == wallet.CategoryHost {
			wallet.Service.IncreaseCent(playerUuid, "", totalWin)
			cent, _ := wallet.Service.Cent(playerUuid)
			wallet.Service.Withdraw(playerUuid, 0, cent, totalCost, totalWin)
		} else {
			wallet.Service.IncreaseBalance(playerUuid, "", totalWin, 0, 0)
		}

		if betCalls != nil {
			result := s.eResult(playerUuid, betCalls, totalWin, totalCost)
			broadcastResult.Results = append(broadcastResult.Results, result)
		}
	}
	bytes, _ := proto.Marshal(broadcastResult)

	flux.Send(EMSGID_eBroadcastLotteryResult, s.Id, gameRoomUuid, bytes, bets, result[minTotalWinIndex], fakeRoomId)

	return allChosenMultiple[minTotalWinIndex], minTotalWinIndex
}

func (s *service) eResult(playerUuid string, calls []bet_proto.BetCall, win, cost uint64) *lottery_proto.Result {
	gameDataResult := s.createResult(playerUuid, calls, win, cost)
	playerdata.Service.SaveUserGameData(playerUuid, calls, win, cost, gameDataResult)

	//發送結果至前端
	frontEndResult := s.createResult(playerUuid, calls, win, cost)
	if win > cost {
		frontEndResult.Pay = win - cost
	}
	bytes, _ := proto.Marshal(frontEndResult)
	// logger.Service.Zap.Infow("EMSGID_eLotteryResult",
	// 	"player:", playerUuid,
	// 	"balance:", balance,
	// )
	playerResult := make(map[string]uint64)
	playerResult["total_Bet"] = cost
	playerResult["total_Win"] = win

	flux.Send(EMSGID_eLotteryResult, s.Id, playerUuid, bytes, playerResult)

	return gameDataResult
}

//建立遊戲紀錄
func (s *service) createResult(playerUuid string, calls []bet_proto.BetCall, win, cost uint64) *lottery_proto.Result {
	r := &lottery_proto.Result{
		Msgid:         commonFS_proto.EMSGID_eLotteryResult,
		Seat:          calls[0].Seat,
		Pay:           0,
		Status:        0,
		PlayerBalance: 0,
	}
	if win > cost {
		r.Pay = win - cost
		r.Status = int32(lottery_proto.Result_WIN)
	}
	if cost > win {
		r.Pay = cost - win
		r.Status = int32(lottery_proto.Result_LOSE)
	}
	if win == cost {
		r.Status = int32(lottery_proto.Result_TIE)
	}
	balance, _ := wallet.Service.Balance(playerUuid)

	if wallet.Service.WalletCategory(playerUuid) == wallet.CategoryHost {
		cent, _ := wallet.Service.Cent(playerUuid)
		balance += cent
	}

	r.PlayerBalance = balance

	//playerdata.Service.SaveUserGameData(playerUuid, calls, win, cost, r)
	return r
}

//選定火焰顏色
func ChooseFireColor(jsonPath string) (probability.ColorWeight, int) {
	combControl := probability.CombServie.GetCombControl(jsonPath) //取得賠率物件

	colorWeights := []probability.ColorWeight{
		combControl.HITX3.ORIGINAL, //0
		combControl.HITX3.YELLOW,   //1
		combControl.HITX3.RED,      //2
		combControl.HITX3.BLUE,     //3
	}

	var weightsValue []int //顏色權重值
	for _, colorWeight := range colorWeights {
		weightsValue = append(weightsValue, colorWeight.Weight)
	}

	randomColorIndex := getRandomIndexByWeight(weightsValue)
	chosenColor := colorWeights[randomColorIndex]

	return chosenColor, randomColorIndex
}

//依權重取得隨機結果
func getRandomIndexByWeight(colorWeights []int) int {
	//計算總權重
	sumWeight := 0
	for _, weight := range colorWeights {
		sumWeight += weight
	}

	if sumWeight == 0 {
		panic("机率值设定有异常！")
	}

	//計算概率區間
	var sortOriginalWeights []float64
	tempSumWeight := 0
	for _, weight := range colorWeights {
		tempSumWeight += weight
		sortOriginalWeights = append(sortOriginalWeights, float64(tempSumWeight)/float64(sumWeight))
	}

	//抽出在哪個區間
	nextDouble := rand.Float64()
	sortOriginalWeights = append(sortOriginalWeights, nextDouble)
	sort.Float64s(sortOriginalWeights)

	//取得索引
	randomIndex := 0
	for i, floatV := range sortOriginalWeights {
		if floatV == nextDouble {
			randomIndex = i

		}
	}

	return randomIndex
}
