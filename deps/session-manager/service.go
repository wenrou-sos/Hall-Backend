package sessionmanager

import (
    "fmt"
    macaddress "gitlab.iplaystar.net/game-server/mac-address"
    "gitlab.iplaystar.net/game-server/mysql"
    "os"
    "strconv"
    "strings"
    "sync"
)

const (
    retryTimes = 3
)

var Service = &service{
    id:              "SessionManagerService",
    ServerId:        parseServerId(),
    sessionManagers: make(map[string]*sessionManager),
    rwMutex:         &sync.RWMutex{},
}

type service struct {
    id              string
    ServerId        string
    sessionManagers map[string]*sessionManager
    rwMutex         *sync.RWMutex
}

func (s *service) clean() {
    for _, db := range mysql.Repository.GameDBs() {
        db.Table("session_map").
            Where("server_id = ?", Service.ServerId).
            Delete(Service.ServerId)
    }
}

func parseServerId() string {
    atoiPort, _ := strconv.Atoi(os.Getenv("HTTP_PORT"))

    macAddr := strings.Replace(macaddress.Get(), ":", "-", -1)

    return fmt.Sprintf("%s-%05d", macAddr, atoiPort)
}
