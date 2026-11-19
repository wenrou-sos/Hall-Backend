package banker

import (
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
)

const (
	ActionBankerCreate = "ActionBankerCreate"
	ActionBankerDelete = "ActionBankerDelete"
)

var Service = &service{
	Id: "BankerService",
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

	bankers := make(map[string]*banker)

	for action := range s.in {
		s.handleAction(action, bankers)
	}
}

func (s *service) handleAction(action *flux.Action, bankers map[string]*banker) {
	switch action.Key().Name() {
	case ActionBankerCreate:
		from := action.Key().From()
		roomUuid := action.Payload()[0].(string)
		roomType := action.Payload()[1].(string)
		size := action.Payload()[2].(int32)
		startSeat := action.Payload()[3].(int32)
		bet := action.Payload()[4].(uint64)
		vip := action.Payload()[5].(bool)

		b := Builder().
			setFrom(from).
			setRoomUuid(roomUuid).
			setRoomType(roomType).
			setSize(size).
			setStartSeat(startSeat).
			setBetCent(bet).
			setVip(vip).
			build()

		bankers[roomUuid] = b

	case ActionBankerDelete:
		gameRoomUuid := action.Payload()[0].(string)

		delete(bankers, gameRoomUuid)
	}
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
