from mysqlassist import ExecutionHandler as ExeHandler

# SQL语句以;;结尾来区分单条查询结尾，所以应避免语句中的数据存在连续;;

class DBHLoadRoomCfg(ExeHandler):
    sSQLType = "load_roomcfg"
    sMainSQL = '''SELECT * FROM `cfg_gameroominfo` WHERE `hash_key` = '%(hash_key)s';;'''

    def __init__(self):
        super(DBHLoadRoomCfg, self).__init__(DBHLoadRoomCfg.sSQLType, DBHLoadRoomCfg.sMainSQL)

class DBHLoadNickName(ExeHandler):
    sSQLType = "load_nickname"
    sMainSQL = '''SELECT `NickName` FROM `cfg_android` ORDER BY RAND() LIMIT %(cnt)d;;'''

    def __init__(self):
        super(DBHLoadNickName, self).__init__(DBHLoadNickName.sSQLType, DBHLoadNickName.sMainSQL)

class DBHLoadAndroidVipName(ExeHandler):
    sSQLType = "load_android_vip_name"
    sMainSQL = '''SELECT `NickName` FROM `cfg_android_vip` ORDER BY RAND() LIMIT %(cnt)d;;'''

    def __init__(self):
        super(DBHLoadAndroidVipName, self).__init__(DBHLoadAndroidVipName.sSQLType, DBHLoadAndroidVipName.sMainSQL)

class DBSaveLogs(ExeHandler):  # 寫入dmgamelog資料庫
    sSQLType = "save_logs"
    sMainSQL = '''INSERT INTO `%(col)s` (`Log`)VALUE ('%(json_data)s');;'''

    def __init__(self):
        super(DBSaveLogs, self).__init__(DBSaveLogs.sSQLType, DBSaveLogs.sMainSQL)

class DBSaveVipLog(ExeHandler):  # 寫入dmgamelog資料庫的vip_log資料表
    sSQLType = "save_vip_log"
    sMainSQL = '''INSERT INTO `%(col)s` (`apikey`, `game_id`, `member_id`, `add_time`) VALUES ('%(apikey)s', '%(game_id)s', '%(member_id)s', '%(add_time)s');;'''

    def __init__(self):
        super(DBSaveVipLog, self).__init__(DBSaveVipLog.sSQLType, DBSaveVipLog.sMainSQL)

class DBSaveVipPlayer(ExeHandler):  # 寫入dmgame資料庫的VIP_player資料表
    sSQLType = "save_vip_player"
    sMainSQL = '''REPLACE INTO `%(col)s` (`apikey`, `game_id`, `member_id`) VALUES ('%(apikey)s', '%(game_id)s', '%(member_id)s');;'''

    def __init__(self):
        super(DBSaveVipPlayer, self).__init__(DBSaveVipPlayer.sSQLType, DBSaveVipPlayer.sMainSQL)

class DBHAddTradeLog(ExeHandler):
    sSQLType = "add_tradelog"
    sMainSQL = '''INSERT INTO `game_trade_log`(`txn_id`, `host_key`, `type`, `member_id`, `amount`, `dtm`) VALUES(
                        '%(txn)s', '%(host)s', %(type)d, '%(memberid)s', %(amount)d, '%(time)s')'''

    def __init__(self):
        super().__init__(DBHAddTradeLog.sSQLType, DBHAddTradeLog.sMainSQL)

class DBHAddSharingTradeLog(ExeHandler):
    sSQLType = "add_sharingtradelog"
    sMainSQL = '''INSERT INTO `game_sharing_trade_log`(`txn_id`, `host_key`, `type`, `member_id`, `amount`, `dtm`) VALUES(
                        '%(txn)s', '%(host)s', %(type)d, '%(memberid)s', %(amount)d, '%(time)s')'''

    def __init__(self):
        super().__init__(DBHAddSharingTradeLog.sSQLType, DBHAddSharingTradeLog.sMainSQL)

