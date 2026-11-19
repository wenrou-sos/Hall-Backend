package PSF_ON_00001_1_MONSTER

import (
    "gitlab.iplaystar.net/game-server/rng"
    "os"
    "strings"
)

var RedEnvelope = &redEnvelope{
    bonusMode: strings.Contains(os.Getenv("ENABLED_BONUS"), "28"),
}

type redEnvelope struct {
    bonusMode bool
}

type BsRedEnvelopeMath struct {
    IconID             int
    IsWildSubstitute   bool
    BonusID            string
    BonusTimes         []int
    HitWeight          []int
    LowIconPays        []int
    LowIconPaysWeight  []int
    HighIconPays       []int
    HighIconPaysWeight []int
}

func (r *redEnvelope) pick(math *BsRedEnvelopeMath) []int {
    lowPayOptions := make([]rng.Option, 0, 6)
    for i := 0; i < len(math.LowIconPaysWeight); i++ {
        lowPayOptions = append(lowPayOptions, rng.Option{math.LowIconPaysWeight[i], math.LowIconPays[i]})
    }

    highPayOptions := make([]rng.Option, 0, 7)
    for i := 0; i < len(math.HighIconPaysWeight); i++ {
        highPayOptions = append(highPayOptions, rng.Option{math.HighIconPaysWeight[i], math.HighIconPays[i]})
    }

    iconPays := []int{
        MONSTER.rng(lowPayOptions).(int),
        MONSTER.rng(lowPayOptions).(int),
        MONSTER.rng(lowPayOptions).(int),
        MONSTER.rng(lowPayOptions).(int),
        MONSTER.rng(highPayOptions).(int),
    }

    if len(iconPays) != 5 {
        panic("Error:PSFM_00001_MONSTER:pick:iconPays")
    }
    return iconPays
}
