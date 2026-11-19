package broadcaster

import (
	"crypto/sha1"
	"fmt"
)

type RegisterBroadcaster struct {
	RoomUuid     string
	GameId       string
	betList      string
	rateList     string
	mathModuleId string
	Rate         uint64
}

func NewRegisterBroadcaster(roomUuid, gameId, betList, rateList, mathModuleId string, rate uint64) *RegisterBroadcaster {
	return &RegisterBroadcaster{
		RoomUuid:     roomUuid,
		GameId:       gameId,
		betList:      betList,
		rateList:     rateList,
		mathModuleId: mathModuleId,
		Rate:         rate,
	}
}

func (r *RegisterBroadcaster) Id() string {
	if r.mathModuleId == "" {
		return fmt.Sprintf("%x", sha1.Sum([]byte(r.GameId+r.betList+r.rateList)))
	} else {
		return fmt.Sprintf("%x", sha1.Sum([]byte(r.GameId+r.betList+r.rateList+r.mathModuleId)))
	}
}
