from mysqlassist import ExecutionHandler as ExeHandler

# SQL语句以;;结尾来区分单条查询结尾，所以应避免语句中的数据存在连续;;

class DBHSaveBase(ExeHandler):
    sSQLType = "db_savebase"
    sMainSQL = '''
    INSERT INTO `data_user`
    (`ID`, `Account`, `Channel`, `ChlUUID`, `Platform`, `Profit`, `DailyProfit`,
    `LastScoreTime`, `CtrlStatus`, `CtrlScore`, `Restriction`, `Extra`)
    VALUES 
    (%(uid)d, '%(acc)s', '%(chl)s', '%(cuid)s', '%(plt)s', %(pft)ld, %(dpft)ld,
    %(lstst)d, %(cst)d, %(csc)ld, %(rstr)d, '%(ex)s')
    ON DUPLICATE KEY UPDATE
    `ID` = %(uid)d, `Account` = '%(acc)s', `Channel` = '%(chl)s', `ChlUUID` = '%(cuid)s',
    `Platform` = '%(plt)s', `Profit` = %(pft)ld, `DailyProfit` = %(dpft)ld,
    `LastScoreTime` = %(lstst)d, `CtrlStatus` = %(cst)d, `CtrlScore` = %(csc)ld,
    `Restriction` = %(rstr)d, `Extra` = '%(ex)s';;'''

    def __init__(self):
        super().__init__(DBHSaveBase.sSQLType, DBHSaveBase.sMainSQL)

class DBHLoadBase(ExeHandler):
    sSQLType = "db_loadbase"
    sMainSQL = '''
    SELECT * FROM `data_user` %(cond)s LIMIT %(start_index)d, %(count)d;;'''
    def __init__(self):
        super().__init__(DBHLoadBase.sSQLType, DBHLoadBase.sMainSQL)

class DBHSaveChl(ExeHandler):
    sSQLType = "db_savechl"
    sMainSQL = '''
    INSERT INTO `data_channel`
    (`Channel`, `Name`, `APIKey`, `Status`, `TotalReg`, `Servers`, `Extra`)
    VALUES
    ('%(chl)s', '%(nam)s', '%(ak)s', %(st)d, %(tr)d, '%(svrs)s', '%(ex)s')
    ON DUPLICATE KEY UPDATE
    `Channel` = '%(chl)s', `Name` = '%(nam)s', `APIKey` = '%(ak)s',
    `Status` = %(st)d, `TotalReg` = %(tr)d, `Servers` = '%(svrs)s',
    `Extra` = '%(ex)s';;'''

    def __init__(self):
        super().__init__(DBHSaveChl.sSQLType, DBHSaveChl.sMainSQL)

class DBHLoadChl(ExeHandler):
    sSQLType = "db_loadchl"
    sMainSQL = '''
    SELECT * FROM `data_channel` %(cond)s LIMIT %(start_index)d, %(count)d;;'''
    def __init__(self):
        super().__init__(DBHLoadChl.sSQLType, DBHLoadChl.sMainSQL)

class DBHSaveSubGame(ExeHandler):
    sSQLType = "db_savesg"
    sMainSQL = '''
    INSERT INTO `data_SubGameInfo`
    (`UUID`, `ServerID`, `JsonData`)
    VALUES 
    (%(uuid)d, %(svr_id)d, '%(json_data)s') 
    ON DUPLICATE KEY UPDATE 
    `UUID` = %(uuid)d, `ServerID` = %(svr_id)d, `JsonData` = '%(json_data)s';;'''

    def __init__(self):
        super().__init__(DBHSaveSubGame.sSQLType, DBHSaveSubGame.sMainSQL)

class DBHLoadSubGame(ExeHandler):
    sSQLType = "db_loadsg"
    sMainSQL = '''
    SELECT * FROM `data_SubGameInfo` %(cond)s LIMIT %(start_index)d, %(count)d;;'''

    def __init__(self):
        super().__init__(DBHLoadSubGame.sSQLType, DBHLoadSubGame.sMainSQL)

class DBHSaveOnlStatus(ExeHandler):
    sSQLType = "db_save_onlstatus"
    sMainSQL = '''
    INSERT INTO `game_online_record`
    (`Channel`, `Time`, `GameCount`, `TotalCount`)
    VALUES
    ('%(chl)s', FROM_UNIXTIME(%(t)d), %(gc)d, %(tc)d);;'''

    def __init__(self):
        super().__init__(DBHSaveOnlStatus.sSQLType, DBHSaveOnlStatus.sMainSQL)

sExeHandlers = {
    DBHSaveBase.sSQLType : DBHSaveBase(),
    DBHLoadBase.sSQLType : DBHLoadBase(),
    DBHSaveChl.sSQLType : DBHSaveChl(),
    DBHLoadChl.sSQLType : DBHLoadChl(),
    DBHSaveSubGame.sSQLType : DBHSaveSubGame(),
    DBHLoadSubGame.sSQLType : DBHLoadSubGame(),
    DBHSaveOnlStatus.sSQLType  : DBHSaveOnlStatus(),
}