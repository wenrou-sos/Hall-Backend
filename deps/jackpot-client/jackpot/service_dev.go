//+build dev

package jackpot

import (
	jackpot_proto "gitlab.iplaystar.net/game-server/jackpot-client/proto"
	"gitlab.iplaystar.net/game-server/wallet"
)

func (s *service) InsertJackpot(jackpot *jackpot, hostExtId, secWebSocketKey string) {
	// do nothing
}

func (s *service) InsertVp1(accountingSn uint64, contributeValue float64, hostExtId, secWebSocketKey string) {
	// do nothing
}

func (s *service) UpdateJackpot(jackpot *jackpot, hostExtId, secWebSocketKey string) {
	// do nothing
}

func (s *service) Award(hitInfo *jackpot_proto.HitInfo) {
	wallet.Service.IncreaseBalance(hitInfo.ClientInfo.SessionId, hitInfo.JackpotData, hitInfo.WinningCent, 0, 0)
}
