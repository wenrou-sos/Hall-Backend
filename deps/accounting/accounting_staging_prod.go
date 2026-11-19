//+build staging prod

package accounting

import (
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
)

func (b *builder) SetDB(hostExtId string) *builder {
    if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
        b.db = db
    } else {
        logger.Service.Zap.Errorw(Accounting_GAME_DB_NOT_FOUND,
            "GameUser", b.secWebSocketKey,
            "HostId", b.hostId,
            "HostExtId", b.hostExtId,
            "GameId", b.gameId,
            "SubgameId", b.subgameId,
            "MemberId", b.memberId,
            "StartBalance", b.initCent,
            "Denom", b.denom,
            "GameModule", b.gameModule,
            "Error", err,
        )
        errorcode.Service.Fatal(b.secWebSocketKey, Accounting_GAME_DB_NOT_FOUND)
    }
    return b
}
