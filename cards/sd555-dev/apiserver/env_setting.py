LOCAL_SERVER = False
DEBUG_LOG_MODE = True
PRODUCTION_MODE = False
SIGNINPS_FLAG = False

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
        PS_FORCE_DELETE_GAME = 'https://pg-api.playgems.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
        PS_GETLAUNCHURL_FISH = 'https://pg-api.iplaystar.net/host/getlaunchurl?host_id={0}&game_id={1}&lang={2}&access_token={3}'
    else:
        PS_API_SERVER_URL = 'https://dev-api.iplaystar.net/'
        PS_UNCOMPLETEGAME_URL = 'https://dev-api.iplaystar.net/feed/uncompletedgames?host_id={0}&member_id={1}'
        PS_FORCE_DELETE_GAME = 'https://dev-api.iplaystar.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
        PS_GETLAUNCHURL_FISH = 'https://dev-api.iplaystar.net/host/getlaunchurl?host_id={0}&game_id={1}&lang={2}&access_token={3}'


if PRODUCTION_MODE == True:
    PS_HOST_ID = '2fa00c5c09708683f0dc7fe5cd9a8e7c'
    PS_HOST_ID_S = '12c68ff93b5607c5465413b403aaa8d2'
    PS_HOST_NAME_S = 'SD555-APP_S'
    PS_HOST_ID_T = '15b41411999301f5a178af526f31cb14'
    SD555_LOBBY_URL = 'https://sd555app.sd555.online/'
    SD555_LOBBY_IP = '10.148.0.22:80'
    Linegame_mgm = 'https://liff.line.me/1657336251-5bP0npjW?type=mgm&sub=game-room&sender_line_uid='
else:
    PS_HOST_ID = '42e003738ca75828e0d3be6e5d6fb7ec'
    PS_HOST_ID_S = 'fc9d7ccaa683e4877868e3c6579e35da'
    PS_HOST_NAME_S = 'SD555-APP_S'
    PS_HOST_ID_T = '42f6917a405848e918df5ff62b837421'
    SD555_LOBBY_URL = 'https://dev-sd555lobby.sd555.online/home/'
    SD555_LOBBY_IP = '10.148.0.6:80'
    Linegame_mgm = 'https://liff.line.me/1657336238-Vl68Rme3?type=mgm&sub=game-room&sender_line_uid='

DUMMY_LAUNCH_URL = 'https://dummy-br-06.iplaystar.net:9500/launch'
DUMMY_CREATE_ROOM_URL = 'https://dummy-br-06.iplaystar.net:9500/create_room_info'
DUMMY_KING_LAUNCH_URL = 'https://dummy-br-06.iplaystar.net:9700/launch'
DUMMY_KING_CREATE_ROOM_URL = 'https://dummy-br-06.iplaystar.net:9700/create_room_info'
POK_DENG_CREATE_ROOM_URL = 'http://35.221.214.229:1323/set89game'
# POK_DENG_LAUNCH_URL = 'http://192.168.10.74:8080/?/' # TODO for test Timmy
POK_DENG_LAUNCH_URL = 'https://dev-api.iplaystar.net/launch/?' # TODO for test GCP 89 GS
PAI_KANG_LAUNCH_URL = 'https://dev-api.iplaystar.net/launch/?'  # TODO for test GCP 52 GS

AES256_key = "sd555sd555_is_best_sd555_is_best"
AES256_IV = "sd555isbesthahaa"


