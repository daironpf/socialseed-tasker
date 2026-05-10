# Graph Data Model Details: Tasker

## 1. Executive Summary & Vision
**Tasker** is designed as a "Control Plane" for AI-native software engineering. Unlike traditional task managers that store data in isolated tables, Tasker uses a **Property Graph Model (Neo4j)** to unify three distinct domains into a single technical memory:
1.  **Management Layer:** Issues, tasks, and project milestones.
2.  **Engineering Layer:** Code structure, symbols, and architectural components.
3.  **Reasoning Layer:** AI Agent thoughts, decisions, and RAG (Retrieval-Augmented Generation) embeddings.

The goal of this model is to provide **Causal Traceability**. When a task is completed, the graph doesn't just show that it's "Done"; it shows exactly which `CodeSymbols` were modified, which `Agent` made the decision, and what `ReasoningNodes` led to that outcome.

## 2. Core Taxonomy (Node Categories)
The graph is organized into four main pillars. Every node in the system must belong to one of these functional groups:

### A. The Organizational Pillar
*   **`Project`**: The root anchor of the graph. It serves as the namespace for all other entities.
*   **`Issue` / `Task`**: Atomic units of work. These represent "intent" before it becomes code.
*   **`Component`**: High-level architectural blocks (e.g., a Microservice or a Frontend Module).

### B. The Code-as-Graph Pillar
*   **`CodeFile`**: Physical files in the repository.
*   **`CodeSymbol`**: Granular code elements like Classes, Methods, or Interfaces. This allows the AI to "see" the code structure without reading the whole file.
*   **`CodeImport`**: Represents the dependency tree between different parts of the system.

### C. The Intelligence Pillar
*   **`Agent`**: The digital entities performing the work.
*   **`ReasoningNode`**: A trace of the LLM's thought process (Chain-of-Thought).
*   **`RAGEmbedding`**: Vector representations stored as node properties to enable semantic search within the graph.

### D. The Governance Pillar
*   **`Label` / `Tag`**: Metadata used for filtering and organization.
*   **`Policy`**: Governance constraints that agents must follow (e.g., "Do not use Library X").

***

This is the comprehensive technical documentation for the **SocialSeed - Tasker v1.0** Data Model, fully updated to include all properties, nodes, and relationships from the finalized graph schema.

---

## Node: Project (n1)
The **Project** node is the root entity of the graph. It defines the global context for a repository, encompassing technical configurations, governance rules for AI agents, and the operational status of the software development lifecycle.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Universal unique identifier for the project. |
| `name` | String | Official name of the project. |
| `slug` | String | URL-friendly identifier and directory name (e.g., `socialseed-tasker`). |
| `description` | String | Detailed description of the project's scope and purpose. |
| `repositoryUrl` | String | Link to the remote Git repository. |
| `basePackage` | String | The root package or primary namespace of the source code. |
| `visibility` | Enum | Project visibility level (e.g., `PUBLIC`, `PRIVATE`). |
| `status` | Enum | Current project lifecycle state. |
| `techStack` | List[String] | Complete list of all integrated technologies. |
| `mainStack` | List[String] | Core technologies: `['Spring Boot', 'Neo4j', 'Python']`. |
| `architectureStyle`| String | Architectural pattern followed (e.g., `Microservices`). |
| `version` | String | Current semantic version of the project. |
| `conventionsUrl` | String | Reference to external coding standards documentation. |
| `conventionsRules` | JSON/String | Specific rules and guidelines for AI agents to validate and follow. |
| `lastFullScan` | DateTime | Timestamp of the last complete repository analysis. |
| `globalStatus` | Enum | Operational status: `[DEVELOPMENT, STAGING, PRODUCTION]`. |
| `createdAt` | DateTime | Timestamp when the project node was created. |
| `updatedAt` | DateTime | Timestamp of the last project metadata update. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (p:Project) REQUIRE p.id IS UNIQUE;`
* `CREATE CONSTRAINT FOR (p:Project) REQUIRE p.slug IS UNIQUE;`

---

**Relationships:**
* **(Project)-[:HAS_COMPONENT]->(Component):** Breaks the project down into functional modules or units.
* **(Project)-[:HAS_ISSUE]->(Issue):** Links all requirements, tasks, and bugs to the project context.
* **(Project)-[:ASSIGNED_TO]->(Agent):** Defines which AI agents are authorized to operate on this project.
* **(Project)-[:DEFINES_CONTEXT]->(RAGEmbedding):** Provides the specific semantic knowledge base for this repository.
* **(User)-[:MANAGES]->(Project):** Establishes human ownership and administrative authority.
---


## Node: Component (n2)
The **Component** node represents a logical module, service, or architectural unit within the project. It serves as a middle-layer organization tool that groups related code files and issues, allowing AI agents to understand the boundaries and responsibilities of different parts of the system.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the component. |
| `name` | String | The functional name of the module (e.g., `auth-service`, `gateway`, `database-layer`). |
| `description` | String | A high-level description of the component’s responsibility and scope. |
| `createdAt` | DateTime | Timestamp of when the component was first registered in the graph. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (c:Component) REQUIRE c.id IS UNIQUE;`
* `CREATE INDEX FOR (c:Component) ON (c.name);`

