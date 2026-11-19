package sessionmanager

import "gitlab.iplaystar.net/game-server/common"

const (
    SessionManager_DUPICATE_SESSION          = common.SessionManager + "0"
    SessionManager_SESSION_NOT_FOUND         = common.SessionManager + "1"
    SessionManager_INSERT_SESSION_MAP_FAILED = common.SessionManager + "2"
    SessionManager_GAME_DB_NOT_FOUND         = common.SessionManager + "3"
    SessionManager_POLLING_KICKOUT_STOP      = common.SessionManager + "4"
    SessionManager_UPDATE_SESSION_MAP_FAILED = common.SessionManager + "5"
    SessionManager_INSERT_SESSION_TIMEOUT    = common.SessionManager + "6"
)
