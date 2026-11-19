/*
 Navicat Premium Data Transfer

 Source Server         : 192.168.1.106(linux)
 Source Server Type    : MySQL
 Source Server Version : 50725
 Source Host           : 192.168.1.106:3306
 Source Schema         : dmgame

 Target Server Type    : MySQL
 Target Server Version : 50725
 File Encoding         : 65001

 Date: 18/05/2020 13:27:43
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for cfg_android
-- ----------------------------
DROP TABLE IF EXISTS `cfg_android`;
CREATE TABLE `cfg_android`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `NickName` varchar(127) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT '',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 283 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for cfg_android_vip
-- ----------------------------
DROP TABLE IF EXISTS `cfg_android_vip`;
CREATE TABLE `cfg_android_vip`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `NickName` varchar(127) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT '',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 283 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for cfg_gameroominfo
-- ----------------------------
DROP TABLE IF EXISTS `cfg_gameroominfo`;
CREATE TABLE `cfg_gameroominfo`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hash_key` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `host_api_key` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `subgame_id` int(11) NOT NULL,
  `create_time` datetime(0) NOT NULL,
  `json_options` json NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `hash_key_idx`(`hash_key`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for data_channel
-- ----------------------------
DROP TABLE IF EXISTS `data_channel`;
CREATE TABLE `data_channel`  (
  `channel` varchar(8) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '渠道短号',
  `name` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '渠道名字',
  `apikey` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '密钥',
  `status` int(8) NOT NULL COMMENT '0在使用 1已禁用',
  `totalreg` int(11) NOT NULL COMMENT '总注册量',
  `servers` json NOT NULL,
  `extra` json NOT NULL COMMENT '额外数据json',
  PRIMARY KEY (`channel`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for data_subgameinfo
-- ----------------------------
DROP TABLE IF EXISTS `data_subgameinfo`;
CREATE TABLE `data_subgameinfo`  (
  `UUID` int(11) NOT NULL,
  `ServerID` int(11) NOT NULL,
  `vTime` int(11) GENERATED ALWAYS AS (replace(json_extract(`JsonData`,_utf8'$.st'),_utf8'"',_utf8'')) VIRTUAL NULL,
  `JsonData` json NOT NULL,
  PRIMARY KEY (`UUID`, `ServerID`) USING BTREE,
  UNIQUE INDEX `Index`(`UUID`, `ServerID`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for data_user
-- ----------------------------
DROP TABLE IF EXISTS `data_user`;
CREATE TABLE `data_user`  (
  `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '唯一ID，uuid',
  `account` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '账号，渠道短号+渠道方唯一号',
  `channel` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '渠道短号',
  `chluuid` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '渠道方唯一ID',
  `platform` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `profit` bigint(20) NOT NULL DEFAULT 0 COMMENT '累计盈亏',
  `dailyprofit` bigint(20) NOT NULL DEFAULT 0 COMMENT '当日盈亏',
  `lastscoretime` int(11) NOT NULL DEFAULT 0 COMMENT '最后一次写分时间，算当日盈亏用',
  `ctrlstatus` int(11) NOT NULL,
  `ctrlscore` bigint(20) NOT NULL,
  `restriction` int(11) NOT NULL,
  `extra` json NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ban_player
-- ----------------------------
DROP TABLE IF EXISTS `ban_player`;
CREATE TABLE `ban_player`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `apikey` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '密钥',
  `game_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '遊戲id',
  `member_id` varchar(127) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '玩家id',
  PRIMARY KEY (`id`) USING BTREE,
  constraint `apikey_and_member` unique (`apikey`, `member_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 0 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for VIP_player
-- ----------------------------
DROP TABLE IF EXISTS `VIP_player`;
CREATE TABLE `VIP_player`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `apikey` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '密钥',
  `game_id` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '遊戲id',
  `member_id` varchar(127) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '玩家id',
  PRIMARY KEY (`id`) USING BTREE,
  constraint `apikey_and_member` unique (`apikey`, `member_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 0 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for cfg_threshold
-- ----------------------------
DROP TABLE IF EXISTS `cfg_threshold`;
CREATE TABLE `cfg_threshold`  (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(45) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `data` json NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 0 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Procedure structure for pro_Cleanup
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_Cleanup`;
delimiter ;;
CREATE PROCEDURE `pro_Cleanup`()
BEGIN
	TRUNCATE TABLE dmgame.data_reservoir;
	TRUNCATE TABLE dmgame.data_subgameinfo;
	TRUNCATE TABLE dmgame.data_user;
	TRUNCATE TABLE dmgame.cfg_admin;
	TRUNCATE TABLE dmgame.cfg_android;
	
	TRUNCATE TABLE dmgamelog.game_channel_profit;
	TRUNCATE TABLE dmgamelog.game_error_modify_stock;
	TRUNCATE TABLE dmgamelog.game_online_record;
	TRUNCATE TABLE dmgamelog.game_profit;
	TRUNCATE TABLE dmgamelog.game_stock_pump;
	TRUNCATE TABLE dmgamelog.game_tool_change_status;
	TRUNCATE TABLE dmgamelog.game_tool_change_stock;
	TRUNCATE TABLE dmgamelog.game_tool_change_user;
	TRUNCATE TABLE dmgamelog.modify_channel_log;
	TRUNCATE TABLE dmgamelog.registe_channel_log;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_Config
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_Config`;
delimiter ;;
CREATE PROCEDURE `pro_Config`(IN `inDBAddr` varchar(16), IN `inDBPassword` varchar(16))
BEGIN
	#Routine body goes here...
	update cfg_databaseinfo set DBAddr = inDBAddr, DBPassword = inDBPassword;
	update cfg_gameiteminfo set DataBaseAddr = inDBAddr;
	update cfg_gameroominfo set DataBaseAddr = inDBAddr;
 
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_GetPumpLimit
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_GetPumpLimit`;
delimiter ;;
CREATE PROCEDURE `pro_GetPumpLimit`(IN `inServerID` INT)
BEGIN#Routine body goes here...
	SELECT
		StockPumpTime,
		StockPumpLimit,
		StockPumpRate,
		AwardPumpTime,
		AwardPumpLimit,
		AwardPumpRate
	FROM
		cfg_Reservoir
	WHERE
		ServerID = inServerID;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_LoadAndroid
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_LoadAndroid`;
delimiter ;;
CREATE PROCEDURE `pro_LoadAndroid`(IN `inServerID` INT)
BEGIN#Routine body goes here...
	SELECT
		*
	FROM
		cfg_Android
	WHERE
		ServerID = inServerID;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_LoadDataBaseInfo
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_LoadDataBaseInfo`;
delimiter ;;
CREATE PROCEDURE `pro_LoadDataBaseInfo`(IN `inStrDataBaseAddr` VARCHAR ( 15 ))
BEGIN#Routine body goes here...
## 基本信息
	DECLARE _DBPort INT;
	DECLARE _DBAddr VARCHAR ( 15 );
	DECLARE _DBName VARCHAR ( 32 );
	DECLARE _DBUser VARCHAR ( 512 );
	DECLARE _DBPassword VARCHAR ( 512 );
	DECLARE __ROWCOUNT INT;
	DECLARE outErrorCode INT;

	SET outErrorCode = 0;
	SELECT DBPort,DBAddr,DBUser,DBPassword INTO _DBPort,_DBAddr,_DBUser,_DBPassword FROM cfg_DataBaseInfo WHERE DBAddr = inStrDataBaseAddr;## 存在判断

	SELECT FOUND_ROWS() INTO __ROWCOUNT;
	IF __ROWCOUNT = 0 THEN
		SET outErrorCode = 1;
	END IF;## 输出变量

	SELECT _DBPort AS DBPort,_DBAddr AS DBAddr,_DBUser AS DBUser,_DBPassword AS DBPassword;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_LoadGameRoomItem
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_LoadGameRoomItem`;
delimiter ;;
CREATE PROCEDURE `pro_LoadGameRoomItem`(IN `hashkey` VARCHAR(64))
BEGIN
	SELECT * FROM cfg_GameRoomInfo WHERE hash_key = hashkey;
/*
	SELECT
		abc.*,
		COALESCE ( d.JsonData, '' )  AS JsonData
	FROM
		(
		SELECT
			a.*,
			b.GameName,
			b.ServerDLLName,
			c.InitStock,
			c.InitAward
		FROM
			cfg_GameRoomInfo a,
			cfg_GameItemInfo b,
			cfg_Reservoir c
		WHERE
		  a.Valid = 1
			AND a.GameID = b.GameID
			AND a.ServerID = c.ServerID
			AND ( a.ServerID = inServerID OR inServerID = 0 )
		) abc
		LEFT JOIN data_Reservoir d ON abc.ServerID = d.ServerID;
*/
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_LoadGameRoomItem_copy1
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_LoadGameRoomItem_copy1`;
delimiter ;;
CREATE PROCEDURE `pro_LoadGameRoomItem_copy1`(IN `inServerID` INT)
BEGIN#Routine body goes here...
	SELECT
		abc.*,
		COALESCE ( d.JsonData, '' )  AS JsonData
	FROM
		(
		SELECT
			a.*,
			b.GameName,
			b.ServerDLLName,
			c.InitStock,
			c.InitAward
		FROM
			cfg_GameRoomInfo a,
			cfg_GameItemInfo b,
			cfg_Reservoir c
		WHERE
		  a.Valid = 1
			AND a.GameID = b.GameID
			AND a.ServerID = c.ServerID
			AND ( a.ServerID = inServerID OR inServerID = 0 )
		) abc
		LEFT JOIN data_Reservoir d ON abc.ServerID = d.ServerID;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_LoadVersion
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_LoadVersion`;
delimiter ;;
CREATE PROCEDURE `pro_LoadVersion`(OUT `outVersion` INT)
BEGIN#Routine body goes here...

	SET outVersion = 0;
	SELECT
		type INTO outVersion
	FROM
		cfg_data
	WHERE
		id = 99999;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_RequestReservoir
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_RequestReservoir`;
delimiter ;;
CREATE PROCEDURE `pro_RequestReservoir`(IN inServer_id INT)
BEGIN#Routine body goes here...
	DECLARE
		_iStock BIGINT;
	DECLARE
		_iAward BIGINT;
	IF
		NOT EXISTS ( SELECT UpdateSettingStamp FROM data_Reservoir WHERE ServerID = inServer_id ) THEN
		SELECT
			InitStock,
			InitAward INTO _iStock,
			_iAward 
		FROM
			cfg_Reservoir 
		WHERE
			ServerID = inServer_id;
		IF
			_iStock IS NULL THEN
				
				SET _iStock = 0;
			
			SET _iAward = 0;
			
		END IF;
		INSERT INTO data_Reservoir ( ServerID, UpdateSettingStamp, UpdateDataStamp, Stock, Award )
		VALUES
			( inServer_id, UNIX_TIMESTAMP( ), UNIX_TIMESTAMP( ), _iStock, _iAward );
		
	END IF;
	SELECT
		Stock,
		Award 
	FROM
		data_Reservoir 
	WHERE
		ServerID = inServer_id;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_SaveGameRecord
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_SaveGameRecord`;
delimiter ;;
CREATE PROCEDURE `pro_SaveGameRecord`(IN `inUUID` BIGINT, IN `inRecord` VARCHAR ( 4096 ))
BEGIN#Routine body goes here...
	DECLARE
		_curLen INT;
	IF
		EXISTS ( SELECT * FROM data_gamerecord WHERE uuid = inUUID ) THEN
			UPDATE data_gamerecord 
			SET jsonData = JSON_ARRAY_APPEND( jsonData, '$', inRecord ) 
		WHERE
			uuid = inUUID;
		SELECT
			JSON_LENGTH( jsonData ) INTO _curLen 
		FROM
			data_gamerecord 
		WHERE
			uuid = inUUID;
		IF
			_curLen > 10 THEN
				UPDATE data_gamerecord 
				SET jsonData = JSON_REMOVE( jsonData, '$[0]' ) 
			WHERE
				uuid = inUUID;
			
		END IF;
		ELSE INSERT INTO data_gamerecord ( uuid, jsondata )
		VALUES
			( inUUID, '[]' );
		UPDATE data_gamerecord 
		SET jsonData = JSON_ARRAY_APPEND( jsonData, '$', inRecord ) 
		WHERE
			uuid = inUUID;
		
	END IF;

