package botuser

import (
	"colorgame-game-server/application/gamesettingFS"
	"colorgame-game-server/application/lottery"
	"colorgame-game-server/domain/avatar"
	"colorgame-game-server/domain/bet"
	bet_proto "colorgame-game-server/domain/bet/proto"
	commonFS_proto "colorgame-game-server/models/proto"
	cryptoRand "crypto/rand"
	"math/big"
	"runtime/debug"
	"strconv"
	"sync"
	"time"

	"github.com/gogo/protobuf/proto"
	"github.com/google/uuid"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	packageName              = "botuser"
	ActionGameRoomJoinCall   = packageName + "ActionGameRoomJoinCall"
	ActionGameRoomJoinRecall = packageName + "ActionGameRoomJoinRecall"
	ActionGameRoomLeave      = packageName + "ActionGameRoomLeave"
	actionDestroy            = "actionDestroy"
	destoryBotPlayer         = "destoryBotPlayer"
	EMSGID_eRoundEnd         = "EMSGID_eRoundEnd" //gameroom.EMSGID_eRoundEnd
)

func Builder() *builder {
	return &builder{
		from:            "",
		betRoundUuid:    "",
		gameRoomUuid:    "",
		rate:            0,
		rateIndex:       0,
		balanceLimit:    1,
		secWebSocketKey: "",
	}
}

type builder struct {
	from            string
	betRoundUuid    string
	gameRoomUuid    string
	rate            uint32
	rateIndex       int
	betList         []string
	balanceLimit    uint64
	secWebSocketKey string
}

type botUser struct {
	uuid            string
	from            string
	secWebSocketKey string
	betRoundUuid    string
	gameRoomUuid    string
	memberId        string
	memberName      string
	avatar          string
	seat            int
	rate            uint32
	rateIndex       int
	betList         []string
	balanceLimit    uint64
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
	isDestroy       bool
}

func (b *builder) setFrom(from string) *builder {
	b.from = from
	return b
}

func (b *builder) setGameRoomUuid(gameRoomUuid string) *builder {
	b.gameRoomUuid = gameRoomUuid
	return b
}

func (b *builder) setBetRoundUuid(betRoundUuid string) *builder {
	b.betRoundUuid = betRoundUuid
	return b
}

func (b *builder) setRate(rate uint32) *builder {
	b.rate = rate
	return b
}

func (b *builder) setBalanceLimit(balanceLimit uint64) *builder {
	b.balanceLimit = balanceLimit
	return b
}

func (b *builder) setRateIndex(rateIndex int) *builder {
	b.rateIndex = rateIndex
	return b
}

func (b *builder) setBetList(betList []string) *builder {
	b.betList = betList
	return b
}

func (b *builder) build() *botUser {
	v := &botUser{
		uuid:            uuid.New().String(),
		from:            b.from,
		secWebSocketKey: b.secWebSocketKey,
		betRoundUuid:    b.betRoundUuid,
		gameRoomUuid:    b.gameRoomUuid,
		avatar:          avatar.Service.Random(),
		seat:            -1,
		rate:            b.rate,
		rateIndex:       b.rateIndex,
		betList:         b.betList,
		balanceLimit:    b.balanceLimit,
		in:              make(chan *flux.Action, 1024),
		rwMutex:         &sync.RWMutex{},
		isDestroy:       false,
	}

	gamesettingFS.Service.Clone(gamesettingFS.Service.DefaultBotKeys[b.rateIndex], v.uuid)
	go v.run()

	return v
}

func (b *botUser) run() {
	flux.Register(b.uuid, b.in)

	for action := range b.in {
		b.handleAction(action)
	}
}

func (b *botUser) handleAction(action *flux.Action) {
	defer func() {
		if err := recover(); err != nil {
			logger.Service.Zap.Fatalw("999",
				"err", err,
				"stacktrace", string(debug.Stack()),
			)
		}
	}()

	if action.Key().To() != b.uuid {
		return
	}

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		balance := b.rngBalance()
		b.memberId = b.uuid
		b.memberName = b.rngName()

		wallet.Service.Open(
			wallet.Builder().
				SetSecWebSocketKey(b.uuid).
				SetHostId("BOT").
				SetHostExtId("BOT").
				SetMemberId(b.uuid).
				SetMemberName(b.memberName).
				SetBalance(balance).
				SetCategory(wallet.CategoryGuest).
				SetGuest(wallet.GuestOn).
				Build(),
		)

		wallet.Service.IncreaseBalance(b.uuid, "", balance, 0, 0)

	case wallet.ActionWalletOpened:
		flux.Send(ActionGameRoomJoinCall, b.uuid, b.from,
			b.gameRoomUuid,
			b.avatar,
		)

	case ActionGameRoomJoinRecall:
		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		seat := action.Payload()[0].(int)

		if seat < 0 {
			b.destroy()
			return
		}

		b.seat = seat
		flux.Send(auth.EMSGID_eBroadcastPlayerIn, b.uuid, b.gameRoomUuid, auth_proto.PLAYER_TYPE_BOT)

	case EMSGID_eRoundEnd:
		isLeave := b.rngLeaveRoom(70)

		if !isLeave && !b.isBalanceEnough() { //尚未離開且錢不夠
			b.rngLeaveRoom(90)
		}

	case bet.EMSGID_eBetRoundStart:
		bytes := action.Payload()[0].([]byte)

		betStartRoundCall := &bet_proto.BetRoundStart{}
		_ = proto.Unmarshal(bytes, betStartRoundCall)
		b.betRoundUuid = betStartRoundCall.BetRoundUuid

	case bet.EMSGID_eBetRoundCountdown:
		randNum, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(int64(1000)))
		time.Sleep(time.Duration(randNum.Uint64()) * time.Millisecond)
		b.rngBet()

	case auth.EMSGID_eBroadcastPlayerOut:
		bytes := action.Payload()[0].([]byte)
		data := &auth_proto.BroadcastPlayerOut{}
		_ = proto.Unmarshal(bytes, data)
		if data.Player.Id == b.uuid {
			b.destroy()
		}

	}
}

