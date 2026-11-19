package gameroom

func LeaveBuilder() *leaveBuilder {
	return &leaveBuilder{
		controllerId:    "",
		secWebSocketKey: "",
		gameRoomUuid:    "",
		kind:            "",
	}
}

type leaveBuilder struct {
	controllerId    string
	secWebSocketKey string
	gameRoomUuid    string
	kind            string
}

type Leave struct {
	controllerId    string
	SecWebSocketKey string
	GameRoomUuid    string
	Kind            string
}

func (b *leaveBuilder) SetControllerId(controllerId string) *leaveBuilder {
	b.controllerId = controllerId
	return b
}

func (b *leaveBuilder) SetSecWebSocketKey(secWebSocketKey string) *leaveBuilder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *leaveBuilder) SetGameRoomUuid(gameRoomUuid string) *leaveBuilder {
	b.gameRoomUuid = gameRoomUuid
	return b
}

func (b *leaveBuilder) SetKind(kind string) *leaveBuilder {
	b.kind = kind
	return b
}

func (b *leaveBuilder) Build() *Leave {
	return &Leave{
		controllerId:    b.controllerId,
		SecWebSocketKey: b.secWebSocketKey,
		GameRoomUuid:    b.gameRoomUuid,
		Kind:            b.kind,
	}
}
