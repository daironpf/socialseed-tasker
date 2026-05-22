"""CLI commands package exposing all Typer apps and command functions."""

from socialseed_tasker.cli.commands.status_commands import status_app
from socialseed_tasker.cli.commands.project_commands import project_app
from socialseed_tasker.cli.commands.issue_commands import issue_app
from socialseed_tasker.cli.commands.dependency_commands import dependency_app
from socialseed_tasker.cli.commands.component_commands import component_app
from socialseed_tasker.cli.commands.analysis_commands import analyze_app
from socialseed_tasker.cli.commands.seed_commands import seed_app
from socialseed_tasker.cli.commands.constraints_commands import constraints_app
from socialseed_tasker.cli.commands.code_graph_commands import code_graph_app
from socialseed_tasker.cli.commands.rag_commands import rag_app
from socialseed_tasker.cli.commands.reasoning_commands import reasoning_app
from socialseed_tasker.cli.commands.agent_commands import agent_app

from socialseed_tasker.cli.commands.shared import (
    _CLI_CONFIG_FILE,
    _components_table,
    _dependency_tree,
    _format_issue_card,
    _get_password_with_fallback,
    _issues_table,
    _load_saved_credentials,
    _priority_style,
    _save_credentials,
    _status_style,
    console,
    get_repository,
    resolve_component_id,
    resolve_issue_id,
)

from socialseed_tasker.cli.commands.status_commands import (
    login_command,
    logout_command,
    status_command,
)

from socialseed_tasker.cli.commands.project_commands import (
    project_detect,
    project_setup,
)

from socialseed_tasker.cli.commands.issue_commands import (
    issue_close,
    issue_create,
    issue_delete,
    issue_finish,
    issue_list,
    issue_move,
    issue_show,
    issue_start,
)

from socialseed_tasker.cli.commands.dependency_commands import (
    dependency_add,
    dependency_blocked,
    dependency_chain,
    dependency_list,
    dependency_remove,
)

from socialseed_tasker.cli.commands.component_commands import (
    component_add_dependency,
    component_create,
    component_delete,
    component_list,
    component_list_dependencies,
    component_show,
    component_update,
)

from socialseed_tasker.cli.commands.analysis_commands import (
    analyze_code_impact,
    analyze_impact,
    analyze_root_cause,
)

from socialseed_tasker.cli.commands.seed_commands import (
    seed_run,
)

from socialseed_tasker.cli.commands.constraints_commands import (
    constraints_doc_gaps,
    constraints_list,
    constraints_set,
    constraints_validate,
)

from socialseed_tasker.cli.commands.code_graph_commands import (
    code_graph_calls,
    code_graph_clear,
    code_graph_depends,
    code_graph_file,
    code_graph_files,
    code_graph_find,
    code_graph_impact,
    code_graph_scan,
    code_graph_stats,
    code_graph_tests,
)

from socialseed_tasker.cli.commands.rag_commands import (
    rag_clear,
    rag_embed_native,
    rag_index,
    rag_search,
    rag_search_native,
    rag_stats,
)

from socialseed_tasker.cli.commands.reasoning_commands import (
    reasoning_clear,
    reasoning_history,
    reasoning_log,
    reasoning_stats,
)

from socialseed_tasker.cli.commands.agent_commands import (
    agent_architect,
    agent_context,
    agent_dispatch,
    agent_list,
    agent_reasoning,
    agent_register,
    agent_specialize,
    agent_suggest,
)

__all__ = [
    "agent_app",
    "agent_architect",
    "agent_context",
    "agent_dispatch",
    "agent_list",
    "agent_reasoning",
    "agent_register",
    "agent_specialize",
    "agent_suggest",
    "analyze_app",
    "analyze_code_impact",
    "analyze_impact",
    "analyze_root_cause",
    "code_graph_app",
    "code_graph_calls",
    "code_graph_clear",
    "code_graph_depends",
    "code_graph_file",
    "code_graph_files",
    "code_graph_find",
    "code_graph_impact",
    "code_graph_scan",
    "code_graph_stats",
    "code_graph_tests",
    "component_add_dependency",
    "component_app",
    "component_create",
    "component_delete",
    "component_list",
    "component_list_dependencies",
    "component_show",
    "component_update",
    "console",
    "constraints_app",
    "constraints_doc_gaps",
    "constraints_list",
    "constraints_set",
    "constraints_validate",
    "dependency_add",
    "dependency_app",
    "dependency_blocked",
    "dependency_chain",
    "dependency_list",
    "dependency_remove",
    "get_repository",
    "issue_app",
    "issue_close",
    "issue_create",
    "issue_delete",
    "issue_finish",
    "issue_list",
    "issue_move",
    "issue_show",
    "issue_start",
    "login_command",
    "logout_command",
    "project_app",
    "project_detect",
    "project_setup",
    "rag_app",
    "rag_clear",
    "rag_embed_native",
    "rag_index",
    "rag_search",
    "rag_search_native",
    "rag_stats",
    "reasoning_app",
    "reasoning_clear",
    "reasoning_history",
    "reasoning_log",
    "reasoning_stats",
    "resolve_component_id",
    "resolve_issue_id",
    "seed_app",
    "seed_run",
    "status_app",
    "status_command",
]
