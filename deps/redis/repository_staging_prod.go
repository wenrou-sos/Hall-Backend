//+build staging prod

package redis

import (
    redigo "github.com/gomodule/redigo/redis"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
)

func init() {
    logger.Service.Zap.Infow("Service Created",
        "Service", Repository.Id,
    )

    for k, v := range mysql.Repository.EventDBs() {
        Repository.New(
            Builder().
                SetAddr(v).
                SetPort(Repository.Port).
                SetPassword(Repository.Password).
                SetHostExtId(k).
                Build(),
        )
    }
}

func (r *repository) Conn(hostExtId string) redigo.Conn {
    if v, ok := r.redis[hostExtId]; ok {
        return v.pool.Get()
    }
    return nil
}