class DBHAddHostErrLog(ExeHandler):
    sSQLType = "add_hosterrlog"
    sMainSQL = '''INSERT INTO `game_host_err_log`(`action_key`, `host_key`, `type`, `action`, `err_code`,`err_descr`, `dtm`) 
                        VALUES('%(txn)s', '%(host)s', %(type)d, '%(action)d', %(err_code)d, '%(err_descr)s', '%(time)s');;'''

    def __init__(self):
        super().__init__(DBHAddHostErrLog.sSQLType, DBHAddHostErrLog.sMainSQL)

class DBHDeleteHostErrLog(ExeHandler):
    sSQLType = "delete_hosterrlog"
    sMainSQL = '''DELETE FROM `game_host_err_log` WHERE `action_key` = '%(txn)s' AND `host_key` = '%(host)s' AND `type` = %(type)d 
                        AND `action` = %(action)d AND `err_code` =  %(err_code)d AND `err_descr` =  '%(err_descr)s'
                        AND `dtm` = '%(time)s';;'''

    def __init__(self):
        super().__init__(DBHDeleteHostErrLog.sSQLType, DBHDeleteHostErrLog.sMainSQL)

class DBAddRolloutTimeoutErrLog(ExeHandler):
    sSQLType = "add_rollout_timeout_err"
    sMainSQL = '''INSERT INTO `rollout_timeout_err_log`(`wallet_type`, `txn_id`, `host_key`, `flag`, `member_id`,`amount`, `dtm`) 
                VALUES(%(wallet_type)d, '%(txn_id)s', '%(host_key)s', %(flag)d, '%(member_id)s', %(amount)d, '%(time)s');;'''

    def __init__(self):
        super(DBAddRolloutTimeoutErrLog, self).__init__(DBAddRolloutTimeoutErrLog.sSQLType, DBAddRolloutTimeoutErrLog.sMainSQL)

class DBGetFaceMemberLockLvList(ExeHandler):
    sSQLType = "get_face_member_lock_lv_list"
    sMainSQL = '''SELECT `data` FROM `cfg_threshold` WHERE `name`='face_member_lock_lv';;'''

    def __init__(self):
        super().__init__(DBGetFaceMemberLockLvList.sSQLType, DBGetFaceMemberLockLvList.sMainSQL)

class DBGetUpgradeThresholdList(ExeHandler):
    sSQLType = "get_upgrade_threshold_list"
    sMainSQL = '''SELECT `data` FROM `cfg_threshold` WHERE `name`='upgrade_threshold';;'''

    def __init__(self):
        super().__init__(DBGetUpgradeThresholdList.sSQLType, DBGetUpgradeThresholdList.sMainSQL)

class DBHInsertOnceRefundbetError(ExeHandler):
    sSQLType = "insert_once_refundbet_error"
    sMainSQL = '''INSERT INTO `game_bet_err_log`(`txn_id`, `uuid`, `member_id`, `host_api_key`, `amount`, 
    `status`, `date`) VALUES('%(txn_id)s', %(uuid)d, '%(member_id)s', '%(host_api_key)s', %(amount)d, 
    %(status)d, '%(date)s');;'''

    def __init__(self):
        super().__init__(DBHInsertOnceRefundbetError.sSQLType, DBHInsertOnceRefundbetError.sMainSQL)

class DBHInsertShareResultError(ExeHandler):
    sSQLType = "insert_share_result_error"
    sMainSQL = '''INSERT INTO `game_share_result_err_log`(`txn_id`, `uuid`, `member_id`, 
    `host_api_key`, `gold`, `winamt`, `betamt`, `game_id`, `subgame_id`, `status_code`, `date`) 
    VALUES('%(txn_id)s', %(uuid)d, '%(member_id)s', '%(host_api_key)s', %(gold)d, 
    %(winamt)d, %(betamt)d, '%(game_id)s', %(subgame_id)d, %(status_code)d, '%(date)s');;'''

    def __init__(self):
        super().__init__(DBHInsertShareResultError.sSQLType, DBHInsertShareResultError.sMainSQL)

class DBHGetRetryTimes(ExeHandler):
    sSQLType = "get_retry_times"
    sMainSQL = '''SELECT `api_info` FROM `slot-game`.`host_id` WHERE `host_ext_id`= '%(host_api_key)s';;'''

    def __init__(self):
        super().__init__(DBHGetRetryTimes.sSQLType, DBHGetRetryTimes.sMainSQL)

