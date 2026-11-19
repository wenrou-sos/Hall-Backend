import json
from redisassist import RDSPGuard
from utils import *
from main_cmd_pb2 import *
from error_pb2 import *
from c_l_lobby_pb2 import *
from data_struct_pb2 import *
from center_game_pb2 import *
from network.message import MsgHandler

class SubGameHandler(MsgHandler):
    def __init__(self, mainservice):
        self.mMainService = mainservice

    def Initialize(self, dispatcher):
        dispatcher.registe(e_msgid_game_register, e_c_msgid_register_server, self.OnMsgGameRegister)
        #dispatcher.registe(e_msgid_game_register, e_c_msgid_server_info_sync, self.OnMsgSvrInfoSync)

    def OnNetClose(self, conn):
        try:
            if len(conn.GetServId()) > 0:
                rp1 = RDSPGuard.RP("gamelist")
                server_list_db = rp1.LibGrd.R.get("var@serverlist")
                if server_list_db is None or len(server_list_db) == 0:
                    return

                server_list = get_game_server_list_ret()
                server_list.ParseFromString(server_list_db)

                find = -1
                for idx in range(len(server_list.gslist)):
                    if server_list.gslist[idx].context_id == conn.GetID():
                        find = idx
                        break
                if find == -1:
                    return

                server_data = server_list.gslist[find]

                del server_list.gslist[find]
                server_list_ss = server_list.SerializeToString()
                rp1.LibGrd.R.set("var@serverlist", server_list_ss)

                # 广播所有在线玩家
                DEBUG("server closed, %s,(%s,%d)", server_data.hash_key, \
                      server_data.server_addr, server_data.server_port)
                rp = RDSPGuard.RP("game")
                rp.LibGrd.R.publish("dmsubgameclose", server_data.SerializeToString())
                #删除在线人数
                rp1.LibGrd.R.hdel("sha@onlinenums", server_data.server_uuid.decode())

                # 删除当前玩家所在子游戏状态
                results = rp.LibGrd.R.hgetall("sha@uuid2sid")
                server_id = conn.GetServId()
                if results != None and isinstance(results, dict) == True:
                    for uuid, svrid in results.items():
                        if uuid.isdigit() \
                                and svrid == server_id:
                            Log("离开子游戏", uuid.decode())
                            rp.LibGrd.Call("common.OnLogoutSG", *(int(uuid.decode()),))
        except:
            PrintEXC()

    def OnMsgGameRegister(self, conn, data, size):
        try:
            request = msg_register_server()
            request.ParseFromString(data)
            response = msg_register_server_ret()
            server_list = get_game_server_list_ret()

            rp = RDSPGuard.RP("gamelist")
            server_list_db = rp.LibGrd.R.get("var@serverlist")
            if server_list_db is not None and len(server_list_db) > 0:
                server_list.ParseFromString(server_list_db)

            response.ret = e_error_ok
            #更新配置
            for idx in range(len(server_list.gslist)):
                if server_list.gslist[idx].server_uuid == request.server_uuid:
                    Info("更新底注和准入金额")
                    server_list.gslist[idx].cell_score = request.cell_score
                    server_list.gslist[idx].admission_score = request.admission_score
                    server_list_ss = server_list.SerializeToString()
                    rp.LibGrd.R.set("var@serverlist", server_list_ss)
                    conn.SendProtoMsg(e_msgid_game_register, e_c_msgid_register_server, response)
                    return

            server_data = game_server_data()
            server_data.server_uuid = request.server_uuid
            server_data.hash_key = request.hash_key
            server_data.host_api_key = request.host_api_key
            server_data.subgame_id = request.subgame_id
            server_data.server_addr = request.server_addr
            server_data.server_port = request.server_port
            server_data.server_type = request.server_type
            server_data.cell_score = request.cell_score
            server_data.admission_score = request.admission_score
            server_data.max_player = request.max_player
            server_data.cur_player = request.cur_player
            server_data.context_id = conn.GetID()

            server_data_item = server_list.gslist.add()
            server_data_item.CopyFrom(server_data)
            server_list_ss = server_list.SerializeToString()
            rp.LibGrd.R.set("var@serverlist", server_list_ss)

            conn.SendProtoMsg(e_msgid_game_register,e_c_msgid_register_server, response)
            conn.SetServId(server_data.server_uuid)

            # 广播所有在线玩家
            DEBUG("new server registed, %s,(%s,%d)", server_data.hash_key, \
                  server_data.server_addr, server_data.server_port)
            RDSPGuard.RP("game").LibGrd.R.publish("dmsubgameopen", server_data.SerializeToString())
        except:
            PrintEXC()

    def OnMsgSvrInfoSync(self):
        pass
