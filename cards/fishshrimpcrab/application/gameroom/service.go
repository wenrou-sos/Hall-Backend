package gameroom

import (
	"crypto/rand"
	"crypto/sha1"
	"fish-shrimp-crab-game-server/application/botuser"
	"fish-shrimp-crab-game-server/application/gamesettingFS"
	"fish-shrimp-crab-game-server/application/lobbysettingFS"
	"fish-shrimp-crab-game-server/domain/probability"
	"fish-shrimp-crab-game-server/domain/vip"
	"fmt"
	"math/big"
	"strconv"
	"time"

	"github.com/google/uuid"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/player"
)

const (
	PLAYER                   = "PLAYER"
	BOT                      = "BOT"
	ActionGameRoomJoinCall   = "ActionGameRoomJoinCall"
	ActionGameRoomJoinRecall = "ActionGameRoomJoinRecall"
	ActionGameRoomLeaveCall  = "ActionGameRoomLeaveCall"
	ActionGameRoomCreated    = "ActionGameRoomCreated"
	actionCreateBotRoom      = "actionCreateBotRoom"
	actionAddRoom            = "actionAddRoom"
	PlayerIsReconnected      = "PlayerIsReconnected"
	ActionVipSetting         = "ActionVipSetting"
)

var Service = &service{
	Id:       "GameRoomService",
	roomSize: 11,
	in:       make(chan *flux.Action, common.Service.ChanSize),
}

type service struct {
	Id       string
	roomSize int
	in       chan *flux.Action
}

func init() {
	go Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	allGameRooms := make(map[string]*gameRoom)

	for action := range s.in {
		s.handleAction(action, allGameRooms)
	}
}

func (s *service) handleAction(action *flux.Action, allGameRooms map[string]*gameRoom) {
	switch action.Key().Name() {
	case ActionGameRoomJoinCall:
		j := action.Payload()[0].(*Join)
		switch j.Kind {
		case BOT:
			isJoined := false

			if g, ok := allGameRooms[j.GameRoomUuid]; ok {
				flux.Send(actionCheckVacancy, s.Id, g.uuid, BOT, j)

				if <-g.isVacancy {
					flux.Send(actionPlayerAddCall, s.Id, g.uuid, j)

					if <-g.isJoined {
						isJoined = true
					}
				}
			}

			if isJoined {
				flux.Send(ActionGameRoomJoinRecall, s.Id, j.controllerId, j)
			}

		case PLAYER:
			if vipLevel := vip.Service.CheckVip(
                false,
                j.SecWebSocketKey,
                j.HostExtId,
                j.vipInfo.hostId,
                j.vipInfo.memberId,
                j.vipInfo.gameid,
                j.vipInfo.billCurrency,
                0,
                0,
                0,
            ); vipLevel != 0 {
                r := s.createVipRoom(j, vipLevel)
                allGameRooms[r.uuid] = r
                return
            }

			isJoined := false

			for gameRoomUuid, room := range allGameRooms {
				if room.rate == j.rate && room.kind == GAME_ROOM {
					flux.Send(actionCheckVacancy, s.Id, gameRoomUuid, PLAYER, j)
					if <-room.isVacancy && room.uuid != j.lastRoomId { //有空房而且不跟上局房相同
						flux.Send(actionPlayerAddCall, s.Id, gameRoomUuid, j)

						isJoined = true

						logger.Service.Zap.Infow("Join Existed GAME_ROOM",
							"GameUser", j.SecWebSocketKey,
							"GameRoomUuid", gameRoomUuid,
							"GameId", j.gameId,
							"SeatId", j.Seat,
							"BetList", j.betList,
							"RateList", j.rateList,
							"Rate", j.rate,
							"AllGameRooms", len(allGameRooms),
						)
						break
					}
				}
			}

			if !isJoined {
				for gameRoomUuid, room := range allGameRooms {
					if room.rate == j.rate && room.kind == BOT_ROOM {
						flux.Send(actionCheckVacancy, s.Id, gameRoomUuid, PLAYER, j)

						if <-room.isVacancy {
							flux.Send(actionPlayerAddCall, s.Id, gameRoomUuid, j)
							isJoined = true
							logger.Service.Zap.Infow("Join Existed BOT_ROOM",
								"GameUser", j.SecWebSocketKey,
								"GameRoomUuid", gameRoomUuid,
								"GameId", j.gameId,
								"SeatId", j.Seat,
								"BetList", j.betList,
								"RateList", j.rateList,
								"Rate", j.rate,
								"AllGameRooms", len(allGameRooms),
							)
							flux.Send(actionCreateBotRoom, Service.Id, Service.Id, j)
							break
						}
					}
				}
			}

			if !isJoined {
				r := s.createRoom(j)
				allGameRooms[r.uuid] = r
			}

		}

	case actionCreateBotRoom:
		j := action.Payload()[0].(*Join)
		logger.Service.Zap.Infow("create new BOT_ROOM", "player", j.SecWebSocketKey)

		fakeHistory := [10][3]int32{}
		for i := range fakeHistory {
			fakeHistory[i] = probability.Service.Roll()
		}

		lobbySetting := lobbysettingFS.Service.BotDefaultLobbySetting(j.HostExtId, j.gameId)
		botRoom := s.createBotRoom(
			j.rateIndex,
			j.rate,
			player.Controller.Id,
			lobbySetting,
			fakeHistory,
			j.HostExtId,
		)

		//botNums, _ := strconv.Atoi(os.Getenv("BOTROOM_BOT_NUM"))
		botNums := lobbySetting.GetBotNumPerRoom()
		for i := 0; i < botNums; i++ {
			flux.Send(botuser.ActionBotUserCreate, player.Controller.Id, botuser.Service.Id,
				botRoom.uuid,
				botRoom.rate,
				j.rateIndex,
				"",
				botRoom.betList,
			)
			time.Sleep(500 * time.Microsecond)
		}

		logger.Service.Zap.Infow("new BOT_ROOM start", "player", j.SecWebSocketKey, "room uuid", botRoom.uuid)
		flux.Send(ActionGameRoundStart, s.Id, botRoom.uuid, botRoom.uuid)

		allGameRooms[botRoom.uuid] = botRoom

	case actionPlayerAddRecall:
		j := action.Payload()[0].(*Join)

		flux.Send(ActionGameRoomJoinRecall, s.Id, j.controllerId, j)

	case ActionGameRoomLeaveCall:
		l := action.Payload()[0].(*Leave)
		flux.Send(ActionPlayerDeleteCall, s.Id, l.GameRoomUuid, l)

	case actionAddRoom:
		room := action.Payload()[0].(*gameRoom)
		allGameRooms[room.uuid] = room

	case actionDestroy:
		gameRoomUuid := action.Key().From()
		delete(allGameRooms, gameRoomUuid)

	case PlayerIsReconnected:
		newWebSocketKey := action.Key().From()
		betRoundUuid := action.Payload()[0].(string)
		memberId := action.Payload()[1].(string)

		for gameRoomUuid, room := range allGameRooms {
			if room.betRoundUuid == betRoundUuid {
				logger.Service.Zap.Infow("發生玩家還在遊戲中，斷線重回房", "新Socket", newWebSocketKey)
				flux.Send(PlayerIsReconnected, s.Id, gameRoomUuid, newWebSocketKey, memberId)
				break
			}
		}
	}
}

