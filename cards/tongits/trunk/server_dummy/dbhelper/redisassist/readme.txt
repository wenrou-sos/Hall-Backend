建库命令
python createdb.py 0 cfg/createdb0.json 1
python createdb.py 1 cfg/createdb0.json

# redis client配置
# 暂时不支持SSL转换的加密Socket
# 支持通用Socket和Unix Domain Socket(IPC解决方案)
{
    "host":"192.168.1.106",       # redis 地址（字符串）
    "port":6379,                  # redis 端口（整型）
    "db":0,                       # redis db号（整型）
    "password":"123456",          # redis 密码（字符串），该字段可选，当字段被设置且不为空字符串时，启用Redis验证登录
    "encoding":"utf-8",           # redis 数据（字符串）编码，该字段可选，当字段被设置且不为空字符串时，采用自定义值，否则使用默认值"utf-8"
    "path":"",                    # 填写具体的socket路径（redis server socket），该字段可选，当字段被设置时启用Unix Domain Socket模式
    "compatible":1,               # 兼容模式，该字段可选，当字段被设置且不为0时，启用兼容模式，兼容模式下如果Unix Domain Socket的"path"不是有效的sock文件描述符，将启用通用Socket模式
    "decode_responses":0,         # 设置系统接收redis响应后将数据decode为Unicode编码，该字段可选，当字段被设置且不为0时，启用该功能
    "socket_timeout":1.0,         # 设置socket通讯超时时间（单位：秒 浮点数），该字段可选，当字段被设置且大于0时，socket为非阻塞模式，否则为阻塞模式
    "retry_on_timeout":1,         # 设置Socket超时后重试操作，该字段可选，当字段被设置且不为0时，启用该功能，注：重试只会最多进行一次
    "socket_read_size":65536,     # 设置单次读取Socket的数据大小（单位：字节），该字段可选，当字段被设置且大于0时，采用自定义大小，否则使用默认大小为65536
    "socket_connect_timeout":1.0, # Socket建立连接超时（单位：秒 浮点数）（只在通用Socket模式下有效），该字段可选，当字段被设置且大于0时，socket建立连接将启用超时判定，否则只进行异常判定
    "max_connections":1024,       # 连接池最大连接数，该字段可选，当字段被设置且大于0时，采用自定义大小，否则使用默认大小为1024
    "lua_lib_cfg":{},             # redis lua函数库的配置（详见redis lua库管理），该字段可选，当字段被设置时务必严格按照格式，否则将产生异常，该字段被设置时启用客户端redis lua脚本映射
    "subscribe" : [ "chl1", "chl2"], # 订阅的渠道
    "psubscribe" : [ "chl*" ]    # 订阅的渠道patterns
}
# redis client lua脚本映射配置
{
    "libs":[ "name1", "name2" ],  # 库列表
    "preload":1,                  # 预加载redis Lua脚本库，该字段可选，当字段被设置且不为0时，启用该功能
    "dynamic_update":0,           # 动态更新脚本库，
    "update_hint":"",             # 动态更新的暗号，
}

# 脚本源码
{
    "lib1":{
        "GenUUID":'''
        local new_uuid = redis.Call("get", "UUIDBase")
        redis.Call('incr', 'UUIDBase')
        return new_uuid
        '''
    }
}

# 建库规则
全局变量会在导入时在变量名前加上`var@`的前缀;
查找库SHA映射表为`lib@`前缀 + 库名;

redisassist发布/订阅协程模式用法
1.通过RDSPGuard.RP(proxy_name)获得对应的RP
2.RP下有PubSub和LibGrd组件，只有配置了订阅渠道时才会创建PubSub组件，只有配置了lua_lib_cfg选项才会创建LibGrd组件
3.这两个组件存在Update和AsyncUpdate，Update函数为同步调用方式（每帧或定时调用），AsyncUpdate调用方式如下：
'''
@gen.coroutine
def RunPubSubRecv():
    pub_sub = RDSPGuard.RP("game").PubSub
    if pub_sub is not None:
        await pub_sub.AsyncUpdate()

@gen.coroutine
def RunLibGrdRecv():
   lib_grd = RDSPGuard.RP("game").LibGrd
    if lib_grd is not None:
        await lib_grd.AsyncUpdate()

if __name__ == "__main__":
    RunPubSubRecv()
    RunLibGrdRecv()
    IOLoop.current().start()
'''