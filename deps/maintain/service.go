package maintain

const (
	Card = "host_89_game"
	Fish = "host_fish_game"

	Dev_Test_Open = "MAINTAIN_OPEN"
)

var Service = &service{
	Id: "Maintain",
}

type service struct {
	Id string
}
