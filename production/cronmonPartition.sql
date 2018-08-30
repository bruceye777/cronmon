--  Create composite primary key
ALTER TABLE apirequestlog DROP PRIMARY KEY, ADD PRIMARY KEY(id,create_datetime);
ALTER TABLE taskmonitorlog DROP PRIMARY KEY, ADD PRIMARY KEY(id,create_datetime);

DELIMITER $$
CREATE PROCEDURE `partition_create`(SCHEMANAME varchar(64), TABLENAME varchar(64), PARTITIONNAME varchar(64), FUTURETIMESTAMP timestamp)
BEGIN
        /*
           Verify that the partition does not already exist
        */

        DECLARE RETROWS INT;
        SELECT COUNT(1) INTO RETROWS
        FROM information_schema.partitions
        WHERE table_schema = SCHEMANAME AND table_name = TABLENAME AND UNIX_TIMESTAMP(STR_TO_DATE(SUBSTRING(CONVERT(partition_description, CHAR),2,19), '%Y-%m-%d %H:%i:%s')) >= UNIX_TIMESTAMP(FUTURETIMESTAMP);

        IF RETROWS = 0 THEN
                /*
                   1. Print a message indicating that a partition was created.
                   2. Create the SQL to create the partition.
                   3. Execute the SQL from #2.
                */
                SELECT CONCAT( "partition_create(", SCHEMANAME, ",", TABLENAME, ",", PARTITIONNAME, ",", FUTURETIMESTAMP, ")" ) AS msg;
                SET @sql = CONCAT( "ALTER TABLE ", SCHEMANAME, ".", TABLENAME, " ADD PARTITION (PARTITION ", PARTITIONNAME, " VALUES LESS THAN ('", FUTURETIMESTAMP, "'));" );
                PREPARE STMT FROM @sql;
                EXECUTE STMT;
                DEALLOCATE PREPARE STMT;
        END IF;
END$$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE `partition_drop`(SCHEMANAME VARCHAR(64), TABLENAME VARCHAR(64), DELETE_BELOW_PARTITION_DATE BIGINT)
BEGIN
        DECLARE done INT DEFAULT FALSE;
        DECLARE drop_part_name VARCHAR(16);

        /*
           Get a list of all the partitions that are older than the date
           in DELETE_BELOW_PARTITION_DATE.  All partitions are prefixed with
           a "p", so use SUBSTRING TO get rid of that character.
        */		
        DECLARE myCursor CURSOR FOR
                SELECT partition_name
                FROM information_schema.partitions
                WHERE table_schema = SCHEMANAME AND table_name = TABLENAME AND CAST(SUBSTRING(partition_name FROM 2) AS UNSIGNED) < DELETE_BELOW_PARTITION_DATE;
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

        /*
           Create the basics for when we need to drop the partition.  Also, create
           @drop_partitions to hold a comma-delimited list of all partitions that
           should be deleted.
        */
        SET @alter_header = CONCAT("ALTER TABLE ", SCHEMANAME, ".", TABLENAME, " DROP PARTITION ");
        SET @drop_partitions = "";

        /*
           Start looping through all the partitions that are too old.
        */
        OPEN myCursor;
        read_loop: LOOP
                FETCH myCursor INTO drop_part_name;
                IF done THEN
                        LEAVE read_loop;
                END IF;
                SET @drop_partitions = IF(@drop_partitions = "", drop_part_name, CONCAT(@drop_partitions, ",", drop_part_name));
        END LOOP;
        IF @drop_partitions != "" THEN
                /*
                   1. Build the SQL to drop all the necessary partitions.
                   2. Run the SQL to drop the partitions.
                   3. Print out the table partitions that were deleted.
                */
                SET @full_sql = CONCAT(@alter_header, @drop_partitions, ";");
                PREPARE STMT FROM @full_sql;
                EXECUTE STMT;
                DEALLOCATE PREPARE STMT;

                SELECT CONCAT(SCHEMANAME, ".", TABLENAME) AS `table`, @drop_partitions AS `partitions_deleted`;
        ELSE
                /*
                   No partitions are being deleted, so print out "N/A" (Not applicable) to indicate
                   that no changes were made.
                */
                SELECT CONCAT(SCHEMANAME, ".", TABLENAME) AS `table`, "N/A" AS `partitions_deleted`;
        END IF;
