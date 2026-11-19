package PSF_ON_00003_1_RTP

import (
	PSF_ON_00003_1 "fish-game-server/domain/probability/PSF-ON-00003-1"
	"reflect"
)

func (s *service) RngRtp(state int, drbMathI interface{}) (rtpState int, rtpId string, bullets uint64, netWinGroup int) {
	drbMath := reflect.ValueOf(drbMathI).Interface().(*PSF_ON_00003_1.DrbMath)

	rtpState = s.rngWinLoss(state, drbMath)
	netWinOrLoss := s.rngWinLossLevel(rtpState, drbMath)
	rtpId, bullets = s.getBullet(rtpState, netWinOrLoss, drbMath)

	return rtpState, rtpId, bullets, netWinOrLoss
}