package gamesetting52

import (
	game_setting52_proto "52-game-server/application/gamesetting52/proto"
	"strconv"
	"strings"
	"sync"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/auth"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	game_setting_proto "gitlab.iplaystar.net/game-server/game-setting/proto"
	"gitlab.iplaystar.net/game-server/idle"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/session"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

var Service = &service{
	Id:                "GameSetting52Service",
	allSelected52Game: make(map[string]*selected52Game),
	rwMutex:           &sync.RWMutex{},
}

type service struct {
	Id                string
	allSelected52Game map[string]*selected52Game
	rwMutex           *sync.RWMutex
}

func (s *service) EMSGID_eGameConfigCallHandler(memberId string, guestEnable int, gs *gamesetting.GameSetting, cc *game_setting_proto.ConfigCall) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	st52 := s.parseGameSetting(cc.GameId, cc.SubgameId, gs)

	if st52 == nil {
		gs.SelectedGame = nil
		return
	}

	cent, err := wallet.Service.Cent(gs.SecWebSocketKey)

	if err != nil {
		gs.SelectedGame = nil
		logger.Service.Zap.Errorw(GameSetting52_GET_CENT_FAILED,
			"GameUser", gs.SecWebSocketKey,
			"MemberId", memberId,
			"CentLimit", st52.balanceLimit,
			"Cent", cent,
			"Error", err,
		)
		errorcode.Service.Fatal(gs.SecWebSocketKey, GameSetting52_GET_CENT_FAILED)
		return
	}

	if cent < uint64(st52.balanceLimit) {
		gs.SelectedGame = nil
		logger.Service.Zap.Warnw(GameSetting52_NOT_ENOUGH_BALANCE,
			"GameUser", gs.SecWebSocketKey,
			"MemberId", memberId,
			"CentLimit", st52.balanceLimit,
			"Cent", cent,
		)
		return
	}

	s.allSelected52Game[gs.SecWebSocketKey] = st52

	gs.SelectedGame = st52

	session.Service.New(
		gs.SecWebSocketKey,
		gs.HostExtId,
		st52.hostId,
		memberId,
		st52.gameId,
		cc.SubgameId,
		gs.RemoteAddr,
		gs.UserAgent,
		cc.Version,
		cc.GameVersion,
	)

	if guestEnable == auth.GuestOff {
		sessionmanager.Service.Start(
			gs.SecWebSocketKey,
			gs.HostExtId,
			st52.hostId,
			memberId,
			st52.gameId,
		)
	}

	flux.Send(idle.ActionIdleTimeoutStart, s.Id, idle.Service.Id,
		gs.SecWebSocketKey,
		st52.sessionTimeout,
	)
}

func (s *service) parseGameSetting(gameId string, subGameId uint32, gs *gamesetting.GameSetting) *selected52Game {
	if game, ok := gs.AvailableGames[gameId].(*host52Game); ok {
		atoiBalance, _ := strconv.Atoi(strings.Split(game.BalanceLimit, ",")[subGameId])
		atoiBet, _ := strconv.Atoi(strings.Split(game.BetList, ",")[subGameId])
		atoiAutoBlacklistValue, _ := strconv.Atoi(strings.Split(game.AutoBlacklistValue, ",")[subGameId%6])
		atoiRoundCount, _ := strconv.Atoi(strings.Split(game.BlacklistRoundCount, ",")[subGameId%6])
		atoiTriggerCount, _ := strconv.Atoi(strings.Split(game.BlacklistTriggerCount, ",")[subGameId%6])

		st52 := &selected52Game{
			hostId:                game.HostId,
			gameId:                game.GameId,
			subGameId:             subGameId,
			betList:               game.BetList, // for game room id used
			rateIndex:             subGameId,
			bet:                   uint32(atoiBet),
			langs:                 nil,
			balanceLimit:          uint32(atoiBalance),
			sessionTimeout:        game.SessionTimeout,
			ipConfig:              game.IpConfig,
			roomConfig:            game.RoomConfig,
			bankerConfig:          game.BankerConfig,
			hostConnectConfig:     game.HostConnectConfig,
			fee:                   game.Fee,
			idBlockPercent:        game.IdBlockPercent,
			autoBlacklistValue:    uint64(atoiAutoBlacklistValue),
			blacklistRoundCount:   uint32(atoiRoundCount),
			blacklistTriggerCount: uint32(atoiTriggerCount),
		}

		for _, v := range strings.Split(game.Langs, ",") {
			st52.langs = append(st52.langs, v)
		}

		for _, time := range strings.Split(game.WaitingTime, ",") {
			atoiTime, _ := strconv.Atoi(time)
			st52.waitingTime = append(st52.waitingTime, uint32(atoiTime))
		}
		sid := subGameId % 6
		st52.waitingTime = st52.waitingTime[sid*4 : sid*4+4]

		for _, id := range strings.Split(game.MathId, ",") {
			atoiId, _ := strconv.Atoi(id)
			st52.mathModuleId = append(st52.mathModuleId, atoiId)
		}
		st52.mathModuleId = st52.mathModuleId[sid*12 : sid*12+12]

		for _, credit := range strings.Split(game.TransferCredit, ",") {
			atoiCredit, _ := strconv.Atoi(credit)
			st52.transferCredit = append(st52.transferCredit, uint32(atoiCredit))
		}

		rates := strings.Split(game.UnluckyRate, ",")
		r, _ := strconv.Atoi(rates[sid])
		vipr, _ := strconv.Atoi(rates[subGameId%6+6])
		st52.UnluckyRate = []int{r, vipr}

		st52.blacklistCondition, _ = strconv.Atoi(strings.Split(game.BlacklistCondition, ",")[sid])
		st52.isolateRate, _ = strconv.Atoi(strings.Split(game.IsolateRate, ",")[sid])

		return st52
	} else {
		logger.Service.Zap.Errorw(gamesetting.GameSetting_GAME_SETTING_NOT_FOUND,
			"GameUser", gs.SecWebSocketKey,
			"gameId", gameId,
			"SubGameId", subGameId,
		)
		errorcode.Service.Fatal(gs.SecWebSocketKey, gamesetting.GameSetting_GAME_SETTING_NOT_FOUND)
		return nil
	}
}

