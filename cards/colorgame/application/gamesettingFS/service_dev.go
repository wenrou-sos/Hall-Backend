//go:build dev
// +build dev

package gamesettingFS

import (
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
)

func (s *service) GameSetting(hostExtId string) *HostFSGame {
	return &HostFSGame{
		HostId:    "DEV",
		GameId:    "PSC-ON-00016",
		SubGameId: 0,
		Langs:     "en-US,zh-CN,zh-TW,th-TH",
		BetList:   "10,50,100,500,10,50",
		BetAreaLimit: "50000,10000,10000,10000," +
			"100000,20000,20000,20000," +
			"250000,50000,50000,50000," +
			"350000,70000,70000,70000," +
			"500000,100000,100000,100000," +
			"1000000,200000,200000,200000",
		RateList:       "1,2,5,7,10,20",
		BalanceLimit:   "20,40,100,200,400,1000",
		WaitingTime:    "15,15,15,15,15,15",
		SessionTimeout: 300,
	}
}

func (s *service) NewHandler(gs *gamesetting.GameSetting) *gamesetting.GameSetting {
	game1 := s.GameSetting(gs.HostExtId)

	gs.AvailableGames[game1.GameId] = game1

	return gs
}
