package PSF_ON_00001_2_MONSTER

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
    IconID     int                        `json:"IconID"`
    BonusID    string                     `json:"BonusID"`
    BonusTimes []int                      `json:"BonusTimes"`
    IconPays   []int                      `json:"IconPays"`
    RTP1       struct{ HitBsFaceOffMath } `json:"RTP1"`
    RTP2       struct{ HitBsFaceOffMath } `json:"RTP2"`
    RTP3       struct{ HitBsFaceOffMath } `json:"RTP3"`
    RTP4       struct{ HitBsFaceOffMath } `json:"RTP4"`
    RTP5       struct{ HitBsFaceOffMath } `json:"RTP5"`
    RTP6       struct{ HitBsFaceOffMath } `json:"RTP6"`
    RTP7       struct{ HitBsFaceOffMath } `json:"RTP7"`
    RTP8       struct{ HitBsFaceOffMath } `json:"RTP8"`
    RTP9       struct{ HitBsFaceOffMath } `json:"RTP9"`
    RTP10      struct{ HitBsFaceOffMath } `json:"RTP10"`
    RTP11      struct{ HitBsFaceOffMath } `json:"RTP11"`
}

type HitBsFaceOffMath struct {
    ID            string `json:"ID"`
    HitWeight     []int  `json:"HitWeight"`
    TriggerIconID int    `json:"TriggerIconID"`
    TriggerWeight []int  `json:"TriggerWeight"`
    Type          int    `json:"Type"`
}

type FsFaceOffMath struct {
    IconID   int
    IconPays []int
}
