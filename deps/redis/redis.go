package redis

import (
    redigo "github.com/gomodule/redigo/redis"
    "gitlab.iplaystar.net/game-server/logger"
    "time"
)

func Builder() *builder {
    return &builder{
        addr:      "",
        port:      "6379",
        password:  "",
        hostExtId: "",
        dbIndex:   0,
    }
}

type builder struct {
    addr      string
    port      string
    password  string
    hostExtId string
    dbIndex   uint8
}

type redis struct {
    addr      string
    port      string
    password  string
    hostExtId string
    dbIndex   uint8
    pool      *redigo.Pool
}

func (b *builder) SetAddr(addr string) *builder {
    b.addr = addr
    return b
}

func (b *builder) SetPort(port string) *builder {
    if port != "" {
        b.port = port
    }
    return b
}

func (b *builder) SetPassword(password string) *builder {
    b.password = password
    return b
}

func (b *builder) SetHostExtId(hostExtId string) *builder {
    b.hostExtId = hostExtId
    return b
}

func (b *builder) SetDBIndex(index uint8) *builder {
    b.dbIndex = index
    return b
}

func (b *builder) Build() *redis {
    return &redis{
        addr:      b.addr,
        port:      b.port,
        password:  b.password,
        hostExtId: b.hostExtId,
        dbIndex:   b.dbIndex,
        pool: &redigo.Pool{
            MaxIdle:     3,
            IdleTimeout: 60 * time.Second,
            Dial: func() (redigo.Conn, error) {

                c, err := redigo.Dial("tcp", b.addr+":"+b.port)

                if err != nil {
                    logger.Service.Zap.Errorw("Dial REDIS Failed",
                        "IP", b.addr,
                        "Port", b.port,
                        "Error", err,
                    )
                    return nil, err
                }

                if b.password != "" {
                    if _, err := c.Do("AUTH", b.password); err != nil {
                        c.Close()
                        logger.Service.Zap.Errorw("Auth REDIS Failed",
                            "IP", b.addr,
                            "Port", b.port,
                            "Error", err,
                            "Password", b.password,
                        )
                        return nil, err
                    }
                }

                if _, err := c.Do("SELECT", b.dbIndex); err != nil {
                    c.Close()
                    logger.Service.Zap.Errorw("Select REDIS DB Failed",
                        "IP", b.addr,
                        "Port", b.port,
                        "Index", b.dbIndex,
                        "Error", err,
                    )
                    return nil, err
                }
                return c, nil
            },

            TestOnBorrow: func(c redigo.Conn, t time.Time) error {
                if time.Since(t) < time.Second {
                    return nil
                }
                _, err := c.Do("PING")
                return err
            },
        },
    }
}
