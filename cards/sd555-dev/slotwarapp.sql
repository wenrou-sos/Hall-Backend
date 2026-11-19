CREATE TABLE `create_club_verify_list` (
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`member_id` BIGINT(20) NOT NULL DEFAULT '0',
	`right` TINYINT(4) NOT NULL DEFAULT '0' COMMENT '是否可以建立俱樂部 0: 否 1: 可以',
	PRIMARY KEY (`id`) USING BTREE
)
COMMENT='確認該名玩家是否能夠創建俱樂部'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
AUTO_INCREMENT=2
;