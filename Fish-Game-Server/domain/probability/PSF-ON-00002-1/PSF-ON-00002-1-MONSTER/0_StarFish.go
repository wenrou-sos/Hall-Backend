package PSF_ON_00002_1_MONSTER

import (
    "os"
    "strings"
)

var StarFish = &starFish{
    bonusMode: strings.Contains(os.Getenv("ENABLED_BONUS"), "31"),
}

type starFish struct {
    bonusMode bool
}

type BsFishMath struct {
    IconID     int                     `json:"IconID"`
    BonusID    string                  `json:"BonusID"`
    BonusTimes []int                   `json:"BonusTimes"`
    IconPays   []int                   `json:"IconPays"`
    RTP1       struct{ HitBsFishMath } `json:"RTP1"`
    RTP2       struct{ HitBsFishMath } `json:"RTP2"`
    RTP3       struct{ HitBsFishMath } `json:"RTP3"`
    RTP4       struct{ HitBsFishMath } `json:"RTP4"`
    RTP5       struct{ HitBsFishMath } `json:"RTP5"`
    RTP6       struct{ HitBsFishMath } `json:"RTP6"`
    RTP7       struct{ HitBsFishMath } `json:"RTP7"`
    RTP8       struct{ HitBsFishMath } `json:"RTP8"`
    RTP9       struct{ HitBsFishMath } `json:"RTP9"`
    RTP10      struct{ HitBsFishMath } `json:"RTP10"`
    RTP11      struct{ HitBsFishMath } `json:"RTP11"`
}

type HitBsFishMath struct {
    ID            string `json:"ID"`
    HitWeight     []int  `json:"HitWeight"`
    TriggerIconID int    `json:"TriggerIconID"`
    TriggerWeight []int  `json:"TriggerWeight"`
    Type          int    `json:"Type"`
}

type FsFishMath struct {
    IconID   int   `json:"IconID"`
    IconPays []int `json:"IconPays"`
}
