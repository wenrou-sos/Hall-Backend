package playerstate

import (
	"runtime/debug"
	"sync"

	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	ActionSaveBetState          = "ActionSaveBetState"
	ActionClearBetState         = "ActionClearBetState"
	ActionCreateState           = "ActionCreateState"
	ActionUpdateConnectionState = "ActionUpdateConnectionState"
	ActionDisconnectState       = "ActionDisconnectState"
)

type PlayerState struct {
	isOnline     bool
	BetRoundUuid string
}

type service struct {
	Id          string
	in          chan *flux.Action
	playerState map[string]*PlayerState
	rwMutex     *sync.RWMutex
}

var Service = service{
	Id:          "PlayerStateService",
	in:          make(chan *flux.Action, common.Service.ChanSize),
	playerState: map[string]*PlayerState{},
	rwMutex:     &sync.RWMutex{},
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	for action := range s.in {
		s.handleAction(action)
	}
}

func init() {
	go Service.run()
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
		"GameUser", action.Key().From(),
	)

	switch action.Key().Name() {
	case ActionCreateState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		secWebSocketKey := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		s.createState(hostId, secWebSocketKey)

	case ActionUpdateConnectionState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		secWebSocketKey := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		state := s.playerState[hostId+"|"+secWebSocketKey]

		if state != nil {
			state.isOnline = true
		}

	case ActionSaveBetState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		secWebSocketKey := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)
		betRoundUuid := action.Payload()[2].(string)

		if state := s.playerState[hostId+"|"+secWebSocketKey]; state != nil {
			state.BetRoundUuid = betRoundUuid

			logger.Service.Zap.Infow("save BetRoundUuid",
				"GameUser", secWebSocketKey,
				"hostId", hostId,
				"BetRoundUuid", betRoundUuid,
			)
		}

	case ActionClearBetState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		secWebSocketKey := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		state := s.playerState[hostId+"|"+secWebSocketKey]

		if state != nil {
			state.BetRoundUuid = ""
			if !state.isOnline {
				s.deleteState(hostId, secWebSocketKey)

				logger.Service.Zap.Infow("deleteState",
					"GameUser", secWebSocketKey,
					"hostId", hostId,
				)
			} else {
				logger.Service.Zap.Infow("clear BetRoundUuid",
					"GameUser", secWebSocketKey,
					"hostId", hostId,
				)
			}
		}

	case ActionDisconnectState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		secWebSocketKey := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		state := s.playerState[hostId+"|"+secWebSocketKey]

		if state != nil {
			state.isOnline = false
			if state.BetRoundUuid == "" {
				s.deleteState(hostId, secWebSocketKey)

				logger.Service.Zap.Infow("deleteState",
					"GameUser", secWebSocketKey,
					"hostId", hostId,
				)
			} else {
				logger.Service.Zap.Infow("isOnline false",
					"GameUser", secWebSocketKey,
					"hostId", hostId,
				)
			}
		}
	}
}

func (s *service) createState(hostId string, secWebSocketKey string) {
	s.playerState[hostId+"|"+secWebSocketKey] = &PlayerState{
		isOnline:     true,
		BetRoundUuid: "",
	}
}

func (s *service) deleteState(hostId, secWebSocketKey string) {
	state := s.playerState[hostId+"|"+secWebSocketKey]

	if state != nil {
		delete(s.playerState, hostId+"|"+secWebSocketKey)
	}
}

func (s *service) GetState(hostId string, secWebSocketKey string) *PlayerState {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if state, ok := s.playerState[hostId+"|"+secWebSocketKey]; ok {
		return state
	}
	return nil
}
