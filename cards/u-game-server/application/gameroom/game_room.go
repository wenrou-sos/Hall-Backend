package gameroom

import (
	"crypto/rand"
	"fmt"
	"math/big"
	"os"
	"strconv"
	"sync"
	"time"
	"u-game-server/application/banker"
	banker_proto "u-game-server/application/banker/proto"
	"u-game-server/application/botuser"
	"u-game-server/application/gamesettingU"
	lobby_settingU_proto "u-game-server/application/lobbysettingU/proto"
	"u-game-server/application/lottery"
	"u-game-server/domain/draw"
	"u-game-server/domain/playcards"
	"u-game-server/domain/probability"
	probability_proto "u-game-server/domain/probability/proto"
	"u-game-server/domain/waitingroom"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/format"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	ActionPlayersReady       = "ActionPlayersReady"
	actionCheckVacancy       = "actionCheckVacancy"
	actionPlayerAddCall      = "actionPlayerAddCall"
	actionPlayerAddRecall    = "actionPlayerAddRecall"
	ActionPlayerDeleteCall   = "ActionPlayerDeleteCall"
	actionPlayerDeleteRecall = "actionPlayerDeleteRecall"
	actionDestroy            = "actionDestroy"
	ActionKickOut            = "ActionKickOut"
)

func Builder() *builder {
	return &builder{
		controllerId:               "",
		secWebSocketKey:            "",
		gameId:                     "",
		bet:                        0,
		uuid:                       "",
		roomSize:                   1,
		roundTime:                  0,
		blacklistValue:             0,
		fee:                        0,
		memberType:                 0,
		isIsolated:                 false,
		firstRoundStartWaitingTime: 0,
		roundStartWaitingTime:      0,
	}
}

type builder struct {
	controllerId               string
	secWebSocketKey            string
	gameId                     string
	bet                        uint64
	uuid                       string
	roomSize                   int
	hostextid                  string
	iPBlock                    uint32
	hostBlock                  uint32
	roundTime                  uint32
	predictTime                uint32
	blacklistValue             uint32
	fee                        uint32
	memberType                 int
	isIsolated                 bool
	firstRoundStartWaitingTime uint32
	roundStartWaitingTime      uint32
}

type gameRoom struct {
	controllerId               string
	secWebSocketKey            string
	gameId                     string
	bet                        uint64
	hostextid                  string
	uuid                       string
	roomSize                   int
	poolSize                   string
	in                         chan *flux.Action
	isReady                    chan bool
	isJoined                   chan bool
	isStopCountdown            chan bool
	isVacancy                  chan bool
	isStart                    chan bool
	rwMutex                    *sync.RWMutex
	isDestroy                  bool
	isGaming                   bool
	iPBlock                    uint32
	hostBlock                  uint32
	startSeat                  int32
	lowestSize                 int32
	roundTime                  uint32
	predictTime                uint32
	count                      int32
	blacklistValue             uint32
	fee                        uint32
	memberType                 int
	isIsolated                 bool
	firstRoundStartWaitingTime uint32
	roundStartWaitingTime      uint32
}

func (b *builder) setControllerId(controllerId string) *builder {
	b.controllerId = controllerId
	return b
}

func (b *builder) setSecWebSocketKey(secWebSocketKey string) *builder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *builder) setGameId(gameId string) *builder {
	b.gameId = gameId
	return b
}

