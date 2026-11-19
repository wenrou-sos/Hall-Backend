from redisassist import RDSPGuard
from mysqlassist import MYPGuard
from network.tcpserver import *
from network.message import MsgHandler
from data_struct_pb2 import *
from main_cmd_pb2 import *
from c_l_lobby_pb2 import *
import json
from utils import *

class ControlHandler(MsgHandler):
    def __init__(self, mainservice):
        self.mAdminCfgs = []
        self.mAdmin = {}
        self.mMainService = mainservice
        self.mCtrlExec = {
            b'ctl_login' : self.OnCtl_AdminLogon,
            b'get_server_list' : self.OnCtl_GetServerList,
            b'get_player_list' : self.OnCtl_GetPlayerList,
            b'get_user_info' : self.OnCtl_GetUserInfo,
            b'forbid_user' : self.OnCtl_ForbidUser,
            b'kick_user' : self.OnCtl_KickUser,
            b'set_user_status' : self.OnCtl_SetUserStatus
        }

    def Initialize(self, dispatcher):
        dispatcher.registe(e_msgid_ctl, e_cl_msgid_ctl_request, self.OnCtl_Request)
        dispatcher.registe(e_msgid_ctl, e_cl_msgid_ctl_response, self.OnCtl_Response)
        #self.OnReloadCfg()

    def OnReloadCfg(self):
        pass
        #MYPGuard.MYP("game").Exec("SELECT * FROM `cfg_admin`", None, self.OnLoadAdminResult)

    def OnLoadAdminResult(self, args, row_results):
        try:
            if row_results != None \
                    and isinstance(row_results, list) == True:
                for row in row_results:
                    admin_info = {}
                    admin_info["username"] = row["UserName"]
                    admin_info["passwd"] = row["PassWord"]
                    admin_info["ips"] = []
                    ips = row["IPS"]
                    if len(ips) > 0:
                        admin_info["ips"] = ips.split("|")
                    admin_info["authority"] = row["Auth"]
                    self.mAdminCfgs.append(admin_info)
        except:
            PrintEXC()

    def GetAdminUser(self, username):
        for idx in range(len(self.mAdminCfgs)):
            if self.mAdminCfgs[idx]["username"] == username:
                return self.mAdminCfgs[idx]
        return None

    def WriteToolLog(self, json_data):
        try:
            MYPGuard.MYP("log").Exec("INSERT INTO game_tool_change_user (log) VALUES ('" + json_data + "')")
        except:
            PrintEXC()

    def OnNetClose(self, conn):
        try:
            if conn.GetID() in self.mAdmin:
                del self.mAdmin[conn.GetID()]
                # INFO("Tool User %d 登出成功", conn.GetID())
        except:
            PrintEXC()

    def OnCtl_Request(self, conn, data, size):
        try:
            request = msg_clt_request()
            request.ParseFromString(data)
            json_data = json.loads(request.json)
            ##INFO("OnCtl_Request rpc_name [%s] json_data %s", request.rpc_name, request.json)
            if request.context_id == 0:
                if request.rpc_name in self.mCtrlExec:
                    if request.rpc_name == b"ctl_login":
                        self.mCtrlExec[request.rpc_name](conn, json_data)
                    else:
                        if conn.GetID() in self.mAdmin:
                            self.mCtrlExec[request.rpc_name](conn, json_data)
                return
            else:
                if conn.GetID() in self.mAdmin:
                    serv_context_id = request.context_id
                    request.context_id = conn.GetID()
                    if request.rpc_name != b"get_server_info":  # 其他要操作权限
                        admin_cfg = self.GetAdminUser(self.mAdmin[conn.GetID()])
                        if admin_cfg is None or admin_cfg["authority"] <= 0 or \
						        (admin_cfg["authority"] == 2 and json_data["control_status"] in (5, 6, 7, 8)):
                            return
                    self.mMainService.TCPServer.SendProtoMsgByServerId(serv_context_id,
                                                         e_msgid_ctl,
                                                         e_cl_msgid_ctl_request,
                                                         request)
        except:
            PrintEXC()

    def OnCtl_Response(self, conn, data, size):
        try:
            request = msg_clt_response()
            request.ParseFromString(data)
            if request.route is True:
                ##INFO("OnCtl_Response rpc_name [%s] json_data %s", request.rpc_name, request.json)
                self.mMainService.TCPServer.SendProtoMsg(request.context_id,
                                                     e_msgid_ctl,
                                                     e_cl_msgid_ctl_response,
                                                     request)
            else:
                json_data = json.loads(request.json)
                if request.rpc_name in self.mCtrlExec:
                    self.mCtrlExec[request.rpc_name](conn, json_data)
        except:
            PrintEXC()

    def OnCtl_AdminLogon(self, conn, json_data):
        try:
            if conn.GetID() not in self.mAdmin:
                if "username" in json_data and "passwd" in json_data:
                    name, pwd = json_data["username"], json_data["passwd"]
                    admin_cfg = self.GetAdminUser(name)
                    if admin_cfg is None \
                            or admin_cfg["passwd"] != pwd:
                        return
                    ok = True
                    enable_ips = admin_cfg["ips"]
                    if len(enable_ips) > 0:
                        ok = False
                        for idx in range(len(enable_ips)):
                            if enable_ips[idx] == conn.GetIP():
                                ok = True
                                break
                    if ok is False:
                        return
                    self.mAdmin[conn.GetID()] = name
                    # 登录日志
                    # INFO("Tool User %d:%s 登录成功", conn.GetID(), name)
                    json_rsp = {}
                    json_rsp["ret"] = 1
                    json_rsp["username"] = name
                    response = msg_clt_response()
                    response.rpc_name = b"ctl_login"
                    response.json = json.dumps(json_rsp).encode('utf-8')
                    conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def OnCtl_GetServerList(self, conn, json_data):
        try:
            if conn.GetID() in self.mAdmin:
                rp1 = RDSPGuard.RP("gamelist")
                server_list_db = rp1.LibGrd.R.get("var@serverlist")
                if server_list_db is None or len(server_list_db) == 0:
                    INFO("get_server_list is none")
                    return

                server_list = get_game_server_list_ret()
                server_list.ParseFromString(server_list_db)

                json_rsp = {}
                for idx in range(len(server_list.gslist)):
                    serv_data = server_list.gslist[idx]
                    json_rsp[serv_data.server_id] = serv_data.server_name.decode('gbk')

                response = msg_clt_response()
                response.rpc_name = b"get_server_list_rsp"
                response.json = json.dumps(json_rsp).encode('utf-8')
                conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def OnCtl_GetPlayerList(self, conn, json_data):
        try:
            if conn.GetID() in self.mAdmin:
                rp0 = RDSPGuard.RP("game")
                results = rp0.LibGrd.R.hkeys("sha@uuid2sid")

                response = msg_clt_response()
                response.rpc_name = b"get_user_list_rsp"
                json_rsp = []
                if results is not None and isinstance(results, list) is True:
                    for idx in range(len(results)):
                        if results[idx].isdigit():
                            json_rsp.append(int(results[idx]))
                            if len(json_rsp) >= 500:
                                response.json = json.dumps(json_rsp).encode('utf-8')
                                conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
                                json_rsp.clear()
                    if len(json_rsp) > 0:
                        response.json = json.dumps(json_rsp).encode('utf-8')
                        ##INFO("__OnCtl_GetPlayerList %s", response.json)
                        conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def OnCtl_GetUserInfo(self, conn, json_data):
        try:
            if conn.GetID() in self.mAdmin:
                if len(json_data) > 0:
                    ##INFO("__OnCtl_GetUserInfo JSON_DATA %s", json_data)
                    json_rsp = []
                    for idx in range(len(json_data)):
                        sha_uuid = ("sha@data_" + str(json_data[idx]))
                        rp0 = RDSPGuard.RP("game")
                        results = rp0.LibGrd.R.hmget(sha_uuid, "base", "svr_id")
                        if results is None or not isinstance(results, list) \
                                or results[0] is None:
                            continue
                        account_base = db_data_user()
                        account_base.ParseFromString(results[0])

                        info = {}
                        info["channel"] = account_base.channel
                        info["channeluuid"] = account_base.sdk_uuid
                        info["uuid"] = account_base.uuid
                        info["name"] = account_base.nickname
                        info["today_profit"] = account_base.dailyprofit
                        info["total_profit"] = account_base.profit
                        info["score"] = account_base.score
                        info["control_status"] = account_base.control_status
                        info["control_score"] = account_base.control_score
                        info["server_id"] = -1 if results[1] is None else int(results[1])
                        json_rsp.append(info)

                    response = msg_clt_response()
                    response.rpc_name = b"get_user_info_rsp"
                    response.json = json.dumps(json_rsp).encode('utf-8')
                    ##INFO("__OnCtl_GetUserInfo %s %s", response.rpc_name, response.json)
                    conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def OnCtl_ForbidUser(self, conn, json_data):
        try:
            response = msg_clt_response()
            response.rpc_name = b"forbid_user_rsp"

            json_rsp = {}
            json_rsp["ret"] = 0
            rp = RDSPGuard.RP("game")
            serverid = rp.LibGrd.R.hget("sha@data_" + str(json_data["uuid"]), "svr_id")
            while True:
                if serverid is None or serverid <= 0:
                    json_rsp["ret"] = -1
                    break
                results = rp.LibGrd.Call("api.GetInfoBySYS", *(json_data["uuid"], ))
                if results is None or results[0] != 0:
                    json_rsp["ret"] = results[0]
                    break
                account_base = db_data_user()
                account_base.ParseFromString(results[1])
                account_base.disable_login = 1
                account_base_ss = pb_base.SerializeToString()
                rp.LibGrd.Call("api.SetInfoBySYS", *(json_data["uuid"], account_base_ss))
                json_rsp["ret"] = 0

                request = msg_clt_request()
                request.rpc_name = b'kick_user'
                req_json_data = {}
                req_json_data["uuid"] = json_data["uuid"]
                request.json = json.dumps(req_json_data).encode('utf-8')
                self.mMainService.TCPServer.SendProtoMsgByServerId(serverid,
                                                                   e_msgid_user,
                                                                   e_cl_msgid_ctl_request,
                                                                   request)
                break
            response.json = json.dumps(json_rsp).encode('utf-8')
            conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def OnCtl_KickUser(self, conn, json_data):
        try:
            response = msg_clt_response()
            response.rpc_name = b"kick_user_rsp"

            json_rsp = {}
            json_rsp["ret"] = 0
            rp = RDSPGuard.RP("game")
            while True:
                serverid = rp.LibGrd.R.hget("sha@data_" + str(json_data["uuid"]), "svr_id")
                if serverid is None or serverid <= 0:
                    json_rsp["ret"] = -1
                    break
                request = msg_clt_request()
                request.rpc_name = b'kick_user'
                req_json_data = {}
                req_json_data["uuid"] = json_data["uuid"]
                request.json = json.dumps(req_json_data).encode('utf-8')
                self.mMainService.TCPServer.SendProtoMsgByServerId(serverid,
                                                                   e_msgid_user,
                                                                   e_cl_msgid_ctl_request,
                                                                   request)
                break
            response.json = json.dumps(json_rsp).encode('utf-8')
            conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def DoSetUserStatus(self, json_data, op_user, context_id):
        try:
            uuid = json_data["uuid"]
            control_status = json_data["control_status"]
            control_score = json_data["control_score"]

            sha_uuid = ("sha@data_" + str(uuid))
            rp = RDSPGuard.RP("game")
            results = rp.LibGrd.R.hmget(sha_uuid, "base", "svr_id")
            if results is None:
                return

            account_base = db_data_user()
            account_base.ParseFromString(results[0])
            account_base.control_status = control_status
            account_base.control_score = control_score
            account_base_ss = account_base.SerializeToString()
            rp.LibGrd.Call("api.SetInfoBySYS", *(uuid, account_base_ss))

            # 写日志
            jsonlog = {}
            jsonlog["uuid"] = uuid
            jsonlog["control_status"] = control_status
            jsonlog["control_score"] = control_score
            jsonlog["opuser"] = op_user
            jsonlog["optime"] = GetServerTimeStr()
            self.WriteToolLog(json.dumps(jsonlog))

            servid = 0 if results[1] is None else int(results[1])
            if servid <= 0:
                return
            request = msg_clt_request()
            request.context_id = context_id
            request.rpc_name = b"set_user_status"
            request.json = json.dumps(json_data).encode('utf-8')
            self.mMainService.TCPServer.SendProtoMsgByServerId(servid,
                                                           e_msgid_ctl,
                                                           e_cl_msgid_ctl_request,
                                                           request)
        except:
            PrintEXC()

    def OnCtl_SetUserStatus(self, conn, json_data):
        try:
            response = msg_clt_response()
            response.rpc_name = b"set_user_status_rsp"
            json_rsp = {}

            uuid = json_data["uuid"]
            control_status = json_data["control_status"]
            control_score = json_data["control_score"]

            admin_cfg = self.GetAdminUser(self.mAdmin[conn.GetID()])
            if admin_cfg is None or admin_cfg["authority"] <= 0 or \
					(admin_cfg["authority"] == 2 and json_data["control_status"] in (5, 6, 7, 8)):
                return
            self.DoSetUserStatus(json_data, self.mAdmin[conn.GetID()], conn.GetID())

            json_rsp["ret"] = 0
            json_rsp["uuid"] = uuid
            json_rsp["control_status"] = control_status
            json_rsp["control_score"] = control_score
            response.json = json.dumps(json_rsp).encode('utf-8')
            conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def OnTool_UserLoginout(self, t, uuid):      # 1：登录 2：登出
        try:
            json_rsp = {}
            json_rsp["uuid"] = int(uuid)
            json_rsp["t"] = t

            response = msg_clt_response()
            response.rpc_name = b"user_login"
            response.json = json.dumps(json_rsp).encode('utf-8')

            for socketId, name in self.mAdmin.items():
                conn = self.mMainService.TCPServer.Get(socketId)
                if conn is not None:
                    conn.SendProtoMsg(e_msgid_ctl, e_cl_msgid_ctl_response, response)
        except:
            PrintEXC()

    def KickAllToolUser(self):       #踢掉所有工具号
        try:
            for socketId, name in self.mAdmin.items():
                conn = self.mMainService.TCPServer.Get(socketId)
                if conn is not None:
                    conn.SafeClose()
            self.mAdmin.clear()
        except:
            PrintEXC()
