package gamesettingU

import (
	"strconv"
	"strings"
	"sync"
	game_settingU_proto "u-game-server/application/gamesettingU/proto"

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
	Id:               "GameSettingUService",
	allSelectedUGame: make(map[string]*selectedUGame),
	rwMutex:          &sync.RWMutex{},
}

type service struct {
	Id               string
	allSelectedUGame map[string]*selectedUGame
	rwMutex          *sync.RWMutex
}

func (s *service) EMSGID_eGameConfigCallHandler(memberId string, guestEnable int, gs *gamesetting.GameSetting, cc *game_setting_proto.ConfigCall) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	stU := s.parseGameSetting(cc.GameId, cc.SubgameId, gs)

	if stU == nil {
		gs.SelectedGame = nil
		return
	}

	cent, err := wallet.Service.Cent(gs.SecWebSocketKey)

	if err != nil {
		gs.SelectedGame = nil
		logger.Service.Zap.Errorw(GameSettingU_GET_CENT_FAILED,
			"GameUser", gs.SecWebSocketKey,
			"MemberId", memberId,
			"CentLimit", stU.balanceLimit,
			"Cent", cent,
			"Error", err,
		)
		errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingU_GET_CENT_FAILED)
		return
	}

	if cent < uint64(stU.balanceLimit) {
		gs.SelectedGame = nil
		logger.Service.Zap.Warnw(GameSettingU_NOT_ENOUGH_BALANCE,
			"GameUser", gs.SecWebSocketKey,
			"MemberId", memberId,
			"CentLimit", stU.balanceLimit,
			"Cent", cent,
		)
		return
	}

	s.allSelectedUGame[gs.SecWebSocketKey] = stU

	gs.SelectedGame = stU

	session.Service.New(
		gs.SecWebSocketKey,
		gs.HostExtId,
		stU.hostId,
		memberId,
		stU.gameId,
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
			stU.hostId,
			memberId,
			stU.gameId,
		)
	}

	flux.Send(idle.ActionIdleTimeoutStart, s.Id, idle.Service.Id,
		gs.SecWebSocketKey,
		stU.sessionTimeout,
	)
}

func (s *service) parseGameSetting(gameId string, subGameId uint32, gs *gamesetting.GameSetting) *selectedUGame {
	if game, ok := gs.AvailableGames[gameId].(*hostUGame); ok {
		atoiBalance, _ := strconv.Atoi(strings.Split(game.BalanceLimit, ",")[subGameId])
		atoiBet, _ := strconv.Atoi(strings.Split(game.BetList, ",")[subGameId])
		atoiRoomLimit, _ := strconv.Atoi(strings.Split(game.RoomLimit, ",")[subGameId])
		atoiAutoBlacklistValue, _ := strconv.Atoi(strings.Split(game.AutoBlacklistValue, ",")[subGameId%6])

		stU := &selectedUGame{
			hostId:             game.HostId,
			gameId:             game.GameId,
			subGameId:          subGameId,
			betList:            game.BetList, // for game room id used
			rateIndex:          subGameId,
			bet:                uint32(atoiBet),
			langs:              nil,
			balanceLimit:       uint32(atoiBalance),
			roomLimit:          uint32(atoiRoomLimit),
			sessionTimeout:     game.SessionTimeout,
			ipConfig:           game.IpConfig,
			roomConfig:         game.RoomConfig,
			bankerConfig:       game.BankerConfig,
			hostConnectConfig:  game.HostConnectConfig,
			fee:                game.Fee,
			idBlockPercent:     game.IdBlockPercent,
			autoBlacklistValue: uint64(atoiAutoBlacklistValue),
		}

		for _, v := range strings.Split(game.Langs, ",") {
			stU.langs = append(stU.langs, v)
		}

		for _, time := range strings.Split(game.WaitingTime, ",") {
			atoiTime, _ := strconv.Atoi(time)
			stU.waitingTime = append(stU.waitingTime, uint32(atoiTime))
		}
		sid := subGameId % 6
		stU.waitingTime = stU.waitingTime[sid*6 : sid*6+6]

		for _, id := range strings.Split(game.MathId, ",") {
			atoiId, _ := strconv.Atoi(id)
			stU.mathModuleId = append(stU.mathModuleId, atoiId)
		}
		stU.mathModuleId = stU.mathModuleId[sid*6 : sid*6+6]

		for _, credit := range strings.Split(game.TransferCredit, ",") {
			atoiCredit, _ := strconv.Atoi(credit)
			stU.transferCredit = append(stU.transferCredit, uint32(atoiCredit))
		}

		rates := strings.Split(game.UnluckyRate, ",")
		r, _ := strconv.Atoi(rates[sid])
		vipr, _ := strconv.Atoi(rates[sid+6])
		stU.unluckyRate = []int{r, vipr}

		stU.blacklistCondition, _ = strconv.Atoi(strings.Split(game.BlacklistCondition, ",")[sid])
		stU.isolateRate, _ = strconv.Atoi(strings.Split(game.IsolateRate, ",")[sid])

		return stU
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
	data := &game_settingU_proto.ConfigRecall{
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
		logger.Service.Zap.Warnw(GameSettingU_NOT_ENOUGH_BALANCE,
			"GameUser", gs.SecWebSocketKey)

		data.StatusCode = common_proto.Status_kNoEnoughCredit
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	go session.Service.Start(gs.SecWebSocketKey)

	data.StatusCode = common_proto.Status_kSuccess

	stU := gs.SelectedGame.(*selectedUGame)

	data.WaitingTime = stU.waitingTime

	data.TransferCredit = stU.transferCredit

	data.Languages = stU.langs

	data.Line = []uint32{1}

	data.Bet = stU.bet

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

	if data, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		s.allSelectedUGame[uuid] = data
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

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.gameId
	}

	logger.Service.Zap.Errorw(GameSettingU_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)

	errorcode.Service.Fatal(secWebSocketKey, GameSettingU_GAME_ID_NOT_FOUND)

	return ""
}

func (s *service) BetList(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.betList
	}

	return ""
}

