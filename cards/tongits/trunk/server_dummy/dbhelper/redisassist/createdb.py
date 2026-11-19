import redis
import json
import sys

def DataImport(url, cfg, flush = False):
    r = redis.from_url(url)
    print(r)
    if flush:
        r.flushdb()
        #r.script_flush()
        print("清理完成！")

    print("初始化全局变量...")
    if "global_vars" in cfg:
        g_keys = cfg["global_vars"]
        for key in g_keys:
            val = g_keys[key]
            if isinstance(val, dict):
                for field in val:
                    r.hset("sha@" + key, field, val[field])
                    print("sha@" + key, field, val[field])
            elif isinstance(val, list):
                for ele in val:
                    r.sadd("set@" + key, ele)
                    print("set@" + key, ele)
            else:
                r.set("var@" + key, g_keys[key])
                print("var@" + key, g_keys[key])
    print("建库完成！")

def UpdateScripts(url, cfg, flush = False):
    r = redis.from_url(url)
    print(r)
    if flush:
        r.script_flush()
        print("清理完成！")

    print("更新脚本...")
    if "scripts_src" in cfg:
        src = cfg["scripts_src"]
        for lib in src:
            path = ""
            libnam = lib
            pair = lib.split("@")
            if len(pair) == 2:
                path = pair[0]
                libnam = pair[1]

            if not path.endswith("/") and len(path) > 0:
                path += "/"

            full_lib_name = path + libnam
            if full_lib_name.endswith("/"):
                full_lib_name = full_lib_name[:-1]
            full_lib_name = full_lib_name.replace("/", "_")

            prefix = libnam
            if len(prefix) > 0:
                prefix += "."

            scripts_desc = ""
            scs = src[lib]
            for name in scs:
                sc_path = "lua/" + path + prefix + name + ".lua"
                with open(sc_path, "r") as hd:
                    sc = hd.read()
                    sha = r.script_load(sc)
                    scripts_desc += name + ":" + sha + "|"
                    print("lib@" + full_lib_name, name, sha)
            scripts_desc = scripts_desc[:-1]
            r.set("lib@" + full_lib_name, scripts_desc)
            r.publish("scupdate", "lib@" + full_lib_name + "/" + scripts_desc)
    print("更新脚本完成！")

def Create(path, flush = False):
    with open(path, "r") as hd:
        data = json.loads(hd.read())
        print("执行建库测试...")
        for db_cfg in data:
            if "test_url" in db_cfg:
                DataImport(db_cfg["test_url"], db_cfg, flush = True)
                
        print("测试完成！")
        input("<<<按Enter开始正式建库>>>")
        print("执行正式建库...")
        for db_cfg in data:
            DataImport(db_cfg["url"], db_cfg, flush = flush)

def Update(path, flush = False):
    with open(path, "r") as hd:
        data = json.loads(hd.read())
        print("执行脚本热更...")
        for data_cfg in data:
            UpdateScripts(data_cfg["url"], data_cfg, flush = flush)
            if flush:
                flush = False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("请输入启动选项：")
        print("  <0> <path> [flush_sig] # 建库")
        print("  <1> <path> [flush_sig] # 热更脚本")
    else:
        opt = int(sys.argv[1])
        path = sys.argv[2]
        flush = False
        if len(sys.argv) >= 4:
            flush = True

        if opt == 0:
            Create(path, flush = flush)
        elif opt == 1:
            Update(path, flush = flush)
        else:
            print("未知的命令参数：", sys.argv)
