package PSF_ON_00001_2_MONSTER

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
    BonusID            string
    BonusTimes         []int
    LowIconPays        []int
    LowIconPaysWeight  []int
    HighIconPays       []int
    HighIconPaysWeight []int
    RTP1               struct{ HitBsRedEnvelopeMath } `json:"RTP1"`
    RTP2               struct{ HitBsRedEnvelopeMath } `json:"RTP2"`
    RTP3               struct{ HitBsRedEnvelopeMath } `json:"RTP3"`
    RTP4               struct{ HitBsRedEnvelopeMath } `json:"RTP4"`
    RTP5               struct{ HitBsRedEnvelopeMath } `json:"RTP5"`
    RTP6               struct{ HitBsRedEnvelopeMath } `json:"RTP6"`
    RTP7               struct{ HitBsRedEnvelopeMath } `json:"RTP7"`
    RTP8               struct{ HitBsRedEnvelopeMath } `json:"RTP8"`
    RTP9               struct{ HitBsRedEnvelopeMath } `json:"RTP9"`
    RTP10              struct{ HitBsRedEnvelopeMath } `json:"RTP10"`
    RTP11              struct{ HitBsRedEnvelopeMath } `json:"RTP11"`
}

type HitBsRedEnvelopeMath struct {
    ID            string `json:"ID"`
    HitWeight     []int  `json:"HitWeight"`
    TriggerIconID int    `json:"TriggerIconID"`
    TriggerWeight []int  `json:"TriggerWeight"`
    Type          int    `json:"Type"`
}

func (r *redEnvelope) pick(math *BsRedEnvelopeMath) []int {
    lowPayOptions := make([]rng.Option, 0, 6)
    for i := 0; i < len(math.LowIconPaysWeight); i++ {
        lowPayOptions = append(lowPayOptions, rng.Option{math.LowIconPaysWeight[i], math.LowIconPays[i]})
    }

    highPayOptions := make([]rng.Option, 0, 5)
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
