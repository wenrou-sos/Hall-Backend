package mysql

import (
    "errors"
    "fmt"
    "github.com/jinzhu/gorm"
    "gitlab.iplaystar.net/game-server/logger"
    "strings"
    "sync"
)

type repository struct {
    id            string
    host          string
    port          string
    user          string
    password      string
    dbName        string
    isPublicMySQL string
    isPublicRedis string
    hosts         map[string]*mysql
    dbs           map[string]*gorm.DB
    events        map[string]string
    rwMutex       sync.RWMutex
}

type hostGameDB struct {
    hostID    string // not used yet
    hostExtID string
    publicIP  string
    privateIP string
    port      string
    user      string
    password  string
    dbName    string
}

type hostEventDB struct {
    hostID    string // not used yet
    hostExtID string
    publicIP  string
    privateIP string
}

func (r *repository) Reload() {
    user := strings.Split(r.user, ",")
    password := strings.Split(r.password, ",")
    dbName := strings.Split(r.dbName, ",")

    if b := r.backstageDB(user[0], password[0], dbName[0]); b != nil {

        r.initHostMySQL(b, user[1], password[1], dbName[1])
        r.initHostRedis(b)

        b.Conn.Close()
    }
}

func (r *repository) backstageDB(user, password, dbName string) *mysql {
    r.rwMutex.RLock()
    defer r.rwMutex.RUnlock()

    var backstageDB *mysql

    if backstageDB = newMySQL(user, password, r.host, r.port, dbName, nil); backstageDB == nil {
        logger.Service.Zap.Errorw("Creating BackstageDB Connection Failed",
            "IP", r.host,
            "Name", dbName,
            "User", user,
            "Port", r.port,
            "PoolSize", len(r.dbs),
        )
        return nil
    }

    return backstageDB
}

func (r *repository) initHostMySQL(backstageDB *mysql, user, password, dbName string) {
    r.rwMutex.Lock()
    defer r.rwMutex.Unlock()

    if rows, err := backstageDB.Conn.
        Table("host_list").
        Select("host_list.host_ext_id, server_info.public_ip, server_info.private_ip").
        Joins("INNER JOIN server_info ON host_list.server_id = server_info.id").
        Rows(); err == nil {

        defer rows.Close()

        for rows.Next() {
            dbResult := &hostGameDB{
                port:     r.port,
                user:     user,
                password: password,
                dbName:   dbName,
            }

            if err := rows.Scan(&dbResult.hostExtID, &dbResult.publicIP, &dbResult.privateIP); err == nil {
                ip := dbResult.privateIP

                if r.isPublicMySQL == "true" {
                    ip = dbResult.publicIP
                }

                if conn, ok := r.dbs[ip]; ok {
                    if v := newMySQL(
                        dbResult.user,
                        dbResult.password,
                        ip,
                        dbResult.port,
                        dbResult.dbName,
                        conn,
                    ); v != nil {
                        r.hosts[dbResult.hostExtID] = v
                    }
                } else {
                    if v := newMySQL(
                        dbResult.user,
                        dbResult.password,
                        ip,
                        dbResult.port,
                        dbResult.dbName,
                        nil,
                    ); v != nil {
                        r.hosts[dbResult.hostExtID] = v
                        r.dbs[ip] = v.Conn
                    }
                }

                logger.Service.Zap.Infow("New MYSQL Connection",
                    "IP", ip,
                    "PublicIP", dbResult.publicIP,
                    "PrivateIP", dbResult.privateIP,
                    "HostExtId", dbResult.hostExtID,
                    "Name", dbResult.dbName,
                    "User", dbResult.user,
                    "Port", dbResult.port,
                    "PoolSize", len(r.dbs),
                )
            } else {
                logger.Service.Zap.Errorw("Get hostGameDB Rows Failed",
                    "PublicIP", dbResult.publicIP,
                    "PrivateIP", dbResult.privateIP,
                    "HostExtId", dbResult.hostExtID,
                    "Name", dbResult.dbName,
                    "User", dbResult.user,
                    "Port", dbResult.port,
                    "PoolSize", len(r.dbs),
                )
            }
        }
    }
}

func (r *repository) initHostRedis(backstageDB *mysql) {
    r.rwMutex.Lock()
    defer r.rwMutex.Unlock()

    if rows, err := backstageDB.Conn.
        Table("host_list").
        Select("host_list.host_ext_id, server_info.public_ip, server_info.private_ip").
        Joins("INNER JOIN server_info ON host_list.event_redis_server = server_info.id").
        Rows(); err == nil {

        defer rows.Close()

        for rows.Next() {
            dbResult := &hostEventDB{}

            if err := rows.Scan(&dbResult.hostExtID, &dbResult.publicIP, &dbResult.privateIP); err == nil {
                ip := dbResult.privateIP

                if r.isPublicRedis == "true" {
                    ip = dbResult.publicIP
                }

                r.events[dbResult.hostExtID] = ip

                logger.Service.Zap.Infow("New REDIS Connection",
                    "IP", ip,
                    "PublicIP", dbResult.publicIP,
                    "PrivateIP", dbResult.privateIP,
                    "HostExtId", dbResult.hostExtID,
                    "PoolSize", len(r.events),
                )
            } else {
                logger.Service.Zap.Errorw("Get hostEventDB Rows Failed",
                    "PublicIP", dbResult.publicIP,
                    "PrivateIP", dbResult.privateIP,
                    "HostExtId", dbResult.hostExtID,
                    "PoolSize", len(r.events),
                )
            }
        }
    }
}

func (r *repository) GameDBs() map[string]*gorm.DB {
    r.rwMutex.RLock()
    defer r.rwMutex.RUnlock()

    return r.dbs
}

func (r *repository) GameDB(hostExtId string) (db *gorm.DB, err error) {
    r.rwMutex.Lock()
    defer r.rwMutex.Unlock()

    if v, ok := r.hosts[hostExtId]; ok {
        if err := v.Conn.DB().Ping(); err == nil {
            return v.Conn, nil
        } else {
            logger.Service.Zap.Warnw("GameDB Connection Ping Failed",
                "HostExtId", hostExtId,
                "Error", err,
            )
        }

        if v.retry() {
            r.dbs[v.host] = v.Conn
            return v.Conn, nil
        }

        v.Conn.Close()
    }
    return nil, errors.New(fmt.Sprintf("HostExtId %s GameDB connection not found", hostExtId))
}

func (r *repository) EventDBs() map[string]string {
    r.rwMutex.RLock()
    defer r.rwMutex.RUnlock()

    return r.events
}

func (r *repository) Destroy() {
    r.rwMutex.Lock()
    defer r.rwMutex.Unlock()

    for k := range r.hosts {
        delete(r.hosts, k)
    }

    for k, v := range r.dbs {
        v.Close()
        delete(r.dbs, k)
    }
}
