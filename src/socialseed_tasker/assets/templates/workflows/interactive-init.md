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

### Step 2: Interactive Question Flow

**CRITICAL RULE**: The agent MUST ask questions **ONE AT A TIME**. Never present a list of all questions at once.

For each field, the agent follows this pattern:

```
1. Ask the question clearly
2. Explain what the field is for (brief)
3. Provide a recommendation
4. Offer 2-3 suggested options (when applicable)
5. Wait for user response
6. If user writes their own value, accept it
7. If user selects an option, use it
8. Move to next question
```

#### Example Pattern:

```
Agent: 📋 **Question 1 of 25: Project Name**
       
       What is the official name of your project?
       
       💡 This will be used in documentation, agent context, and configuration files.
       
       🎯 Recommendation: Use your repository name or a descriptive name.
       
       Detected from git: socialseed-tasker
       
       Your choice (or press Enter to use detected): 
```

```
User: My Awesome API

Agent: ✅ Great! Project name set to: "My Awesome API"

       📋 **Question 2 of 25: Project Slug**
       
       What is the URL-friendly identifier for your project?
       
       💡 This is used for URLs, directory names, and API endpoints.
       
       🎯 Recommendation: Use lowercase with hyphens, no spaces.
       
       Suggested options:
       1. my-awesome-api
       2. my_awesome_api
       3. myawesomeapi
       
       Your choice (type 1-3 or write your own):
```

---

### Step 3: Fields to Collect (Ask ONE at a Time)

| # | Field | Question to Ask | Recommendation | Options to Offer |
|---|---|---|---|---|
| 1 | **Project Name** | "What is the official name of your project?" | Use repo name | Detect from git remote |
| 2 | **Project Slug** | "What is the URL-friendly identifier?" | lowercase-hyphens | 1. detected-slug, 2. detected_slug, 3. detectedslug |
| 3 | **Description** | "Briefly describe what your project does." | 1-2 sentences | None |
| 4 | **Repository URL** | "What is your Git repository URL?" | From `git remote -v` | Detected URL or "none" |
| 5 | **Architecture Type** | "What architecture does your project use?" | **hexagonal** | 1. hexagonal, 2. monolithic, 3. microservices, 4. serverless, 5. api-first |
| 6 | **Language** | "What is the primary programming language?" | Detect from codebase | 1. python, 2. typescript, 3. java, 4. go, 5. other |
| 7 | **Framework** | "What is the main framework?" | Detect from deps | 1. fastapi, 2. django, 3. spring-boot, 4. express, 5. other |
| 8 | **Database** | "What database does your project use?" | **neo4j** (required) | 1. neo4j, 2. postgresql, 3. mysql, 4. mongodb, 5. other |
| 9 | **Frontend** | "What frontend technology do you use?" | vue/react | 1. vue, 2. react, 3. angular, 4. none |
| 10 | **Other Services** | "Any additional services?" | List only if needed | redis, celery, rabbitmq, none |
| 11 | **Version** | "What version is your project?" | 0.1.0 | 0.1.0, 1.0.0, other |
| 12 | **Visibility** | "Is your project public or private?" | PUBLIC | 1. PUBLIC, 2. PRIVATE |
| 13 | **Status** | "What is the current project status?" | DEVELOPMENT | 1. DEVELOPMENT, 2. STAGING, 3. PRODUCTION |
| 14 | **Main Stack** | "What are the core technologies?" | python,fastapi,neo4j | Comma-separated list |
| 15 | **Tech Stack** | "List all technologies used." | Full list | Comma-separated list |
| 16 | **GitHub Repo** | "What is your GitHub repository URL?" | From git remote | Detected URL or "none" |
| 17 | **Default Branch** | "What is your default git branch?" | main | 1. main, 2. master, 3. develop |
| 18 | **Forbidden Technologies** | "Any technologies to avoid?" | file storage | Comma-separated or "none" |
| 19 | **Required Patterns** | "What architectural patterns to enforce?" | Hexagonal, Repository | Comma-separated |
| 20 | **Naming Conventions** | "What naming conventions do you follow?" | snake_case, PascalCase | 1. snake_case/PascalCase, 2. camelCase, 3. other |
| 21 | **Max Dependency Depth** | "Maximum dependency chain depth?" | 5 | 3, 5, 10, other |
| 22 | **Setup Commands** | "How do you set up the project?" | pip install -e . | Custom or default |
| 23 | **Test Commands** | "How do you run tests?" | pytest tests/ | Custom or default |
| 24 | **Build Commands** | "How do you build the project?" | pip wheel . | Custom or default |
| 25 | **Code Review Approvals** | "Required approvals before merge?" | 1 | 1, 2, 3, other |

