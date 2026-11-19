package botuser

import (
	"89-game-server/application/banker"
	banker_proto "89-game-server/application/banker/proto"
	"89-game-server/application/gamesetting89"
	"89-game-server/domain/avatar"
	"89-game-server/domain/bet"
	"89-game-server/domain/draw"
	"crypto/rand"
	"math/big"
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
)

func Builder() *builder {
	return &builder{
		from:            "",
		gameRoomUuid:    "",
		rate:            0,
		balanceLimit:    0,
		secWebSocketKey: "",
	}
}

type builder struct {
	from            string
	gameRoomUuid    string
	gameRoomType    string
	rate            uint32
	balanceLimit    uint64
	secWebSocketKey string
}

type botUser struct {
	uuid            string
	from            string
	secWebSocketKey string
	bankerUuid      string
	gameRoomUuid    string
	gameRoomType    string
	memberId        string
	memberName      string
	avatar          string
	seat            int
	rate            uint32
	balanceLimit    uint64
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
}

func (b *builder) setFrom(from string) *builder {
	b.from = from
	return b
}

func (b *builder) setGameRoomUuid(gameRoomUuid string) *builder {
	b.gameRoomUuid = gameRoomUuid
	return b
}

func (b *builder) setGameRoomType(gameRoomType string) *builder {
	b.gameRoomType = gameRoomType
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

func (b *builder) setSecWebSocketKey(secWebSocketKey string) *builder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *builder) build() *botUser {
	v := &botUser{
		uuid:            uuid.New().String(),
		from:            b.from,
		secWebSocketKey: b.secWebSocketKey,
		bankerUuid:      "",
		gameRoomUuid:    b.gameRoomUuid,
		gameRoomType:    b.gameRoomType,
		avatar:          avatar.Service.Random(),
		seat:            -1,
		rate:            b.rate,
		balanceLimit:    b.balanceLimit,
		in:              make(chan *flux.Action, 1024),
		rwMutex:         &sync.RWMutex{},
	}

	gamesetting89.Service.Clone(v.secWebSocketKey, v.uuid)

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
	if action.Key().To() != b.uuid {
		return
	}

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		cent := b.rngCent()
		b.memberId = b.uuid
		b.memberName = b.rngName()

		wallet.Service.Open(
			wallet.Builder().
				SetSecWebSocketKey(b.uuid).
				SetHostId("BOT").
				SetHostExtId("BOT").
				SetMemberId(b.uuid).
				SetMemberName(b.memberName).
				SetBalance(cent).
				SetCategory(wallet.CategoryGuest).
				SetGuest(wallet.GuestOn).
				Build(),
		)

		wallet.Service.Deposit(b.uuid, cent)

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

	case banker.EMSGID_eRoundStart:
		b.rwMutex.RLock()
		defer b.rwMutex.RUnlock()

		if b.seat < 0 || b.gameRoomUuid == "" || b.bankerUuid == "" {
			logger.Service.Zap.Errorw("Round Start Failed",
				"GameUser", b.uuid,
				"GameRoomUuid", b.gameRoomUuid,
				"Seat", b.seat,
				"BankerUuid", b.bankerUuid,
			)

			panic("ERROR SEAT : " + b.uuid)
			return
		}

		if b.seat != banker.BANKER_SEAT {
			cent, err := wallet.Service.CentCache(b.uuid)

			if err != nil {
				panic("BOT CENT ERROR")
			}

			flux.Send(bet.ActionBetStart, b.uuid, bet.Service.Id,
				bet.Builder().
					SetBankerUuid(b.bankerUuid).
					SetSecWebSocketKey(b.uuid).
					SetGameRoomUuid(b.gameRoomUuid).
					SetGameRoomType(b.gameRoomType).
					SetSeat(int32(b.seat)).
					SetWaitingTime(gamesetting89.Service.BetWaitingTime(b.uuid)).
					SetKind(bet.BOT).
					SetRate(gamesetting89.Service.Rate(b.uuid)).
					SetBetList(gamesetting89.Service.BetList(b.uuid)).
					SetCent(cent).
					Build(),
			)
		}

	case banker.EMSGID_eRoundEnd:
		n, err := rand.Int(rand.Reader, big.NewInt(3))

		if err != nil {
			panic(err)
		}

		if n.Uint64() == 0 {
			n = big.NewInt(1)
		}

		time.Sleep(time.Duration(n.Uint64()) * time.Second)

		b.destroy()

	case banker.ActionBankerDeal:
		b.rwMutex.RLock()
		defer b.rwMutex.RUnlock()

		dataByte := action.Payload()[0].([]byte)
		isEnd, _ := strconv.ParseBool(string(action.Payload()[1].([]byte)))
		isDrawDelay, _ := strconv.ParseBool(string(action.Payload()[2].([]byte)))

		data := &banker_proto.Deal{}

		proto.Unmarshal(dataByte, data)

		if !isEnd {
			sleepTime := 0

			if isDrawDelay && b.seat == 0 {
				sleepTime = 2
			}

			if b.seat == 0 {
				sleepTime = 5
			}

			d := draw.Builder().
				SetBankerUuid(b.bankerUuid).
				SetSecWebSocketKey(b.uuid).
				SetGameRoomUuid(b.gameRoomUuid).
				SetGameRoomType(b.gameRoomType).
				SetSeat(int32(b.seat)).
				SetSumPoint(data.Cards[b.seat].SumPoint).
				SetWaitingTime(gamesetting89.Service.DrawWaitingTime(b.uuid)).
				SetKind(draw.BOT).
				SetSleepTime(uint32(sleepTime)).
				Build()

			flux.Send(draw.ActionDrawStart, b.uuid, draw.Service.Id, d)
		}

	case banker.ActionBankerStart:
		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		switch action.Payload()[0].(type) {
		case string:
			b.bankerUuid = action.Payload()[0].(string)

		case []byte:
			b.bankerUuid = string(action.Payload()[0].([]byte))
		}

	case draw.ActionDrawNext:
		gameRoomUuid := string(action.Payload()[0].([]byte))

		seat, _ := strconv.Atoi(string(action.Payload()[1].([]byte)))

		if seat < b.seat {
			flux.Send(draw.ActionDrawNext, b.uuid, draw.Service.Id, gameRoomUuid, int32(seat))
		}
	}
}

