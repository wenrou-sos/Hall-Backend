package friendroom

import (
	"52-game-server/application/atm"
	"52-game-server/application/banker"
	banker_proto "52-game-server/application/banker/proto"
	"52-game-server/application/botuser"
	friend_room_proto "52-game-server/application/friendroom/proto"
	"52-game-server/application/gamesetting52"
	game_setting52_proto "52-game-server/application/gamesetting52/proto"
	"52-game-server/application/lobbysetting52"
	lobby_setting52_proto "52-game-server/application/lobbysetting52/proto"

	"52-game-server/domain/playcards"

	"math/big"

	"52-game-server/domain/draw"
	"52-game-server/domain/probability"
	"52-game-server/domain/waitingroom"
	common52_proto "52-game-server/models/proto"
	"crypto/rand"
	"crypto/sha1"
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gogo/protobuf/proto"
	"github.com/google/uuid"
	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	flux_proto "gitlab.iplaystar.net/game-server/flux/proto"
	"gitlab.iplaystar.net/game-server/format"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	game_setting_proto "gitlab.iplaystar.net/game-server/game-setting/proto"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"gitlab.iplaystar.net/game-server/logger"
	macaddress "gitlab.iplaystar.net/game-server/mac-address"
	"gitlab.iplaystar.net/game-server/postman"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	EMSGID_eFriendRoomJoinCall    = "EMSGID_eFriendRoomJoinCall"
	EMSGID_eFriendRoomJoinRecall  = "EMSGID_eFriendRoomJoinRecall"
	EMSGID_eFriendRoomLeaveCall   = "EMSGID_eFriendRoomLeaveCall"
	EMSGID_eFriendRoomLeaveRecall = "EMSGID_eFriendRoomLeaveRecall"
	EMSGID_eFriendRoomDestroy     = "EMSGID_eFriendRoomDestroy"
	EMSGID_eFriendRoomHostChanged = "EMSGID_eFriendRoomHostChanged"
	EMSGID_eFriendRoomGameStart   = "EMSGID_eFriendRoomGameStart"
	ActionNoEnoughCredit          = "ActionNoEnoughCredit"
	playerMin                     = 2
	roomNumberDigital             = 6
)

func Builder() *builder {
	return &builder{
		secWebSocketKey: "",
		memberId:        "",
		memberName:      "",
		avatar:          "",
		hostExtId:       "",
		kind:            "",
		guestEnable:     auth.GuestOn,
	}
}

type builder struct {
	secWebSocketKey string
	memberId        string
	memberName      string
	avatar          string
	hostExtId       string
	kind            string
	guestEnable     int
	ipConfig        uint32
}

type friendRoom struct {
	bankerUuid      string
	secWebSocketKey string
	serverId        string
	uuid            string
	memberId        string
	memberName      string
	avatar          string
	hostExtId       string
	kind            string
	gameId          string
	betList         string
	rateList        string
	rate            uint32
	bet             uint32
	number          int32
	seat            int32
	size            int32
	ipConfig        uint32
	guestEnable     int
	isHost          bool
	isDestroy       bool
	isStopCountdown chan bool
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
	startSeat       int32
}

func (b *builder) SetSecWebSocketKey(secWebSocketKey string) *builder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *builder) SetMemberId(memberId string) *builder {
	b.memberId = memberId
	return b
}

func (b *builder) SetMemberName(memberName string) *builder {
	b.memberName = memberName
	return b
}

func (b *builder) SetAvatar(avatar string) *builder {
	b.avatar = avatar
	return b
}

func (b *builder) SetHostExtId(hostExtId string) *builder {
	b.hostExtId = hostExtId
	return b
}

func (b *builder) SetKind(kind string) *builder {
	b.kind = kind
	return b
}

func (b *builder) SetGuest(guestEnable int) *builder {
	b.guestEnable = guestEnable
	return b
}

func (b *builder) SetIpConfig(ipConfig uint32) *builder {
	b.ipConfig = ipConfig
	return b
}

func (b *builder) Build() *friendRoom {
	return &friendRoom{
		secWebSocketKey: b.secWebSocketKey,
		serverId:        format.ServerId(macaddress.Get()),
		uuid:            "",
		memberId:        b.memberId,
		memberName:      b.memberName,
		avatar:          b.avatar,
		hostExtId:       b.hostExtId,
		kind:            b.kind,
		number:          -1,
		seat:            0,
		size:            5,
		ipConfig:        b.ipConfig,
		guestEnable:     b.guestEnable,
		isHost:          false,
		isDestroy:       false,
		isStopCountdown: make(chan bool, 4),
		rwMutex:         &sync.RWMutex{},
		startSeat:       -1,
	}
}

func (f *friendRoom) run() {
	f.rwMutex.Lock()
	f.isDestroy = false
	f.isStopCountdown = make(chan bool, 4)
	f.in = make(chan *flux.Action, 1024)
	f.rwMutex.Unlock()

	flux.Register(f.uuid, f.in)

	for action := range f.in {
		f.handleAction(action)
	}
}

