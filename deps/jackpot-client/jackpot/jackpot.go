package jackpot

func Builder() *builder {
	return &builder{
		AccountingSn: 0,
		JackpotSn:    0,
		HostId:       "",
		JackpotType:  0,
		JackpotGroup: 0,
		JackpotPool:  0,
		JackpotName:  "",
		JackpotWin:   0,
		JackpotData:  "",
	}
}

// database table `accounting_vp1`
type vp1 struct {
	AccountingSn uint64 `gorm:"PRIMARY_KEY"`
	JpContrib    float64
	BonusType    int32
	GameTime     string `gorm:"PRIMARY_KEY"`
}

// database table `accounting_jackpot`
type jackpot struct {
	AccountingSn uint64 `gorm:"PRIMARY_KEY"`
	JackpotSn    uint64
	HostId       string
	JackpotType  int32
	JackpotGroup int32
	JackpotPool  int32
	JackpotName  string
	JackpotWin   uint64
	JackpotData  string
}

type builder struct {
	AccountingSn uint64
	JackpotSn    uint64
	HostId       string
	JackpotType  int32
	JackpotGroup int32
	JackpotPool  int32
	JackpotName  string
	JackpotWin   uint64
	JackpotData  string
}

func (b *builder) SetAccountingSn(accountingSn uint64) *builder {
	b.AccountingSn = accountingSn
	return b
}

func (b *builder) SetJackpotSn(jackpotSn uint64) *builder {
	b.JackpotSn = jackpotSn
	return b
}

func (b *builder) SetHostId(hostId string) *builder {
	b.HostId = hostId
	return b
}

func (b *builder) SetJackpotType(jackpotType int32) *builder {
	b.JackpotType = jackpotType
	return b
}

func (b *builder) SetJackpotGroup(jackpotGroup int32) *builder {
	b.JackpotGroup = jackpotGroup
	return b
}

func (b *builder) SetJackpotPool(jackpotPool int32) *builder {
	b.JackpotPool = jackpotPool
	return b
}

func (b *builder) SetJackpotName(jackpotName string) *builder {
	b.JackpotName = jackpotName
	return b
}

func (b *builder) SetJackpotWin(jackpotWin uint64) *builder {
	b.JackpotWin = jackpotWin
	return b
}

func (b *builder) SetJackpotData(jackpotData string) *builder {
	b.JackpotData = jackpotData
	return b
}

func (b *builder) Build() *jackpot {
	return &jackpot{
		AccountingSn: b.AccountingSn,
		JackpotSn:    b.JackpotSn,
		HostId:       b.HostId,
		JackpotType:  b.JackpotType,
		JackpotGroup: b.JackpotGroup,
		JackpotPool:  b.JackpotPool,
		JackpotName:  b.JackpotName,
		JackpotWin:   b.JackpotWin,
		JackpotData:  b.JackpotData,
	}
}
