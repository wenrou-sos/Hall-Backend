//+build staging prod

package mysql

import (
    "github.com/jinzhu/gorm"
    "gitlab.iplaystar.net/game-server/logger"
    "os"
    "sync"
)

var Repository = &repository{
    id:            "MysqlRepository",
    host:          os.Getenv("MYSQL_HOST"),
    port:          os.Getenv("MYSQL_PORT"),
    user:          os.Getenv("MYSQL_USER"),
    password:      os.Getenv("MYSQL_PASSWORD"),
    dbName:        os.Getenv("MYSQL_DATABASE"),
    isPublicMySQL: os.Getenv("MYSQL_PUBLIC"),
    isPublicRedis: os.Getenv("REDIS_PUBLIC"),
    hosts:         make(map[string]*mysql),
    dbs:           make(map[string]*gorm.DB),
    events:        make(map[string]string),
    rwMutex:       sync.RWMutex{},
}

func init() {
    logger.Service.Zap.Infow("Service Created",
        "Service", Repository.id,
    )
    Repository.Reload()
}
