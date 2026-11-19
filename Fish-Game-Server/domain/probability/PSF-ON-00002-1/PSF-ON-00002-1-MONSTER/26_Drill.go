package PSF_ON_00002_1_MONSTER

import (
    "gitlab.iplaystar.net/game-server/rng"
    "os"
    "strings"
)

var Drill = &drill{
    bonusMode:      strings.Contains(os.Getenv("ENABLED_BONUS"), "26"),
    extraBonusMode: strings.Contains(os.Getenv("ENABLED_BONUS"), "31"),
}

type drill struct {
    bonusMode      bool
    extraBonusMode bool
}

type BsDrillMath struct {
    IconID           int
    BonusID          string
    BonusTimes       []int
    BonusTimesWeight []int
    BonusIconID      []int
    IconPays         []int
    RTP1             struct{ HitBsDrillMath } `json:"RTP1"`
    RTP2             struct{ HitBsDrillMath } `json:"RTP2"`
    RTP3             struct{ HitBsDrillMath } `json:"RTP3"`
    RTP4             struct{ HitBsDrillMath } `json:"RTP4"`
    RTP5             struct{ HitBsDrillMath } `json:"RTP5"`
    RTP6             struct{ HitBsDrillMath } `json:"RTP6"`
    RTP7             struct{ HitBsDrillMath } `json:"RTP7"`
    RTP8             struct{ HitBsDrillMath } `json:"RTP8"`
    RTP9             struct{ HitBsDrillMath } `json:"RTP9"`
    RTP10            struct{ HitBsDrillMath } `json:"RTP10"`
    RTP11            struct{ HitBsDrillMath } `json:"RTP11"`
}

type HitBsDrillMath struct {
    ID            string `json:"ID"`
    HitWeight     []int  `json:"HitWeight"`
    TriggerIconID int    `json:"TriggerIconID"`
    TriggerWeight []int  `json:"TriggerWeight"`
    Type          int    `json:"Type"`
}

func (d *drill) pick(math *BsDrillMath) int {
    bonusTimes := make([]rng.Option, 0, 6)

    for i := 0; i < len(math.BonusTimesWeight); i++ {
        bonusTimes = append(bonusTimes, rng.Option{math.BonusTimesWeight[i], math.BonusTimes[i]})
    }

    return MONSTER.rng(bonusTimes).(int)
}
