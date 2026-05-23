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
