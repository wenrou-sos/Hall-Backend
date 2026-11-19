package accountingU

import (
	"fmt"
	"strconv"
	"strings"
	"u-game-server/application/gamesettingU"
	probability_proto "u-game-server/domain/probability/proto"

	"gitlab.iplaystar.net/game-server/wallet"

	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/flux"
)

type AccountingU struct {
}

func (aU *AccountingU) FluxActionHandler(action *flux.Action, a *accounting.Accounting, isOk chan bool) {
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		isOk <- true

	case accounting.ActionAccountingStop:
		// do nothing

	case accounting.ActionAccountingEnd:

		results := action.Payload()[0].(map[string]*probability_proto.PlayerData)
		betCent := action.Payload()[1].(uint64)
		bankruptcy := action.Payload()[2].([]int32)
		bankerUuid := action.Payload()[3].(string)
		newSecWebSocketKey := action.Payload()[4].(string)
		betamt := action.Payload()[5].(uint64)
		winamt := action.Payload()[6].(uint64)

		player := results[newSecWebSocketKey]

		playerGameResult := aU.ResultString(player, bankruptcy, wallet.Service.MemberName(newSecWebSocketKey), bankerUuid, player.Avatar, betCent, gamesettingU.Service.HostId(newSecWebSocketKey))
		gameResult := fmt.Sprintf("%s", playerGameResult)

		gameData0, gameData1, gameData2, gameData3 := "", "", "", ""

		for k, v := range results {
			if k != newSecWebSocketKey {
				name := wallet.Service.MemberName(k)
				hostId := gamesettingU.Service.HostId(k)
				if k == wallet.Service.MemberId(k) {
					hostId = "BOT"
				}
				switch v.Seat {
				case 0:
					gameData0 = aU.ResultString(v, bankruptcy, name, bankerUuid, v.Avatar, betCent, hostId)

				case 1:
					gameData1 = aU.ResultString(v, bankruptcy, name, bankerUuid, v.Avatar, betCent, hostId)

				case 2:
					gameData2 = aU.ResultString(v, bankruptcy, name, bankerUuid, v.Avatar, betCent, hostId)

				case 3:
					gameData3 = aU.ResultString(v, bankruptcy, name, bankerUuid, v.Avatar, betCent, hostId)
				}
			}
		}

		gameData := ""

		switch {
		case gameData0 == "":
			gameData = fmt.Sprintf("%s", gameData1+"|"+gameData2+"|"+gameData3)

		case gameData1 == "":
			gameData = fmt.Sprintf("%s", gameData2+"|"+gameData3+"|"+gameData0)

		case gameData2 == "":
			gameData = fmt.Sprintf("%s", gameData3+"|"+gameData0+"|"+gameData1)

		case gameData3 == "":
			gameData = fmt.Sprintf("%s", gameData0+"|"+gameData1+"|"+gameData2)
		}

		switch player.AllWin {
		case 0:
			//loseCent := results[newSecWebSocketKey].AllScore
			//a.End(betCent, 0, int64(betCent)-loseCent, 0, gameData, gameResult)
			a.End(betamt, 0, int64(winamt), 0, gameData, gameResult)

		case 1:
			//winCent := results[newSecWebSocketKey].AllScore
			//a.End(betCent, 0, winCent+int64(betCent), 0, gameData, gameResult)
			a.End(betamt, 0, int64(winamt), 0, gameData, gameResult)

		default:
			panic("ERROR LOTTERY STATUS")
		}

	case accounting.ActionAccountingDelete:
		a.Delete()
	}
}

func (aU *AccountingU) RotationHandler(a *accounting.Accounting) {
	// do nothing
}
func (aU *AccountingU) ResultString(result *probability_proto.PlayerData, bankruptcy []int32, name, uuid, avatar string, betCent uint64, hostId string) string {
	var s []string
	var handS []string
	isBankruptcy := 0

	for _, h := range result.Cards.Hands {
		handS = append(handS, strconv.Itoa(int(h)))
	}
	for _, v := range bankruptcy {
		if v == result.Seat {
			isBankruptcy = 1
			break
		}
	}
	s = append(s, uuid)
	s = append(s, strconv.Itoa(int(betCent)))
	s = append(s, avatar)
	s = append(s, name)
	s = append(s, strconv.Itoa(int(result.Cent)))
	s = append(s, strconv.Itoa(int(result.Cards.SumPoint)))
	s = append(s, strconv.Itoa(int(result.AllWin)))
	s = append(s, strconv.Itoa(int(result.AllScore)))
	s = append(s, strings.Join(handS, ","))
	s = append(s, strconv.Itoa(isBankruptcy))
	s = append(s, strconv.Itoa(int(result.MaxWin)))
	s = append(s, strconv.Itoa(int(result.Rank)))
	s = append(s, hostId)
	return strings.Join(s, "/")
}
