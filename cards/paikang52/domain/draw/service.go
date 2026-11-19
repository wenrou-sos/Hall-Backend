package draw

import (
	draw_proto "52-game-server/domain/draw/proto"
	probability_proto "52-game-server/domain/probability/proto"
	common52_proto "52-game-server/models/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"os"
	"strconv"
	"sync"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
)

var Service = &service{
	Id:       		"DrawService",
	poolSize:		os.Getenv("POOL_SIZE"),
	in:       		make(chan *flux.Action, common.Service.ChanSize),
	rwMutex:  		&sync.RWMutex{},
	resumePlayer: 	make(map[string]string),
}

type service struct {
	Id       		string
	poolSize 		string
	in       		chan *flux.Action
	rwMutex  		*sync.RWMutex
	resumePlayer 	map[string]string
}

func init() {
	go Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	draws := make(map[string]*draw)

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action, draws)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action, draws map[string]*draw) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if action.Key().To() != s.Id {
		return
	}
	logger.Service.Zap.Infow(action.Key().Name())

	switch action.Key().Name() {
	case ActionDrawCreate:
		d := action.Payload()[0].(*draw)

		if v, ok := draws[action.Key().From()]; ok {
			v.destroy()
		}

		draws[action.Key().From()] = d

		go d.run()

	case ActionDrawReset:
		secWebSocketKey := action.Key().From()

		if v, ok := s.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		if v, ok := draws[secWebSocketKey]; ok {
			v.reset()
		}

	case ActionDrawResume:
		secWebSocketKey := action.Payload()[0].(string)
		oldSecWebSocketKey := action.Payload()[1].(string)
		resumePlayer := action.Payload()[2].(map[string]string)

		if v, ok := draws[oldSecWebSocketKey]; ok {
			s.resumePlayer = resumePlayer
			v.secWebSocketKey = secWebSocketKey
			delete(draws, oldSecWebSocketKey)
			draws[secWebSocketKey] = v
		}

	case ActionDrawStop:
		if v, ok := draws[action.Key().From()]; ok {
			v.timer.Stop()
		}

	case ActionDrawDelete:
		if v, ok := draws[action.Key().From()]; ok {
			v.destroy()
		}

	case EMSGID_eDrawCall:
		msg := action.Payload()[0].([]byte)

		if v, ok := draws[action.Key().From()]; ok {
			if data := v.eDrawCall(msg); data != nil {
				v.eDrawRecall()
			}
		}


	default:
		break
	}
}

func (s *service) BroadcastDrawRecall(draw *draw_proto.DrawRecall) []byte {
	data := &draw_proto.BroadcastDrawRecall{
		Msgid: common52_proto.EMSGID_eBroadcastDrawRecall,
		DrawRecall: &draw_proto.DrawRecall{
			RoomUuid: draw.RoomUuid,
			Pool:     draw.Pool,
			PlayerData: &probability_proto.PlayerData{
				Seat:        draw.PlayerData.Seat,
				PokerNumber: draw.PlayerData.PokerNumber,
			},
		},
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (s *service) BroadcastDrawTimeout(draw *draw_proto.DrawTimeout) []byte {

	data := &draw_proto.BroadcastDrawRecall{
		Msgid: common52_proto.EMSGID_eBroadcastDrawTimeout,
		DrawRecall: &draw_proto.DrawRecall{
			RoomUuid: draw.RoomUuid,
			Pool:     draw.Pool,
			PlayerData: &probability_proto.PlayerData{
				Seat:        draw.PlayerData.Seat,
				PokerNumber: draw.PlayerData.PokerNumber,
			},
		},
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (s *service) HashId(secWebSocketKey, gameRoomUuid string) string {
	return secWebSocketKey + s.Id + gameRoomUuid
}

func (s *service) destroy() {
	flux.UnRegister(s.Id, s.in)
}