func (f *friendRoom) handleAction(action *flux.Action) {
	f.rwMutex.Lock()
	defer f.rwMutex.Unlock()

	if action.Key().To() != f.uuid {
		return
	}

	switch action.Key().Name() {

	case flux.ActionFluxRegisterDone:
		// do nothing now
		logger.Service.Zap.Infow("Friend Room Registered",
			"ServerId", f.serverId,
			"GameUser", f.secWebSocketKey,
			"MemberId", f.memberId,
			"MemberName", f.memberName,
			"IsHost", f.isHost,
			"FriendRoomUuid", f.uuid,
			"Size", f.size,
			"Kind", f.kind,
		)

	case botuser.ActionGameRoomJoinCall:
		// only banker situation
		if !f.isHost {
			return
		}

		botUuid := action.Key().From()
		gameRoomUuid := action.Payload()[0].(string)
		avatar := action.Payload()[1].(string)

		seat := Join.do(f.hostExtId, f.number, &player{
			ServerId: f.serverId,
			RoomUuid: gameRoomUuid,
			Uid:      botUuid,
			Name:     botUuid,
			Avatar:   avatar,
			Kind:     BANKER,
			Balance:  0,
			IsHost:   true,
		})

		// seat should be BANKER_SEAT
		if seat != banker.BANKER_SEAT {
			logger.Service.Zap.Errorw(FriendRoom_BANKER_SEAT_INCORRECT,
				"ServerId", f.serverId,
				"GameUser", f.secWebSocketKey,
				"MemberId", f.memberId,
				"MemberName", f.memberName,
				"IsHost", f.isHost,
				"FriendRoomUuid", f.uuid,
				"Size", f.size,
				"Kind", f.kind,
				"Seat", seat,
			)
			panic("ERROR BANKER SEAT")
			return
		}

		flux.Send(botuser.ActionGameRoomJoinRecall, f.uuid, botUuid, int(seat))

		if f.startSeat < 0 {
			n, _ := rand.Int(rand.Reader, big.NewInt(int64(Player.size(f.hostExtId, f.number))))
			f.startSeat = int32(n.Int64())
		}

		flux.Send(banker.ActionBankerCreate, f.uuid, banker.Service.Id,
			f.uuid,
			banker.FRIEND_ROOM,
			Player.size(f.hostExtId, f.number),
			f.startSeat,
			uint64(f.bet),
		)

	case banker.ActionBankerStart:
		bankerUuid := action.Payload()[0].(string)

		logger.Service.Zap.Infow("Friend Room Banker Start",
			"ServerId", f.serverId,
			"GameUser", f.secWebSocketKey,
			"MemberId", f.memberId,
			"MemberName", f.memberName,
			"IsHost", f.isHost,
			"FriendRoomUuid", f.uuid,
			"Size", f.size,
			"Kind", f.kind,
			"BankerUuid1", bankerUuid,
			"BankerUuid2", f.bankerUuid,
		)

		if f.bankerUuid == bankerUuid {
			return
		}

		f.bankerUuid = bankerUuid

		// only host needs broadcast ActionBankerStart
		if !f.isHost {
			return
		}

		r := Room.info(f.hostExtId, f.number)

		if r == nil {
			panic("REDIS ROOM NULL")
		}

		r.BankerUuid = bankerUuid

		Room.update(f.hostExtId, f.redisKey(), r)

		fluxData := &flux_proto.FluxAction{
			Name: banker.ActionBankerStart,
		}

		fluxData.Payload = append(fluxData.Payload, []byte(f.bankerUuid))

		f.toAll(fluxData)

	case banker.ActionBankerAccountingSn:
		// every player needed send this to banker
		secWebSocketKey := action.Key().From()

		if f.secWebSocketKey != secWebSocketKey && f.bankerUuid != "" {
			return
		}

		accountingSn := action.Payload()[0].(uint64)

		r := Room.info(f.hostExtId, f.number)

		if r == nil {
			panic("REDIS ROOM NULL")
		}

		logger.Service.Zap.Infow("Friend Room Got Accounting SN",
			"ServerId", f.serverId,
			"GameUser", f.secWebSocketKey,
			"MemberId", f.memberId,
			"MemberName", f.memberName,
			"IsHost", f.isHost,
			"FriendRoomUuid", f.uuid,
			"Size", f.size,
			"Kind", f.kind,
			"BankerUuid", f.bankerUuid,
			"HostServerId", r.HostServerId,
			"AccountingSn", accountingSn,
		)

		fluxData := &flux_proto.FluxAction{
			Name: banker.ActionBankerAccountingSn,
		}

		fluxData.Payload = append(fluxData.Payload, []byte(f.secWebSocketKey))
		fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatUint(accountingSn, 10)))

		f.toSomeone(fluxData, f.bankerUuid, r.HostServerId)

	case banker.EMSGID_eRoundStart:
		if !f.isHost {
			return
		}

		logger.Service.Zap.Infow("Friend Room Round Start",
			"ServerId", f.serverId,
			"GameUser", f.secWebSocketKey,
			"MemberId", f.memberId,
			"MemberName", f.memberName,
			"IsHost", f.isHost,
			"FriendRoomUuid", f.uuid,
			"Size", f.size,
			"Kind", f.kind,
		)

		data := action.Payload()[0].(*banker_proto.RoundStart)

		for i := int32(0); i < f.size; i++ {
			if p := Player.info(f.hostExtId, f.number, i); p != nil {
				u := &auth_proto.PlayerInfo{
					Id:      	p.Uid,
					Balance: 	p.Balance,
					Name:    	format.HideWithStar(p.Name),
					Seat:    	uint32(i),
					Avatar:  	p.Avatar,
					Type:    	auth_proto.PLAYER_TYPE_GAME,
					Visible: 	nil,
					WinCount: 	p.WinCount,
				}
				data.PlayerInfos = append(data.PlayerInfos, u)
			} else {
				u := &auth_proto.PlayerInfo{
					Id:      	"",
					Balance: 	0,
					Name:    	"",
					Seat:    	uint32(i),
					Visible: 	nil,
					WinCount: 	0,
				}
				data.PlayerInfos = append(data.PlayerInfos, u)
			}
		}

		dataByte, _ := proto.Marshal(data)

		fluxData := &flux_proto.FluxAction{
			Name: banker.EMSGID_eRoundStart,
		}

		fluxData.Payload = append(fluxData.Payload, dataByte)
		fluxData.Payload = append(fluxData.Payload, []byte(f.uuid))

		f.toAll(fluxData)

	case banker.EMSGID_eRoundEnd:
		logger.Service.Zap.Infow("Friend Room Round End",
			"ServerId", f.serverId,
			"GameUser", f.secWebSocketKey,
			"MemberId", f.memberId,
			"MemberName", f.memberName,
			"IsHost", f.isHost,
			"FriendRoomUuid", f.uuid,
			"Size", f.size,
			"Kind", f.kind,
		)

		f.bankerUuid = ""

		if !f.isHost {
			return
		}

		dataByte := action.Payload()[0].([]byte)

		r := Room.info(f.hostExtId, f.number)

		if r == nil {
			panic("REDIS ROOM NULL")
		}

		r.Status = IDLE
		r.BankerUuid = ""
		Room.update(f.hostExtId, f.redisKey(), r)

		Leave.do(f.hostExtId, f.redisKey(), f.number, banker.BANKER_SEAT)

		fluxData := &flux_proto.FluxAction{
			Name: banker.EMSGID_eRoundEnd,
		}

		fluxData.Payload = append(fluxData.Payload, dataByte)

		f.toAll(fluxData)

		if Player.size(f.hostExtId, f.number) >= playerMin {
			t := gamesetting52.Service.RoundStartWaitingTime(f.secWebSocketKey)
			go f.waitingCountdown(int(t))
		}

	case banker.ActionBankerDeal:
		if !f.isHost {
			return
		}

		dataByte := action.Payload()[0].([]byte)
		isDirectEnd := action.Payload()[1].([]byte)
		isDrawDelay := action.Payload()[2].([]byte)

		fluxData := &flux_proto.FluxAction{
			Name: banker.ActionBankerDeal,
		}

		fluxData.Payload = append(fluxData.Payload, dataByte)
		fluxData.Payload = append(fluxData.Payload, isDirectEnd)
		fluxData.Payload = append(fluxData.Payload, isDrawDelay)

		f.toAll(fluxData)
	case banker.EMSGID_ePlayerRoundStart:
		data := action.Payload()[0].(*banker_proto.PlayerRoundStart)
		dataByte, _ := proto.Marshal(data)
		if p := Player.info(f.hostExtId, f.number, data.Seat); p != nil {
			flux.Send(banker.EMSGID_ePlayerRoundStart, f.uuid, p.Uid, dataByte)
		}
	case banker.EMSGID_eBroadcastPlayerRoundStart:
		dataByte := action.Payload()[0].([]byte)

		fluxData := &flux_proto.FluxAction{
			Name: banker.EMSGID_eBroadcastPlayerRoundStart,
		}
		fluxData.Payload = append(fluxData.Payload, dataByte)
		f.toAll(fluxData)

	case draw.EMSGID_eBroadcastDrawRecall:
		fallthrough
	case draw.EMSGID_eBroadcastDrawTimeout:
		if !f.isHost {
			return
		}

		dataByte := action.Payload()[0].([]byte)

		fluxData := &flux_proto.FluxAction{
			Name: action.Key().Name(),
		}

		fluxData.Payload = append(fluxData.Payload, dataByte)

		f.toAll(fluxData)

	case playcards.EMSGID_ePlayCardsRecall:
		fallthrough
	case playcards.EMSGID_ePlayCardsTimeout:

		if f.bankerUuid == "" {
			panic("BANKER UUID NULL")
		}

		// this part's data from banker.go
		if action.Key().From() == f.bankerUuid {
			dataByte := action.Payload()[0].([]byte)
			secWebSocketKey := action.Payload()[1].(string)
			seat := action.Payload()[2].(int32)

			if !f.isHost && f.secWebSocketKey != secWebSocketKey {
				return
			}

			if p := Player.info(f.hostExtId, f.number, seat); p != nil {
				fluxData := &flux_proto.FluxAction{
					Name: action.Key().Name(),
				}

				fluxData.Payload = append(fluxData.Payload, dataByte)

				f.toSomeone(fluxData, p.Uid, p.ServerId)
			} else {
				panic("FRIEND DRAW PLAYER NIL")
			}
			return
		}

		// this part's data from play_cards.go
		dataByte := action.Payload()[0].([]byte)
		bankerUuid := action.Payload()[1].(string)
		secWebSocketKey := action.Payload()[2].(string)
		seat := action.Payload()[3].(int32)
		playType := action.Payload()[4].(int32)
		cards := action.Payload()[5].([]byte)

		if secWebSocketKey != f.secWebSocketKey && seat != banker.BANKER_SEAT {
			return
		}

		r := Room.info(f.hostExtId, f.number)

		if r == nil {
			panic("REDIS ROOM NULL")
		}

		fluxData := &flux_proto.FluxAction{
			Name: action.Key().Name(),
		}

		fluxData.Payload = append(fluxData.Payload, []byte(secWebSocketKey))
		fluxData.Payload = append(fluxData.Payload, []byte(strconv.Itoa(int(seat))))
		fluxData.Payload = append(fluxData.Payload, dataByte)
		fluxData.Payload = append(fluxData.Payload, cards)
		fluxData.Payload = append(fluxData.Payload, []byte(strconv.Itoa(int(playType))))

		f.toSomeone(fluxData, bankerUuid, r.HostServerId)

	case playcards.EMSGID_eBroadcastPlayCardsRecall:
		fallthrough
	case playcards.EMSGID_eBroadcastPlayCardsTimeout:
		if !f.isHost {
			return
		}

		dataByte := action.Payload()[0].([]byte)

		fluxData := &flux_proto.FluxAction{
			Name: action.Key().Name(),
		}

		fluxData.Payload = append(fluxData.Payload, dataByte)

		f.toAll(fluxData)

	case probability.EMSGID_eBroadcastResult:
		if !f.isHost {
			return
		}

		for i := int32(0); i < f.size; i++ {
			if p := Player.info(f.hostExtId, f.number, i); p != nil {
				cent, err := wallet.Service.Cent(p.Uid)

				if err != nil {
					panic("ERROR CENT " + p.Uid)
				}

				p.Balance = cent

				Player.update(f.hostExtId, f.number, i, p)
			}
		}

		dataByte := action.Payload()[0].([]byte)

		fluxData := &flux_proto.FluxAction{
			Name: probability.EMSGID_eBroadcastResult,
		}

		fluxData.Payload = append(fluxData.Payload, dataByte)

		f.toAll(fluxData)

	case waitingroom.ActionWaitingRoomDone:
		if f.isHost && Player.size(f.hostExtId, f.number) >= playerMin {

			r := Room.info(f.hostExtId, f.number)

			if r == nil {
				panic("ROOM REDIS NULL")
			}

			r.Status = GAMING
			r.BankerUuid = ""
			f.bankerUuid = ""
			Room.update(f.hostExtId, f.redisKey(), r)

			flux.Send(botuser.ActionBotUserCreate, f.uuid, botuser.Service.Id,
				f.uuid,
				f.secWebSocketKey,
				banker.FRIEND_ROOM,
				1,
			)

			fluxData := &flux_proto.FluxAction{
				Name: waitingroom.ActionWaitingRoomDone,
			}
			fluxData.Payload = append(fluxData.Payload, []byte(f.uuid))
			f.toAll(fluxData)
			return
		}

		if f.isHost {
			flux.Send(waitingroom.EMSGID_eWaitingRoundEnd, f.uuid, f.secWebSocketKey, waitingroom.Service.EMSGID_eWaitingRoundEnd())
		}

	case auth.EMSGID_eBroadcastPlayerOut:
		secWebSocketKey := action.Key().From()

		if secWebSocketKey == f.secWebSocketKey {
			f.eBroadcastPlayerOut()
		}

	case gameuser.ActionLeaveGameRoomCall:
		secWebSocketKey := action.Payload()[0].(string)

		if secWebSocketKey != f.secWebSocketKey {
			return
		}

		if f.isHost {
			f.eFriendRoomDestroy(nil)
		}

		Leave.do(f.hostExtId, f.redisKey(), f.number, f.seat)
		flux.Send(gameuser.ActionLeaveGameRoomRecall, f.uuid, f.secWebSocketKey, f.uuid)

	case ActionNoEnoughCredit:
		isDone := action.Payload()[0].(chan bool)
		secWebSocketKey := action.Key().From()

		if secWebSocketKey != f.secWebSocketKey {
			return
		}

		if f.isHost {
			f.eFriendRoomDestroy(nil)
		}

		Leave.do(f.hostExtId, f.redisKey(), f.number, f.seat)

		isDone <- true
		close(isDone)

	case auth.ActionAuthNotify:
		secWebSocketKey := action.Key().From()

		if secWebSocketKey != f.secWebSocketKey {
			return
		}

		memberId := action.Payload()[0].(string)
		hostId := action.Payload()[1].(string)
		dataByte := action.Payload()[2].([]byte)

		fluxData := &flux_proto.FluxAction{
			Name: auth.ActionAuthNotify,
		}

		fluxData.Payload = append(fluxData.Payload, []byte(memberId))
		fluxData.Payload = append(fluxData.Payload, []byte(hostId))
		fluxData.Payload = append(fluxData.Payload, dataByte)

		f.toSomeone(fluxData, auth.Service.Id, postman.SERVER_TRIGGER)

	case accounting.ActionAccountingEnd:
		// if !f.isHost {
		// 	return
		// }

		// results := action.Payload()[0].(map[string]*probability_proto.Card)
		// bankerUuid := action.Payload()[2].(string)
		// secWebSocketKey := action.Payload()[3].(string)
		// seat := action.Payload()[4].(int32)
		// accountingSn := action.Payload()[5].(uint64)

		// p := Player.info(f.hostExtId, f.number, seat)

		// fluxData := &flux_proto.FluxAction{
		// 	Name: accounting.ActionAccountingEnd,
		// }

		// data1 := &probability_proto.ResultMap{ResultMap: results}
		// dataByte1, _ := proto.Marshal(data1)

		// fluxData.Payload = append(fluxData.Payload, dataByte1)
		// fluxData.Payload = append(fluxData.Payload, []byte(bankerUuid))

		// f.toSomeone(fluxData, accounting.Service.HashId(secWebSocketKey, accountingSn), p.ServerId)
	}
}

