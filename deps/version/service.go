package Version

import (
	"github.com/gorilla/mux"
	"gitlab.iplaystar.net/game-server/logger"
	"net/http"
	"os"
	"strconv"
)

var Service = &service{
	Id: ServiceId,
}

type service struct {
	Id string
}

func (s *service) Start() {
	versionPort := os.Getenv(VersionPort)

	if versionPort != "" {
		if _, err := strconv.Atoi(versionPort); err == nil {
			go s.run(versionPort, VersionPath)
			logger.Service.Zap.Infow("Service created", "Service", Service.Id, "port", versionPort)
		} else {
			logger.Service.Zap.Infow("Service creat failed, port isn't number", "Service", Service.Id, "port", versionPort)
		}
	} else {
		logger.Service.Zap.Infow("Service creat failed, port is null", "Service", Service.Id, "port", versionPort)
	}
}

func (s *service) run(port string, path string) {
	r := mux.NewRouter()
	r.HandleFunc(path, getVersion).Methods(GetMethod)

	http.ListenAndServe(":"+port, r)
}
