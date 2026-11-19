package Version

import (
	"encoding/json"
	"net/http"
	"os"
)

type version struct {
	Rev string `json:"rev"`
}

const (
	ServiceId       = "VersionService"
	VersionPort     = "VERSION_PORT"
	Version         = "VERSION"
	ApplicationJson = "application/json"
	ContentType     = "Content-Type"
	GetMethod       = "GET"
	VersionPath     = "/fish/version"
)

func getVersion(w http.ResponseWriter, r *http.Request) {
	version := &version{
		Rev: os.Getenv(Version),
	}

	data, _ := json.Marshal(version)
	w.Header().Set(ContentType, ApplicationJson)
	w.Write(data)
}
