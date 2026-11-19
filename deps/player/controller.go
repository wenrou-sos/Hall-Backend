package player

import (
    "fmt"
    fastHttpWebsocket "github.com/fasthttp/websocket"
    gorillaWebsocket "github.com/gorilla/websocket"
    "github.com/valyala/fasthttp"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "net/http"
    "os"
    "strconv"
    "time"
)

const (
    bufferSize = 8192
    timeout    = 60 * time.Second
)

var Controller = &controller{
    Id: "PlayerController",
    GorillaUpgrader: &gorillaWebsocket.Upgrader{
        HandshakeTimeout:  timeout,
        ReadBufferSize:    bufferSize,
        WriteBufferSize:   bufferSize,
        WriteBufferPool:   newBufferPool(),
        CheckOrigin:       func(req *http.Request) bool { return true },
        EnableCompression: true,
    },
    FastHttpUpgrader: &fastHttpWebsocket.FastHTTPUpgrader{
        HandshakeTimeout:  timeout,
        ReadBufferSize:    bufferSize,
        WriteBufferSize:   bufferSize,
        WriteBufferPool:   newBufferPool(),
        CheckOrigin:       func(ctx *fasthttp.RequestCtx) bool { return true },
        EnableCompression: true,
    },
    poolSize: os.Getenv("POOL_SIZE"),
    in:       make(chan *flux.Action, 1024),
}

type controller struct {
    Id               string
    GorillaUpgrader  *gorillaWebsocket.Upgrader
    FastHttpUpgrader *fastHttpWebsocket.FastHTTPUpgrader
    poolSize         string
    in               chan *flux.Action
}

type IHandler interface {
    FluxActionHandler(action *flux.Action)
    HttpHandler(res http.ResponseWriter, req *http.Request)
    FastHttpHandler(ctx *fasthttp.RequestCtx)
    ServeHandler(h IHandler)
}

func (c *controller) Start(h IHandler) {
    go c.run(h)

    time.Sleep(500 * time.Millisecond)

    h.ServeHandler(h)
}

func (c *controller) run(h IHandler) {
    flux.Register(c.Id, c.in)

    logger.Service.Zap.Infow("Controller Running",
        "Controller", c.Id,
        "Chan", fmt.Sprintf("%p", c.in),
    )

    poolSize := 10

    if c.poolSize != "" {
        if poolSize, _ = strconv.Atoi(c.poolSize); poolSize == 0 {
            poolSize = 10
        }
    }

    for i := 0; i < poolSize*10; i++ {
        go func() {
            for action := range c.in {
                h.FluxActionHandler(action)
            }
        }()
    }
}

func (c *controller) Destroy() {
    flux.UnRegister(c.Id, c.in)
}