func (f *friendRoom) EMSGID_eFriendRoomJoinCall(msg []byte, hostextid, ipaddress string) {
	gameConfigRecall := &game_setting52_proto.ConfigRecall{}

	cent, err := wallet.Service.Cent(f.secWebSocketKey)

	if err != nil {
		panic("ERROR CENT " + f.secWebSocketKey)
	}

	data := &friend_room_proto.FriendRoomJoinCall{}

	proto.Unmarshal(msg, data)

	if r := Room.info(f.hostExtId, data.Number); r != nil && r.Status == GAMING {
		gameConfigRecall.StatusCode = common_proto.Status_kGaming
		f.eFriendRoomJoinRecall(cent, gameConfigRecall)
		return
	}

	if data.Number <= 0 && data.GameConfigCall.SubgameId < uint32(f.size) {
		f.uuid = uuid.New().String()
		f.number = Service.rngNumber(roomNumberDigital)
		f.isHost = true

		f.eGameConfigCall(data.GameConfigCall, gameConfigRecall)

		switch gameConfigRecall.StatusCode {
		case common_proto.Status_kInvalid, common_proto.Status_kNoEnoughCredit:
			f.eFriendRoomJoinRecall(cent, gameConfigRecall)
			return
		}

		f.gameId = gamesetting52.Service.GameId(f.secWebSocketKey)
		f.bet = gameConfigRecall.Bet

		go f.run()

		if isOk := Create.do(f.hostExtId, f.redisKey(), &room{
			Uuid:         f.uuid,
			BankerUuid:   "",
			HostServerId: f.serverId,
			Number:       f.number,
			SubGameId:    data.GameConfigCall.SubgameId,
			Size:         f.size,
			HostExtId:    hostextid,
			Status:       IDLE,
		}); !isOk {
			logger.Service.Zap.Errorw(FriendRoom_CREATE_FAILED,
				"GameUser", f.secWebSocketKey,
			)
			errorcode.Service.Fatal(f.secWebSocketKey, FriendRoom_CREATE_FAILED)
			return
		}
		f.seat = Join.do(f.hostExtId, f.number, &player{
			ServerId:  f.serverId,
			RoomUuid:  f.uuid,
			Uid:       f.secWebSocketKey,
			Name:      f.memberName,
			Avatar:    f.avatar,
			Kind:      f.kind,
			Balance:   cent,
			IsHost:    f.isHost,
			IpAddress: ipaddress,
		})

		if f.seat == -1 {
			panic("ERROR SEAT " + f.secWebSocketKey)
		}

		flux.Send(gameuser.ActionJoinGameRoomRecall, f.uuid, f.secWebSocketKey, f.uuid, int(f.seat), banker.FRIEND_ROOM)
	} else {
		if v := Room.info(f.hostExtId, data.Number); v != nil && v.Status == IDLE && data.Number >= 100000 {

			if Player.size(f.hostExtId, data.Number) >= f.size-1 {
				gameConfigRecall.StatusCode = common_proto.Status_kNoSeatAvailable
				f.eFriendRoomJoinRecall(cent, gameConfigRecall)
				return
			}
			if r := Room.info(f.hostExtId, data.Number); r != nil && r.HostExtId != hostextid {
				gameConfigRecall.StatusCode = common_proto.Status_kInvalid
				f.eFriendRoomJoinRecall(cent, gameConfigRecall)
				return
			}
			data.GameConfigCall.SubgameId = v.SubGameId
			f.eGameConfigCall(data.GameConfigCall, gameConfigRecall)

			if gamesetting52.Service.IPConfigEnable(f.secWebSocketKey) > 0 {

				for i := int32(0); i < f.size; i++ {
					if p := Player.info(f.hostExtId, f.number, i); p != nil {
						ipAddressArr := strings.Split(p.IpAddress, ".")
						ipAddressArr2 := strings.Split(ipaddress, ".")
						if ipAddressArr[0] == ipAddressArr2[0] && ipAddressArr[1] == ipAddressArr2[1] {
							gameConfigRecall.StatusCode = common_proto.Status_kIPisSame
							f.eFriendRoomJoinRecall(cent, gameConfigRecall)

							return
						}
					}
				}
			}
			f.uuid = v.Uuid
			f.number = data.Number
			f.isHost = false
			switch gameConfigRecall.StatusCode {
			case common_proto.Status_kInvalid, common_proto.Status_kNoEnoughCredit:
				f.eFriendRoomJoinRecall(cent, gameConfigRecall)
				logger.Service.Zap.Infow("kNoEnoughCredit",
					"ServerId", f.serverId,
					"GameUser", f.secWebSocketKey,
					"MemberId", f.memberId,
					"MemberName", f.memberName,
					"BankerUuid", f.bankerUuid,
					"IsHost", f.isHost,
					"FriendRoomUuid", f.uuid,
					"Size", f.size,
					"Kind", f.kind,
				)
				return
			}

			f.gameId = gamesetting52.Service.GameId(f.secWebSocketKey)
			f.betList = gamesetting52.Service.BetList(f.secWebSocketKey)

			go f.run()

			f.seat = Join.do(f.hostExtId, f.number, &player{
				ServerId:  f.serverId,
				RoomUuid:  f.uuid,
				Uid:       f.secWebSocketKey,
				Name:      f.memberName,
				Avatar:    f.avatar,
				Kind:      f.kind,
				Balance:   cent,
				IsHost:    f.isHost,
				IpAddress: ipaddress,
			})

			if f.seat == -1 {
				panic("ERROR SEAT " + f.secWebSocketKey)
			}

			flux.Send(gameuser.ActionJoinGameRoomRecall, f.uuid, f.secWebSocketKey, f.uuid, int(f.seat), banker.FRIEND_ROOM)
		} else {
			gameConfigRecall.StatusCode = common_proto.Status_kInvalid
		}
	}

	f.eFriendRoomJoinRecall(cent, gameConfigRecall)

	if gameConfigRecall.StatusCode == common_proto.Status_kSuccess {
		f.eBroadcastPlayerIn()

		if f.isHost {
			f.eFriendRoomHostChanged()
		}
	}
}

