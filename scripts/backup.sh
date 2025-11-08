#!/bin/bash
#
# KooAI Backup Script
# 
# This script backs up:
# 1. PostgreSQL database
# 2. Redis data (optional)
# 3. Uploaded files
# 4. Configuration files
#
# Usage:
#   ./scripts/backup.sh [options]
#
# Options:
#   --db-only       Backup database only
#   --files-only    Backup files only
#   --full          Full backup (default)
#   --upload-s3     Upload to S3 after backup
#   --retention N   Keep backups for N days (default: 30)
#

set -euo pipefail

# ===========================
# Configuration
# ===========================

# Backup directory
BACKUP_DIR="${BACKUP_DIR:-/backup/kooai}"
LOG_FILE="${LOG_FILE:-/var/log/kooai/backup.log}"

# Database settings
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-kooai_db}"
DB_USER="${DB_USER:-kooai_user}"
DB_PASSWORD="${PGPASSWORD:-}"

# Redis settings
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_BACKUP="${REDIS_BACKUP:-false}"

# File paths
UPLOAD_DIR="${UPLOAD_DIR:-/var/lib/kooai/uploads}"
CONFIG_DIR="${CONFIG_DIR:-/etc/kooai}"

# S3 settings
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/kooai}"

# Retention
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y%m%d)

# Options
BACKUP_TYPE="full"
UPLOAD_TO_S3=false

# ===========================
# Functions
# ===========================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

check_dependencies() {
    local deps=("pg_dump" "tar" "gzip")
    
    for cmd in "${deps[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "$cmd is not installed"
            exit 1
        fi
    done
    
    if [ "$UPLOAD_TO_S3" = true ] && ! command -v aws &> /dev/null; then
        error "aws CLI is not installed but --upload-s3 was specified"
        exit 1
    fi
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

backup_database() {
    log "Starting database backup..."
    
    local backup_file="$BACKUP_DIR/db_${TIMESTAMP}.dump"
    
    # Export password for pg_dump
    export PGPASSWORD="$DB_PASSWORD"
    
    # Backup database
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -F c -f "$backup_file" 2>> "$LOG_FILE"; then
        
        # Compress
        log "Compressing database backup..."
        gzip "$backup_file"
        backup_file="${backup_file}.gz"
        
        local size=$(du -h "$backup_file" | cut -f1)
        log "Database backup completed: $backup_file ($size)"
        
        echo "$backup_file"
    else
        error "Database backup failed"
        return 1
    fi
    
    unset PGPASSWORD
}

backup_redis() {
    if [ "$REDIS_BACKUP" != "true" ]; then
        return 0
    fi
    
    log "Starting Redis backup..."
    
    local backup_file="$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
    
    # Trigger Redis save
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SAVE > /dev/null 2>&1; then
        # Copy RDB file
        local redis_rdb="/var/lib/redis/dump.rdb"
        if [ -f "$redis_rdb" ]; then
            cp "$redis_rdb" "$backup_file"
            gzip "$backup_file"
            backup_file="${backup_file}.gz"
            
            local size=$(du -h "$backup_file" | cut -f1)
            log "Redis backup completed: $backup_file ($size)"
            
            echo "$backup_file"
        else
            error "Redis RDB file not found: $redis_rdb"
            return 1
        fi
    else
        error "Redis backup failed"
        return 1
    fi
}

backup_files() {
    log "Starting files backup..."
    
    if [ ! -d "$UPLOAD_DIR" ]; then
        log "Upload directory does not exist: $UPLOAD_DIR"
        return 0
    fi
    
    local backup_file="$BACKUP_DIR/files_${TIMESTAMP}.tar.gz"
    
    # Count files
    local file_count=$(find "$UPLOAD_DIR" -type f | wc -l)
    log "Backing up $file_count files from $UPLOAD_DIR"
    
    # Create tarball
    if tar -czf "$backup_file" -C "$(dirname "$UPLOAD_DIR")" "$(basename "$UPLOAD_DIR")" 2>> "$LOG_FILE"; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "Files backup completed: $backup_file ($size)"
        
        echo "$backup_file"
    else
        error "Files backup failed"
        return 1
    fi
}

backup_config() {
    log "Starting configuration backup..."
    
    if [ ! -d "$CONFIG_DIR" ]; then
        log "Config directory does not exist: $CONFIG_DIR"
        return 0
    fi
    
    local backup_file="$BACKUP_DIR/config_${TIMESTAMP}.tar.gz"
    
    if tar -czf "$backup_file" -C "$(dirname "$CONFIG_DIR")" "$(basename "$CONFIG_DIR")" 2>> "$LOG_FILE"; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "Config backup completed: $backup_file ($size)"
        
        echo "$backup_file"
    else
        error "Config backup failed"
        return 1
    fi
}

upload_to_s3() {
    local file="$1"
    
    if [ -z "$S3_BUCKET" ]; then
        error "S3_BUCKET not set"
        return 1
    fi
    
    log "Uploading to S3: s3://$S3_BUCKET/$S3_PREFIX/$(basename "$file")"
    
    if aws s3 cp "$file" "s3://$S3_BUCKET/$S3_PREFIX/$(basename "$file")" 2>> "$LOG_FILE"; then
        log "Upload to S3 completed"
        return 0
    else
        error "Upload to S3 failed"
        return 1
    fi
}

cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    local deleted=0
    
    # Clean database backups
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "db_*.dump.gz" -type f -mtime +"$RETENTION_DAYS" -print0)
    
    # Clean file backups
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "files_*.tar.gz" -type f -mtime +"$RETENTION_DAYS" -print0)
    
    # Clean Redis backups
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "redis_*.rdb.gz" -type f -mtime +"$RETENTION_DAYS" -print0)
    
    # Clean config backups
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "config_*.tar.gz" -type f -mtime +"$RETENTION_DAYS" -print0)
    
    log "Deleted $deleted old backup files"
}

