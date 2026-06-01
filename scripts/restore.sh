#!/bin/bash
# Database Restore Script for Sovereign Grid
# Version: 31.0

set -euo pipefail

# Configuration
BACKUP_FILE=${1:-}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/backups/restore_${TIMESTAMP}.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Validate backup file
if [ -z "$BACKUP_FILE" ]; then
    error "Usage: $0 <backup_file>"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
fi

log "Starting database restore from: $BACKUP_FILE"

# Confirm restore
read -p "⚠️  This will overwrite the current database. Are you sure? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    error "Restore cancelled by user"
fi

# Check required tools
command -v pg_restore >/dev/null 2>&1 || error "pg_restore not found"

# Check if file is gzipped
if file "$BACKUP_FILE" | grep -q "gzip compressed"; then
    log "Decompressing backup file..."
    gunzip -c "$BACKUP_FILE" > "${BACKUP_FILE%.gz}"
    RESTORE_FILE="${BACKUP_FILE%.gz}"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Perform restore
log "Restoring database..."
PGPASSWORD="${DB_PASSWORD}" pg_restore \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --clean \
    --if-exists \
    --no-owner \
    --verbose \
    "$RESTORE_FILE" 2>>"$LOG_FILE" || error "Database restore failed"

# Clean up temp file
if [ "$RESTORE_FILE" != "$BACKUP_FILE" ]; then
    rm -f "$RESTORE_FILE"
fi

log "Database restore completed successfully!"
