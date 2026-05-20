# Workflow: Interactive Project Initialization (tasker init)

## Purpose
When an AI agent needs to initialize Tasker in a project (`tasker init`), the agent MUST interact with the user to collect all necessary information. This ensures the project is properly configured with accurate metadata.

---

## Rule: Always Guide the User

The agent acts as a **project initialization assistant**. It asks targeted questions, provides recommendations, and helps the user make informed decisions about their project setup.

---

## Step-by-Step Process

### Step 1: Detect Initialization Request
When the user mentions any of these keywords:
- "inicializar proyecto", "tasker init", "setup project", "initialize tasker"
- "crear proyecto", "create project", "scaffold"
- "configurar tasker", "setup tasker"

The agent must start the interactive initialization flow.

### Step 2: Collect Project Information

The agent asks the user for each piece of information below. For each field, the agent:
1. **Explains** what the field is for
2. **Recommends** a value based on best practices
3. **Asks** the user to confirm or provide their own value

#### Fields to Collect:

| # | Field | Description | Agent Recommendation |
|---|---|---|---|
| 1 | **Project Name** | Official name of the project | Use the repository name or a descriptive name |
| 2 | **Project Slug** | URL-friendly identifier (e.g., `my-project`) | Lowercase, hyphens, no spaces |
| 3 | **Description** | What the project does | Keep it concise but informative |
| 4 | **Repository URL** | Git remote URL | From `git remote -v` if available |
| 5 | **Architecture Type** | `hexagonal`, `monolithic`, `microservices`, `serverless`, `api-first` | **Recommend: `hexagonal`** for clean separation |
| 6 | **Language** | Primary programming language | Detect from existing codebase |
| 7 | **Framework** | Main framework (e.g., `fastapi`, `django`, `spring-boot`) | Detect from dependencies |
| 8 | **Database** | Primary database | **Recommend: `neo4j`** (required by Tasker) |
| 9 | **Frontend** | Frontend technology (if any) | `vue`, `react`, `angular`, `none` |
| 10 | **Other Services** | Additional services (e.g., `redis`, `celery`) | List only if needed |
| 11 | **Version** | Semantic version | Default: `0.1.0` |
| 12 | **Visibility** | `PUBLIC` or `PRIVATE` | Ask user |
| 13 | **Status** | `DEVELOPMENT`, `STAGING`, `PRODUCTION` | Default: `DEVELOPMENT` |
| 14 | **Main Stack** | Core technologies (comma-separated) | e.g., `python, fastapi, neo4j` |
| 15 | **Tech Stack** | All technologies used | Full list including dev tools |
| 16 | **GitHub Repo** | Full GitHub URL | From `git remote -v` |
| 17 | **Default Branch** | Git default branch | Default: `main` |
| 18 | **Forbidden Technologies** | Technologies to avoid | e.g., `file storage, external databases in core` |
| 19 | **Required Patterns** | Architectural patterns to enforce | e.g., `Hexagonal Architecture, Repository Pattern` |
| 20 | **Naming Conventions** | Code naming rules | e.g., `snake_case functions, PascalCase classes` |
| 21 | **Max Dependency Depth** | Max dependency chain depth | Default: `5` |
| 22 | **Setup Commands** | How to set up the project | e.g., `pip install -e . && docker compose up -d` |
| 23 | **Test Commands** | How to run tests | e.g., `pytest tests/` |
| 24 | **Build Commands** | How to build the project | e.g., `pip wheel . --wheel-dir dist/` |
| 25 | **Code Review Approvals** | Required approvals before merge | Default: `1` |

---

### Step 3: Present Summary

After collecting all information, the agent presents a summary table:

```
┌─────────────────────────────────────────────────────────┐
│              Project Initialization Summary              │
├─────────────────────────────────────────────────────────┤
│ Project Name:        socialseed-tasker                  │
│ Slug:                socialseed-tasker                  │
│ Description:         Graph-based task manager for AI    │
│ Architecture:        hexagonal                          │
│ Language:            python                             │
│ Framework:           fastapi/typer                      │
│ Database:            neo4j                              │
│ Frontend:            vue                                │
│ Version:             0.1.0                              │
│ Visibility:          PUBLIC                             │
│ Status:              DEVELOPMENT                        │
│ Main Stack:          python, fastapi, neo4j             │
│ GitHub Repo:         https://github.com/...             │
│ Default Branch:      main                               │
│ Forbidden Tech:      file storage, external DB in core  │
│ Required Patterns:   Hexagonal Architecture             │
│ Naming Conventions:  snake_case functions               │
│ Max Dependency Depth: 5                                 │
│ Setup Command:       pip install -e . && docker up -d   │
│ Test Command:        pytest tests/                      │
│ Build Command:       pip wheel . --wheel-dir dist/      │
│ Code Review:         1 approval                         │
├─────────────────────────────────────────────────────────┤
│ Confirm? [Y/n]:                                         │
└─────────────────────────────────────────────────────────┘
```