---

**Relationships:**
* **(Project)-[:HAS_COMPONENT]->(Component):** Defines which architectural units belong to the specific project.
* **(Issue)-[:PART_OF]->(Component):** Maps tasks or bugs to the specific module they affect, aiding in impact analysis.
* **(Agent)-[:SPECIALIST_IN]->(Component):** Designates an AI Agent as an expert in a particular module, ensuring it is prioritized for related tasks.
* **(Component)-[:CATEGORIZED_BY]->(Label):** Applies semantic tags to the component for easier filtering and domain grouping.
* **(CodeFile)-[:BELONGS_TO]->(Component):** (Optional/Implicit) Connects physical source files to their logical architectural parent.

### Implementation Note:
By using the **Component** node, **SocialSeed - Tasker** can implement "Domain-Driven Dispatching." When a new **Issue** is created, the system identifies which **Component** it belongs to and automatically assigns it to the **Agent** that has the `SPECIALIST_IN` relationship with that specific module.

---

## Node: Agent (n3)
The **Agent** node represents an autonomous AI entity within the system. Each agent is characterized by a specific role, set of technical capabilities, and domain expertise. Agents interact with the graph by processing issues, generating reasoning paths, and committing code changes.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the agent instance. |
| `name` | String | The display name or identifier of the AI agent (e.g., "Architect-Agent-01"). |
| `role` | Enum | The agent's specialized function (e.g., `DEVELOPER`, `TESTER`, `ARCHITECT`). |
| `status` | Enum | Current operational state (e.g., `IDLE`, `BUSY`, `OFFLINE`). |
| `capabilities` | List[String] | A list of tools or technical skills the agent is authorized to use (e.g., `git-write`, `neo4j-query`, `unit-testing`). |
| `createdAt` | DateTime | Timestamp when the agent was registered in the system. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (a:Agent) REQUIRE a.id IS UNIQUE;`
* `CREATE INDEX FOR (a:Agent) ON (a.role);`

---

**Relationships:**
* **(Project)-[:ASSIGNED_TO]->(Agent):** Defines the scope of the agent's work, granting it permission to operate within a specific project.
* **(Agent)-[:SPECIALIST_IN]->(Component):** Indicates high proficiency in a specific module, prioritizing the agent for tasks related to that component.
* **(Agent)-[:INTERESTED_IN]->(Label):** A semantic filter that guides the agent toward issues or tasks tagged with specific domains.
* **(Agent)-[:PRODUCED]->(ReasoningNode):** Links the agent to its cognitive output and the logic behind its decisions.
* **(Agent)-[:AUTHORED]->(Commit):** Records the agent as the creator of physical code changes, ensuring total traceability.

### Implementation Note:
In the **v1.0.0** release, the `capabilities` property is used to enforce security boundaries. For instance, a `TESTER` agent might have `read` access to the entire repository but `write` access only to the `src/test` directory. This ensures that autonomous actions remain within the architectural governance established by the Human-in-the-Loop.

---

## Node: User (n4)
The **User** node represents the human architect, lead developer, or project owner. It is the primary entity for tracking responsibility, providing manual oversight for AI-generated decisions, and managing administrative project control. This node ensures that the "Human-in-the-Loop" (HITL) principle is enforced throughout the development lifecycle.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the human user. |
| `username` | String | Display name or alias for the user. |
| `email` | String | Primary email address for notifications and Git authorship mapping. |
| `role` | Enum | The user's authority level (e.g., `ADMIN`, `LEAD_ARCHITECT`, `DEVELOPER`). |
| `githubHandle` | String | Linked GitHub username to synchronize authorship across the graph and repository. |
| `createdAt` | DateTime | Timestamp when the user profile was initially created. |
| `lastLogin` | DateTime | Audit field recording the most recent system access. |
| `preferences` | JSON/String | Configuration for UI themes, notification thresholds, and agent interaction settings. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (u:User) REQUIRE u.id IS UNIQUE;`
* `CREATE CONSTRAINT FOR (u:User) REQUIRE u.email IS UNIQUE;`
* `CREATE CONSTRAINT FOR (u:User) REQUIRE u.username IS UNIQUE;`

