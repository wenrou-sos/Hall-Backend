package playerstate

import (
	"sync"

	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
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
	switch action.Key().Name() {
	case ActionCreateState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		memberId := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		s.createState(hostId, memberId)

	case ActionUpdateConnectionState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		memberId := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		state := s.playerState[hostId+"|"+memberId]

		if state != nil {
			state.isOnline = true
		}

	case ActionSaveBetState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		memberId := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)
		betRoundUuid := action.Payload()[2].(string)

		if state := s.playerState[hostId+"|"+memberId]; state != nil {
			state.BetRoundUuid = betRoundUuid
		}

	case ActionClearBetState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		memberId := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		state := s.playerState[hostId+"|"+memberId]

		if state != nil {
			state.BetRoundUuid = ""
			if !state.isOnline {
				s.deleteState(hostId, memberId)
			}
		}

	case ActionDisconnectState:
		s.rwMutex.Lock()
		defer s.rwMutex.Unlock()

		memberId := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)

		state := s.playerState[hostId+"|"+memberId]

		if state != nil {
			state.isOnline = false
			if state.BetRoundUuid == "" {
				s.deleteState(hostId, memberId)
			}
		}
	}
}

func (s *service) createState(hostId string, memberId string) {
	s.playerState[hostId+"|"+memberId] = &PlayerState{
		isOnline:     true,
		BetRoundUuid: "",
	}
}

func (s *service) deleteState(hostId, memberId string) {
	state := s.playerState[hostId+"|"+memberId]

	if state != nil {
		delete(s.playerState, hostId+"|"+memberId)
	}
}

func (s *service) GetState(hostId string, memberId string) *PlayerState {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if state, ok := s.playerState[hostId+"|"+memberId]; ok {
		return state
	}
	return nil
}
