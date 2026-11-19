//+build dev

package redis

import redigo "github.com/gomodule/redigo/redis"

func init() {
    // do nothing
}

func (r *repository) Conn(hostExtId string) redigo.Conn {
    return nil
}
