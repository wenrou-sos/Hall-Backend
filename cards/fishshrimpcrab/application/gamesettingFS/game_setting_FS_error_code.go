package gamesettingFS

import (
	"fish-shrimp-crab-game-server/models"
)

const (
	GameSettingFS_QUERY_HOST_FS_GAME_FAILED = models.GameSettingFS + "0"
	GameSettingFS_GAME_DB_NOT_FOUND         = models.GameSettingFS + "1"
	GameSettingFS_NOT_ENOUGH_BALANCE        = models.GameSettingFS + "2"
	GameSettingFS_GAME_ID_NOT_FOUND         = models.GameSettingFS + "3"
	GameSettingFS_GET_BALANCE_FAILED        = models.GameSettingFS + "4"
)
