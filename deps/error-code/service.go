package errorcode

import (
	"github.com/gogo/protobuf/proto"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode_proto "gitlab.iplaystar.net/game-server/error-code/proto"
	"gitlab.iplaystar.net/game-server/flux"
)

const (
	ActionErrorCode = "ActionErrorCode"
)

var Service = &service{
	id: "ErrorCodeService",
}

type service struct {
	id string
}

func (s *service) Warning(to string, code string) {
	s.send(to, errorcode_proto.Level_WARNING, code)
}

func (s *service) Error(to string, code string) {
	s.send(to, errorcode_proto.Level_ERROR, code)
}

func (s *service) Fatal(to string, code string) {
	s.send(to, errorcode_proto.Level_FATAL, code)
}

func (s *service) send(to string, level errorcode_proto.Level, code string) {
	data := &errorcode_proto.Error{
		Msgid: common_proto.EMSGID_eErrorCode,
		Code:  code,
		Level: level,
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(ActionErrorCode, s.id, to, dataByte)
}
