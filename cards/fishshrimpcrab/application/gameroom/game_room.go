package gameroom

import (
	"crypto/rand"
	"fish-shrimp-crab-game-server/application/botuser"
	gameroom_proto "fish-shrimp-crab-game-server/application/gameroom/proto"
	"fish-shrimp-crab-game-server/application/gamesettingFS"
	game_settingFS_proto "fish-shrimp-crab-game-server/application/gamesettingFS/proto"
	"fish-shrimp-crab-game-server/application/lottery"
	"fish-shrimp-crab-game-server/domain/bet"
	bet_proto "fish-shrimp-crab-game-server/domain/bet/proto"
	"fish-shrimp-crab-game-server/domain/probability"
	probability_proto "fish-shrimp-crab-game-server/domain/probability/proto"
	commonFS_proto "fish-shrimp-crab-game-server/models/proto"
	"fmt"
	"math/big"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"gitlab.iplaystar.net/game-server/player"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/format"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	GAME_ROOM                     = "GAME_ROOM"
	BOT_ROOM                      = "BOT_ROOM"
	VIP_ROOM                      = "VIP_ROOM"
	ActionPlayersReady            = "ActionPlayersReady"
	actionCheckVacancy            = "actionCheckVacancy"
	actionPlayerAddCall           = "actionPlayerAddCall"
	actionPlayerAddRecall         = "actionPlayerAddRecall"
	ActionPlayerDeleteCall        = "ActionPlayerDeleteCall"
	actionDestroy                 = "actionDestroy"
	EMSGID_eHistory               = "EMSGID_eHistory"
	ActionGameRoundStart          = "ActionGameRoundStart"
	ActionGameRoundEnd            = "ActionGameRoundEnd"
	ActionNewBetRound             = "ActionNewBetRound"
	EMSGID_eRoundStart            = "EMSGID_eRoundStart"
	EMSGID_eRoundEnd              = "EMSGID_eRoundEnd"
	EMSGID_eKickOutWarn           = "EMSGID_eKickOutWarn"
	EMSGID_eJoinedRoomInfo        = "EMSGID_eJoinedRoomInfo"
	EMSGID_eGameroomHistoryCall   = "EMSGID_eGameroomHistoryCall"
	EMSGID_eGameroomHistoryRecall = "EMSGID_eGameroomHistoryRecall"
	destoryBotPlayer              = "destoryBotPlayer"
	EMSGID_ePlayerLevaeRoom       = "EMSGID_ePlayerLevaeRoom"
	STATUS_RollDice               = 1
	STATUS_BetRound               = 2
	STATUS_result                 = 3
	IDLE_KICK_TIMES               = 5     //閒置幾局剔除次數
	ROLL_DICE_WAITING_TIME        = 6000  //搖骰動畫時間(毫秒)
	DEFAULT_BET_WAITING_TIME      = 15    //預設的下注時間
	RESULT_WAITING_TIME           = 13500 //開骰動畫時間(毫秒)
)

func Builder() *builder {
	return &builder{
		controllerId: "",
		gameId:       "",
		betList:      "",
		rateIndex:    0,
		rateList:     "",
		rate:         0,
		uuid:         "",
		roomSize:     1,
		kind:         "",
		vipInfo:      nil,
	}
}

type builder struct {
	controllerId string
	gameId       string
	betList      string
	rateList     string
	rate         uint32
	rateIndex    int
	uuid         string
	roomSize     int
	hostextid    string
	iPBlock      uint32
	hostBlock    uint32
	histories    [10][3]int32
	kind         string
	vipInfo      *vipInfo
}

type gameRoom struct {
	controllerId    string
	gameId          string
	betList         string
	rateList        string
	hostextid       string
	rate            uint32
	rateIndex       int
	uuid            string
	histories       [10][3]int32
	kind            string
	roomSize        int
	poolSize        string
	in              chan *flux.Action
	isReady         chan bool
	isJoined        chan bool
	isStopCountdown chan bool
	isVacancy       chan bool
	rwMutex         *sync.RWMutex
	isDestroy       bool
	isBetting       bool
	iPBlock         uint32
	hostBlock       uint32
	betRoundUuid    string
	status          int32
	vipInfo         *vipInfo
}

