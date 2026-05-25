# Contract Testing and Mock Server

## Quickstart

Start mock server:
```bash
python tools/contracts/mockctl.py start --spec openapi.yaml --port 9000 --overrides mocks/overrides --seed 42
```

Run contract tests against provider:
```bash
python tools/contracts/contractctl.py run --provider http://localhost:8000 --spec openapi.yaml --out reports/report.json
```

## Overrides

Place JSON files in `mocks/overrides` named `METHOD_path_to_route.json`, e.g., `GET_api_v1_items.json`.

## CI

Use `.github/workflows/contract-test.yml` to run unit tests on PRs.

## Determinism

Example generation uses deterministic seed; mock responses are stable across runs when seed and spec are unchanged.
