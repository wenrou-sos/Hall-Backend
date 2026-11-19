package redis

import "os"

var Repository = &repository{
    Id:       "RedisRepository",
    Port:     os.Getenv("REDIS_PORT"),
    Password: os.Getenv("REDIS_PASSWORD"),
    redis:    make(map[string]*redis),
}

type repository struct {
    Id       string
    Port     string
    Password string
    redis    map[string]*redis
}

func (r *repository) New(rs *redis) *redis {
    // TODO JOHNNY  changed to sync.map
    if rs != nil {
        r.redis[rs.hostExtId] = rs
        return rs
    }
    return nil
}