type vipInfo struct {
    secWebSocketKey string
    level           uint32
    hostId          string
    memberId        string
    gameid          string
    lastRoomId      string
    histories       [10][3]int32
    billCurrency    string
    isVipChangeRoom bool
}

func (b *builder) setControllerId(controllerId string) *builder {
	b.controllerId = controllerId
	return b
}

func (b *builder) setGameId(gameId string) *builder {
	b.gameId = gameId
	return b
}

func (b *builder) setBetList(betList string) *builder {
	b.betList = betList
	return b
}

func (b *builder) setRateList(rateList string) *builder {
	b.rateList = rateList
	return b
}

func (b *builder) setRate(rate uint32) *builder {
	b.rate = rate
	return b
}

func (b *builder) setRateIndex(rateIndex int) *builder {
	b.rateIndex = rateIndex
	return b
}

func (b *builder) setUuid(uuid string) *builder {
	b.uuid = uuid
	return b
}

func (b *builder) setRoomSize(roomSize int) *builder {
	b.roomSize = roomSize
	return b
}

func (b *builder) setHostExtId(hostextid string) *builder {
	b.hostextid = hostextid
	return b
}

func (b *builder) setIPBlock(enable uint32) *builder {
	b.iPBlock = enable
	return b
}

func (b *builder) setHostBlock(enable uint32) *builder {
	b.hostBlock = enable
	return b
}

func (b *builder) setHistory(histories [10][3]int32) *builder {
	b.histories = histories
	return b
}

func (b *builder) setKind(kind string) *builder {
	b.kind = kind
	return b
}

func (b *builder) SetVipInfo(secWebSocketKey string, level uint32, lastRoomId string, isVipChangeRoom bool) *builder {
    b.vipInfo = &vipInfo{
        secWebSocketKey: secWebSocketKey,
        level:           level,
        lastRoomId:      lastRoomId,
        isVipChangeRoom: isVipChangeRoom,
    }
    return b
}

func (b *builder) build() *gameRoom {
	v := &gameRoom{
		controllerId:    b.controllerId,
		gameId:          b.gameId,
		betList:         b.betList,
		rateList:        b.rateList,
		rate:            b.rate,
		rateIndex:       b.rateIndex,
		uuid:            b.uuid,
		hostextid:       b.hostextid,
		roomSize:        b.roomSize,
		histories:       b.histories,
		kind:            b.kind,
		poolSize:        os.Getenv("POOL_SIZE"),
		in:              make(chan *flux.Action, 1024),
		isReady:         make(chan bool, 1024),
		isJoined:        make(chan bool, 1024),
		isStopCountdown: make(chan bool, 4),
		isVacancy:       make(chan bool, 1024),
		rwMutex:         &sync.RWMutex{},
		isDestroy:       false,
		isBetting:       false,
		iPBlock:         b.iPBlock,
		hostBlock:       b.hostBlock,
		status:          STATUS_RollDice,
		vipInfo:         b.vipInfo,
	}

	v.run()

	return v
}

