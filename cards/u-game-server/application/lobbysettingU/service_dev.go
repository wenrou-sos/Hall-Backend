//+build dev

package lobbysettingU

import (
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"u-game-server/models"
)

func (s *service) NewHandler(ls *lobbysetting.LobbySetting) *lobbysetting.LobbySetting {
	s.setDefaultAvailableGame(ls, models.PSC_ON_00013)
	s.setDefaultAvailableGame(ls, "PSC-ON-00014")

	return ls
}

func (s *service) setDefaultAvailableGame(ls *lobbysetting.LobbySetting, gameId string) {
	game := &hostUGame{
		HostId:         "DEV",
		GameId:         gameId,
		SubGameId:      0,
		Langs:          "en-US,zh-CN,zh-TW,th-TH",
		BetList:        "10,20,50,100,10,20,50,100,10,20,50,100",
		BalanceLimit:   "1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000",
		RoomLimit:      "10000,10000,10000,10000,10000,10000,10000,10000,10000,10000,10000,10000",
		TransferCredit: "5000,10000,20000,50000,100000,200000,500000,1000000",
		WaitingTime:    "10,8,300,5,30,250", // first round start, player round, game round, round start, predict time, bot logic time
		SessionTimeout: 300,
		Fee:            5,
	}

	ls.AvailableGames[gameId] = game
}