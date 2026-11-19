package friendroom

import (
	"encoding/json"

	redigo "github.com/gomodule/redigo/redis"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/redis"
)

const (
	PLAYER = "PLAYER"
	BOT    = "BOT"
	BANKER = "BANKER"
)

// redis.call("HLEN", KEYS[1]) - 1 excluded HASH_ID
const sizeScript = `
return redis.call("HLEN", KEYS[1]) - 1
`

const infoScript = `
return redis.call("HGET", KEYS[1], ARGV[1])
`

const updatePlayerScript = `
redis.call("HSET", KEYS[1], ARGV[1], ARGV[2])
`

var Player = &player{}

type player struct {
	ServerId  string `json:"ServerId"`
	RoomUuid  string `json:"RoomUuid"`
	Uid       string `json:"Uid"`
	Name      string `json:"Name"`
	Avatar    string `json:"Avatar"`
	Kind      string `json:"Kind"`
	IpAddress string `json:"IpAddress"`
	Balance   uint64 `json:"Balance"`
	IsHost    bool   `json:"IsHost"`
	WinCount  uint32 `json:"WinCount"`
}

func (p *player) size(hostExtId string, number int32) int32 {
	conn := redis.Repository.Conn(hostExtId)

	defer conn.Close()

	v, _ := redigo.Int64(redigo.NewScript(1, sizeScript).Do(conn, number))

	logger.Service.Zap.Infow("Friend Room Redis Player Size",
		"HostExtId", hostExtId,
		"Number", number,
		"Size", v,
	)

	return int32(v)
}

func (p *player) info(hostExtId string, number, seat int32) *player {
	conn := redis.Repository.Conn(hostExtId)

	defer conn.Close()

	field := ""

	switch seat {
	case 0:
		field = "SEAT0"

	case 1:
		field = "SEAT1"

	case 2:
		field = "SEAT2"

	case 3:
		field = "SEAT3"

	case 4:
		field = "SEAT4"

	case 5:
		field = "SEAT5"

	default:
		panic("ERROR SEAT")
	}

	v, _ := redigo.Bytes(redigo.NewScript(1, infoScript).Do(conn, number, field))

	if v != nil {
		p := &player{}

		json.Unmarshal(v, p)

		logger.Service.Zap.Infow("Friend Room Redis Player Info",
			"HostExtId", hostExtId,
			"Number", number,
			"Seat", seat,
			"Field", field,
			"Player", p,
		)
		return p
	}
	return nil
}

func (p *player) update(hostExtId string, number, seat int32, player *player) {
	conn := redis.Repository.Conn(hostExtId)

	defer conn.Close()

	field := ""

	switch seat {
	case 0:
		field = "SEAT0"

	case 1:
		field = "SEAT1"

	case 2:
		field = "SEAT2"

	case 3:
		field = "SEAT3"

	case 4:
		field = "SEAT4"

	case 5:
		field = "SEAT5"

	default:
		panic("ERROR SEAT")
	}

	dataByte, _ := json.Marshal(player)

	v, _ := redigo.NewScript(1, updatePlayerScript).Do(conn, number, field, string(dataByte))

	logger.Service.Zap.Infow("Friend Room Redis Player Info Update",
		"HostExtId", hostExtId,
		"Key", number,
		"Field", field,
		"Player", Player,
		"Result", v,
	)
}
