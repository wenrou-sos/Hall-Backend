package jackpot_client

import (
	"fmt"
	"github.com/gogo/protobuf/proto"
	"github.com/gorilla/websocket"
	"gitlab.iplaystar.net/game-server/flux"
	jackpot_proto "gitlab.iplaystar.net/game-server/jackpot-client/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"math"
	"net/url"
	"strconv"
	"sync"
	"time"
)

const (
	writeWait      = 10 * time.Second
	pongWait       = 20 * time.Second
	pingPeriod     = (pongWait * 1) / 10
	maxMessageSize = 1024 * 1024

	actionSync           = "actionSync"
	actionSendClientInfo = "actionSendClientInfo"
)

type mysteryJackpotClient struct {
	accountingSnMap map[string]uint64
	totalBetMap     map[string]uint64
	scheme          string
	host            string
	port            string
	useSSL          bool
	path            string
	conn            *websocket.Conn
	hitInfo         map[uint64]*jackpot_proto.HitInfo
	poolInfoMaps	map[int32]*jackpot_proto.PoolInfoMap
	clientInfoMap   *jackpot_proto.ClientInfoMap
	hasSynced       bool
	reconnect       bool
	connected       bool
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
	contributeMutex *sync.RWMutex
	iJackpot        IJackpot
}

func (m *mysteryJackpotClient) run() {
	flux.Register(Service.HashId(JackpotType_MYS), m.in)

	go m.handleConnection()

	ticker := time.NewTicker(3 * time.Second)

	for {
		m.rwMutex.Lock()

		if m.connected {
			select {
			case <-ticker.C:
				m.contributeMutex.Lock()

				if len(m.clientInfoMap.Map) > 0 {
					m.clientInfoMap.MessageId = jackpot_proto.MessageID_kClientInfoMap
					m.clientInfoMap.GameServerId = Service.Id
					//m.clientInfoMap.GameServerId = sessionmanager.Service.ServerId

					dataBuffer, _ := proto.Marshal(m.clientInfoMap)
					flux.Send(actionSendClientInfo, Service.HashId(JackpotType_MYS), Service.HashId(JackpotType_MYS), dataBuffer)

					for v, _ := range m.clientInfoMap.Map {
						delete(m.clientInfoMap.Map, v)
					}
				}

				m.contributeMutex.Unlock()
			default:
				for jackpotSn, hitInfo := range m.hitInfo {
					if v := m.accountingSnMap[hitInfo.ClientInfo.SessionId]; v != 0 {
						m.iJackpot.OnJackpotHit(hitInfo, v, JackpotType_MYS)
						delete(m.hitInfo, jackpotSn)
					} else {
						logger.Service.Zap.Warnw("Jackpot Hit Failed.",
							"GameUser", hitInfo.ClientInfo.SessionId,
							"AccountingSn", v,
							"JackpotSn", jackpotSn,
						)
					}
				}
			}
		}

		m.rwMutex.Unlock()
	}
}

func (m *mysteryJackpotClient) handleAction(action *flux.Action) {
	switch action.Key().Name() {
	case actionSync:
		m.sendAction(action)

	case actionSendClientInfo:
		m.sendAction(action)

	case actionJackpotHit:
		m.sendAction(action)

	case actionJackpotEnd:
		m.sendAction(action)

	default:
		break
	}
}

func (m *mysteryJackpotClient) handleConnection() {
	u := url.URL{
		Scheme: m.scheme,
		Host:   m.host + ":" + m.port,
		Path:   m.path,
	}

	retryCount := 0
	retryTimes := Config.Client.MYS.RetryTimes
	retryPeriod := Config.Client.MYS.RetryPeriod
	readSignal := make(chan bool, 1)
	writeSignal := make(chan bool, 1)

	for {
		m.rwMutex.Lock()

		if m.reconnect {
			if m.connected {
				// close previous connection
				readSignal <- true
				writeSignal <- true
				m.conn.Close()
			}

			conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
			logger.Service.Zap.Infow("Jackpot Server Connecting...", "Url", u.String())

			if err != nil {
				if retryCount > retryTimes && retryTimes != -1 {
					conn.Close()
					return
				}

				logger.Service.Zap.Warnw("Jackpot Server Connecting Failed", "Url", u.String())

				m.reconnect = true
				retryCount++

				time.Sleep(time.Duration(retryPeriod) * time.Second)

			} else {
				logger.Service.Zap.Infow("Jackpot Server Connection Success", "Url", u.String())
				m.reconnect = false
				m.connected = true
				m.conn = conn

				go m.runReadMessage(readSignal)
				go m.runWriteMessage(writeSignal)
			}
		}

		m.rwMutex.Unlock()
	}
}

