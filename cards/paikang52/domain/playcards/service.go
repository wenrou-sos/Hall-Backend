package playcards

import (
	play_cards_proto "52-game-server/domain/playcards/proto"
	probability_proto "52-game-server/domain/probability/proto"
	common52_proto "52-game-server/models/proto"
	"fmt"
	"os"
	"strconv"
	"sync"

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

		go p.run()

	case ActionPlayCardsReset:
		playType := action.Payload()[0].(int)
		waitingTime := action.Payload()[1].(uint32)
		playCard := action.Payload()[2].(int32)
		logic := action.Payload()[3].(bool)
		secWebSocketKey := action.Key().From()

		if v, ok := s.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		if v, ok := plays[secWebSocketKey]; ok {
			v.playType = int32(playType)
			v.playCard = playCard
			v.logic = logic
			v.waitingTime = waitingTime
			v.reset()
		}

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

	case EMSGID_ePlayCardsCall:
		if v, ok := plays[action.Key().From()]; ok {
			v.ePlayCardsCall()
		}

	case ActionPlayCardsDelete:
		if v, ok := plays[action.Key().From()]; ok {
			v.destroy()
		}

	default:
		break
	}
}
func (s *service) PlayCardsRecall(roomUuid, secWebSocketKey string, playerData *probability_proto.PlayerData, seat int32, allScore []int64) *play_cards_proto.PlayCardsRecall {
	data := &play_cards_proto.PlayCardsRecall{
		Msgid:      common52_proto.EMSGID_ePlayCardsRecall,
		RoomUuid:   roomUuid,
		PlayerData: playerData,
		HitSeat:    seat,
		AllScore:   allScore,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_ePlayCardsRecall, s.Id, secWebSocketKey, dataByte)

	return data
}
func (s *service) BroadcastPlayCardsRecall(playCardsRecall *play_cards_proto.PlayCardsRecall) []byte {
	data := &play_cards_proto.BroadcastPlayCardsRecall{
		Msgid: common52_proto.EMSGID_eBroadcastPlayCardsRecall,
		PlayCardsRecall: &play_cards_proto.PlayCardsRecall{
			RoomUuid: playCardsRecall.RoomUuid,
			PlayerData: &probability_proto.PlayerData{
				Seat:        playCardsRecall.PlayerData.Seat,
				PokerNumber: playCardsRecall.PlayerData.PokerNumber,
				PlayCard:    playCardsRecall.PlayerData.PlayCard,
				ChangeWin:   playCardsRecall.PlayerData.ChangeWin,
				ChangeScore: playCardsRecall.PlayerData.ChangeScore,
				AllScore:    playCardsRecall.PlayerData.AllScore,
			},
			HitSeat:  playCardsRecall.HitSeat,
			AllScore: playCardsRecall.AllScore,
		},
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eBroadcastPlayCardsRecall, s.Id, playCardsRecall.RoomUuid, dataByte, playCardsRecall.PlayerData.Seat, playCardsRecall.HitSeat)
	return dataByte
}

func (s *service) BroadcastPlayCardsTimeout(playCardsTimeout *play_cards_proto.PlayCardsTimeout) []byte {
	data := &play_cards_proto.BroadcastPlayCardsTimeout{
		Msgid: common52_proto.EMSGID_eBroadcastPlayCardsTimeout,
		PlayCardsTimeout: &play_cards_proto.PlayCardsTimeout{
			RoomUuid: playCardsTimeout.RoomUuid,
			PlayerData: &probability_proto.PlayerData{
				Seat:        playCardsTimeout.PlayerData.Seat,
				PokerNumber: playCardsTimeout.PlayerData.PokerNumber,
				PlayCard:    playCardsTimeout.PlayerData.PlayCard,
				ChangeWin:   playCardsTimeout.PlayerData.ChangeWin,
				ChangeScore: playCardsTimeout.PlayerData.ChangeScore,
				AllScore:    playCardsTimeout.PlayerData.AllScore,
			},
			HitSeat:  playCardsTimeout.HitSeat,
			AllScore: playCardsTimeout.AllScore,
		},
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eBroadcastPlayCardsTimeout, s.Id, playCardsTimeout.RoomUuid, dataByte, playCardsTimeout.PlayerData.Seat, playCardsTimeout.HitSeat)
	return dataByte
}

func (s *service) HashId(secWebSocketKey, gameRoomUuid string) string {
	return secWebSocketKey + s.Id + gameRoomUuid
}

func (s *service) destroy() {
	flux.UnRegister(s.Id, s.in)
}
