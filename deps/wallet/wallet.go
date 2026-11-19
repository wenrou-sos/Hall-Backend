package wallet

import (
	"time"

	"github.com/jinzhu/gorm"
)

const (
	CategoryGuest      = -1
	CategoryHost       = 0	 // WalletType = 0 and FishShareType = 0
	CategoryPlayer     = 1	 // WalletType = 1
	CategoryShared     = 2	 // WalletType = 0 and FishShareType = 1
	WalletSharedFish   = 1
	WalletSharedCard   = 128 // 1000 0000
	WalletSharedCard89 = 129 // 1000 0001
	logDeposit         = 0
	logWithdraw        = 1
	logRefund          = 2
	logNote            = "GS"
)

func Builder() *builder {
	return &builder{
		secWebSocketKey: "",
		hostId:          "",
		hostExtId:       "",
		memberName:      "",
		memberId:        "",
		balance:         0,
		category:        -2,
		purposeMajor:    0,
		purposeMinor:    0,
		token:           "",
		gameId:          "",
		subGameId:       0,
		isGuest:         false,
		db:              nil,
		iHandler:        nil,
	}
}

type builder struct {
	secWebSocketKey string
	hostId          string
	hostExtId       string
	memberName      string
	memberId        string
	balance         uint64
	category        int
	purposeMajor    int
	purposeMinor    int
	isGuest         bool
	token           string
	db              *gorm.DB
	iHandler        IHandler
	gameId          string
	subGameId       int
}

type wallet struct {
	secWebSocketKey   string
	hostId            string
	hostExtId         string
	memberName        string
	memberId          string
	category          int
	isGuest           bool
	accType           uint8 // 0:locked 1:regular 2:test 3:vip
	token             string
	iHandler          IHandler
	walletGuest       *walletGuest
	walletPlayer      *walletPlayer
	walletSharedMajor *walletSharedMajor
	walletSharedMinor *walletSharedMinor
	walletHost        *walletHost
	gameId            string
	subGameId         int
}

type IHandler interface {
	DecreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64)
	IncreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64)
	GetAccountingSnHandler(secWebSocketKey string, balance, cent, sn uint64, depositCheck bool) (accountingSn uint64)
	EndAccountingHandler(secWebSocketKey string, checkAccountingEnd bool, walletType int, cent, accountingSn uint64)
	BetErrorHandler(secWebSocketKey string, accountingSn uint64)
}

// database table member
type member struct {
	HostId     string
	Id         string
	PlayerCent uint64
	AccType    uint8 // 0:locked 1:regular 2:test 3:vip
}

// database table member_wallet
type memberWallet struct {
	HostId   string
	MemberId string
	Purpose  uint
	Balance  uint64
}

// database table member_wallet_log
type memberWalletLog struct {
	HostId    string
	MemberId  string
	Purpose   uint
	Action    uint // 0:Deposit  1:Withdraw
	TxnId     string
	Amount    uint64
	Balance   uint64
	Note      string
	OccurTime time.Time
}

// database table member_wallet_refund_log
type memberWalletRefundLog struct {
	HostId    string
	GameId    string
	SubgameId int
	ServerId  string
	MemberId  string
	TxnId     string
	Bet    	  uint64
	Note      string
	Refund    int
	OccurTime time.Time
}

// database table host_error_log
type hostErrorLog struct {
	HostId    string
	Action    uint
	ActionKey uint64
	ErrCode   int
	ErrDescr  string
	OccurTime time.Time
	GameEnd   uint
}

func (b *builder) SetSecWebSocketKey(secWebSocketKey string) *builder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *builder) SetHostId(hostId string) *builder {
	b.hostId = hostId
	return b
}

func (b *builder) SetHostExtId(hostExtId string) *builder {
	b.hostExtId = hostExtId
	return b
}

func (b *builder) SetMemberName(memberName string) *builder {
	b.memberName = memberName
	return b
}

func (b *builder) SetMemberId(memberId string) *builder {
	b.memberId = memberId
	return b
}

func (b *builder) SetBalance(balance uint64) *builder {
	b.balance = balance
	return b
}

func (b *builder) SetCategory(category int) *builder {
	b.category = category
	return b
}

func (b *builder) SetPurposeMajor(purposeMajor int) *builder {
	b.purposeMajor = purposeMajor
	return b
}

func (b *builder) SetPurposeMinor(purposeMinor int) *builder {
	b.purposeMinor = purposeMinor
	return b
}

func (b *builder) SetGuest(guestEnable int) *builder {
	b.isGuest = guestEnable == GuestOn
	return b
}

func (b *builder) SetHandler(iHandler IHandler) *builder {
	b.iHandler = iHandler
	return b
}

func (b *builder) SetToken(token string) *builder {
	b.token = token
	return b
}

func (b *builder) SetGameId(gameId string) *builder {
	b.gameId = gameId
	return b
}

func (b *builder) SetSubGameId(subGameId int) *builder {
	b.subGameId = subGameId
	return b
}
