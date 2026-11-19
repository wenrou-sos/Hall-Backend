package bet

import "colorgame-game-server/models"

const (
	Bet_PROTO_BET_CALL_INVAILD = models.Bet + "0"
	Bet_BET_INDEX_INVAILD      = models.Bet + "1"
	Bet_BALANCE_NOT_ENOUGHT    = models.Bet + "2"
	Bet_AREA_REACH_LIMIT       = models.Bet + "3"
	Bet_ROUND_END              = models.Bet + "4"
	Bet_SEAT_INVAILD           = models.Bet + "5"
)
