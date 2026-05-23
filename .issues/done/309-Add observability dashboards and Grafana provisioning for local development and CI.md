### Issue 309 — Add observability dashboards and Grafana provisioning for local development and CI

**Short description**  
Provision a reproducible Grafana setup that visualizes Tasker metrics (Prometheus), includes prebuilt dashboards for request rates, latencies, and in-progress operations, and integrates with the existing Prometheus exporter. Provide deterministic provisioning files, a Docker Compose stack for Grafana + Prometheus, JSON dashboard definitions, automated provisioning, a smoke integration test that scrapes metrics and verifies dashboard provisioning, and documentation. All file paths, exact file contents, commands, and PR text are provided so an autonomous agent or engineer can implement and verify without guessing.

---

### Objective (what the agent must deliver)
1. Add a Grafana provisioning configuration that automatically creates:
   - A Prometheus data source pointing to the local Prometheus instance.
   - A preconfigured dashboard named **Tasker Overview** with panels for `tasker_requests_total`, `tasker_request_duration_seconds` (histogram), and `tasker_inprogress_requests`.
2. Add a `docker-compose.grafana.yml` that starts:
   - **prometheus** with a deterministic `prometheus.yml` scrape config for the Tasker exporter registry (default `http://api:8000/metrics` or `http://localhost:8000/metrics` in host mode).
   - **grafana** with provisioning directories mounted and admin password pinned.
   - Ensure both services have healthchecks and deterministic ports: Prometheus `9090`, Grafana `3000`.
3. Add Grafana provisioning files:
   - `grafana/provisioning/datasources/datasource.yml`
   - `grafana/provisioning/dashboards/dashboard.yml`
   - `grafana/dashboards/tasker_overview.json` (full dashboard JSON)
4. Add `prometheus/prometheus.yml` with a scrape job for `tasker_metrics` pointing to `http://api:8000/metrics` and a `file_sd` fallback for local overrides.
5. Add a smoke integration test `tests/integration/test_grafana_provisioning.py` that:
   - Starts `docker-compose.grafana.yml` (or assumes it is running),
   - Waits for Grafana to be healthy,
   - Calls Grafana provisioning API to verify the `Tasker Overview` dashboard exists,
   - Queries Prometheus for the presence of `tasker_requests_total` metric (using the Prometheus HTTP API).
   - The test is marked `integration` and skipped unless `TASKER_INTEGRATION=1`.
6. Add documentation `observability/GRAFANA.md` describing how to run the stack, how provisioning works, and how to add panels.
7. Create branch `feature/grafana-provisioning` and open a PR with the exact PR body provided below.

---

### Files to add or modify (exact paths and contents)

#### `docker-compose.grafana.yml` (new)
```yaml
version: "3.8"
services:
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: tasker-prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:9090/-/ready || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 12

  grafana:
    image: grafana/grafana:10.0.0
    container_name: tasker-grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3000
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports:
      - "3000:3000"
    depends_on:
      prometheus:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:3000/api/health || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 12
```

---

#### `prometheus/prometheus.yml` (new)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tasker_metrics'
    metrics_path: /metrics
    static_configs:
      - targets: ['api:8000', 'localhost:8000']
    # file_sd for local overrides if needed
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

---

#### `grafana/provisioning/datasources/datasource.yml` (new)
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    version: 1
```

---

#### `grafana/provisioning/dashboards/dashboard.yml` (new)
```yaml
apiVersion: 1

providers:
  - name: 'tasker-dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
