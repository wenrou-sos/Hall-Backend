package flux

type Action struct {
    key     *Name
    payload interface{}
}

func newAction(name *Name, payload interface{}) *Action {
    return &Action{
        key:     name,
        payload: payload,
    }
}

func (a *Action) Key() *Name {
    return a.key
}

func (a *Action) Payload() []interface{} {
    return a.payload.([]interface{})
}
