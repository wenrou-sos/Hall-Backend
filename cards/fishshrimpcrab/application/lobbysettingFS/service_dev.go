//go:build dev
// +build dev

package lobbysettingFS

import (
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
)

func (s *service) LobbyConfig(hostExtId string) *HostFSGame {
	return &HostFSGame{
		HostId:    "DEV",
		GameId:    "PSC-ON-00009",
		SubGameId: 0,
		Langs:     "en-US,zh-CN,zh-TW,th-TH",
		BetList:   "10,50,100,500",
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
		Fee:            5,
	}
}

func (s *service) NewHandler(ls *lobbysetting.LobbySetting) *lobbysetting.LobbySetting {
	game1 := s.LobbyConfig(ls.HostExtId)

	ls.AvailableGames[game1.GameId] = game1

	return ls
}

func (s *service) BotDefaultLobbySetting(hostExtId, gameId string) *HostFSGame {
	return &HostFSGame{
		HostId:    "DEV",
		GameId:    "PSC-ON-00009",
		SubGameId: 0,
		Langs:     "en-US,zh-CN,zh-TW,th-TH",
		BetList:   "10,50,100,500",
		BetAreaLimit: "50000,10000,10000,10000," +
			"100000,20000,20000,20000," +
			"250000,50000,50000,50000," +
			"350000,70000,70000,70000," +
			"500000,100000,100000,100000," +
			"1000000,200000,200000,200000",
		RateList:       "1,2,5,7,10,20",
		BalanceLimit:   "20,40,100,200,400,1000",
		WaitingTime:    "6000,15000,13500", // roll, bet, result (MilliSecond)
		SessionTimeout: 300,
		Fee:            5,
	}
}
