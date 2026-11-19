package wallet

import "gitlab.iplaystar.net/game-server/common"

const (
	Wallet_NOT_FOUND               = common.Wallet + "0"
	Wallet_INCREASE_BALANCE_FAILED = common.Wallet + "1"
	Wallet_DECREASE_BALANCE_FAILED = common.Wallet + "2"
	Wallet_OPEN_BALANCE_FAILED     = common.Wallet + "3"
	Wallet_GAME_DB_NOT_FOUND       = common.Wallet + "4"
	Wallet_TYPE_INVALID            = common.Wallet + "5"
	Wallet_GET_BALANCE_FAILED      = common.Wallet + "6"
	Wallet_CENT_INVALID            = common.Wallet + "7"
	Wallet_DEPOSIT_BALANCE_FAILED  = common.Wallet + "8"
	Wallet_WITHDRAW_BALANCE_FAILED = common.Wallet + "9"
	Wallet_GET_CENT_FAILED         = common.Wallet + "10"
	Wallet_INCREASE_CENT_FAILED    = common.Wallet + "11"
	Wallet_DECREASE_CENT_FAILED    = common.Wallet + "12"
	Wallet_DEPOSIT_CENT_FAILED     = common.Wallet + "13"
	Wallet_WITHDRAW_CENT_FAILED    = common.Wallet + "14"
	Wallet_INSERT_LOG_FAILED       = common.Wallet + "15"
	Wallet_REFUND_CENT_FAILED      = common.Wallet + "16"
	Wallet_REFUND_BALANCE_FAILED   = common.Wallet + "17"
)
