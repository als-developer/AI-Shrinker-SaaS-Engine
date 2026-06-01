#!/bin/bash
# Database Backup Script for Sovereign Grid
# Version: 31.0

set -euo pipefail

# Configuration
BACKUP_DIR="/backups/sovereign-grid"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sovereign_grid_${TIMESTAMP}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

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

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting database backup..."

# Check required tools
command -v pg_dump >/dev/null 2>&1 || error "pg_dump not found"
command -v gzip >/dev/null 2>&1 || error "gzip not found"
command -v aws >/dev/null 2>&1 || warn "aws CLI not found - S3 upload will be skipped"

# Perform backup
log "Dumping database..."
PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -F c \
    -f "${BACKUP_FILE%.gz}" \
    2>>"$LOG_FILE" || error "Database dump failed"

# Compress backup
log "Compressing backup..."
gzip "${BACKUP_FILE%.gz}" || error "Compression failed"

# Get file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup created: ${BACKUP_FILE} (${FILE_SIZE})"

# Upload to S3 (if configured)
if command -v aws >/dev/null 2>&1 && [ -n "${AWS_S3_BUCKET:-}" ]; then
    log "Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://${AWS_S3_BUCKET}/backups/${BACKUP_FILE##*/}" \
        --storage-class STANDARD_IA \
        2>>"$LOG_FILE" || warn "S3 upload failed"
fi

# Clean old backups
log "Cleaning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "sovereign_grid_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

log "Backup completed successfully!"
