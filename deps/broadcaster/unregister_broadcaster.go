package broadcaster

import (
	"crypto/sha1"
	"fmt"
)

type UnRegisterBroadcaster struct {
	roomUuid     string
	gameId       string
	betList      string
	rateList     string
	mathModuleId string
	rate         uint64
}

func NewUnRegisterBroadcaster(roomUuid, gameId, betList, rateList, mathModuleId string, rate uint64) *UnRegisterBroadcaster {
	return &UnRegisterBroadcaster{
		roomUuid:     roomUuid,
		gameId:       gameId,
		betList:      betList,
		rateList:     rateList,
		mathModuleId: mathModuleId,
		rate:         rate,
	}
}

func (u *UnRegisterBroadcaster) Id() string {
	if u.mathModuleId == "" {
		return fmt.Sprintf("%x", sha1.Sum([]byte(u.gameId+u.betList+u.rateList)))
	} else {
		return fmt.Sprintf("%x", sha1.Sum([]byte(u.gameId+u.betList+u.rateList+u.mathModuleId)))
	}
}