func (f *friendRoom) eFriendRoomJoinRecall(cent uint64, gameConfigRecall *game_setting52_proto.ConfigRecall) {
	gameConfigRecall.RoomUuid = f.uuid
	gameConfigRecall.PlayerInfo = &auth_proto.PlayerInfo{
		Id:      	f.secWebSocketKey,
		Balance: 	cent,
		Name:    	f.memberName,
		Avatar:  	f.avatar,
		Seat:    	uint32(f.seat),
		Visible: 	nil,
		WinCount: 	0,
	}
	if gameConfigRecall.StatusCode != common_proto.Status_kSuccess {
		if lobbysetting52.Service.AutoATM(f.secWebSocketKey) {
			// TODO JOHNNY 以後可能會有要自動儲值幾%的...
			flux.Send(atm.ActionAtmAutoWithdraw, f.secWebSocketKey, atm.Service.Id, uint8(100), f.hostExtId, f.memberId)
			time.Sleep(1 * time.Second)
		}
	}
	newcent, err := wallet.Service.CentCache(f.secWebSocketKey)
	if err != nil {
		panic("ERROR CENT " + f.secWebSocketKey)
	}
	balance, errBalance := wallet.Service.BalanceCache(f.secWebSocketKey)
	if errBalance != nil {
		panic("ERROR CENT " + f.secWebSocketKey)
	}
	gameConfigRecall.Cent = newcent
	gameConfigRecall.Balance = balance

	data := &friend_room_proto.FriendRoomJoinRecall{
		Msgid:            common52_proto.EMSGID_eFriendRoomJoinRecall,
		StatusCode:       gameConfigRecall.StatusCode,
		Number:           f.number,
		Uuid:             f.uuid,
		GameConfigRecall: gameConfigRecall,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eFriendRoomJoinRecall, f.uuid, f.secWebSocketKey, dataByte)
}

