package gameuserU

import "u-game-server/models"

const (
	GameUserU_ACCOUNTING_SN_ZERO         = models.GameUserU + "0"
	GameUserU_ROUND_START_PROTO_INVALID  = models.GameUserU + "1"
	GameUserU_GET_CENT_FAILED            = models.GameUserU + "2"
	GameUserU_WITHDRAW_CALL_INVALID      = models.GameUserU + "3"
	GameUserU_DEPOSIT_CALL_INVALID       = models.GameUserU + "4"
	GameUserU_AUTO_TRANSFER_CALL_INVALID = models.GameUserU + "5"
)
