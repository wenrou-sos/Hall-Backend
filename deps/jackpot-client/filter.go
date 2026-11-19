package jackpot_client

import (
	"errors"
	"fmt"
	"github.com/gogo/protobuf/proto"
	jackpot_proto "gitlab.iplaystar.net/game-server/jackpot-client/proto"
)

func parseHeaderJackpot(msg []byte) *jackpot_proto.Header {
	header := &jackpot_proto.Header{}

	if err := proto.Unmarshal(msg, header); err != nil {
		return nil
	}
	return header
}

func FindActionName(msg []byte) (header string, err error) {
	if headerJackpot := parseHeaderJackpot(msg); headerJackpot != nil {
		switch headerJackpot.MessageId {
		case jackpot_proto.MessageID_kHitInfo:
			return EMSGID_kHitInfo, nil
		case jackpot_proto.MessageID_kGroupInfoMap:
			return EMSGID_kGroupInfoMap, nil
		case jackpot_proto.MessageID_kNotifyInfo:
			return EMSGID_kNotifyInfo, nil
		default:
			return "", errors.New(fmt.Sprintf("Unknown MSGID : %s", headerJackpot.MessageId))
		}
	}

	return "", errors.New(fmt.Sprintf("Unknown header format %T", msg))
}