package gamesetting89

import (
	game_setting89_proto "89-game-server/application/gamesetting89/proto"
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
	Id:                "GameSetting89Service",
	allSelected89Game: make(map[string]*selected89Game),
	rwMutex:           &sync.RWMutex{},
}

type service struct {
	Id                string
	allSelected89Game map[string]*selected89Game
	rwMutex           *sync.RWMutex
}

func (s *service) EMSGID_eGameConfigCallHandler(memberId string, guestEnable int, gs *gamesetting.GameSetting, cc *game_setting_proto.ConfigCall) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	st89 := s.parseGameSetting(cc.GameId, cc.SubgameId, gs)

	if st89 == nil {
		gs.SelectedGame = nil
		return
	}

	cent, err := wallet.Service.Cent(gs.SecWebSocketKey)

	if err != nil {
		gs.SelectedGame = nil
		logger.Service.Zap.Errorw(GameSetting89_GET_CENT_FAILED,
			"GameUser", gs.SecWebSocketKey,
			"MemberId", memberId,
			"CentLimit", st89.balanceLimit,
			"Cent", cent,
			"Error", err,
		)
		errorcode.Service.Fatal(gs.SecWebSocketKey, GameSetting89_GET_CENT_FAILED)
		return
	}

	if cent < uint64(st89.balanceLimit) {
		gs.SelectedGame = nil
		logger.Service.Zap.Warnw(GameSetting89_NOT_ENOUGH_BALANCE,
			"GameUser", gs.SecWebSocketKey,
			"MemberId", memberId,
			"CentLimit", st89.balanceLimit,
			"Cent", cent,
		)
		return
	}

	s.allSelected89Game[gs.SecWebSocketKey] = st89

	gs.SelectedGame = st89

	session.Service.New(
		gs.SecWebSocketKey,
		gs.HostExtId,
		st89.hostId,
		memberId,
		st89.gameId,
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
			st89.hostId,
			memberId,
			st89.gameId,
		)
	}

	flux.Send(idle.ActionIdleTimeoutStart, s.Id, idle.Service.Id,
		gs.SecWebSocketKey,
		st89.sessionTimeout,
	)
}

func (s *service) parseGameSetting(gameId string, subGameId uint32, gs *gamesetting.GameSetting) *selected89Game {
	if game, ok := gs.AvailableGames[gameId].(*host89Game); ok {
		atoiRate, _ := strconv.Atoi(strings.Split(game.RateList, ",")[subGameId])
		atoiBalance, _ := strconv.Atoi(strings.Split(game.BalanceLimit, ",")[subGameId])
		atoiBanker, _ := strconv.Atoi(strings.Split(game.BankerLimit, ",")[subGameId])

		st89 := &selected89Game{
			hostId:            game.HostId,
			gameId:            game.GameId,
			mathModuleId:      game.MathId,
			betList:           game.BetList,  // for game room id used
			rateList:          game.RateList, // for game room id used
			rateIndex:         subGameId,
			rate:              []uint32{uint32(atoiRate)},
			bets:              [1][]uint32{},
			langs:             nil,
			balanceLimit:      uint32(atoiBalance * atoiRate),
			bankerLimit:       uint32(atoiBanker * atoiRate),
			sessionTimeout:    game.SessionTimeout,
			ipConfig:          game.IpConfig,
			roomConfig:        game.RoomConfig,
			bankerConfig:      game.BankerConfig,
			hostConnectConfig: game.HostConnectConfig,
		}

		for _, bet := range strings.Split(game.BetList, ",") {
			atoiBet, _ := strconv.Atoi(bet)
			st89.bets[0] = append(st89.bets[0], uint32(atoiBet))
		}

		for _, v := range strings.Split(game.Langs, ",") {
			st89.langs = append(st89.langs, v)
		}

		for _, time := range strings.Split(game.WaitingTime, ",") {
			atoiTime, _ := strconv.Atoi(time)
			st89.waitingTime = append(st89.waitingTime, uint32(atoiTime))
		}

		for _, credit := range strings.Split(game.TransferCredit, ",") {
			atoiCredit, _ := strconv.Atoi(credit)
			st89.transferCredit = append(st89.transferCredit, uint32(atoiCredit))
		}

		return st89
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
	data := &game_setting89_proto.ConfigRecall{
		Msgid:                 common_proto.EMSGID_eGameConfigRecall,
		RatesDefaultIndex:     subGameId,
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
		logger.Service.Zap.Warnw(GameSetting89_NOT_ENOUGH_BALANCE,
			"GameUser", gs.SecWebSocketKey)

		data.StatusCode = common_proto.Status_kNoEnoughCredit
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	go session.Service.Start(gs.SecWebSocketKey)

	data.StatusCode = common_proto.Status_kSuccess

	st89 := gs.SelectedGame.(*selected89Game)

	data.WaitingTime = st89.waitingTime

	data.TransferCredit = st89.transferCredit

	data.Languages = st89.langs

	b := &game_setting89_proto.ConfigRecall_Bets{}

	for _, bet := range st89.bets[0] {
		b.Bet = append(b.Bet, bet)
	}

	data.Levels = append(data.Levels, b)

	data.Line = []uint32{1}

	data.Rates = st89.rate

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

	if data, ok := s.allSelected89Game[secWebSocketKey]; ok {
		s.allSelected89Game[uuid] = data
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

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.gameId
	}

	logger.Service.Zap.Errorw(GameSetting89_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)

	errorcode.Service.Fatal(secWebSocketKey, GameSetting89_GAME_ID_NOT_FOUND)

	return ""
}

func (s *service) MathModuleId(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.mathModuleId
	}

	// TODO JOHNNY ERROR CODE

	return ""
}

func (s *service) BetList(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.betList
	}

	// TODO JOHNNY ERROR CODE

	return ""
}

func (s *service) Bet(secWebSocketKey string, index uint32) (bet uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {

		return v.bets[0][index]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) RateList(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.rateList
	}

	// TODO JOHNNY ERROR CODE

	return ""
}

func (s *service) Rate(secWebSocketKey string) (rate uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.rate[0]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) RateIndex(secWebSocketKey string) (rateIndex uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.rateIndex
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) BalanceLimit(secWebSocketKey string) (balanceLimit uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.balanceLimit
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) RoundStartWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.waitingTime[0]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) BetWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.waitingTime[1]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) DrawWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.waitingTime[2]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) Idle(secWebSocketKey string) (sessionTimeout uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.sessionTimeout
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) IPConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.ipConfig
	}

	// TODO JOHNNY ERROR CODE

	return 0
}
func (s *service) HostConnectConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelected89Game[secWebSocketKey]; ok {
		return v.hostConnectConfig
	}

	// TODO JOHNNY ERROR CODE

	return 0
}
