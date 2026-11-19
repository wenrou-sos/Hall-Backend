//+build staging prod

package sessionmanager

import (
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
    "time"
)

func init() {
    Service.clean()
    go Service.kickOut()
}

func (s *service) kickOut() {
    t := time.NewTicker(1 * time.Second)

    defer func() {
        t.Stop()

        logger.Service.Zap.Errorw(SessionManager_POLLING_KICKOUT_STOP,
            "ServiceId", s.ServerId,
        )
    }()

    for {
        <-t.C

        for _, v := range mysql.Repository.GameDBs() {
            if rows, err := v.Table("session_map").
                Where("server_id = ?", s.ServerId).
                Rows(); err == nil {

                for rows.Next() {
                    dbResult := &sessionMap{}

                    if err := v.ScanRows(rows, &dbResult); err == nil {

                        if dbResult.KickOut == 1 {
                            logger.Service.Zap.Warnw(SessionManager_DUPICATE_SESSION,
                                "GameUser", dbResult.Id,
                                "HostId", dbResult.HostId,
                                "MemberId", dbResult.MemberId,
                                "GameId", dbResult.GameId,
                                "SubGameId", dbResult.SubgameId,
                                "ServerId", dbResult.ServerId,
                                "KickOut", dbResult.KickOut,
                            )
                            errorcode.Service.Fatal(dbResult.Id, SessionManager_DUPICATE_SESSION)

                            v.Table("session_map").
                                Where("id = ?", dbResult.Id).
                                Delete(dbResult.Id)
                        }
                    }
                }
                rows.Close()
            }
        }
    }
}

func (s *service) Start(secWebSocketKey, hostExtId, hostId, memberId, gameId string) {
    s.rwMutex.Lock()
    defer s.rwMutex.Unlock()

    if v, ok := s.sessionManagers[secWebSocketKey]; ok {
        if v.isStarted {
            return
        }
        delete(s.sessionManagers, secWebSocketKey)
    }

    sm := Builder().
        setSecWebSocketKey(secWebSocketKey).
        setHostExtId(hostExtId).
        setHostId(hostId).
        setMemberId(memberId).
        setGameId(gameId).
        setDB(hostExtId).
        build()

    s.sessionManagers[secWebSocketKey] = sm

    go func() {
        count := 0
        t1 := time.NewTicker(1 * time.Second)

        defer func() {
            t1.Stop()

            if count == retryTimes {
                logger.Service.Zap.Errorw(SessionManager_INSERT_SESSION_TIMEOUT,
                    "GameUser", secWebSocketKey,
                    "HostExtId", sm.hostExtId,
                    "HostId", sm.sessionMap.HostId,
                    "MemberId", sm.sessionMap.MemberId,
                    "GameId", sm.sessionMap.GameId,
                    "SubGameId", sm.sessionMap.SubgameId,
                    "ServerId", sm.sessionMap.ServerId,
                    "KickOut", sm.sessionMap.KickOut,
                )
                errorcode.Service.Fatal(secWebSocketKey, SessionManager_INSERT_SESSION_TIMEOUT)
                s.queryDelete(secWebSocketKey, sm.hostExtId)

                s.rwMutex.Lock()
                delete(s.sessionManagers, secWebSocketKey)
                s.rwMutex.Unlock()
            }
        }()

        for {
            count++

            dbResult := s.querySelect(sm)

            if dbResult != nil && dbResult.ServerId == s.ServerId {
                logger.Service.Zap.Warnw(SessionManager_DUPICATE_SESSION,
                    "GameUser", dbResult.Id,
                    "HostId", dbResult.HostId,
                    "MemberId", dbResult.MemberId,
                    "GameId", dbResult.GameId,
                    "SubGameId", dbResult.SubgameId,
                    "ServerId", dbResult.ServerId,
                    "KickOut", dbResult.KickOut,
                )
                errorcode.Service.Fatal(dbResult.Id, SessionManager_DUPICATE_SESSION)

                s.queryDelete(dbResult.Id, sm.hostExtId)

                s.rwMutex.Lock()
                delete(s.sessionManagers, dbResult.Id)
                s.rwMutex.Unlock()
            }

            if dbResult != nil && dbResult.ServerId != s.ServerId {
                s.queryUpdate(sm)
            }

            if dbResult == nil {
                s.queryInsert(sm)
                return
            }

            if count == retryTimes {
                return
            }

            <-t1.C
        }
    }()
}

