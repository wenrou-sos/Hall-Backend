from mysqlassist import ExecutionHandler as ExeHandler

# SQL语句以;;结尾来区分单条查询结尾，所以应避免语句中的数据存在连续;;

class DBHQueryTradeLog(ExeHandler):
    sSQLType = "query_trade"
    sMainSQL = '''SELECT * FROM `game_trade_log` %(cond)s LIMIT %(start_index)d, %(count)d;;'''

    def __init__(self):
        super().__init__(DBHQueryTradeLog.sSQLType, DBHQueryTradeLog.sMainSQL)

class DBHQueryLoginLog(ExeHandler):
    sSQLType = "query_login"
    sMainSQL = '''SELECT * FROM `game_login_log` %(cond)s LIMIT %(start_index)d, %(count)d;;'''

    def __init__(self):
        super().__init__(DBHQueryLoginLog.sSQLType, DBHQueryLoginLog.sMainSQL)

class DBHQueryTableLog(ExeHandler):
    sSQLType = "query_table"
    sMainSQL = '''SELECT * FROM `game_table_log` %(cond)s ORDER BY `vTime` DESC LIMIT %(start_index)d, %(count)d;;'''

    def __init__(self):
        super().__init__(DBHQueryTableLog.sSQLType, DBHQueryTableLog.sMainSQL)

class DBHQueryPlayLog(ExeHandler):
    sSQLType = "query_play"
    #sMainSQL = '''SELECT * FROM `game_play_log` %(cond)s LIMIT %(start_index)d, %(count)d;;'''
    sMainSQL = '''SELECT gp.*, gt.Log AS da FROM `game_play_log` AS gp 
                      INNER JOIN `game_table_log` AS gt ON gp.vRoundID=gt.vRoundID AND %(cond)s ORDER BY gp.vTime DESC 
                      LIMIT %(start_index)d, %(count)d;;'''

    def __init__(self):
        super().__init__(DBHQueryPlayLog.sSQLType, DBHQueryPlayLog.sMainSQL)

class DBHCreateRoom(ExeHandler):
    sSQLType = "db_createroom"
    sMainSQL = '''INSERT INTO `cfg_gameroominfo` (`hash_key`, `host_api_key`, `subgame_id`, `create_time`, `json_options`)
    VALUES ('%(hash_key)s', '%(host_api_key)s', %(subgame_id)d, '%(create_time)s', '%(json_options)s')
    ON DUPLICATE KEY UPDATE `json_options` = '%(json_options)s';;'''

    def __init__(self):
        super().__init__(DBHCreateRoom.sSQLType, DBHCreateRoom.sMainSQL)

class DBHQueryRoom(ExeHandler):
    sSQLType = "query_room"
    sMainSQL = '''SELECT * FROM `cfg_gameroominfo` WHERE `hash_key` = '%(hash_key)s';;'''

    def __init__(self):
        super().__init__(DBHQueryRoom.sSQLType, DBHQueryRoom.sMainSQL)

class DBHDeleteRoom(ExeHandler):
    sSQLType = "delete_room"
    sMainSQL = '''DELETE FROM `cfg_gameroominfo` WHERE `hash_key` = '%(hash_key)s';;'''

    def __init__(self):
        super().__init__(DBHDeleteRoom.sSQLType, DBHDeleteRoom.sMainSQL)

class DBHUpdateRoom(ExeHandler):
    sSQLType = "update_room"
    sMainSQL = '''UPDATE `cfg_gameroominfo` SET `json_options` = '%(json_options)s' 
                    WHERE `hash_key` = '%(hash_key)s';;'''

    def __init__(self):
        super().__init__(DBHUpdateRoom.sSQLType, DBHUpdateRoom.sMainSQL)

class DBHQueryHourdLog(ExeHandler):
    sSQLType = "query_hourlog"
    sMainSQL = '''SELECT * FROM `game_hour_profit` %(cond)s LIMIT %(start_index)d, %(count)d;;'''

    def __init__(self):
        super().__init__(DBHQueryHourdLog.sSQLType, DBHQueryHourdLog.sMainSQL)

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

class DBHAddTradeErrLog(ExeHandler):
    sSQLType = "add_tradeerrlog"
    sMainSQL = '''INSERT INTO `game_trade_err_log`(`txn_id`, `host_key`, `type`, `member_id`, `amount`, `dtm`, `end`) VALUES(
                        '%(txn)s', '%(host)s', %(type)d, '%(memberid)s', %(amount)d, '%(time)s', %(end)d)'''

    def __init__(self):
        super().__init__(DBHAddTradeErrLog.sSQLType, DBHAddTradeErrLog.sMainSQL)

