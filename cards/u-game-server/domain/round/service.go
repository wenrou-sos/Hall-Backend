package round

import (
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"os"
	"strconv"
	"sync"
)

var Service = &service{
	Id:       		"RoundService",
	poolSize:		os.Getenv("POOL_SIZE"),
	in:       		make(chan *flux.Action, common.Service.ChanSize),
	rwMutex:  		&sync.RWMutex{},
	resumePlayer: 	make(map[string]string),
	rounds:         make(map[string]*round),
}

type service struct {
	Id       		string
	poolSize 		string
	in       		chan *flux.Action
	rwMutex  		*sync.RWMutex
	resumePlayer 	map[string]string
	rounds          map[string]*round
}

func init() {
	go Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if action.Key().To() != s.Id {
		return
	}
	logger.Service.Zap.Infow(action.Key().Name())

	switch action.Key().Name() {
	case ActionRoundCreate:
		r := action.Payload()[0].(*round)

		if v, ok := s.rounds[action.Key().From()]; ok {
			v.destroy()
		}

		s.rounds[action.Key().From()] = r

		go r.run()

	case ActionRoundResume:
		secWebSocketKey := action.Payload()[0].(string)
		oldSecWebSocketKey := action.Payload()[1].(string)
		resumePlayer := action.Payload()[2].(map[string]string)

		if v, ok := s.rounds[oldSecWebSocketKey]; ok {
			s.resumePlayer = resumePlayer
			v.secWebSocketKey = secWebSocketKey
			delete(s.rounds, oldSecWebSocketKey)
			s.rounds[secWebSocketKey] = v
		}

	case ActionRoundDelete:
		if v, ok := s.rounds[action.Key().From()]; ok {
			v.destroy()
		}

	case ActionRoundStateChange:
		secWebSocketKey := action.Payload()[0].(string)
		state := action.Payload()[1].(string)

		if v, ok := s.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		if v, ok := s.rounds[secWebSocketKey]; ok {
			v.stateChange(state)
		}

	default:
		break
	}
}

func (s *service) IsValid(secWebSocketKey, call string) bool {
	valid := true
	state := s.State(secWebSocketKey)

	if state == STATE_END {
		valid = false
	} else {
		switch call {
		case "EMSGID_eDrawCall":
			if state != STATE_START {
				valid = false
			}
		case "EMSGID_ePlayCardsCall":
			if state != STATE_START && state != STATE_DRAW {
				valid = false
			}
		case "EMSGID_eKeepCall":
			if state != STATE_DRAW {
				valid = false
			}
		}
	}

	return valid
}

func (s *service) State(secWebSocketKey string) string {
	if v, ok := s.rounds[secWebSocketKey]; ok {
		return v.state
	}
	return ""
}

func (s *service) HashId(secWebSocketKey, gameRoomUuid string) string {
	return secWebSocketKey + s.Id + gameRoomUuid
}

func (s *service) destroy() {
	flux.UnRegister(s.Id, s.in)
}
