package gamerecovery89

import (
    game_recovery89_proto "89-game-server/domain/gamerecovery89/proto"
    "github.com/gogo/protobuf/proto"
    common_proto "gitlab.iplaystar.net/game-server/common/proto"
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/format"
    gamerecovery "gitlab.iplaystar.net/game-server/game-recovery-v2"
    "gitlab.iplaystar.net/game-server/logger"
    macaddress "gitlab.iplaystar.net/game-server/mac-address"
    "gitlab.iplaystar.net/game-server/mysql"
)

const (
    GAMING = 1
    IDLE   = 0
)

var Service = &service{
    Id:       "GameRecovery89",
    ServerId: format.ServerId(macaddress.Get()),
}

type service struct {
    Id       string
    ServerId string
}

func init() {
    Service.clean()
}

func (s *service) Check(r *gamerecovery.Recovery) *game_recovery89_proto.GameRecovery {
    if g := gamerecovery.Service.Open(r); g != nil {
        data := &game_recovery89_proto.GameRecovery{}

        if err := proto.Unmarshal(g.GameData, data); err != nil {
            logger.Service.Zap.Errorw(GameRecovery89_GAME_RECOVERY_PROTO_INVALID,
                "GameUser", r.SecWebSocketKey,
            )
            errorcode.Service.Fatal(r.SecWebSocketKey, GameRecovery89_GAME_RECOVERY_PROTO_INVALID)
            return nil
        }
        return data
    } else {
        data := &game_recovery89_proto.GameRecovery{
            Msgid: common_proto.EMSGID_eGameRecovery,
            Snapshot: &game_recovery89_proto.Snapshot{
                ServerId:  s.ServerId,
                RoomUuid:  "",
                Seat:      -1,
                SubgameId: -1,
                Rate:      0,
                BetIdx:    0,
                Status:    IDLE,
            },
        }

        dataByte, _ := proto.Marshal(data)

        r.GameRecovery.GameData = dataByte
        gamerecovery.Service.New(r)

        return data
    }
}

func (s *service) Update(secWebSocketKey, gameRoomUuid string, seat int32, rate uint32, status int32) {
    data := &game_recovery89_proto.GameRecovery{
        Msgid: common_proto.EMSGID_eGameRecovery,
        Snapshot: &game_recovery89_proto.Snapshot{
            ServerId:  s.ServerId,
            RoomUuid:  gameRoomUuid,
            Seat:      seat,
            SubgameId: -1,
            Rate:      rate,
            BetIdx:    0,
            Status:    status,
        },
    }

    dataByte, _ := proto.Marshal(data)

    gamerecovery.Service.Save(secWebSocketKey, dataByte)
}

func (s *service) Delete(secWebSocketKey string) {
    gamerecovery.Service.Delete(secWebSocketKey)
}

func (s *service) clean() {
    for _, db := range mysql.Repository.GameDBs() {
        db.Table("member_game_recovery_per_server").
            Where("server_id = ?", s.ServerId).
            Delete(s.ServerId)
    }
}
