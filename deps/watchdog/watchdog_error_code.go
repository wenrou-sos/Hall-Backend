package watchdog

import "gitlab.iplaystar.net/game-server/common"

const (
    Watchdog_PATH_NOT_FOUND = common.Watchdog + "0"
    Watchdog_INTERNAL_ERROR = common.Watchdog + "1"
    Watchdog_INIT_ERROR     = common.Watchdog + "2"
)
