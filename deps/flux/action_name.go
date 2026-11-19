package flux

type Name struct {
    name string
    from string
    to   string
}

func newName(name, from, to string) *Name {
    return &Name{
        name: name,
        from: from,
        to:   to,
    }
}

func (n *Name) Name() string {
    return n.name
}

func (n *Name) From() string {
    return n.from
}

func (n *Name) To() string {
    return n.to
}
