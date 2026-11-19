package broadcaster

import (
	"crypto/sha1"
	"fmt"
)

type Broadcaster struct {
	SecWebSocketKey string
	GameId          string
	MemberId        string
	BetList         string
	RateList        string
	mathModuleId    string
	SubGameId       int
	FishId          int32
	Pay             uint64
	Cent            uint64
	Rate            uint64
}

func New(secWebSocketKey, gameId, memberId, betList, rateList, mathModuleId string, subGameId int, fishId int32, pay, cent, rate uint64) *Broadcaster {
	return &Broadcaster{
		SecWebSocketKey: secWebSocketKey,
		GameId:          gameId,
		MemberId:        memberId,
		BetList:         betList,
		RateList:        rateList,
		mathModuleId:    mathModuleId,
		SubGameId:       subGameId,
		FishId:          fishId,
		Pay:             pay,
		Cent:            cent,
		Rate:            rate,
	}
}

func (b *Broadcaster) Id() string {
	if b.mathModuleId == "" {
		return fmt.Sprintf("%x", sha1.Sum([]byte(b.GameId+b.BetList+b.RateList)))
	} else {
		return fmt.Sprintf("%x", sha1.Sum([]byte(b.GameId+b.BetList+b.RateList+b.mathModuleId)))
	}
}
