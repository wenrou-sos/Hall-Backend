
from handlers import *

sUrls = [
    (r"/", OnHandler),
    (r"/launch", HDRRequestGame),
    (r"/traderecords", HDRQueryTradeLog),
    (r"/onlineinfo", HDROnlineInfo),
    # (r"/numofsingleinmulti", HDRNumOfSingleInMulti),
    (r"/loginrecords", HDRLoginRecords),
    (r"/forcelogout", HDRForceLogout),
    (r"/getscore", HDRGetScore),
    (r"/rollout", HDRRollOut),

    (r"/tablerecords", HDRQueryTableLog),
    (r"/playrecords", HDRQueryPlayLog),
    (r"/hourrecords", HDRQueryPlayerHourLog),
    (r"/dayrecords", HDRQueryPlayerDayLog),

    (r"/newsvrcfg", HDRCreateServerConfig),
    (r"/getsvrcfg", HDRGetServerConfig),
    (r"/modsvrcfg", HDRUpdateServerConfig),
    (r"/delsvrcfg", HDRDeleteServerConfig),

    (r"/newchl", HDRCreateChannel),
    (r"/getchl", HDRGetChannelInfo),
    (r"/modchl", HDRModChannelInfo),
    (r"/delchl", HDRDeleteChannel),
    
    (r"/newsvropt", HDRCreateServerOption),
    (r"/getsvropt", HDRGetServerOption),
    (r"/modsvropt", HDRUpdateServerOption),
    (r"/delsvropt", HDRDeleteServerOption),

    (r"/newmultihostinf", HDRInsertMultiHostInformation),
    (r"/getmultihostinf", HDRGetMultiHostInformation),
    (r"/delmultihostinf", HDRDeleteMultiHostInformation),

    (r"/setbotname", HDRSetAndroidOption),
    (r"/setbotvip", HDRSetAndroidVip),
    (r"/excepplayer", HDRExcepplayer),
    (r"/healthcheck", HDRHealthcheck),
    (r"/versionjson", HDRVersionJson),
    (r"/loginhistory", HDRGetLoginHistory),
    (r"/gettradeerrlog", HDRGetTradeErrLog),
    (r"/rectradelog", HDRRecoveryTradeLog),
    # (r"/multihostscore", HDRMultiHostScore),
    (r"/banplayer", HDRBanPlayer),
    (r"/gameserverlist", HDRGameServerList),
    (r"/dismissgame", HDRDisMissGame),
    (r"/hosturl", HDRHosturl),
    (r"/wallettype", HDRWalletType),
    (r"/vipplayer", HDRVIPPlayer),

    (r"/singlechlhostuuid", HDRSingleChlHostUUID),
    (r"/serverlist", HDRServerlist),
    (r"/multionlogout", HDRMultiOnLogout),
    (r"/synctoken", HDRSyncToken),
    (r"/hostmaintain", HDRHostMainTain),

    (r"/psaskresultex", HDRPsAskResultEx),

    (r"/writeslotgameaccounting", HDRWriteSlotGameAccounting),
    (r"/getslotgameaccountingsn", HDRGetSlotGameAccountingSN),
]