END$$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE `partition_verify`(SCHEMANAME VARCHAR(64), TABLENAME VARCHAR(64), PARTITIONNAME varchar(64), FUTURETIMESTAMP timestamp)
BEGIN
        DECLARE RETROWS INT(11);

        /*
           Check if any partitions exist for the given SCHEMANAME.TABLENAME.
         */
        SELECT COUNT(1) INTO RETROWS
        FROM information_schema.partitions
        WHERE table_schema = SCHEMANAME AND table_name = TABLENAME AND partition_name IS NULL;

        /*
           If partitions do not exist, go ahead and partition the table
         */
        IF RETROWS = 1 THEN
                /*
                   Take the current date at 00:00:00 and add HOURLYINTERVAL to it.  This is the timestamp below which we will store values.
                   We begin partitioning based on the beginning of a day.  This is because we don't want to generate a random partition
                   that won't necessarily fall in line with the desired partition naming (ie: if the hour interval is 24 hours, we could
                   end up creating a partition now named "p201403270600" when all other partitions will be like "p201403280000").
                 */
                -- Create the partitioning query
                SET @__PARTITION_SQL = CONCAT("ALTER TABLE ", SCHEMANAME, ".", TABLENAME, " PARTITION BY RANGE COLUMNS(`create_datetime`)");
                SET @__PARTITION_SQL = CONCAT(@__PARTITION_SQL, "(PARTITION ", PARTITIONNAME, " VALUES LESS THAN ('", FUTURETIMESTAMP, "'));");

                -- Run the partitioning query
                PREPARE STMT FROM @__PARTITION_SQL;
                EXECUTE STMT;
                DEALLOCATE PREPARE STMT;
        END IF;
END$$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE `partition_maintenance`(SCHEMA_NAME VARCHAR(32), TABLE_NAME VARCHAR(32), KEEP_DATA_DAYS INT, HOURLY_INTERVAL INT, CREATE_NEXT_INTERVALS INT)
BEGIN
        DECLARE OLDER_THAN_PARTITION_DATE VARCHAR(16);
        DECLARE PARTITION_NAME VARCHAR(16);
        DECLARE OLD_PARTITION_NAME VARCHAR(16);
        DECLARE FUTURE_TIMESTAMP TIMESTAMP;
        DECLARE CUR_TIME INT;

        SET FUTURE_TIMESTAMP = TIMESTAMPADD(HOUR, HOURLY_INTERVAL, CONCAT(CURDATE(), " ", '00:00:00'));
        SET PARTITION_NAME = DATE_FORMAT(CURDATE(), 'p%Y%m%d%H00');

        -- Start partiitioning if there's no partition info.
        CALL partition_verify(SCHEMA_NAME, TABLE_NAME, PARTITION_NAME, FUTURE_TIMESTAMP);

        SET CUR_TIME = UNIX_TIMESTAMP(DATE_FORMAT(NOW(), '%Y-%m-%d 00:00:00'));

        SET @__interval = 1;
        create_loop: LOOP
                IF @__interval > CREATE_NEXT_INTERVALS THEN
                        LEAVE create_loop;
                END IF;
                
                -- Create the next CREATE_NEXT_INTERVALS days partitions.
                SET FUTURE_TIMESTAMP = FROM_UNIXTIME(CUR_TIME + (HOURLY_INTERVAL * @__interval * 3600));
                SET PARTITION_NAME = FROM_UNIXTIME(CUR_TIME + HOURLY_INTERVAL * (@__interval - 1) * 3600, 'p%Y%m%d%H00');
                IF(PARTITION_NAME != OLD_PARTITION_NAME) THEN
                        CALL partition_create(SCHEMA_NAME, TABLE_NAME, PARTITION_NAME, FUTURE_TIMESTAMP);
                END IF;
                SET @__interval=@__interval+1;
                SET OLD_PARTITION_NAME = PARTITION_NAME;
        END LOOP;

        SET OLDER_THAN_PARTITION_DATE=DATE_FORMAT(DATE_SUB(NOW(), INTERVAL KEEP_DATA_DAYS DAY), '%Y%m%d0000');

        -- Drop old partitions base on the date(partition name).
        CALL partition_drop(SCHEMA_NAME, TABLE_NAME, OLDER_THAN_PARTITION_DATE);
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE `partition_maintenance_all`(SCHEMA_NAME VARCHAR(32))
BEGIN
                CALL partition_maintenance(SCHEMA_NAME, 'apirequestlog', 183, 24, 14);
                CALL partition_maintenance(SCHEMA_NAME, 'taskmonitorlog', 31, 24, 14);
END$$
DELIMITER ;
