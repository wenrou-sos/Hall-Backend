package friendroom

import (
    "encoding/json"
    redigo "github.com/gomodule/redigo/redis"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/redis"
)

var Create = &create{
}

const createScript = `
if redis.call("HGET", KEYS[1], ARGV[1]) then
  redis.call("HDEL", ARGV[1], "HASH_ID")
  redis.call("HDEL", KEYS[1], ARGV[1])
  redis.call("HSET", ARGV[1], "HASH_ID", KEYS[1])
  return redis.call("HSET", KEYS[1], ARGV[1], ARGV[2])
else
  redis.call("HSET", ARGV[1], "HASH_ID", KEYS[1])
  return redis.call("HSET", KEYS[1], ARGV[1], ARGV[2])
end
`

type create struct {
}

func (c *create) do(hostExtId, key string, r *room) bool {
    conn := redis.Repository.Conn(hostExtId)

    defer conn.Close()

    dataByte, _ := json.Marshal(r)

    v, _ := redigo.NewScript(1, createScript).Do(conn, key, r.Number, string(dataByte))

    logger.Service.Zap.Infow("Friend Room Redis Create",
        "HostExtId", hostExtId,
        "Key", key,
        "Room", r,
        "Result", v,
    )

    return v != nil
}
