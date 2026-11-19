package sessionmanager

import (
    "github.com/jinzhu/gorm"
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
)

func Builder() *builder {
    return &builder{
        secWebSocketKey: "",
        hostExtId:       "",
        hostId:          "",
        memberId:        "",
        gameId:          "",
        db:              nil,
    }
}

type builder struct {
    secWebSocketKey string
    hostExtId       string
    hostId          string
    memberId        string
    gameId          string
    db              *gorm.DB
}

type sessionManager struct {
    hostExtId  string
    isStarted  bool
    db         *gorm.DB
    sessionMap *sessionMap
}

// database table session_map
type sessionMap struct {
    Id        string // secWebSocketKey
    HostId    string
    MemberId  string
    GameId    string
    SubgameId int
    ServerId  string
    KickOut   int
}

func (b *builder) setSecWebSocketKey(secWebSocketKey string) *builder {
    b.secWebSocketKey = secWebSocketKey
    return b
}

func (b *builder) setHostExtId(hostExtId string) *builder {
    b.hostExtId = hostExtId
    return b
}

func (b *builder) setHostId(hostId string) *builder {
    b.hostId = hostId
    return b
}

func (b *builder) setMemberId(memberId string) *builder {
    b.memberId = memberId
    return b
}

func (b *builder) setGameId(gameId string) *builder {
    b.gameId = gameId
    return b
}

func (b *builder) setDB(hostExtId string) *builder {
    if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
        b.db = db
    } else {
        logger.Service.Zap.Errorw(SessionManager_GAME_DB_NOT_FOUND,
            "GameUser", b.secWebSocketKey,
            "HostExtId", hostExtId,
            "Error", err,
        )
        errorcode.Service.Fatal(b.secWebSocketKey, SessionManager_GAME_DB_NOT_FOUND)
    }
    return b
}

func (b *builder) build() *sessionManager {
    return &sessionManager{
        hostExtId: b.hostExtId,
        isStarted: true,
        db:        b.db,
        sessionMap: &sessionMap{
            Id:        b.secWebSocketKey,
            HostId:    b.hostId,
            MemberId:  b.memberId,
            GameId:    b.gameId,
            SubgameId: -1,
            ServerId:  Service.ServerId,
            KickOut:   0,
        },
    }
}
