from pprint import pprint
from typing import Any, cast

from agently import Agently


ACTION_ID = "example_managed_python_environment"


Agently.action.register_python_sandbox_action(
    action_id=ACTION_ID,
    desc="Execute deterministic Python code inside a managed Python sandbox.",
    expose_to_model=False,
)


if __name__ == "__main__":
    result = Agently.action.execute_action(
        ACTION_ID,
        {
            "python_code": (
                "numbers = [15, 23, 42, 8, 12]\n"
                "result = {\n"
                "    'average': sum(numbers) / len(numbers),\n"
                "    'gap': max(numbers) - min(numbers),\n"
                "}"
            )
        },
    )

    print("[ACTION_RESULT]")
    pprint(result)

    result_data = cast(dict[str, Any], result.get("data"))
    assert result.get("status") == "success"
    assert result_data["result"] == {"average": 20.0, "gap": 34}

    action_call_handles = Agently.execution_environment.list(scope="action_call")
    print("[ACTION_CALL_HANDLES_AFTER_RELEASE]")
    pprint(action_call_handles)
    assert action_call_handles == []