class DBHAddHostErrLog(ExeHandler):
    sSQLType = "add_hosterrlog"
    sMainSQL = '''INSERT INTO `game_host_err_log`(`action_key`, `host_key`, `type`, `action`, `err_code`,`err_descr`, `dtm`) 
                        VALUES('%(txn)s', '%(host)s', %(type)d, '%(action)d', %(err_code)d, '%(err_descr)s', '%(time)s');;'''

    def __init__(self):
        super().__init__(DBHAddHostErrLog.sSQLType, DBHAddHostErrLog.sMainSQL)

class DBHDeleteTradeErrLog(ExeHandler):
    sSQLType = "delete_tradeerrlog"
    sMainSQL = '''DELETE FROM `game_trade_err_log` WHERE `txn_id` = '%(txn)s' AND `host_key` = '%(host)s' AND `type` = %(type)d 
                        AND `member_id` = '%(memberid)s' AND `amount` =  %(amount)d AND `dtm` = '%(time)s' AND `end` = %(end)d;;'''

    def __init__(self):
        super().__init__(DBHDeleteTradeErrLog.sSQLType, DBHDeleteTradeErrLog.sMainSQL)

class DBHDeleteHostErrLog(ExeHandler):
    sSQLType = "delete_hosterrlog"
    sMainSQL = '''DELETE FROM `game_host_err_log` WHERE `action_key` = '%(txn)s' AND `host_key` = '%(host)s' AND `type` = %(type)d 
                        AND `action` = %(action)d AND `err_code` =  %(err_code)d AND `err_descr` =  '%(err_descr)s' 
                        AND `dtm` = '%(time)s';;'''

    def __init__(self):
        super().__init__(DBHDeleteHostErrLog.sSQLType, DBHDeleteHostErrLog.sMainSQL)

class DBSaveLogs(ExeHandler):
    sSQLType = "save_logs"
    sMainSQL = '''INSERT INTO `%(col)s` (`Log`)VALUE ('%(json_data)s');;'''

    def __init__(self):
        super(DBSaveLogs, self).__init__(DBSaveLogs.sSQLType, DBSaveLogs.sMainSQL)

class DBSecondaryRecharge(ExeHandler):
    sSQLType = "secondary_recharge"
    sMainSQL = '''SELECT `amount`,`type` FROM `game_trade_log` WHERE `member_id` = '%(memberid)s' ORDER BY dtm DESC LIMIT 1;;'''

    def __init__(self):
        super(DBSecondaryRecharge, self).__init__(DBSecondaryRecharge.sSQLType, DBSecondaryRecharge.sMainSQL)

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

class DBGetGameShareResultErrLog(ExeHandler):
    sSQLType = "get_game_share_result_err_log"
    sMainSQL = '''SELECT * FROM `game_share_result_err_log` WHERE `member_id` = '%(member_id)s' AND 
    `gold` = %(gold)d AND `game_id` = '%(game_id)s' AND `subgame_id` = %(subgame_id)d;;'''

    def __init__(self):
        super().__init__(DBGetGameShareResultErrLog.sSQLType, DBGetGameShareResultErrLog.sMainSQL)

class DBDeleteGameShareResultErrLog(ExeHandler):
    sSQLType = "delete_game_share_result_err_log"
    sMainSQL = '''DELETE FROM `game_share_result_err_log` WHERE `member_id` = '%(member_id)s' AND 
    `gold` = %(gold)d AND `game_id` = '%(game_id)s' AND `subgame_id` = %(subgame_id)d;;'''

    def __init__(self):
        super().__init__(DBDeleteGameShareResultErrLog.sSQLType, DBDeleteGameShareResultErrLog.sMainSQL)

class DBGetSn(ExeHandler):
    sSQLType = "get_sn"
    sMainSQL = '''SELECT `sn` FROM `accounting` WHERE `member_id` = '%(member_id)s' AND 
    `total_win` = %(total_win)d AND `bet` = %(bet)d AND `game_id` = '%(game_id)s' AND 
    `subgame_id` = %(subgame_id)d;;'''

    def __init__(self):
        super().__init__(DBGetSn.sSQLType, DBGetSn.sMainSQL)

class DBInsertPSAccounting(ExeHandler):
    """寫遊戲記錄到 slot-game.accounting 表"""
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

