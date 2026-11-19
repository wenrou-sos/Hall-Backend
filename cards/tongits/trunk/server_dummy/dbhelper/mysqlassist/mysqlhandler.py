import pymysql
import json
from mysqlassist.utils import *

class MySQLHandler(object):
    @classmethod
    def Create(cls, **kwargs):
        Log("创建MySQL连接句柄：")
        Log(json.dumps(kwargs, indent = 4))
        hdr = cls(**kwargs)
        resp = hdr.TestConnection()
        Log("连接测试结果：", resp)
        if resp is not None:
            return hdr
        else:
            return None

    def __init__(self, sql_type = "default", **connection_kwargv):
        self.mType = sql_type
        self.mConnectionKWArgv = connection_kwargv
        self.mConnection = None
        self.mCursor = None

    @property
    def Type(self):
        return self.mType

    @property
    def Config(self):
        return self.mConnectionKWArgv

    def TestConnection(self):
        sql = "SELECT NOW()"
        date = self.Exec(sql)
        try:
            return date[0]
        except:
            PrintEXC()
            return None

    def Begin(self):
        try:
            if self.mConnection is None:
                self.mConnection = pymysql.Connection(**self.mConnectionKWArgv)
            else:
                self.mConnection.ping()
            if self.mCursor is None:
                self.mCursor = self.mConnection.cursor(cursor = pymysql.cursors.DictCursor)

            return True
        except:
            Err("<连接池>配置：")
            Err(json.dumps(self.mConnectionKWArgv, indent=4))
            PrintEXC()

        return False

    def End(self):
        if self.mCursor:
            self.mCursor.close()
            self.mCursor = None

    def Exec(self, sql):
        try:
            sql_list = None
            if isinstance(sql, list):
                sql_list = sql
            elif isinstance(sql, str):
                sql_list = sql.split(";;")
            else:
                Err("Not a valid type to be executed!", sql)
                return tuple()

            results = []
            if len(sql_list) > 0:
                if self.Begin():
                    Log("执行批量查询：", sql_list)
                    i = 0
                    for s in sql_list:
                        if len(s) > 0:
                            self.mCursor.execute(s)
                            i += 1
                    if i > 0:
                        self.mConnection.commit()
                        results = self.mCursor.fetchall()
                self.End()
            return results
        except:
            Err("Exec except", sql)
            PrintEXC()
            return tuple()

class ExecutionHandler(object):
    def __init__(self, sql_type, template):
        self.mType = sql_type
        self.mTemplate = template

    @property
    def Type(self):
        return self.mType

    @property
    def Template(self):
        return self.mTemplate

    def GetSQL(self, params = {}):
        sql = self.mTemplate
        if len(params) > 0:
            for key in params:
                p = params[key]
                if isinstance(p, str):
                    p.replace("\'", "\\\'").replace("\"", "\\\"")
            sql = sql % params
        return sql

    def DoTask(self, db_hd):
        return True

    def ProcessResult(self, results):
        return True

class MySQLHandlerPool(object):
    def __init__(self, max_connection = 128, **connection_kwargv):
        self.mMaxConnection = max_connection
        self.mConnectionCnt = 0
        self.mCachedConnections = []
        self.mInUseConnections = set()
        self.mConnectionKWArgv = connection_kwargv
        conn = self.MakeConnection()
        self.ReleaseConnection(conn)

    def __repr__(self):
        return "<MySQLHandlerPool>[MaxConnection:%d][ConnectionCount:%d]" % (self.mMaxConnection, self.mConnectionCnt)

    @property
    def ActiveCount(self):
        return len(self.mInUseConnections)

    def MakeConnection(self):
        if self.mConnectionCnt < self.mMaxConnection:
            conn = MySQLHandler.Create(**self.mConnectionKWArgv)
            if conn is not None:
                self.mInUseConnections.add(conn)
                self.mConnectionCnt += 1
                Info("激活连接数：", self.mConnectionCnt)

                #Info("<连接池>配置：")
                #Info(json.dumps(self.mConnectionKWArgv, indent=4))
                return conn
        return None

    def GetConnection(self):
        try:
            conn = self.mCachedConnections.pop()
            self.mInUseConnections.add(conn)
        except:
            conn = self.MakeConnection()

        Log("活跃连接数：", len(self.mInUseConnections))
        return conn

    def ReleaseConnection(self, conn):
        if conn is not None and isinstance(conn, MySQLHandler):
            self.mInUseConnections.remove(conn)
            self.mCachedConnections.append(conn)
            Log("活跃连接数：", len(self.mInUseConnections))