class DBInsertPSAccounting(ExeHandler):
    sSQLType = "insert_ps_db_accounting"
    sMainSQL = '''INSERT INTO `accounting`(`machine_id`, `host_id`, `host_level`, `begin_time`, `game_time`,
    `game_id`, `subgame_id`, `member_id`, `init_cent`, `bet`, `denom`, `total_win`, `bonus_win`, `gamble_win`,
    `jackpot_win`, `game_data`, `game_result`, `end_cent`, `bonus`, `gamble`, `game_module`, `game_end`, 
    `test_account`) VALUES(%(machine_id)d, '%(host_id)s', %(host_level)d, '%(begin_time)s', '%(game_time)s', 
    '%(game_id)s', %(subgame_id)d, '%(member_id)s', %(init_cent)d, %(bet)d, %(denom)d, %(total_win)d, 
    %(bonus_win)d, %(gamble_win)d, %(jackpot_win)d, '%(game_data)s', '%(game_result)s', %(end_cent)d, 
    %(bonus)d, %(gamble)d, '%(game_module)s', %(game_end)d, %(test_account)d);;'''

    def __init__(self):
        super().__init__(DBInsertPSAccounting.sSQLType, DBInsertPSAccounting.sMainSQL)

class DBInsertPSAccountingRobot(ExeHandler):
    sSQLType = "insert_ps_db_accounting_robot"
    sMainSQL = '''INSERT INTO `accounting_robot`(`machine_id`, `host_id`, `host_level`, `begin_time`, `game_time`,
    `game_id`, `subgame_id`, `member_id`, `init_cent`, `bet`, `denom`, `total_win`, `bonus_win`, `gamble_win`,
    `jackpot_win`, `game_data`, `game_result`, `end_cent`, `bonus`, `gamble`, `game_module`, `game_end`, 
    `test_account`) VALUES(%(machine_id)d, '%(host_id)s', %(host_level)d, '%(begin_time)s', '%(game_time)s', 
    '%(game_id)s', %(subgame_id)d, '%(member_id)s', %(init_cent)d, %(bet)d, %(denom)d, %(total_win)d, 
    %(bonus_win)d, %(gamble_win)d, %(jackpot_win)d, '%(game_data)s', '%(game_result)s', %(end_cent)d, 
    %(bonus)d, %(gamble)d, '%(game_module)s', %(game_end)d, %(test_account)d);;'''

    def __init__(self):
        super().__init__(DBInsertPSAccountingRobot.sSQLType, DBInsertPSAccountingRobot.sMainSQL)

class DBUpdatePSAccounting(ExeHandler):
    sSQLType = "update_ps_db_accounting"
    sMainSQL = '''UPDATE `accounting` SET `machine_id` = %(machine_id)d , `host_id` = '%(host_id)s',
    `host_level` = %(host_level)d , `begin_time` = '%(begin_time)s' , `game_time` = '%(game_time)s',
    `game_id` = '%(game_id)s' , `subgame_id` = %(subgame_id)d , `member_id` = '%(member_id)s',
    `init_cent` = %(init_cent)d , `bet` = %(bet)d , `denom` = %(denom)d , `total_win` = %(total_win)d,
    `bonus_win` = %(bonus_win)d , `gamble_win` = %(gamble_win)d , `jackpot_win` = %(jackpot_win)d ,
    `game_data` = '%(game_data)s' , `game_result` = '%(game_result)s' , `end_cent` = %(end_cent)d ,
    `bonus` = %(bonus)d , `gamble` = %(gamble)d , `game_module` = '%(game_module)s' ,
    `game_end` = %(game_end)d , `test_account` = %(test_account)d WHERE `sn` = %(sn)d;;'''

    def __init__(self):
        super().__init__(DBUpdatePSAccounting.sSQLType, DBUpdatePSAccounting.sMainSQL)

