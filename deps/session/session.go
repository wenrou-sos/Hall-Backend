package session

type Session struct {
    secWebSocketKey string // not used yet
    hostExtId       string
    isStarted       bool
    addSession      *addSession
    deleteSession   *deleteSession
}

type addSession struct {
    sessionId    string
    hostId       string
    memberId     string
    gameId       string
    subGameId    uint32
    serverId     string
    remoteIp     string
    userAgent    string
    protoVersion uint32
    gameRevision uint32
}

type deleteSession struct {
    sessionId string
    hostId    string
    memberId  string
    gameTimes uint64
}

func newSession(
    secWebSocketKey,
    hostExtId,
    hostId,
    memberId,
    gameId string,
    subGameId uint32,
    serverId, remoteIp, userAgent string,
    protoVersion, gameRevision uint32) *Session {
    return &Session{
        secWebSocketKey: secWebSocketKey, // not used yet
        hostExtId:       hostExtId,
        isStarted:       false,
        addSession: &addSession{
            sessionId:    secWebSocketKey,
            hostId:       hostId,
            memberId:     memberId,
            gameId:       gameId,
            subGameId:    subGameId,
            serverId:     serverId,
            remoteIp:     remoteIp,
            userAgent:    userAgent,
            protoVersion: protoVersion,
            gameRevision: gameRevision,
        },
        deleteSession: &deleteSession{
            sessionId: secWebSocketKey,
            hostId:    hostId,
            memberId:  memberId,
        },
    }
}
