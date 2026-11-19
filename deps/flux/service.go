package flux

func Start(h IHandler) {
    Dispatcher.iHandler = h
}

func Register(id string, in chan *Action) {
    Dispatcher.register <- newFlux(id, in)
}

func UnRegister(id string, in chan *Action) {
    Dispatcher.unRegister <- newFlux(id, in)
}

func Send(key, from, to string, payload ...interface{}) {
    Dispatcher.send <- newAction(newName(key, from, to), payload)
}

func NewAction(key, from, to string, payload ...interface{}) *Action {
    return newAction(newName(key, from, to), payload)
}