func (s *service) CreateBotRooms(rateIndex int, fakeWebSocketKey, hostExtId, gameId string) {
	lobbyConfig := lobbysettingFS.Service.BotDefaultLobbySetting(hostExtId, gameId)

	fakeHistory := [10][3]int32{}
	for i := range fakeHistory {
		fakeHistory[i] = probability.Service.Roll()
	}

	//botRoomNums, _ := strconv.Atoi(os.Getenv("BOTROOM_ROOM_NUM"))
	//botNums, _ := strconv.Atoi(os.Getenv("BOTROOM_BOT_NUM"))
	botRoomNums := lobbyConfig.GetRoomNum()
	botNums := lobbyConfig.GetBotNumPerRoom()
	for i := 0; i < botRoomNums; i++ {
		g := s.createBotRoom(rateIndex, gamesettingFS.Service.Rate(fakeWebSocketKey), player.Controller.Id, lobbyConfig, fakeHistory, hostExtId)

		flux.Send(actionAddRoom, Service.Id, Service.Id, g)

		for i := 0; i < botNums; i++ {
			flux.Send(botuser.ActionBotUserCreate, player.Controller.Id, botuser.Service.Id,
				g.uuid,
				g.rate,
				g.rateIndex,
				"",
				g.betList,
			)
			time.Sleep(500 * time.Microsecond)
		}
		time.Sleep(500 * time.Microsecond)

		if <-g.isReady {
			flux.Send(ActionGameRoundStart, s.Id, g.uuid, g.uuid)
		}
	}
}

func (s *service) createBotRoom(rateIndex int, rate uint32, controllerId string, lobbyConfig *lobbysettingFS.HostFSGame, fakeHistory [10][3]int32, hostExtId string) *gameRoom {
	g := Builder().
		setUuid(uuid.New().String()).
		setControllerId(controllerId).
		setRoomSize(s.roomSize).
		setGameId(lobbyConfig.GameId).
		setBetList(lobbyConfig.RateList).
		setRate(rate).
		setRateIndex(rateIndex).
		setRateList(lobbyConfig.RateList).
		setKind(BOT_ROOM).
		setHostExtId(hostExtId).
		setHostBlock(lobbyConfig.HostConnectConfig).
		setHistory(fakeHistory).
		setIPBlock(lobbyConfig.IpConfig).
		build()

	return g
}

