//+build dev

package activity

import (
    "fish-game-server/domain/bullet"
    "fish-game-server/domain/fish"
    "fish-game-server/domain/probability"
)

func init() {
    // do nothing
}

func (s *service) Check(secWebSocketKey, hostExtId, hostId, memberId string, isGuest bool) {
    // do nothing
}

func (s *service) Record(secWebSocketKey string, hitFish *fish.Fish, hitBullet *bullet.Bullet, hitResult *probability.Probability) {
    // do nothing
}

func (s *service) RecordBonus(secWebSocketKey string, bonus interface{}) {
    // do nothing
}
