//+build dev

package sessionmanager

import (
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
)

func init() {
    // do nothing
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

    for k, v := range s.sessionManagers {
        if v.sessionMap.HostId == hostId &&
            v.sessionMap.MemberId == memberId &&
            v.sessionMap.GameId == gameId {

            logger.Service.Zap.Errorw(SessionManager_DUPICATE_SESSION,
                "GameUser", v.sessionMap.Id,
                "HostExtId", v.hostExtId,
                "HostId", v.sessionMap.HostId,
                "MemberId", v.sessionMap.MemberId,
                "GameId", v.sessionMap.GameId,
                "SubGameId", v.sessionMap.SubgameId,
                "ServerId", v.sessionMap.ServerId,
                "KickOut", v.sessionMap.KickOut,
            )
            errorcode.Service.Fatal(k, SessionManager_DUPICATE_SESSION)
            delete(s.sessionManagers, secWebSocketKey)
        }
    }

    s.sessionManagers[secWebSocketKey] = Builder().
        setSecWebSocketKey(secWebSocketKey).
        setHostExtId(hostExtId).
        setHostId(hostId).
        setMemberId(memberId).
        setGameId(gameId).
        build()
}

func (s *service) End(secWebSocketKey, hostExtId string) {
    s.rwMutex.Lock()
    defer s.rwMutex.Unlock()

    delete(s.sessionManagers, secWebSocketKey)
}
