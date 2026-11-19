package gameroom

import (
	"crypto/sha1"
	"fmt"
	"strconv"

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
							"BetList", j.betList,
							"RateList", j.rateList,
							"Rate", j.rate,
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

			for gameRoomUuid, g := range allGameRooms {
				count++

				if g.hashId() == j.hashId() {
					flux.Send(actionCheckVacancy, s.Id, gameRoomUuid, PLAYER, j)

					if <-g.isVacancy {
						flux.Send(actionPlayerAddCall, s.Id, gameRoomUuid, j)

						if <-g.isJoined {
							logger.Service.Zap.Infow("Join Existed Game Room",
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
				// all rooms full
				if count >= len(allGameRooms) {
					r := s.createRoom(j)
					allGameRooms[r.uuid] = r
					break
				}
			}

			// first game room
			if len(allGameRooms) == 0 {
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
		setRoomSize(s.roomSize).
		setGameId(j.gameId).
		setBetList(j.betList).
		setRateList(j.rateList).
		setRate(j.rate).
		setHostExtId(j.HostExtId).
		setIPBlock(j.IPBlock).
		setHostBlock(j.HostBlock).
		build()

	if <-g.isReady {
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
			)
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
