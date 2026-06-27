# Feature Flags & Runtime Configuration

## Overview

The feature-flag system allows operators to toggle behaviour at runtime
without redeploying.  Flags are stored in the shared key-value `StoragePort`
under the single key `flags:registry`.

## Precedence

1. **Environment variable** `TASKER_FLAG_<NAME>` (uppercased, dashes → underscores).
   If the value is valid JSON it is decoded; otherwise it is treated as a raw string.
2. **Persisted store** (the `flags:registry` key in `StoragePort`).
3. **Default value** supplied by the caller.

## CLI Usage

```
tasker flag-set --name my_flag --value true
tasker flag-get --name my_flag
tasker flag-list
tasker flag-delete --name my_flag
```

All commands require `admin` RBAC permission and a valid `--token`.

## API Endpoints

| Method | Path                     | Description        |
|--------|--------------------------|--------------------|
| GET    | /api/v1/admin/flags      | List all flags     |
| GET    | /api/v1/admin/flags/{name} | Get a single flag |
| POST   | /api/v1/admin/flags      | Create/update flag |
| DELETE | /api/v1/admin/flags/{name} | Delete a flag     |

All endpoints require `admin` RBAC permission (checked via bearer token).

## Hot-Reload Polling

When `TASKER_CONFIG_RELOAD=1` the `RuntimeConfig` spawns a background thread
that polls the store every `TASKER_CONFIG_POLL_SECONDS` (default `5`) and
fires registered callbacks on changes.  Use `register_callback(name, fn)` to
subscribe.

## Environment Variables

| Variable                      | Default | Description                        |
|-------------------------------|---------|------------------------------------|
| `TASKER_FLAG_<NAME>`          | —       | Override a flag at process start   |
| `TASKER_CONFIG_RELOAD`        | `0`     | Enable polling thread              |
| `TASKER_CONFIG_POLL_SECONDS`  | `5`     | Polling interval in seconds        |
