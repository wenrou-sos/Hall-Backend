package waitingroom

func LeaveBuilder() *leaveBuilder {
    return &leaveBuilder{
        secWebSocketKey: "",
        gameId:          "",
        betList:         "",
        rateList:        "",
        rate:            0,
    }
}

type leaveBuilder struct {
    secWebSocketKey string
    gameId          string
    betList         string
    rateList        string
    rate            uint32
}

type leave struct {
    secWebSocketKey string
    gameId          string
    betList         string
    rateList        string
    rate            uint32
}

func (b *leaveBuilder) SetSecWebSocketKey(secWebSocketKey string) *leaveBuilder {
    b.secWebSocketKey = secWebSocketKey
    return b
}

func (b *leaveBuilder) SetGameId(gameId string) *leaveBuilder {
    b.gameId = gameId
    return b
}

func (b *leaveBuilder) SetBetList(betList string) *leaveBuilder {
    b.betList = betList
    return b
}

func (b *leaveBuilder) SetRateList(rateList string) *leaveBuilder {
    b.rateList = rateList
    return b
}

func (b *leaveBuilder) SetRate(rate uint32) *leaveBuilder {
    b.rate = rate
    return b
}

func (b *leaveBuilder) Build() *leave {
    return &leave{
        secWebSocketKey: b.secWebSocketKey,
        gameId:          b.gameId,
        betList:         b.betList,
        rateList:        b.rateList,
        rate:            b.rate,
    }
}

func (l *leave) hashId() string {
    return Service.hashId(l.gameId, l.betList, l.rateList, l.rate)
}
