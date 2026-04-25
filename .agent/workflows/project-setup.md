# Workflow: Project Setup and Module Detection

## When to Use

When starting to work on a new project or when the user wants to configure the project modules in SocialSeed Tasker. This workflow should be triggered for setting up the project context.

## Purpose

1. Analyze project structure to identify modules/services
2. Create proper Tasker components with real module names
3. Set up project context for issue organization
4. Enable AI agents to understand project architecture

## Steps

### Step 1: Discover Project Structure

Analyze the codebase to identify the project type and modules:

#### For Microservices Projects
Check for:
- `docker-compose.yml` - Extract service names
- `docker-compose.yaml` - Alternative filename
- `kubernetes/` or `k8s/` - Kubernetes definitions
- Service names in config files

#### For Monorepo Projects
Check for:
- `package.json` workspaces
- Nx/Turborepo/Lerna config
- Multiple packages in `packages/` or `apps/`

#### For Modular Projects
Check for:
- Multiple directories in `src/` or `lib/`
- Python packages (directories with `__init__.py`)
- Go modules

#### For Monolithic Projects
Check for:
- Single main entry point
- Framework indicators (Django, Rails, Express, etc.)

### Step 2: Document Discovered Modules

Create a list of modules with:
- **Name**: The actual module/service name
- **Type**: service, package, module, app
- **Description**: What it does (from code analysis or docs)

### Step 3: Create Tasker Components

For each discovered module, create a component:

```bash
tasker component create "<module-name>" \
  -p "<project-name>" \
  -d "<description>" \
  -l "<module-type>"
```

Example:
```bash
# For a microservices project
tasker component create "auth-service" \
  -p "ecommerce-platform" \
  -d "Authentication and authorization microservice" \
  -l "microservice,auth"

tasker component create "inventory-service" \
  -p "ecommerce-platform" \
  -d "Product inventory management" \
  -l "microservice,inventory"
```

### Step 4: Verify Setup

List all created components to verify:
```bash
tasker component list
```

## Project Type Detection Examples

### Example: Microservices Detection

Given `docker-compose.yml`:
```yaml
services:
  auth-service:
    build: ./auth
  user-service:
    build: ./users
  order-service:
    build: ./orders
  payment-service:
    build: ./payments
  api-gateway:
    build: ./gateway
```

Create components:
- `auth-service` - Authentication service
- `user-service` - User management service
- `order-service` - Order processing service
- `payment-service` - Payment processing service
- `api-gateway` - API Gateway

### Example: Monorepo Detection

Given `package.json`:
```json
{
  "workspaces": ["packages/*"]
}
```

With `packages/` containing:
- `auth/` - Authentication package
- `users/` - User management package
- `billing/` - Billing package

Create components:
- `@myorg/auth` - Authentication package
- `@myorg/users` - User management package
- `@myorg/billing` - Billing package

### Example: Python Project Detection

Given directory structure:
```
src/
  auth/
    __init__.py
    models.py
    views.py
  users/
    __init__.py
    models.py
    views.py
  products/
    __init__.py
    models.py
    views.py
  orders/
    __init__.py
    models.py
    views.py
```

Create components:
- `auth` - Authentication module
- `users` - User management module
- `products` - Product catalog module
- `orders` - Order processing module

## Important Notes

1. **Use real names**: NOT "Backend" or "Frontend" - use actual module names
2. **Project name**: Use the actual project/repository name
3. **Descriptions**: Add meaningful descriptions for each component
4. **Labels**: Add appropriate labels like `microservice`, `package`, `module`, `app`

## Anti-Patterns to Avoid

- Using generic names like "Backend", "Frontend", "API"
- Creating components without analyzing project structure
- Not setting proper project name
- Skipping module detection and using default components