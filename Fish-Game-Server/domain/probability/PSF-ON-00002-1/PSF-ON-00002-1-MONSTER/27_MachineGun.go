package PSF_ON_00002_1_MONSTER

import (
    "gitlab.iplaystar.net/game-server/rng"
    "os"
    "strings"
)

var MachineGun = &machineGun{
    bonusMode:      strings.Contains(os.Getenv("ENABLED_BONUS"), "27"),
    extraBonusMode: strings.Contains(os.Getenv("ENABLED_BONUS"), "31"),
}

type machineGun struct {
    bonusMode      bool
    extraBonusMode bool
}

type BsMachineGunMath struct {
    IconID           int
    BonusID          string
    BonusTimes       []int
    BonusTimesWeight []int
    BonusIconID      []int
    IconPays         []int
    RTP1             struct{ HitBsMachineGunMath } `json:"RTP1"`
    RTP2             struct{ HitBsMachineGunMath } `json:"RTP2"`
    RTP3             struct{ HitBsMachineGunMath } `json:"RTP3"`
    RTP4             struct{ HitBsMachineGunMath } `json:"RTP4"`
    RTP5             struct{ HitBsMachineGunMath } `json:"RTP5"`
    RTP6             struct{ HitBsMachineGunMath } `json:"RTP6"`
    RTP7             struct{ HitBsMachineGunMath } `json:"RTP7"`
    RTP8             struct{ HitBsMachineGunMath } `json:"RTP8"`
    RTP9             struct{ HitBsMachineGunMath } `json:"RTP9"`
    RTP10            struct{ HitBsMachineGunMath } `json:"RTP10"`
    RTP11            struct{ HitBsMachineGunMath } `json:"RTP11"`
}

type HitBsMachineGunMath struct {
    ID            string `json:"ID"`
    HitWeight     []int  `json:"HitWeight"`
    TriggerIconID int    `json:"TriggerIconID"`
    TriggerWeight []int  `json:"TriggerWeight"`
    Type          int    `json:"Type"`
}

func (m *machineGun) pick(math *BsMachineGunMath) int {
    bonusTimes := make([]rng.Option, 0, 6)

    for i := 0; i < len(math.BonusTimesWeight); i++ {
        bonusTimes = append(bonusTimes, rng.Option{math.BonusTimesWeight[i], math.BonusTimes[i]})
    }

    return MONSTER.rng(bonusTimes).(int)
}
