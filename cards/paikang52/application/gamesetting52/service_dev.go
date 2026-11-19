//+build dev

package gamesetting52

import (
	"52-game-server/models"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
)

func (s *service) NewHandler(gs *gamesetting.GameSetting) *gamesetting.GameSetting {
	s.setDefaultAvailableGame(gs, models.PSC_ON_00007)
	s.setDefaultAvailableGame(gs, models.PSC_ON_00008)

	return gs
}

func (s *service) setDefaultAvailableGame(gs *gamesetting.GameSetting, gameId string) {
	game := &host52Game{
		HostId:                "DEV",
		GameId:                gameId,
		SubGameId:             0,
		MathId:                "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0",
		Langs:                 "en-US,zh-CN,zh-TW,th-TH",
		BetList:               "10,20,50,100,10,20,50,100,10,20,50,100",
		BalanceLimit:          "1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000",
		TransferCredit:        "5000,10000,20000,50000,100000,200000,500000,1000000",
		WaitingTime:           "10,5,9,5,10,5,9,5,10,5,9,5,10,5,9,5,10,5,9,5,10,5,9,5", // first round start, draw, play cards, round start
		SessionTimeout:        300,
		Fee:                   5,
		IdBlockPercent:        0,
		UnluckyRate:           "100,100,100,100,100,100,100,100,100,100,100,100",
		BlacklistCondition:    "0,0,0,0,0,0",
		IsolateRate:           "0,0,0,0,0,0",
		AutoBlacklistValue:    "50,50,50,50,50,50",
		BlacklistRoundCount:   "3,3,3,3,3,3",
		BlacklistTriggerCount: "6,6,6,6,6,6",
	}

	gs.AvailableGames[gameId] = game
}