func (f *friendRoom) eGameConfigCall(call *game_setting_proto.ConfigCall, recall *game_setting52_proto.ConfigRecall) {
	dataByte, _ := proto.Marshal(call)

	proto.Unmarshal(
		gamesetting.Service.EMSGID_eGameConfigCall(
			f.secWebSocketKey,
			f.memberId,
			f.guestEnable,
			dataByte,
		),
		recall,
	)
}

func (f *friendRoom) EMSGID_eFriendRoomLeaveCall(msg []byte) {
	r := Room.info(f.hostExtId, f.number)

	if r == nil {
		return
	}

	if r.Status == GAMING {
		return
	}

	data := &friend_room_proto.FriendRoomLeaveCall{}

	proto.Unmarshal(msg, data)

	dataByte, _ := proto.Marshal(data.LobbyConfigCall)
	f.eFriendRoomLeaveRecall(dataByte)
}

func (f *friendRoom) eFriendRoomLeaveRecall(lobbyConfigCall []byte) {
	lobbyConfigRecall := &lobby_setting52_proto.ConfigRecall{}

	if lobbysetting52.Service.AutoATM(f.secWebSocketKey) {
		// TODO JOHNNY 以後可能會有要自動儲值幾%的...
		flux.Send(atm.ActionAtmAutoWithdraw, f.secWebSocketKey, atm.Service.Id, uint8(100), f.hostExtId, f.memberId)

	}

	cent, err := wallet.Service.CentCache(f.secWebSocketKey)
	if err != nil {
		panic("ERROR CENT " + f.secWebSocketKey)
	}
	balance, errBalance := wallet.Service.BalanceCache(f.secWebSocketKey)
	if errBalance != nil {
		panic("ERROR CENT " + f.secWebSocketKey)
	}
	proto.Unmarshal(
		lobbysetting.Service.EMSGID_eLobbyConfigCall(
			f.secWebSocketKey,
			f.memberId,
			f.guestEnable,
			lobbyConfigCall,
		),
		lobbyConfigRecall,
	)

	lobbyConfigRecall.Balance = balance
	lobbyConfigRecall.Cent = cent

	lobbyConfigRecall.PlayerInfo = &auth_proto.PlayerInfo{
		Id:      	f.secWebSocketKey,
		Balance: 	cent,
		Name:    	f.memberName,
		Avatar:  	f.avatar,
		Seat:    	uint32(f.seat),
		Visible: 	nil,
		WinCount: 	0,
	}

	data := &friend_room_proto.FriendRoomLeaveRecall{
		Msgid:             common52_proto.EMSGID_eFriendRoomLeaveRecall,
		StatusCode:        lobbyConfigRecall.StatusCode,
		LobbyConfigRecall: lobbyConfigRecall,
		Uuid:              f.uuid,
		Number:            f.number,
	}

	dataByte, _ := proto.Marshal(data)

	f.eBroadcastPlayerOut()

	if f.isHost {
		f.eFriendRoomDestroy(lobbyConfigRecall)
	}

	flux.Send(EMSGID_eFriendRoomLeaveRecall, f.uuid, f.secWebSocketKey, dataByte)

	Leave.do(f.hostExtId, f.redisKey(), f.number, f.seat)

	f.destroy()

}