func (g *gameRoom) run() {
	flux.Register(g.uuid, g.in)

	players := make(map[int]*Join, g.roomSize)

	poolSize := 10

	if g.poolSize != "" {
		if poolSize, _ = strconv.Atoi(g.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	// used 10 pool size to reduce memory usage
	for i := 0; i < 10; i++ {
		go func() {
			for action := range g.in {
				g.handleAction(action, players)
			}
		}()
	}
}

func (g *gameRoom) handleAction(action *flux.Action, players map[int]*Join) {
	if action.Key().To() != g.uuid {
		return
	}

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		g.isReady <- true

		go g.addBotUserContinuously()

	case actionCheckVacancy:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		if g.isDestroy {
			return
		}

		kind := action.Payload()[0].(string)
		j := action.Payload()[1].(*Join)
		for k, v := range players {
			if _, err := wallet.Service.BalanceCache(v.SecWebSocketKey); err != nil {
				logger.Service.Zap.Warnw("Check Players Alive",
					"GameUser", v.SecWebSocketKey,
					"Seat", k,
					"GameRoomUuid", g.uuid,
					"Chan", fmt.Sprintf("%p", g.in),
					"GameRoomPlayersMap", players,
				)
				delete(players, k)
			}
		}

		if kind == BOT {
			g.isVacancy <- len(players) < g.roomSize
			return
		}

		vacancy := len(players) < g.roomSize && g.status != STATUS_result
		if kind == PLAYER {
			if g.iPBlock > 0 || j.IPBlock > 0 {
				for _, v := range players {
					ipAddressArr := strings.Split(v.IPAddress, ".")
					ipAddressArr2 := strings.Split(j.IPAddress, ".")
					if ipAddressArr[0] == ipAddressArr2[0] && ipAddressArr[1] == ipAddressArr2[1] {
						vacancy = false
					}
				}
			}
			if g.hostBlock > 0 || j.HostBlock > 0 {
				if g.hostextid != j.HostExtId {
					vacancy = false
				}
			}
		}

		g.isVacancy <- vacancy

	case actionPlayerAddCall:

		j := action.Payload()[0].(*Join)

		if g.isDestroy {
			g.addPlayerRecall(j, players)
			return
		}

		g.rwMutex.Lock()
		for i := 0; i < g.roomSize; i++ {
			if v, ok := players[i]; ok {
				if v != nil && v.SecWebSocketKey == j.SecWebSocketKey {
					delete(players, i)
				}
			}
		}

		emptySeats := make([]int, 0)
		for i := 0; i < g.roomSize; i++ {
			if _, ok := players[i]; !ok {
				emptySeats = append(emptySeats, i)
			}
		}

		r, _ := rand.Int(rand.Reader, big.NewInt(int64(len(emptySeats))))
		seat := emptySeats[int(r.Int64())]

		players[seat] = j
		j.Seat = seat
		j.GameRoomUuid = g.uuid
		j.lastRoomId = g.uuid
		if j.Kind == PLAYER && g.kind != VIP_ROOM {
			g.kind = GAME_ROOM
		}
		g.addPlayerRecall(j, players)
		//flux.Send(actionPlayerAddRecall, g.uuid, action.Key().From(), j)
		g.isJoined <- true
		if j.Kind != "BOT" {
			logger.Service.Zap.Infow("Join Game Room Success",
				"GameUser", j.SecWebSocketKey,
				"Seat", j.Seat,
				"GameRoomUuid", g.uuid,
				"Kind", j.Kind,
				"Chan", fmt.Sprintf("%p", g.in),
				"GameRoomPlayers", len(players),
			)
		}

		g.rwMutex.Unlock()

		if j.Seat < 0 {
			logger.Service.Zap.Warnw("Join Game Room Failed",
				"GameUser", j.SecWebSocketKey,
				"Seat", j.Seat,
				"GameRoomUuid", g.uuid,
				"Kind", j.Kind,
				"Chan", fmt.Sprintf("%p", g.in),
				"GameRoomPlayers", len(players),
			)
			g.addPlayerRecall(j, players)
			//flux.Send(actionPlayerAddRecall, g.uuid, action.Key().From(), j)
			g.isJoined <- false
		}

	case ActionPlayerDeleteCall:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()
		l := action.Payload()[0].(*Leave)

		//刪除舊有的player
		for k, v := range players {
			if v.SecWebSocketKey == l.SecWebSocketKey {
				l.SecWebSocketKey = v.ReconnectWebSocketKey //如果有玩家斷線重進房的話，ReconnectWebSocketKey會不同
				delete(players, k)
				break
			}
		}

		logger.Service.Zap.Infow("Leave Game Room",
			"GameUser", l.SecWebSocketKey,
			"GameRoomUuid", g.uuid,
			"Chan", fmt.Sprintf("%p", g.in),
			"GameRoomPlayers", len(players),
		)

		leaveGameRoomRecall := &gameroom_proto.ActionLeaveGameRoomRecall{
			Msgid: commonFS_proto.EMSGID_ePlayerLevaeRoom,
		}
		bytes, _ := proto.Marshal(leaveGameRoomRecall)

		flux.Send(EMSGID_ePlayerLevaeRoom, g.uuid, l.SecWebSocketKey, bytes, g.histories)

		if len(players) == 0 {
			g.destroy()
		}

	case auth.EMSGID_eBroadcastPlayerIn:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		secWebSocketKey := action.Key().From() // player or bot
		playerType := action.Payload()[0].(auth_proto.PLAYER_TYPE)

		data := auth.Service.BroadcastPlayerIn(g.uuid)

		for i := 0; i < g.roomSize; i++ {

			if v, ok := players[i]; ok {

				balance, err := wallet.Service.BalanceCache(v.SecWebSocketKey)

				if err != nil {
					logger.Service.Zap.Warnw("Check Players Alive",
						"GameUser", v.SecWebSocketKey,
						"Seat", i,
						"GameRoomUuid", g.uuid,
						"Chan", fmt.Sprintf("%p", g.in),
						"GameRoomPlayersMap", players,
					)
					delete(players, i)
					return
				}

				u := &auth_proto.PlayerInfo{
					Id:      v.SecWebSocketKey,
					Balance: balance,
					Name:    format.HideWithStar(wallet.Service.MemberName(v.SecWebSocketKey)),
					Seat:    uint32(i),
					Avatar:  v.Avatar,
					Visible: nil,
				}

				if len(v.SecWebSocketKey) == len(secWebSocketKey) {
					u.Type = playerType
				} else {
					switch playerType {
					case auth_proto.PLAYER_TYPE_GAME:
						u.Type = auth_proto.PLAYER_TYPE_BOT

					case auth_proto.PLAYER_TYPE_BOT:
						u.Type = auth_proto.PLAYER_TYPE_GAME
					}
				}

				data.Player = append(data.Player, u)
			} else {
				u := &auth_proto.PlayerInfo{
					Id:      "",
					Balance: 0,
					Name:    "",
					Seat:    uint32(i),
					Visible: nil,
				}
				data.Player = append(data.Player, u)
			}
		}

		dataByte, _ := proto.Marshal(data)
		g.broadcastData(auth.EMSGID_eBroadcastPlayerIn, players, dataByte)

	case auth.EMSGID_eBroadcastPlayerOut:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(auth.EMSGID_eBroadcastPlayerOut, action, players)

	case bet.EMSGID_eBroadcastBetRecall:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		for _, player := range players {
			if player.Kind == PLAYER {
				flux.Send(bet.EMSGID_eBroadcastBetRecall, g.uuid, player.SecWebSocketKey, action.Payload()[0])
			}
		}

	case bet.EMSGID_eBroadcastClearBetsRecall:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		for _, player := range players {
			if player.Kind == PLAYER {
				flux.Send(bet.EMSGID_eBroadcastClearBetsRecall, g.uuid, player.SecWebSocketKey, action.Payload()[0])
			}
		}

	case bet.EMSGID_eBroadcastMultiBetRecall:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		for _, player := range players {
			if player.Kind == PLAYER {
				flux.Send(bet.EMSGID_eBroadcastMultiBetRecall, g.uuid, player.SecWebSocketKey, action.Payload()[0])
			}
		}

	case probability.EMSGID_eBroadcastResult:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(probability.EMSGID_eBroadcastResult, action, players)

	case ActionNewBetRound:
		betTime := DEFAULT_BET_WAITING_TIME //TODO
		for _, j := range players {
			if j.Kind != "BOT" {
				if t := gamesettingFS.Service.BetWaitingTime(j.SecWebSocketKey); t > 0 {
					betTime = int(t)
					break
				}
			}
		}

		flux.Send(bet.ActionBetRoundStart, g.uuid, bet.Service.Id, g.uuid, g.kind, betTime)

		g.status = STATUS_BetRound

	case bet.EMSGID_eBetRoundStart:
		g.rwMutex.Lock()
		betRoundUuid := action.Payload()[1].(string)
		g.betRoundUuid = betRoundUuid
		g.isBetting = true

		g.rwMutex.Unlock()

		g.broadcastAction(bet.EMSGID_eBetRoundStart, action, players)

	case bet.EMSGID_eBetRoundCountdown:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(bet.EMSGID_eBetRoundCountdown, action, players)

	case bet.EMSGID_eBetRoundEnd:
		g.rwMutex.Lock()
		g.isBetting = false
		g.betRoundUuid = ""
		g.rwMutex.Unlock()

		g.rwMutex.RLock()
		bets := action.Payload()[1].(map[string][]bet_proto.BetCall)

		// 累積未下注次數
		for _, join := range players {
			if join.Kind == PLAYER {
				if bets[join.SecWebSocketKey] == nil {
					join.NoneBetCount++
				} else {
					join.NoneBetCount = 0
				}
			}
		}
		for playerUuid := range bets {
			flux.Send(bet.ActionClearBetStatus, g.uuid, playerUuid)
		}

		flux.Send(bet.ActionBetRoundEnd, Service.Id, g.uuid, g.uuid, bets)
		g.broadcastAction(bet.EMSGID_eBetRoundEnd, action, players)
		g.rwMutex.RUnlock()

	case ActionGameRoundStart:
		g.rwMutex.Lock()
		g.status = STATUS_RollDice
		g.rwMutex.Unlock()

		logger.Service.Zap.Infow("Game Round Start", "GameRoomUuid", g.uuid)

		roundStartCall := &gameroom_proto.RoundStart{
			Msgid:    commonFS_proto.EMSGID_eRoundStart,
			RoomUuid: g.uuid,
		}
		bytes, _ := proto.Marshal(roundStartCall)

		g.rwMutex.RLock()
		g.broadcastData(EMSGID_eRoundStart, players, bytes)

		// 搖骰
		//rollTime, _ := strconv.Atoi(os.Getenv("ROLL_DICE_TIME"))
		//time.Sleep(time.Duration(rollTime) * time.Millisecond)

		rollTime := uint32(ROLL_DICE_WAITING_TIME)
		go g.rolldiceCountdown(rollTime)

		g.rwMutex.RUnlock()

	case bet.ActionBetRoundEnd:
		g.rwMutex.Lock()
		g.status = STATUS_result
		g.rwMutex.Unlock()

		gameRoomUuid := action.Payload()[0].(string)
		bets := action.Payload()[1].(map[string][]bet_proto.BetCall)
		logger.Service.Zap.Infow("Bet Round End ", "GameRoomUuid", gameRoomUuid)

		var result [3]int32
		if g.kind == VIP_ROOM && g.vipInfo.level != 0 {
			var allResult [][3]int32
			for i := 0; i < int(g.vipInfo.level); i++ {
				r := probability.Service.Roll()
				allResult = append(allResult, r)
			}
			
			minTotalWinIndex := lottery.Service.VipResult(bets, allResult, gameRoomUuid, g.vipInfo.secWebSocketKey, int(g.vipInfo.level))

			result = allResult[minTotalWinIndex]
		} else { //原本GAME_ROOM流程
			//取得開骰結果
			result = probability.Service.Roll()
			logger.Service.Zap.Infow("Dice Result ", "Dices", result)

			lottery.Service.Result(bets, result, gameRoomUuid)
		}
			
		//將開骰結果廣播給前端
		deal := &probability_proto.Deal{
			Msgid:         commonFS_proto.EMSGID_eDeal,
			RoomUuid:      gameRoomUuid,
			Dice1:         result[0],
			Dice2:         result[1],
			Dice3:         result[2],
		}

		bytes, _ := proto.Marshal(deal)

		g.broadcastData(probability.EMSGID_eBroadcastDeal, players, bytes)

		g.rwMutex.Lock()

		for i := 9; i >= 1; i-- {
			g.histories[i] = g.histories[i-1]
		}

		g.histories[0] = result

		g.rwMutex.Unlock()

		record := &probability_proto.Record{
			Msgid:   commonFS_proto.EMSGID_eHistory,
			Records: nil,
		}

		for _, histories := range g.histories {
			d := &probability_proto.Deal{
				Dice1: histories[0],
				Dice2: histories[1],
				Dice3: histories[2],
			}
			record.Records = append(record.Records, d)
		}

		//清除betRound的記憶體
		flux.Send(bet.ActionBetRoundEnd, g.uuid, bet.Service.Id, g.uuid)

		go g.waitTimeCountdown(uint32(RESULT_WAITING_TIME))

	case ActionGameRoundEnd:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()
		// 機器人房繼續遊玩
		if g.kind == BOT_ROOM {
			logger.Service.Zap.Infow("BOT_ROOM keep playing", "uuid", g.uuid, "bot remaining", len(players))
			flux.Send(ActionGameRoundStart, g.uuid, g.uuid)
			break
		}

		roundEndCall := &gameroom_proto.RoundEnd{
			Msgid:    commonFS_proto.EMSGID_eRoundEnd,
			RoomUuid: g.uuid,
		}
		bytes, _ := proto.Marshal(roundEndCall)
		g.broadcastData(EMSGID_eRoundEnd, players, bytes)

		// 連續未下注達 10 次則踢出房間
		for _, join := range players {
			if join.NoneBetCount == IDLE_KICK_TIMES {
				kickwarn := &gameroom_proto.KickOutWarn{
					Msgid:    commonFS_proto.EMSGID_eKickOutWarn,
					RoomUuid: g.uuid,
				}

				bytes, _ := proto.Marshal(kickwarn)
				flux.Send(EMSGID_eKickOutWarn, g.uuid, join.SecWebSocketKey, bytes)

				l := LeaveBuilder().
					SetControllerId(player.Controller.Id).
					SetSecWebSocketKey(join.SecWebSocketKey).
					SetGameRoomUuid(join.GameRoomUuid).
					SetKind(PLAYER).
					Build()

				flux.Send(ActionPlayerDeleteCall, g.uuid, g.uuid, l)
			}
		}

		// 一般房需要有實體玩家才會繼續遊玩
		isContinue := false
		for _, join := range players {
			if join.Kind == PLAYER {
				isContinue = true
			}
		}

		if isContinue {
			flux.Send(ActionGameRoundStart, g.uuid, g.uuid)
		} else {
			g.destroy()
		}

	case lottery.EMSGID_eBroadcastLotteryResult:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()
		g.broadcastAction(lottery.EMSGID_eBroadcastLotteryResult, action, players)

	case EMSGID_eGameroomHistoryCall:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		secWebSocketKey := action.Key().From()
		gameHistoryRecall := &gameroom_proto.GameroomHistoryRecall{
			Msgid:     commonFS_proto.EMSGID_eGameroomHistoryRecall,
			Histories: nil,
		}
		for i := range g.histories {
			var history []int32
			for j := range g.histories[i] {
				history = append(history, g.histories[i][j])
			}
			gameHistoryRecall.Histories = append(gameHistoryRecall.Histories,
				&gameroom_proto.History{Dices: history},
			)
		}
		bytes, _ := proto.Marshal(gameHistoryRecall)
		flux.Send(EMSGID_eGameroomHistoryRecall, g.uuid, secWebSocketKey, bytes)

	case destoryBotPlayer: //用uuid去找
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		botUuid := action.Payload()[0].(string)
		for _, player := range players {
			if player.SecWebSocketKey == botUuid {
				delete(players, player.Seat)
				break
			}
		}

	case PlayerIsReconnected:
		newSocketKey := action.Payload()[0].(string)
		newSocketMemberId := action.Payload()[1].(string)
		for _, player := range players {
			memberId := wallet.Service.MemberId(player.SecWebSocketKey)
			if memberId == newSocketMemberId {
				player.ReconnectWebSocketKey = newSocketKey
				break
			}
		}
		
	case ActionVipSetting:
		newLevel := action.Payload()[0].(uint32)
		if g.kind == VIP_ROOM {
			g.vipInfo.level = newLevel
		}
	}
}

func (g *gameRoom) broadcastAction(actionName string, action *flux.Action, players map[int]*Join) {
	g.broadcastData(actionName, players, action.Payload()...)
}

func (g *gameRoom) broadcastData(actionName string, players map[int]*Join, data ...interface{}) {
	for _, v := range players {
		flux.Send(actionName, g.uuid, v.SecWebSocketKey, data...)
	}
}

func (g *gameRoom) addPlayerRecall(j *Join, players map[int]*Join) {
	switch j.Kind {
	case BOT:

		// TODO JOHNNY 改同步
		flux.Send(botuser.ActionGameRoomJoinRecall, player.Controller.Id, j.SecWebSocketKey, j.Seat)

	case PLAYER:
		// TODO JOHNNY 改同步
		flux.Send(gameuser.ActionJoinGameRoomRecall, player.Controller.Id, j.SecWebSocketKey,
			j.GameRoomUuid,
			j.Seat,
			j.lastRoomId,
			g.kind,
		)

		if g.betRoundUuid != "" {
			flux.Send(bet.ActionBetRoundJoin, g.uuid, g.betRoundUuid, j.SecWebSocketKey)
		}

		roomInfo := &game_settingFS_proto.JoinedRoomInfo{
			Msgid:      commonFS_proto.EMSGID_eJoinedRoomInfo,
			RoomUuid:   g.uuid,
			Status:     g.status,
			Seat:       int32(j.Seat),
			PlayerInfo: nil,
		}
		//從GAME_ROOM -> VIP_ROOM
        if g.kind == VIP_ROOM && j.lastRoomId != "" && j.vipInfo.isVipChangeRoom {
            roomInfo.RoomUuid = g.vipInfo.lastRoomId
        }
		for _, join := range players {
			balance, _ := wallet.Service.Balance(join.SecWebSocketKey)
			roomInfo.PlayerInfo = append(roomInfo.PlayerInfo, &auth_proto.PlayerInfo{
				Id:      join.SecWebSocketKey,
				Name:    format.HideWithStar(wallet.Service.MemberName(join.SecWebSocketKey)),
				Seat:    uint32(join.Seat),
				Avatar:  join.Avatar,
				Balance: balance,
				Visible: nil,
			})
		}
		flux.Send(EMSGID_eJoinedRoomInfo, g.uuid, j.SecWebSocketKey, roomInfo)
	}
}

func (g *gameRoom) hashId() string {
	return Service.hashId(g.gameId, g.betList, g.rateList, g.rate)
}

func (g *gameRoom) destroy() {

	if g.isDestroy {
		return
	}

	if !g.isDestroy {
		g.isDestroy = true

		g.isStopCountdown <- true

		logger.Service.Zap.Infow("Unregister GameRoom",
			"GameRoomUuid", g.uuid,
		)

		flux.UnRegister(g.uuid, g.in)
		flux.Send(actionDestroy, g.uuid, Service.Id, "")
		close(g.isReady)
		close(g.isJoined)
		close(g.isStopCountdown)
		close(g.isVacancy)
	}
}

func (g *gameRoom) waitTimeCountdown(timeout uint32) {
	count := timeout

	t := time.Tick(time.Second)
	for {
		select {
		case <-t:

			count -= 1000

			if count < 1000 {
				time.Sleep(time.Duration(count) * time.Millisecond) // for web client animation
				flux.Send(ActionGameRoundEnd, g.uuid, g.uuid)
				return
			}
		}
	}
}

func (g *gameRoom) rolldiceCountdown(timeout uint32) {
	count := timeout

	t := time.Tick(time.Second)
	for {
		select {
		case <-t:

			count -= 1000

			if count < 1000 {
				time.Sleep(time.Duration(count) * time.Millisecond) // for web client animation
				// logger.Service.Zap.Infow("roll dice Count Down Finish")
				flux.Send(ActionNewBetRound, g.uuid, g.uuid)
				return
			}
		}
	}
}

func (g *gameRoom) addBotUserContinuously() {
	for {
		//房間已銷毀
		if g.isDestroy {
			return
		}

		timeout := uint64(5000)
		r1, _ := rand.Int(rand.Reader, big.NewInt(100))
		if r1.Uint64() < 40 {
			r2, _ := rand.Int(rand.Reader, big.NewInt(2901))
			timeout = 100 + r2.Uint64()
		} else if r1.Uint64() < 80 {
			r2, _ := rand.Int(rand.Reader, big.NewInt(1001))
			timeout = 2000 + r2.Uint64()
		} else {
			r2, _ := rand.Int(rand.Reader, big.NewInt(3001))
			timeout = 2000 + r2.Uint64()
		}
		time.Sleep(time.Duration(timeout) * time.Millisecond)
		if g.status != STATUS_result {
			flux.Send(botuser.ActionBotUserCreate, player.Controller.Id, botuser.Service.Id,
				g.uuid,
				g.rate,
				g.rateIndex,
				g.betRoundUuid,
				g.betList,
			)
		}
	}
}
