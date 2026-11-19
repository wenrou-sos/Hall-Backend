package accounting

import "gitlab.iplaystar.net/game-server/common"

const (
    Accounting_ACCOUNTING_NOT_FOUND    = common.Accounting + "0"
    Accounting_START_ACCOUNTING_FAILED = common.Accounting + "1"
    Accounting_END_ACCOUNTING_FAILED   = common.Accounting + "2"
    Accounting_GAME_ID_INVALID         = common.Accounting + "3"
    Accounting_BONUS_TYPE_INVALID      = common.Accounting + "4"
    Accounting_GAME_DB_NOT_FOUND       = common.Accounting + "5"
)
