from multiagent_cli.input_parser import (
    InputModel,
    TaskModel,
    WorkloadModel,
    parse_and_validate_input,
)


def test_parse_and_validate_input_parses_valid_file(tmp_path):
    input_data = {
        "workloads": [
            {
                "id": "w1",
                "tasks": [
                    {"id": "t1", "type": "reasoning", "input": {"question": "Test?"}}
                ],
            }
        ]
    }
    file = tmp_path / "input.json"
    import json

    file.write_text(json.dumps(input_data))
    model = parse_and_validate_input(str(file))
    assert isinstance(model, InputModel)
    assert model.workloads[0].id == "w1"


def test_must_have_tasks_detects_workloads_with_no_tasks():
    workloads = [
        WorkloadModel(id="w1", tasks=[]),
        WorkloadModel(id="w2", tasks=None),
        WorkloadModel(id="w3", tasks=[TaskModel(id="t1", type="reasoning", input={})]),
    ]
    missing_tasks = InputModel.must_have_tasks(workloads)
    assert workloads[1] in missing_tasks
    assert workloads[0] not in missing_tasks
    assert workloads[2] not in missing_tasks
