#!/usr/bin/env bash
# ==============================================================================
# ArthaAI PostgreSQL Backup Script
# Creates a compressed, timestamped database dump from the ArthaAI Postgres container.
# NOTE: This only backs up ArthaAI's isolated PostgreSQL database.
# It does NOT touch any other database.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/arthaai}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/arthaai_backup_${TIMESTAMP}.sql.gz"
CONTAINER_NAME="${CONTAINER_NAME:-arthaai-postgres}"
DB_USER="${POSTGRES_USER:-artha_user}"
DB_NAME="${POSTGRES_DB:-arthaai}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting ArthaAI PostgreSQL backup..."

# Execute pg_dump inside the container and compress on the fly
docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"

echo "[$(date)] Backup completed successfully: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Prune old backups older than retention window
find "${BACKUP_DIR}" -type f -name "arthaai_backup_*.sql.gz" -mtime +"${RETENTION_DAYS}" -exec rm -f {} \;
echo "[$(date)] Cleaned up backups older than ${RETENTION_DAYS} days."
