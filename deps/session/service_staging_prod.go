//+build staging prod

package session

import (
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
)

func init() {
    Service.clean()
}

func (s *service) New(secWebSocketKey, hostExtId, hostId, memberId, gameId string,
    subGameId uint32,
    remoteIp, userAgent string,
    protoVersion, gameRevision uint32) {
    s.mutex.Lock()
    defer s.mutex.Unlock()

    if _, ok := s.usersSession[secWebSocketKey]; ok {
        return
    }

    s.usersSession[secWebSocketKey] = newSession(
        secWebSocketKey,
        hostExtId,
        hostId,
        memberId,
        gameId,
        subGameId,
        s.ServerId,
        remoteIp,
        userAgent,
        protoVersion,
        gameRevision,
    )
}

func (s *service) Start(secWebSocketKey string) {
    s.mutex.Lock()
    defer s.mutex.Unlock()

    if v, ok := s.usersSession[secWebSocketKey]; ok {
        if v.isStarted {
            return
        }

        if db, err := mysql.Repository.GameDB(v.hostExtId); err == nil {
            if ok := db.Exec("CALL add_session(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                v.addSession.sessionId,
                v.addSession.hostId,
                v.addSession.memberId,
                v.addSession.gameId,
                v.addSession.subGameId,
                v.addSession.serverId,
                v.addSession.remoteIp,
                v.addSession.userAgent,
                v.addSession.protoVersion,
                v.addSession.gameRevision,
            ).RowsAffected; ok != 1 {
                logger.Service.Zap.Errorw(Session_EXEC_STORED_PROCEDURE_FAILED,
                    "GameUser", secWebSocketKey,
                    "HostExtId", v.hostExtId,
                    "Error", err,
                )
                errorcode.Service.Fatal(secWebSocketKey, Session_EXEC_STORED_PROCEDURE_FAILED)
                return
            }

            v.isStarted = true
        } else {
            logger.Service.Zap.Errorw(Session_GAME_DB_NOT_FOUND,
                "GameUser", secWebSocketKey,
                "HostExtId", v.hostExtId,
                "Error", err,
            )
            errorcode.Service.Fatal(secWebSocketKey, Session_GAME_DB_NOT_FOUND)
        }
    } else {
        logger.Service.Zap.Errorw(Session_NOT_FOUND,
            "GameUser", secWebSocketKey,
        )
        errorcode.Service.Fatal(secWebSocketKey, Session_NOT_FOUND)
    }
}

func (s *service) End(secWebSocketKey, hostId, hostExtId, memberId string, rounds uint64) {
    s.mutex.Lock()
    defer s.mutex.Unlock()

    if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
        if ok := db.Exec("CALL delete_session_20181123(?, ?, ?, ?)",
            secWebSocketKey,
            hostId,
            memberId,
            rounds,
        ).RowsAffected; ok != 1 {
            logger.Service.Zap.Errorw(Session_EXEC_STORED_PROCEDURE_FAILED,
                "GameUser", secWebSocketKey,
                "MemberId", memberId,
                "HostId", hostId,
                "HostExtId", hostExtId,
                "Error", err,
            )
            errorcode.Service.Fatal(secWebSocketKey, Session_EXEC_STORED_PROCEDURE_FAILED)
        }
    } else {
        logger.Service.Zap.Errorw(Session_GAME_DB_NOT_FOUND,
            "GameUser", secWebSocketKey,
            "MemberId", memberId,
            "HostId", hostId,
            "HostExtId", hostExtId,
            "Error", err,
        )
        errorcode.Service.Fatal(secWebSocketKey, Session_GAME_DB_NOT_FOUND)
    }
    delete(s.usersSession, secWebSocketKey)
}
