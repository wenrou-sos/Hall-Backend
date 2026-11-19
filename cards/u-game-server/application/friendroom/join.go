package friendroom

import (
	"encoding/json"

	redigo "github.com/gomodule/redigo/redis"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/redis"
)

const joinScript = `
if redis.call("HGET", KEYS[1], "SEAT5") and ARGV[2] == "BANKER" then
  return -1
end

if not redis.call("HGET", KEYS[1], "SEAT5") and ARGV[2] == "BANKER" then
  redis.call("HSET", KEYS[1], "SEAT5", ARGV[1])
  return 5
end

if not redis.call("HGET", KEYS[1], "SEAT0") and ARGV[2] == "PLAYER" then
  redis.call("HSET", KEYS[1], "SEAT0", ARGV[1])
  return 0
end

if not redis.call("HGET", KEYS[1], "SEAT1") and ARGV[2] == "PLAYER" then
  redis.call("HSET", KEYS[1], "SEAT1", ARGV[1])
  return 1
end

if not redis.call("HGET", KEYS[1], "SEAT2") and ARGV[2] == "PLAYER" then
  redis.call("HSET", KEYS[1], "SEAT2", ARGV[1])
  return 2
end

if not redis.call("HGET", KEYS[1], "SEAT3") and ARGV[2] == "PLAYER" then
  redis.call("HSET", KEYS[1], "SEAT3", ARGV[1])
  return 3
end

if not redis.call("HGET", KEYS[1], "SEAT4") and ARGV[2] == "PLAYER" then
  redis.call("HSET", KEYS[1], "SEAT4", ARGV[1])
  return 4
end

return -1
`

var Join = &join{}

type join struct {
}

func (j *join) do(hostExtId string, key int32, p *player) (seat int32) {
	conn := redis.Repository.Conn(hostExtId)

	defer conn.Close()

	dataByte, _ := json.Marshal(p)

	v, _ := redigo.Int64(redigo.NewScript(1, joinScript).Do(conn, key, string(dataByte), p.Kind))

	logger.Service.Zap.Infow("Friend Room Redis Join",
		"HostExtId", hostExtId,
		"Key", key,
		"Player", p,
		"Result", v,
	)

	return int32(v)
}
