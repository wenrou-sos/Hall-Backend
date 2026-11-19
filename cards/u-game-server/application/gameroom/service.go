package gameroom

import (
	"crypto/sha1"
	"fmt"
	"strconv"
	"u-game-server/application/gamesettingU"

	"github.com/google/uuid"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	PLAYER                    = "PLAYER"
	BOT                       = "BOT"
	ActionGameRoomJoinCall    = "ActionGameRoomJoinCall"
	ActionGameRoomJoinRecall  = "ActionGameRoomJoinRecall"
	ActionGameRoomLeaveCall   = "ActionGameRoomLeaveCall"
	ActionGameRoomLeaveRecall = "ActionGameRoomLeaveRecall"
	ActionGameRoomCreated     = "ActionGameRoomCreated"
)

var Service = &service{
	Id:       "GameRoomService",
	roomSize: 6,
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
						logger.Service.Zap.Infow("Join Existed Game Room",
							"GameUser", j.SecWebSocketKey,
							"GameRoomUuid", g.uuid,
							"GameId", j.gameId,
							"SeatId", j.Seat,
							"Bet", j.bet,
							"AllGameRooms", len(allGameRooms),
						)
					}
				}
			}

			if !isJoined {
				flux.Send(ActionGameRoomJoinRecall, s.Id, j.controllerId, j)
			}

		case PLAYER:
			count := 0

			if j.blacklistValue == 0 && !j.isIsolated {
				for gameRoomUuid, g := range allGameRooms {
					count++

					//if g.hashId() == j.hashId() {
					if s.isMatch(g, j) {
						flux.Send(actionCheckVacancy, s.Id, gameRoomUuid, PLAYER, j)

						if <-g.isVacancy {
							flux.Send(actionPlayerAddCall, s.Id, gameRoomUuid, j)

							if <-g.isJoined {
								logger.Service.Zap.Infow("Join Existed Game Room",
									"GameUser", j.SecWebSocketKey,
									"GameRoomUuid", gameRoomUuid,
									"GameId", j.gameId,
									"SeatId", j.Seat,
									"Bet", j.bet,
									"AllGameRooms", len(allGameRooms),
								)
								break
							}
						}
					}
					// all rooms full
					if count >= len(allGameRooms) {
						r := s.createRoom(j)
						allGameRooms[r.uuid] = r
						break
					}
				}
			}

			// first game room or blacklist
			if len(allGameRooms) == 0 || j.blacklistValue > 0 || j.isIsolated {
				r := s.createRoom(j)
				allGameRooms[r.uuid] = r
			}

			logger.Service.Zap.Infow("All Game Rooms",
				"GameUser", j.SecWebSocketKey,
				"AllGameRooms", len(allGameRooms),
			)
		}

	case actionPlayerAddRecall:
		j := action.Payload()[0].(*Join)

		flux.Send(ActionGameRoomJoinRecall, s.Id, j.controllerId, j)

	case ActionGameRoomLeaveCall:
		l := action.Payload()[0].(*Leave)
		flux.Send(ActionPlayerDeleteCall, s.Id, l.GameRoomUuid, l)

	case actionPlayerDeleteRecall:
		l := action.Payload()[0].(*Leave)

		flux.Send(ActionGameRoomLeaveRecall, s.Id, l.controllerId, l)

	case actionDestroy:
		gameRoomUuid := action.Key().From()
		delete(allGameRooms, gameRoomUuid)
	}
}

func (s *service) createRoom(j *Join) *gameRoom {
	g := Builder().
		setUuid(uuid.New().String()).
		setControllerId(j.controllerId).
		setSecWebSocketKey(j.SecWebSocketKey).
		setRoomSize(s.roomSize).
		setGameId(j.gameId).
		setBet(j.bet).
		setHostExtId(j.HostExtId).
		setIPBlock(j.IPBlock).
		setHostBlock(j.HostBlock).
		setRoundTime(gamesettingU.Service.GameRoundWaitingTime(j.SecWebSocketKey)).
		setPredictTime(gamesettingU.Service.PredictTime(j.SecWebSocketKey)).
		setBlacklistValue(j.blacklistValue).
		setFee(j.fee).
		setMemberType(j.memberType).
		setIsIsolated(j.isIsolated).
		setFirstRoundStartWaitingTime(gamesettingU.Service.FirstRoundStartWaitingTime(j.SecWebSocketKey)).
		setRoundStartWaitingTime(gamesettingU.Service.RoundStartWaitingTime(j.SecWebSocketKey)).
		build()

	if <-g.isReady {
		flux.Send(ActionGameRoomCreated, s.Id, j.controllerId, j)
		flux.Send(actionPlayerAddCall, s.Id, g.uuid, j)

		if <-g.isJoined {
			logger.Service.Zap.Infow("Join New Game Room",
				"GameUser", j.SecWebSocketKey,
				"GameRoomUuid", g.uuid,
				"GameId", j.gameId,
				"Bet", j.bet,
			)
		}
	}
	return g
}

func (s *service) hashId(gameId string, bet uint64) string {
	return fmt.Sprintf("%x", sha1.Sum([]byte(gameId+strconv.FormatUint(bet, 10))))
}

func (s *service) isMatch(gameRoom *gameRoom, joinRoom *Join) bool {
	ok := gameRoom.bet == joinRoom.bet && gameRoom.fee == joinRoom.fee && gameRoom.memberType == joinRoom.memberType
	if ok {
		g_time1 := gamesettingU.Service.FirstRoundStartWaitingTime(gameRoom.secWebSocketKey)
		g_time2 := gamesettingU.Service.PlayerRoundWaitingTime(gameRoom.secWebSocketKey)
		g_time3 := gamesettingU.Service.GameRoundWaitingTime(gameRoom.secWebSocketKey)
		g_time4 := gamesettingU.Service.RoundStartWaitingTime(gameRoom.secWebSocketKey)
		g_time5 := gamesettingU.Service.PredictTime(gameRoom.secWebSocketKey)
		g_time6 := gamesettingU.Service.BotLogicTime(gameRoom.secWebSocketKey)
		j_time1 := gamesettingU.Service.FirstRoundStartWaitingTime(joinRoom.SecWebSocketKey)
		j_time2 := gamesettingU.Service.PlayerRoundWaitingTime(joinRoom.SecWebSocketKey)
		j_time3 := gamesettingU.Service.GameRoundWaitingTime(joinRoom.SecWebSocketKey)
		j_time4 := gamesettingU.Service.RoundStartWaitingTime(joinRoom.SecWebSocketKey)
		j_time5 := gamesettingU.Service.PredictTime(joinRoom.SecWebSocketKey)
		j_time6 := gamesettingU.Service.BotLogicTime(joinRoom.SecWebSocketKey)
		ok = g_time1 == j_time1 && g_time2 == j_time2 && g_time3 == j_time3 && g_time4 == j_time4 && g_time5 == j_time5 && g_time6 == j_time6
	}
	return ok
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
