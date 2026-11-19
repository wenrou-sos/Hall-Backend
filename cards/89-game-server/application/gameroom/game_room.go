package gameroom

import (
	"89-game-server/application/banker"
	banker_proto "89-game-server/application/banker/proto"
	"89-game-server/application/botuser"
	"89-game-server/application/gamesetting89"
	"89-game-server/domain/bet"
	bet_proto "89-game-server/domain/bet/proto"
	"89-game-server/domain/draw"
	"89-game-server/domain/probability"
	"89-game-server/domain/waitingroom"
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

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
)

func Builder() *builder {
	return &builder{
		controllerId: "",
		gameId:       "",
		betList:      "",
		rateList:     "",
		rate:         0,
		uuid:         "",
		roomSize:     1,
	}
}

type builder struct {
	controllerId string
	gameId       string
	betList      string
	rateList     string
	rate         uint32
	uuid         string
	roomSize     int
	hostextid    string
	iPBlock      uint32
	hostBlock    uint32
}

type gameRoom struct {
	controllerId    string
	gameId          string
	betList         string
	rateList        string
	hostextid       string
	rate            uint32
	uuid            string
	roomSize        int
	poolSize        string
	in              chan *flux.Action
	isReady         chan bool
	isJoined        chan bool
	isStopCountdown chan bool
	isVacancy       chan bool
	rwMutex         *sync.RWMutex
	isDestroy       bool
	isGaming        bool
	iPBlock         uint32
	hostBlock       uint32
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
func (b *builder) build() *gameRoom {
	v := &gameRoom{
		controllerId:    b.controllerId,
		gameId:          b.gameId,
		betList:         b.betList,
		rateList:        b.rateList,
		rate:            b.rate,
		uuid:            b.uuid,
		hostextid:       b.hostextid,
		roomSize:        b.roomSize,
		poolSize:        os.Getenv("POOL_SIZE"),
		in:              make(chan *flux.Action, 1024),
		isReady:         make(chan bool, 1024),
		isJoined:        make(chan bool, 1024),
		isStopCountdown: make(chan bool, 4),
		isVacancy:       make(chan bool, 1024),
		rwMutex:         &sync.RWMutex{},
		isDestroy:       false,
		isGaming:        false,
		iPBlock:         b.iPBlock,
		hostBlock:       b.hostBlock,
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

		timeout := 0

		g.rwMutex.RLock()
		for _, v := range players {
			if t := gamesetting89.Service.RoundStartWaitingTime(v.SecWebSocketKey); t > 0 {
				timeout = int(t)
				break
			}
		}
		g.rwMutex.RUnlock()

		go g.waitingCountdown(timeout)

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
					Id:      v.SecWebSocketKey,
					Balance: cent,
					Name:    format.HideWithStar(wallet.Service.MemberName(v.SecWebSocketKey)),
					Seat:    uint32(i),
					Avatar:  v.avatar,
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

	case waitingroom.ActionWaitingRoomDone:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		g.broadcastAction(waitingroom.ActionWaitingRoomDone, action, players)

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
			} else {

				if v.Kind == PLAYER {

					g.isGaming = true

					flux.Send(ActionPlayersReady, g.uuid, g.controllerId,
						g.roomSize-len(players),
						g.uuid,
						g.rate,
						v.SecWebSocketKey,
					)
					break
				}
			}
		}

		if len(players) == 0 {
			g.destroy()
		}

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
				Id:      v.SecWebSocketKey,
				Balance: cent,
				Name:    format.HideWithStar(wallet.Service.MemberName(v.SecWebSocketKey)),
				Seat:    uint32(k),
				Avatar:  v.avatar,
				Visible: nil,
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
			}
		}

		timeout := 0

		for _, v := range players {
			if t := gamesetting89.Service.RoundStartWaitingTime(v.SecWebSocketKey); t > 0 {
				timeout = int(t)
				break
			}
		}

		g.rwMutex.Unlock()

		go g.waitingCountdown(timeout)

	case bet.EMSGID_eBroadcastBetRecall:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		data := action.Payload()[0].(*bet_proto.BroadcastBetRecall)
		if _, ok := players[int(data.BetRecall.Seat)]; !ok {
			logger.Service.Zap.Infow("Check BroadcastBetRecall",
				"Seat", data.BetRecall.Seat,
				"GameRoomUuid", data.BetRecall.GetRoomUuid,
			)
			return
		}

		dataByte, _ := proto.Marshal(data)
		g.broadcastData(bet.EMSGID_eBroadcastBetRecall, players, dataByte)

	case banker.ActionBankerDeal:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.ActionBankerDeal, action, players)

	case draw.EMSGID_eBroadcastDrawTimeout:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(draw.EMSGID_eBroadcastDrawTimeout, action, players)

	case draw.EMSGID_eBroadcastDrawRecall:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(draw.EMSGID_eBroadcastDrawRecall, action, players)

	case draw.EMSGID_eBroadcastDrawRoundStart:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(draw.EMSGID_eBroadcastDrawRoundStart, action, players)

	case draw.EMSGID_eBroadcastDrawRoundEnd:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(draw.EMSGID_eBroadcastDrawRoundEnd, action, players)

	case banker.ActionBankerStart:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(banker.ActionBankerStart, action, players)

	case probability.EMSGID_eBroadcastResult:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(probability.EMSGID_eBroadcastResult, action, players)

	case bet.EMSGID_eBetRoundStart:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(bet.EMSGID_eBetRoundStart, action, players)

	case bet.EMSGID_eBetRoundEnd:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(bet.EMSGID_eBetRoundEnd, action, players)

	case bet.EMSGID_eBroadcastBetTimeout:
		g.rwMutex.RLock()
		defer g.rwMutex.RUnlock()

		g.broadcastAction(bet.EMSGID_eBroadcastBetTimeout, action, players)

	case waitingroom.EMSGID_eWaitingCountdown:
		g.rwMutex.Lock()
		defer g.rwMutex.Unlock()

		g.isGaming = false

		g.broadcastAction(waitingroom.EMSGID_eWaitingCountdown, action, players)
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

	l := gamesetting89.Service.BalanceLimit(secWebSocketKey)

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

		// TODO JOHNNY 目前沒有搶莊寫死
		if j.Seat == banker.BANKER_SEAT {
			// TODO JOHNNY 這裡直接發送搶到莊家

			flux.Send(banker.ActionBankerCreate, g.uuid, banker.Service.Id,
				j.SecWebSocketKey,
				j.GameRoomUuid,
				banker.GAME_ROOM,
				j.Seat,
				int32(6), // 一桌6人
			)
		}

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
