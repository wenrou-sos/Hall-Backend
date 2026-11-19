@echo off

SET CUR_PATH=%~dp0
SET PROTOC=D:\software\protoc\protobuf-all-3.12.3\protobuf-3.12.3\python\

rem %PROTOC%protoc.exe -I=%CUR_PATH% --python_out=%CUR_PATH% %CUR_PATH%\error.proto

for %%i in (*.proto) Do %PROTOC%protoc.exe -I=%CUR_PATH% --python_out=%CUR_PATH% %CUR_PATH%%%i

pause