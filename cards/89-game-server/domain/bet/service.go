package bet

import (
    bet_proto "89-game-server/domain/bet/proto"
    common89_proto "89-game-server/models/proto"
    "github.com/gogo/protobuf/proto"
    "gitlab.iplaystar.net/game-server/common"
    "gitlab.iplaystar.net/game-server/flux"
    "sync"
)

const (
    ActionBetStart  = "ActionBetStart"
    ActionBetDelete = "ActionBetDelete"
)

var Service = &service{
    Id:      "BetService",
    in:      make(chan *flux.Action, common.Service.ChanSize),
    rwMutex: &sync.RWMutex{},
}

type service struct {
    Id      string
    in      chan *flux.Action
    rwMutex *sync.RWMutex
}

func init() {
    go Service.run()
}

func (s *service) run() {
    flux.Register(s.Id, s.in)

    bets := make(map[string]*bet)

    for action := range s.in {
        s.handleAction(action, bets)
    }
}

func (s *service) handleAction(action *flux.Action, bets map[string]*bet) {
    s.rwMutex.Lock()
    defer s.rwMutex.Unlock()

    if action.Key().To() != s.Id {
        return
    }

    switch action.Key().Name() {
    case ActionBetStart:
        bet := action.Payload()[0].(*bet)

        if v, ok := bets[bet.hashId()]; ok {
            delete(bets, v.hashId())
        }

        bets[bet.hashId()] = bet
        go bet.run()

    case ActionBetDelete:
        gameRoomUuid := action.Payload()[0].(string)

        for k, v := range bets {
            if v.gameRoomUuid == gameRoomUuid {
                delete(bets, k)
            }
        }
    }
}

func (s *service) BetRoundStart(gameRoomUuid string) {
    data := &bet_proto.BetRoundStart{
        Msgid:    common89_proto.EMSGID_eBetRoundStart,
        RoomUuid: gameRoomUuid,
    }

    dataByte, _ := proto.Marshal(data)

    flux.Send(EMSGID_eBetRoundStart, s.Id, gameRoomUuid, dataByte)
}

func (s *service) BetRoundEnd(gameRoomUuid string) {
    data := &bet_proto.BetRoundEnd{
        Msgid:    common89_proto.EMSGID_eBetRoundEnd,
        RoomUuid: gameRoomUuid,
    }

    dataByte, _ := proto.Marshal(data)

    flux.Send(EMSGID_eBetRoundEnd, s.Id, gameRoomUuid, dataByte)
}

func (s *service) HashId(secWebSocketKey, gameRoomUuid string) string {
    return secWebSocketKey + s.Id + gameRoomUuid
}

func (s *service) destroy() {
    flux.UnRegister(s.Id, s.in)
}