func (m *mysteryJackpotClient) runReadMessage(signal chan bool) {
	m.conn.SetReadLimit(maxMessageSize)

	for {
		select {
		case <-signal:
			return

		default:
			_, msg, err := m.conn.ReadMessage()

			if err != nil {
				m.rwMutex.Lock()

				logger.Service.Zap.Warnw("Jackpot Client Read Message Closed",
					"Error", err,
				)
				m.reconnect = true
				m.connected = false

				m.rwMutex.Unlock()

				return
			}

			v, err := FindActionName(msg)
			if err != nil {
				logger.Service.Zap.Errorw(MSGID_PROTO_INVALID, "Error", err)
				return
			} else {
				switch v {
				case EMSGID_kHitInfo:
					m.handleHitInfo(msg)

				case EMSGID_kNotifyInfo:
					m.handleNotifyInfo(msg)

				case EMSGID_kGroupInfoMap:
					m.handleGroupInfoMap(msg)
				}
			}

			logger.Service.Zap.Infow("Jackpot Client Read Message",
				"Msg", v,
			)
		}
	}
}

func (m *mysteryJackpotClient) runWriteMessage(signal chan bool) {
	ticker := time.NewTicker(pingPeriod)
	defer ticker.Stop()

	for {
		select {
		case <-signal:
			return

		case action, ok := <-m.in:
			if !ok {
				return
			}
			m.handleAction(action)

		case <-ticker.C:
			m.conn.SetWriteDeadline(time.Now().Add(writeWait))

			data := strconv.FormatInt(time.Now().UnixNano(), 10)

			if err := m.conn.WriteMessage(websocket.PingMessage, []byte(data)); err != nil {
				logger.Service.Zap.Warnw("Jackpot Client Ping Failed",
					"Error", err,
				)
				return
			}
		}
	}
}

func (m *mysteryJackpotClient) sendAction(action *flux.Action) {
	m.sendByte(action.Payload()[0].([]byte))
}

func (m *mysteryJackpotClient) sendByte(data []byte) {
	m.conn.SetWriteDeadline(time.Now().Add(writeWait))
	w, err := m.conn.NextWriter(websocket.BinaryMessage)

	defer func() {
		if w != nil {
			w.Close()
		}
	}()

	if err == nil && w != nil {
		w.Write(data)
	}
}

func (m *mysteryJackpotClient) handleHitInfo(msg []byte) {
	m.rwMutex.Lock()
	defer m.rwMutex.Unlock()

	data := &jackpot_proto.HitInfo{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Warnw(HIT_INFO_PROTO_INVALID, "Error", err)
		return
	}

	switch data.Status {
	case jackpot_proto.HitInfo_kNotified:
		if _, ok := m.hitInfo[data.JackpotSn]; !ok {
			m.hitInfo[data.JackpotSn] = data
		} else {
			logger.Service.Zap.Warnw("Jackpot hit info is already existed",
				"GameUser", data.ClientInfo.SessionId,
				"Jackpot Sn", data.JackpotSn,
			)
		}
		return

	case jackpot_proto.HitInfo_kTimeout:
		if _, ok := m.hitInfo[data.JackpotSn]; ok {
			delete(m.hitInfo, data.JackpotSn)
		} else {
			logger.Service.Zap.Warnw("Jackpot hit info did not exist",
				"GameUser", data.ClientInfo.SessionId,
				"Jackpot Sn", data.JackpotSn,
			)
		}
		return

	default:
		return
	}
}

