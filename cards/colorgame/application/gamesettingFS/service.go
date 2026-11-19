package gamesettingFS

import (
	game_settingFS_proto "colorgame-game-server/application/gamesettingFS/proto"
	"colorgame-game-server/application/lobbysettingFS"
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
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/session"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	BET_AREA_LIMIT_GROUPE_OF_TWO = 2 //押注值n個一組
)

var Service = &service{
	Id:                "GameSettingFSService",
	allSelectedFSGame: make(map[string]*selectedFSGame),
	rwMutex:           &sync.RWMutex{},
	DefaultBotKeys: []string{
		"Rate0DefaultBot",
		"Rate1DefaultBot",
		"Rate2DefaultBot",
		"Rate3DefaultBot",
		"Rate4DefaultBot",
		"Rate5DefaultBot",
	},
}

type service struct {
	Id                string
	allSelectedFSGame map[string]*selectedFSGame
	rwMutex           *sync.RWMutex
	DefaultBotKeys    []string
}

func (s *service) EMSGID_eGameConfigCallHandler(memberId string, guestEnable int, gs *gamesetting.GameSetting, cc *game_setting_proto.ConfigCall) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	st := s.parseGameSetting(cc.GameId, cc.SubgameId, gs)

	if st == nil {
		gs.SelectedGame = nil
		return
	}

	balance, err := wallet.Service.BalanceCache(gs.SecWebSocketKey)

	if err != nil {
		gs.SelectedGame = nil
		logger.Service.Zap.Errorw(GameSettingFS_GET_BALANCE_FAILED,
			"GameUser", gs.SecWebSocketKey,
			"MemberId", memberId,
			"Balance", balance,
			"Error", err,
		)
		errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingFS_GET_BALANCE_FAILED)
		return
	}

	s.allSelectedFSGame[gs.SecWebSocketKey] = st

	gs.SelectedGame = st

	session.Service.New(
		gs.SecWebSocketKey,
		gs.HostExtId,
		st.hostId,
		memberId,
		st.gameId,
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
			st.hostId,
			memberId,
			st.gameId,
		)
	}

	flux.Send("startChangeRoomCountdown", s.Id, gs.SecWebSocketKey)

	// flux.Send(idle.ActionIdleTimeoutStart, s.Id, idle.Service.Id,
	// 	gs.SecWebSocketKey,
	// 	st.sessionTimeout,
	// )
}

func (s *service) parseGameSetting(gameId string, subGameId uint32, gs *gamesetting.GameSetting) *selectedFSGame {
	if game, ok := gs.AvailableGames[gameId].(*HostFSGame); ok {
		if int(subGameId+1) > len(strings.Split(game.RateList, ",")) {
			logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_CALL_PROTO_INVALID,
				"GameUser", gs.SecWebSocketKey,
				"SubGameId", subGameId,
			)
			return nil
		}

		atoiRate, _ := strconv.Atoi(strings.Split(game.RateList, ",")[subGameId])

		st := &selectedFSGame{
			hostId:            game.HostId,
			gameId:            game.GameId,
			betList:           game.BetList, // for game room id used
			betAreaLimit:      []uint32{},
			rateList:          game.RateList, // for game room id used
			rateIndex:         subGameId,
			rate:              []uint32{uint32(atoiRate)},
			bets:              [1][]uint32{},
			langs:             nil,
			sessionTimeout:    game.SessionTimeout,
			ipConfig:          game.IpConfig,
			roomConfig:        game.RoomConfig,
			hostConnectConfig: game.HostConnectConfig,
		}

		for _, bet := range strings.Split(game.BetList, ",") {
			atoiBet, _ := strconv.Atoi(bet)
			st.bets[0] = append(st.bets[0], uint32(atoiBet))
		}

		for _, time := range strings.Split(game.WaitingTime, ",") {
			atoiTime, _ := strconv.Atoi(time)
			st.waitingTime = append(st.waitingTime, uint32(atoiTime))
		}
		st.waitingTime = st.waitingTime[subGameId : subGameId+1]

		groupOfNum := BET_AREA_LIMIT_GROUPE_OF_TWO
		for i, betAreaLimit := range strings.Split(game.BetAreaLimit, ",") {
			if i >= int(subGameId)*groupOfNum && i < int(subGameId)*groupOfNum+groupOfNum {
				atoiBetAreaLimit, _ := strconv.Atoi(betAreaLimit)
				st.betAreaLimit = append(st.betAreaLimit, uint32(atoiBetAreaLimit))
			}
		}

		for _, v := range strings.Split(game.Langs, ",") {
			st.langs = append(st.langs, v)
		}

		return st
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
	data := &game_settingFS_proto.ConfigRecall{
		Msgid:                 common_proto.EMSGID_eGameConfigRecall,
		RatesDefaultIndex:     subGameId,
		LanguagesDefaultIndex: 0,
	}

	if !isTokenValid {
		logger.Service.Zap.Warnw(auth.Auth_TOKEN_EXPIRED,
			"GameUser", gs.SecWebSocketKey)

		s.cleanData(gs.SecWebSocketKey, auth.Auth_TOKEN_EXPIRED)
		data.StatusCode = common_proto.Status_kInvalid
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	if !wallet.Service.Existed(gs.SecWebSocketKey) {
		logger.Service.Zap.Warnw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
			"GameUser", gs.SecWebSocketKey)

		s.cleanData(gs.SecWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)
		data.StatusCode = common_proto.Status_kInvalid
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	if gs.SelectedGame == nil {
		logger.Service.Zap.Warnw(GameSettingFS_NOT_ENOUGH_BALANCE,
			"GameUser", gs.SecWebSocketKey)

		data.StatusCode = common_proto.Status_kNoEnoughCredit
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	go session.Service.Start(gs.SecWebSocketKey)

	data.StatusCode = common_proto.Status_kSuccess

	st := gs.SelectedGame.(*selectedFSGame)

	data.Languages = st.langs

	b := &game_settingFS_proto.ConfigRecall_Bets{}

	for _, bet := range st.bets[0] {
		b.Bet = append(b.Bet, bet)
	}

	data.Levels = append(data.Levels, b)

	data.Line = []uint32{1}

	data.Rates = st.rate

	data.BetAreaLimit = st.betAreaLimit

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

	if data, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		s.allSelectedFSGame[uuid] = data
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

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.gameId
	}

	logger.Service.Zap.Errorw(GameSettingFS_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)

	errorcode.Service.Fatal(secWebSocketKey, GameSettingFS_GAME_ID_NOT_FOUND)

	return ""
}

func (s *service) BetList(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.betList
	}

	// TODO JOHNNY ERROR CODE

	return ""
}

