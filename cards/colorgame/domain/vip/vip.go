package vip

import "time"

// database table `auto_vip_member_info`
type VipMember struct {
	AutoVipType    int8   `gorm:"column:auto_vip_type"`
	EnforceVipType int8   `gorm:"column:enforce_vip_type"`
	LimitType      uint32 `gorm:"column:limit_type"`
	AllTotalBet    uint64
	AllTotalWin    uint64
	AllTotalTimes  uint64
	NowRtp         uint32 `gorm:"column:now_RTP"`
}

// database table `auto_vip_setting_new`
type VipSetting struct {
	UpperRtpLimit1   uint32 `gorm:"column:upper_RTP_limit1"`
	UpperRtpLimit2   uint32 `gorm:"column:upper_RTP_limit2"`
	UpperRtpLimit3   uint32 `gorm:"column:upper_RTP_limit3"`
	LowerRtpLimit    uint32 `gorm:"column:lower_RTP_limit"`
	JudgeCycle1      uint64 `gorm:"column:judge_cycle1"`
	JudgeCycle2      uint64 `gorm:"column:judge_cycle2"`
	JudgeCycle3      uint64 `gorm:"column:judge_cycle3"`
	LevelValue1      uint32 `gorm:"column:common_data1_level1"`
	LevelValue2      uint32 `gorm:"column:common_data1_level2"`
	LevelValue3      uint32 `gorm:"column:common_data1_level3"`
	NetwinRatio1     uint64 `gorm:"column:netwin_ratio1"`
	NetwinRatio2     uint64 `gorm:"column:netwin_ratio2"`
	NetwinRatio3     uint64 `gorm:"column:netwin_ratio3"`
	LogicalJudgment1 int8   `gorm:"column:logical_judgment1"`
	LogicalJudgment2 int8   `gorm:"column:logical_judgment2"`
	LogicalJudgment3 int8   `gorm:"column:logical_judgment3"`
	MaxTimes         uint64
}

// database table `auto_vip_currency_setting`
type CurrencySetting struct {
	BillCurrency string `gorm:"column:bill_currency"`
	Value        uint64
	Normalize    uint64
}

// database table `auto_vip_log`
type VipLog struct {
	Sn         uint64 `gorm:"PRIMARY_KEY;AUTO_INCREMENT"`
	HostId     string
	MemberId   string
	GameType   string
	VipType    int8
	EnterSn    uint64
	EnterBet   uint64
	EnterWin   uint64
	EnterTimes uint64
	EnterTime  time.Time
	LeaveSn    uint64
	LeaveBet   uint64
	LeaveWin   uint64
	LeaveTimes uint64
	LeaveTime  time.Time
	LogEnd     int8
}

type defaultVip struct {
	HostId   string
	MemberId string
	GameType string
}