func (b *botUser) rngCent() (cent uint64) {
	min := b.balanceLimit
	max := b.balanceLimit / 100 * 2000

	n, err := rand.Int(rand.Reader, big.NewInt(int64(max-min+1)))

	if err != nil {
		panic(err)
	}

	return n.Uint64() + min
}

func (b *botUser) rngName() (name string) {
	names := []string{
		"eNiZsrR9821", "OvrFkqu4990", "cUjEUdx5862", "XIFByYq5461", "VhROYsq4571", "HdTAgWn1928", "ZboJIlE1072", "WaKkGZf8011", "VZDXqqJ902", "FPjuwgi85",
		"mPOCpkr2264", "eCxIxIN9528", "RzVTbNE2652", "kTdrOBS6203", "hhMjsZP2620", "dnpdmEp1980", "VOVxgWW9679", "xTVCdMw5770", "NRlOZXL3484", "oHGIVEH3393",
		"byDEzJR8042", "HMRNvcj2618", "SkkqzqE2953", "eEbXJAz5622", "ExRTjKc6933", "WXLPMAn6069", "ddalwLO1027", "SkYfGJJ1008", "MpORcrb2561", "nItfSoi4429",
		"kxLAEeg9071",
		"pFqgLUj6247",
		"isGmjYn4171",
		"OLPcakE4799",
		"vtZTaql7467",
		"yuWbvwq8414",
		"vADAjLP7487",
		"uByDbmW3594",
		"nbEyVSY8871",
		"opGegcl1933",
		"CFEYUJV4815",
		"QklMvPd829",
		"NYgGHZB9401",
		"hJuqlzv2927",
		"tXpzIOx9309",
		"BuYyWRw3869",
		"yEqxpDy897",
		"sPtDllR205",
		"zPPhnxQ383",
		"JGSIiRK9608",
		"fQnJ69239081",
		"WewX9028365",
		"gczM35253458",
		"utpU16453640",
		"KklW44665764",
		"HJvE19010240",
		"eXxX62880881",
		"yEmo37851834",
		"caqd19002893",
		"LxiP37767220",
		"RFkJ16360302",
		"pKkg34791182",
		"URiR39999963",
		"vYZJ54892408",
		"xBhe61342155",
		"JitM39654704",
		"JeoE36914806",
		"Ears492419",
		"ursR40829939",
		"lWYJ21782081",
		"hkGF73440245",
		"eiEe55081160",
		"LzuJ59195100",
		"AsVd90185747",
		"HBho9217456",
		"eAmD54432226",
		"WdIg12072065",
		"nzhU20738438",
		"Jqfd63659190",
		"ROzt37579464",
		"GMxD8092607",
		"NtDJ21552820",
		"zrqm67095609",
		"Wjae62319532",
		"kVoS54708611",
		"JWQo3079447",
		"cYOb58899492",
		"JbnG79644876",
		"rJSX16811115",
		"kJsK61711204",
		"vGoX69520795",
		"zDFj74772463",
		"ZqTG18461268",
		"xptF66494637",
		"NYvh61836781",
		"ldQu50716352",
		"byYg35750694",
		"rHAy23058327",
		"niTx78110139",
		"exIi15021003",
		"jyyj907344",
		"GfiC514467",
		"dGSo960505",
		"TfBD559835",
		"GubT985820",
		"RlfE34756",
		"EOvV473631",
		"PIkX88267",
		"sDYj953880",
		"ZeYx297303",
		"jeIq304947",
		"Oqfi943247",
		"zYaJ538945",
		"xeyG646021",
		"mcHu808045",
		"bzLt353828",
		"vSjU803985",
		"kUmb629591",
		"YBSy287502",
		"TEsp252649",
		"xQjq842016",
		"zlWS908637",
		"mWVo75086",
		"yMny839656",
		"rSlk893640",
		"iCkM449503",
		"JEdt258977",
		"NCmR381535",
		"xrbs775895",
		"xYny406133",
		"tuMg778290",
		"sHCl930485",
		"eOHb857",
		"JNJO712454",
		"ANnV100237",
		"SsnE14911",
		"rRav414961",
		"rAlG666024",
		"mvgx127240",
		"vXxp719463",
		"NRYb112545",
		"LUwa166604",
		"GeIe51318",
		"vbrj253385",
		"EpNZ770637",
		"zJDw83633",
		"bipp436685",
		"ODGl205619",
		"NBmP848383",
		"lziJ938397",
		"tiZo787095",
		"hhJZ774527",
		"RZPY719780",
		"SiCL73106",
		"TjtT144953",
		"Qieu518125",
		"eXiZ291807",
		"lFdX873191",
		"PLEj228737",
		"LdFc379691",
		"TcJU743977",
		"hLttvpt540011",
		"slOdxEV428487",
		"PxqvRlX768014",
		"KkhCQTT744860",
		"pMatDaC537751",
		"CIBwTEP868319",
		"zHyeVvN70145",
		"XAVSBKz636865",
		"jsSxbUe853888",
		"jDDiieb933012",
		"nxFUxzO998765",
		"duWkbzh266583",
		"mLuYxdZ999645",
		"rJixxaM162085",
		"gZBHTaK760139",
		"UEytIDg253350",
		"trGOZJx548264",
		"DjmyGHx141502",
		"FAwCNJZ226",
		"AWBLmXn687150",
		"FYucZSe732613",
		"EjgJkxe918042",
		"OCBFFHN443376",
		"VGyKlaG961820",
		"TDpYfPD598539",
		"wfYKUQO522695",
		"tbMxoGn82331",
		"isosbwZ903821",
		"SYfeKkr60860",
		"dGudYYa849653",
		"bKDnadK601382",
		"qgTrRsQ519076",
		"nbigBCT854643",
		"fAOeGwa276140",
		"PQoCsCK941205",
		"wztzFeP42425",
		"bypSswG456763",
		"dUAlTOT377145",
		"IPLCpLN114526",
	}
	n, err := rand.Int(rand.Reader, big.NewInt(int64(len(names))))

	if err != nil {
		panic(err)
	}

	return names[int(n.Int64())]
}

func (b *botUser) destroy() {
	if b.seat > -1 {
		time.Sleep(1 * time.Second) // for web client animation

		flux.Send(auth.EMSGID_eBroadcastPlayerOut, b.uuid, b.gameRoomUuid, auth.Service.BroadcastPlayerOut(
			b.gameRoomUuid,
			b.memberId,
			b.memberName,
			b.avatar,
			uint32(b.seat),
			uint64(0),
		))
	}

	flux.UnRegister(b.uuid, b.in)
	flux.Send(actionDestroy, b.uuid, Service.Id, b.uuid)
}
