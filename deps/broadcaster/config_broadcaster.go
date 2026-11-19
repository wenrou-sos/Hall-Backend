package broadcaster

import (
	"crypto/sha1"
	"fmt"
)

type ConfigBroadcaster struct {
	gameId       string
	betList      string
	rateList     string
	mathModuleId string
	bet          uint64
	rate         uint64
}

func NewConfigBroadcaster(gameId, betList, rateList, mathModuleId string, bet, rate uint64) *ConfigBroadcaster {
	return &ConfigBroadcaster{
		gameId:       gameId,
		betList:      betList,
		rateList:     rateList,
		mathModuleId: mathModuleId,
		bet:          bet,
		rate:         rate,
	}
}

func (c *ConfigBroadcaster) Id() string {
	if c.mathModuleId == "" {
		return fmt.Sprintf("%x", sha1.Sum([]byte(c.gameId+c.betList+c.rateList)))
	} else {
		return fmt.Sprintf("%x", sha1.Sum([]byte(c.gameId+c.betList+c.rateList+c.mathModuleId)))
	}
}

func (c *ConfigBroadcaster) MinCent() (cent uint64) {
	return c.bet * c.rate * BigWinPay
}
