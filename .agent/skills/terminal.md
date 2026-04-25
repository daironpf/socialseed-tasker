# Skill: Terminal Management

## Description
Provides capabilities for shell command execution, venv management, and Docker operations. Essential for environment isolation and infrastructure control.

---

## Capabilities

### 1. Docker Management

```bash
# Stop and remove containers + volumes (clean slate)
docker-compose down -v --remove-orphans

# Start services in background
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service]

# Stop services (data persists)
docker-compose down
```

### 2. Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Deactivate
deactivate

# Install package
pip install -e .
# or
pip install .
```

### 3. Shell Operations

```bash
# Create directory
mkdir -p <dir>

# Change directory
cd <dir>

# List files
ls -la

# Remove directory recursively
rm -rf <dir>
```

### 4. Service Health Check

```bash
# Wait for service readiness
sleep 10

# Check if port is listening
curl -s http://localhost:8000/health
```

---

## Usage Examples

### Setup isolated environment (Phase 1)

```bash
docker-compose down -v --remove-orphans  # Clean slate
mkdir -p real-test && cd real-test      # Create isolation dir
python -m venv venv                   # Create venv
venv\Scripts\activate                 # Activate
pip install -e ..                     # Install package
```

### Initialize infrastructure (Phase 2)

```bash
tasker init .                          # Scaffold
docker-compose up -d                  # Start services
sleep 10                               # Wait for readiness
docker-compose ps                     # Verify status
```

### Cleanup (Phase 4)

```bash
docker-compose down -v --remove-orphans  # Clean Docker
deactivate                             # Deactivate venv
```

---

## Best Practices

1. **Always clean before starting**: Use `docker-compose down -v --remove-orphans` to ensure zero state
2. **Wait for services**: Add `sleep 10` or health check before relying on services
3. **Verify installation**: Run `tasker --version` after pip install to confirm
4. **Check logs on errors**: Use `docker-compose logs -f` for debugging

---

## Key Commands Reference

| Command | Purpose |
|---------|---------|
| `docker-compose down -v --remove-orphans` | Full cleanup |
| `docker-compose up -d` | Start services |
| `docker-compose ps` | Check status |
| `python -m venv venv` | Create venv |
| `venv\Scripts\activate` | Activate (Windows) |
| `source venv/bin/activate` | Activate (Linux/Mac) |
| `pip install -e .` | Install editable |
| `tasker --version` | Verify installation |