class DBDeletePSAccounting(ExeHandler):
    sSQLType = "delete_ps_db_accounting"
    sMainSQL = '''DELETE FROM `slot-game`.`accounting` WHERE `sn` = '%(sn)s';;'''

    def __init__(self):
        super().__init__(DBDeletePSAccounting.sSQLType, DBDeletePSAccounting.sMainSQL)

class DBUpdate_Rollin_Member(ExeHandler):
    """新增玩家金額到 slot-game.member 表"""
    sSQLType = "update_rollin_member"
    sMainSQL = '''UPDATE member 
    SET `player_cent` = `player_cent` + '%(amount)d' 
    WHERE `host_id`='%(host_id)s' AND `id`='%(id)s';;'''

    def __init__(self):
        super().__init__(DBUpdate_Rollin_Member.sSQLType, DBUpdate_Rollin_Member.sMainSQL)

class DBUpdate_Rollout_Member(ExeHandler):
    """取出玩家金額到 slot-game.member 表"""
    sSQLType = "update_rollout_member"
    sMainSQL = '''UPDATE member 
    SET `player_cent` = `player_cent` - '%(amount)d' 
    WHERE `host_id`='%(host_id)s' AND `id`='%(id)s' AND `player_cent` >= '%(amount)d';;'''

    def __init__(self):
        super().__init__(DBUpdate_Rollout_Member.sSQLType, DBUpdate_Rollout_Member.sMainSQL)

class DBInsert_Funds_Log(ExeHandler):
    """新增交易紀錄到 slot-game.funds_log 表"""
    sSQLType = "insert_funds_log"
    sMainSQL = '''INSERT INTO funds_log (txn_id,type,host_id,member_id,amount,balance,note) 
    VALUES ('%(txn_id)s','%(type)d','%(host_id)s','%(member_id)s','%(amount)d',(SELECT player_cent FROM member WHERE host_id='%(host_id)s' AND id='%(id)s'),'%(note)s');;'''

    def __init__(self):
        super().__init__(DBInsert_Funds_Log.sSQLType, DBInsert_Funds_Log.sMainSQL)

sSqls = {
    DBHLoadRoomCfg.sSQLType : DBHLoadRoomCfg(),
    DBHLoadNickName.sSQLType : DBHLoadNickName(),
    DBHLoadAndroidVipName.sSQLType : DBHLoadAndroidVipName(),
    DBSaveLogs.sSQLType : DBSaveLogs(),
    DBSaveVipLog.sSQLType : DBSaveVipLog(),
    DBSaveVipPlayer.sSQLType : DBSaveVipPlayer(),
    DBHAddTradeLog.sSQLType : DBHAddTradeLog(),
    DBHAddSharingTradeLog.sSQLType : DBHAddSharingTradeLog(),
    DBHAddHostErrLog.sSQLType : DBHAddHostErrLog(),
    DBHDeleteHostErrLog.sSQLType : DBHDeleteHostErrLog(),
    DBAddRolloutTimeoutErrLog.sSQLType : DBAddRolloutTimeoutErrLog(),
    DBGetFaceMemberLockLvList.sSQLType: DBGetFaceMemberLockLvList(),
    DBGetUpgradeThresholdList.sSQLType: DBGetUpgradeThresholdList(),

    DBHInsertOnceRefundbetError.sSQLType: DBHInsertOnceRefundbetError(),
    DBHInsertShareResultError.sSQLType: DBHInsertShareResultError(),
    DBHGetRetryTimes.sSQLType: DBHGetRetryTimes(),

    DBInsertPSAccounting.sSQLType: DBInsertPSAccounting(),
    DBInsertPSAccountingRobot.sSQLType: DBInsertPSAccountingRobot(),
    DBUpdatePSAccounting.sSQLType: DBUpdatePSAccounting(),
    DBDeletePSAccounting.sSQLType: DBDeletePSAccounting(),
    DBUpdate_Rollin_Member.sSQLType: DBUpdate_Rollin_Member(),
    DBUpdate_Rollout_Member.sSQLType: DBUpdate_Rollout_Member(),
    DBInsert_Funds_Log.sSQLType: DBInsert_Funds_Log(),
}