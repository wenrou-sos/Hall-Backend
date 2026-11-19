# 棋牌 B 组收尾报告（2026-11-17）

## 结论
- **跑通 2/4 服务端**：u-game-server(124)→8914、colorgame(154)→8916，dev 构建、LISTENING、WS 握手 101 并回二进制帧。
- **6/6 客户端已 serve**：8097–8102 全部 LISTENING，HTTP 200；WS 地址全部 patch 到本地对应端口。
- **失败 2 项**：dummy-king(201)→8913 **源码在所有可用备份中缺失**；tongits(178)→8915 **实为 Python 旧服务端栈**，非 Go，无法走 build_b.ps1 管线，本轮未启动（超出已批准的 Go 编译范围，见建议）。
- 映射：`fish/lobby/cards_map_B.json`（6 个 PSC id，按任务给定形状；8913/8915 为规划端口，当前未监听）。

## 一、做了什么

### 服务端（Go，复用上一轮已编译产物）
| 家族 | repo id | 源码 | 端口 | 状态 |
|---|---|---|---|---|
| u-game-server | 124 | fish/cards/u-game-server（master，app.exe 上一轮 19:33 已编译，deps_u-game-server 32 项） | 8914 | 本轮启动，LISTENING |
| colorgame | 154 | fish/cards/colorgame（master，app.exe 已编译，deps_colorgame 26 项） | 8916 | 本轮启动，LISTENING |
| dummy-king | 201 | **缺失**（见三） | 8913 | 未启动 |
| tongits | 178 | fish/cards/tongits = Python server_dummy（无 go.mod，全 16 分支均同） | 8915 | 未启动 |

- 启动 env：HTTP_PORT/SERVER_NAME=<name>-dev/LOG_LEVEL=0/POOL_SIZE=100/CHAN_SIZE=102400/VERSION=dev；日志 fish/lobby/<name>.out.log / .err.log。
- 启动脚本固化：`fish/lobby/start_b.ps1 -name <n> -port <p>`。
- endpoint 核实：u-game-server presentation/playerU/controllerU.go:48 与 colorgame presentation/playerFS/controllerFS.go:48 均 `endPoint="card"`；各自 PSC-ON-00013 / PSC-ON-00016 分支亦为 "card"（u master↔00013 分支仅差 banker.go 19 行，未换分支，沿用已验证 master 构建）。

### 客户端（nocache_server.py，serve D:\games_wc\<id>\trunk）
| PSC id | 端口 | 工程类型 | WS patch 位置 | 改后地址 |
|---|---|---|---|---|
| PSC-ON-00010 | 8097 | Cocos Creator 源码工程 | assets/Script/AppManager/NetManager.js:16 | ws://127.0.0.1:8913/service/ |
| PSC-ON-00011 | 8098 | 同上 | 同上 | ws://127.0.0.1:8913/service/ |
| PSC-ON-00013 | 8099 | cocos2d-x JS（有 index.html） | src/g_message.js:72 | ws://127.0.0.1:8914/card |
| PSC-ON-00014 | 8100 | 同上 | src/g_message.js:73 | ws://127.0.0.1:8914/card |
| PSC-ON-00015 | 8101 | Cocos Creator 源码工程 | assets/Script/AppManager/NetManager.js:16 | ws://127.0.0.1:8915/service/ |
| PSC-ON-00016 | 8102 | cocos2d-x JS | src/g_message.js:65 | ws://127.0.0.1:8916/card |

- Creator 三客户端无 g_message.js；其 WS 在 NetManager.login 动态拼 `Constants.wsExtend + ip + ":" + port + "/service/"`（wsExtend 为空串、ip/port 来自平台服务器列表）。等价最小 patch：整行替换为固定本地 URL（原写法保留在行尾注释）。"/service/" 与 Python server_dummy game 组件 urls.py 的 WS 路由一致（gitlab tongits trunk/server_dummy/dummy/game/urls.py）。
- 00016 原活动行是 /arcade（旧 arcade 平台），colorgame 服务端只有 /card（全仓库无 "arcade" 字符串；其注释行留有 ws://127.0.0.1:8699/card 本地测试痕迹），故按服务端实际 endpoint 改为 /card。

