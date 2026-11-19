package filter

import (
	"errors"
	"fmt"
	"u-game-server/application/atm"
	"u-game-server/application/banker"
	"u-game-server/application/friendroom"
	"u-game-server/domain/draw"
	"u-game-server/domain/playcards"
	commonU_proto "u-game-server/models/proto"

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

func parseHeaderU(msg []byte) *commonU_proto.Header {
	header := &commonU_proto.Header{}

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

	if headerU := parseHeaderU(msg); headerU != nil {
		switch headerU.Msgid {
		case commonU_proto.EMSGID_eDepositCall:
			return atm.EMSGID_eDepositCall, nil

		case commonU_proto.EMSGID_eWithdrawCall:
			return atm.EMSGID_eWithdrawCall, nil

		case commonU_proto.EMSGID_eInquireCall:
			return atm.EMSGID_eInquireCall, nil

		case commonU_proto.EMSGID_eDrawCall:
			return draw.EMSGID_eDrawCall, nil

		case commonU_proto.EMSGID_eAutoTransferCall:
			return atm.EMSGID_eAutoTransferCall, nil

		case commonU_proto.EMSGID_eAutoTransferOutCall:
			return atm.EMSGID_eAutoTransferOutCall, nil

		case commonU_proto.EMSGID_eFriendRoomJoinCall:
			return friendroom.EMSGID_eFriendRoomJoinCall, nil

		case commonU_proto.EMSGID_eFriendRoomLeaveCall:
			return friendroom.EMSGID_eFriendRoomLeaveCall, nil

		case commonU_proto.EMSGID_eFriendRoomGameStart:
			return friendroom.EMSGID_eFriendRoomGameStart, nil

		case commonU_proto.EMSGID_ePlayCardsCall:
			return playcards.EMSGID_ePlayCardsCall, nil

		case commonU_proto.EMSGID_eKeepCall:
			return banker.EMSGID_eKeepCall, nil

		default:
			return "", errors.New(fmt.Sprintf("Unknown MSGID : %s", headerU.Msgid))
		}
	}
	return "", errors.New(fmt.Sprintf("Unknown header format %T.", msg))
}