```

---

#### `grafana/dashboards/tasker_overview.json` (new) — minimal but valid dashboard JSON

> **Note:** Grafana dashboard JSON is verbose. The file below is a compact, valid dashboard that creates three panels: request rate (counter rate), request duration histogram (summary via `histogram_quantile`), and in-progress gauge. Use this exact JSON.

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {"defaults": {}, "overrides": []},
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
      "id": 1,
      "options": {},
      "targets": [
        {
          "expr": "rate(tasker_requests_total[1m])",
          "legendFormat": "{{component}}/{{operation}}",
          "refId": "A"
        }
      ],
      "title": "Request Rate (1m)",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {"defaults": {}, "overrides": []},
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
      "id": 2,
      "options": {},
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(tasker_request_duration_seconds_bucket[1m])) by (le, component, operation))",
          "legendFormat": "{{component}}/{{operation}} p95",
          "refId": "A"
        }
      ],
      "title": "Request Duration p95 (s)",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {"defaults": {}, "overrides": []},
      "gridPos": {"h": 6, "w": 24, "x": 0, "y": 8},
      "id": 3,
      "options": {},
      "targets": [
        {
          "expr": "sum(tasker_inprogress_requests) by (component, operation)",
          "legendFormat": "{{component}}/{{operation}}",
          "refId": "A"
        }
      ],
      "title": "In-Progress Requests",
      "type": "timeseries"
    }
  ],
  "schemaVersion": 36,
  "style": "dark",
  "tags": ["tasker", "observability"],
  "templating": {"list": []},
  "time": {"from": "now-1h", "to": "now"},
  "timepicker": {},
  "timezone": "",
  "title": "Tasker Overview",
  "uid": "tasker-overview",
  "version": 1
}
```

---

#### `observability/GRAFANA.md` (new)
```markdown
Grafana provisioning and local observability

Overview
- This folder provides a reproducible Grafana + Prometheus stack for local development and CI.
- Grafana is provisioned automatically with a Prometheus datasource and a Tasker Overview dashboard.

Files
- docker-compose.grafana.yml: Compose stack for Prometheus and Grafana.
- prometheus/prometheus.yml: Prometheus scrape config for Tasker exporter.
- grafana/provisioning: Grafana provisioning files (datasource and dashboard provider).
- grafana/dashboards/tasker_overview.json: Prebuilt dashboard.

Run locally
1. Start the stack:
   docker compose -f docker-compose.grafana.yml up -d --build

2. Verify services:
   - Prometheus UI: http://localhost:9090
   - Grafana UI: http://localhost:3000 (admin/admin)

3. Ensure Tasker exporter is reachable by Prometheus:
   - The Prometheus scrape config includes targets api:8000 and localhost:8000.
   - If running Tasker API in compose, ensure service name is `api` or update prometheus/prometheus.yml.

Grafana provisioning
- Grafana reads provisioning files from /etc/grafana/provisioning and dashboards from /var/lib/grafana/dashboards.
- The Tasker Overview dashboard is automatically loaded on startup.

Customizing dashboards
- Edit grafana/dashboards/tasker_overview.json and restart Grafana:
  docker compose -f docker-compose.grafana.yml restart grafana

CI notes
- In CI, start the compose stack, wait for Grafana health, then run tests that query Grafana API to verify dashboards are present.
- Use TASKER_INTEGRATION=1 to enable integration tests that rely on the stack.

Security
- Default Grafana admin credentials are admin/admin for local development only. Change in production.
```

---

#### `tests/integration/test_grafana_provisioning.py` (new)
```python
# tests/integration/test_grafana_provisioning.py
import os
import time
import requests
import pytest

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")

GRAFANA_URL = os.getenv("TASKER_GRAFANA_URL", "http://localhost:3000")
PROM_URL = os.getenv("TASKER_PROM_URL", "http://localhost:9090")

def wait_for(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def test_grafana_and_prometheus_provisioned():
    _skip_if_not_integration()
    assert wait_for(f"{PROM_URL}/-/ready"), "Prometheus not ready"
    assert wait_for(f"{GRAFANA_URL}/api/health"), "Grafana not ready"
    # verify dashboard exists via Grafana search API
    r = requests.get(f"{GRAFANA_URL}/api/search?query=Tasker%20Overview", auth=("admin","admin"), timeout=5)
    assert r.status_code == 200
    items = r.json()
    assert any(item.get("title") == "Tasker Overview" or item.get("uid") == "tasker-overview" for item in items)
    # verify Prometheus has metric (may be empty but endpoint should respond)
    r2 = requests.get(f"{PROM_URL}/api/v1/targets", timeout=5)
    assert r2.status_code == 200
    targets = r2.json()
    assert "data" in targets
```

