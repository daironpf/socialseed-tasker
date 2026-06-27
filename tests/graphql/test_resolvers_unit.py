from ariadne import graphql_sync, make_executable_schema, load_schema_from_path
from unittest.mock import MagicMock

from socialseed_tasker.graphql import SDL_PATH
from socialseed_tasker.graphql.resolvers import query, mutation


def test_create_issue_resolver_enforces_auth():
    sdl = load_schema_from_path(SDL_PATH)
    schema = make_executable_schema(sdl, [query, mutation])
    container = MagicMock()
    container.rbac.has_permission.return_value = False
    context = {"container": container, "user_id": "u1"}
    query_str = '''
    mutation { createIssue(id: "i1", title: "T") { id title } }
    '''
    success, result = graphql_sync(schema, {"query": query_str}, context_value=context)
    assert not success or "errors" in result
