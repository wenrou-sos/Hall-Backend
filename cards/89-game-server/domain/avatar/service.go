package avatar

import (
    "crypto/rand"
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
    "math/big"
    "strconv"
)

var Service = &service{}

type service struct {
}

func (s *service) Create(secWebSocketKey, hostExtId, hostId, memberId string) string {
    avatar := s.Random()

    if db, err := mysql.Repository.GameDB(hostExtId); err == nil {

        if ok := db.Table("member").
            Where("id = ? AND host_id = ?", memberId, hostId).
            UpdateColumn("avatar", avatar).
            RowsAffected; ok != 1 {
            logger.Service.Zap.Errorw(Avatar_UPDATE_MEMBER_FAILED,
                "GameUser", secWebSocketKey,
                "MemberId", memberId,
                "HostId", hostId,
                "HostExtId", hostExtId,
                "Error", err,
            )
            errorcode.Service.Fatal(secWebSocketKey, Avatar_UPDATE_MEMBER_FAILED)
        }
    } else {
        logger.Service.Zap.Errorw(Avatar_GAME_DB_NOT_FOUND,
            "GameUser", secWebSocketKey,
            "MemberId", memberId,
            "HostId", hostId,
            "HostExtId", hostExtId,
            "Error", err,
        )
        errorcode.Service.Fatal(secWebSocketKey, Avatar_GAME_DB_NOT_FOUND)
    }
    return avatar
}

func (s *service) Random() string {
    n, err := rand.Int(rand.Reader, big.NewInt(16))

    if err != nil {
        panic(err)
    }

    return strconv.FormatUint(n.Uint64(), 10)
}
