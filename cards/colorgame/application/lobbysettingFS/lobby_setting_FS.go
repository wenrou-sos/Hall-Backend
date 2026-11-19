package lobbysettingFS

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
	Fee               uint32
}

//取得房間數量
func (h *HostFSGame) GetRoomNum() int {
	return 0
}

//取得每房的機器人數量
func (h *HostFSGame) GetBotNumPerRoom() int {
	return 0
}

//取得機器人補房的人數數量條件
func (h *HostFSGame) GetFillRoomMinPlayerNum() int {
	return 6
}
