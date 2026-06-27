from socialseed_tasker.graphql import SDL_PATH
from ariadne import load_schema_from_path


def test_schema_loads():
    s = load_schema_from_path(SDL_PATH)
    assert "type Query" in s
    assert "type Mutation" in s
    assert "type Subscription" in s
