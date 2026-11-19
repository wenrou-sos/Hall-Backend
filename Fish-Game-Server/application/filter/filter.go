package filter

import (
    "errors"
    "fish-game-server/application/gamesetting"
    "gitlab.iplaystar.net/game-server/jackpot-client/jackpot"
    "fish-game-server/application/lobbysetting"
    "fish-game-server/domain/auth"
    "fish-game-server/domain/bullet"
    "fish-game-server/domain/fish"
    "fish-game-server/domain/probability"
    common_fish_proto "fish-game-server/models/proto"
    "fmt"
    "github.com/gogo/protobuf/proto"
    common_proto "gitlab.iplaystar.net/game-server/common/proto"
    heartbeat "gitlab.iplaystar.net/game-server/heart-beat"
)

func parseHeader(msg []byte) *common_proto.Header {
    header := &common_proto.Header{}

    if err := proto.Unmarshal(msg, header); err != nil {
        return nil
    }
    return header
}

func parseHeaderFish(msg []byte) *common_fish_proto.Header {
    header := &common_fish_proto.Header{}

    if err := proto.Unmarshal(msg, header); err != nil {
        return nil
    }
    return header
}

func FindActionName(msg []byte) (string, error) {
    if header := parseHeader(msg); header != nil {
        switch header.Msgid {
        case common_proto.EMSGID_eLoginCall:
            return auth.EMSGID_eLoginCall, nil

        case common_proto.EMSGID_eResultCall:
            return probability.EMSGID_eResultCall, nil

        case common_proto.EMSGID_eMultiResultCall:
            return probability.EMSGID_eMultiResultCall, nil

        case common_proto.EMSGID_eLobbyConfigCall:
            return lobbysetting.EMSGID_eLobbyConfigCall, nil

        case common_proto.EMSGID_eGameConfigCall:
            return gamesetting.EMSGID_eGameConfigCall, nil

        case common_proto.EMSGID_eGameStripsCall:
            return gamesetting.EMSGID_eGameStripsCall, nil

        case common_proto.EMSGID_eOptionCall:
            return probability.EMSGID_eOptionCall, nil

        case common_proto.EMSGID_eHeartbeatCall:
            return heartbeat.ActionHeartBeatCall, nil

        case common_proto.EMSGID_eCentInReask:
           return jackpot.EMSGID_eCentInReask, nil

        }
    }

    if headerFish := parseHeaderFish(msg); headerFish != nil {
        switch headerFish.Msgid {

        case common_fish_proto.EMSGID_eShoot:
            return bullet.EMSGID_eShoot, nil

        case common_fish_proto.EMSGID_eBetChange:
            return bullet.EMSGID_eBetChange, nil

        case common_fish_proto.EMSGID_eAllFishCall:
            return fish.EMSGID_eAllFishCall, nil

        case common_fish_proto.EMSGID_eMercenaryOpenCall:
            return probability.EMSGID_eMercenaryOpenCall, nil

        default:
            return "", errors.New(fmt.Sprintf("Unknown MSGID : %s", headerFish.Msgid))
        }
    }

    return "", errors.New(fmt.Sprintf("Unknown header format %T.", msg))
}
