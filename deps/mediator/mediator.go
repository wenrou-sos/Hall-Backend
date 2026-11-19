package mediator

import "sync"

type mediator struct {
    secWebSocketKey string
    key             string
    works           int64
    wg              *sync.WaitGroup
}
