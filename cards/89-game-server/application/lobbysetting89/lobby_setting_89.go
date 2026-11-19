package lobbysetting89

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
	PanelConfig       uint32 // reserved, reserved, ATM_ICON, ATM_DASHBOARD (1:show, 0:hidden) All show:1 (0011)
	SessionTimeout    uint32
	IpConfig          uint32
	RoomConfig        uint32
	BankerConfig      uint32
	HostConnectConfig uint32
}
