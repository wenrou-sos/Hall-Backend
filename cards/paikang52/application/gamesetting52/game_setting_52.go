package gamesetting52

// table host_52_game
type host52Game struct {
	HostId                string
	GameId                string
	SubGameId             uint32
	MathId                string
	Langs                 string
	BetList               string
	RateList              string
	BalanceLimit          string
	BankerLimit           string
	WaitingTime           string
	TransferCredit        string
	SessionTimeout        uint32
	IpConfig              uint32
	RoomConfig            uint32
	BankerConfig          uint32
	HostConnectConfig     uint32
	Fee                   uint32
	IdBlockPercent        int
	UnluckyRate           string
	BlacklistCondition    string
	IsolateRate           string
	AutoBlacklistValue    string
	BlacklistRoundCount   string
	BlacklistTriggerCount string
}

type selected52Game struct {
	hostId                string
	gameId                string
	subGameId             uint32
	mathModuleId          []int
	betList               string // for game room id used
	rateList              string // for game room id used
	bet                   uint32
	langs                 []string
	rateIndex             uint32
	balanceLimit          uint32
	bankerLimit           uint32
	waitingTime           []uint32 // round start, bet, draw
	transferCredit        []uint32
	sessionTimeout        uint32
	ipConfig              uint32
	roomConfig            uint32
	bankerConfig          uint32
	hostConnectConfig     uint32
	fee                   uint32
	idBlockPercent        int
	UnluckyRate           []int
	blacklistCondition    int
	isolateRate           int
	autoBlacklistValue    uint64
	blacklistRoundCount   uint32
	blacklistTriggerCount uint32
}
