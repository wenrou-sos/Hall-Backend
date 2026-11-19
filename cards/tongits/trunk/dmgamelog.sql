/*
 Navicat Premium Data Transfer

 Source Server         : 192.168.1.106(linux)
 Source Server Type    : MySQL
 Source Server Version : 50725
 Source Host           : 192.168.1.106:3306
 Source Schema         : dmgamelog

 Target Server Type    : MySQL
 Target Server Version : 50725
 File Encoding         : 65001

 Date: 18/05/2020 13:27:33
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for game_channel_profit
-- ----------------------------
DROP TABLE IF EXISTS `game_channel_profit`;
CREATE TABLE `game_channel_profit`  (
  `time` datetime(0) NULL DEFAULT NULL,
  `channel` varchar(8) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT '0',
  `profit` bigint(20) NULL DEFAULT 0
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_hour_profit
-- ----------------------------
DROP TABLE IF EXISTS `game_hour_profit`;
CREATE TABLE `game_hour_profit`  (
  `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `host_api_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '代理',
  `member_id` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'PS玩家ID',
  `subgame_id` int(11) NOT NULL COMMENT '服务器ID',
  `profit` bigint(20) NOT NULL COMMENT '盈亏',
  `count` int(11) NOT NULL COMMENT '总场次',
  `time` datetime(0) NOT NULL COMMENT '统计时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `serverid_index`(`subgame_id`) USING BTREE,
  INDEX `memberid_index`(`member_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 519 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_login_log
-- ----------------------------
DROP TABLE IF EXISTS `game_login_log`;
CREATE TABLE `game_login_log`  (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `vHostApiKey` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.host_api_key'),'"','')) VIRTUAL NULL,
  `vMemberId` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.member_id'),'"','')) VIRTUAL NULL,
  `vSubGameId` int(11) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.subgame_id'),'"','')) VIRTUAL NULL,
  `vTime` datetime(0) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.time'),'"','')) VIRTUAL NULL,
  `vUUID` bigint(20) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.uuid'),'"','')) VIRTUAL NULL,
  `vType` int(11) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.logType'),'"','')) VIRTUAL COMMENT '3：登入子游戏 4：登出子游戏' NULL,
  `Log` json NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `type_virtual_index`(`vHostApiKey`) USING BTREE,
  INDEX `uuid_virtual_index`(`vUUID`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1448 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_online_record
-- ----------------------------
DROP TABLE IF EXISTS `game_online_record`;
CREATE TABLE `game_online_record`  (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Channel` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `Time` datetime(0) NULL DEFAULT NULL,
  `GameCount` int(11) NULL DEFAULT NULL,
  `TotalCount` int(11) NULL DEFAULT NULL,
  PRIMARY KEY (`ID`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_play_log
-- ----------------------------
DROP TABLE IF EXISTS `game_play_log`;
CREATE TABLE `game_play_log`  (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `vUUID` bigint(20) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.uuid'),'"','')) VIRTUAL NULL,
  `vChairID` int(11) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.chairID'),'"','')) VIRTUAL NULL,
  `vRoundID` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.roundID'),'"','')) VIRTUAL NULL,
  `vHostApiKey` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.hostapikey'),'"','')) VIRTUAL NULL,
  `vMemberID` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.memberID'),'"','')) VIRTUAL NULL,
  `vHashKey` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.hashkey'),'"','')) VIRTUAL NULL,
  `vSubGameID` int(11) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.subgameid'),'"','')) VIRTUAL NULL,
  `vCalScore` bigint(20) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.calScore'),'"','')) VIRTUAL NULL,
  `vCurScore` bigint(20) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.curScore'),'"','')) VIRTUAL NULL,
  `vTax` bigint(20) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.tax'),'"','')) VIRTUAL NULL,
  `vTime` datetime(0) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.time'),'"','')) VIRTUAL NULL,
  `vStatus` int(11) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.status'),'"','')) VIRTUAL COMMENT '此資料 1:須同步 0:不須同步' NULL,
  `Log` json NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `serverid_index`(`vHashKey`) USING BTREE,
  INDEX `uuid_index`(`vUUID`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 970 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_profit
-- ----------------------------
DROP TABLE IF EXISTS `game_profit`;
CREATE TABLE `game_profit`  (
  `Date` bigint(20) NOT NULL,
  `ServerID` int(11) NOT NULL,
  `Profit` bigint(20) NOT NULL,
  UNIQUE INDEX `Index`(`Date`, `ServerID`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_table_log
-- ----------------------------
DROP TABLE IF EXISTS `game_table_log`;
CREATE TABLE `game_table_log`  (
  `ID` bigint(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `vRoundID` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.roundid'),'"','')) VIRTUAL COMMENT '游戏局号' NOT NULL,
  `vHashKey` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.hashkey'),'"','')) VIRTUAL COMMENT '服务器ID' NOT NULL,
  `vHostApiKey` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.hostapikey'),'"','')) VIRTUAL NULL,
  `vSubGameID` int(11) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.subgameid'),'"','')) VIRTUAL NULL,
  `vTime` datetime(0) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.time'),'"','')) VIRTUAL COMMENT '游戏结束时间' NULL,
  `vStatus` int(11) GENERATED ALWAYS AS (replace(json_extract(`Log`,_utf8'$.status'),'"','')) VIRTUAL COMMENT '此資料 1:須同步 0:不須同步' NULL,
  `Log` json NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  UNIQUE INDEX `index_round_id`(`vRoundID`) USING BTREE COMMENT '游戏局号'
) ENGINE = InnoDB AUTO_INCREMENT = 411 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for vip_log
-- ----------------------------
DROP TABLE IF EXISTS `vip_log`;
CREATE TABLE `vip_log`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `apikey` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '密钥',
  `game_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '遊戲id',
  `member_id` varchar(127) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '玩家id',
  `add_time` varchar(127) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '加入vip時間',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 0 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_trade_err_log
-- ----------------------------
DROP TABLE IF EXISTS `game_trade_err_log`;
CREATE TABLE `game_trade_err_log`  (
  `txn_id` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `host_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `type` int(11) NOT NULL COMMENT '0 转入 1 转出',
  `member_id` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `amount` bigint(20) NOT NULL COMMENT '单位 cent',
  `dtm` datetime(0) NOT NULL,
  `end` int(11) NOT NULL DEFAULT 1 COMMENT '0 轉出中 1 成功', 
  PRIMARY KEY (`txn_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_trade_log
-- ----------------------------
DROP TABLE IF EXISTS `game_trade_log`;
CREATE TABLE `game_trade_log`  (
  `txn_id` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `host_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `type` int(11) NOT NULL COMMENT '0 转入 1 转出',
  `member_id` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `amount` bigint(20) NOT NULL COMMENT '单位 cent',
  `dtm` datetime(0) NOT NULL,
  PRIMARY KEY (`txn_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_sharing_trade_log
-- ----------------------------
DROP TABLE IF EXISTS `game_sharing_trade_log`;
CREATE TABLE `game_sharing_trade_log`  (
  `txn_id` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `host_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `type` int(11) NOT NULL COMMENT '0 kRefundBet 1 kBet 2 kResult 3 kAuthenticate 4 kBonusAward 5 kLogout 6 kGetBalance',
  `member_id` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `amount` bigint(20) NOT NULL COMMENT '单位 cent',
  `dtm` datetime(0) NOT NULL,
  constraint `txn_id_type` unique (`txn_id`, `type`)
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_host_err_log
-- ----------------------------
DROP TABLE IF EXISTS `game_host_err_log`;
CREATE TABLE `game_host_err_log`  (
  `action_key` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `host_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `type` int(11) NOT NULL COMMENT '0 kRefundBet 1 kBet 2 kResult 3 kAuthenticate 4 kBonusAward 5 kLogout 6 kGetBalance 供內部使用',
  `action` int(11) NOT NULL COMMENT '0 kAuthenticate 1 kBet 2 kResult 3 kRefundBet 4 kBonusAward 5 kLogout 6 kGetBalance',
  `err_code` int(11) NOT NULL COMMENT '-1 kUnknown 0 kSuccess 1 kNetError 2 kParseError 3 kFormatError 4 kHostError 5 kNegativeError 6 kSystemError 7 kFundsError 8 kSlowRequest',
  `err_descr` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci,
  `dtm` datetime(0) NOT NULL,
  constraint `action_key_type` unique (`action_key`, `type`)
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_host_err_log
-- ----------------------------
DROP TABLE IF EXISTS `rollout_timeout_err_log`;
CREATE TABLE `rollout_timeout_err_log`  (
	`id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
	`wallet_type` int(11) UNSIGNED NOT NULL,
  `txn_id` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `host_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `flag` int(11) NOT NULL COMMENT '0 預設 -1 獨立多代取得網址錯誤 -2 共享多代取得網址錯誤 1 獨立轉錢錯誤 2 共享卡錢錯誤 3 共享轉錢錯誤',
  `member_id` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `amount` bigint(20) NOT NULL COMMENT '单位 cent',
  `dtm` datetime(0) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_bet_err_log
-- ----------------------------

CREATE TABLE `game_bet_err_log` (
	`txn_id` VARCHAR(40) NOT NULL DEFAULT '0' COMMENT '單號' COLLATE 'latin1_swedish_ci',
	`uuid` INT(20) NOT NULL DEFAULT '0',
	`member_id` VARCHAR(40) NOT NULL DEFAULT '' COMMENT '會員名稱' COLLATE 'latin1_swedish_ci',
	`host_api_key` VARCHAR(60) NOT NULL DEFAULT '' COMMENT '代理商金鑰' COLLATE 'latin1_swedish_ci',
	`amount` INT(20) NOT NULL COMMENT '預備押注金額',
	`status` INT(5) NOT NULL COMMENT '0正常押注-100沒回應',
	`date` VARCHAR(40) NOT NULL DEFAULT '' COMMENT '初始押注異常發生時間' COLLATE 'latin1_swedish_ci'
)
COMMENT='共享錢包轉進遊戲錢包一次bet失敗後，先進行一次refundbet'
COLLATE='latin1_swedish_ci'
ENGINE=InnoDB
;

-- ----------------------------
-- Table structure for game_share_result_err_log
-- ----------------------------

CREATE TABLE `game_share_result_err_log` (
	`txn_id` VARCHAR(40) NOT NULL DEFAULT '0' COMMENT '單號' COLLATE 'latin1_swedish_ci',
	`uuid` INT(20) NOT NULL DEFAULT '0',
	`member_id` VARCHAR(40) NOT NULL DEFAULT '' COMMENT '會員名稱' COLLATE 'latin1_swedish_ci',
	`host_api_key` VARCHAR(60) NOT NULL DEFAULT '' COMMENT '代理商金鑰' COLLATE 'latin1_swedish_ci',
	`gold` INT(20) NOT NULL COMMENT '結算完畢後，剩餘帶入內的金額',
	`winamt` INT(20) NOT NULL COMMENT '獲勝且沒有抽水的tot + 獲勝且抽過水的tot',
	`betamt` INT(20) NOT NULL COMMENT '沒有抽水的tot的絕對值',
	`game_id` VARCHAR(20) NOT NULL DEFAULT '' COMMENT '遊戲代號' COLLATE 'latin1_swedish_ci',
	`subgame_id` INT(2) NOT NULL COMMENT '房間號碼',
	`status_code` INT(3) NULL DEFAULT NULL COMMENT '請求result失敗時的回應訊號',
	`date` VARCHAR(40) NOT NULL DEFAULT '' COMMENT '異常發生時間' COLLATE 'latin1_swedish_ci'
)
COMMENT='遊戲結束向共享方請求result失敗，經數次請求仍未果，寫入異常紀錄'
COLLATE='latin1_swedish_ci'
ENGINE=InnoDB
;

-- ----------------------------
-- View structure for _view
-- ----------------------------
DROP VIEW IF EXISTS `_view`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `_view` AS select `game_play_log`.`vSubGameID` AS `subgameid`,`game_play_log`.`vHostApiKey` AS `hostapikey`,`game_play_log`.`vMemberID` AS `memberid`,count(0) AS `count`,sum(`game_play_log`.`vCalScore`) AS `profit` from `game_play_log` where (`game_play_log`.`vTime` between '2020-05-18 12:00:01' and '2020-05-18 13:00:00') group by `game_play_log`.`vMemberID`;

-- ----------------------------
-- Procedure structure for pro_AutoChannelProfit
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_AutoChannelProfit`;
delimiter ;;
CREATE PROCEDURE `pro_AutoChannelProfit`()
BEGIN#Routine body goes here...
	DECLARE
		_profit BIGINT DEFAULT 0;
	DECLARE
		_channel VARCHAR ( 8 );
	DECLARE
		_curtablename VARCHAR ( 32 );
	DECLARE
		_sqlstr VARCHAR ( 128 );
	DECLARE
		done INT DEFAULT 0;
	DECLARE
		cur CURSOR FOR SELECT
		Channel,
		Profit
	FROM
		_view;
	DECLARE
		CONTINUE HANDLER FOR NOT FOUND
		SET done = 1;
	DROP VIEW
	IF
		EXISTS _view;

	SET _curtablename = concat( 'game_play_log_', DATE_FORMAT( DATE_SUB( CURDATE( ), INTERVAL 1 DAY ), '%Y%m%d' ) );

	SET _sqlstr = concat( "CREATE VIEW _view as Select vChannel as Channel, SUM(vCalScore) as Profit from ", _curtablename, " group by vChannel;" );

	SET @sqlstr = _sqlstr;
	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;
	OPEN cur;
	FETCH cur INTO _channel,
	_profit;
	WHILE
			done <> 1 DO
			INSERT INTO game_channel_profit ( time, channel, profit )
		VALUES
			( NOW( ), _channel, _profit );
		FETCH cur INTO _channel,
		_profit;

	END WHILE;
	CLOSE cur;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_AutoCreateLogTable
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_AutoCreateLogTable`;
delimiter ;;
CREATE PROCEDURE `pro_AutoCreateLogTable`()
BEGIN#Routine body goes here...
	DECLARE
		_curtablename VARCHAR ( 32 );
	DECLARE
		_nexttablename VARCHAR ( 32 );
	DECLARE
		_sqlstr VARCHAR ( 128 );

	## play_log
	SET _curtablename = concat( 'game_play_log_', DATE_FORMAT( DATE_SUB( CURDATE( ), INTERVAL 0 DAY ) ,'%Y%m%d'));

	SET _nexttablename = concat( 'game_play_log_', DATE_FORMAT( DATE_SUB( CURDATE( ), INTERVAL -1 DAY ) ,'%Y%m%d'));

	SET _sqlstr = concat( concat( 'create table if not exists ', _curtablename ), ' like game_play_log;' );

	SET @sqlstr = _sqlstr;
	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;

	SET _sqlstr = concat( concat( 'create table if not exists ', _nexttablename ), ' like game_play_log;' );

	SET @sqlstr = _sqlstr;
	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;

	## login_log

	SET _curtablename = concat( 'game_login_log_', DATE_FORMAT( DATE_SUB( CURDATE( ), INTERVAL 0 DAY ) ,'%Y%m%d'));

	SET _nexttablename = concat( 'game_login_log_', DATE_FORMAT( DATE_SUB( CURDATE( ), INTERVAL -1 DAY ) ,'%Y%m%d'));

	SET _sqlstr = concat( concat( 'create table if not exists ', _curtablename ), ' like game_login_log;' );

	SET @sqlstr = _sqlstr;
	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;

	SET _sqlstr = concat( concat( 'create table if not exists ', _nexttablename ), ' like game_login_log;' );

	SET @sqlstr = _sqlstr;
	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_AutoHourProfit
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_AutoHourProfit`;
delimiter ;;
CREATE PROCEDURE `pro_AutoHourProfit`()
BEGIN
	DECLARE _subgameid INT DEFAULT 0;
	DECLARE _hostapikey VARCHAR ( 64 );
	DECLARE _memberid VARCHAR ( 64 );
	DECLARE _profit BIGINT DEFAULT 0;
	DECLARE _count INT DEFAULT 0;
	DECLARE _sqlstr VARCHAR ( 256 );
	DECLARE _nowtime datetime DEFAULT(NOW());
	
	DECLARE done INT DEFAULT 0;
	DECLARE cur CURSOR FOR SELECT subgameid, hostapikey, memberid, profit, count FROM _view;
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
	DROP VIEW IF EXISTS _view;
	
	SET _sqlstr = concat( "CREATE VIEW _view AS SELECT vSubGameID AS subgameid, vHostApiKey AS hostapikey, vMemberID AS memberid, COUNT(*) AS count, SUM(vCalScore) AS profit FROM game_play_log WHERE vTime BETWEEN '", DATE_SUB(_nowtime, INTERVAL 3599 SECOND), "' AND '", _nowtime, "' GROUP BY vMemberID" );
	SET @sqlstr = _sqlstr;
	PREPARE stmt FROM @sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;
	OPEN cur;
	FETCH cur INTO _subgameid, _hostapikey, _memberid, _profit, _count;
	WHILE done <> 1 DO
		INSERT INTO game_hour_profit(subgame_id, host_api_key, member_id, profit, count, time ) VALUES ( _subgameid, _hostapikey, _memberid, _profit, _count, _nowtime);
		FETCH cur INTO _subgameid, _hostapikey, _memberid, _profit, _count;
	END WHILE;
	CLOSE cur;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_AutoStayTime
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_AutoStayTime`;
delimiter ;;
CREATE PROCEDURE `pro_AutoStayTime`()
BEGIN#Routine body goes here...
	DECLARE
		_uuid BIGINT;
	DECLARE
		_serverid INT;
	DECLARE
		_staytime BIGINT;
	DECLARE
		Done INT DEFAULT 0;
	DECLARE
		rs CURSOR FOR SELECT
		UUID,
		ServerID,
		vTime AS StayTime
		-- COALESCE ( JSON_EXTRACT( JsonData, "$.st" ), 0 ) AS StayTime
	FROM
		apigame.data_subgameinfo;
	DECLARE
		CONTINUE HANDLER FOR SQLSTATE '02000'
		SET Done = 1;
	OPEN rs;
	FETCH rs INTO _uuid,
	_serverid,
	_staytime;
	WHILE
			Done <> 1 DO
			INSERT INTO game_player_stay ( UUID, ServerID, StayTime )
		VALUES
			( _uuid, _serverid, _staytime )
			ON DUPLICATE KEY UPDATE StayTime = _staytime;
		FETCH rs INTO _uuid,
		_serverid,
		_staytime;

	END WHILE;
	CLOSE rs;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_Remain
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_Remain`;
delimiter ;;
CREATE PROCEDURE `pro_Remain`()
BEGIN#Routine body goes here...
#定义参数   日期  表名
	DECLARE
		pi INT DEFAULT ( 0 );
	DECLARE
		tablename VARCHAR ( 1024 );
	DECLARE
		temptablename VARCHAR ( 1024 );
	DECLARE
		i INT DEFAULT ( 0 );
	DECLARE
		login INT DEFAULT ( 0 );
	DECLARE
		reg INT DEFAULT ( 0 );
	DECLARE
		sqlstr VARCHAR ( 2048 );
	DECLARE
		dates VARCHAR ( 64 );

	SET dates = CURDATE( );

	SET tablename = CONCAT( 'game_Login_Log_', DATE_FORMAT( dates, '%Y%m%d' ) );-- 今天  game_Login_Log_20190418

	SET i = 1;
	WHILE
			i < 7 DO--  七天日期表

			SET temptablename = CONCAT( 'game_Login_Log_', DATE_FORMAT( DATE_SUB( dates, INTERVAL i DAY ), '%Y%m%d' ) );-- 昨天注册 今天登录的人数

		SET @sqlstr = Concat( " SELECT    count(1) into @pram  FROM (select   DISTINCT vUUID   FROM  ", tablename, " as a
		where exists (select  vUUID from ", temptablename, " as b 			where 	 	a.vUUID = b.vUUID and b.vType = 0)) as m" );
		PREPARE stmt
		FROM
			@sqlstr;
		EXECUTE stmt;
		DEALLOCATE PREPARE stmt;

		SET pi = @pram;-- 修改或添加 次留 三留 四留

		SET @sqlstr = Concat(
			'INSERT INTO weblog.data_remain(time,d',
			i,
			') VALUES(DATE_SUB("',
			dates,
			'",INTERVAL ',
			i,
			' DAY),',
			pi,
			') ON DUPLICATE KEY UPDATE d',
			i,
			' = ',
			pi,
			',time=DATE_SUB("',
			dates,
			'",INTERVAL ',
			i,
			' DAY)'
		);
		PREPARE stmt
		FROM
			@sqlstr;
		EXECUTE stmt;
		DEALLOCATE PREPARE stmt;

		SET i = i + 1;

	END WHILE;-- 查询今天登录人数

	SET @sqlstr = Concat( 'SELECT  COUNT(DISTINCT  vUUID)  AS  login_count into @pra  FROM ', tablename, ' WHERE vType=1' );


	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;
	IF
		( @pra IS NOT NULL ) THEN

			SET login = @pra;-- 为输出参数赋值
		ELSE
			SET login = 0;

	END IF;-- SET login = @pra;--   		-- 查询今天注册人数

	SET @sqlstr = Concat( 'SELECT  COUNT(DISTINCT  vUUID)  AS  reg_count  into @pra2 FROM ', tablename, ' WHERE vType=0' );


	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;
	IF
		( @pra2 IS NOT NULL ) THEN

			SET reg = @pra2;-- 为输出参数赋值
		ELSE
			SET reg = 0;

	END IF;--  SET reg = @pra2;-- --  插入  今天 登录  注册的用户

	SET @sqlstr = Concat( 'INSERT INTO weblog.data_remain(time,login_peo,reg_count) VALUES("', dates, '",', login, ',', reg, ') ON DUPLICATE KEY UPDATE  login_peo= ', login, ',reg_count=', reg, '' );
	PREPARE stmt
	FROM
		@sqlstr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_SaveProfit
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_SaveProfit`;
delimiter ;;
CREATE PROCEDURE `pro_SaveProfit`(IN `inDate` BIGINT, IN `inServerID` INT, IN `inProfit` BIGINT)
BEGIN#Routine body goes here...
	INSERT INTO game_profit ( Date, ServerID, Profit )
	VALUES
		( inDate, inServerID, inProfit )
		ON DUPLICATE KEY UPDATE Profit = inProfit;

END
;;
delimiter ;

-- ----------------------------
-- Event structure for event_AutoHourProfit
-- ----------------------------
DROP EVENT IF EXISTS `event_AutoHourProfit`;
delimiter ;;
CREATE EVENT `event_AutoHourProfit`
ON SCHEDULE
EVERY '1' HOUR STARTS '2019-04-09 00:00:00'
DO call pro_AutoHourProfit()
;;
delimiter ;

-- ----------------------------
-- Event structure for event_AutoStayTime
-- ----------------------------
DROP EVENT IF EXISTS `event_AutoStayTime`;
delimiter ;;
CREATE EVENT `event_AutoStayTime`
ON SCHEDULE
EVERY '1' DAY STARTS '2019-01-16 05:05:00'
DO call pro_AutoStayTime()
;;
delimiter ;

-- ----------------------------
-- Event structure for event_ChannelProfit
-- ----------------------------
DROP EVENT IF EXISTS `event_ChannelProfit`;
delimiter ;;
CREATE EVENT `event_ChannelProfit`
ON SCHEDULE
EVERY '1' DAY STARTS '2019-04-30 00:00:00'
DO call pro_AutoChannelProfit()
;;
delimiter ;

-- ----------------------------
-- Event structure for event_Remain
-- ----------------------------
DROP EVENT IF EXISTS `event_Remain`;
delimiter ;;
CREATE EVENT `event_Remain`
ON SCHEDULE
EVERY '30' MINUTE STARTS '2019-04-18 23:59:30'
DO call pro_Remain()
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
