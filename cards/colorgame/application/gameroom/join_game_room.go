package gameroom

func JoinBuilder() *joinBuilder {
	return &joinBuilder{
		controllerId:          "",
		secWebSocketKey:       "",
		reconnectWebSocketKey: "",
		gameRoomUuid:          "",
		avatar:                "",
		gameId:                "",
		betList:               "",
		rateList:              "",
		rate:                  0,
		rateIndex:             0,
		kind:                  "",
		hostExtId:             "",
		ipblock:               0,
		hostblock:             0,
		lastRoomId:            "",
		vipInfo:               nil,
	}
}

type joinBuilder struct {
	controllerId          string
	secWebSocketKey       string
	reconnectWebSocketKey string
	gameRoomUuid          string
	avatar                string
	gameId                string
	betList               string
	rateList              string
	rateIndex             int
	rate                  uint32
	kind                  string
	hostId                string
	hostExtId             string
	ipblock               uint32
	hostblock             uint32
	ipaddress             string
	lastRoomId            string
	vipInfo               *vipInfo //only vip room use
}

type Join struct {
	controllerId          string
	SecWebSocketKey       string
	ReconnectWebSocketKey string
	GameRoomUuid          string
	Avatar                string
	gameId                string
	betList               string
	rateList              string
	rateIndex             int
	rate                  uint32
	Seat                  int
	Kind                  string
	HostId                string
	HostExtId             string
	IPBlock               uint32
	HostBlock             uint32
	IPAddress             string
	NoneBetCount          int
	lastRoomId            string
	vipInfo               *vipInfo
}

func (b *joinBuilder) SetControllerId(controllerId string) *joinBuilder {
	b.controllerId = controllerId
	return b
}

func (b *joinBuilder) SetSecWebSocketKey(secWebSocketKey string) *joinBuilder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *joinBuilder) SetReconnectWebSocketKey(reconnectWebSocketKey string) *joinBuilder {
	b.reconnectWebSocketKey = reconnectWebSocketKey
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

func (b *joinBuilder) SetRateIndex(rateIndex uint32) *joinBuilder {
	b.rateIndex = int(rateIndex)
	return b
}

func (b *joinBuilder) SetKind(kind string) *joinBuilder {
	b.kind = kind
	return b
}

func (b *joinBuilder) SetHostId(hostId string) *joinBuilder {
	b.hostId = hostId
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

func (b *joinBuilder) SetLastRoomId(lastRoomId string) *joinBuilder {
	b.lastRoomId = lastRoomId
	return b
}

func (b *joinBuilder) SetVipInfo(secWebSocketKey, hostId, memberId, gameid, lastRoomId string, histories [10][3]int32, billCurrency string, isVipChangeRoom bool) *joinBuilder {
	b.vipInfo = &vipInfo{
		secWebSocketKey: secWebSocketKey,
		level:           0,
		hostId:          hostId,
		memberId:        memberId,
		gameid:          gameid,
		lastRoomId:      lastRoomId,
		histories:       histories,
		billCurrency:    billCurrency,
		isVipChangeRoom: isVipChangeRoom,
	}
	return b
}

func (b *joinBuilder) Build() *Join {
	return &Join{
		controllerId:          b.controllerId,
		SecWebSocketKey:       b.secWebSocketKey,
		ReconnectWebSocketKey: b.secWebSocketKey,
		GameRoomUuid:          b.gameRoomUuid,
		Avatar:                b.avatar,
		gameId:                b.gameId,
		betList:               b.betList,
		rateList:              b.rateList,
		rate:                  b.rate,
		rateIndex:             b.rateIndex,
		Seat:                  -1,
		Kind:                  b.kind,
		HostId:                b.hostId,
		HostExtId:             b.hostExtId,
		IPBlock:               b.ipblock,
		HostBlock:             b.hostblock,
		IPAddress:             b.ipaddress,
		lastRoomId:            b.lastRoomId,
		vipInfo:               b.vipInfo,
	}
}

func (j *Join) hashId() string {
	return Service.hashId(j.gameId, j.betList, j.rateList, j.rate)
}