func (s *service) querySelect(sm *sessionManager) *sessionMap {
    secWebSocketKey := sm.sessionMap.Id

    dbResult := &sessionMap{}

    if ok := sm.db.Table("session_map").
        Where("host_id = ? AND member_id = ? AND game_id = ?",
            sm.sessionMap.HostId,
            sm.sessionMap.MemberId,
            sm.sessionMap.GameId,
        ).
        Scan(dbResult).
        RowsAffected; ok == 1 {

        logger.Service.Zap.Infow("Get Session Map",
            "GameUser", secWebSocketKey,
            "HostExtId", sm.hostExtId,
            "HostId", dbResult.HostId,
            "MemberId", dbResult.MemberId,
            "GameId", dbResult.GameId,
            "SubGameId", dbResult.SubgameId,
            "ServerId", dbResult.ServerId,
            "KickOut", dbResult.KickOut,
        )
        return dbResult
    }
    return nil
}

func (s *service) queryInsert(sm *sessionManager) {
    secWebSocketKey := sm.sessionMap.Id

    if ok := sm.db.Table("session_map").Create(sm.sessionMap).RowsAffected; ok == 1 {
        logger.Service.Zap.Infow("Insert Session Map",
            "GameUser", secWebSocketKey,
            "HostExtId", sm.hostExtId,
            "HostId", sm.sessionMap.HostId,
            "MemberId", sm.sessionMap.MemberId,
            "GameId", sm.sessionMap.GameId,
            "SubGameId", sm.sessionMap.SubgameId,
            "ServerId", sm.sessionMap.ServerId,
            "KickOut", sm.sessionMap.KickOut,
        )

        s.rwMutex.Lock()
        sm.isStarted = true
        s.rwMutex.Unlock()
    } else {
        logger.Service.Zap.Errorw(SessionManager_INSERT_SESSION_MAP_FAILED,
            "GameUser", secWebSocketKey,
            "HostExtId", sm.hostExtId,
            "HostId", sm.sessionMap.HostId,
            "MemberId", sm.sessionMap.MemberId,
            "GameId", sm.sessionMap.GameId,
            "SubGameId", sm.sessionMap.SubgameId,
            "ServerId", sm.sessionMap.ServerId,
            "KickOut", sm.sessionMap.KickOut,
        )
        errorcode.Service.Fatal(secWebSocketKey, SessionManager_INSERT_SESSION_MAP_FAILED)

        s.rwMutex.Lock()
        sm.isStarted = false
        s.rwMutex.Unlock()
    }
}

func (s *service) queryUpdate(sm *sessionManager) {
    secWebSocketKey := sm.sessionMap.Id

    if ok := sm.db.Table("session_map").
        Where("host_id = ? AND member_id = ? AND game_id = ?",
            sm.sessionMap.HostId,
            sm.sessionMap.MemberId,
            sm.sessionMap.GameId,
        ).
        UpdateColumn("kick_out", 1).
        RowsAffected; ok != 1 {
        logger.Service.Zap.Warnw(SessionManager_UPDATE_SESSION_MAP_FAILED,
            "GameUser", secWebSocketKey,
            "HostExtId", sm.hostExtId,
            "HostId", sm.sessionMap.HostId,
            "MemberId", sm.sessionMap.MemberId,
            "GameId", sm.sessionMap.GameId,
            "SubGameId", sm.sessionMap.SubgameId,
            "ServerId", sm.sessionMap.ServerId,
            "KickOut", sm.sessionMap.KickOut,
        )
    }
}

func (s *service) queryDelete(secWebSocketKey, hostExtId string) {
    if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
        db.Table("session_map").
            Where("id = ?", secWebSocketKey).
            Delete(secWebSocketKey)
    } else {
        logger.Service.Zap.Errorw(SessionManager_GAME_DB_NOT_FOUND,
            "GameUser", secWebSocketKey,
            "HostExtId", hostExtId,
            "Error", err,
        )
        errorcode.Service.Fatal(secWebSocketKey, SessionManager_GAME_DB_NOT_FOUND)
    }
}

func (s *service) End(secWebSocketKey, hostExtId string) {
    s.rwMutex.Lock()
    defer s.rwMutex.Unlock()

    s.queryDelete(secWebSocketKey, hostExtId)
    delete(s.sessionManagers, secWebSocketKey)
}
