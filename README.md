# Hall-Backend（PlayStar 服务端：捕鱼/棋牌 Go + 大厅 WS stub）

dev 模式**无需 MySQL/Redis/素材**，clone 即可跑。

## 环境
- Go 1.14（旧依赖需 1.14；自行安装或用一个 Go1.14 发行版）
- Python 3 + `pip install aiohttp protobuf`（大厅 WS stub 用）

## 目录
- Fish-Game-Server/ 捕鱼 Go 服务端
- cards/{89-game-server,paikang52,u-game-server,colorgame,fishshrimpcrab} 棋牌 Go 服务端
- deps/ 27 个内部依赖（go.mod replace 指向这里）
- lobby/ 大厅 WS stub(pslobby_ws_stub.py:8084/lobby) + 全部修复/构建脚本 + playable_games.json(白名单)
- deploy/ 交叉编译/打包/上传/服务器修复脚本

## 构建（Windows 本地 dev）
设环境变量（GOPATH/GOCACHE/GOPROXY=https://goproxy.cn,direct GOSUMDB=off GOFLAGS=-mod=mod GOPRIVATE=gitlab.iplaystar.net），
用 `lobby/rebuild_cards.ps1`、`lobby/rebuild_fish_all.ps1`（脚本内 GOROOT 指向自带 Go，需按本机调整）。
Linux 交叉：`deploy/build_linux.ps1`（GOOS=linux GOARCH=amd64 CGO_ENABLED=0 -tags dev）。

## 跑（本地）
- 大厅 stub：`python lobby/pslobby_ws_stub.py`（:8084/lobby，读 playable_games.json）
- 捕鱼：Fish-Game-Server dev build :8899/fish
- 棋牌：89→8901/card、52→8911/card、u4→8914/card（CWD=各服务端目录，env HTTP_PORT/SERVER_NAME/VERSION=dev）
- 前端：clone Hall-Frontend，fetch_assets.py 拉素材，静态服务 :8083

## 公网现成环境
http://82.158.228.38:8888/ ；服务器 /data/playstar 已部署（systemd: playstar-fish/card89/card52/cardu4/lobby）。
deploy/ 脚本可增量上传/修复（paramiko，密码见交接手册）。

## 关键修复（已内置于源码/脚本）
- 概率表 runtime.Caller 绝对路径→相对（patch_prob_relative.py）
- 棋牌 dev-stub 五层修法（accounting nil 守卫/wallet cent/89 deposit/lobbysetting/gamesetting）
- 多语言回退（restore_lang_fallback.py）
详见交接手册.md（项目根）。