verify_backup() {
    local file="$1"
    
    log "Verifying backup: $file"
    
    case "$file" in
        *.dump.gz)
            # Verify gzip integrity
            if gzip -t "$file" 2>> "$LOG_FILE"; then
                log "Backup verification passed"
                return 0
            else
                error "Backup verification failed"
                return 1
            fi
            ;;
        *.tar.gz)
            # Verify tar.gz integrity
            if tar -tzf "$file" > /dev/null 2>> "$LOG_FILE"; then
                log "Backup verification passed"
                return 0
            else
                error "Backup verification failed"
                return 1
            fi
            ;;
        *)
            log "Skipping verification for unknown file type"
            return 0
            ;;
    esac
}

# ===========================
# Parse Arguments
# ===========================

while [[ $# -gt 0 ]]; do
    case $1 in
        --db-only)
            BACKUP_TYPE="database"
            shift
            ;;
        --files-only)
            BACKUP_TYPE="files"
            shift
            ;;
        --full)
            BACKUP_TYPE="full"
            shift
            ;;
        --upload-s3)
            UPLOAD_TO_S3=true
            shift
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --help)
            cat << HELP
KooAI Backup Script

Usage: $0 [options]

Options:
  --db-only       Backup database only
  --files-only    Backup files only
  --full          Full backup (default)
  --upload-s3     Upload to S3 after backup
  --retention N   Keep backups for N days (default: 30)
  --help          Show this help message

Environment Variables:
  BACKUP_DIR      Backup directory (default: /backup/kooai)
  DB_HOST         Database host (default: localhost)
  DB_PORT         Database port (default: 5432)
  DB_NAME         Database name (default: kooai_db)
  DB_USER         Database user (default: kooai_user)
  PGPASSWORD      Database password
  S3_BUCKET       S3 bucket name for uploads
  S3_PREFIX       S3 prefix (default: backups/kooai)

Example:
  # Full backup
  ./scripts/backup.sh

  # Database only with S3 upload
  ./scripts/backup.sh --db-only --upload-s3

  # Files only with custom retention
  ./scripts/backup.sh --files-only --retention 60
HELP
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ===========================
# Main
# ===========================

main() {
    log "=========================================="
    log "KooAI Backup Starting"
    log "Type: $BACKUP_TYPE"
    log "Timestamp: $TIMESTAMP"
    log "=========================================="
    
    # Check dependencies
    check_dependencies
    
    # Create backup directory
    create_backup_dir
    
    # Track backed up files
    local backed_up_files=()
    
    # Perform backups based on type
    case "$BACKUP_TYPE" in
        database)
            if db_file=$(backup_database); then
                backed_up_files+=("$db_file")
                verify_backup "$db_file"
            fi
            ;;
        files)
            if files_file=$(backup_files); then
                backed_up_files+=("$files_file")
                verify_backup "$files_file"
            fi
            ;;
        full)
            # Database
            if db_file=$(backup_database); then
                backed_up_files+=("$db_file")
                verify_backup "$db_file"
            fi
            
            # Redis
            if redis_file=$(backup_redis); then
                backed_up_files+=("$redis_file")
                verify_backup "$redis_file"
            fi
            
            # Files
            if files_file=$(backup_files); then
                backed_up_files+=("$files_file")
                verify_backup "$files_file"
            fi
            
            # Config
            if config_file=$(backup_config); then
                backed_up_files+=("$config_file")
                verify_backup "$config_file"
            fi
            ;;
    esac
    
    # Upload to S3 if requested
    if [ "$UPLOAD_TO_S3" = true ]; then
        for file in "${backed_up_files[@]}"; do
            upload_to_s3 "$file"
        done
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Summary
    log "=========================================="
    log "Backup Summary:"
    log "  Files created: ${#backed_up_files[@]}"
    for file in "${backed_up_files[@]}"; do
        local size=$(du -h "$file" | cut -f1)
        log "    - $(basename "$file") ($size)"
    done
    log "  Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    log "=========================================="
    log "KooAI Backup Completed Successfully"
    log "=========================================="
}

# Run main function
main
