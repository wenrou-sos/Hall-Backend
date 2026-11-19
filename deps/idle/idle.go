package idle

import (
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "time"
)

const (
    ActionIdleTimeoutReset = "ActionIdleTimeoutReset"
)

func Builder() *builder {
    return &builder{
        secWebSocketKey: "",
        timeout:         0,
    }
}

type builder struct {
    secWebSocketKey string
    timeout         uint32
}

type idle struct {
    secWebSocketKey string
    timeout         uint32
    in              chan *flux.Action
}

func (b *builder) setSecWebSocketKey(secWebSocketKey string) *builder {
    b.secWebSocketKey = secWebSocketKey
    return b
}

func (b *builder) setTimeout(timeout uint32) *builder {
    b.timeout = timeout
    return b
}

func (b *builder) build() *idle {
    v := &idle{
        secWebSocketKey: b.secWebSocketKey,
        timeout:         b.timeout,
        in:              make(chan *flux.Action, 1024),
    }

    go v.run()

    return v
}

func (i *idle) run() {
    flux.Register(i.hashId(), i.in)

    t := time.NewTimer(time.Duration(i.timeout) * time.Second)

    defer func() {
        t.Stop()
    }()

    for {
        select {
        case action, ok := <-i.in:
            if !ok {
                return
            }

            switch action.Key().Name() {
            case ActionIdleTimeoutReset:
                t.Stop()
                t = time.NewTimer(time.Duration(i.timeout) * time.Second)
            }

        case <-t.C:
            logger.Service.Zap.Warnw(Idle_TIMEOUT,
                "GameUser", i.secWebSocketKey,
                "Timeout", i.timeout,
            )
            errorcode.Service.Fatal(i.secWebSocketKey, Idle_TIMEOUT)
            return
        }
    }
}

func (i *idle) hashId() string {
    return Service.HashId(i.secWebSocketKey)
}

func (i *idle) destroy() {
    flux.UnRegister(i.hashId(), i.in)
}
