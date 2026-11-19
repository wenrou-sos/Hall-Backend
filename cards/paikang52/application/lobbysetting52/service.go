package lobbysetting52

import (
	lobby_setting52_proto "52-game-server/application/lobbysetting52/proto"
	"strconv"
	"strings"
	"sync"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/auth"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/idle"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	lobby_setting_proto "gitlab.iplaystar.net/game-server/lobby-setting/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/session"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

var Service = &service{
	Id:             "LobbySetting52Service",
	allHost52Games: make(map[string]*host52Game),
	rwMutex:        &sync.RWMutex{},
}

type service struct {
	Id             string
	allHost52Games map[string]*host52Game
	rwMutex        *sync.RWMutex
}

func (s *service) EMSGID_eLobbyConfigCallHandler(memberId string, guestEnable int, ls *lobbysetting.LobbySetting, cc *lobby_setting_proto.ConfigCall) {
	s.rwMutex.Lock()
	if game, ok := ls.AvailableGames[cc.GameId]; ok {
		s.allHost52Games[ls.SecWebSocketKey] = game.(*host52Game)
	} else {
		logger.Service.Zap.Errorw(LobbySetting52_GAME_ID_NOT_FOUND, "MemberId", memberId, "GameId", cc.GameId)
		s.rwMutex.Unlock()
		return
	}

	s.rwMutex.Unlock()

	session.Service.New(
		ls.SecWebSocketKey,
		ls.HostExtId,
		ls.AvailableGames[cc.GameId].(*host52Game).HostId,
		memberId,
		cc.GameId,
		cc.SubgameId,
		ls.RemoteAddr,
		ls.UserAgent,
		cc.Version,
		cc.GameVersion,
	)

	if guestEnable == 0 {
		sessionmanager.Service.Start(
			ls.SecWebSocketKey,
			ls.HostExtId,
			ls.AvailableGames[cc.GameId].(*host52Game).HostId,
			memberId,
			cc.GameId,
		)
	}

	flux.Send(idle.ActionIdleTimeoutStart, s.Id, idle.Service.Id,
		ls.SecWebSocketKey,
		ls.AvailableGames[cc.GameId].(*host52Game).SessionTimeout,
	)
}

func (s *service) EMSGID_eLobbyConfigRecallHandler(ls *lobbysetting.LobbySetting, isTokenValid bool, cc *lobby_setting_proto.ConfigCall) []byte {
	data := &lobby_setting52_proto.ConfigRecall{
		Msgid: common_proto.EMSGID_eLobbyConfigRecall,
	}

	if !isTokenValid {
		s.cleanData(ls.SecWebSocketKey, auth.Auth_TOKEN_EXPIRED)
		data.StatusCode = common_proto.Status_kInvalid
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	if !wallet.Service.Existed(ls.SecWebSocketKey) {
		s.cleanData(ls.SecWebSocketKey, wallet.Wallet_NOT_FOUND)
		data.StatusCode = common_proto.Status_kInvalid
	}

	go session.Service.Start(ls.SecWebSocketKey)

	data.StatusCode = common_proto.Status_kSuccess

	if game, ok := ls.AvailableGames[cc.GameId].(*host52Game); ok {
		bets := strings.Split(game.BetList, ",")

		data.Visible = s.ColumnVisible(game.PanelConfig, game.RoomConfig)

		data.Fee = game.Fee

		for _, credit := range strings.Split(game.TransferCredit, ",") {
			atoiCredit, _ := strconv.Atoi(credit)
			data.TransferCredit = append(data.TransferCredit, uint32(atoiCredit))
		}
		for k, l := range strings.Split(game.BalanceLimit, ",") {
			atoiBalance, _ := strconv.Atoi(l)
			bet, _ := strconv.Atoi(bets[k])
			r := &lobby_setting52_proto.ConfigRecall_RoomInfo{
				GameId:                game.GameId,
				SubgameId:             uint32(k),
				Line:                  []uint32{1},
				Bets:                  uint32(bet),
				BalanceLimit:          uint32(atoiBalance),
				LanguagesDefaultIndex: 0,
			}

			data.RoomInfo = append(data.RoomInfo, s.parseGameSetting(game, r))
		}
	}

	dataByte, _ := proto.Marshal(data)
	return dataByte
}

func (s *service) parseGameSetting(game *host52Game, r *lobby_setting52_proto.ConfigRecall_RoomInfo) *lobby_setting52_proto.ConfigRecall_RoomInfo {
	data := &lobby_setting52_proto.ConfigRecall_Bets{}

	for _, bet := range strings.Split(game.BetList, ",") {
		atoiBet, _ := strconv.Atoi(bet)
		data.Bet = append(data.Bet, uint32(atoiBet))
	}

	r.Levels = append(r.Levels, data)

	for _, v := range strings.Split(game.Langs, ",") {
		r.Languages = append(r.Languages, v)
	}

	for _, time := range strings.Split(game.WaitingTime, ",") {
		atoiTime, _ := strconv.Atoi(time)
		r.WaitingTime = append(r.WaitingTime, uint32(atoiTime))
	}

	return r
}

func (s *service) ColumnVisible(status uint32, status2 uint32) *lobby_setting52_proto.ConfigRecall_Column {
	// reserved, reserved, ATM_ICON, ATM_DASHBOARD
	// (1 ASCII(49):show, 0 ASCII(48):hidden)
	// All show:1 (0011)

	data := &lobby_setting52_proto.ConfigRecall_Column{}

	for k, v := range []rune(strconv.FormatUint(uint64(status), 2)) {
		switch k {
		case 0: // ATM_ICON
			data.AtmIcon = v == 49

		case 1: // ATM_DASHBOARD
			data.AtmDashboard = v == 49
		}
	}
	data.FriendroomIcon = status2 != 0

	return data
}

func (s *service) cleanData(secWebSocketKey, errorCode string) {
	logger.Service.Zap.Errorw(errorCode,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, errorCode)
}

func (s *service) GameId(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allHost52Games[secWebSocketKey]; ok {
		return v.GameId
	}

	logger.Service.Zap.Errorw(LobbySetting52_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey)

	errorcode.Service.Fatal(secWebSocketKey, LobbySetting52_GAME_ID_NOT_FOUND)
	return ""
}

func (s *service) AutoATM(secWebSocketKey string) bool {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allHost52Games[secWebSocketKey]; ok {
		atm := s.ColumnVisible(v.PanelConfig, v.RoomConfig)
		return atm.AtmIcon == false && atm.AtmDashboard == false
	}
	logger.Service.Zap.Errorw(LobbySetting52_PANEL_CONFIG_NOT_FOUND,
		"GameUser", secWebSocketKey)

	errorcode.Service.Fatal(secWebSocketKey, LobbySetting52_PANEL_CONFIG_NOT_FOUND)
	return false
}