func (s *service) EMSGID_eGameConfigRecallHandler(gs *gamesetting.GameSetting, subGameId uint32, isTokenValid bool) []byte {
	data := &game_setting52_proto.ConfigRecall{
		Msgid:                 common_proto.EMSGID_eGameConfigRecall,
		LanguagesDefaultIndex: 0,
	}

	if !isTokenValid {
		s.cleanData(gs.SecWebSocketKey, auth.Auth_TOKEN_EXPIRED)
		data.StatusCode = common_proto.Status_kInvalid
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	if !wallet.Service.Existed(gs.SecWebSocketKey) {
		s.cleanData(gs.SecWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)
		data.StatusCode = common_proto.Status_kInvalid
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	if gs.SelectedGame == nil {
		logger.Service.Zap.Warnw(GameSetting52_NOT_ENOUGH_BALANCE,
			"GameUser", gs.SecWebSocketKey)

		data.StatusCode = common_proto.Status_kNoEnoughCredit
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	go session.Service.Start(gs.SecWebSocketKey)

	data.StatusCode = common_proto.Status_kSuccess

	st52 := gs.SelectedGame.(*selected52Game)

	data.WaitingTime = st52.waitingTime

	data.TransferCredit = st52.transferCredit

	data.Languages = st52.langs

	data.Line = []uint32{1}

	data.Bet = st52.bet

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (s *service) EMSGID_eGameStripsRecallHandler(gs *gamesetting.GameSetting, isTokenValid bool) []byte {
	// do nothing now
	return nil
}

func (s *service) cleanData(secWebSocketKey, errorCode string) {
	logger.Service.Zap.Errorw(errorCode,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, errorCode)
}

func (s *service) Clone(secWebSocketKey, uuid string) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if data, ok := s.allSelected52Game[secWebSocketKey]; ok {
		s.allSelected52Game[uuid] = data
	} else {
		logger.Service.Zap.Errorw(gamesetting.GameSetting_CLONE_FAILED,
			"GameUser", secWebSocketKey,
			"UUID", uuid,
		)
		errorcode.Service.Fatal(uuid, gamesetting.GameSetting_CLONE_FAILED)
	}
}

func (s *service) GameId(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.gameId
	}

	logger.Service.Zap.Errorw(GameSetting52_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)

	errorcode.Service.Fatal(secWebSocketKey, GameSetting52_GAME_ID_NOT_FOUND)

	return ""
}

func (s *service) MathModuleId(secWebSocketKey string) []int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.mathModuleId
	}

	// TODO JOHNNY ERROR CODE

	return []int{80, 60, 25, 15, 24, 14, 90, 70, 25, 15, 24, 14}
}

func (s *service) BetList(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.betList
	}

	// TODO JOHNNY ERROR CODE

	return ""
}

func (s *service) BalanceLimit(secWebSocketKey string) (balanceLimit uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.balanceLimit
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) FirstRoundStartWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.waitingTime[0]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) DrawCardsWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.waitingTime[1]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) PlayCardsWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.waitingTime[2]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) RoundStartWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.waitingTime[3]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) Idle(secWebSocketKey string) (sessionTimeout uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.sessionTimeout
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) IPConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.ipConfig
	}

	// TODO JOHNNY ERROR CODE

	return 0
}
func (s *service) HostConnectConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.hostConnectConfig
	}

	// TODO JOHNNY ERROR CODE

	return 0
}
func (s *service) Fee(secWebSocketKey string) uint32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		if v.fee <= 50 && v.fee > 0 {
			return v.fee
		} else {
			return 5
		}
	}

	// TODO JOHNNY ERROR CODE

	return 5
}

func (s *service) SubGameId(secWebSocketKey string) int32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return int32(v.subGameId)
	}

	logger.Service.Zap.Errorw(GameSetting52_SUB_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)

	errorcode.Service.Fatal(secWebSocketKey, GameSetting52_SUB_GAME_ID_NOT_FOUND)

	return -1
}

func (s *service) IdBlockPercent(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		if v.idBlockPercent <= 100 && v.idBlockPercent >= 0 {
			return v.idBlockPercent
		} else {
			return 0
		}
	}

	return 0
}

func (s *service) HostId(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.hostId
	}
	return ""
}

func (s *service) Bet(secWebSocketKey string) uint32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.bet
	}
	return 0
}

func (s *service) UnluckyRate(secWebSocketKey string, isVip bool) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		if isVip {
			return v.UnluckyRate[1]
		} else {
			return v.UnluckyRate[0]
		}
	}
	return 0
}

func (s *service) BlacklistCondition(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.blacklistCondition
	}

	return 0
}

func (s *service) IsolateRate(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.isolateRate
	}

	return 0
}

func (s *service) AutoBlacklistValue(secWebSocketKey string) uint64 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.autoBlacklistValue
	}

	return 0
}

func (s *service) BlacklistRoundCount(secWebSocketKey string) uint32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.blacklistRoundCount
	}
	return 0
}

func (s *service) BlacklistTriggerCount(secWebSocketKey string) uint32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected52Game[secWebSocketKey]; ok {
		return v.blacklistTriggerCount
	}
	return 0
}
