package PSF_ON_00001_1_MONSTER

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
    IconID           int    `json:"IconID"`
    IsWildSubstitute bool   `json:"IsWildSubstitute"`
    BonusID          string `json:"BonusID"`
    BonusTimes       []int  `json:"BonusTimes"`
    HitWeight        []int  `json:"HitWeight"`
    IconPays         []int  `json:"IconPays"`
    TriggerIconID    int    `json:"TriggerIconID"`
    TriggerWeight    []int  `json:"TriggerWeight"`
}

type FsFishMath struct {
    IconID   int   `json:"IconID"`
    IconPays []int `json:"IconPays"`
}
