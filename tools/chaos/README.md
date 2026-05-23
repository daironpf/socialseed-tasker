Chaos Testing Harness

Overview
- tools/chaos/chaosctl.py runs deterministic chaos scenarios defined in YAML.
- Scenarios live in tools/chaos/scenarios and produce JSON artifacts in tools/chaos/artifacts.

Run a scenario
- Build images and start baseline services:
  docker compose -f docker-compose.chaos.yml up -d --build
- Run scenario:
  python tools/chaos/chaosctl.py run redis-flap
- List scenarios:
  python tools/chaos/chaosctl.py list
- View latest artifact:
  python tools/chaos/chaosctl.py status

CI integration
- Set TASKER_CHAOS=1 in CI to enable chaos integration tests.
- Ensure Docker-in-Docker or Docker socket access is available in CI.

Adding scenarios
- Add a YAML file to tools/chaos/scenarios with steps using actions: docker_compose, exec, sleep, health_check.
- Keep steps deterministic and bounded in time.

Artifacts
- JSON artifacts include actions, checks, start/end timestamps, and errors.
