.PHONY: dev-up dev-down test integration example-run wait-for-neo4j

DEV_COMPOSE = docker compose -f docker-compose.dev.yml
PY = python

dev-up:
	$(DEV_COMPOSE) up -d
	./scripts/wait-for-service.sh http://localhost:7474 60

dev-down:
	$(DEV_COMPOSE) down -v

wait-for-neo4j:
	./scripts/wait-for-service.sh http://localhost:7474 60

test:
	$(PY) -m pip install -e ".[dev]"
	pytest -q -k "not integration"

integration:
	$(PY) -m pip install -e ".[dev]"
	$(DEV_COMPOSE) up -d
	./scripts/wait-for-service.sh http://localhost:7474 60
	pytest -q -m integration

example-run:
	$(PY) -m pip install -e ".[dev]"
	$(DEV_COMPOSE) up -d
	./scripts/wait-for-service.sh http://localhost:7474 60
	$(DEV_COMPOSE) exec -T tasker-dev bash -lc "pip install -e /workspace 2>/dev/null; python /workspace/examples/mini_project/bootstrap.py"
	@echo "Example output written to examples/output.json"
