//+build dev

package gamesettingU

import (
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	"u-game-server/models"
)

func (s *service) NewHandler(gs *gamesetting.GameSetting) *gamesetting.GameSetting {
	s.setDefaultAvailableGame(gs, models.PSC_ON_00013)

	return gs
}

func (s *service) setDefaultAvailableGame(gs *gamesetting.GameSetting, gameId string) {
	game := &hostUGame{
		HostId:             "DEV",
		GameId:             gameId,
		SubGameId:          0,
		MathId:             "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0",
		Langs:              "en-US,zh-CN,zh-TW,th-TH",
		BetList:            "10,20,50,100,10,20,50,100,10,20,50,100",
		BalanceLimit:       "1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000,1000",
		RoomLimit:          "10000,10000,10000,10000",
		TransferCredit:     "5000,10000,20000,50000,100000,200000,500000,1000000",
		WaitingTime:        "10,8,300,5,30,250,10,8,300,5,30,250,10,8,300,5,30,250,10,8,300,5,30,250,10,8,300,5,30,250,10,8,300,5,30,250", // first round start, player round, game round, round start, predict time, bot logic time
		SessionTimeout:     300,
		Fee:                5,
		IdBlockPercent:     0,
		UnluckyRate:        "100,100,100,100,100,100,100,100,100,100,100,100",
		BlacklistCondition: "0,0,0,0,0,0",
		IsolateRate:        "0,0,0,0,0,0",
		AutoBlacklistValue: "50,50,50,50,50,50",
	}

	gs.AvailableGames[gameId] = game
}
