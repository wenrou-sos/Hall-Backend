package playerinfo

import "sync"

type Key struct {
	HostId   string
	MemberId string
}

type PlayerInfo struct {
	SecWebSocketKey string
}

type service struct {
	playerInfos map[Key]*PlayerInfo
	rwMutex     *sync.RWMutex
}

var Service = service{
	playerInfos: map[Key]*PlayerInfo{},
	rwMutex:     &sync.RWMutex{},
}

func (s *service) GetOrCreate(hostId, memberId, secWebSocketKey string) *PlayerInfo {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if p, ok := s.playerInfos[Key{hostId, memberId}]; ok {
		return p
	}

	s.playerInfos[Key{hostId, memberId}] = &PlayerInfo{
		SecWebSocketKey: secWebSocketKey,
	}
	return nil
}

func (s *service) Delete(hostId, memberId string) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	delete(s.playerInfos, Key{hostId, memberId})
}
