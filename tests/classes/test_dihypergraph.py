import pickle
import tempfile

import pytest

import xgi
from xgi.exception import IDNotFound, XGIError
from xgi.utils import dual_dict


def test_constructor(diedgelist1, diedgedict1):
    H_list = xgi.DiHypergraph(diedgelist1)
    H_dict = xgi.DiHypergraph(diedgedict1)
    H_hg = xgi.DiHypergraph(H_list)

    assert set(H_list.nodes) == set(H_dict.nodes) == set(H_hg.nodes)
    assert set(H_list.edges) == set(H_dict.edges) == set(H_hg.edges)
    for e in H_hg.edges:
        assert (
            H_list.edges.members(e) == H_dict.edges.members(e) == H_hg.edges.members(e)
        )

    with pytest.raises(XGIError):
        xgi.DiHypergraph(1)


def test_hypergraph_attrs():
    H = xgi.DiHypergraph()
    assert H._hypergraph == {}
    with pytest.raises(XGIError):
        H["name"]
    H = xgi.DiHypergraph(name="test")
    assert H["name"] == "test"


def test_contains(diedgelist1):
    el1 = diedgelist1
    H = xgi.DiHypergraph(el1)
    unique_nodes = {node for edge in el1 for node in edge[0].union(edge[1])}
    for node in unique_nodes:
        assert node in H

    # test TypeError handling
    assert [0] not in H


def test_string():
    H1 = xgi.DiHypergraph()
    assert str(H1) == "Unnamed DiHypergraph with 0 nodes and 0 hyperedges"
    H2 = xgi.DiHypergraph(name="test")
    assert str(H2) == "DiHypergraph named test with 0 nodes and 0 hyperedges"


def test_len(diedgelist1):
    assert len(xgi.DiHypergraph(diedgelist1)) == 8


def test_add_nodes_from(attr1, attr2, attr3):
    H = xgi.DiHypergraph()
    H.add_nodes_from(range(3), **attr1)
    assert H.nodes[0]["color"] == attr1["color"]
    assert H.nodes[1]["color"] == attr1["color"]
    assert H.nodes[2]["color"] == attr1["color"]

    H = xgi.DiHypergraph()
    H.add_nodes_from(zip(range(3), [attr1, attr2, attr3]))
    assert H.nodes[0]["color"] == attr1["color"]
    assert H.nodes[1]["color"] == attr2["color"]
    assert H.nodes[2]["color"] == attr3["color"]


def test_add_node_attr(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)
    assert "new_node" not in H
    H.add_node("new_node", color="red")
    assert "new_node" in H
    assert "color" in H.nodes["new_node"]
    assert H.nodes["new_node"]["color"] == "red"


def test_hypergraph_attr(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)
    with pytest.raises(XGIError):
        H["color"]
    H["color"] = "red"
    assert H["color"] == "red"


def test_memberships(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)
    assert H.nodes.memberships(1) == {0}
    assert H.nodes.memberships(2) == {0}
    assert H.nodes.memberships(3) == {0}
    assert H.nodes.memberships(4) == {0}
    assert H.nodes.memberships(6) == {1}
    assert H.nodes([1, 2, 6]).memberships() == {1: {0}, 2: {0}, 6: {1}}
    with pytest.raises(IDNotFound):
        H.nodes.memberships(0)
    with pytest.raises(TypeError):
        H.nodes.memberships(slice(1, 4))


def test_dimemberships(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)
    assert H.nodes.dimemberships(1) == (set(), {0})
    assert H.nodes.dimemberships(2) == (set(), {0})
    assert H.nodes.dimemberships(3) == (set(), {0})
    assert H.nodes.dimemberships(4) == ({0}, set())
    assert H.nodes.dimemberships(6) == ({1}, {1})
    assert H.nodes([1, 2, 6]).dimemberships() == {
        1: (set(), {0}),
        2: (set(), {0}),
        6: ({1}, {1}),
    }
    with pytest.raises(IDNotFound):
        H.nodes.memberships(0)
    with pytest.raises(TypeError):
        H.nodes.memberships(slice(1, 4))