func (b *builder) setBet(bet uint64) *builder {
	b.bet = bet
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

func (b *builder) setRoundTime(time uint32) *builder {
	b.roundTime = time
	return b
}

func (b *builder) setPredictTime(time uint32) *builder {
	b.predictTime = time
	return b
}

func (b *builder) setBlacklistValue(value uint32) *builder {
	b.blacklistValue = value
	return b
}

func (b *builder) setFee(fee uint32) *builder {
	b.fee = fee
	return b
}

func (b *builder) setMemberType(memberType int) *builder {
	b.memberType = memberType
	return b
}

func (b *builder) setIsIsolated(isIsolated bool) *builder {
	b.isIsolated = isIsolated
	return b
}

func (b *builder) setFirstRoundStartWaitingTime(time uint32) *builder {
	b.firstRoundStartWaitingTime = time
	return b
}

func (b *builder) setRoundStartWaitingTime(time uint32) *builder {
	b.roundStartWaitingTime = time
	return b
}

func (b *builder) build() *gameRoom {
	v := &gameRoom{
		controllerId:               b.controllerId,
		secWebSocketKey:            b.secWebSocketKey,
		gameId:                     b.gameId,
		bet:                        b.bet,
		uuid:                       b.uuid,
		hostextid:                  b.hostextid,
		roomSize:                   b.roomSize,
		poolSize:                   os.Getenv("POOL_SIZE"),
		in:                         make(chan *flux.Action, 1024),
		isReady:                    make(chan bool, 1024),
		isJoined:                   make(chan bool, 1024),
		isStopCountdown:            make(chan bool, 4),
		isVacancy:                  make(chan bool, 1024),
		isStart:                    make(chan bool, 4),
		rwMutex:                    &sync.RWMutex{},
		isDestroy:                  false,
		isGaming:                   false,
		iPBlock:                    b.iPBlock,
		hostBlock:                  b.hostBlock,
		startSeat:                  -1,
		lowestSize:                 4,
		roundTime:                  b.roundTime,
		predictTime:                b.predictTime,
		count:                      0,
		blacklistValue:             b.blacklistValue,
		fee:                        b.fee,
		memberType:                 b.memberType,
		isIsolated:                 b.isIsolated,
		firstRoundStartWaitingTime: b.firstRoundStartWaitingTime,
		roundStartWaitingTime:      b.roundStartWaitingTime,
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
	logger.Service.Zap.Infow(action.Key().Name(),
		"uuid", g.uuid,
		"bet", g.bet,
	)
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		g.isReady <- true

		go g.waitingCountdown(int(g.firstRoundStartWaitingTime))

	case actionCheckVacancy:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		if g.isDestroy {
			return
		}

		kind := action.Payload()[0].(string)
		j := action.Payload()[1].(*Join)
		for k, v := range players {
			if _, err := wallet.Service.CentCache(v.SecWebSocketKey); err != nil {
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

		vacancy := (len(players) < g.roomSize) && !g.isGaming
		if kind == PLAYER {
			if g.iPBlock > 0 || j.IPBlock > 0 {
				for _, v := range players {
					if len(v.IPAddress) < 2 || len(j.IPAddress) < 2 {
						continue
					}
					if v.IPAddress[0] == j.IPAddress[0] && v.IPAddress[1] == j.IPAddress[1] {
						vacancy = false
					}
				}
			}
			if g.hostBlock > 0 || j.HostBlock > 0 {
				if g.hostextid != j.HostExtId {
					vacancy = false
				}
			}
			p := gamesettingU.Service.IdBlockPercent(j.SecWebSocketKey)
			if p > 0 {
				id := wallet.Service.MemberId(j.SecWebSocketKey)
				for _, v := range players {
					vid := wallet.Service.MemberId(v.SecWebSocketKey)
					minl, maxl := len(id), len(vid)
					if minl > maxl {
						minl, maxl = maxl, minl
					}
					s := 0
					for i := 0; i < minl; i++ {
						if id[i] == vid[i] {
							s++
						}
					}
					if s*100/maxl >= p {
						vacancy = false
						break
					}
				}
			}
		}

		if g.blacklistValue > 0 || g.isIsolated {
			vacancy = false
		}

		switch kind {
		case BOT:
			g.isVacancy <- len(players) < g.roomSize

		case PLAYER:
			g.isVacancy <- vacancy

		default:
			g.isVacancy <- false
		}

	case actionPlayerAddCall:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		j := action.Payload()[0].(*Join)

		if g.isDestroy {
			g.addPlayerRecall(j)
			//flux.Send(actionPlayerAddRecall, g.uuid, action.Key().From(), j)
			return
		}

		for i := 0; i < g.roomSize; i++ {
			if i == 5 && j.Kind == PLAYER {
				break
			}

			if v, ok := players[i]; !ok && g.balanceLimit(j.SecWebSocketKey) {

				if v != nil && v.SecWebSocketKey == j.SecWebSocketKey {
					delete(players, i)
				}

				players[i] = j
				j.Seat = i
				j.GameRoomUuid = g.uuid
				g.addPlayerRecall(j)
				//flux.Send(actionPlayerAddRecall, g.uuid, action.Key().From(), j)
				g.isJoined <- true
				logger.Service.Zap.Infow("Join Game Room Success",
					"GameUser", j.SecWebSocketKey,
					"Seat", j.Seat,
					"GameRoomUuid", g.uuid,
					"Kind", j.Kind,
					"Chan", fmt.Sprintf("%p", g.in),
					"GameRoomPlayers", len(players),
				)
				break
			}
		}
		if j.Kind == BOT && len(players) == int(g.lowestSize) {
			g.isStart <- true
		}
		logger.Service.Zap.Infow("Join Game Room",
			"GameUser", j.SecWebSocketKey,
			"Seat", j.Seat,
			"GameRoomUuid", g.uuid,
			"Kind", j.Kind,
			"Chan", fmt.Sprintf("%p", g.in),
			"GameRoomPlayers", len(players),
		)

		logger.Service.Zap.Debugw("Join Game Room",
			"GameRoomPlayersMap", players,
		)

		if j.Seat < 0 {
			logger.Service.Zap.Warnw("Join Game Room Failed",
				"GameUser", j.SecWebSocketKey,
				"Seat", j.Seat,
				"GameRoomUuid", g.uuid,
				"Kind", j.Kind,
				"Chan", fmt.Sprintf("%p", g.in),
				"GameRoomPlayers", len(players),
			)
			g.addPlayerRecall(j)
			//flux.Send(actionPlayerAddRecall, g.uuid, action.Key().From(), j)
			g.isJoined <- false
		}

	case ActionPlayerDeleteCall:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		l := action.Payload()[0].(*Leave)

		for k, v := range players {
			if v.SecWebSocketKey == l.SecWebSocketKey {
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

		logger.Service.Zap.Debugw("Leave Game Room",
			"GameRoomPlayersMap", players,
		)

		flux.Send(gameuser.ActionLeaveGameRoomRecall, g.uuid, l.SecWebSocketKey, l.GameRoomUuid)
		//flux.Send(actionPlayerDeleteRecall, g.uuid, action.Key().From(), l)

		if len(players) == 0 {
			g.destroy()
		}

	case auth.EMSGID_eBroadcastPlayerIn:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		secWebSocketKey := action.Key().From() // player or bot
		playerType := action.Payload()[0].(auth_proto.PLAYER_TYPE)

		data := auth.Service.BroadcastPlayerIn(g.uuid)

		for i := 0; i < g.roomSize; i++ {

			if v, ok := players[i]; ok {

				cent, err := wallet.Service.CentCache(v.SecWebSocketKey)

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
					Id:       v.SecWebSocketKey,
					Balance:  cent,
					Name:     format.HideWithStar(wallet.Service.MemberName(v.SecWebSocketKey)),
					Seat:     uint32(i),
					Avatar:   v.avatar,
					Visible:  nil,
					WinCount: 0,
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
					Id:       "",
					Balance:  0,
					Name:     "",
					Seat:     uint32(i),
					Visible:  nil,
					WinCount: 0,
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

	case waitingroom.ActionWaitingRoomDone:
		g.rwMutex.Lock()

		g.isGaming = true
		for k, v := range players {
			_, err := wallet.Service.CentCache(v.SecWebSocketKey)

			if err != nil {
				logger.Service.Zap.Infow("Check Players Alive",
					"GameUser", v.SecWebSocketKey,
					"Seat", v.Seat,
					"GameRoomUuid", g.uuid,
					"Chan", fmt.Sprintf("%p", g.in),
					"GameRoomPlayersMap", players,
				)
				delete(players, k)
			}
		}

		playerCount := len(players)

		if len(players) < int(g.lowestSize) && len(players) > 0 {
			var player *Join
			for _, p := range players {
				player = p
			}
			availableSeats := int(g.lowestSize) - len(players)
			playerCount = int(g.lowestSize)
			flux.Send(ActionPlayersReady, g.uuid, g.controllerId, availableSeats, g.uuid, player.SecWebSocketKey, player.HostId, player.HostExtId)
		} else if len(players) == 0 {
			g.destroy()
			return
		} else {
			g.isStart <- true
		}

		if g.startSeat < 0 {
			if n, err := rand.Int(rand.Reader, big.NewInt(int64(playerCount))); err == nil {
				g.startSeat = int32(n.Int64())
			} else {
				panic(err)
			}
		}

		g.rwMutex.Unlock()

		<-g.isStart
		flux.Send(banker.ActionBankerCreate, g.uuid, banker.Service.Id,
			g.uuid,
			banker.GAME_ROOM,
			int32(len(players)),
			g.startSeat,
			g.bet,
			g.roundTime,
			g.predictTime,
		)

		g.broadcastAction(waitingroom.ActionWaitingRoomDone, action, players)

	case banker.EMSGID_eRoundStart:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		data := action.Payload()[0].(*banker_proto.RoundStart)

		for k, v := range players {

			cent, err := wallet.Service.CentCache(v.SecWebSocketKey)

			if err != nil {
				logger.Service.Zap.Errorw("Check Players Alive",
					"GameUser", v.SecWebSocketKey,
					"Seat", k,
					"GameRoomUuid", g.uuid,
					"Chan", fmt.Sprintf("%p", g.in),
					"GameRoomPlayersMap", players,
				)
				panic("ERROR CENT " + v.SecWebSocketKey) // TODO JOHNNY 壓測進來過
				delete(players, k)
			}

			p := &auth_proto.PlayerInfo{
				Id:       v.SecWebSocketKey,
				Balance:  cent,
				Name:     format.HideWithStar(wallet.Service.MemberName(v.SecWebSocketKey)),
				Seat:     uint32(k),
				Avatar:   v.avatar,
				Visible:  nil,
				WinCount: v.winCount,
			}

			switch v.Kind {
			case BOT:
				p.Type = auth_proto.PLAYER_TYPE_BOT

			case PLAYER:
				p.Type = auth_proto.PLAYER_TYPE_GAME
			}

			data.PlayerInfos = append(data.PlayerInfos, p)
		}

		dataByte, _ := proto.Marshal(data)

		g.broadcastData(banker.EMSGID_eRoundStart, players, dataByte, []byte(g.uuid))

	case banker.EMSGID_eRoundEnd:
		g.broadcastAction(banker.EMSGID_eRoundEnd, action, players)

		g.rwMutex.Lock()

		for k, v := range players {
			if v.Kind == BOT {
				delete(players, k)
			} else if g.count >= 3 {
				flux.Send(ActionKickOut, g.uuid, v.SecWebSocketKey, g.uuid)
			}
		}

		g.rwMutex.Unlock()

		go g.waitingCountdown(int(g.roundStartWaitingTime))

	case banker.ActionBankerDeal:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.ActionBankerDeal, action, players)

	case banker.EMSGID_ePlayerRoundStart:
		data := action.Payload()[0].(*banker_proto.PlayerRoundStart)
		dataByte, _ := proto.Marshal(data)
		hands := action.Payload()[1].([]int)
		lastCard := action.Payload()[2].(int)
		lastColor := action.Payload()[3].(int)
		penalty := action.Payload()[4].(int)

		flux.Send(banker.EMSGID_ePlayerRoundStart, g.uuid, players[int(data.Seat)].SecWebSocketKey, dataByte, hands, lastCard, lastColor, penalty)

	case banker.EMSGID_eBroadcastPlayerRoundStart:
		g.broadcastAction(banker.EMSGID_eBroadcastPlayerRoundStart, action, players)

	case draw.EMSGID_eBroadcastDrawTimeout:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(draw.EMSGID_eBroadcastDrawTimeout, action, players)

	case draw.EMSGID_eBroadcastDrawRecall:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(draw.EMSGID_eBroadcastDrawRecall, action, players)

	case playcards.EMSGID_eBroadcastPlayCardsTimeout:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(playcards.EMSGID_eBroadcastPlayCardsTimeout, action, players)

	case playcards.EMSGID_eBroadcastPlayCardsRecall:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(playcards.EMSGID_eBroadcastPlayCardsRecall, action, players)

	case banker.EMSGID_eBroadcastPenalty:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.EMSGID_eBroadcastPenalty, action, players)

	case banker.EMSGID_eBroadcastKeepRecall:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.EMSGID_eBroadcastKeepRecall, action, players)

	case banker.EMSGID_eBroadcastKeepTimeout:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.EMSGID_eBroadcastKeepTimeout, action, players)

	case probability.EMSGID_eBroadcastRanking:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(probability.EMSGID_eBroadcastRanking, action, players)

	case banker.EMSGID_eBroadcastShuffle:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.EMSGID_eBroadcastShuffle, action, players)

	case banker.ActionBankerStart:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.ActionBankerStart, action, players)

	case probability.EMSGID_eBroadcastResult:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		data := action.Payload()[0].(*probability_proto.BroadcastResult)

		g.count++
		g.startSeat = -1

		if g.count < 3 {
			data.Continue = 1
		} else {
			data.Continue = 0
		}

		dataByte, _ := proto.Marshal(data)

		action = flux.NewAction(probability.EMSGID_eBroadcastResult, lottery.Service.Id, g.uuid, dataByte)

		g.broadcastAction(probability.EMSGID_eBroadcastResult, action, players)

	case waitingroom.EMSGID_eWaitingCountdown:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		g.isGaming = false

		g.broadcastAction(waitingroom.EMSGID_eWaitingCountdown, action, players)

	case banker.ActionPlayerResumeGame:
		data := action.Payload()[0].(*lobby_settingU_proto.ConfigRecall)
		secWebSocketKey := action.Payload()[1].(string)

		for k, v := range players {

			if v.Seat == int(data.ResumeGame.GameRecovery.Snapshot.Seat) {
				v.SecWebSocketKey = secWebSocketKey
			}

			cent, err := wallet.Service.CentCache(v.SecWebSocketKey)

			if err != nil {
				logger.Service.Zap.Errorw("Check Players Alive",
					"GameUser", v.SecWebSocketKey,
					"Seat", k,
					"GameRoomUuid", g.uuid,
					"Chan", fmt.Sprintf("%p", g.in),
					"GameRoomPlayersMap", players,
				)
				panic("ERROR CENT " + v.SecWebSocketKey) // TODO JOHNNY 壓測進來過
				delete(players, k)
			}

			p := &auth_proto.PlayerInfo{
				Id:       v.SecWebSocketKey,
				Balance:  cent,
				Name:     format.HideWithStar(wallet.Service.MemberName(v.SecWebSocketKey)),
				Seat:     uint32(k),
				Avatar:   v.avatar,
				Visible:  nil,
				WinCount: v.winCount,
			}

			switch v.Kind {
			case BOT:
				p.Type = auth_proto.PLAYER_TYPE_BOT

			case PLAYER:
				p.Type = auth_proto.PLAYER_TYPE_GAME
			}

			data.ResumeGame.PlayerInfo = append(data.ResumeGame.PlayerInfo, p)
		}
		dataByte, _ := proto.Marshal(data)
		flux.Send(banker.ActionPlayerResumeGame, g.uuid, secWebSocketKey, dataByte)
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

func (g *gameRoom) waitingCountdown(timeout int) {

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

				g.isGaming = true
				time.Sleep(1 * time.Second) // for web client animation

				logger.Service.Zap.Infow("Finish Waiting Count Down",
					"GameRoomUuid", g.uuid,
					"Count", count,
				)

				flux.Send(waitingroom.ActionWaitingRoomDone, g.uuid, g.uuid, "")
				return
			}

			logger.Service.Zap.Infow("Waiting Count Down",
				"GameRoomUuid", g.uuid,
				"Count", count,
			)

			flux.Send(waitingroom.EMSGID_eWaitingCountdown, g.uuid, g.uuid,
				waitingroom.Service.EMSGID_eWaitingCountdown(uint64(count)),
			)

		case <-g.isStopCountdown:
			logger.Service.Zap.Infow("Stop Waiting Count Down",
				"GameRoomUuid", g.uuid,
			)
			return
		}
	}
}

