package waitingroom

func JoinBuilder() *joinBuilder {
    return &joinBuilder{
        secWebSocketKey: "",
        hostExtId:       "",
        gameId:          "",
        betList:         "",
        rateList:        "",
        rate:            0,
        balance:         0,
    }
}

type joinBuilder struct {
    secWebSocketKey string
    hostExtId       string
    gameId          string
    betList         string
    rateList        string
    rate            uint32
    balance         uint64
}

type Join struct {
    secWebSocketKey string
    hostExtId       string
    gameId          string
    betList         string
    rateList        string
    rate            uint32
    balance         uint64
}

func (b *joinBuilder) SetSecWebSocketKey(secWebSocketKey string) *joinBuilder {
    b.secWebSocketKey = secWebSocketKey
    return b
}

func (b *joinBuilder) SetHostExtId(hostExtId string) *joinBuilder {
    b.hostExtId = hostExtId
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

func (b *joinBuilder) SetBalance(balance uint64) *joinBuilder {
    b.balance = balance
    return b
}

func (b *joinBuilder) Build() *Join {
    return &Join{
        secWebSocketKey: b.secWebSocketKey,
        hostExtId:       b.hostExtId,
        gameId:          b.gameId,
        betList:         b.betList,
        rateList:        b.rateList,
        rate:            b.rate,
        balance:         b.balance,
    }
}

func (j *Join) HashId() string {
    return Service.hashId(j.gameId, j.betList, j.rateList, j.rate)
}
