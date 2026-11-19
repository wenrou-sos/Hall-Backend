//+build staging prod

package accounting

import (
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "strconv"
    "strings"
)

func (s *service) run() {
    flux.Register(s.Id, s.in)
    usersAccounting := make(map[string]*Accounting)

    poolSize := 10

    if s.poolSize != "" {
        if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
            poolSize = 10
        }
    }

    for i := 0; i < poolSize; i++ {
        go func() {
            for action := range s.in {
                s.handleAction(action, usersAccounting)
            }
        }()
    }
}

func (s *service) handleAction(action *flux.Action, usersAccounting map[string]*Accounting) {
    s.rwMutex.Lock()
    defer s.rwMutex.Unlock()

    switch action.Key().Name() {

    case actionAccountingStart:
        a := action.Payload()[0].(*Accounting)

        usersAccounting[a.HashId()] = a

        logger.Service.Zap.Infow("Start Accounting",
            "GameUser", a.SecWebSocketKey,
            "AccountingSn", a.Start.Sn,
        )

    case actionAccountingDelete:
        secWebSocketKey := action.Payload()[0].(string)
        sn := action.Payload()[1].(uint64)

        if v, ok := usersAccounting[s.HashId(secWebSocketKey, sn)]; ok {
            v.destroy()
            delete(usersAccounting, s.HashId(secWebSocketKey, sn))

            logger.Service.Zap.Infow("Delete Accounting",
                "GameUser", secWebSocketKey,
                "AccountingSn", sn,
            )
        }

    case ActionAccountingEnd:
        // Accounting rotation feature will cause got bonus in the
        // previous AccountingSn and picked up by player in the next
        // AccountingSn. This situation made the previous AccountingSn
        // cannot be closed. Here provided force closed older
        // AccountingSn when the newest AccountingSn did closed.

        hashId := action.Key().From()
        secWebSocketKey := action.Payload()[0].(string)
        accountingSn := action.Payload()[1].(uint64)

        for k, v := range usersAccounting {

            // unfinished old AccountingSn here
            if k != hashId && strings.Contains(k, secWebSocketKey) && v.Start.Sn < accountingSn {

                logger.Service.Zap.Infow("Force End Accounting",
                    "GameUser", secWebSocketKey,
                    "AccountingSn", v.Start.Sn,
                    "CtrlRotation", v.IsStop,
                )

                // bonus will appear in next AccountingSn
                flux.Send(ActionAccountingEnd, s.Id, k, hashId)
            }
        }
    }
}