### 回退清单（原值）
- 00013 g_message.js:72 原：`socket= new WebSocket("ws://192.168.10.51:8765/card");//KYE`
- 00014 g_message.js:73 原：`socket= new WebSocket("ws://192.168.10.25:8899/card");`
- 00016 g_message.js:65 原：`socket= new WebSocket('ws://192.168.15.60:8787/arcade');`
- 00010/00011/00015 NetManager.js:16 原：`this.url = Constants.wsExtend + ip + ":" + port + "/service/";`
- 其余为新增文件/进程，无覆盖。停服：taskkill /PID 210696（u）/207820（colorgame）；静态服务 PID 见 netstat 8097–8102。

### 本轮新增资产/脚本
- fish/lobby/scan_svn_server_dirs.py + .log：svn.tar.gz 全量扫（5,239,967 条目），srv/svn/server/ 90 个顶层目录清单。
- fish/lobby/extract_server_wc.py + .log：定向提取 srv/svn/server/git/**（含 .git）与 tongits-server 工作副本（去 .svn）→ D:\server_wc（18,053 文件）。git/ 仅 4 个 C++ 库：mysql-connector-c-6.1.6、poco-1.6.0 及两个变体。
- fish/scm_b/ps-scm/repositories/svn/server/tongits-server：从 ps-scm.zip 提取的 SVN 仓库（r133，2.3MB，svnlook 确认 trunk=Python server_dummy，14 分支无 Go）。
- fish/tools/sliksvn/PFiles/bin/：svn.exe/svnadmin.exe/svnlook.exe 等（Slik-Subversion-1.14.5 MSI 管理式解包，未安装进系统；原 sliksvn.zip 为残缺下载，已重下 fish/tools/slik.zip）。
- fish/lobby/extract_servers_b2.py：本地源码→deps 管线复用脚本（本轮未用上，备 Go 源码出现时使用）。
- fish/lobby/start_b.ps1、cards_map_B.json、b_tar_members_full.txt（gitlab tar 全 562 成员清单）。

## 二、验证了什么（均为实际运行观察）
1. **端口层**：netstat 两次（启动后、收尾）——8914/8916 LISTENING（PID 210696/207820，进程存活复核）；8097–8102 全部 LISTENING；8913/8915 无监听（失败项如实记录）。
2. **HTTP 层**：6 个客户端端口 GET /project.json 均 200（两次）；8099/8100/8102 GET /index.html 均 200。Creator 三工程无 index.html（源码工程，见三）。
3. **WS 集成层**：curl 升级请求 → 8914/card 与 8916/card 均回 `HTTP/1.1 101 Switching Protocols` + 正确 Sec-WebSocket-Accept，并立即下发二进制帧；colorgame 日志显示该测试连接完整走完 GameUser 创建→断开→删除生命周期（game-user/service.go:122 "Delete Game User"）。
4. **patch 完整性（检视+运行读取）**：三个 g_message.js 各仅 1 条活动 new WebSocket 行且已指向本地；三个 NetManager.js:16 已替换（读回核对）。
5. **源码缺失结论（运行证据）**：gitlab tar 全成员清单 562 条，141 个项目 bundle 逐一按 sha256(id) 匹配 projects.json，**无 bundle 的 5 个项目恰为 201/199/94/200/104**（dummy 系服务端+training）；artifacts/uploads 内无 dummy/king/tongits；svn 全量扫描 90 个 server 目录无 dummy-king；ps-scm.zip 636 仓库无 dummy-king；server/git/ 实提仅 C++ 库。
6. **tongits 性质（运行证据）**：gitlab 178 全 16 分支 ls-tree 均为 docker 配置+trunk Python（211 文件，无 go.mod）；SVN 仓库 svnlook tree 同；docker_env/requirements.txt=protobuf/tornado/pymysql/redis/hiredis/xxtea/pycrypto/apscheduler。

## 三、没验证什么 / 失败项与建议

### 失败项 1：dummy-king(201) → 8913
- **根因**：GitLab 备份 tar 中该项目 bundle 缺失（备份时即不在 @hashed 存储），SVN 两备份亦无其服务端仓库/工作副本。客户端 00010/00011 已 serve 并 patch 到 8913/service/，但无服务端可连。
- 未验证：8913 无任何监听；dummy-king 游戏协议链路完全未测。
- 建议（交父 agent 决策）：a) 寻找其他备份源（如原始 GitLab 服务器磁盘、bu02 部署机镜像）；b) 若接受 Python 栈，dummy-king 与 tongits 同属 server_dummy 框架（proto 完全一致：c_g_game/dummy/main_cmd/heartbeat/error，见 00010/trunk/Protobuf/Protocols），可评估用 tongits 的 Python 框架换 subgame 逻辑承载——但 gamelogic 是否兼容需专门核对，本轮未做。

### 失败项 2：tongits(178) → 8915
- **根因**：任务前提（Go 编译）不成立。178 是 Python server_dummy 四进程架构（center/game/service/assist，tornado+pymysql+redis+protobuf 3.x），game 组件 WS 路由 /service/ 与 00015 客户端吻合，是真实服务端，但本机 Python 3.13+protobuf 7.36 与旧代码/旧生成码不兼容，且需 MySQL（dmgame.sql schema 在 trunk 内）、支持 Lua 的真 Redis（local_redis.py 桩无 EVAL）、平台 API 桩（ps_urls: getcardshoe/getbalance/rollin/rollout/login/logout）。
- 未验证：8915 无监听；00015 协议链路未测。
- 建议（超出本轮已批准 Go 范围，未动手）：按 A 组大厅本地化同法立项——Python 3.7 嵌入式+旧版依赖（或逐文件移植 3.13）、mysql-5.7.44.zip（已在 fish/tools）初始化+导 schema、Windows Redis 5.x、grpcio-tools 重生成 proto、扩展 stub_apiserver.py、四进程 cfg 编排。预估工作量与 A 组大厅相当（数小时级、多迭代）。

### 其他未验证（范围/环境所限）
- **浏览器渲染未测**：00013/00014/00016 为 cocos2d-x JS 工程，index.html/main.js/引擎文件齐备且 HTTP 200，但未在真实浏览器跑 boot（本环境无浏览器验证步骤，任务验收口径为端口 Listen）。00010/00011/00015 为 **Cocos Creator 源码工程，trunk 内无 web 构建产物**（仅 build-templates/web-mobile 模板）——静态 serve 无法直接在浏览器渲染，需 Cocos Creator 构建 web-mobile（与 A 组 PSC-ON-00002 同样局限）。
- Creator 客户端登录依赖平台 HTTP（Constants.sUrl=http://192.168.10.94:9400/，已死）取服务器列表/launch；WS patch 只保证连接地址正确，登录闭环未测（需平台桩，超出本轮范围）。
- Go 服务端仅验证到 WS 握手+连接生命周期；登录/对局协议需客户端+平台桩联调，未测。
- u-game-server 用 master 而非 PSC-ON-00013 分支（差 19 行 banker.go）；colorgame 用 master 而非 PSC-ON-00016 分支——分支差异对玩法的影响未评估。

### 复跑命令
```powershell
# 端口
netstat -ano | Select-String ':(8913|8914|8915|8916|8097|8098|8099|8100|8101|8102)\s.*LISTENING'
# WS 握手（预期 101）
curl.exe -s -i --max-time 4 -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" http://127.0.0.1:8914/card
# 重启 Go 服务端
powershell -File fish\lobby\start_b.ps1 -name u-game-server -port 8914
powershell -File fish\lobby\start_b.ps1 -name colorgame -port 8916
# 重 serve 某客户端
python fish\lobby\nocache_server.py D:\games_wc\PSC-ON-00013\trunk 8099
```