//+build dev

package session

func init() {
    // do nothing
}

func (s *service) New(secWebSocketKey, hostExtId, hostId, memberId, gameId string,
    subGameId uint32,
    remoteIp, userAgent string,
    protoVersion, gameRevision uint32) {
    // do nothing
}

func (s *service) Start(secWebSocketKey string) {
    // do nothing
}

func (s *service) End(secWebSocketKey, hostId, hostExtId, memberId string, rounds uint64) {
    // do nothing
}