def test_add_edge_accepts_different_types():
    for edge in [([1, 2, 3], [4]), [{1, 2, 3}, {4}], (iter([1, 2, 3]), iter([4]))]:
        H = xgi.DiHypergraph()
        H.add_edge(edge)
        assert (1 in H) and (2 in H) and (3 in H) and (4 in H)
        assert 0 in H.edges
        assert {1, 2, 3, 4} in H.edges.members()
        assert {1, 2, 3, 4} == H.edges.members(0)
        assert H.edges.members(dtype=dict) == {0: {1, 2, 3, 4}}
        assert H.edges.tail(dtype=dict) == {0: {1, 2, 3}}
        assert H.edges.head(dtype=dict) == {0: {4}}


def test_add_edge_raises_with_empty_edges():
    H = xgi.DiHypergraph()
    for edge in [[], {}, iter([])]:
        with pytest.raises(XGIError):
            H.add_edge(edge)

    for edge in [[[], []], (set(), set())]:
        with pytest.raises(XGIError):
            H.add_edge(edge)


def test_add_edge_rejects_set():
    H = xgi.DiHypergraph()
    with pytest.raises(XGIError):
        H.add_edge({(1, 2), (3, 4)})


def test_add_edge_handles_uid_correctly():
    H1 = xgi.DiHypergraph()
    H1.add_edge(([1, 2], [3]), id=0)
    H1.add_edge(([3, 4], [4, 5]), id=2)
    H1.add_edge([[5, 6], [2, 3]])
    assert H1.edges.dimembers(dtype=dict) == {
        0: ({1, 2}, {3}),
        2: ({3, 4}, {4, 5}),
        3: ({5, 6}, {2, 3}),
    }


def test_add_edge_warns_when_overwriting_edge_id():
    H2 = xgi.DiHypergraph()
    H2.add_edge(([1, 2], [3]))
    H2.add_edge(([3, 4], [5, 6, 7]))
    with pytest.warns(Warning):
        H2.add_edge(([5, 6], [8]), id=0)
    assert H2._edge_out == {0: {1, 2}, 1: {3, 4}}


def test_add_edge_with_id():
    H = xgi.DiHypergraph()
    H.add_edge(([1, 2, 3], [3, 4]), id="myedge")
    assert (1 in H) and (2 in H) and (3 in H) and (4 in H)
    assert "myedge" in H.edges
    assert {1, 2, 3, 4} in H.edges.members()
    assert {1, 2, 3, 4} == H.edges.members("myedge")
    assert ({1, 2, 3}, {3, 4}) in H.edges.dimembers()
    assert ({1, 2, 3}, {3, 4}) == H.edges.dimembers("myedge")
    assert H.edges.members(dtype=dict) == {"myedge": {1, 2, 3, 4}}


def test_add_edge_with_attr():
    H = xgi.DiHypergraph()
    H.add_edge(([1, 2, 3], [1, 4]), color="red", place="peru")
    assert (1 in H) and (2 in H) and (3 in H) and (4 in H)
    assert 0 in H.edges
    assert {1, 2, 3, 4} in H.edges.members()
    assert {1, 2, 3, 4} == H.edges.members(0)
    assert ({1, 2, 3}, {1, 4}) in H.edges.dimembers()
    assert ({1, 2, 3}, {1, 4}) == H.edges.dimembers(0)
    assert H.edges.members(dtype=dict) == {0: {1, 2, 3, 4}}
    assert H.edges[0] == {"color": "red", "place": "peru"}


def test_add_edges_from_iterable_of_members():
    edges = [({0, 1}, {2}), ({1, 2}, {4}), ({2, 3, 4}, {1})]
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert H.edges.dimembers() == edges

    H1 = xgi.DiHypergraph(edges)
    with pytest.raises(XGIError):
        xgi.DiHypergraph(H1.edges)

    edges = {
        (frozenset([0, 1]), frozenset([2])),
        (frozenset([1, 2]), frozenset([4])),
        (frozenset([2, 3, 4]), frozenset([1])),
    }
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert H.edges.dimembers() == [(set(e[0]), set(e[1])) for e in edges]

    edges = [([0, 1], {2}), [{1, 2}, [4]], ((2, 3, 4), [1])]
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert H.edges.dimembers() == [(set(e[0]), set(e[1])) for e in edges]


