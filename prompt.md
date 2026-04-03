# AI System Instruction: "The Seeder" – Injected Tasker Infrastructure

## **1. The Objective**
Transform `socialseed-tasker` into an **injected management layer**. When a user is inside a separate project (Project XX), they should be able to create a `tasker/` directory, install our package, and run a command that "seeds" the environment with pre-configured **AI Skills** and **Docker Infrastructure**.

## **2. Functional Requirements: The "ss-tasker init" Flow**
You must implement a bootstrapping command (`init`) with the following logic:
- **Directory Detection:** Identify the current working directory.
- **Scaffolding:** Create a structure inside the user's project:
  ```text
  Project-XX/
  └── tasker/
      ├── skills/         # Injected AI Agent Skills (Python/JSON)
      ├── configs/        # Local configuration
      └── docker-compose.yml
  ```
- **Asset Migration:** Copy a set of "Template Skills" from the `socialseed_tasker/assets` directory (inside the library) to the user's local `tasker/skills/` folder.
- **Skill Overwriting:** If the skills already exist, provide a `--force` flag to update them with the latest versions from the library.

## **3. Architectural Implementation (Hexagonal-Feature Style)**
Maintain the existing hexagonal structure while adding these new components:

### **A. Entrypoints (Input)**
- **`src/socialseed_tasker/entrypoints/cli/init_command.py`**:
  - Use `typer` to handle the `init` command.
  - Implement a `ScaffolderService` that handles the physical file copying.

### **B. Assets (The Templates)**
- Create a directory **`src/socialseed_tasker/assets/templates/skills/`**.
- Inside, place a generic `task_skill.py` that acts as a **Function Calling** bridge between an external AI Agent and the Tasker REST API.

### **C. Storage (Output Adaptability)**
- **Hybrid Connection Logic:** Update the `graph_database` adapter to support **Neo4j Aura DB**.
- The `docker-compose.yml` generated during `init` should support an `.env` file that toggles between:
  - `MODE=LOCAL`: Connects to the local Docker container.
  - `MODE=AURA`: Connects to a remote Neo4j Aura instance via `bolt+s://` protocol.

## **4. The "AI Skill" Architecture**
The injected skills in `Project-XX/tasker/skills/` must be **API-Centric**. They should not import the Tasker Core. Instead, they should:
1. Identify the Tasker API endpoint (defaulting to `http://localhost:8000`).
2. Provide standardized functions (e.g., `create_issue`, `get_architecture_graph`) that the AI Agent in Project XX can "import" and use immediately.

## **5. Packaging Constraints (PyPI Readiness)**
- Update `pyproject.toml` to include all files in `src/socialseed_tasker/assets/` in the build distribution (`include-package-data = true`).
- Ensure the `ss-tasker` CLI command is correctly mapped to the new `init` logic.

## **Initial Task Sequence:**
1. **Create the Asset System:** Design the `assets/` directory and create the initial `docker-compose.yml` and `skill_template.py` files.
2. **Implement the Scaffolder Service:** Write the Python logic in `core/system_init/` that handles file system operations.
3. **Build the CLI command:** Connect the `ss-tasker init` command to the Scaffolder.
4. **Update README:** Add an "Injected Setup" section in English explaining how Project XX users can adopt the Tasker.

**Strict Rule:** All generated code must be documented in English and maintain the "Feature-Oriented" folder naming convention we established. Do not use generic names like "helpers" or "utils".