func (s *service) createRoom(j *Join) *gameRoom {
	fakeHistory := [10][3]int32{}
	for i := range fakeHistory {
		fakeHistory[i] = probability.Service.Roll()
	}

	g := Builder().
		setUuid(uuid.New().String()).
		setControllerId(j.controllerId).
		setRoomSize(s.roomSize).
		setGameId(j.gameId).
		setBetList(j.betList).
		setRateList(j.rateList).
		setRateIndex(j.rateIndex).
		setRate(j.rate).
		setHostExtId(j.HostExtId).
		setIPBlock(j.IPBlock).
		setHostBlock(j.HostBlock).
		setKind(BOT_ROOM).
		setHistory(fakeHistory).
		SetVipInfo(j.SecWebSocketKey, 0, j.lastRoomId, j.vipInfo.isVipChangeRoom).
        build()

    if <-g.isReady {

        botNum := 0
        if n, err := rand.Int(rand.Reader, big.NewInt(100)); err == nil {
            if n.Uint64() < 5 {
                botNum = 8
            } else if n.Uint64() < 10 {
                botNum = 7
            } else if n.Uint64() < 20 {
                botNum = 6
            } else if n.Uint64() < 30 {
                botNum = 5
            } else if n.Uint64() < 40 {
                botNum = 4
            } else if n.Uint64() < 50 {
                botNum = 3
            } else if n.Uint64() < 60 {
                botNum = 2
            } else if n.Uint64() < 70 {
                botNum = 1
            }
        }

        for i := 0; i < botNum; i++ {
            flux.Send(botuser.ActionBotUserCreate, player.Controller.Id, botuser.Service.Id,
                g.uuid,
                g.rate,
                g.rateIndex,
                "",
                g.betList,
            )
        }

        flux.Send(ActionGameRoomCreated, s.Id, j.controllerId, j)
        flux.Send(actionPlayerAddCall, s.Id, g.uuid, j)

        if <-g.isJoined {
            logger.Service.Zap.Infow("Join New Game Room",
                "GameUser", j.SecWebSocketKey,
                "GameRoomUuid", g.uuid,
                "GameId", j.gameId,
                "BetList", j.betList,
                "RateList", j.rateList,
                "Rate", j.rate,
                "Seat", j.Seat,
            )
            flux.Send(ActionGameRoundStart, s.Id, g.uuid, g.uuid)
        }
    }
    return g
}

func (s *service) createVipRoom(j *Join, level uint32) *gameRoom {
    History := [10][3]int32{}
    //從GAME_ROOM -> VIP_ROOM
    if j.vipInfo.isVipChangeRoom && j.lastRoomId != "" {
        History = j.vipInfo.histories
    } else {
        for i := range History {
            History[i] = probability.Service.Roll()
        }
    }
    
    g := Builder().
        setUuid(uuid.New().String()).
        setControllerId(j.controllerId).
        setRoomSize(s.roomSize).
        setGameId(j.gameId).
        setBetList(j.betList).
        setRateList(j.rateList).
        setRateIndex(j.rateIndex).
        setRate(j.rate).
        setHostExtId(j.HostExtId).
        setIPBlock(j.IPBlock).
        setHostBlock(j.HostBlock).
        setKind(VIP_ROOM).
        setHistory(History).
        SetVipInfo(j.SecWebSocketKey, level, j.lastRoomId, j.vipInfo.isVipChangeRoom).
		build()

	if <-g.isReady {

		botNum := 0
		if n, err := rand.Int(rand.Reader, big.NewInt(100)); err == nil {
			if n.Uint64() < 5 {
				botNum = 8
			} else if n.Uint64() < 10 {
				botNum = 7
			} else if n.Uint64() < 20 {
				botNum = 6
			} else if n.Uint64() < 30 {
				botNum = 5
			} else if n.Uint64() < 40 {
				botNum = 4
			} else if n.Uint64() < 50 {
				botNum = 3
			} else if n.Uint64() < 60 {
				botNum = 2
			} else if n.Uint64() < 70 {
				botNum = 1
			}
		}

		for i := 0; i < botNum; i++ {
			flux.Send(botuser.ActionBotUserCreate, player.Controller.Id, botuser.Service.Id,
				g.uuid,
				g.rate,
				g.rateIndex,
				"",
				g.betList,
			)
		}

		flux.Send(ActionGameRoomCreated, s.Id, j.controllerId, j)
		flux.Send(actionPlayerAddCall, s.Id, g.uuid, j)

		if <-g.isJoined {
			logger.Service.Zap.Infow("Join New Game Room",
				"GameUser", j.SecWebSocketKey,
				"GameRoomUuid", g.uuid,
				"GameId", j.gameId,
				"BetList", j.betList,
				"RateList", j.rateList,
				"Rate", j.rate,
				"Seat", j.Seat,
			)
			flux.Send(ActionGameRoundStart, s.Id, g.uuid, g.uuid)
		}
	}
	return g
}

func (s *service) hashId(gameId, betList, rateList string, rate uint32) string {
	return fmt.Sprintf("%x", sha1.Sum([]byte(gameId+betList+rateList+strconv.FormatUint(uint64(rate), 10))))
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
