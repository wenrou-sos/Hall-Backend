@echo off
rem Start SD555 platform lobby stack (local stubbed): redis:6379 stub-api:81 lobbyserver:80 frontend:8082
cd /d %~dp0
start "local-redis" /min python local_redis.py
timeout /t 2 /nobreak >nul
start "stub-apiserver" /min python stub_apiserver.py
timeout /t 2 /nobreak >nul
start "lobbyserver" /min python run_lobby.py
timeout /t 2 /nobreak >nul
start "lobby-frontend" /min python nocache_server.py D:\lobby_fe 8082
echo Lobby stack starting: frontend http://127.0.0.1:8082/  (login via guest; backend ws:80)
pause