---

**Relationships:**
* **(User)-[:VALIDATES {approved: Boolean, comment: String}]->(ReasoningNode):** The critical governance link where the human reviews and authorizes or rejects an AI agent's logic.
* **(User)-[:MANAGES]->(Project):** Defines administrative ownership and control over specific project instances.
* **(User)-[:ASSIGNED_TO]->(Issue):** Tracks tasks that are specifically delegated to the human developer.
* **(User)-[:AUTHORED]->(Commit):** Attributes code changes to the human user, maintaining a clear distinction between human and AI contributions.

---

## Node: Issue (n5)
The **Issue** node acts as the bridge between business requirements and technical execution. It encapsulates bugs, feature requests, or refactoring tasks. In this graph-native approach, an Issue is not just a static ticket but a dynamic entity connected to the code symbols it affects and the agents assigned to solve it.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Universal unique identifier for the task. |
| `title` | String | A concise summary of the requirement or problem. |
| `description` | String | A detailed breakdown of the task, including steps to reproduce or acceptance criteria. |
| `status` | Enum | The current stage in the workflow (e.g., `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`). |
| `priority` | Enum | Relative urgency of the task (e.g., `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| `createdAt` | DateTime | Timestamp of when the issue was first indexed. |
| `updatedAt` | DateTime | Timestamp of the most recent modification to the issue metadata. |
| `closedAt` | DateTime | Timestamp recording exactly when the issue reached a terminal state. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (i:Issue) REQUIRE i.id IS UNIQUE;`
* `CREATE INDEX FOR (i:Issue) ON (i.status);`

---

**Relationships:**
* **(Project)-[:HAS_ISSUE]->(Issue):** Establishes the project scope to which the task belongs.
* **(Issue)-[:PART_OF]->(Component):** Pins the issue to a specific architectural module for better impact analysis.
* **(Issue)-[:AFFECTS]->(CodeSymbol):** A high-granularity link identifying exactly which classes or methods are involved in the task.
* **(Issue)-[:HAS_LABEL]->(Label):** Categorizes the issue for automated routing to specialized agents.
* **(Issue)-[:RESOLVED_BY]->(Commit):** Provides a direct link to the physical code changes that satisfied the requirement.
* **(ReasoningNode)-[:PROPOSES_FIX_FOR]->(Issue):** Connects the AI's logical solution to the problem description.
* **(User/Agent)-[:ASSIGNED_TO]->(Issue):** Defines the entity (human or AI) responsible for moving the task to completion.

### Implementation Note:
The relationship `(Issue)-[:AFFECTS]->(CodeSymbol)` is what makes your system "AI-Native." By knowing exactly which code symbols are affected before the agent starts working, the system can provide the LLM with a highly targeted RAG context, reducing token usage and increasing the accuracy of the proposed fix.

---

## Node: CodeFile (n6)
The **CodeFile** node represents a physical source file within the project's repository. It acts as the structural bridge between the version control system (Git) and the logical code analysis (Symbols). It tracks the file's physical location, its content integrity via hashing, and its current state within the development lifecycle.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the file instance. |
| `name` | String | Filename including the extension (e.g., `main.py`, `UserController.java`). |
| `path` | String | The full system path of the file within the repository structure. |
| `language` | String | The programming language of the file (e.g., `Python`, `Java`, `TypeScript`). |
| `linesOfCode` | Integer | Total count of lines in the file, used for complexity and size metrics. |
| `fileHash` | String | A unique SHA-256 hash of the file's content to detect unauthorized or external changes. |
| `repositoryPath` | String | The relative path from the repository root, used for Git operations. |
| `commitSha` | String | The SHA of the most recent commit that modified this specific file. |
| `scannedAt` | DateTime | Timestamp of the last time the file was parsed and its symbols updated. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (f:CodeFile) REQUIRE f.id IS UNIQUE;`
* `CREATE INDEX FOR (f:CodeFile) ON (f.path);`
* `CREATE INDEX FOR (f:CodeFile) ON (f.name);`

---

**Relationships:**
* **(CodeFile)-[:CONTAINS]->(CodeSymbol):** Links the physical file to the classes and methods defined within it.
* **(CodeFile)-[:IMPORTS]->(CodeImport):** Tracks the dependencies declared at the top of the file.
* **(CodeImport)-[:RESOLVES_TO]->(CodeFile):** Points to the specific destination file where an imported module is defined.
* **(Commit)-[:MODIFIED {type: "Enum"}]->(CodeFile):** Connects version history to the file, specifying if it was `ADDED`, `MODIFIED`, or `DELETED`.

### Implementation Note:
The `fileHash` property is a critical security and sync feature for **SocialSeed - Tasker**. Before an AI Agent begins a task, the system compares the current `fileHash` on disk with the one stored in Neo4j. If they do not match, a "Re-scan" is triggered to ensure the Agent is not working with an outdated architectural mental model.

---

## Node: CodeSymbol (n7)
The **CodeSymbol** node represents a specific functional element within a source file, such as a Class or a Method. It allows the **SocialSeed - Tasker** engine to perform high-precision analysis, mapping issues and reasoning directly to specific blocks of logic rather than just entire files.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the code symbol. |
| `name` | String | The name of the symbol (e.g., `UserService`, `calculateTotal`). |
| `symbolType` | Enum | Categorization of the symbol: `[Class, Method]`. |
| `startLine` | Integer | The line number where the symbol definition begins. |
| `endLine` | Integer | The line number where the symbol definition ends. |
| `startColumn` | Integer | The starting character column of the symbol. |
| `endColumn` | Integer | The ending character column of the symbol. |
| `parameters` | List[String] | A list of input parameters (for Methods). |
| `returnType` | String | The data type returned by the method. |
| `decorators` | List[String] | Applied annotations or decorators (e.g., `@Override`, `@Transactional`). |
| `isTest` | Boolean | Flag identifying if this symbol is a test case or test class. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (s:CodeSymbol) REQUIRE s.id IS UNIQUE;`
* `CREATE INDEX FOR (s:CodeSymbol) ON (s.name);`

---

**Relationships:**
* **(CodeFile)-[:CONTAINS]->(CodeSymbol):** Establishes the physical location of the symbol within the file system.
* **(CodeSymbol)-[:CHILD_OF]->(CodeSymbol):** Represents nesting, such as a method belonging to a class.
* **(CodeSymbol)-[:CALLS]->(CodeSymbol):** Maps the execution flow and internal dependencies between different parts of the code.
* **(Issue)-[:AFFECTS]->(CodeSymbol):** Pins a task or bug to the specific logic block that requires modification.

### Implementation Note:
The `(CodeSymbol)-[:CALLS]->(CodeSymbol)` relationship is vital for **Impact Analysis**. If an agent modifies a method, the graph allows the system to instantly identify every other method that depends on it, automatically generating a list of "Risk Areas" that need to be re-tested by the **socialseed-e2e** framework.

---

## Node: CodeImport (n8)
The **CodeImport** node represents a dependency declaration within a source file. It maps how one file references another module, class, or function. By modeling imports as discrete nodes, the system can perform complex "impact analysis," tracing how a change in a low-level utility might ripple through the entire architecture.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the import entry. |
| `fileId` | UUID | The ID of the **CodeFile** (parent) where this import statement is written. |
| `moduleName` | String | The full name of the imported module (e.g., `org.springframework.stereotype`, `os.path`). |
| `names` | List[String] | Specific items imported (e.g., `['Service', 'Component']` or `['path']`). |
| `lineNumber` | Integer | The specific line in the source file where the import is defined. |
| `isFrom` | Boolean | True if the syntax used was `from module import name` (specific to Python). |
| `isExternal` | Boolean | Flag identifying if the import is a third-party library or an internal project file. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (ci:CodeImport) REQUIRE ci.id IS UNIQUE;`
* `CREATE INDEX FOR (ci:CodeImport) ON (ci.module_name);`

---

**Relationships:**
* **(CodeFile)-[:IMPORTS]->(CodeImport):** Connects the source file to its dependency requirements.
* **(CodeImport)-[:RESOLVES_TO]->(CodeFile):** Points to the specific **CodeFile** node where the imported logic is physically located (for internal project files).

### Implementation Note:
The `isExternal` property is vital for filtering the agent's focus. When an agent is tasked with refactoring, the system uses this flag to prevent the agent from attempting to "jump" into the source code of external libraries (like Spring Boot or NumPy), keeping the RAG context strictly focused on the user's project codebase.

---

## Node: Commit (n9)
The **Commit** node represents a physical change in the repository's version control history. It acts as the ultimate proof of work, linking the high-level reasoning of an agent to the low-level modifications of the source code. By tracking additions, deletions, and authorship, it provides a full audit trail for system governance.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `sha` | String | The unique Git commit hash (Primary identifier). |
| `message` | String | The commit message describing the changes. |
| `authorName` | String | The name of the individual or agent who created the commit. |
| `authorEmail` | String | The email address associated with the author. |
| `timestamp` | DateTime | The exact date and time the commit was created. |
| `isAiGenerated` | Boolean | Flag indicating if the commit was produced by an AI Agent. |
| `branch` | String | The branch name where the commit was pushed (e.g., `main`, `feature/task-1`). |
| `additions` | Integer | Total number of lines added in this commit. |
| `deletions` | Integer | Total number of lines removed in this commit. |
| `filesChanged` | Integer | The total number of files impacted by this specific change. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (c:Commit) REQUIRE c.sha IS UNIQUE;`
* `CREATE INDEX FOR (c:Commit) ON (c.timestamp);`

---

**Relationships:**
* **(Agent)-[:AUTHORED]->(Commit):** Attributes the change to a specific AI Agent for accountability.
* **(User)-[:AUTHORED]->(Commit):** Attributes the change to a human user.
* **(Commit)-[:MODIFIED {type: "Enum"}]->(CodeFile):** Connects the commit to the files it changed, labeled as `ADDED`, `MODIFIED`, or `DELETED`.
* **(Commit)-[:PARENT_OF]->(Commit):** Models the chronological and branching history of the Git tree.
* **(ReasoningNode)-[:RESULTED_IN]->(Commit):** Provides the "Why" behind the "What," linking the code change to the AI's logical process.
* **(Issue)-[:RESOLVED_BY]->(Commit):** Indicates which specific code change satisfied the requirement of a given issue.

### Implementation Note:
The `isAiGenerated` flag is essential for the **SocialSeed** governance model. It allows you to generate reports on "AI Productivity vs. Human Oversight" and ensures that every change made by an agent can be traced back through a **ReasoningNode** to a specific **User** validation.

---

## Node: ReasoningNode (n10)
The **ReasoningNode** stores the internal logic, justifications, and decision-making processes of an AI Agent. Unlike traditional logs, this is a first-class citizen in the graph, allowing humans to audit **why** a specific code change was proposed and ensuring that every autonomous action is backed by a traceable thought process.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the reasoning instance. |
| `thought` | String | A detailed natural language explanation of the logic, strategy, or analysis. |
| `confidence` | Float | A numerical score (0.0 to 1.0) representing the agent's certainty in its decision. |
| `decisionType` | Enum | The category of the proposed action (e.g., `BUG_FIX`, `REFACTOR`, `FEATURE`). |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (r:ReasoningNode) REQUIRE r.id IS UNIQUE;`

---

**Relationships:**
* **(Agent)-[:PRODUCED]->(ReasoningNode):** Connects the thought process to the specific AI entity that generated it.
* **(ReasoningNode)-[:PROPOSES_FIX_FOR]->(Issue):** Links the logical solution to the original problem or requirement.
* **(ReasoningNode)-[:RESULTED_IN]->(Commit):** Provides a direct link between the validated thought and the physical code implementation.
* **(ReasoningNode)-[:SUGGESTS]->(Label):** Allows the AI to propose semantic tags for the task based on its findings.
* **(User)-[:VALIDATES {approved: Boolean, comment: String}]->(ReasoningNode):** The "Human-in-the-Loop" link, where you provide feedback or authorization for the AI to proceed.

### Implementation Note:
The **ReasoningNode** is essential for maintaining the integrity of the **SocialSeed** ecosystem. By requiring a `VALIDATES` relationship from a **User** node for critical `decisionType` values (like `REFACTOR`), you can prevent the AI from making unauthorized structural changes to the project while still allowing it to operate autonomously on lower-risk tasks.

---

## Node: RAGEmbedding (n11)
This node stores the vectorized representations of project assets, such as code snippets, documentation, or architectural decisions. It enables agents to perform high-speed semantic retrieval, allowing them to "remember" relevant context that isn't directly linked through traditional graph relationships.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the embedding entry. |
| `content` | String | The raw text or code block that was vectorized. |
| `embedding` | List[Float] | The high-dimensional vector representation (e.g., 1536 dimensions). |
| `sourceType` | Enum | The origin of the data: `[CODE_SNIPPET, DOCUMENTATION, ARCH_DECISION]`. |
| `modelInfo` | String | Metadata about the embedding model used (e.g., `text-embedding-3-small`). |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (re:RAGEmbedding) REQUIRE re.id IS UNIQUE;`
* `CREATE VECTOR INDEX rag_content_index FOR (re:RAGEmbedding) ON (re.embedding);`

---

**Relationships:**
* **(Project)-[:DEFINES_CONTEXT]->(RAGEmbedding):** Ensures that the vector search is scoped specifically to the current project's knowledge base.
* **(CodeSymbol)-[:HAS_VECTOR]->(RAGEmbedding):** (Optional) Directly links a specific class or method to its semantic vector for faster lookup during specialized code analysis.

---

### Implementation Note:
For the **SocialSeed - Tasker** backend, it is recommended to use the `sourceType` property as a pre-filter in your Cypher queries. This allows an agent to specify if it needs "Architectural Context" (searching only `ARCH_DECISION`) or "Implementation Examples" (searching `CODE_SNIPPET`), significantly improving the relevance of the retrieved context and reducing LLM hallucinations.

---

## Node: Label (n12)
The **Label** node provides a flexible, many-to-many tagging system. It is used to categorize **Issues**, **Components**, and **ReasoningNodes**, enabling the system to route tasks to specific agents and allowing users to filter the project state based on priorities, domains, or risk levels.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the label entry. |
| `name` | String | The unique display name of the tag (e.g., `bug`, `refactor`, `security`, `ui`). |
| `color` | String | Hexadecimal color code for visual identification in the UI. |
| `description` | String | A brief explanation of the label's purpose and usage criteria. |
| `createdAt` | DateTime | Timestamp of when the label was first registered in the system. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (l:Label) REQUIRE l.id IS UNIQUE;`
* `CREATE CONSTRAINT FOR (l:Label) REQUIRE l.name IS UNIQUE;`

---

**Relationships:**
* **(Issue)-[:HAS_LABEL]->(Label):** Categorizes tasks for automated routing and reporting.
* **(Component)-[:CATEGORIZED_BY]->(Label):** Groups architectural modules under specific technical domains or business areas.
* **(Agent)-[:INTERESTED_IN]->(Label):** Defines the agent's subscription to specific types of work, acting as a primary filter for the task dispatcher.
* **(ReasoningNode)-[:SUGGESTS]->(Label):** Allows an AI Agent to propose new categorizations for a task based on its analysis.

---

## Node: Policy (n13)
The **Policy** node represents a set of architectural rules, coding standards, or security constraints that the system must enforce. It serves as the "Law" of the repository, which Agents must consult during their reasoning phase to ensure that proposed changes do not violate project integrity.

| Property | Data Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique identifier for the policy. |
| `name` | String | Short name of the rule (e.g., `NO_CIRCULAR_DEPENDENCIES`, `MAX_METHOD_LENGTH`). |
| `description` | String | A clear explanation of the rule for the AI Agent to interpret. |
| `severity` | Enum | The impact of a violation: `[INFO, WARNING, BLOCKER]`. |
| `targetScope` | Enum | What the policy applies to: `[CODE_SYMBOL, COMPONENT, COMMIT, PROJECT]`. |
| `logicDefinition` | JSON/String | The technical parameters or regex used to programmatically validate the rule. |
| `remediationStrategy`| String | Instructions for the Agent on how to resolve a violation (e.g., "Refactor to use Utility X"). |
| `autofixTemplate`| String | A code template or command that can be used to automatically correct the violation. |
| `isActive` | Boolean | Flag to enable or disable the policy enforcement. |
| `createdAt` | DateTime | Timestamp of when the policy was established. |

---

**Constraints:**
* `CREATE CONSTRAINT FOR (p:Policy) REQUIRE p.id IS UNIQUE;`
* `CREATE CONSTRAINT FOR (p:Policy) REQUIRE p.name IS UNIQUE;`

---

**Relationships:**
* **(Project)-[:ENFORCES]->(Policy):** Links a global or specific rule to the project context.
* **(Agent)-[:MUST_COMPLY_WITH]->(Policy):** A governance link that mandates the agent to check this node during its reasoning process.
* **(ReasoningNode)-[:VALIDATED_AGAINST]->(Policy):** Records that the agent explicitly checked its proposed solution against this rule.
* **(Commit)-[:VIOLATES]->(Policy):** (Audit) Used if a change is pushed that breaks a `WARNING` or `INFO` level policy.
* **(Policy)-[:APPLIES_TO]->(Component):** Allows for granular rules that only apply to specific modules (e.g., stricter security policies for an `auth-service`).

---

### Implementation Note:
The **Policy** node is the key to achieving "Autonomous Quality Assurance." By including this in the graph, you can instruct your agents to perform a **Pre-Commit Audit**:
1. Agent generates a `ReasoningNode`.
2. Agent queries the graph for all `Policy` nodes linked to the `Project`.
3. Agent evaluates its `thought` and `proposed_code` against these policies.
4. If a `BLOCKER` is found, the Agent uses the `remediationStrategy` to self-correct.
5. If an `autofixTemplate` exists, the Agent can apply it directly before presenting the `ReasoningNode` to the **User** for validation.

This ensures that the Human-in-the-Loop only spends time on architectural decisions, not on fixing linting or convention errors.

---

## 3. Intelligence Queries (Cypher Examples)

### A. Impact Analysis
"If I change this Method, what else do I need to test?"
```cypher
MATCH (s:CodeSymbol {name: 'calculateTotal'})<-[:CALLS*1..3]-(dependent)
RETURN dependent.name, dependent.symbolType
```

### B. Traceability Audit
"Why was this specific line of code changed?"
```cypher
MATCH (c:Commit {sha: 'a1b2c3d'})<-[:RESULTED_IN]-(r:ReasoningNode)<-[:PRODUCED]-(a:Agent)
MATCH (r)-[:PROPOSES_FIX_FOR]->(i:Issue)
RETURN a.name as Agent, r.thought as Reasoning, i.title as Requirement
```

### C. Governance Check
"Are there any components violating active policies?"
```cypher
MATCH (comp:Component)<-[:APPLIES_TO]-(p:Policy {severity: 'BLOCKER'})
MATCH (comp)<-[:PART_OF]-(i:Issue)-[:RESOLVED_BY]->(c:Commit)-[:VIOLATES]->(p)
RETURN comp.name, p.name, c.sha
```
