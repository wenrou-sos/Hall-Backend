package PSF_ON_00001_1_MONSTER

import "gitlab.iplaystar.net/game-server/rng"

var HotPot = &hotPot{}

type hotPot struct {
}

type BsHotPotMath struct {
    IconID           int
    IsWildSubstitute bool
    BonusID          string
    BonusTimes       []int
    HitWeight        []int
    IconPays         []int
    IconPaysWeight   []int
}

func (h *hotPot) Hit(math *BsHotPotMath) (iconPay int) {
    if MONSTER.isHit(math.HitWeight) {
        return h.pick(math)
    }

    return 0
}

func (h *hotPot) pick(math *BsHotPotMath) int {
    iconPays := make([]rng.Option, 0, 9)
    for i := 0; i < len(math.IconPaysWeight); i++ {
        iconPays = append(iconPays, rng.Option{math.IconPaysWeight[i], math.IconPays[i]})
    }

    return MONSTER.rng(iconPays).(int)
}
