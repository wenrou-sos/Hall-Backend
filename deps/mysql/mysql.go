package mysql

import (
    "fmt"
    "github.com/jinzhu/gorm"
    _ "github.com/jinzhu/gorm/dialects/mysql"
    "gitlab.iplaystar.net/game-server/logger"
    "os"
    "time"
)

type mysql struct {
    user     string
    password string
    host     string
    port     string
    dbName   string
    timeout  string
    Conn     *gorm.DB
}

func newMySQL(user, password, host, port, dbName string, conn *gorm.DB) *mysql {
    m := &mysql{
        user:     user,
        password: password,
        host:     host,
        port:     port,
        dbName:   dbName,
        timeout:  os.Getenv("MYSQL_TIMEOUT"),
        Conn:     conn,
    }

    // default timeout 2s
    if m.timeout == "" {
        m.timeout = "2"
    }

    // used existed db connection
    if conn != nil {
        return m
    }

    // created new db connection
    if v := m.connect(); v != nil {
        m.Conn = v
        return m
    }
    return nil
}

func (m *mysql) connect() *gorm.DB {
    db, err := gorm.Open(
        "mysql",
        fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4&timeout=%ss",
            m.user, m.password, m.host, m.port, m.dbName, m.timeout),
    )

    if err != nil {
        logger.Service.Zap.Errorw("Creating MYSQL Connection Failed",
            "IP", m.host,
            "Name", m.dbName,
            "User", m.user,
            "Port", m.port,
            "Error", err,
        )

        db.Close()
        return nil
    }

    db.LogMode(true)

    db.SetLogger(logger.Service)

    db.SingularTable(true)

    // SetMaxIdleConns sets the maximum number of connections in the idle connection pool.
    db.DB().SetMaxIdleConns(8)

    // SetMaxOpenConns sets the maximum number of open connections to the database.
    db.DB().SetMaxOpenConns(32)

    // SetConnMaxLifetime sets the maximum amount of time a connection may be reused.
    db.DB().SetConnMaxLifetime(time.Hour)
    return db
}

func (m *mysql) retry() bool {
    ok := false

    for i := 0; i < 10; i++ {
        if v := m.connect(); v != nil {
            m.Conn = v
            ok = true
            break
        }
    }
    return ok
}
