package filter

import (
	"89-game-server/application/atm"
	"89-game-server/application/friendroom"
	"89-game-server/domain/bet"
	"89-game-server/domain/draw"
	common89_proto "89-game-server/models/proto"
	"errors"
	"fmt"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/auth"
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

func parseHeader89(msg []byte) *common89_proto.Header {
	header := &common89_proto.Header{}

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
		}
	}

	if header89 := parseHeader89(msg); header89 != nil {
		switch header89.Msgid {
		case common89_proto.EMSGID_eDepositCall:
			return atm.EMSGID_eDepositCall, nil

		case common89_proto.EMSGID_eWithdrawCall:
			return atm.EMSGID_eWithdrawCall, nil

		case common89_proto.EMSGID_eInquireCall:
			return atm.EMSGID_eInquireCall, nil

		case common89_proto.EMSGID_eBetCall:
			return bet.EMSGID_eBetCall, nil

		case common89_proto.EMSGID_eDrawCall:
			return draw.EMSGID_eDrawCall, nil

		case common89_proto.EMSGID_eAutoTransferCall:
			return atm.EMSGID_eAutoTransferCall, nil

		case common89_proto.EMSGID_eAutoTransferOutCall:
			return atm.EMSGID_eAutoTransferOutCall, nil

		case common89_proto.EMSGID_eFriendRoomJoinCall:
			return friendroom.EMSGID_eFriendRoomJoinCall, nil

		case common89_proto.EMSGID_eFriendRoomLeaveCall:
			return friendroom.EMSGID_eFriendRoomLeaveCall, nil

		case common89_proto.EMSGID_eFriendRoomGameStart:
			return friendroom.EMSGID_eFriendRoomGameStart, nil

		default:
			return "", errors.New(fmt.Sprintf("Unknown MSGID : %s", header89.Msgid))
		}
	}
	return "", errors.New(fmt.Sprintf("Unknown header format %T.", msg))
}