def test_add_edges_from_format2():
    edges = [(({0, 1}, {2}), 0), (({1, 2}, {4}), 1), (({2, 3, 4}, {1}), 2)]
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert list(H.edges) == [e[1] for e in edges]
    assert H.edges.dimembers(dtype=dict) == {e[1]: (e[0][0], e[0][1]) for e in edges}

    edges = [(({0, 1}, {2}), "a"), (({1, 2}, {4}), "b"), (({2, 3, 4}, {1}), "foo")]
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert list(H.edges) == [e[1] for e in edges]
    assert H.edges.dimembers(dtype=dict) == {e[1]: (e[0][0], e[0][1]) for e in edges}

    edges = [(({0, 1}, {2}), "a"), (({1, 2}, {4}), "b"), (({2, 3, 4}, {1}), 100)]
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert list(H.edges) == [e[1] for e in edges]
    assert H.edges.dimembers(dtype=dict) == {e[1]: (e[0][0], e[0][1]) for e in edges}

    # check counter
    H.add_edge(([1, 9, 2], [10]))
    assert H.edges.members(101) == {1, 2, 9, 10}

    H1 = xgi.DiHypergraph([({1, 2}, {3}), ({2, 3, 4}, {1})])
    with pytest.warns(Warning):
        H1.add_edges_from([(({1, 3}, {2}), 0)])
    assert H1._edge_out == {0: {1, 2}, 1: {2, 3, 4}}


def test_add_edges_from_format3():
    edges = [
        (({0, 1}, {2}), {"color": "red"}),
        (({1, 2}, {4}), {"age": 30}),
        (({2, 3, 4}, {1}), {"color": "blue", "age": 40}),
    ]
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert list(H.edges) == list(range(len(edges)))
    assert H.edges.dimembers() == [(e[0][0], e[0][1]) for e in edges]
    for idx, e in enumerate(H.edges):
        assert H.edges[e] == edges[idx][1]
    # check counter
    H.add_edge(([1, 9, 2], [10]))
    assert H.edges.members(3) == {1, 2, 9, 10}


def test_add_edges_from_format4():
    edges = [
        (({0, 1}, {2}), "one", {"color": "red"}),
        (({1, 2}, {4}), "two", {"age": 30}),
        (({2, 3, 4}, {1}), "three", {"color": "blue", "age": 40}),
    ]
    H = xgi.DiHypergraph()
    H.add_edges_from(edges)
    assert list(H.edges) == [e[1] for e in edges]
    assert H.edges.dimembers() == [(e[0][0], e[0][1]) for e in edges]
    for idx, e in enumerate(H.edges):
        assert H.edges[e] == edges[idx][2]
    # check counter
    H.add_edge(([1, 9, 2], [10]))
    assert H.edges.members(0) == {1, 2, 9, 10}

    H1 = xgi.DiHypergraph([({1, 2}, {3}), ({2, 3, 4}, {1})])
    with pytest.warns(Warning):
        H1.add_edges_from([(({0, 1}, {2}), 0, {"color": "red"})])
    assert H1._edge_out == {0: {1, 2}, 1: {2, 3, 4}}


def test_add_edges_from_dict(diedgedict1):
    H = xgi.DiHypergraph()
    H.add_edges_from(diedgedict1)
    assert list(H.edges) == [0, 1]
    assert H.edges.members() == [{1, 2, 3, 4}, {5, 6, 7, 8}]
    # check counter
    H.add_edge(([1, 9, 2], [10]))
    assert H.edges.members(2) == {1, 2, 9, 10}

    H1 = xgi.DiHypergraph([({1, 2}, {2, 3, 4})])
    with pytest.warns(Warning):
        H1.add_edges_from({0: ({1, 3}, {2})})
    assert H1.edges.dimembers(0) == ({1, 2}, {2, 3, 4})


def test_add_edges_from_attr_precedence():
    H = xgi.DiHypergraph()
    edges = [
        (([0, 1], [2]), "one", {"color": "red"}),
        (([1, 2], [0]), "two", {"age": 30}),
        (([2, 3, 4], [5]), "three", {"color": "blue", "age": 40}),
    ]
    H.add_edges_from(edges, color="black")
    assert H.edges["one"] == {"color": "red"}
    assert H.edges["two"] == {"age": 30, "color": "black"}
    assert H.edges["three"] == {"age": 40, "color": "blue"}


def test_remove_edge(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)
    H.remove_edge(0)
    assert 0 not in H.edges
    assert 1 in H and 2 in H and 3 in H and 4 in H
    assert H.nodes.memberships() == {
        1: set(),
        2: set(),
        3: set(),
        4: set(),
        5: {1},
        6: {1},
        7: {1},
        8: {1},
    }

    with pytest.raises(IDNotFound):
        H.edges[0]