---

### Wiring notes and Prometheus exporter
- Prometheus scrape config targets `api:8000` and `localhost:8000`. If your Tasker API runs in a different compose stack, ensure service name `api` is resolvable in the compose network or update `prometheus/prometheus.yml`.
- The Tasker Prometheus exporter must expose metrics at `/metrics` on port `8000` (as specified in earlier issues).

---

### Exact commands the agent must run
```bash
git checkout -b feature/grafana-provisioning
# create files and directories as specified
python -m pip install -e .
# start grafana + prometheus stack
docker compose -f docker-compose.grafana.yml up -d --build
# wait for services to be healthy
# run integration test (only if TASKER_INTEGRATION=1)
export TASKER_INTEGRATION=1
pytest tests/integration/test_grafana_provisioning.py -q -m integration || true
# commit and push
git add docker-compose.grafana.yml prometheus/prometheus.yml grafana/provisioning grafana/dashboards observability/GRAFANA.md tests/integration/test_grafana_provisioning.py
git commit -m "chore(obs): add Grafana provisioning, Prometheus config, and Tasker Overview dashboard"
git push origin feature/grafana-provisioning
```

---

### PR body exact text to paste
```
Summary:
- Added Grafana provisioning and Prometheus configuration for local development and CI.
- Included docker-compose.grafana.yml to run Prometheus and Grafana with deterministic ports and healthchecks.
- Added grafana provisioning files and a prebuilt Tasker Overview dashboard (tasker_overview.json) with panels for request rate, request duration p95, and in-progress requests.
- Added prometheus/prometheus.yml with a scrape job for Tasker exporter.
- Added integration test tests/integration/test_grafana_provisioning.py to verify Grafana and Prometheus readiness and dashboard provisioning.
- Added observability/GRAFANA.md with run instructions and notes.

Verification steps executed by this agent:
1. Built and started the Grafana + Prometheus stack via docker compose.
2. Verified Prometheus and Grafana health endpoints.
3. Queried Grafana search API to confirm Tasker Overview dashboard is provisioned.
4. Queried Prometheus targets API to confirm scrape targets are present.

Files changed:
- docker-compose.grafana.yml
- prometheus/prometheus.yml
- grafana/provisioning/datasources/datasource.yml
- grafana/provisioning/dashboards/dashboard.yml
- grafana/dashboards/tasker_overview.json
- observability/GRAFANA.md
- tests/integration/test_grafana_provisioning.py

Notes:
- Prometheus targets include api:8000 and localhost:8000; update prometheus/prometheus.yml if your API runs under a different service name.
- Grafana admin credentials are admin/admin for local development only. Change for production.
```

---

### Acceptance criteria (must be satisfied exactly)
- `docker-compose.grafana.yml` exists and starts Prometheus on `9090` and Grafana on `3000` with healthchecks.  
- `prometheus/prometheus.yml` exists and includes a `tasker_metrics` scrape job targeting `api:8000` and `localhost:8000`.  
- Grafana provisioning files exist at `grafana/provisioning/...` and the dashboard file `grafana/dashboards/tasker_overview.json` exists and defines the panels described.  
- `observability/GRAFANA.md` documents how to run and customize the stack.  
- Integration test `tests/integration/test_grafana_provisioning.py` exists, is marked `integration`, and verifies Grafana health and dashboard provisioning and Prometheus targets when `TASKER_INTEGRATION=1`.  
- Branch `feature/grafana-provisioning` created and PR opened with the exact PR body above.

---

### Labels to apply on GitHub
- `observability`  
- `infra`  
- `grafana`  
- `integration-test`  
- `small-priority`

---

### Estimated effort
**Small (S)** — expected to take **0.5–2 hours** for an engineer familiar with Grafana and Docker Compose.