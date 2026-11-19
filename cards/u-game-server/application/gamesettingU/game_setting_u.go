package gamesettingU

// table host_u_game
type hostUGame struct {
	HostId             string
	GameId             string
	SubGameId          uint32
	MathId             string
	Langs              string
	BetList            string
	RateList           string
	BalanceLimit       string
	BankerLimit        string
	RoomLimit          string
	WaitingTime        string
	TransferCredit     string
	SessionTimeout     uint32
	IpConfig           uint32
	RoomConfig         uint32
	BankerConfig       uint32
	HostConnectConfig  uint32
	Fee                uint32
	IdBlockPercent     int
	UnluckyRate        string
	BlacklistCondition string
	IsolateRate        string
	AutoBlacklistValue string
}

type selectedUGame struct {
	hostId             string
	gameId             string
	subGameId          uint32
	mathModuleId       []int
	betList            string // for game room id used
	rateList           string // for game room id used
	bet                uint32
	langs              []string
	rateIndex          uint32
	balanceLimit       uint32
	bankerLimit        uint32
	roomLimit          uint32
	waitingTime        []uint32
	transferCredit     []uint32
	sessionTimeout     uint32
	ipConfig           uint32
	roomConfig         uint32
	bankerConfig       uint32
	hostConnectConfig  uint32
	fee                uint32
	idBlockPercent     int
	unluckyRate        []int
	blacklistCondition int
	isolateRate        int
	autoBlacklistValue uint64
}
