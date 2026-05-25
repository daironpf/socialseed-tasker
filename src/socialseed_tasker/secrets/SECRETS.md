# Secrets Management and Rotation Guide

## Overview
- Secrets are stored encrypted using AES-256-GCM derived from `TASKER_SECRETS_MASTER_KEY`.
- `SecretsStore` persists encrypted blobs in `StoragePort` under keys `secrets:<name>`.
- `Rotator` schedules and runs deterministic rotations for tests when `TASKER_SECRETS_DETERMINISTIC=1`.

## Environment variables
| Variable | Description |
|----------|-------------|
| `TASKER_SECRETS_MASTER_KEY` | Hex-encoded AES-256-GCM master key (required in production) |
| `TASKER_SECRETS_DETERMINISTIC=1` | Enable deterministic rotation for tests |
| `TASKER_SECRETS_USE_RANDOM_NONCE=0` | Use deterministic nonce (dev only) |

## API usage

### Create secret
```http
POST /api/v1/secrets
{
  "name": "db/password",
  "value": "<base64-encoded-value>",
  "metadata": {"env": "prod"}
}
```

### Read metadata
```http
GET /api/v1/secrets/db/password
```

### Read value
```http
GET /api/v1/secrets/db/password/value
```

### Schedule rotation
```http
POST /api/v1/secrets/rotate
{
  "name": "db/password",
  "interval_seconds": 3600,
  "policy": {"strategy": "random", "length": 32}
}
```

### Run rotation
```http
POST /api/v1/secrets/rotate/run
{
  "rotation_id": "rot-..."
}
```

### Audit log
```http
GET /api/v1/secrets/audit
```

## CLI
```bash
# Put secret from file
python tools/secrets/secretctl.py put --name db/password --file ./pw.bin

# Get secret metadata
python tools/secrets/secretctl.py get --name db/password

# Get secret value
python tools/secrets/secretctl.py get --name db/password --value

# Schedule rotation
python tools/secrets/secretctl.py rotate --name db/password --interval 3600 --policy '{"strategy":"random","length":32}'

# Run rotation
python tools/secrets/secretctl.py rotate-run --id rot-...

# Export audit log
python tools/secrets/secretctl.py audit --out audit.json
```

## Security notes
- Never commit `TASKER_SECRETS_MASTER_KEY` to source control.
- In production, use a secure KMS and set `TASKER_SECRETS_MASTER_KEY` from KMS-derived key.
- Deterministic modes are for tests only.
