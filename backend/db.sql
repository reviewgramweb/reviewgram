CREATE DATABASE reviewgram CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'reviewgram'@'localhost' IDENTIFIED BY 'REPLACE_WITH_ACTUAL_PASSWORD';
GRANT ALL PRIVILEGES ON reviewgram . * TO 'reviewgram'@'localhost';
FLUSH PRIVILEGES;
USE `reviewgram`;

CREATE TABLE token_to_user_id(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    TOKEN TEXT,
    USER_ID BIGINT,
    TSTAMP BIGINT,
    KEY IX_TTUI_TOKEN (TOKEN(50)),
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;


CREATE TABLE token_to_chat_id(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    TOKEN TEXT,
    CHAT_ID BIGINT,
    TSTAMP BIGINT,
    KEY IX_TTUI_TOKEN (TOKEN(50)),
    KEY IX_TCUI_CHAT (CHAT_ID),
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE repository_settings(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    CHAT_ID BIGINT,
    REPO_SITE TEXT,
    REPO_USER_NAME TEXT,
    REPO_SAME_NAME TEXT,
    USER TEXT,
    PASSWORD TEXT,
    LANG_ID BIGINT,
    KEY IX_RS_CHAT_ID (CHAT_ID),
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE repo_locks(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    TOKEN TEXT,
    CHAT_ID BIGINT,
    TSTAMP BIGINT,
    KEY IX_TTUI_TOKEN (TOKEN(50)),
    KEY IX_TCUI_CHAT (CHAT_ID),
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;


CREATE TABLE repository_cache_storage_table(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    REPO_SITE TEXT,
    REPO_USER_NAME TEXT,
    REPO_SAME_NAME TEXT,
    BRANCH_ID TEXT,
    TSTAMP BIGINT,
    KEY IX_RCST_REPO_USER_NAME (REPO_USER_NAME(50)),
    KEY IX_RCST_REPO_SAME_NAME (REPO_SAME_NAME(50)),
    KEY IX_RCST_BRANCH_ID (BRANCH_ID(50)),
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

UPDATE `repository_autocompletion_lexemes` SET `LANG_ID`=1;
CREATE TABLE repository_autocompletion_lexemes(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    ROW_ID BIGINT,
    LEXEME_ID BIGINT,
    TEXT VARCHAR(1024),
    LANG_ID BIGINT,
    KEY IX_RAL_ROW_ID (ROW_ID),
    KEY IX_RAL_LEXEME_ID (LEXEME_ID),
    KEY IX_RAL_TEXT (TEXT(512)),
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
ALTER TABLE `repository_autocompletion_lexemes` ADD KEY `IX_LANG_ID`('LANG_ID')

CREATE TABLE languages(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    NAME VARCHAR(1024),
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

INSERT INTO languages(NAME) VALUES  ('Python');

CREATE TABLE recognize_tasks(
    ID BIGINT NOT NULL AUTO_INCREMENT,
    FILENAME VARCHAR(1024),
    DATE_START DATETIME DEFAULT NULL,
    DATE_END DATETIME  DEFAULT NULL,
    LANG_ID  INT DEFAULT NULL, 
    RES      LONGTEXT  DEFAULT NULL, 
    PRIMARY KEY(ID)
) ENGINE=InnoDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;


DELIMITER $$
CREATE FUNCTION levenshtein( s1 VARCHAR(1024), s2 VARCHAR(1024) )
    RETURNS INT
    DETERMINISTIC
    BEGIN
        DECLARE s1_len, s2_len, i, j, c, c_temp, cost INT;
        DECLARE s1_char CHAR;
        -- max strlen=255
        DECLARE cv0, cv1 VARBINARY(1025);

        SET s1_len = CHAR_LENGTH(s1), s2_len = CHAR_LENGTH(s2), cv1 = 0x00, j = 1, i = 1, c = 0;

        IF s1 = s2 THEN
            RETURN 0;
        ELSEIF s1_len = 0 THEN
            RETURN s2_len;
        ELSEIF s2_len = 0 THEN
            RETURN s1_len;
        ELSE
            WHILE j <= s2_len DO
                SET cv1 = CONCAT(cv1, UNHEX(HEX(j))), j = j + 1;
            END WHILE;
            WHILE i <= s1_len DO
                SET s1_char = SUBSTRING(s1, i, 1), c = i, cv0 = UNHEX(HEX(i)), j = 1;
                WHILE j <= s2_len DO
                    SET c = c + 1;
                    IF s1_char = SUBSTRING(s2, j, 1) THEN
                        SET cost = 0; ELSE SET cost = 1;
                    END IF;
                    SET c_temp = CONV(HEX(SUBSTRING(cv1, j, 1)), 16, 10) + cost;
                    IF c > c_temp THEN SET c = c_temp; END IF;
                    SET c_temp = CONV(HEX(SUBSTRING(cv1, j+1, 1)), 16, 10) + 1;
                    IF c > c_temp THEN
                        SET c = c_temp;
                    END IF;
                    SET cv0 = CONCAT(cv0, UNHEX(HEX(c))), j = j + 1;
                END WHILE;
                SET cv1 = cv0, i = i + 1;
            END WHILE;
        END IF;
        RETURN c;
    END$$
DELIMITER ;
