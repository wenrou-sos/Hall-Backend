package filter

import (
	"colorgame-game-server/application/gameroom"
	"colorgame-game-server/application/playerdata"
	"colorgame-game-server/domain/avatar"
	"colorgame-game-server/domain/bet"
	"colorgame-game-server/domain/walletFS"
	commonFS_proto "colorgame-game-server/models/proto"
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

func parseHeaderFS(msg []byte) *commonFS_proto.Header {
	header := &commonFS_proto.Header{}

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

	if headerFS := parseHeaderFS(msg); headerFS != nil {
		switch headerFS.Msgid {

		case commonFS_proto.EMSGID_eBetCall:
			return bet.EMSGID_eBetCall, nil

		case commonFS_proto.EMSGID_eClearBetsCall:
			return bet.EMSGID_eClearBetsCall, nil

		case commonFS_proto.EMSGID_ePlayerDataCall:
			return playerdata.EMSGID_eUserDataCall, nil

		case commonFS_proto.EMSGID_eGameroomHistoryCall:
			return gameroom.EMSGID_eGameroomHistoryCall, nil

		case commonFS_proto.EMSGID_eAvatarChangeCall:
			return avatar.EMSGID_eAvatarChangeCall, nil

		case commonFS_proto.EMSGID_eWalletBalanceCall:
			return walletFS.EMSGID_eWalletBalanceCall, nil

		case commonFS_proto.EMSGID_eMultiBetCall:
			return bet.EMSGID_eMultiBetCall, nil

		default:
			return "", errors.New(fmt.Sprintf("Unknown MSGID : %s", headerFS.Msgid))
		}
	}
	return "", errors.New(fmt.Sprintf("Unknown header format %T.", msg))
}
