# Data Catalog and Schema Registry

## Overview
- Register JSON Schemas and datasets.
- Validate incoming payloads against registered schema versions.
- Enforce compatibility when adding new schema versions.

## API Endpoints
- `POST /api/v1/registry/schemas`
- `GET /api/v1/registry/schemas/{name}/versions`
- `GET /api/v1/registry/schemas/{name}/{version}`
- `POST /api/v1/registry/datasets`
- `GET /api/v1/registry/datasets`
- `GET /api/v1/registry/datasets/{dataset_id}`

## CLI
- `tasker-registry register-schema --name <name> --version <v> --file <schema.json>`
- `tasker-registry get-schema --name <name> --version <v>`
- `tasker-registry register-dataset --dataset-id <id> --title <t> --description <d> --schema-name <s> --default-schema-version <v> --owner <o>`

## Compatibility Modes
- `BACKWARD`, `FORWARD`, `FULL`, `NONE`

## Validation Hook
- Use `ValidationMiddleware.validate_request(request, dataset_id)` in ingestion endpoints to enforce schema validation.

## Notes
- Registry persists schemas and datasets in StoragePort.
- Compatibility checks are conservative structural checks suitable for deterministic CI.