func (f *friendRoom) EMSGID_eFriendRoomGameStart(msg []byte) {
	r := Room.info(f.hostExtId, f.number)

	if r == nil {
		return
	}

	if r.Status == GAMING {
		return
	}

	if Player.size(f.hostExtId, f.number) < playerMin {
		return
	}

	data := &friend_room_proto.FriendRoomGameStart{}

	proto.Unmarshal(msg, data)

	logger.Service.Zap.Infow("Friend Room Game Start",
		"ServerId", f.serverId,
		"GameUser", f.secWebSocketKey,
		"MemberId", f.memberId,
		"MemberName", f.memberName,
		"IsHost", f.isHost,
		"FriendRoomUuid", f.uuid,
		"FriendRoomNumber", f.number,
		"Size", f.size,
		"Kind", f.kind,
		"Data", data,
	)

	if f.isHost && f.number == data.Number && f.uuid == data.Uuid {
		r.Status = GAMING
		Room.update(f.hostExtId, f.redisKey(), r)

		flux.Send(botuser.ActionBotUserCreate, f.uuid, botuser.Service.Id,
			f.uuid,
			f.secWebSocketKey,
			banker.FRIEND_ROOM,
			1,
		)

		fluxData := &flux_proto.FluxAction{
			Name: waitingroom.ActionWaitingRoomDone,
		}
		fluxData.Payload = append(fluxData.Payload, []byte(f.uuid))
		f.toAll(fluxData)
	}
}

