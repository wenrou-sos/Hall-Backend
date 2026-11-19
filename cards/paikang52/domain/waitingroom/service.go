package waitingroom

import (
	waiting_room_proto "52-game-server/domain/waitingroom/proto"
	common52_proto "52-game-server/models/proto"
	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
)

const (
	EMSGID_eWaitingCountdown  = "EMSGID_eWaitingCountdown"
	EMSGID_eWaitingRoundEnd   = "EMSGID_eWaitingRoundEnd"
	ActionWaitingRoomDone    = "ActionWaitingRoomDone"
)

var Service = &service{
	Id: "WaitingRoomService",
	in: make(chan *flux.Action, common.Service.ChanSize),
}

type service struct {
	Id string
	in chan *flux.Action
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
	default:
		break
	}
}

func (s *service) EMSGID_eWaitingRoundStart() []byte {
	data := &waiting_room_proto.WaitingRoundStart{
		Msgid: common52_proto.EMSGID_eWaitingRoundStart,
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (s *service) EMSGID_eWaitingRoundEnd() []byte {
	data := &waiting_room_proto.WaitingRoundEnd{
		Msgid: common52_proto.EMSGID_eWaitingRoundEnd,
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (s *service) EMSGID_eWaitingCountdown(countdown uint64) []byte {
	data := &waiting_room_proto.WaitingCountdown{
		Msgid:     common52_proto.EMSGID_eWaitingCountdown,
		Countdown: countdown,
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
