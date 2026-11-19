package accounting

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
    actionAccountingStart  = "actionAccountingStart"
    actionAccountingDelete = "actionAccountingDelete"
)

var Service = &service{
    Id:       "AccountingService",
    poolSize: os.Getenv("POOL_SIZE"),
    in:       make(chan *flux.Action, common.Service.ChanSize),
    rwMutex:  &sync.RWMutex{},
}

type service struct {
    Id       string
    poolSize string
    in       chan *flux.Action
    rwMutex  *sync.RWMutex
}

func init() {
    Service.run()
    logger.Service.Zap.Infow("Service Created",
        "Service", Service.Id,
        "Chan", fmt.Sprintf("%p", Service.in),
    )
}

func (s *service) HashId(secWebSocketKey string, accountingSn uint64) string {
    return s.Id + secWebSocketKey + strconv.FormatUint(accountingSn, 10)
}

func (s *service) Destroy() {
    flux.UnRegister(s.Id, s.in)
}
