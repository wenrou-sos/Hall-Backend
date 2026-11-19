package gamesettingFS

// table host_89_game
type HostFSGame struct {
	HostId            string
	GameId            string
	SubGameId         uint32
	Langs             string
	BetList           string
	RateList          string
	BalanceLimit      string
	WaitingTime       string
	SessionTimeout    uint32
	IpConfig          uint32
	RoomConfig        uint32
	HostConnectConfig uint32
	BetAreaLimit      string
}

type selectedFSGame struct {
	hostId            string
	gameId            string
	betList           string // for game room id used
	rateList          string // for game room id used
	bets              [1][]uint32
	rate              []uint32
	langs             []string
	rateIndex         uint32
	waitingTime       []uint32 // roll, bet, result (MilliSecond)
	sessionTimeout    uint32
	ipConfig          uint32
	roomConfig        uint32
	hostConnectConfig uint32
	betAreaLimit      []uint32
}
