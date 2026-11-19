package waitingroom

import (
    waiting_room_proto "89-game-server/domain/waitingroom/proto"
    common89_proto "89-game-server/models/proto"
    "crypto/sha1"
    "fmt"
    "github.com/gogo/protobuf/proto"
    "gitlab.iplaystar.net/game-server/common"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "strconv"
)

const (
    EMSGID_eWaitingRoundStart = "EMSGID_eWaitingRoundStart"
    EMSGID_eWaitingCountdown  = "EMSGID_eWaitingCountdown"
    EMSGID_eWaitingRoundEnd   = "EMSGID_eWaitingRoundEnd"
    ActionWaitingRoomJoin     = "ActionWaitingRoomJoin"
    ActionWaitingRoomLeave    = "ActionWaitingRoomLeave"
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

    allWaitingRooms := make(map[string]*waitingRoom)

    for action := range s.in {
        s.handleAction(action, allWaitingRooms)
    }
}

func (s *service) handleAction(action *flux.Action, allWaitingRooms map[string]*waitingRoom) {
    switch action.Key().Name() {
    case ActionWaitingRoomJoin:
        j := action.Payload()[0].(*Join)

        if v, ok := allWaitingRooms[j.HashId()]; ok {
            logger.Service.Zap.Infow("Join Waiting Room",
                "GameUser", j.secWebSocketKey,
                "HostExtId", j.hostExtId,
                "Balance", j.balance,
            )

            flux.Send(actionWaitingRoomAdd, s.Id, v.hashId(), j)
            return
        }

        w := Builder().
            setGameId(j.gameId).
            setBetList(j.betList).
            setRateList(j.rateList).
            setRate(j.rate).
            build()

        if <-w.isReady {
            logger.Service.Zap.Infow("Join Waiting Room",
                "GameUser", j.secWebSocketKey,
                "HostExtId", j.hostExtId,
                "Balance", j.balance,
            )

            allWaitingRooms[w.hashId()] = w
            flux.Send(actionWaitingRoomAdd, s.Id, w.hashId(), j)
        }

    case ActionWaitingRoomLeave:
        l := action.Payload()[0].(*leave)

        if v, ok := allWaitingRooms[l.hashId()]; ok {
            logger.Service.Zap.Infow("Leave Waiting Room",
                "GameUser", l.secWebSocketKey,
            )

            flux.Send(actionWaitingRoomDelete, s.Id, v.hashId(), l)
        }

    case actionWaitingRoomDestroy:
        delete(allWaitingRooms, action.Key().From())
    }
}

func (s *service) EMSGID_eWaitingRoundStart() []byte {
    data := &waiting_room_proto.WaitingRoundStart{
        Msgid: common89_proto.EMSGID_eWaitingRoundStart,
    }

    dataByte, _ := proto.Marshal(data)

    return dataByte
}

func (s *service) EMSGID_eWaitingRoundEnd() []byte {
    data := &waiting_room_proto.WaitingRoundEnd{
        Msgid: common89_proto.EMSGID_eWaitingRoundEnd,
    }

    dataByte, _ := proto.Marshal(data)

    return dataByte
}

func (s *service) EMSGID_eWaitingCountdown(countdown uint64) []byte {
    data := &waiting_room_proto.WaitingCountdown{
        Msgid:     common89_proto.EMSGID_eWaitingCountdown,
        Countdown: countdown,
    }

    dataByte, _ := proto.Marshal(data)

    return dataByte
}

func (s *service) hashId(gameId, betList, rateList string, rate uint32) string {
    return fmt.Sprintf("%x", sha1.Sum([]byte(gameId+betList+rateList+strconv.FormatUint(uint64(rate), 10))))
}

func (s *service) Destroy() {
    flux.UnRegister(s.Id, s.in)
}
