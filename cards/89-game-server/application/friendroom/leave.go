package friendroom

import (
    redigo "github.com/gomodule/redigo/redis"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/redis"
)

// redis.call("HLEN", KEYS[2]) == 1 included HASH_ID
const leaveScript = `
redis.call("HDEL", KEYS[2], ARGV[1])

if ARGV[1] == "SEAT0" then
  redis.call("HDEL", KEYS[1], KEYS[2])
  redis.call("HDEL", KEYS[2], "SEAT1")
  redis.call("HDEL", KEYS[2], "SEAT2")
  redis.call("HDEL", KEYS[2], "SEAT3")
  redis.call("HDEL", KEYS[2], "SEAT4")
  redis.call("HDEL", KEYS[2], "SEAT5")
  redis.call("HDEL", KEYS[2], "HASH_ID")
  return 2
end

return 1
`

var Leave = &leave{
}

type leave struct {
}

func (l *leave) do(hostExtId, hashId string, number, seat int32) (status int32) {
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

    v, _ := redigo.Int64(redigo.NewScript(2, leaveScript).Do(conn, hashId, number, field))

    logger.Service.Zap.Infow("Friend Room Redis Leave",
        "HostExtId", hostExtId,
        "HashId", hashId,
        "Number", number,
        "Seat", seat,
        "Field", field,
        "Result", v,
    )

    return int32(v)
}
