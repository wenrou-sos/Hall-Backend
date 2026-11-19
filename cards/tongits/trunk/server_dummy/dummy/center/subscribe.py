
import json
from redisassist import RDSPGuard
from utils import *
from main_cmd_pb2 import *
from c_l_lobby_pb2 import *

def OnRedisRunPubSubRecv(loop):
    loop.asyncio_loop.create_task(RDSPGuard.RP("game").PubSub.AsyncUpdate())

def OnRedisRunLibGrdRecv(loop):
    loop.asyncio_loop.create_task(RDSPGuard.RP("game").LibGrd.AsyncUpdate())

class Subscribecb(object):
    def __init__(self, mainservice):
        self.mMainService = mainservice

    def OnWebEventKickUser(self, nKickType, eventData):
        Log("進入center server的def OnWebEventKickUser")
        if eventData is None or not isinstance(eventData, str):
            return
        request = msg_clt_request()
        request.rpc_name = b'kick_user'
        json_data = {}

        mTCPServer = self.mMainService.TCPServer
        rp = RDSPGuard.RP("game")

        datasps = eventData.split("|")
        if nKickType == 10:     #踢单个人
            serverid = rp.LibGrd.R.hget("sha@uuid2sid", datasps[0])
            if serverid is None:
                return
            json_data["uuid"] = int(datasps[0])
            request.json = json.dumps(json_data).encode('utf-8')
            mTCPServer.SendProtoMsgByServerId(serverid, e_msgid_ctl,
                                              e_cl_msgid_ctl_request, request)
        elif nKickType == 11:   #踢subgameid
            host_api_key = datasps[0]
            subgame_id = int(datasps[1])
            server_list = get_game_server_list_ret()
            rp = RDSPGuard.RP("gamelist")
            server_list_db = rp.LibGrd.R.get("var@serverlist")
            if server_list_db is not None and len(server_list_db) > 0:
                server_list.ParseFromString(server_list_db)

            json_data["uuid"] = -1
            request.json = json.dumps(json_data).encode('utf-8')
            host_api_key = host_api_key.encode()
            for idx in range(len(server_list.gslist)):
                if server_list.gslist[idx].host_api_key == host_api_key \
                        and server_list.gslist[idx].subgame_id == subgame_id:
                    mTCPServer.SendProtoMsgByServerId(server_list.gslist[idx].server_uuid, e_msgid_ctl,
                                                      e_cl_msgid_ctl_request, request)
        elif nKickType == 12:   #踢渠道所有人
            host_api_key = datasps[0]
            server_list = get_game_server_list_ret()
            rp = RDSPGuard.RP("gamelist")
            server_list_db = rp.LibGrd.R.get("var@serverlist")
            if server_list_db is not None and len(server_list_db) > 0:
                server_list.ParseFromString(server_list_db)

            json_data["uuid"] = -1
            request.json = json.dumps(json_data).encode('utf-8')
            host_api_key = host_api_key.encode()
            for idx in range(len(server_list.gslist)):
                if server_list.gslist[idx].host_api_key == host_api_key:
                    mTCPServer.SendProtoMsgByServerId(server_list.gslist[idx].server_uuid, e_msgid_ctl,
                                                      e_cl_msgid_ctl_request, request)
        elif nKickType == 13:   # 解散指定桌子
            host_api_key = str(datasps[0])  # 多代理商戶或主服務商戶金鑰
            single_host_api_key = str(datasps[1])  # 目標玩家來源商戶金鑰
            subgame_id = int(datasps[2])  # 遊戲房號
            nick_name = str(datasps[3])  # 玩家名稱
            server_list = get_game_server_list_ret()
            rp = RDSPGuard.RP("gamelist")
            server_list_db = rp.LibGrd.R.get("var@serverlist")
            if server_list_db is not None and len(server_list_db) > 0:
                server_list.ParseFromString(server_list_db)

            json_data["uuid"] = -1
            request.json = json.dumps(json_data).encode('utf-8')
            host_api_key = host_api_key.encode()
            # 目標玩家的來源商戶塞入proto，等待送入game server
            request.channel = single_host_api_key
            # 目標玩家名稱塞入proto，等待送入game server
            request.nick_name = nick_name
            for idx in range(len(server_list.gslist)):
                # 確認商戶與房號，兩者都與api設定相同，解散目標物明確
                if server_list.gslist[idx].host_api_key == host_api_key \
                        and server_list.gslist[idx].subgame_id == subgame_id:
                    # 送入game→registe註冊→registeDisMissGame
                    mTCPServer.SendProtoMsgByServerId(server_list.gslist[idx].server_uuid, e_msgid_ctl,
                                                      e_cl_msgid_ctl_dismissgame, request)
        elif nKickType == 14:  # 解散指定單廳
            host_api_key = str(datasps[0])  # 多代理商戶或主服務商戶金鑰
            subgame_id = int(datasps[1])  # 遊戲房號
            server_list = get_game_server_list_ret()
            rp = RDSPGuard.RP("gamelist")
            server_list_db = rp.LibGrd.R.get("var@serverlist")
            if server_list_db is not None and len(server_list_db) > 0:
                server_list.ParseFromString(server_list_db)

            json_data["uuid"] = -1
            request.json = json.dumps(json_data).encode('utf-8')
            host_api_key = host_api_key.encode()
            for idx in range(len(server_list.gslist)):
                if server_list.gslist[idx].host_api_key == host_api_key \
                        and server_list.gslist[idx].subgame_id == subgame_id:
                    mTCPServer.SendProtoMsgByServerId(server_list.gslist[idx].server_uuid, e_msgid_ctl,
                                                      e_cl_msgid_ctl_dismissroom, request)

    def OnWebReloadOptions(self, eventData):
        if eventData is None or not isinstance(eventData, str):
            return
        serverid = int(eventData)
        request = msg_clt_request()
        request.rpc_name = b'reload_cfg'
        request.json = json.dumps({}).encode('utf-8')
        mTCPServer = self.mMainService.TCPServer
        mTCPServer.SendProtoMsgByServerId(serverid, e_msgid_ctl,
                                          e_cl_msgid_ctl_request, request)

    def OnWebEnableOption(self, eventData):
        if eventData is None or not isinstance(eventData, str):
            return
        enable = int(eventData)     #0:关闭 1:开启
        request = msg_clt_request()
        request.rpc_name = b'enable'
        request.json = json.dumps({"enable" : enable}).encode('utf-8')
        mTCPServer = self.mMainService.TCPServer
        mTCPServer.SendProtoMsgToAllServer(e_msgid_ctl, e_cl_msgid_ctl_request, request)

    def OnRedisSubscribeCB(self, proxy, msg, ptn, chl, data):
        try:
            if chl == "sg_event":
                if data is not None \
                        and (isinstance(data, bytes) is True or isinstance(data, str) is True):
                    dataStr = data if isinstance(data, str) else data.decode('utf-8')
                    if len(dataStr) >= 2:
                        dataSprStr = dataStr[0:2]
                        if dataSprStr == "2:":  # 重载游戏设定
                            self.OnWebReloadOptions(dataStr[2:])
                        elif dataSprStr == "3:":  # enable所有游戏
                            self.OnWebEnableOption(dataStr[2:])
                        elif dataSprStr == "5:":  # 踢人
                            self.OnWebEventKickUser(10, dataStr[2:])
                        elif dataSprStr == "6:":  # 踢subgameid
                            self.OnWebEventKickUser(11, dataStr[2:])
                        elif dataSprStr == "7:":  # 踢商戶所有人
                            self.OnWebEventKickUser(12, dataStr[2:])
                        elif dataSprStr == "8:":  # 解散指定桌子
                            self.OnWebEventKickUser(13, dataStr[2:])
                        elif dataSprStr == "9:":  # 解散指定單廳
                            self.OnWebEventKickUser(14, dataStr[2:])
        except:
            PrintEXC()