func (b *botUser) rngBet() {
	if b.betRoundUuid == "" ||
		b.seat < 0 || b.seat >= 11 {
		return
	}

	// 1/n的機率不押注
	probability := 3
	randNum, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(int64(probability)))
	if randNum.Uint64() == 0 {
		return
	}
	betType, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(int64(lottery.MAX_BET_TYPE)))
	betIndex, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(int64(3)))
	betCall := &bet_proto.BetCall{
		Msgid:        commonFS_proto.EMSGID_eBetCall,
		Seat:         int32(b.seat),
		BetType:      uint32(betType.Int64()),
		BetIndex:     uint32(betIndex.Int64()),
		BetRoundUuid: b.betRoundUuid,
	}
	bytes, _ := proto.Marshal(betCall)
	flux.Send(bet.EMSGID_eBetCall, b.uuid, b.betRoundUuid, bytes)
}

//執行隨機離房
//回傳是否有離房
func (b *botUser) rngLeaveRoom(probability uint64) bool {
	isLeave := false

	randNum, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(100))
	if randNum.Uint64() < probability {
		isLeave = true
		b.betRoundUuid = ""
		flux.Send(auth.EMSGID_eBroadcastPlayerOut, b.uuid, b.gameRoomUuid, auth.Service.BroadcastPlayerOut(
			b.gameRoomUuid,
			b.memberId,
			b.memberName,
			b.avatar,
			uint32(b.seat),
			uint64(0),
		))
	}

	return isLeave
}

func (b *botUser) rngBalance() uint64 {
	min := b.balanceLimit * uint64(b.rate) * 50                                //最小值
	minMultiple, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(int64(10))) //隨機1~10倍
	coda, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(int64(1000)))      //加一點尾數
	n := (uint64(minMultiple.Int64()+1)*min + uint64(coda.Int64()+1))

	return n
}

func (b *botUser) rngName() (name string) {
	// names := []string{
	// 	"ann", "AV8D", "AV01", "arina", "andy", "Agnes", "alvin", "aizawa", "akiho", "asukakiraran",
	// 	"boking", "Bblythe", "Beatrice", "benz", "Beryl", "blue", "Bonnie", "Breenda", "bmw", "Beverly",
	// 	"Carol", "Cara", "colton", "Caroline", "Charlotte", "Cherry", "Claire", "Cora", "Crystal", "Cynthia",
	// 	"dD", "Dale", "Dana", "Debby", "doraemon", "duke", "Donna", "Dora", "ding", "Dorothy",
	// 	"Eden", "Eileen", "Elaine", "Elizabeth", "eddie", "Elma", "Elsa", "Emily", "Emma", "Eve",
	// 	"Fanny", "Fay", "Flora", "fifi", "Frances", "Freda", "Frederica", "Father", "Faith", "fafa",
	// 	"Gabrielle", "gogoro", "gareth", "Gloria", "Grace", "Griselda", "Gustave", "Gwendolyn", "Gemma", "Gail",
	// 	"hatano", "hashimoto",
	// 	"Jade", "Jane", "janet", "Jean", "Jennifer", "jenny", "Jessie", "Jill", "johnny", "Joyce",
	// 	"mikami", "Minami", "max", "mayday",
	// 	"peter", "pinhao", "playstar",
	// 	"ruby",
	// 	"sakumomo", "seven",
	// 	"tsumugi", "totoro", "tokyo",
	// 	"vivian",
	// 	"yua", "yui", "yoshizawa",
	// 	"+0", "177",
	// }

	n, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(int64(len(RobotIdServie.robotIds))))

	return RobotIdServie.robotIds[n.Int64()]
}

func (b *botUser) destroy() {
	if b.isDestroy {
		return
	}

	flux.Send(actionDestroy, b.uuid, Service.Id, b.uuid)
	flux.UnRegister(b.uuid, b.in)

	//銷毀控管在player記憶體裡的機器人
	flux.Send(destoryBotPlayer, b.uuid, b.gameRoomUuid, b.uuid)

	//銷毀flag
	b.isDestroy = true

}

//判斷餘額是否足夠下一局
func (b *botUser) isBalanceEnough() bool {
	balance, _ := wallet.Service.Balance(b.uuid)
	minBet, _ := strconv.ParseUint(b.betList[0], 10, 64)
	balanceLimit := uint64(b.rate * uint32(minBet))
	if balance < balanceLimit {
		return false
	}

	return true
}