def test_remove_edges_from(diedgelist2):
    H = xgi.DiHypergraph(diedgelist2)
    H.remove_edges_from([1, 2])
    assert 0 in H.edges
    assert 1 not in H.edges and 2 not in H.edges
    assert sorted(H.nodes) == list(range(6))
    assert H.nodes.memberships(2) == {0}


def test_copy(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)
    H["key"] = "value"
    copy = H.copy()
    assert list(copy.nodes) == list(H.nodes)
    assert list(copy.edges) == list(H.edges)
    assert list(copy.edges.members()) == list(H.edges.members())
    assert H._hypergraph == copy._hypergraph

    H.add_node(10)
    assert list(copy.nodes) != list(H.nodes)
    assert list(copy.edges) == list(H.edges)

    H.add_edge(([1, 3, 5], [6]))
    assert list(copy.edges) != list(H.edges)

    H["key2"] = "value2"
    assert H._hypergraph != copy._hypergraph

    copy.add_node(10)
    copy.add_edge(([1, 3, 5], [6]))
    copy["key2"] = "value2"
    assert list(copy.nodes) == list(H.nodes)
    assert list(copy.edges) == list(H.edges)
    assert list(copy.edges.members()) == list(H.edges.members())
    assert H._hypergraph == copy._hypergraph

    H1 = xgi.DiHypergraph()
    H1.add_edge(([1, 2], [3]), id="x")
    copy2 = H1.copy()  # does not throw error because of str id
    assert list(copy2.nodes) == list(H1.nodes)
    assert list(copy2.edges) == list(H1.edges)
    assert list(copy2.edges.members()) == list(H1.edges.members())
    assert H1._hypergraph == copy2._hypergraph


def test_copy_issue128():
    # see https://github.com/xgi-org/xgi/issues/128
    H = xgi.DiHypergraph()
    H["key"] = "value"
    K = H.copy()
    K["key"] = "some_other_value"
    assert H["key"] == "value"


def test_remove_node_weak(diedgelist1, diedgelist2):
    H = xgi.DiHypergraph(diedgelist1)

    # node in the tail
    assert 1 in H
    H.remove_node(1)
    assert 1 not in H

    # node in the head
    assert 8 in H
    H.remove_node(8)
    assert 8 not in H

    H = xgi.DiHypergraph(diedgelist1)

    # node in both head and tail
    assert 6 in H
    H.remove_node(6)
    assert 6 not in H

    with pytest.raises(IDNotFound):
        H.remove_node(10)

    # test empty edge removal
    H = xgi.DiHypergraph(diedgelist1)
    H.remove_node(1)
    H.remove_node(2)
    H.remove_node(3)
    H.remove_node(4)

    assert 0 not in H.edges

    # test multiple edge removal with a single node.
    H = xgi.DiHypergraph(diedgelist2)
    H.remove_node(0)
    H.remove_node(1)

    H.remove_node(3)
    H.remove_node(4)
    H.remove_node(5)

    assert H.num_edges == 3

    # this removes three edges at once
    H.remove_node(2)

    assert H.num_edges == 0


def test_remove_node_strong(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)

    # node in the tail
    assert 1 in H
    H.remove_node(1, strong=True)
    assert 1 not in H

    assert 0 not in H.edges

    # node in the head
    assert 8 in H
    H.remove_node(8, strong=True)
    assert 8 not in H

    assert 1 not in H.edges

    H = xgi.DiHypergraph(diedgelist1)

    # node in both head and tail
    assert 6 in H
    H.remove_node(6, strong=True)
    # assert 6 not in H

    # assert 1 not in H.edges


def test_remove_nodes_from(diedgelist1):
    H = xgi.DiHypergraph(diedgelist1)

    H.remove_nodes_from([1, 2, 3])
    assert 1 not in H and 2 not in H and 3 not in H

    with pytest.warns(Warning):
        H.remove_nodes_from([1, 2, 3])


def test_pickle(diedgelist1):
    _, filename = tempfile.mkstemp()
    H1 = xgi.DiHypergraph(diedgelist1)

    with open(filename, "wb") as file:
        pickle.dump(H1, file)
    with open(filename, "rb") as file:
        H2 = pickle.load(file)

    assert H1.nodes == H2.nodes
    assert H1.edges == H2.edges
    assert [H1.edges.members(id) for id in H1.edges] == [
        H2.edges.members(id) for id in H2.edges
    ]
