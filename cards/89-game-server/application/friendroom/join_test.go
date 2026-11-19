package friendroom

import (
	"testing"

	"gitlab.iplaystar.net/game-server/format"
	macaddress "gitlab.iplaystar.net/game-server/mac-address"
)

func Test_Join(t *testing.T) {
	r := &room{
		Uuid:   "A",
		Number: 123456789,
		Size:   6,
		Status: IDLE,
	}

	p := &player{
		ServerId:  format.ServerId(macaddress.Get()),
		Uid:       "ASDFGHJKL",
		Name:      "JOHNNY",
		Avatar:    "12",
		Kind:      PLAYER,
		Balance:   999888777,
		IsHost:    true,
		ipAddress: "123456",
	}

	Join.do("552e233a0fa3d97d4ff2bc93812a04e4", r.Number, p)
}
