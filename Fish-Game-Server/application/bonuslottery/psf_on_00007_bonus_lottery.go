package bonuslottery

import "gitlab.iplaystar.net/game-server/flux"

func psf_on_00007_RedEnvelope(action *flux.Action, depositMultiple uint64) {
	psf_on_00001_RedEnvelope(action, depositMultiple)
}

func psf_on_00007_Slot(action *flux.Action, depositMultiple uint64) {
	psf_on_00001_Slot(action, depositMultiple)
}