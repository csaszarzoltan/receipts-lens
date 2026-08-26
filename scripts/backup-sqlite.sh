#!/usr/bin/env bash
# ReceiptLens SQLite daily backup — receipts.allthezoo.com
# Plan: docs/plans/production-rollout-2026-08-13.md v3 §Fázis 1/4
# DB:   /home/zoltan/receipts-lens/receiptlens-product.db
# Runs while the API is live — uses Python sqlite3 backup API for a
# consistent snapshot (avoids copying a hot WAL file). Retention: 7 days.
set -euo pipefail

DB_PATH="/home/zoltan/receipts-lens/receiptlens-product.db"
BACKUP_DIR="/home/zoltan/receipts-lens/backups"
LOG_FILE="/home/zoltan/receipts-lens/logs/backup.log"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/receiptlens-product-${TIMESTAMP}.db"

mkdir -p "${BACKUP_DIR}" "$(dirname "${LOG_FILE}")"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "[$(date -Iseconds)] BACKUP FAIL: DB not found at ${DB_PATH}" | tee -a "${LOG_FILE}" >&2
  exit 1
fi

# Consistent hot backup via sqlite3 backup API (no sqlite3 binary needed)
python3 -- - "${DB_PATH}" "${BACKUP_FILE}" <<'PY'
import sqlite3, sys
src_path, dst_path = sys.argv[1], sys.argv[2]
src = sqlite3.connect(src_path)
dst = sqlite3.connect(dst_path)
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()
# verify
con = sqlite3.connect(dst_path)
cur = con.execute("PRAGMA integrity_check;")
row = cur.fetchone()
if row is None or row[0] != "ok":
    print(f"integrity_check failed: {row}", file=sys.stderr)
    sys.exit(1)
con.close()
PY

SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
echo "[$(date -Iseconds)] BACKUP OK: ${BACKUP_FILE} (${SIZE})" | tee -a "${LOG_FILE}"

# Retention: keep last 7 days
find "${BACKUP_DIR}" -maxdepth 1 -name "receiptlens-product-*.db" -mtime +7 -print -delete 2>&1 | while read -r old; do
  echo "[$(date -Iseconds)] RETENTION: removed ${old}" | tee -a "${LOG_FILE}"
done

# Optional: log total count
COUNT="$(ls -1 "${BACKUP_DIR}"/receiptlens-product-*.db 2>/dev/null | wc -l)"
echo "[$(date -Iseconds)] BACKUP DONE: ${COUNT} backup(s) in ${BACKUP_DIR}" | tee -a "${LOG_FILE}"
