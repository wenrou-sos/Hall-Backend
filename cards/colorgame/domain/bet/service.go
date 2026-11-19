package bet

import (
	"runtime/debug"
	"sync"

	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

var Service = &service{
	Id:              "BetService",
	in:              make(chan *flux.Action, common.Service.ChanSize),
	rwMutex:         &sync.RWMutex{},
	allGameBetRound: make(map[string]*BetRound), //所有遊戲的betRound
}

type service struct {
	Id              string
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
	allGameBetRound map[string]*BetRound
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
	defer func() {
		if err := recover(); err != nil {
			logger.Service.Zap.Fatalw("999",
				"err", err,
				"stacktrace", string(debug.Stack()),
			)
		}
	}()

	if action.Key().To() != s.Id {
		return
	}

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameRoomUuid", action.Key().From(),
	)

	switch action.Key().Name() {
	case ActionBetRoundStart:
		defer s.rwMutex.Unlock()
		s.rwMutex.Lock()

		gameRoomUuid := action.Payload()[0].(string)
		gameRoomKind := action.Payload()[1].(string)
		countTime := action.Payload()[2].(int)

		betRound := NewBetRound(gameRoomUuid, gameRoomKind, countTime)

		//註冊新的一局
		Service.allGameBetRound[gameRoomUuid] = betRound

		betRound.run()

	case ActionBetRoundEnd:
		defer s.rwMutex.Unlock()
		s.rwMutex.Lock()

		//移除舊的一局
		gameRoomUuid := action.Payload()[0].(string)
		delete(Service.allGameBetRound, gameRoomUuid)
	}
}

func (s *service) HashId(secWebSocketKey, gameRoomUuid string) string {
	return secWebSocketKey + s.Id + gameRoomUuid
}

//依房號取得該局BetRound的下注
func (s *service) GetAllAreaBets(gameRoomUuid string) map[int32]map[uint32]map[uint32]uint32 {
	defer s.rwMutex.Unlock()

	s.rwMutex.Lock()

	betRound := Service.allGameBetRound[gameRoomUuid]
	if betRound != nil { //全新房間開局有可能還沒建好betRound
		return betRound.getAllAreaBets()
	}

	return make(map[int32]map[uint32]map[uint32]uint32)
}