func (f *friendRoom) eFriendRoomHostChanged() {
	data := &friend_room_proto.FriendRoomHostChanged{
		Msgid:  common52_proto.EMSGID_eFriendRoomHostChanged,
		Number: f.number,
		Uuid:   f.uuid,
		Uid:    f.secWebSocketKey,
		Seat:   f.seat,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eFriendRoomHostChanged, f.uuid, f.secWebSocketKey, dataByte)
}

func (f *friendRoom) eBroadcastPlayerIn() {

	data := auth.Service.BroadcastPlayerIn(f.uuid)

	for i := int32(0); i < f.size; i++ {
		if p := Player.info(f.hostExtId, f.number, i); p != nil {
			u := &auth_proto.PlayerInfo{
				Id:      	p.Uid,
				Balance: 	p.Balance,
				Name:    	format.HideWithStar(p.Name),
				Seat:    	uint32(i),
				Avatar:  	p.Avatar,
				Type:    	auth_proto.PLAYER_TYPE_GAME,
				Visible: 	nil,
				WinCount: 	0,
			}
			data.Player = append(data.Player, u)
		} else {
			u := &auth_proto.PlayerInfo{
				Id:      	"",
				Balance: 	0,
				Name:    	"",
				Seat:    	uint32(i),
				Visible: 	nil,
				WinCount: 	0,
			}
			data.Player = append(data.Player, u)
		}
	}

	dataByte, _ := proto.Marshal(data)

	fluxData := &flux_proto.FluxAction{
		Name: auth.EMSGID_eBroadcastPlayerIn,
	}

	fluxData.Payload = append(fluxData.Payload, dataByte)

	f.toOthers(fluxData)

	flux.Send(auth.EMSGID_eBroadcastPlayerIn, f.uuid, f.secWebSocketKey, dataByte)
}

func (f *friendRoom) eBroadcastPlayerOut() {
	dataByte := auth.Service.BroadcastPlayerOut(
		f.uuid,
		f.secWebSocketKey,
		f.memberName,
		f.avatar,
		uint32(f.seat),
		uint64(0),
	)

	fluxData := &flux_proto.FluxAction{
		Name: auth.EMSGID_eBroadcastPlayerOut,
	}

	fluxData.Payload = append(fluxData.Payload, dataByte)

	f.toOthers(fluxData)

	flux.Send(auth.EMSGID_eBroadcastPlayerOut, f.uuid, f.secWebSocketKey, dataByte)
}

