package atm

import (
    "sync"
    "time"
)

func Builder() *builder {
    return &builder{
        secWebSocketKey: "",
        hostExtId:       "",
        memberId:        "",
    }
}

type builder struct {
    secWebSocketKey string
    hostExtId       string
    memberId        string
}

type atm struct {
    secWebSocketKey string
    hostExtId       string
    memberId        string
    isLock          bool
    rwMutex         *sync.RWMutex
}

func (b *builder) setSecWebSocketKey(secWebSocketKey string) *builder {
    b.secWebSocketKey = secWebSocketKey
    return b
}

func (b *builder) setHostExtId(hostExtId string) *builder {
    b.hostExtId = hostExtId
    return b
}

func (b *builder) setMemberId(memberId string) *builder {
    b.memberId = memberId
    return b
}

func (b *builder) build() *atm {
    return &atm{
        secWebSocketKey: b.secWebSocketKey,
        hostExtId:       b.hostExtId,
        memberId:        b.memberId,
        isLock:          false,
        rwMutex:         &sync.RWMutex{},
    }
}

func (a *atm) run() {
    a.rwMutex.Lock()
    a.isLock = true
    a.rwMutex.Unlock()

    time.Sleep(2 * time.Second)

    a.rwMutex.Lock()
    a.isLock = false
    a.rwMutex.Unlock()
}

func (a *atm) lock() bool {
    a.rwMutex.RLock()
    defer a.rwMutex.RUnlock()

    return a.isLock
}
