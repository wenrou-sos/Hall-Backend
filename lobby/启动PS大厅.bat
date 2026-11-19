@echo off
rem Start PlayStar PS-LOBBY stack: ws-stub:8084 + frontend:8083 (fish game stack separate: 8080/8899)
cd /d %~dp0
start "pslobby-ws-stub" /min python pslobby_ws_stub.py
timeout /t 2 /nobreak >nul
start "pslobby-frontend" /min python nocache_server.py D:\pslobby_wc\trunk 8083
echo PS-LOBBY: http://127.0.0.1:8083/?access_token=dev^&lang=eng
echo (login auto via WS stub; click FISH game -> local fish 8080)
pause