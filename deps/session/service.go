package session

import (
    "fmt"
    macaddress "gitlab.iplaystar.net/game-server/mac-address"
    "gitlab.iplaystar.net/game-server/mysql"
    "os"
    "strconv"
    "strings"
    "sync"
)

var Service = &service{
    id:           "SessionService",
    ServerId:     parseServerId(),
    usersSession: make(map[string]*Session),
    mutex:        &sync.Mutex{},
}

type service struct {
    id           string
    ServerId     string
    usersSession map[string]*Session
    mutex        *sync.Mutex
}

func (s *service) clean() {
    for _, db := range mysql.Repository.GameDBs() {
        db.Table("session").
            Where("server_id = ?", Service.ServerId).
            Delete(Service.ServerId)
    }
}

func parseServerId() string {
    atoiPort, _ := strconv.Atoi(os.Getenv("HTTP_PORT"))

    macAddr := strings.Replace(macaddress.Get(), ":", "-", -1)

    return fmt.Sprintf("%s-%05d", macAddr, atoiPort)
}