func (s *service) BalanceLimit(secWebSocketKey string) (balanceLimit uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.balanceLimit
	}

	return 0
}

func (s *service) RoomLimit(secWebSocketKey string) (roomLimit uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.roomLimit
	}

	return 0
}

func (s *service) FirstRoundStartWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.waitingTime[0]
	}

	return 0
}

func (s *service) PlayerRoundWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.waitingTime[1]
	}

	return 0
}

func (s *service) GameRoundWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.waitingTime[2]
	}

	return 0
}

func (s *service) RoundStartWaitingTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.waitingTime[3]
	}

	return 0
}

func (s *service) PredictTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.waitingTime[4]
	}

	return 0
}

func (s *service) BotLogicTime(secWebSocketKey string) (time uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.waitingTime[5]
	}

	return 0
}

func (s *service) Idle(secWebSocketKey string) (sessionTimeout uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.sessionTimeout
	}

	return 0
}

func (s *service) IPConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.ipConfig
	}

	return 0
}
func (s *service) HostConnectConfigEnable(secWebSocketKey string) (enable uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.hostConnectConfig
	}

	return 0
}
func (s *service) Fee(secWebSocketKey string) uint32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		if v.fee <= 50 && v.fee >= 0 {
			return v.fee
		} else {
			return 5
		}
	}

	return 5
}

func (s *service) SubGameId(secWebSocketKey string) int32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return int32(v.subGameId)
	}

	logger.Service.Zap.Errorw(GameSettingU_SUB_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)

	errorcode.Service.Fatal(secWebSocketKey, GameSettingU_SUB_GAME_ID_NOT_FOUND)

	return -1
}

func (s *service) DrawPercent(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.mathModuleId[0]
	}

	return 10
}

func (s *service) LuckyPercent(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.mathModuleId[1]
	}

	return 60
}

func (s *service) LuckyMax(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.mathModuleId[2]
	}

	return 6
}

func (s *service) DrawPercentVIP(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.mathModuleId[3]
	}

	return 10
}

func (s *service) LuckyPercentVIP(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.mathModuleId[4]
	}

	return 0
}

func (s *service) LuckyMaxVIP(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.mathModuleId[5]
	}

	return 0
}

func (s *service) IdBlockPercent(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
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

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.hostId
	}
	return ""
}

func (s *service) Bet(secWebSocketKey string) uint32 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.bet
	}
	return 0
}

func (s *service) UnluckyRate(secWebSocketKey string, isVip bool) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		if isVip {
			return v.unluckyRate[1]
		} else {
			return v.unluckyRate[0]
		}
	}
	return 0
}

func (s *service) BlacklistCondition(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.blacklistCondition
	}

	return 0
}

func (s *service) IsolateRate(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.isolateRate
	}

	return 0
}

func (s *service) AutoBlacklistValue(secWebSocketKey string) uint64 {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allSelectedUGame[secWebSocketKey]; ok {
		return v.autoBlacklistValue
	}

	return 0
}
