//+build dev

package lobbysetting89

import (
    lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
)

func (s *service) NewHandler(ls *lobbysetting.LobbySetting) *lobbysetting.LobbySetting {
    game1 := &host89Game{
        HostId:         "DEV",
        GameId:         "PSC-ON-00001",
        SubGameId:      0,
        MathId:         "",
        Langs:          "en-US,zh-CN,zh-TW,th-TH",
        BetList:        "10,20,50,100,200,300,400,500",
        RateList:       "10,20,50,100,200,500",
        BalanceLimit:   "20,40,100,200,400,1000",
        BankerLimit:    "200,400,1000,2000,4000,10000",
        TransferCredit: "5000,10000,20000,50000,100000,200000,500000,1000000",
        WaitingTime:    "5,10,5", // round start, bet, draw
        SessionTimeout: 300,
    }

    ls.AvailableGames[game1.GameId] = game1

    return ls
}
