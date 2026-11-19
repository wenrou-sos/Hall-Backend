//+build dev

package lobbysetting52

import (
	"52-game-server/models"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
)

func (s *service) NewHandler(ls *lobbysetting.LobbySetting) *lobbysetting.LobbySetting {
	s.setDefaultAvailableGame(ls, models.PSC_ON_00007)
	s.setDefaultAvailableGame(ls, models.PSC_ON_00008)

	return ls
}

func (s *service) setDefaultAvailableGame(ls *lobbysetting.LobbySetting, gameId string) {
	game := &host52Game{
		HostId:         "DEV",
		GameId:         gameId,
		SubGameId:      0,
		Langs:          "en-US,zh-CN,zh-TW,th-TH",
		BetList:        "10,20,50,100,10,20,50,100,10,20,50,100",
		BalanceLimit:   "1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000",
		TransferCredit: "5000,10000,20000,50000,100000,200000,500000,1000000",
		WaitingTime:    "10,5,9,5,10,5,9,5,10,5,9,5,10,5,9,5,10,5,9,5,10,5,9,5", // first round start, draw, play cards, round start
		SessionTimeout: 300,
		Fee:            5,
	}

	ls.AvailableGames[gameId] = game
}
