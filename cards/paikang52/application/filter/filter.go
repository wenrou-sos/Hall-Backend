package filter

import (
	"52-game-server/application/atm"
	"52-game-server/application/banker"
	"52-game-server/application/friendroom"
	"52-game-server/domain/draw"
	"52-game-server/domain/playcards"
	common52_proto "52-game-server/models/proto"
	"errors"
	"fmt"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/auth"
	"gitlab.iplaystar.net/game-server/avatar"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	heartbeat "gitlab.iplaystar.net/game-server/heart-beat"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
)

func parseHeader(msg []byte) *common_proto.Header {
	header := &common_proto.Header{}

	if err := proto.Unmarshal(msg, header); err != nil {
		return nil
	}
	return header
}

func parseHeader52(msg []byte) *common52_proto.Header {
	header := &common52_proto.Header{}

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

		case common_proto.EMSGID_eLobbyConfigCall:
			return lobbysetting.EMSGID_eLobbyConfigCall, nil

		case common_proto.EMSGID_eGameConfigCall:
			return gamesetting.EMSGID_eGameConfigCall, nil

		case common_proto.EMSGID_eGameStripsCall:
			return gamesetting.EMSGID_eGameStripsCall, nil

		case common_proto.EMSGID_eHeartbeatCall:
			return heartbeat.ActionHeartBeatCall, nil

		case common_proto.EMSGID_eAvatarCall:
			return avatar.EMSGID_eAvatarCall, nil
		}
	}

	if header52 := parseHeader52(msg); header52 != nil {
		switch header52.Msgid {
		case common52_proto.EMSGID_eDepositCall:
			return atm.EMSGID_eDepositCall, nil

		case common52_proto.EMSGID_eWithdrawCall:
			return atm.EMSGID_eWithdrawCall, nil

		case common52_proto.EMSGID_eInquireCall:
			return atm.EMSGID_eInquireCall, nil

		case common52_proto.EMSGID_eDrawCall:
			return draw.EMSGID_eDrawCall, nil

		case common52_proto.EMSGID_eAutoTransferCall:
			return atm.EMSGID_eAutoTransferCall, nil

		case common52_proto.EMSGID_eAutoTransferOutCall:
			return atm.EMSGID_eAutoTransferOutCall, nil

		case common52_proto.EMSGID_eFriendRoomJoinCall:
			return friendroom.EMSGID_eFriendRoomJoinCall, nil

		case common52_proto.EMSGID_eFriendRoomLeaveCall:
			return friendroom.EMSGID_eFriendRoomLeaveCall, nil

		case common52_proto.EMSGID_eFriendRoomGameStart:
			return friendroom.EMSGID_eFriendRoomGameStart, nil

		case common52_proto.EMSGID_eShowdownCall:
			return banker.EMSGID_eShowdownCall, nil

		case common52_proto.EMSGID_ePlayCardsCall:
			return playcards.EMSGID_ePlayCardsCall, nil

		default:
			return "", errors.New(fmt.Sprintf("Unknown MSGID : %s", header52.Msgid))
		}
	}
	return "", errors.New(fmt.Sprintf("Unknown header format %T.", msg))
}
