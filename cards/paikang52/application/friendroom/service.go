package friendroom

import (
    "crypto/rand"
    "math/big"
    "strconv"
    "sync"
)

var Service = &service{
    id:          "FriendRoomService",
    friendRooms: sync.Map{},
}

type service struct {
    id          string
    friendRooms sync.Map
}

func (s *service) Create(f *friendRoom) *friendRoom {
    s.friendRooms.Store(f.secWebSocketKey, f)
    return f
}

func (s *service) Get(secWebSocketKey string) *friendRoom {
    if v, ok := s.friendRooms.Load(secWebSocketKey); ok {
        return v.(*friendRoom)
    }
    return nil
}

func (s *service) Delete(secWebSocketKey string) {
    if v, ok := s.friendRooms.Load(secWebSocketKey); ok {
        s.friendRooms.Delete(secWebSocketKey)
        v.(*friendRoom).destroy()
    }
}

func (s *service) rngNumber(digital int) int32 {
    min := 1
    max := 9

    temp := ""

    for i := 0; i < digital; i++ {

        n, err := rand.Int(rand.Reader, big.NewInt(int64(max-min+1)))

        if err != nil {
            panic(err)
        }

        temp += strconv.FormatUint(n.Uint64()+uint64(min), 10)
    }

    number, _ := strconv.ParseUint(temp, 10, 32)

    return int32(number)
}