class DBSelect_Player_Cent(ExeHandler):
    """從slot-game.member表，查詢player_cent"""
    sSQLType = "select_player_cent"
    sMainSQL = '''SELECT player_cent FROM member WHERE host_id='%(host_id)s' AND id='%(id)s' FOR UPDATE;;'''

    def __init__(self):
        super().__init__(DBSelect_Player_Cent.sSQLType, DBSelect_Player_Cent.sMainSQL)

class DBGetPSAccountingSN(ExeHandler):
    """取得 slot-game.accounting 表內尚未結束的 SN 值"""
    sSQLType = "get_ps_db_accounting_sn"
    sMainSQL = '''SELECT `sn` FROM `accounting` 
    WHERE `game_id`='%(game_id)s' AND `member_id`='%(member_id)s' AND `game_end`=0
    AND `subgame_id`=%(subgame_id)d AND `host_id`='%(host_id)s' 
    ORDER BY begin_time DESC;;'''

    def __init__(self):
        super().__init__(DBGetPSAccountingSN.sSQLType, DBGetPSAccountingSN.sMainSQL)

class DBDeletePSAccounting(ExeHandler):
    sSQLType = "delete_ps_db_accounting"
    sMainSQL = '''DELETE FROM `slot-game`.`accounting` WHERE `sn` = '%(sn)s';;'''

    def __init__(self):
        super().__init__(DBDeletePSAccounting.sSQLType, DBDeletePSAccounting.sMainSQL)

class DBHQueryPlayLogCount(ExeHandler):
    sSQLType = "query_play_count"
    sMainSQL = '''SELECT COUNT(*) AS count FROM `game_play_log` WHERE `vUUID` = '%(uuid)d' AND `vRoundID` = '%(round_id)s';'''

    def __init__(self):
        super().__init__(DBHQueryPlayLogCount.sSQLType, DBHQueryPlayLogCount.sMainSQL)


sSqls = {
    DBHQueryTradeLog.sSQLType : DBHQueryTradeLog(),
    DBHQueryLoginLog.sSQLType : DBHQueryLoginLog(),
    DBHQueryTableLog.sSQLType : DBHQueryTableLog(),
    DBHQueryPlayLog.sSQLType : DBHQueryPlayLog(),
    DBHCreateRoom.sSQLType : DBHCreateRoom(),
    DBHQueryRoom.sSQLType : DBHQueryRoom(),
    DBHDeleteRoom.sSQLType : DBHDeleteRoom(),
    DBHUpdateRoom.sSQLType : DBHUpdateRoom(),
    DBHQueryHourdLog.sSQLType : DBHQueryHourdLog(),
    DBHAddTradeLog.sSQLType : DBHAddTradeLog(),
    DBHAddSharingTradeLog.sSQLType : DBHAddSharingTradeLog(),
    DBHAddTradeErrLog.sSQLType : DBHAddTradeErrLog(),
    DBHAddHostErrLog.sSQLType : DBHAddHostErrLog(),
    DBHDeleteTradeErrLog.sSQLType : DBHDeleteTradeErrLog(),
    DBHDeleteHostErrLog.sSQLType : DBHDeleteHostErrLog(),
    DBSaveLogs.sSQLType : DBSaveLogs(),
    DBSecondaryRecharge.sSQLType : DBSecondaryRecharge(),
    DBGetFaceMemberLockLvList.sSQLType : DBGetFaceMemberLockLvList(),
    DBGetUpgradeThresholdList.sSQLType : DBGetUpgradeThresholdList(),
    DBGetGameShareResultErrLog.sSQLType : DBGetGameShareResultErrLog(),
    DBDeleteGameShareResultErrLog.sSQLType : DBDeleteGameShareResultErrLog(),
    DBGetSn.sSQLType : DBGetSn(),
    DBInsertPSAccounting.sSQLType: DBInsertPSAccounting(),
    DBUpdate_Rollin_Member.sSQLType: DBUpdate_Rollin_Member(),
    DBUpdate_Rollout_Member.sSQLType: DBUpdate_Rollout_Member(),
    DBInsert_Funds_Log.sSQLType: DBInsert_Funds_Log(),
    DBSelect_Player_Cent.sSQLType: DBSelect_Player_Cent(),
    DBGetPSAccountingSN.sSQLType: DBGetPSAccountingSN(),
    DBDeletePSAccounting.sSQLType: DBDeletePSAccounting(),
    DBHQueryPlayLogCount.sSQLType: DBHQueryPlayLogCount()
}
