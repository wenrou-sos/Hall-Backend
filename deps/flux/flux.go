package flux

type flux struct {
    id string
    in chan *Action
}

func newFlux(id string, in chan *Action) *flux {
    return &flux{
        id: id,
        in: in,
    }
}
