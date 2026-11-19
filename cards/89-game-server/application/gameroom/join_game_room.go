package gameroom

func JoinBuilder() *joinBuilder {
	return &joinBuilder{
		controllerId:    "",
		secWebSocketKey: "",
		gameRoomUuid:    "",
		avatar:          "",
		gameId:          "",
		betList:         "",
		rateList:        "",
		rate:            0,
		kind:            "",
		hostExtId:       "",
		ipblock:         0,
		hostblock:       0,
	}
}

type joinBuilder struct {
	controllerId    string
	secWebSocketKey string
	gameRoomUuid    string
	avatar          string
	gameId          string
	betList         string
	rateList        string
	rate            uint32
	kind            string
	hostExtId       string
	ipblock         uint32
	hostblock       uint32
	ipaddress       string
}

type Join struct {
	controllerId    string
	SecWebSocketKey string
	GameRoomUuid    string
	avatar          string
	gameId          string
	betList         string
	rateList        string
	rate            uint32
	Seat            int
	Kind            string
	HostExtId       string
	IPBlock         uint32
	HostBlock       uint32
	IPAddress       string
}

func (b *joinBuilder) SetControllerId(controllerId string) *joinBuilder {
	b.controllerId = controllerId
	return b
}

func (b *joinBuilder) SetSecWebSocketKey(secWebSocketKey string) *joinBuilder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *joinBuilder) SetAvatar(avatar string) *joinBuilder {
	b.avatar = avatar
	return b
}

func (b *joinBuilder) SetGameRoomUuid(gameRoomUuid string) *joinBuilder {
	b.gameRoomUuid = gameRoomUuid
	return b
}

func (b *joinBuilder) SetGameId(gameId string) *joinBuilder {
	b.gameId = gameId
	return b
}

func (b *joinBuilder) SetBetList(betList string) *joinBuilder {
	b.betList = betList
	return b
}

func (b *joinBuilder) SetRateList(rateList string) *joinBuilder {
	b.rateList = rateList
	return b
}

func (b *joinBuilder) SetRate(rate uint32) *joinBuilder {
	b.rate = rate
	return b
}

func (b *joinBuilder) SetKind(kind string) *joinBuilder {
	b.kind = kind
	return b
}

func (b *joinBuilder) SetHostExtId(hostExtId string) *joinBuilder {
	b.hostExtId = hostExtId
	return b
}
func (b *joinBuilder) SetIpBlock(block uint32) *joinBuilder {
	b.ipblock = block
	return b
}
func (b *joinBuilder) SetHostBlock(block uint32) *joinBuilder {
	b.hostblock = block
	return b
}
func (b *joinBuilder) SetIPAddress(adderss string) *joinBuilder {
	b.ipaddress = adderss
	return b
}
func (b *joinBuilder) Build() *Join {
	return &Join{
		controllerId:    b.controllerId,
		SecWebSocketKey: b.secWebSocketKey,
		GameRoomUuid:    b.gameRoomUuid,
		avatar:          b.avatar,
		gameId:          b.gameId,
		betList:         b.betList,
		rateList:        b.rateList,
		rate:            b.rate,
		Seat:            -1,
		Kind:            b.kind,
		HostExtId:       b.hostExtId,
		IPBlock:         b.ipblock,
		HostBlock:       b.hostblock,
		IPAddress:       b.ipaddress,
	}
}

func (j *Join) hashId() string {
	return Service.hashId(j.gameId, j.betList, j.rateList, j.rate)
}
