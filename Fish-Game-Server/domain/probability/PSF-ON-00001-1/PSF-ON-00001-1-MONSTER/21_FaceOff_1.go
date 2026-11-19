package PSF_ON_00001_1_MONSTER

import (
    "os"
    "strings"
)

var FaceOff1 = &faceOff1{
    bonusMode: strings.Contains(os.Getenv("ENABLED_BONUS"), "21"),
}

type faceOff1 struct {
    bonusMode bool
}

type BsFaceOffMath struct {
    IconID           int
    IsWildSubstitute bool
    BonusID          string
    BonusTimes       []int
    HitWeight        []int
    IconPays         []int
}

type FsFaceOffMath struct {
    IconID   int
    IconPays []int
}