func (g *gameRoom) balanceLimit(secWebSocketKey string) bool {

	cent, err := wallet.Service.CentCache(secWebSocketKey)
	if err != nil {
		logger.Service.Zap.Errorw(GameRoom_GET_CENT_FAILED,
			"GameUser", secWebSocketKey,
			"GameRoomUuid", g.uuid,
		)
		errorcode.Service.Fatal(secWebSocketKey, GameRoom_GET_CENT_FAILED)
		return false
	}

	l := gamesettingU.Service.BalanceLimit(secWebSocketKey)

	if cent < uint64(l) {
		logger.Service.Zap.Infow("No Money",
			"GameUser", secWebSocketKey,
			"Cent", cent,
			"BalanceLimit", l,
			"GameRoomUuid", g.uuid,
		)
		return false
	}
	return true
}
func (g *gameRoom) addPlayerRecall(j *Join) {
	switch j.Kind {
	case BOT:

		// TODO JOHNNY 改同步
		flux.Send(botuser.ActionGameRoomJoinRecall, g.uuid, j.SecWebSocketKey, j.Seat)
	case PLAYER:
		// TODO JOHNNY 改同步
		flux.Send(gameuser.ActionJoinGameRoomRecall, g.uuid, j.SecWebSocketKey,
			j.GameRoomUuid,
			j.Seat,
			banker.GAME_ROOM,
		)
	}
}
func (g *gameRoom) hashId() string {
	return Service.hashId(g.gameId, g.bet)
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
