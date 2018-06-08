import pytest

from randovania.resolver.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.resolver.resources import SimpleResourceInfo, ResourceDatabase


@pytest.fixture
def database():
    return ResourceDatabase(
        item=[],
        event=[],
        trick=[],
        damage=[],
        version=[],
        misc=[
            SimpleResourceInfo(0, "Trivial", "Trivial"),
            SimpleResourceInfo(1, "Impossible", "Impossible"),
        ],
        difficulty=[],
        pickups=[]
    )


def make_req_a():
    req_a = SimpleResourceInfo(0, "A", "A")
    id_req_a = IndividualRequirement(req_a, 1, False)

    return req_a, id_req_a


def make_req_b():
    req_b = SimpleResourceInfo(1, "B", "B")
    id_req_b = IndividualRequirement(req_b, 1, False)

    return req_b, id_req_b


def test_empty_requirement_set():
    assert not RequirementSet([]).satisfied({})


def test_empty_requirement_list():
    assert RequirementList([]).satisfied({})


def test_simplify_requirement_set_static(database):
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_b]),
    ])

    simple_1 = the_set.simplify({res_a: 0, res_b: 0}, database)
    simple_2 = the_set.simplify({res_a: 0, res_b: 1}, database)
    simple_3 = the_set.simplify({res_a: 1, res_b: 1}, database)

    assert simple_1.alternatives == frozenset()
    assert simple_2.alternatives == frozenset([RequirementList()])
    assert simple_3.alternatives == frozenset([RequirementList()])


def test_prevent_redundant():
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_a, id_req_b]),
    ])

    assert the_set.alternatives == frozenset([RequirementList([id_req_a])])


def test_trivial_merge():
    trivial = RequirementSet.trivial()
    impossible = RequirementSet.impossible()
    res_a, id_req_a = make_req_a()

    the_set = RequirementSet([
        RequirementList([id_req_a]),
    ])

    assert trivial.merge(trivial) == trivial
    assert trivial.merge(the_set) == the_set
    assert the_set.merge(trivial) == the_set
    assert trivial.merge(impossible) == impossible
    assert impossible.merge(the_set) == impossible
    assert the_set.merge(impossible) == impossible
    assert the_set.merge(the_set) == the_set


@pytest.mark.parametrize("replacement", [
    RequirementSet.impossible(),
    RequirementSet([RequirementList([make_req_a()[1]])]),
    RequirementSet([RequirementList([make_req_a()[1], make_req_b()[1]])]),
])
def test_replace_missing(replacement):
    trivial = RequirementSet.trivial()

    req_a = SimpleResourceInfo(0, "A", "A")
    id_req_a = IndividualRequirement(req_a, 1, False)

    result = trivial.replace(id_req_a, replacement)

    assert result == trivial
