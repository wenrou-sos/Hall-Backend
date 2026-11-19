package refund

import "gitlab.iplaystar.net/game-server/flux"

func psf_on_00007_init(action *flux.Action, allRefund map[string]*refund) {
	psf_on_00001_init(action, allRefund)
}