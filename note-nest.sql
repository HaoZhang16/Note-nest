/*
SQLyog Ultimate v12.09 (64 bit)
MySQL - 8.0.40 : Database - courseproject01
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`courseproject01` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `courseproject01`;

/*Table structure for table `book` */

DROP TABLE IF EXISTS `book`;

CREATE TABLE `book` (
  `book_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `author` varchar(255) NOT NULL,
  `total_page` int DEFAULT NULL,
  `cover_path` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`book_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `booknotelink` */

DROP TABLE IF EXISTS `booknotelink`;

CREATE TABLE `booknotelink` (
  `book_id` int NOT NULL,
  `note_id` int NOT NULL,
  PRIMARY KEY (`book_id`,`note_id`),
  KEY `note_id` (`note_id`),
  CONSTRAINT `booknotelink_ibfk_1` FOREIGN KEY (`book_id`) REFERENCES `book` (`book_id`),
  CONSTRAINT `booknotelink_ibfk_2` FOREIGN KEY (`note_id`) REFERENCES `note` (`note_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `booktaglink` */

DROP TABLE IF EXISTS `booktaglink`;

CREATE TABLE `booktaglink` (
  `book_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`book_id`,`tag_id`),
  KEY `tag_id` (`tag_id`),
  CONSTRAINT `booktaglink_ibfk_1` FOREIGN KEY (`book_id`) REFERENCES `book` (`book_id`),
  CONSTRAINT `booktaglink_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `friend` */

DROP TABLE IF EXISTS `friend`;

CREATE TABLE `friend` (
  `user_id` int NOT NULL,
  `friend_id` int NOT NULL,
  PRIMARY KEY (`user_id`,`friend_id`),
  KEY `friend_id` (`friend_id`),
  CONSTRAINT `friend_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `friend_ibfk_2` FOREIGN KEY (`friend_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `friend_chk_1` CHECK ((`user_id` <> `friend_id`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `inread` */

DROP TABLE IF EXISTS `inread`;

CREATE TABLE `inread` (
  `user_id` int NOT NULL,
  `book_id` int NOT NULL,
  PRIMARY KEY (`user_id`,`book_id`),
  KEY `book_id` (`book_id`),
  CONSTRAINT `inread_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `inread_ibfk_2` FOREIGN KEY (`book_id`) REFERENCES `book` (`book_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `note` */

DROP TABLE IF EXISTS `note`;

CREATE TABLE `note` (
  `note_id` int NOT NULL,
  `quote` text,
  `content` text NOT NULL,
  `create_time` datetime NOT NULL,
  `owner_id` int NOT NULL,
  PRIMARY KEY (`note_id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `note_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `noteshare` */

DROP TABLE IF EXISTS `noteshare`;

CREATE TABLE `noteshare` (
  `share_id` int NOT NULL,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `note_id` int NOT NULL,
  `permission` enum('read','write','admin') NOT NULL,
  `share_time` datetime NOT NULL,
  PRIMARY KEY (`share_id`),
  KEY `sender_id` (`sender_id`),
  KEY `receiver_id` (`receiver_id`),
  KEY `note_id` (`note_id`),
  CONSTRAINT `noteshare_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `noteshare_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `noteshare_ibfk_3` FOREIGN KEY (`note_id`) REFERENCES `note` (`note_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `notetaglink` */

DROP TABLE IF EXISTS `notetaglink`;

CREATE TABLE `notetaglink` (
  `note_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`note_id`,`tag_id`),
  KEY `tag_id` (`tag_id`),
  CONSTRAINT `notetaglink_ibfk_1` FOREIGN KEY (`note_id`) REFERENCES `note` (`note_id`),
  CONSTRAINT `notetaglink_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `reviewlog` */

DROP TABLE IF EXISTS `reviewlog`;

CREATE TABLE `reviewlog` (
  `log_id` int NOT NULL,
  `review_time` datetime NOT NULL,
  `score` int NOT NULL,
  `note_id` int NOT NULL,
  PRIMARY KEY (`log_id`),
  KEY `note_id` (`note_id`),
  CONSTRAINT `reviewlog_ibfk_1` FOREIGN KEY (`note_id`) REFERENCES `note` (`note_id`),
  CONSTRAINT `reviewlog_chk_1` CHECK ((`score` between 1 and 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `summary` */

DROP TABLE IF EXISTS `summary`;

CREATE TABLE `summary` (
  `summary_note_id` int NOT NULL,
  `note_id` int NOT NULL,
  PRIMARY KEY (`summary_note_id`,`note_id`),
  KEY `note_id` (`note_id`),
  CONSTRAINT `summary_ibfk_1` FOREIGN KEY (`summary_note_id`) REFERENCES `summarynote` (`note_id`),
  CONSTRAINT `summary_ibfk_2` FOREIGN KEY (`note_id`) REFERENCES `note` (`note_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `summarynote` */

DROP TABLE IF EXISTS `summarynote`;

CREATE TABLE `summarynote` (
  `note_id` int NOT NULL,
  `quote` text,
  `content` text NOT NULL,
  `create_time` datetime NOT NULL,
  `owner_id` int NOT NULL,
  `summary_topic` varchar(255) NOT NULL,
  PRIMARY KEY (`note_id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `summarynote_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `tag` */

DROP TABLE IF EXISTS `tag`;

CREATE TABLE `tag` (
  `tag_id` int NOT NULL,
  `tag_name` varchar(255) NOT NULL,
  `use_count` int DEFAULT '0',
  PRIMARY KEY (`tag_id`),
  UNIQUE KEY `tag_name` (`tag_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Table structure for table `users` */

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `user_id` int NOT NULL,
  `user_name` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_name` (`user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/* Trigger structure for table `notetaglink` */

DELIMITER $$

/*!50003 DROP TRIGGER*//*!50032 IF EXISTS */ /*!50003 `increment_use_count_after_insert` */$$

/*!50003 CREATE */ /*!50017 DEFINER = 'root'@'localhost' */ /*!50003 TRIGGER `increment_use_count_after_insert` AFTER INSERT ON `notetaglink` FOR EACH ROW BEGIN
    UPDATE Tag SET use_count = use_count + 1 WHERE tag_id = NEW.tag_id;
END */$$


DELIMITER ;

/* Trigger structure for table `notetaglink` */

DELIMITER $$

/*!50003 DROP TRIGGER*//*!50032 IF EXISTS */ /*!50003 `decrement_use_count_after_delete` */$$

/*!50003 CREATE */ /*!50017 DEFINER = 'root'@'localhost' */ /*!50003 TRIGGER `decrement_use_count_after_delete` AFTER DELETE ON `notetaglink` FOR EACH ROW BEGIN
    UPDATE Tag SET use_count = use_count - 1 WHERE tag_id = OLD.tag_id;
END */$$


DELIMITER ;

/* Procedure structure for procedure `AddNoteAndMarkInRead` */

/*!50003 DROP PROCEDURE IF EXISTS  `AddNoteAndMarkInRead` */;

DELIMITER $$

/*!50003 CREATE DEFINER=`root`@`localhost` PROCEDURE `AddNoteAndMarkInRead`(
    IN p_note_id INT,
    IN p_quote TEXT,
    IN p_content TEXT,
    IN p_owner_id INT,
    IN p_create_time DATETIME,
    IN p_book_id INT
)
BEGIN
    DECLARE existing_count INT;
    START TRANSACTION;
    -- 插入 Note 表
    INSERT INTO Note(note_id, quote, content, owner_id, create_time)
    VALUES (p_note_id, p_quote, p_content, p_owner_id, p_create_time);
    -- 如果 p_book_id 不为空（非 0 或 NULL），则插入 inread
    IF p_book_id IS NOT NULL THEN
        SELECT COUNT(*) INTO existing_count
        FROM inread
        WHERE user_id = p_owner_id AND book_id = p_book_id;
        IF existing_count = 0 THEN
            INSERT INTO inread(user_id, book_id)
            VALUES (p_owner_id, p_book_id);
        END IF;
    END IF;
    COMMIT;
END */$$
DELIMITER ;

/*Table structure for table `userlatestnote` */

DROP TABLE IF EXISTS `userlatestnote`;

/*!50001 DROP VIEW IF EXISTS `userlatestnote` */;
/*!50001 DROP TABLE IF EXISTS `userlatestnote` */;

/*!50001 CREATE TABLE  `userlatestnote`(
 `user_id` int ,
 `user_name` varchar(255) ,
 `content` text ,
 `create_time` datetime 
)*/;

/*View structure for view userlatestnote */

/*!50001 DROP TABLE IF EXISTS `userlatestnote` */;
/*!50001 DROP VIEW IF EXISTS `userlatestnote` */;

/*!50001 CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `userlatestnote` AS select `u`.`user_id` AS `user_id`,`u`.`user_name` AS `user_name`,`n`.`content` AS `content`,`n`.`create_time` AS `create_time` from (`users` `u` join `note` `n` on((`u`.`user_id` = `n`.`owner_id`))) where (`n`.`create_time` = (select max(`n2`.`create_time`) from `note` `n2` where (`n2`.`owner_id` = `u`.`user_id`))) */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