func (m *mysteryJackpotClient) handleNotifyInfo(msg []byte) {
	data := &jackpot_proto.NotifyInfo{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Warnw(NOTIFY_INFO_PROTO_INVALID, "Error", err)
		return
	}
	m.iJackpot.OnJackpotNotify(data, JackpotType_MYS)
}

func (m *mysteryJackpotClient) handleGroupInfoMap(msg []byte) {
	data := &jackpot_proto.GroupInfoMap{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Warnw(GROUP_INFO_MAP_PROTO_INVALID, "Error", err)
		return
	}

	switch data.Status {
	case jackpot_proto.GroupInfoMap_kAll:
		m.hasSynced = true
		m.poolInfoMaps = data.PoolMap
		m.iJackpot.OnJackpotUpdate(data.PoolMap, JackpotType_MYS, "")

	case jackpot_proto.GroupInfoMap_kPartial:
		if !m.hasSynced {
			m.sync()
			return
		}

		for k, _ := range m.poolInfoMaps {
			if data, ok := data.PoolMap[k]; ok {
				m.poolInfoMaps[k] = data
			}
		}
		m.iJackpot.OnJackpotUpdate(data.PoolMap, JackpotType_MYS, "")

	default:
		return
	}
}

func (m *mysteryJackpotClient) contribute(clientInfo *jackpot_proto.ClientInfo, accountingSn uint64) float64 {
	if !m.connected {
		return 0
	}

	m.contributeMutex.Lock()
	defer m.contributeMutex.Unlock()

	if v := m.accountingSnMap[clientInfo.SessionId]; v != accountingSn && accountingSn != 0 {
		m.accountingSnMap[clientInfo.SessionId] = accountingSn
		m.totalBetMap[clientInfo.SessionId] = clientInfo.TotalBetLong
	} else {
		m.totalBetMap[clientInfo.SessionId] += clientInfo.TotalBetLong
	}

	if v, ok := m.clientInfoMap.Map[clientInfo.SessionId]; ok {
		if clientInfo.TotalBet > 0 {
			v.TotalBet += clientInfo.TotalBet
			v.TotalBetLong += clientInfo.TotalBetLong
		} else {
			v.TotalBet = 0
			v.TotalBetLong = 0
		}
	} else {
		m.clientInfoMap.Map[clientInfo.SessionId] = clientInfo
	}

	return math.Round(float64(m.totalBetMap[clientInfo.SessionId])*float64(m.poolInfoMaps[clientInfo.GroupId].ContributionRate)*100) / 100
}

func (m *mysteryJackpotClient) jackpotUpdate(secWebsocketKey string) {
	if m.hasSynced {
		m.iJackpot.OnJackpotUpdate(m.poolInfoMaps, JackpotType_MYS, secWebsocketKey)
	} else {
		m.sync()
	}
}

func (m *mysteryJackpotClient) deleteUser(secWebsocketKey string) {
	if _, ok := m.accountingSnMap[secWebsocketKey]; ok {
		delete(m.accountingSnMap, secWebsocketKey)
		if _, ok := m.totalBetMap[secWebsocketKey]; ok {
			delete(m.totalBetMap, secWebsocketKey)
		}
	}
}

func (m *mysteryJackpotClient) sync() {
	if !m.hasSynced {
		data := &jackpot_proto.SysCall{
			MessageId: jackpot_proto.MessageID_kSysCall,
			Function:  jackpot_proto.SysCall_kSync,
		}
		dataBuffer, _ := proto.Marshal(data)
		flux.Send(actionSync, Service.HashId(JackpotType_MYS), Service.HashId(JackpotType_MYS), dataBuffer)
	}
}

func (m *mysteryJackpotClient) id() string {
	return Service.HashId(JackpotType_MYS)
}

func (m *mysteryJackpotClient) destroy() {
	m.rwMutex.Lock()
	defer m.rwMutex.Unlock()

	logger.Service.Zap.Infow("Mystery Jackpot Client Unregister", "Chan", fmt.Sprintf("%p", m.in))
	flux.UnRegister(m.id(), m.in)
}
