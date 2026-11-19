package session

import "gitlab.iplaystar.net/game-server/common"

const (
    Session_NOT_FOUND                    = common.Session + "0"
    Session_EXEC_STORED_PROCEDURE_FAILED = common.Session + "1"
    Session_GAME_DB_NOT_FOUND            = common.Session + "2"
)
