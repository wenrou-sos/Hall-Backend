package playcards

import (
	"fmt"
	"os"
	"strconv"
	"sync"
	play_cards_proto "u-game-server/domain/playcards/proto"
	probability_proto "u-game-server/domain/probability/proto"
	commonU_proto "u-game-server/models/proto"

	"gitlab.iplaystar.net/game-server/logger"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
)

var Service = &service{
	Id:           "PlayCardsService",
	poolSize:     os.Getenv("POOL_SIZE"),
	in:           make(chan *flux.Action, common.Service.ChanSize),
	rwMutex:      &sync.RWMutex{},
	resumePlayer: make(map[string]string),
}

type service struct {
	Id           string
	poolSize     string
	in           chan *flux.Action
	rwMutex      *sync.RWMutex
	resumePlayer map[string]string
}

func init() {
	go Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	plays := make(map[string]*playCards)

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action, plays)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action, plays map[string]*playCards) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if action.Key().To() != s.Id {
		return
	}
	logger.Service.Zap.Infow(action.Key().Name())

	switch action.Key().Name() {
	case ActionPlayCardsCreate:
		p := action.Payload()[0].(*playCards)

		if v, ok := plays[action.Key().From()]; ok {
			v.destroy()
		}

		plays[action.Key().From()] = p

	case ActionPlayCardsResume:
		secWebSocketKey := action.Payload()[0].(string)
		oldSecWebSocketKey := action.Payload()[1].(string)
		resumePlayer := action.Payload()[2].(map[string]string)

		if v, ok := plays[oldSecWebSocketKey]; ok {
			s.resumePlayer = resumePlayer
			fmt.Println(s.resumePlayer)
			v.secWebSocketKey = secWebSocketKey
			delete(plays, oldSecWebSocketKey)
			plays[secWebSocketKey] = v
		}

	case ActionPlayCardsDelete:
		if v, ok := plays[action.Key().From()]; ok {
			v.destroy()
		}

	case ActionPlayCardsReset:
		secWebSocketKey := action.Key().From()

		if v, ok := s.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		if v, ok := plays[secWebSocketKey]; ok {
			v.reset()
		}

	case EMSGID_ePlayCardsCall:
		msg := action.Payload()[0].([]byte)

		if v, ok := plays[action.Key().From()]; ok {
			if data := v.ePlayCardsCall(msg); data != nil {
				v.ePlayCardsRecall(data)
			}
		}

	case EMSGID_ePlayCardsTimeout:
		secWebSocketKey := action.Payload()[0].(string)

		if v, ok := s.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		if v, ok := plays[secWebSocketKey]; ok {
			v.ePlayCardsTimeout()
		}

	default:
		break
	}
}

func (s *service) BroadcastPlayCardsRecall(playCardsRecall *play_cards_proto.PlayCardsRecall) []byte {
	data := &play_cards_proto.BroadcastPlayCardsRecall{
		Msgid: commonU_proto.EMSGID_eBroadcastPlayCardsRecall,
		PlayCardsRecall: &play_cards_proto.PlayCardsRecall{
			RoomUuid: playCardsRecall.RoomUuid,
			PlayerData: &probability_proto.PlayerData{
				Seat:        playCardsRecall.PlayerData.Seat,
				PokerNumber: playCardsRecall.PlayerData.PokerNumber,
				PlayCard:    playCardsRecall.PlayerData.PlayCard,
				AllScore:    playCardsRecall.PlayerData.AllScore,
			},
			Color: playCardsRecall.Color,
		},
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eBroadcastPlayCardsRecall, s.Id, playCardsRecall.RoomUuid, dataByte)
	return dataByte
}

func (s *service) BroadcastPlayCardsTimeout(playCardsTimeout *play_cards_proto.PlayCardsTimeout) []byte {
	data := &play_cards_proto.BroadcastPlayCardsTimeout{
		Msgid: commonU_proto.EMSGID_eBroadcastPlayCardsTimeout,
		PlayCardsTimeout: &play_cards_proto.PlayCardsTimeout{
			RoomUuid: playCardsTimeout.RoomUuid,
			PlayerData: &probability_proto.PlayerData{
				Seat:        playCardsTimeout.PlayerData.Seat,
				PokerNumber: playCardsTimeout.PlayerData.PokerNumber,
				PlayCard:    playCardsTimeout.PlayerData.PlayCard,
				AllScore:    playCardsTimeout.PlayerData.AllScore,
			},
			Color: playCardsTimeout.Color,
		},
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eBroadcastPlayCardsTimeout, s.Id, playCardsTimeout.RoomUuid, dataByte)
	return dataByte
}

func (s *service) HashId(secWebSocketKey, gameRoomUuid string) string {
	return secWebSocketKey + s.Id + gameRoomUuid
}

func (s *service) destroy() {
	flux.UnRegister(s.Id, s.in)
}
