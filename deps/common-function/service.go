package Common_Function

import (
	"math/rand"
	"time"
)

var Service = &service{
	Id: "CommonFunctionService",
}

type service struct {
	Id string
}

func (s *service) RngBotName() (name string) {
	rand.Seed(time.Now().UnixNano())
	return BotName[rand.Intn(len(BotName))]
}
