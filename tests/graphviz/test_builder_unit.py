from socialseed_tasker.graphviz.builder import Graph, compute_impact


def test_compute_impact_simple():
    g = Graph()
    g.add_node("a", "A")
    g.add_node("b", "B")
    g.add_node("c", "C")
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    imp = compute_impact(g, "a", max_depth=5)
    assert imp == ["b", "c"]


def test_compute_impact_max_depth():
    g = Graph()
    g.add_node("a", "A")
    g.add_node("b", "B")
    g.add_node("c", "C")
    g.add_node("d", "D")
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    g.add_edge("c", "d")
    imp = compute_impact(g, "a", max_depth=2)
    assert imp == ["b", "c"]


def test_compute_impact_no_dependencies():
    g = Graph()
    g.add_node("a", "A")
    g.add_node("b", "B")
    imp = compute_impact(g, "a", max_depth=5)
    assert imp == []


def test_compute_impact_unknown_node():
    g = Graph()
    g.add_node("a", "A")
    imp = compute_impact(g, "unknown", max_depth=5)
    assert imp == []


def test_graph_to_json_deterministic():
    g = Graph()
    g.add_node("z", "Z")
    g.add_node("a", "A")
    g.add_node("m", "M")
    g.add_edge("z", "a", "DEPENDS_ON")
    g.add_edge("a", "m", "DEPENDS_ON")
    j = g.to_json()
    node_ids = [n["id"] for n in j["nodes"]]
    assert node_ids == ["a", "m", "z"]
    assert j["edges"] == [
        {"from": "a", "to": "m", "relation": "DEPENDS_ON"},
        {"from": "z", "to": "a", "relation": "DEPENDS_ON"},
    ]


def test_graph_empty():
    g = Graph()
    j = g.to_json()
    assert j == {"nodes": [], "edges": []}


def test_compute_impact_branching():
    g = Graph()
    g.add_node("a", "A")
    g.add_node("b", "B")
    g.add_node("c", "C")
    g.add_node("d", "D")
    g.add_edge("a", "b")
    g.add_edge("a", "c")
    g.add_edge("c", "d")
    imp = compute_impact(g, "a", max_depth=5)
    assert sorted(imp) == ["b", "c", "d"]
