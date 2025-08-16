import pytest
from mistake_prevention_system import require_params, MistakePreventionSystem


@require_params("collection", "key", "update")
def arango_update(collection=None, key=None, update=None):
    return True


def test_arango_update_missing_params():
    system = MistakePreventionSystem()
    # Missing 'update'
    try:
        system.validate_tool_call_params(
            arango_update, collection="agent_memory", key="123"
        )
    except ValueError as e:
        assert "Missing required parameter(s): update" in str(e)
    else:
        assert False, "Expected ValueError for missing parameter"

    # All params present
    assert (
        system.validate_tool_call_params(
            arango_update, collection="agent_memory", key="123", update={"foo": "bar"}
        )
        is True
    )


if __name__ == "__main__":
    test_arango_update_missing_params()
    print("All tests passed.")
