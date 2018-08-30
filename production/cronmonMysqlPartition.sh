#!/bin/bash
# GRANT EXECUTE ON PROCEDURE partition_maintenance_all TO cronmonPartition@localhost IDENTIFIED BY 'yourpwd';
source /etc/profile

mysql -ucronmonPartition -p'yourpwd' cronmon -e"CALL partition_maintenance_all('cronmon');"