### Step 4: Execute Initialization

If the user confirms:
```bash
tasker init . \
  --project-name "<name>" \
  --architecture "<arch>" \
  --language "<lang>" \
  --framework "<framework>" \
  --database "<db>" \
  --frontend "<frontend>" \
  --version "<version>" \
  --visibility "<visibility>" \
  --status "<status>" \
  --main-stack "<main_stack>" \
  --tech-stack "<tech_stack>" \
  --github-repo "<repo>" \
  --default-branch "<branch>" \
  --forbidden-tech "<forbidden>" \
  --required-patterns "<patterns>" \
  --naming-conventions "<naming>" \
  --max-dependency-depth <depth> \
  --setup-commands "<setup>" \
  --test-commands "<test>" \
  --build-commands "<build>" \
  --code-review-count <count>
```

### Step 5: Verify and Report

After initialization:
1. Check that `.agent/` directory was created
2. Verify `project.json` has correct data
3. Verify `project.md` has correct context
4. Report success to user with next steps

---

## Example Conversation

```
Agent: I see you want to initialize Tasker in your project. Let me help you
       configure it properly. I'll ask you a few questions to set up the
       project metadata.

Agent: First, what's the name of your project?
       (This will be used in agent context files and documentation)

User: My awesome API

Agent: Great! For the slug (URL-friendly identifier), I recommend:
       `my-awesome-api` (lowercase, hyphens). Does that work?

User: Yes

Agent: Perfect. What does your project do? (Brief description)

User: It's a REST API for managing inventory

Agent: Got it. Now, what architecture does your project use?
       I recommend `hexagonal` for clean separation of concerns.
       Options: hexagonal, monolithic, microservices, serverless, api-first

User: hexagonal

... (continues for all fields) ...

Agent: Here's the summary of your project configuration:
       [presents table]

       Does this look correct? [Y/n]

User: Y

Agent: Initializing Tasker in your project...
       [runs tasker init with all parameters]

       ✅ Tasker initialized successfully!
       Next steps:
       1. Start Neo4j: docker compose -f .agent/docker-compose.yml up -d
       2. Configure environment: cp .agent/configs/.env.example .agent/configs/.env
       3. Start API: tasker api
       4. Register your agent: tasker agent register --id my-agent --name "My Agent" --role developer
```

---

## Important Notes

1. **Never skip fields**: All fields should be collected, even if using defaults.
2. **Explain each field**: The user may not know what each field means.
3. **Provide recommendations**: Help the user make informed decisions.
4. **Detect from codebase**: If the project already has code, detect language, framework, etc.
5. **Validate input**: Ensure slugs are URL-friendly, versions are semantic, etc.
6. **Allow defaults**: If the user doesn't know, provide sensible defaults.

---

## CLI Reference

```bash
# Full initialization with all parameters
tasker init . \
  --project-name "my-project" \
  --architecture "hexagonal" \
  --language "python" \
  --framework "fastapi" \
  --database "neo4j" \
  --frontend "vue" \
  --version "0.1.0" \
  --visibility "PUBLIC" \
  --status "DEVELOPMENT" \
  --main-stack "python,fastapi,neo4j" \
  --tech-stack "python,fastapi,neo4j,vue,tree-sitter" \
  --github-repo "https://github.com/user/repo" \
  --default-branch "main" \
  --forbidden-tech "file storage,external databases in core" \
  --required-patterns "Hexagonal Architecture,Repository Pattern" \
  --naming-conventions "snake_case functions,PascalCase classes" \
  --max-dependency-depth 5 \
  --setup-commands "pip install -e . && docker compose up -d" \
  --test-commands "pytest tests/" \
  --build-commands "pip wheel . --wheel-dir dist/" \
  --code-review-count 1

# Quick initialization with defaults
tasker init .

# Force overwrite existing configuration
tasker init . --force
```

---

## See Also

- [AGENT_GUIDE.md](./AGENT_GUIDE.md) - Full agent protocol
- [API_REFERENCE.md](../../docs/API_REFERENCE.md) - Complete API documentation
- [ONBOARDING.md](../../docs/ONBOARDING.md) - Setup and configuration