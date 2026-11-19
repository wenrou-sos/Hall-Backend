package atm

import "u-game-server/models"

const (
	Atm_DEPOSIT_CALL_PROTO_INVALID       = models.Atm + "0"
	Atm_WITHDRAW_CALL_PROTO_INVALID      = models.Atm + "1"
	Atm_INQUIRE_CALL_PROTO_INVALID       = models.Atm + "2"
	Atm_GET_BALANCE_FAILED               = models.Atm + "3"
	Atm_GET_CENT_FAILED                  = models.Atm + "4"
	Atm_AUTO_TRANSFER_CALL_PROTO_INVALID = models.Atm + "5"
)