---

### Step 4: Present Summary Table

After collecting all 25 fields, the agent presents a summary:

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
│ Tech Stack:          python, fastapi, neo4j, vue        │
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

If the user says **N**, the agent asks which fields to change and goes back to those questions.

If the user says **Y**, proceed to Step 5.

### Step 5: Execute Initialization

The agent runs the command with all collected values:

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

### Step 6: Verify and Report

After initialization:
1. Check that `.agent/` directory was created
2. Verify `project.json` has correct data
3. Verify `project.md` has correct context
4. Report success to user with next steps

---

## Important Rules

1. **ONE question at a time**: Never ask multiple questions in one message.
2. **Always explain**: Tell the user what each field is for.
3. **Always recommend**: Provide a best-practice recommendation.
4. **Always offer options**: Give 2-3 suggested values when applicable.
5. **Accept custom input**: If the user writes their own value, use it.
6. **Detect when possible**: Use `git remote -v`, existing code, etc. to auto-detect values.
7. **Show progress**: Display "Question X of 25" so the user knows where they are.
8. **Allow skipping**: If the user doesn't know, accept "skip" or "default".
9. **Validate input**: Ensure slugs are URL-friendly, versions are semantic, etc.
10. **Confirm before executing**: Always show summary table and get explicit confirmation.

---

## Example Full Conversation

```
Agent: 👋 I see you want to initialize Tasker in your project. I'll help you
       configure it properly. I'll ask you 25 questions one by one to set up
       your project metadata. Let's start!

       📋 **Question 1 of 25: Project Name**
       
       What is the official name of your project?
       
       💡 This will be used in documentation, agent context, and configuration files.
       
       🎯 Recommendation: Use your repository name or a descriptive name.
       
       Detected from git: socialseed-tasker
       
       Your choice (or press Enter to use "socialseed-tasker"):

User: socialseed-tasker

Agent: ✅ Great! Project name set to: "socialseed-tasker"

       📋 **Question 2 of 25: Project Slug**
       
       What is the URL-friendly identifier for your project?
       
       💡 This is used for URLs, directory names, and API endpoints.
       
       🎯 Recommendation: Use lowercase with hyphens, no spaces.
       
       Suggested options:
       1. socialseed-tasker
       2. socialseed_tasker
       3. socialseedtasker
       
       Your choice (type 1-3 or write your own):

User: 1

Agent: ✅ Slug set to: "socialseed-tasker"

       📋 **Question 3 of 25: Description**
       
       Briefly describe what your project does.
       
       💡 This helps agents understand the project scope.
       
       🎯 Recommendation: Keep it concise but informative (1-2 sentences).
       
       Your description:

User: A graph-based task management framework for AI agents

Agent: ✅ Description saved.

       📋 **Question 4 of 25: Repository URL**
       
       What is your Git repository URL?
       
       💡 This links your project to the remote repository.
       
       🎯 Recommendation: Use the URL from git remote.
       
       Detected: https://github.com/daironpf/socialseed-tasker
       
       Your choice (or press Enter to use detected):

User: (enters)

Agent: ✅ Repository URL set.

       📋 **Question 5 of 25: Architecture Type**
       
       What architecture does your project use?
       
       💡 This defines how your code is organized.
       
       🎯 Recommendation: **hexagonal** for clean separation of concerns.
       
       Suggested options:
       1. hexagonal (recommended)
       2. monolithic
       3. microservices
       4. serverless
       5. api-first
       
       Your choice (type 1-5 or write your own):

User: 1

Agent: ✅ Architecture set to: "hexagonal"

... (continues for all 25 questions) ...

Agent: 📋 **All questions completed!** Here's your project configuration:

       [presents summary table]

       Does this look correct? [Y/n]

User: Y

Agent: 🚀 Initializing Tasker in your project...
       [runs tasker init with all parameters]

       ✅ Tasker initialized successfully!
       
       Next steps:
       1. Start Neo4j: docker compose -f .agent/docker-compose.yml up -d
       2. Configure environment: cp .agent/configs/.env.example .agent/configs/.env
       3. Start API: tasker api
       4. Register your agent: tasker agent register --id my-agent --name "My Agent" --role developer
```

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