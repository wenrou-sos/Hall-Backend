package playerdata

import (
	lottery_proto "fish-shrimp-crab-game-server/application/lottery/proto"
	playdata_proto "fish-shrimp-crab-game-server/application/playerdata/proto"
	bet_proto "fish-shrimp-crab-game-server/domain/bet/proto"
	commonFS_proto "fish-shrimp-crab-game-server/models/proto"
	"sync"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	EMSGID_eUserDataCall   = "EMSGID_eUserDataCall"
	EMSGID_eUserDataRecall = "EMSGID_eUserDataRecall"
)

type PlayData struct {
	seat           int32
	bets           []bet_proto.BetCall
	status         int32  // lose = 0, win = 1
	balance        uint64 // 數贏
	player_balance uint64
}

type service struct {
	in        chan *flux.Action
	Id        string
	usersData map[string][]*PlayData
	rwMutex   *sync.RWMutex
}

var Service = service{
	in:        make(chan *flux.Action, common.Service.ChanSize),
	Id:        "UserDataService",
	usersData: make(map[string][]*PlayData),
	rwMutex:   &sync.RWMutex{},
}

func init() {
	go Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	for action := range s.in {
		s.handleAction(action)
	}
}

func (s *service) handleAction(action *flux.Action) {
	switch action.Key().Name() {
	case EMSGID_eUserDataCall:
		s.rwMutex.RLock()
		defer s.rwMutex.RUnlock()

		secWebSocketKey := action.Key().From()
		userGameData := s.usersData[secWebSocketKey]

		playdataRecall := &playdata_proto.PlayerDataRecall{
			Msgid:      commonFS_proto.EMSGID_ePlayerDataRecall,
			PlayerData: nil,
		}
		for _, data := range userGameData {
			playerData := &playdata_proto.PlayerData{
				Seat:          data.seat,
				Status:        data.status,
				Balance:       data.balance,
				PlayerBalance: data.player_balance,
			}
			for _, bet := range data.bets {
				playerData.Bets = append(playerData.Bets, &bet)
			}
			playdataRecall.PlayerData = append(playdataRecall.PlayerData, playerData)

		}
		bytes, _ := proto.Marshal(playdataRecall)
		flux.Send(EMSGID_eUserDataRecall, s.Id, secWebSocketKey, bytes)
	}
}

func (s *service) SaveUserGameData(playerUuid string, calls []bet_proto.BetCall, win int, cost int, result *lottery_proto.Result) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()
	balance, err := wallet.Service.Balance(playerUuid)

	if err != nil {
		return
	}

	data := &PlayData{
		seat:           calls[0].Seat,
		bets:           calls,
		status:         0,
		balance:        0,
		player_balance: balance,
	}

	if result.Status == 2 {
		// 玩家贏錢
		data.status = 1
		data.balance = uint64(win - cost)
	} else if result.Status == 1 {
		// 玩家輸錢
		data.status = 0
		data.balance = uint64(cost - win)
	}

	s.usersData[playerUuid] = append(s.usersData[playerUuid], data)
}