func (s *service) Bet(secWebSocketKey string, index uint32) (bet uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {

		return v.bets[0][index]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) BetAreaLimit(secWebSocketKey string, betAreaIndex uint32) uint32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.betAreaLimit[betAreaIndex]
	}
	return 0
}

func (s *service) RateList(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.rateList
	}

	// TODO JOHNNY ERROR CODE

	return ""
}

func (s *service) Rate(secWebSocketKey string) (rate uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.rate[0]
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) RateIndex(secWebSocketKey string) (rateIndex uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.rateIndex
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) BetWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.waitingTime[0]
	}

	return 0
}

func (s *service) Idle(secWebSocketKey string) (sessionTimeout uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.sessionTimeout
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) IPConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.ipConfig
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) HostConnectConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedFSGame[secWebSocketKey]; ok {
		return v.hostConnectConfig
	}

	// TODO JOHNNY ERROR CODE

	return 0
}

func (s *service) NewAllselectedGame(secWebSocketKey, hostExtId, gameId string, rateIndex uint32) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	gameSetting := lobbysettingFS.Service.BotDefaultLobbySetting(hostExtId, gameId)
	if gameSetting == nil {
		logger.Service.Zap.Errorw(gamesetting.GameSetting_GAME_SETTING_NOT_FOUND,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
			"GameId", gameId,
		)
		return
	}

	ratelist := strings.Split(gameSetting.RateList, ",")
	if len(ratelist) == 0 || int(rateIndex) >= len(ratelist) {
		logger.Service.Zap.Errorw(gamesetting.GameSetting_GAME_SETTING_NOT_FOUND,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
			"gameId", gameId,
			"rateIndex", rateIndex,
		)
		return
	}

	rateString := ratelist[rateIndex]
	rate, _ := strconv.Atoi(rateString)

	fakegameSetting := &selectedFSGame{
		hostId:            gameSetting.HostId,
		gameId:            gameSetting.GameId,
		betList:           gameSetting.BetList,
		rateList:          gameSetting.RateList,
		bets:              [1][]uint32{},
		rate:              []uint32{uint32(rate)},
		langs:             nil,
		rateIndex:         rateIndex,
		waitingTime:       []uint32{},
		sessionTimeout:    gameSetting.SessionTimeout,
		ipConfig:          gameSetting.IpConfig,
		roomConfig:        gameSetting.RoomConfig,
		hostConnectConfig: gameSetting.HostConnectConfig,
		betAreaLimit:      nil,
	}

	betStrings := strings.Split(gameSetting.BetList, ",")
	for _, betString := range betStrings {
		bet, _ := strconv.Atoi(betString)
		fakegameSetting.bets[0] = append(fakegameSetting.bets[0], uint32(bet))
	}

	waitingTimeStrings := strings.Split(gameSetting.WaitingTime, ",")
	for _, waitingTimeString := range waitingTimeStrings {
		waitingTime, _ := strconv.Atoi(waitingTimeString)
		fakegameSetting.waitingTime = append(fakegameSetting.waitingTime, uint32(waitingTime))
	}

	//2個一組，分別代表(全區上限 . 一符號)
	betAreaLimitNumPerSet := uint32(BET_AREA_LIMIT_GROUPE_OF_TWO)
	betAreaLimitStrings := strings.Split(gameSetting.BetAreaLimit, ",")
	betAreaLimitStrings = betAreaLimitStrings[betAreaLimitNumPerSet*rateIndex : betAreaLimitNumPerSet*(rateIndex+1)]
	for _, limitString := range betAreaLimitStrings {
		limit, _ := strconv.Atoi(limitString)
		fakegameSetting.betAreaLimit = append(fakegameSetting.betAreaLimit, uint32(limit))
	}

	s.allSelectedFSGame[secWebSocketKey] = fakegameSetting
}
