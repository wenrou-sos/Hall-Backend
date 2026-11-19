package gameroom

import "strings"

func JoinBuilder() *joinBuilder {
	return &joinBuilder{
		controllerId:    "",
		secWebSocketKey: "",
		gameRoomUuid:    "",
		avatar:          "",
		gameId:          "",
		bet:             0,
		kind:            "",
		hostExtId:       "",
		ipblock:         0,
		hostblock:       0,
		blacklistValue:  0,
		hostId:          "",
		fee:             0,
		memberType:      0,
		isIsolated:      false,
	}
}

type joinBuilder struct {
	controllerId    string
	secWebSocketKey string
	gameRoomUuid    string
	avatar          string
	gameId          string
	bet             uint64
	kind            string
	hostExtId       string
	ipblock         uint32
	hostblock       uint32
	ipaddress       []string
	blacklistValue  uint32
	hostId          string
	fee             uint32
	memberType      int
	isIsolated      bool
}

type Join struct {
	controllerId    string
	SecWebSocketKey string
	GameRoomUuid    string
	avatar          string
	gameId          string
	bet             uint64
	Seat            int
	Kind            string
	HostExtId       string
	IPBlock         uint32
	HostBlock       uint32
	IPAddress       []string
	winCount        uint32
	blacklistValue  uint32
	HostId          string
	fee             uint32
	memberType      int
	isIsolated      bool
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

func (b *joinBuilder) SetBet(bet uint64) *joinBuilder {
	b.bet = bet
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
	for _, v := range strings.Split(adderss, ".") {
		b.ipaddress = append(b.ipaddress, v)
	}
	return b
}
func (b *joinBuilder) SetBlacklistValue(value uint32) *joinBuilder {
	b.blacklistValue = value
	return b
}
func (b *joinBuilder) SetHostId(hostId string) *joinBuilder {
	b.hostId = hostId
	return b
}
func (b *joinBuilder) SetFee(fee uint32) *joinBuilder {
	b.fee = fee
	return b
}
func (b *joinBuilder) SetMemberType(memberType int) *joinBuilder {
	b.memberType = memberType
	return b
}
func (b *joinBuilder) SetIsIsolated(isIsolated bool) *joinBuilder {
	b.isIsolated = isIsolated
	return b
}
func (b *joinBuilder) Build() *Join {
	return &Join{
		controllerId:    b.controllerId,
		SecWebSocketKey: b.secWebSocketKey,
		GameRoomUuid:    b.gameRoomUuid,
		avatar:          b.avatar,
		gameId:          b.gameId,
		bet:             b.bet,
		Seat:            -1,
		Kind:            b.kind,
		HostExtId:       b.hostExtId,
		IPBlock:         b.ipblock,
		HostBlock:       b.hostblock,
		IPAddress:       b.ipaddress,
		winCount:        0,
		blacklistValue:  b.blacklistValue,
		HostId:          b.hostId,
		fee:             b.fee,
		memberType:      b.memberType,
		isIsolated:      b.isIsolated,
	}
}

func (j *Join) hashId() string {
	return Service.hashId(j.gameId, j.bet)
}