func (f *friendRoom) eFriendRoomDestroy(lobbyConfigRecall *lobby_setting52_proto.ConfigRecall) {
	data := &friend_room_proto.FriendRoomDestroy{
		Msgid:             common52_proto.EMSGID_eFriendRoomDestroy,
		StatusCode:        common_proto.Status_kSuccess,
		LobbyConfigRecall: lobbyConfigRecall,
		Number:            f.number,
		Uuid:              f.uuid,
	}

	dataByte, _ := proto.Marshal(data)

	fluxData := &flux_proto.FluxAction{
		Name: EMSGID_eFriendRoomDestroy,
	}

	fluxData.Payload = append(fluxData.Payload, dataByte)

	f.toOthers(fluxData)
}

func (f *friendRoom) redisKey() string {
	v := fmt.Sprintf("FRIEND_ROOM:%x", sha1.Sum([]byte(f.gameId+f.betList+f.rateList+strconv.FormatUint(uint64(f.rate), 10))))

	logger.Service.Zap.Infow("Friend Room Redis HashId",
		"ServerId", f.serverId,
		"GameUser", f.secWebSocketKey,
		"MemberId", f.memberId,
		"MemberName", f.memberName,
		"IsHost", f.isHost,
		"FriendRoomUuid", f.uuid,
		"Size", f.size,
		"Kind", f.kind,
		"GameId", f.gameId,
		"BetList", f.betList,
		"RateList", f.rateList,
		"Rate", f.rate,
		"HashId", v,
	)

	return v
}

func (f *friendRoom) toSomeone(fluxData *flux_proto.FluxAction, from, to string) {
	fluxData.From = from
	fluxData.To = to

	fluxDataByte, _ := proto.Marshal(fluxData)

	postman.Service.Pub(fluxDataByte)
}

func (f *friendRoom) toTheOthers(fluxData *flux_proto.FluxAction, to string) {
	for i := int32(0); i < f.size; i++ {
		if p := Player.info(f.hostExtId, f.number, i); p != nil && p.Uid != f.secWebSocketKey {
			fluxData.From = to
			fluxData.To = p.ServerId

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}
	}
}

func (f *friendRoom) toOthers(fluxData *flux_proto.FluxAction) {
	for i := int32(0); i < f.size; i++ {
		if p := Player.info(f.hostExtId, f.number, i); p != nil && p.Uid != f.secWebSocketKey {
			fluxData.From = p.Uid
			fluxData.To = p.ServerId

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}
	}
}

func (f *friendRoom) toTheAll(fluxData *flux_proto.FluxAction, to string) {
	for i := int32(0); i < f.size; i++ {
		if p := Player.info(f.hostExtId, f.number, i); p != nil {
			fluxData.From = to
			fluxData.To = p.ServerId

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}
	}
}

func (f *friendRoom) toAll(fluxData *flux_proto.FluxAction) {
	for i := int32(0); i < f.size; i++ {
		if p := Player.info(f.hostExtId, f.number, i); p != nil {
			fluxData.From = p.Uid
			fluxData.To = p.ServerId

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}
	}
}

func (f *friendRoom) waitingCountdown(timeout int) {

	count := 11

	if timeout > 0 {
		count = timeout
	}

	t := time.Tick(time.Second)

	for {
		select {
		case <-t:

			count--

			if count < 1 {

				time.Sleep(1 * time.Second) // for web client animation

				logger.Service.Zap.Infow("Finish Waiting Count Down",
					"FriendRoomUuid", f.uuid,
					"Count", count,
				)

				flux.Send(waitingroom.ActionWaitingRoomDone, f.uuid, f.uuid, "")
				return
			}

			logger.Service.Zap.Infow("Waiting Count Down",
				"FriendRoomUuid", f.uuid,
				"Count", count,
			)

			data := &flux_proto.FluxAction{
				Name: waitingroom.EMSGID_eWaitingCountdown,
			}

			data.Payload = append(data.Payload, waitingroom.Service.EMSGID_eWaitingCountdown(uint64(count)))

			f.toAll(data)

		case <-f.isStopCountdown:
			logger.Service.Zap.Infow("Stop Waiting Count Down",
				"FriendRoomUuid", f.uuid,
			)
			return
		}
	}
}

func (f *friendRoom) destroy() {
	f.rwMutex.Lock()
	defer f.rwMutex.Unlock()

	logger.Service.Zap.Infow("Friend Room UnRegistered",
		"ServerId", f.serverId,
		"GameUser", f.secWebSocketKey,
		"MemberId", f.memberId,
		"MemberName", f.memberName,
		"IsHost", f.isHost,
		"FriendRoomUuid", f.uuid,
		"Size", f.size,
		"Kind", f.kind,
	)
	if f.isDestroy {
		return
	}
	if !f.isDestroy {
		f.isDestroy = true

		flux.UnRegister(f.uuid, f.in)

		f.isStopCountdown <- true

		close(f.isStopCountdown)
	}
}
