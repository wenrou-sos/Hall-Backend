package friendroom

import (
	"encoding/json"

	redigo "github.com/gomodule/redigo/redis"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/redis"
)

const (
	IDLE   = "IDLE"
	GAMING = "GAMING"
)

const getRoomScript = `
  local hashId = redis.call("HGET", ARGV[1], "HASH_ID")
  return redis.call("HGET", hashId, ARGV[1])
`

const updateRoomScript = `
  return redis.call("HSET", KEYS[1], ARGV[1], ARGV[2])
`

var Room = &room{}

type room struct {
	Uuid         string `json:"Uuid"`
	BankerUuid   string `json:"BankerUuid"`
	HostServerId string `json:"HostServerId"`
	Number       int32  `json:"Number"`
	SubGameId    uint32 `json:"SubGameId"`
	Size         int32  `json:"Size"`
	Status       string `json:"Status"`
	HostExtId    string `json:"HostExtId"`
	IpConfig     uint32 `json:"IpConfig"`
}

func (r *room) info(hostExtId string, number int32) *room {
	conn := redis.Repository.Conn(hostExtId)

	defer conn.Close()

	v, _ := redigo.Bytes(redigo.NewScript(0, getRoomScript).Do(conn, number))

	if len(v) == 0 {
		return nil
	}

	data := &room{}

	json.Unmarshal(v, data)

	logger.Service.Zap.Infow("Friend Room Redis Room Info",
		"HostExtId", hostExtId,
		"Number", number,
		"Room", data,
		"Result", data,
	)

	return data
}

func (r *room) update(hostExtId, key string, room *room) {
	conn := redis.Repository.Conn(hostExtId)

	defer conn.Close()

	dataByte, _ := json.Marshal(room)

	v, _ := redigo.NewScript(1, updateRoomScript).Do(conn, key, room.Number, string(dataByte))

	logger.Service.Zap.Infow("Friend Room Redis Room Info Update",
		"HostExtId", hostExtId,
		"Key", key,
		"Room", room,
		"Result", v,
	)
}
