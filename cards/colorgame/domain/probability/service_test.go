package probability

import (
	"testing"

	"gitlab.iplaystar.net/game-server/logger"
)

func Test_service_Roll(t *testing.T) {
	t.Run("Roll Dice", func(t *testing.T) {
		s := &controllRiceService{}
		diceCount := [6]int{0, 0, 0, 0, 0, 0}
		const times = 50
		for i := 0; i < times; i++ {
			result := s.Roll()
			logger.Service.Zap.Infow("Result", "Dices:", result)
			for _, r := range result {
				diceCount[r] += 1
			}
		}
		logger.Service.Zap.Infow("Result", "Dice Count", diceCount)
	})
}
