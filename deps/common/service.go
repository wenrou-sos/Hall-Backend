package common

import (
    "os"
    "strconv"
)

var Service = &service{
    ChanSize: 1024,
}

type service struct {
    ChanSize int
}

func init() {
    if v := os.Getenv("CHAN_SIZE"); v != "" {
        if atoiV, _ := strconv.Atoi(v); atoiV > 0 {
            Service.ChanSize = atoiV
        }
    }
}
