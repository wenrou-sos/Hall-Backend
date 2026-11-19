package gamesetting89

// table host_89_game
type host89Game struct {
	HostId            string
	GameId            string
	SubGameId         uint32
	MathId            string
	Langs             string
	BetList           string
	RateList          string
	BalanceLimit      string
	BankerLimit       string
	WaitingTime       string
	TransferCredit    string
	SessionTimeout    uint32
	IpConfig          uint32
	RoomConfig        uint32
	BankerConfig      uint32
	HostConnectConfig uint32
}

type selected89Game struct {
	hostId            string
	gameId            string
	mathModuleId      string
	betList           string // for game room id used
	rateList          string // for game room id used
	bets              [1][]uint32
	rate              []uint32
	langs             []string
	rateIndex         uint32
	balanceLimit      uint32
	bankerLimit       uint32
	waitingTime       []uint32 // round start, bet, draw
	transferCredit    []uint32
	sessionTimeout    uint32
	ipConfig          uint32
	roomConfig        uint32
	bankerConfig      uint32
	hostConnectConfig uint32
}
