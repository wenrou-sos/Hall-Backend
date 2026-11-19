package botroom

import (
	"colorgame-game-server/application/gameroom"
	"colorgame-game-server/application/gamesettingFS"
	"os"
	"time"
)

type service struct {
	Id               string
	FakeWebSocketKey []string
	DefaultHostExtId string
	DefaultGameId    string
}

//for background game's gamesetting
var Service = service{
	Id:               "botRoomService",
	DefaultHostExtId: os.Getenv("BOT_DEFAULT_HOST_EXT_ID"),
	DefaultGameId:    "PSC-ON-00016",
}

func (s *service) CreateBotLobbies() {
	for rateIndex, key := range gamesettingFS.Service.DefaultBotKeys {
		time.Sleep(3 * time.Second)

		if s.DefaultHostExtId == ""{
			s.DefaultHostExtId = "dd12f3635bc9599ca58012601d07197c"
		}

		gamesettingFS.Service.NewAllselectedGame(key, s.DefaultHostExtId, s.DefaultGameId, uint32(rateIndex)) // i:0~5, 產生六個倍率的 gamesetting
		gameroom.Service.CreateBotRooms(rateIndex, key, s.DefaultHostExtId, s.DefaultGameId)
	}
}
