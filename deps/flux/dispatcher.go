package flux

import (
    "fmt"
    "log"
    "os"
    "strconv"
    "sync"
)

const (
    ActionFluxRegisterDone = "ActionFluxRegisterDone"
)

var Dispatcher = &dispatcher{
    id:         "FluxDispatcher",
    register:   make(chan *flux, 1024),
    unRegister: make(chan *flux, 1024),
    send:       make(chan *Action, 102400),
    poolSize:   os.Getenv("POOL_SIZE"),
    iHandler:   nil,
    starLog:    " ******************************** ",
    rwMutex:    &sync.RWMutex{},
}

type dispatcher struct {
    id         string
    register   chan *flux
    unRegister chan *flux
    send       chan *Action
    poolSize   string
    iHandler   IHandler
    starLog    string
    rwMutex    *sync.RWMutex
}

type IHandler interface {
    Print(...interface{})
}

func init() {
    inGroup := make(map[string]map[chan *Action]string)

    poolSize := 10

    if Dispatcher.poolSize != "" {
        if poolSize, _ = strconv.Atoi(Dispatcher.poolSize); poolSize == 0 {
            poolSize = 10
        }
    }

    for i := 0; i < poolSize; i++ {
        go Dispatcher.run(inGroup)
        log.Println("Library - Start Flux OK...Pool", i)
    }
}

func (d *dispatcher) run(inGroup map[string]map[chan *Action]string) {
    for {
        select {
        case flux := <-d.register:
            d.rwMutex.Lock()

            if _, ok := inGroup[flux.id]; ok {
                ins := inGroup[flux.id]
                ins[flux.in] = flux.id
            } else {
                ins := make(map[chan *Action]string)
                ins[flux.in] = flux.id
                inGroup[flux.id] = ins
            }

            flux.in <- newAction(newName(ActionFluxRegisterDone, d.id, flux.id), []interface{}{flux.id})
            d.rwMutex.Unlock()

        case flux := <-d.unRegister:
            d.rwMutex.Lock()

            if _, ok := inGroup[flux.id]; ok {
                ins := inGroup[flux.id]
                delete(ins, flux.in)
                close(flux.in)
                flux.in = nil
            } else {
                if d.iHandler != nil {
                    d.iHandler.Print(
                        fmt.Sprintf(
                            d.starLog+"FLUX Pool Delete Not Found"+d.starLog+"%s",
                            flux.id,
                        ),
                    )
                } else {
                    log.Println(
                        d.starLog+"FLUX Pool Delete Not Found"+d.starLog,
                        flux.id,
                    )
                }
            }
            d.rwMutex.Unlock()

        case action := <-d.send:
            d.rwMutex.RLock()

            if _, ok := inGroup[action.Key().To()]; ok {
                for in := range inGroup[action.Key().To()] {
                    in <- action

                    if len(in) > 10 {
                        if d.iHandler != nil {
                            d.iHandler.Print(
                                fmt.Sprintf(
                                    d.starLog+"FLUX Pool Status"+d.starLog+"%s %s %p %d %d %s",
                                    action.Key().From(),
                                    action.Key().To(),
                                    in,
                                    len(in),
                                    cap(in),
                                    action.Key().Name(),
                                ),
                            )
                        } else {
                            log.Println(
                                d.starLog+"FLUX Pool Status"+d.starLog,
                                action.Key().From(),
                                action.Key().To(),
                                in,
                                len(in),
                                cap(in),
                                action.Key().Name(),
                            )
                        }
                    }

                    if len(in) == cap(in) {
                        if d.iHandler != nil {
                            d.iHandler.Print("FLUX CHAN is Full")
                        }
                        panic("FLUX CHAN is Full")
                    }
                }
            } else {
                if d.iHandler != nil {
                    d.iHandler.Print(
                        fmt.Sprintf(
                            d.starLog+"FLUX Pool Send Not Found"+d.starLog+"%s %s %s",
                            action.Key().From(),
                            action.Key().To(),
                            action.Key(),
                        ),
                    )
                } else {
                    log.Println(
                        d.starLog+"FLUX Pool Send Not Found"+d.starLog,
                        action.Key().From(),
                        action.Key().To(),
                        action.Key(),
                    )
                }
            }
            d.rwMutex.RUnlock()
        }
    }
}
