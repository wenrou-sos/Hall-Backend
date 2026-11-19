package probability

import (
	"colorgame-game-server/application/lottery"
	"fmt"
	"os"
	"strconv"
	"testing"

	"colorgame-game-server/domain/probability"

	"gitlab.iplaystar.net/game-server/logger"
)

func TestService(t *testing.T) {
	// Process Input Value
	if len(os.Args) != 4 {
		fmt.Println("參數說明:押注區域 押注金額 局數")
		return
	}

	// 押注區域
	block, err1 := strconv.Atoi(os.Args[1])
	if err1 != nil {
		fmt.Println("押注區域輸入錯誤")
		return
	}

	// 押注金額
	bet, err2 := strconv.Atoi(os.Args[2])
	if err2 != nil {
		fmt.Println("押注金額輸入錯誤")
		return
	}

	// 局數
	runTimes, err3 := strconv.Atoi(os.Args[3])
	if err3 != nil {
		fmt.Println("局數輸入錯誤")
		return
	}

	lottery.Win_list = make(map[int]int)
	lottery.Lose_list = make(map[int]int)
	lottery.Win_Count = make(map[int]int)
	lottery.Lose_Count = make(map[int]int)
	lottery.BetAreaRate = make(map[int]int)

	jsonPath := probability.GetFilePath("")

	for i := 1; i <= runTimes*1; i++ {
		result := ControllRiceService.Roll()
		logger.Service.Zap.Infow("Dice Result ", "Dices", result)

		chosenColor, fireColorType := lottery.ChooseFireColor(jsonPath)
		logger.Service.Zap.Infow("火焰獎 ", "火焰獎", fireColorType, "chosenColor", chosenColor)

		lottery.Service.Result(nil, result, chosenColor, "", true, block, bet, jsonPath)
	}

	for k, v := range lottery.Win_list {
		fmt.Println("贏局統計 ", "單局押注:", k, " 局數:", lottery.Win_Count[k], " 獲得總金額:", v)
	}

	for k, v := range lottery.Lose_list {
		fmt.Println("輸或平局統計 ", "單局押注:", k, " 局數:", lottery.Lose_Count[k], " 獲得總金額:", v)
	}

	for k, v := range lottery.BetAreaRate {
		fmt.Println("賠率統計 ", "賠率:", k, " 次數:", v)
	}

}
