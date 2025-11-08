#!/bin/bash
"""
Backup Restore Script

Restores database and files from backups.

Usage:
    ./restore.sh [OPTIONS]

Options:
    --db-file FILE       Restore database from file
    --files-file FILE    Restore files from file
    --list               List available backups
    --latest             Restore from latest backups
    --date YYYYMMDD      Restore from specific date
    --help               Show help
"""

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKUP_ROOT="/var/backups/kooai"
CONFIG_FILE=".env"

# Variables
DB_FILE=""
FILES_FILE=""
ACTION=""
TARGET_DATE=""

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    log "Loading configuration from $CONFIG_FILE"
    set -a
    source "$CONFIG_FILE"
    set +a
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --db-file)
            DB_FILE="$2"
            shift 2
            ;;
        --files-file)
            FILES_FILE="$2"
            shift 2
            ;;
        --list)
            ACTION="list"
            shift
            ;;
        --latest)
            ACTION="latest"
            shift
            ;;
        --date)
            ACTION="date"
            TARGET_DATE="$2"
            shift 2
            ;;
        --help)
            head -n 20 "$0" | grep "^#" | sed 's/^# //'
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# List available backups
list_backups() {
    log "Available backups in $BACKUP_ROOT:"

    echo
    echo "Database Backups:"
    find "$BACKUP_ROOT/database" -name "*.sql.gz" -type f | sort -r | head -n 10 | while read file; do
        SIZE=$(du -h "$file" | cut -f1)
        DATE=$(stat -c %y "$file" | cut -d' ' -f1)
        echo "  [$DATE] $(basename "$file") ($SIZE)"
    done

    echo
    echo "File Backups:"
    find "$BACKUP_ROOT/files" -name "*.tar.gz" -type f | sort -r | head -n 10 | while read file; do
        SIZE=$(du -h "$file" | cut -f1)
        DATE=$(stat -c %y "$file" | cut -d' ' -f1)
        echo "  [$DATE] $(basename "$file") ($SIZE)"
    done
}

# Get latest backup file
get_latest_backup() {
    TYPE="$1"  # database or files

    if [ "$TYPE" = "database" ]; then
        find "$BACKUP_ROOT/database" -name "*.sql.gz" -type f | sort -r | head -n 1
    elif [ "$TYPE" = "files" ]; then
        find "$BACKUP_ROOT/files" -name "*.tar.gz" -type f | sort -r | head -n 1
    fi
}

# Get backup by date
get_backup_by_date() {
    TYPE="$1"  # database or files
    DATE="$2"  # YYYYMMDD

    if [ "$TYPE" = "database" ]; then
        find "$BACKUP_ROOT/database" -name "*${DATE}*.sql.gz" -type f | head -n 1
    elif [ "$TYPE" = "files" ]; then
        find "$BACKUP_ROOT/files" -name "*${DATE}*.tar.gz" -type f | head -n 1
    fi
}

# Restore database
restore_database() {
    DB_BACKUP="$1"

    if [ ! -f "$DB_BACKUP" ]; then
        error "Database backup not found: $DB_BACKUP"
        return 1
    fi

    log "Restoring database from: $DB_BACKUP"

    # Parse DATABASE_URL
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL not set"
        return 1
    fi

    DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

    DB_USER=${DB_USER:-postgres}
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_NAME=${DB_NAME:-kooai}

    # Confirm
    warning "This will OVERWRITE the current database: $DB_NAME"
    read -p "Are you sure? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log "Restore cancelled"
        return 0
    fi

    # Drop and recreate database
    log "Dropping and recreating database..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

    # Restore
    log "Restoring database..."
    gunzip -c "$DB_BACKUP" | PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"

    if [ $? -eq 0 ]; then
        log "Database restored successfully"
    else
        error "Database restore failed"
        return 1
    fi
}

# Restore files
restore_files() {
    FILES_BACKUP="$1"

    if [ ! -f "$FILES_BACKUP" ]; then
        error "Files backup not found: $FILES_BACKUP"
        return 1
    fi

    log "Restoring files from: $FILES_BACKUP"

    UPLOAD_DIR="${UPLOAD_DIR:-uploads}"

    # Confirm
    warning "This will OVERWRITE files in: $UPLOAD_DIR"
    read -p "Are you sure? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log "Restore cancelled"
        return 0
    fi

    # Backup existing files
    if [ -d "$UPLOAD_DIR" ]; then
        log "Backing up existing files to ${UPLOAD_DIR}.bak"
        mv "$UPLOAD_DIR" "${UPLOAD_DIR}.bak.$(date +%Y%m%d_%H%M%S)"
    fi

    # Extract
    log "Extracting files..."
    tar -xzf "$FILES_BACKUP" -C "$(dirname "$UPLOAD_DIR")"

    if [ $? -eq 0 ]; then
        FILE_COUNT=$(find "$UPLOAD_DIR" -type f | wc -l)
        log "Files restored successfully ($FILE_COUNT files)"
    else
        error "Files restore failed"
        return 1
    fi
}

# Main logic
case "$ACTION" in
    list)
        list_backups
        exit 0
        ;;
    latest)
        log "Restoring from latest backups..."
        DB_FILE=$(get_latest_backup "database")
        FILES_FILE=$(get_latest_backup "files")

        if [ -n "$DB_FILE" ]; then
            log "Latest database backup: $(basename "$DB_FILE")"
            restore_database "$DB_FILE"
        else
            warning "No database backups found"
        fi

        if [ -n "$FILES_FILE" ]; then
            log "Latest files backup: $(basename "$FILES_FILE")"
            restore_files "$FILES_FILE"
        else
            warning "No file backups found"
        fi
        ;;
    date)
        if [ -z "$TARGET_DATE" ]; then
            error "Date not specified"
            exit 1
        fi

        log "Restoring from date: $TARGET_DATE"
        DB_FILE=$(get_backup_by_date "database" "$TARGET_DATE")
        FILES_FILE=$(get_backup_by_date "files" "$TARGET_DATE")

        if [ -n "$DB_FILE" ]; then
            log "Database backup: $(basename "$DB_FILE")"
            restore_database "$DB_FILE"
        else
            warning "No database backup found for date $TARGET_DATE"
        fi

        if [ -n "$FILES_FILE" ]; then
            log "Files backup: $(basename "$FILES_FILE")"
            restore_files "$FILES_FILE"
        else
            warning "No file backup found for date $TARGET_DATE"
        fi
        ;;
    *)
        # Manual file specification
        if [ -n "$DB_FILE" ]; then
            restore_database "$DB_FILE"
        fi

        if [ -n "$FILES_FILE" ]; then
            restore_files "$FILES_FILE"
        fi

        if [ -z "$DB_FILE" ] && [ -z "$FILES_FILE" ]; then
            error "No backup files specified. Use --help for usage."
            exit 1
        fi
        ;;
esac

log "Restore complete"
