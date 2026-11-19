import os
import env_setting


#HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 80))

if env_setting.LOCAL_SERVER:
    apiserver = 'http://127.0.0.1:81'
else:
    if env_setting.PRODUCTION_MODE == True:
        apiserver = 'http://production-jinsong-apiserver.playgems.net:81'
    else:
        apiserver = 'http://10.148.0.2:81'


