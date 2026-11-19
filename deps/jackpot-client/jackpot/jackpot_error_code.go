package jackpot

import (
	"gitlab.iplaystar.net/game-server/jackpot-client"
)

const (
	JACKPOT                                  = "900" + jackpot_client.Symbol
	Jackpot_GAME_DB_NOT_FOUND                = JACKPOT + "0"
	Jackpot_INSERT_ACCOUNTING_JACKPOT_FAILED = JACKPOT + "1"
	Jackpot_INSERT_ACCOUNTING_VP1_FAILED     = JACKPOT + "2"
	Jackpot_UPDATE_ACCOUNTING_JACKPOT_FAILED = JACKPOT + "3"
)
