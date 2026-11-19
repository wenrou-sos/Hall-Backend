package idle

import (
    "fmt"
    "gitlab.iplaystar.net/game-server/common"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "os"
    "strconv"
    "sync"
)

const (
    ActionIdleTimeoutStart = "ActionIdleTimeoutStart"
    ActionIdleTimeoutStop  = "ActionIdleTimeoutStop"
)

var Service = &service{
    Id:       "IdleService",
    poolSize: os.Getenv("POOL_SIZE"),
    idles:    sync.Map{},
    in:       make(chan *flux.Action, common.Service.ChanSize),
}

type service struct {
    Id       string
    poolSize string
    idles    sync.Map
    in       chan *flux.Action
}

func init() {
    Service.run()
    logger.Service.Zap.Infow("Service Created",
        "Service", Service.Id,
        "Chan", fmt.Sprintf("%p", Service.in),
    )
}

func (s *service) run() {
    flux.Register(s.Id, s.in)

    poolSize := 10

    if s.poolSize != "" {
        if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
            poolSize = 10
        }
    }

    for i := 0; i < poolSize*10; i++ {
        go func() {
            for action := range s.in {
                s.handleAction(action)
            }
        }()
    }
}

func (s *service) handleAction(action *flux.Action) {
    switch action.Key().Name() {
    case ActionIdleTimeoutStart:
        secWebSocketKey := action.Payload()[0].(string)
        timeout := action.Payload()[1].(uint32)

        if v, ok := s.idles.Load(secWebSocketKey); ok {
            flux.Send(ActionIdleTimeoutReset, s.Id, v.(*idle).hashId(), "")
            return
        }

        s.idles.Store(
            secWebSocketKey,
            Builder().
                setSecWebSocketKey(secWebSocketKey).
                setTimeout(timeout).
                build(),
        )

    case ActionIdleTimeoutStop:
        secWebSocketKey := action.Payload()[0].(string)

        if v, ok := s.idles.Load(secWebSocketKey); ok {
            v.(*idle).destroy()
            s.idles.Delete(secWebSocketKey)
        }
    }
}

func (s *service) HashId(secWebSocketKey string) string {
    return secWebSocketKey + s.Id
}

func (s *service) Destroy() {
    flux.UnRegister(s.Id, s.in)
}
