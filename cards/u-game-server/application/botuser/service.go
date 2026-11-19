package botuser

import (
	"os"
	"strconv"
	"sync"
	gamesettingU "u-game-server/application/gamesettingU"

	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
)

const (
	ActionBotUserCreate = "ActionBotUserCreate"
)

var Service = &service{
	Id:       "BotUserService",
	poolSize: os.Getenv("POOL_SIZE"),
	in:       make(chan *flux.Action, common.Service.ChanSize),
	rwMutex:  sync.RWMutex{},
}

type service struct {
	Id       string
	poolSize string
	in       chan *flux.Action
	rwMutex  sync.RWMutex
}

func init() {
	Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)
	allBotUsers := make(map[string]*botUser)

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action, allBotUsers)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action, allBotUsers map[string]*botUser) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	switch action.Key().Name() {
	case ActionBotUserCreate:
		from := action.Key().From()
		gameRoomUuid := action.Payload()[0].(string)
		secWebSocketKey := action.Payload()[1].(string)
		gameRoomType := action.Payload()[2].(string)
		hostId := action.Payload()[3].(string)
		hostExtId := action.Payload()[4].(string)

		b := Builder().
			setFrom(from).
			setGameRoomUuid(gameRoomUuid).
			setGameRoomType(gameRoomType).
			setSecWebSocketKey(secWebSocketKey).
			setBalanceLimit(uint64(gamesettingU.Service.BalanceLimit(secWebSocketKey))).
			setHostId(hostId).
			setHostExtId(hostExtId).
			build()

		allBotUsers[b.uuid] = b

	case actionDestroy:
		uuid := action.Key().From()

		delete(allBotUsers, uuid)

	}
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
