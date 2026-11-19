package waitingroom

import (
    "github.com/google/uuid"
    "gitlab.iplaystar.net/game-server/common"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mediator"
    "sync"
    "time"
)

const (
    ActionWaitingRoomTimesUp = "ActionWaitingRoomTimesUp"
    ActionWaitingRoomDone    = "ActionWaitingRoomDone"
    actionWaitingRoomAdd     = "actionWaitingRoomAdd"
    actionWaitingRoomDelete  = "actionWaitingRoomDelete"
    actionWaitingRoomDestroy = "actionWaitingRoomDestroy"
)

func Builder() *builder {
    return &builder{
        hostExtId: "",
        gameId:    "",
        betList:   "",
        rateList:  "",
        rate:      0,
    }
}

type builder struct {
    hostExtId string
    gameId    string
    betList   string
    rateList  string
    rate      uint32
}

type waitingRoom struct {
    hostExtId    string
    gameId       string
    betList      string
    rateList     string
    rate         uint32
    waitingCount int
    isReady      chan bool
    in           chan *flux.Action
    rwMutex      *sync.RWMutex
}

func (b *builder) setHostExtId(hostExtId string) *builder {
    b.hostExtId = hostExtId
    return b
}

func (b *builder) setGameId(gameId string) *builder {
    b.gameId = gameId
    return b
}

func (b *builder) setBetList(betList string) *builder {
    b.betList = betList
    return b
}

func (b *builder) setRateList(rateList string) *builder {
    b.rateList = rateList
    return b
}

func (b *builder) setRate(rate uint32) *builder {
    b.rate = rate
    return b
}

func (b *builder) build() *waitingRoom {
    v := &waitingRoom{
        hostExtId:    b.hostExtId,
        gameId:       b.gameId,
        betList:      b.betList,
        rateList:     b.rateList,
        rate:         b.rate,
        waitingCount: 5,
        isReady:      make(chan bool, 1024),
        in:           make(chan *flux.Action, common.Service.ChanSize),
        rwMutex:      &sync.RWMutex{},
    }

    go v.run()

    return v
}

func (w *waitingRoom) run() {
    flux.Register(w.hashId(), w.in)

    t := time.NewTimer(5 * time.Second)

    var allJoins [5000]*Join

    allPlayers := make(map[string]*Join)

    defer t.Stop()

    for {
        select {
        case action, ok := <-w.in:
            if !ok {
                return
            }

            w.handleAction(action, &allJoins, allPlayers)

        case <-t.C:
            w.destroy()

            gameRoomUuid := uuid.New().String()
            var gameRooms []string

            // TODO JOHNNY need sort joins by balance

            logger.Service.Zap.Infow("Waiting Room Time's Up",
                "WaitingRoomHashId", w.hashId(),
                "QueueSize", len(allJoins),
                "AllPlayers", len(allPlayers),
            )

            if len(allPlayers) == 0 {
                return
            }

            count := 0

            for k, v := range allJoins {
                if v != nil {
                    count++

                    if count == 1 {
                        mediator.Service.New(gameRoomUuid, gameRoomUuid) // 1. 2a392173
                        mediator.Service.Add(gameRoomUuid, gameRoomUuid) // 2. 2a392173
                        gameRooms = append(gameRooms, gameRoomUuid)
                    }

                    if count%w.waitingCount == 0 {
                        gameRoomUuid = uuid.New().String()
                        mediator.Service.New(gameRoomUuid, gameRoomUuid) // 1. 2a392173
                        mediator.Service.Add(gameRoomUuid, gameRoomUuid) // 2. 2a392173
                        gameRooms = append(gameRooms, gameRoomUuid)
                    }

                    if gameRoomUuid == "" {
                        panic("EMPTY GAME ROOM UUID " + v.secWebSocketKey)
                    }

                    mediator.Service.New(gameRoomUuid, ActionWaitingRoomTimesUp) // 1. 5df96725
                    mediator.Service.Add(gameRoomUuid, ActionWaitingRoomTimesUp) // 2. 5df96725

                    flux.Send(ActionWaitingRoomTimesUp, w.hashId(), v.secWebSocketKey, gameRoomUuid)
                    allJoins[k] = nil
                }
            }

            mediator.Service.Wait(gameRoomUuid, gameRoomUuid)             // 4. 2a392173
            mediator.Service.Wait(gameRoomUuid, ActionWaitingRoomTimesUp) // 4. 5df96725

            for _, v := range gameRooms {
                flux.Send(ActionWaitingRoomDone, w.hashId(), v, "")
            }

            return
        }
    }
}

func (w *waitingRoom) handleAction(action *flux.Action, allJoins *[5000]*Join, allPlayers map[string]*Join) {
    if action.Key().To() != w.hashId() {
        return
    }

    switch action.Key().Name() {
    case flux.ActionFluxRegisterDone:
        w.isReady <- true

    case actionWaitingRoomAdd:
        w.rwMutex.Lock()
        defer w.rwMutex.Unlock()

        j := action.Payload()[0].(*Join)

        if _, ok := allPlayers[j.secWebSocketKey]; !ok {
            for k, v := range allJoins {
                if v == nil {
                    allJoins[k] = j
                    allPlayers[j.secWebSocketKey] = j

                    logger.Service.Zap.Infow("Join Waiting Room",
                        "GameUser", j.secWebSocketKey,
                        "HostExtId", j.hostExtId,
                        "BetList", j.betList,
                        "RateList", j.rateList,
                        "Rate", j.rate,
                        "Balance", j.balance,
                    )

                    flux.Send(EMSGID_eWaitingRoundStart, w.hashId(), j.secWebSocketKey, Service.EMSGID_eWaitingRoundStart())

                    break
                }
            }
        }

    case actionWaitingRoomDelete:
        w.rwMutex.Lock()
        defer w.rwMutex.Unlock()

        l := action.Payload()[0].(*leave)

        for k, v := range allJoins {
            if v != nil && (v.secWebSocketKey == l.secWebSocketKey) {
                allJoins[k] = nil
                delete(allPlayers, l.secWebSocketKey)

                logger.Service.Zap.Infow("Leave Waiting Room",
                    "GameUser", l.secWebSocketKey,
                    "BetList", l.betList,
                    "RateList", l.rateList,
                    "Rate", l.rate,
                )

                flux.Send(EMSGID_eWaitingRoundEnd, w.hashId(), l.secWebSocketKey, Service.EMSGID_eWaitingRoundEnd())

                break
            }
        }

    }
}

func (w *waitingRoom) hashId() string {
    return Service.hashId(w.gameId, w.betList, w.rateList, w.rate)
}

func (w *waitingRoom) destroy() {
    flux.UnRegister(w.hashId(), w.in)
    flux.Send(actionWaitingRoomDestroy, w.hashId(), Service.Id, "")
}
