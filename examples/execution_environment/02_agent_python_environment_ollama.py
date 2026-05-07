from typing import Any, cast

from agently import Agently

from _shared import create_agent, print_action_results, print_response


class ManagedListStatsExecutor:
    kind = "managed_python_list_stats"
    sandboxed = True

    async def execute(self, *, spec, action_call, policy, settings):
        _ = (spec, policy, settings)
        action_input = action_call.get("action_input", {})
        if not isinstance(action_input, dict):
            action_input = {}
        numbers = action_input.get("numbers", [])
        if not isinstance(numbers, list):
            numbers = []
        numbers = [int(item) for item in numbers]

        resources = action_call.get("execution_environment_resources", {})
        sandbox = cast(dict[str, Any], resources).get("managed_python_stats")
        if sandbox is None or not hasattr(sandbox, "run"):
            raise RuntimeError("managed_python_stats execution environment is not available.")

        return sandbox.run(
            "numbers = " + repr(numbers) + "\n"
            "result = {\n"
            "    'average': sum(numbers) / len(numbers),\n"
            "    'max_minus_min_gap': max(numbers) - min(numbers),\n"
            "    'count': len(numbers),\n"
            "}\n"
        )["result"]


agent = create_agent(
    "ollama",
    (
        "You are an exact calculation assistant. "
        "When a managed action is available, call it before replying. "
        "Do not calculate list statistics by yourself. "
        "Do not include URLs or source links in the reply."
    ),
)

agent.action.register_action(
    action_id="managed_python_stats",
    desc=(
        "Calculate exact statistics for a list of integers by using a managed Python execution environment."
    ),
    kwargs={"numbers": (list[int], "List of integers to analyze.")},
    executor=ManagedListStatsExecutor(),
    side_effect_level="exec",
    sandbox_required=True,
    expose_to_model=True,
    execution_environments=[
        {
            "kind": "python",
            "scope": "action_call",
            "resource_key": "managed_python_stats",
        }
    ],
)


if __name__ == "__main__":
    agent.use_actions("managed_python_stats")
    agent.input(
        "Use the managed_python_stats action with numbers [15, 23, 42, 8, 12]. "
        "Then reply with the average and max-minus-min gap."
    )

    records = agent.get_action_result()
    print_action_results(records)

    response = agent.get_response()
    print_response(response)

    print("[ACTION_CALL_HANDLES_AFTER_RELEASE]")
    print(Agently.execution_environment.list(scope="action_call"))
