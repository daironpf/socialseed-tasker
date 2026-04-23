# Skill: Project Module Detection and Setup

## Description

This skill enables AI agents to detect the project structure and create appropriate module components in SocialSeed Tasker. Instead of using generic names like "Backend" or "Frontend", the agent should discover and use the actual project module names.

## Trigger Phrases

- "setup project modules"
- "configure modules"
- "detectar modulos"
- "detectar proyecto"
- "analyze project structure"
- "init modules"
- When starting to work on a new project

## What This Skill Does

1. **Discover Project Structure**: Analyze the codebase to identify modules, services, or components
2. **Create Project Context**: Set up the project name and description in Tasker
3. **Create Module Components**: Create proper Tasker components based on discovered modules
4. **Configure for AI Agents**: Ensure modules are properly labeled for AI agent context

## Project Detection Strategy

### Step 1: Analyze Project Structure

Look for indicators of project architecture:

**For Microservices:**
- `docker-compose.yml` or `docker-compose.yaml` - service definitions
- `kubernetes/` or `k8s/` - Kubernetes configs
- Multiple `Dockerfile` files in different directories
- Service names in config files

**For Monolithic:**
- Single `package.json`, `pyproject.toml`, `pom.xml`, etc.
- Single main entry point

**For Modular:**
- Multiple packages/modules in `src/`, `lib/`, `packages/`
- Monorepo configurations (Nx, Turborepo, Lerna)

### Step 2: Identify Module Names

From project analysis:
- Docker service names → Tasker components
- Package/directory names → Tasker components
- Git repository names → Project name

### Step 3: Create Components in Tasker

For each discovered module, create a Tasker component:
```bash
tasker component create "<module-name>" -p "<project-name>" -d "<description>"
```

## Module Discovery Examples

### Example 1: Microservices Project
```
Services discovered:
- auth-service (Authentication service)
- user-service (User management)
- payment-service (Payment processing)
- notification-service (Email/SMS notifications)
- api-gateway (API Gateway)

Actions:
tasker component create "auth-service" -p "my-microservices-app" -d "Authentication and authorization service"
tasker component create "user-service" -p "my-microservices-app" -d "User management and profiles"
tasker component create "payment-service" -p "my-microservices-app" -d "Payment processing and transactions"
tasker component create "notification-service" -p "my-microservices-app" -d "Email and SMS notifications"
tasker component create "api-gateway" -p "my-microservices-app" -d "API Gateway and routing"
```

### Example 2: Monorepo
```
Packages discovered:
- @myapp/auth (Authentication)
- @myapp/users (User management)
- @myapp/billing (Billing)
- @myapp/web (Frontend web app)
- @myapp/mobile (Mobile app)

Actions:
tasker component create "@myapp/auth" -p "my-monorepo" -d "Authentication package"
tasker component create "@myapp/users" -p "my-monorepo" -d "User management package"
tasker component create "@myapp/billing" -p "my-monorepo" -d "Billing package"
tasker component create "@myapp/web" -p "my-monorepo" -d "Frontend web application"
tasker component create "@myapp/mobile" -p "my-monorepo" -d "Mobile application"
```

### Example 3: Modular Python Project
```
Modules discovered:
- auth (Authentication module)
- users (User management)
- products (Product catalog)
- orders (Order processing)
- inventory (Inventory management)

Actions:
tasker component create "auth" -p "my-python-app" -d "Authentication module"
tasker component create "users" -p "my-python-app" -d "User management module"
tasker component create "products" -p "my-python-app" -d "Product catalog module"
tasker component create "orders" -p "my-python-app" -d "Order processing module"
tasker component create "inventory" -p "my-python-app" -d "Inventory management module"
```

## Key Conventions

1. **Use real module names**: Not "Backend" or "Frontend", but actual service/component names
2. **Set project name**: Use the actual project or repository name
3. **Add descriptive descriptions**: Explain what each module does
4. **Create issues under correct modules**: Always assign issues to the appropriate component

## Usage

When starting to work on a new project:
1. Analyze the project structure
2. Identify actual modules/services
3. Create components in Tasker with real names
4. Use these components when creating issues

This ensures that issues are properly organized and AI agents can understand the project context.

## Related Files

- `.agent/workflows/project-setup.md` - Detailed setup workflow
- `.agent/workflows/create-issue.md` - How to create properly categorized issues