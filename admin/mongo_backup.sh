#!/bin/bash

# Determine backup location
[[ -z $BACKUP_DIR ]] && BACKUP_DIR=$HOME/mongo_backup

# Determine if backup location exists
[[ ! -d $BACKUP_DIR ]] && echo "Backup directory not found, exiting..." && exit 1

# Current date
DATE=$(date +"%Y%m%d")

# Dump database in a compressed file
mongodump --archive=${BACKUP_DIR}/mongo_backup_${DATE}.gz --gzip >>${BACKUP_DIR}/mongo_backup.log 2>&1

# Exit if unsuccessful
[[ $? -eq 0 ]] || echo "Backup unsuccessful, exiting..." && exit 1

# Clean up files older than six months
find ${BACKUP_DIR} -name *.gz -mtime +180 -exec rm -f {} \;
