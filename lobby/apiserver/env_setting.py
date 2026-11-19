LOCAL_SERVER = True
DEBUG_LOG_MODE = True
PRODUCTION_MODE = False
SIGNINPS_FLAG = True

if LOCAL_SERVER == True:
    # PS_API_SERVER_URL = 'https://pg-api.playgems.net/'
    PS_API_SERVER_URL = 'https://dev-api.iplaystar.net/'
    PS_UNCOMPLETEGAME_URL = 'https://dev-api.iplaystar.net/feed/uncompletedgames?host_id={0}&member_id={1}'
    PS_FORCE_DELETE_GAME = 'https://dev-api.iplaystar.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
    PS_GETLAUNCHURL_FISH = 'https://dev-api.iplaystar.net/host/getlaunchurl?host_id={0}&game_id={1}&lang={2}&access_token={3}'
else:
    if PRODUCTION_MODE == True:
        PS_API_SERVER_URL = 'http://pg-api.playgems.net/'
        PS_UNCOMPLETEGAME_URL = 'http://pg-api.playgems.net/feed/uncompletedgames?host_id={0}&member_id={1}'
        PS_FORCE_DELETE_GAME = 'http://pg-api.playgems.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
        PS_GETLAUNCHURL_FISH = 'https://playgems-api.iplaystar.net/host/getlaunchurl?host_id={0}&game_id={1}&lang={2}&access_token={3}'
    else:
        PS_API_SERVER_URL = 'https://dev-api.iplaystar.net/'
        PS_UNCOMPLETEGAME_URL = 'https://dev-api.iplaystar.net/feed/uncompletedgames?host_id={0}&member_id={1}'
        PS_FORCE_DELETE_GAME = 'https://dev-api.iplaystar.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
        PS_GETLAUNCHURL_FISH = 'https://dev-api.iplaystar.net/host/getlaunchurl?host_id={0}&game_id={1}&lang={2}&access_token={3}'


if PRODUCTION_MODE == True:
    PS_HOST_ID = '2fa00c5c09708683f0dc7fe5cd9a8e7c'
    PS_HOST_ID_S = '12c68ff93b5607c5465413b403aaa8d2'
    PS_HOST_ID_T = '15b41411999301f5a178af526f31cb14'
else:
    PS_HOST_ID = '9f6301a3d76cdb56de4b747ecc999e6b'
    PS_HOST_ID_S = 'a7f2403adb0fd1fb885828b253f709cf'
    PS_HOST_ID_T = '486b194456a1b202254493db18894350'