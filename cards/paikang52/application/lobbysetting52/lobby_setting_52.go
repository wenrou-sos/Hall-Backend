package lobbysetting52

// table host_52_game
type host52Game struct {
	HostId            string
	GameId            string
	SubGameId         uint32
	Langs             string
	BetList           string
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
	Fee               uint32
}
