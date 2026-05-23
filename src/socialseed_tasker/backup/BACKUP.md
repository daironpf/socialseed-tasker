Backup and Export Guide

Commands
- Manual export:
  ./scripts/backup.sh export --out ./exports/backup-YYYYMMDDTHHMMSSZ.tar.gz
- Verify export:
  ./scripts/backup.sh verify --file ./exports/backup-YYYYMMDDTHHMMSSZ.tar.gz
- Restore:
  ./scripts/backup.sh restore --file ./exports/backup-YYYYMMDDTHHMMSSZ.tar.gz

Options
- --no-storage skip exporting storage keys
- --encrypt enable AES-256-GCM encryption (requires cryptography)
- --passphrase passphrase for encryption

Environment variables
- TASKER_BACKUP_PASSPHRASE optional passphrase for scheduled backups
- TASKER_INTEGRATION set to 1 to run integration tests

Format
- Export is a tar.gz containing:
  - issues.json
  - graph.json
  - storage_* files for storage keys
  - MANIFEST.json with checksums and metadata

Restoration
- restore_data will call repo import methods if available:
  - issue_repo.import_list(list)
  - graph_repo.import_dump(list)
- Storage keys are restored via storage.put(key, bytes)

Security
- Encryption uses AES-256-GCM derived from passphrase via SHA256 for local dev only.
- In production, use a secure key management system and verify signatures.

Verification
- verify_export checks MANIFEST.json checksums and returns True if all match.
