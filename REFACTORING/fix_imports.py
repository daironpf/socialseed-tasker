"""Fix all imports across the codebase after refactoring #289."""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Exact replacements: (old_import_pattern, new_import_string)
# These are applied in order, as literal string replacements (not regex)
REPLACEMENTS = [
    # === CLI layer ===
    # entrypoints.terminal_cli.commands import shared -> cli.commands import shared
    ("from socialseed_tasker.entrypoints.terminal_cli.commands import",
     "from socialseed_tasker.cli.commands import"),
    ("from socialseed_tasker.entrypoints.terminal_cli.commands.shared",
     "from socialseed_tasker.cli.commands.shared"),
    ("from socialseed_tasker.entrypoints.terminal_cli.commands.",
     "from socialseed_tasker.cli.commands."),
    ("import socialseed_tasker.entrypoints.terminal_cli.commands",
     "import socialseed_tasker.cli.commands"),
    # entrypoints.terminal_cli.formatters -> cli.formatters
    ("from socialseed_tasker.entrypoints.terminal_cli.formatters",
     "from socialseed_tasker.cli.formatters"),
    # entrypoints.terminal_cli.utils -> cli.utils
    ("from socialseed_tasker.entrypoints.terminal_cli.utils",
     "from socialseed_tasker.cli.utils"),
    # entrypoints.terminal_cli.cmd.storage -> cli.cmd_storage
    ("from socialseed_tasker.entrypoints.terminal_cli.cmd.storage",
     "from socialseed_tasker.cli.cmd_storage"),
    # entrypoints.terminal_cli.app -> cli.app
    ("from socialseed_tasker.entrypoints.terminal_cli.app",
     "from socialseed_tasker.cli.app"),
    # entrypoints.terminal_cli (direct import of package)
    ("from socialseed_tasker.entrypoints.terminal_cli import",
     "from socialseed_tasker.cli import"),
    ("import socialseed_tasker.entrypoints.terminal_cli",
     "import socialseed_tasker.cli"),

    # entrypoints.cli.init_command -> cli.init_command
    ("from socialseed_tasker.entrypoints.cli.init_command",
     "from socialseed_tasker.cli.init_command"),
    ("from socialseed_tasker.entrypoints.cli import",
     "from socialseed_tasker.cli import"),

    # === WEB API ===
    ("from socialseed_tasker.entrypoints.web_api import",
     "from socialseed_tasker.infrastructure.web_api import"),
    ("from socialseed_tasker.entrypoints.web_api.routers",
     "from socialseed_tasker.infrastructure.web_api.routers"),
    ("from socialseed_tasker.entrypoints.web_api.",
     "from socialseed_tasker.infrastructure.web_api."),
    ("import socialseed_tasker.entrypoints.web_api",
     "import socialseed_tasker.infrastructure.web_api"),

    # === STORAGE -> INFRASTRUCTURE ===
    # Handle `from X import OLD_NAME` (where only module name changes)
    ("from socialseed_tasker.storage.graph_database.impl",
     "from socialseed_tasker.infrastructure.neo4j_impl"),
    ("from socialseed_tasker.storage.graph_database.migrations",
     "from socialseed_tasker.infrastructure.neo4j_migrations"),
    # Handle `from storage.graph_database import OLD_MODULE` -> module name changed
    ("from socialseed_tasker.storage.graph_database import driver",
     "from socialseed_tasker.infrastructure import neo4j_driver"),
    ("from socialseed_tasker.storage.graph_database import queries",
     "from socialseed_tasker.infrastructure import neo4j_queries"),
    ("from socialseed_tasker.storage.graph_database import repositories",
     "from socialseed_tasker.infrastructure import neo4j_repository"),
    ("from socialseed_tasker.storage.graph_database import code_graph_repository",
     "from socialseed_tasker.infrastructure import neo4j_code_graph_repository"),
    ("from socialseed_tasker.storage.graph_database import commit_repository",
     "from socialseed_tasker.infrastructure import neo4j_commit_repository"),
    ("from socialseed_tasker.storage.graph_database import policy_repository",
     "from socialseed_tasker.infrastructure import neo4j_policy_repository"),
    ("from socialseed_tasker.storage.graph_database import rag_repository",
     "from socialseed_tasker.infrastructure import neo4j_rag_repository"),
    ("from socialseed_tasker.storage.graph_database import reasoning_repository",
     "from socialseed_tasker.infrastructure import neo4j_reasoning_repository"),
    ("from socialseed_tasker.storage.graph_database import user_repository",
     "from socialseed_tasker.infrastructure import neo4j_user_repository"),
    # Handle `from X.OLD_MODULE import Y` -> module name changed
    ("from socialseed_tasker.storage.graph_database.driver",
     "from socialseed_tasker.infrastructure.neo4j_driver"),
    ("from socialseed_tasker.storage.graph_database.queries",
     "from socialseed_tasker.infrastructure.neo4j_queries"),
    ("from socialseed_tasker.storage.graph_database.repositories",
     "from socialseed_tasker.infrastructure.neo4j_repository"),
    ("from socialseed_tasker.storage.graph_database.code_graph_repository",
     "from socialseed_tasker.infrastructure.neo4j_code_graph_repository"),
    ("from socialseed_tasker.storage.graph_database.commit_repository",
     "from socialseed_tasker.infrastructure.neo4j_commit_repository"),
    ("from socialseed_tasker.storage.graph_database.policy_repository",
     "from socialseed_tasker.infrastructure.neo4j_policy_repository"),
    ("from socialseed_tasker.storage.graph_database.rag_repository",
     "from socialseed_tasker.infrastructure.neo4j_rag_repository"),
    ("from socialseed_tasker.storage.graph_database.reasoning_repository",
     "from socialseed_tasker.infrastructure.neo4j_reasoning_repository"),
    ("from socialseed_tasker.storage.graph_database.user_repository",
     "from socialseed_tasker.infrastructure.neo4j_user_repository"),
    # Handle `import X.OLD_MODULE` -> module name changed
    ("import socialseed_tasker.storage.graph_database.driver",
     "import socialseed_tasker.infrastructure.neo4j_driver"),
    ("import socialseed_tasker.storage.graph_database.queries",
     "import socialseed_tasker.infrastructure.neo4j_queries"),
    ("import socialseed_tasker.storage.graph_database.repositories",
     "import socialseed_tasker.infrastructure.neo4j_repository"),
    ("import socialseed_tasker.storage.graph_database.code_graph_repository",
     "import socialseed_tasker.infrastructure.neo4j_code_graph_repository"),
    ("import socialseed_tasker.storage.graph_database.commit_repository",
     "import socialseed_tasker.infrastructure.neo4j_commit_repository"),
    ("import socialseed_tasker.storage.graph_database.policy_repository",
     "import socialseed_tasker.infrastructure.neo4j_policy_repository"),
    ("import socialseed_tasker.storage.graph_database.rag_repository",
     "import socialseed_tasker.infrastructure.neo4j_rag_repository"),
    ("import socialseed_tasker.storage.graph_database.reasoning_repository",
     "import socialseed_tasker.infrastructure.neo4j_reasoning_repository"),
    ("import socialseed_tasker.storage.graph_database.user_repository",
     "import socialseed_tasker.infrastructure.neo4j_user_repository"),
    # broad storage.graph_database (this catches remaining `from X.graph_database import Y` where Y is NOT renamed)
    ("from socialseed_tasker.storage.graph_database",
     "from socialseed_tasker.infrastructure"),
    ("import socialseed_tasker.storage.graph_database",
     "import socialseed_tasker.infrastructure"),
    # storage.adapters.github -> infrastructure.github_adapter
    ("from socialseed_tasker.storage.adapters.github",
     "from socialseed_tasker.infrastructure.github_adapter"),
    ("import socialseed_tasker.storage.adapters.github",
     "import socialseed_tasker.infrastructure.github_adapter"),
    # broad storage
    ("from socialseed_tasker.storage",
     "from socialseed_tasker.infrastructure"),
    ("import socialseed_tasker.storage",
     "import socialseed_tasker.infrastructure"),

    # === CORE -> INFRASTRUCTURE ===
    # core.code_analysis.parser -> infrastructure.code_parser
    ("from socialseed_tasker.core.code_analysis.parser",
     "from socialseed_tasker.infrastructure.code_parser"),
    ("import socialseed_tasker.core.code_analysis.parser",
     "import socialseed_tasker.infrastructure.code_parser"),
    # core.code_analysis import
    ("from socialseed_tasker.core.code_analysis",
     "from socialseed_tasker.infrastructure"),
    # core.services -> infrastructure
    ("from socialseed_tasker.core.services",
     "from socialseed_tasker.infrastructure"),
    ("import socialseed_tasker.core.services",
     "import socialseed_tasker.infrastructure"),

    # === CORE -> APPLICATION ===
    ("from socialseed_tasker.core.project_analysis",
     "from socialseed_tasker.application"),
    ("from socialseed_tasker.core.task_management",
     "from socialseed_tasker.application"),
    ("from socialseed_tasker.core.system_init",
     "from socialseed_tasker.application"),

    # === CORE -> DOMAIN ===
    ("from socialseed_tasker.core.validation",
     "from socialseed_tasker.domain"),

    # === BOOTSTRAP -> APPLICATION ===
    ("from socialseed_tasker.bootstrap",
     "from socialseed_tasker.application"),
    ("import socialseed_tasker.bootstrap",
     "import socialseed_tasker.application"),

    # === CORE root (catch remaining core.* after more specific rules) ===
    ("from socialseed_tasker.core.",
     "from socialseed_tasker.infrastructure."),
]


def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    for old, new in REPLACEMENTS:
        content = content.replace(old, new)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def is_python_file(path):
    return path.endswith('.py') and '__pycache__' not in path


def main():
    search_dirs = [
        os.path.join(REPO_ROOT, 'src'),
        os.path.join(REPO_ROOT, 'tests'),
    ]

    fixed_files = []
    errors = []
    for search_dir in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                if is_python_file(f):
                    filepath = os.path.join(root, f)
                    try:
                        if fix_file(filepath):
                            fixed_files.append(os.path.relpath(filepath, REPO_ROOT))
                    except Exception as e:
                        errors.append((os.path.relpath(filepath, REPO_ROOT), str(e)))

    print(f"Fixed {len(fixed_files)} files:")
    for f in sorted(fixed_files):
        print(f"  {f}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for f, e in errors:
            print(f"  {f}: {e}")
    print(f"\nDone! {len(fixed_files)} files updated.")


if __name__ == '__main__':
    main()