END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_UpdateCBStatus
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_UpdateCBStatus`;
delimiter ;;
CREATE PROCEDURE `pro_UpdateCBStatus`(IN inServerID int,											-- 服务器id
	IN inJson varchar(1024))
BEGIN
    #Routine body goes here...
		-- UPDATE cfg_GameRoomInfo SET cbStatus = inStatus WHERE ServerID = inServerID;
		INSERT INTO data_Reservoir(ServerID) VALUES(inServerID) On DUPLICATE key UPDATE JsonData = inJson;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for pro_UpdateReservoir
-- ----------------------------
DROP PROCEDURE IF EXISTS `pro_UpdateReservoir`;
delimiter ;;
CREATE PROCEDURE `pro_UpdateReservoir`(IN `inServerID` INT, IN `inLastStamp` BIGINT, IN `inStock` BIGINT, IN `inAward` BIGINT)
BEGIN#Routine body goes here...
	DECLARE
		_stock BIGINT;
	DECLARE
		_award BIGINT;
	IF
		NOT EXISTS ( SELECT UpdateSettingStamp FROM data_Reservoir WHERE ServerID = inServerID ) THEN
		SELECT
			InitStock,
			InitAward INTO _stock,
			_award 
		FROM
			cfg_Reservoir 
		WHERE
			ServerID = inServerID;
		IF
			_stock IS NULL THEN
				
				SET _stock = 0;
			
			SET _award = 0;
			
		END IF;
		INSERT INTO data_Reservoir ( ServerID, UpdateSettingStamp, UpdateDataStamp, Stock, Award )
		VALUES
			( inServerID, UNIX_TIMESTAMP( ), UNIX_TIMESTAMP( ), _stock, _award );
		
	END IF;
	UPDATE data_Reservoir 
	SET Stock = inStock,
	Award = inAward,
	UpdateDataStamp = inLastStamp 
	WHERE
		ServerID = inServerID;

END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
