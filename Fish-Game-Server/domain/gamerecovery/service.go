package gamerecovery

var Service = &service{
    id:           "GameRecoveryService",
    gameRecovery: make(map[string]*gameRecovery),
}

type service struct {
    id           string
    gameRecovery map[string]*gameRecovery
}
